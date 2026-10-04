import pytest
from pydantic import ValidationError
from app.main import DesignIn, Pad

def pad(**changes):
    return dict(id='pad-1',name='垫块',length=40,width=30,height=15,x=-80,y=10,z=35,**changes)

def test_old_design_defaults_to_no_pads():
    assert DesignIn(name='旧方案',length=240,width=160,height=100).pads == []

def test_pad_accepts_negative_and_outside_positions():
    data=pad(); data.update(x=-100000,y=-15,z=100000)
    assert Pad(**data).x == -100000

@pytest.mark.parametrize('field,value',[('length',0),('height',10001),('x',100001),('y',float('nan')),('z',float('inf')),('name',' ')])
def test_pad_rejects_invalid_values(field,value):
    data=pad(); data[field]=value
    with pytest.raises(ValidationError): Pad(**data)

def test_pad_count_limit():
    with pytest.raises(ValidationError):
        DesignIn(name='方案',length=240,width=160,height=100,pads=[pad()]*101)
