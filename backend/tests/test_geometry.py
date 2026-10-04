import xml.etree.ElementTree as ET
import pytest
from app.geometry import generate_geometry, to_svg

@pytest.mark.parametrize('dims', [(240,160,100),(100,100,100),(1,10000,1),(300,200,50)])
def test_net_is_six_nonoverlapping_connected_faces(dims):
    g=generate_geometry(*dims)
    assert len(g['faces'])==6
    assert len(g['folds'])==5
    assert sum(f['width']*f['height'] for f in g['faces'])==g['surface_area']
    assert g['volume']==dims[0]*dims[1]*dims[2]
    for i,a in enumerate(g['faces']):
        assert 0<=a['x'] and a['x']+a['width']<=g['net_width']
        assert 0<=a['y'] and a['y']+a['height']<=g['net_height']
        for b in g['faces'][i+1:]:
            overlap_x=min(a['x']+a['width'],b['x']+b['width'])-max(a['x'],b['x'])
            overlap_y=min(a['y']+a['height'],b['y']+b['height'])-max(a['y'],b['y'])
            assert overlap_x<=0 or overlap_y<=0
    svg=ET.fromstring(to_svg(g))
    assert len(svg.findall('{http://www.w3.org/2000/svg}text'))==7

@pytest.mark.parametrize('value',[0,-1,10001,float('nan'),float('inf')])
def test_invalid_dimension(value):
    with pytest.raises(ValueError): generate_geometry(value,100,100)

def test_board_thickness_inner_dimensions():
    g=generate_geometry(240,160,100,5)
    assert (g['inner_length'],g['inner_width'],g['inner_height'])==(230,150,90)
    assert 't=5 mm' in to_svg(g)
    for t in [-1,50,float('nan')]:
        with pytest.raises(ValueError): generate_geometry(240,160,100,t)

def test_pad_projection_and_svg_escape():
    from app.geometry import project_pad
    g=generate_geometry(240,160,100)
    p=dict(name='<垫块&>',length=40,width=30,height=15,x=-65,y=20,z=10)
    assert project_pad(g,p)==dict(x=135,y=335)
    svg=ET.fromstring(to_svg(g,[p]))
    rect=svg.find('{http://www.w3.org/2000/svg}rect[@data-pad="1"]')
    assert rect.attrib['x']=='135.0'
    assert any('<垫块&>' in (t.text or '') and '底高 20' in (t.text or '') for t in svg.findall('{http://www.w3.org/2000/svg}text'))

def test_outside_pad_is_inside_svg_viewbox():
    g=generate_geometry(240,160,100)
    p=dict(name='外部',length=40,width=30,height=15,x=-10000,y=20,z=10000)
    svg=ET.fromstring(to_svg(g,[p]))
    x,y,w,h=map(float,svg.attrib['viewBox'].split())
    rect=svg.find('{http://www.w3.org/2000/svg}rect[@data-pad="1"]')
    assert x<=float(rect.attrib['x']) and float(rect.attrib['x'])+40<=x+w
    assert y<=float(rect.attrib['y']) and float(rect.attrib['y'])+30<=y+h
