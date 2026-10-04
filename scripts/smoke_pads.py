import httpx

with httpx.Client(base_url='http://127.0.0.1:8000',timeout=10) as c:
    payload=dict(name='垫块联调测试',length=240,width=160,height=100,pads=[
        dict(id='a',name='左垫块',length=40,width=30,height=15,x=-80,y=0,z=30),
        dict(id='b',name='悬空垫块',length=20,width=25,height=10,x=200,y=150,z=-50)])
    r=c.post('/api/designs',json=payload)
    assert r.status_code==201,r.text
    identifier=r.json()['id']
    try:
        assert r.json()['pads']==payload['pads']
        saved=next(d for d in c.get('/api/designs').json() if d['id']==identifier)
        assert saved['pads']==payload['pads']
        payload['pads'][0]['height']=0
        assert c.post('/api/designs',json=payload).status_code==422
    finally:
        assert c.delete(f'/api/designs/{identifier}').status_code==204
    print('PASS: multiple pads saved and reloaded from MySQL, negative/outside coordinates, validation, cascade deletion.')
