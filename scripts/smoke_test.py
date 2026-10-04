"""Exercise the actual running HTTP server and MySQL persistence."""
import httpx
import xml.etree.ElementTree as ET
from uuid import uuid4

with httpx.Client(base_url='http://127.0.0.1:8000', timeout=10) as client:
    assert client.get('/api/health').json()=={'status':'ok','database':'mysql'}
    dimensions=dict(length=240,width=160,height=100)
    geometry=client.post('/api/geometry',json=dimensions)
    assert geometry.status_code==200
    assert geometry.json()['surface_area']==156800
    assert geometry.json()['volume']==3840000
    assert client.post('/api/geometry',json={**dimensions,'length':0}).status_code==422
    assert client.post('/api/geometry',json={**dimensions,'width':10001}).status_code==422
    assert client.post('/api/designs',json={**dimensions,'name':'   '}).status_code==422
    cors=client.options('/api/geometry',headers={'Origin':'http://127.0.0.1:5173','Access-Control-Request-Method':'POST'})
    assert cors.headers['access-control-allow-origin']=='http://127.0.0.1:5173'
    svg=client.post('/api/export/svg',json=dimensions)
    assert svg.status_code==200
    assert ET.fromstring(svg.text).tag.endswith('svg')
    result=client.post('/api/designs',json={**dimensions,'name':'联调测试-'+uuid4().hex[:8]})
    assert result.status_code==201, result.text
    design=result.json()
    try:
        # A fresh HTTP request creates a fresh database session.
        assert any(d['id']==design['id'] and d['length']==240 for d in client.get('/api/designs').json())
    finally:
        assert client.delete(f'/api/designs/{design["id"]}').status_code==204
    assert client.delete(f'/api/designs/{design["id"]}').status_code==404
    print('PASS: MySQL health, geometry, validation, CORS, SVG export, save, reload, delete, 404.')
