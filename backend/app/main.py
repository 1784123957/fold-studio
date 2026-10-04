import os
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict, model_validator
from sqlalchemy import create_engine, String, Float, DateTime, select, text, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from .geometry import generate_geometry, to_svg

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
engine = create_engine(os.environ['DATABASE_URL'], pool_pre_ping=True)
Session = sessionmaker(engine)
class Base(DeclarativeBase): pass
class Design(Base):
    __tablename__ = 'designs'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    length: Mapped[float] = mapped_column(Float)
    width: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    thickness: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    pad_record: Mapped['DesignPads | None'] = relationship(cascade='all, delete-orphan', lazy='selectin', uselist=False)
    @property
    def pads(self):
        return self.pad_record.items if self.pad_record else []
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class DesignPads(Base):
    __tablename__ = 'design_pads'
    design_id: Mapped[int] = mapped_column(ForeignKey('designs.id'), primary_key=True)
    items: Mapped[list] = mapped_column(JSON)

class Dimensions(BaseModel):
    length: float = Field(ge=1, le=10000, allow_inf_nan=False)
    width: float = Field(ge=1, le=10000, allow_inf_nan=False)
    height: float = Field(ge=1, le=10000, allow_inf_nan=False)
class Pad(Dimensions):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=100, pattern=r'.*\S.*')
    x: float = Field(ge=-100000, le=100000, allow_inf_nan=False)
    y: float = Field(ge=-100000, le=100000, allow_inf_nan=False)
    z: float = Field(ge=-100000, le=100000, allow_inf_nan=False)

class BoxDimensions(Dimensions):
    thickness: float = Field(default=0, ge=0, le=1000, allow_inf_nan=False)
    @model_validator(mode='after')
    def valid_thickness(self):
        if self.thickness * 2 >= min(self.length, self.width, self.height):
            raise ValueError('板厚须小于最短外尺寸的一半')
        return self

class LayoutIn(BoxDimensions):
    pads: list[Pad] = Field(default_factory=list, max_length=100)

class DesignIn(LayoutIn):
    name: str = Field(min_length=1, max_length=100, pattern=r'.*\S.*')
class DesignOut(DesignIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield
    engine.dispose()

app = FastAPI(title='Fold Studio API', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv('CORS_ORIGINS','http://127.0.0.1:5173,http://localhost:5173').split(','), allow_methods=['GET','POST','DELETE'], allow_headers=['Content-Type'])
@app.get('/api/health')
def health():
    try:
        with engine.connect() as conn: conn.execute(text('SELECT 1'))
    except SQLAlchemyError:
        raise HTTPException(503, '数据库连接失败')
    return {'status':'ok','database':'mysql'}
@app.post('/api/geometry')
def geometry(data: BoxDimensions):
    return generate_geometry(**data.model_dump())
@app.post('/api/export/svg')
def export(data: LayoutIn):
    return Response(to_svg(generate_geometry(**data.model_dump(exclude={'pads'})), [p.model_dump() for p in data.pads]), media_type='image/svg+xml', headers={'Content-Disposition':'attachment; filename="fold-net.svg"'})
@app.get('/api/designs', response_model=list[DesignOut])
def designs():
    with Session() as s:
        return s.scalars(select(Design).order_by(Design.id.desc()).limit(100)).all()
@app.post('/api/designs', response_model=DesignOut, status_code=201)
def save(data: DesignIn):
    with Session() as s:
        values = data.model_dump()
        pads = values.pop('pads')
        d = Design(**values)
        d.pad_record = DesignPads(items=pads)
        s.add(d); s.commit(); s.refresh(d)
        return d
@app.delete('/api/designs/{design_id}', status_code=204)
def delete(design_id: int):
    with Session() as s:
        d = s.get(Design, design_id)
        if d is None: raise HTTPException(404, '方案不存在')
        s.delete(d); s.commit()
