from math import isfinite, pi
from html import escape

def generate_geometry(length: float, width: float, height: float, thickness: float = 0):
    if any(not isfinite(x) or x < 1 or x > 10000 for x in (length, width, height)):
        raise ValueError('尺寸必须在 1–10000 mm 之间')
    if not isfinite(thickness) or thickness < 0 or thickness > 1000 or 2*thickness >= min(length,width,height):
        raise ValueError("Invalid board thickness")
    l, w, h = length, width, height
    seam_allowance = max(3 * thickness, 5 if thickness else 0)
    bend_allowance = pi / 2 * (thickness + 0.5 * thickness) if thickness else 0
    origin = seam_allowance + bend_allowance / 2
    # A cross net: bottom, front/back, left/right; lid hinged to back.
    faces = [
        dict(id='bottom', label='底面', x=origin+h, y=origin+h+w, width=l, height=w),
        dict(id='back', label='后面', x=origin+h, y=origin+w, width=l, height=h),
        dict(id='top', label='顶面', x=origin+h, y=origin, width=l, height=w),
        dict(id='front', label='前面', x=origin+h, y=origin+h+2*w, width=l, height=h),
        dict(id='left', label='左面', x=origin, y=origin+h+w, width=h, height=w),
        dict(id='right', label='右面', x=origin+h+l, y=origin+h+w, width=h, height=w),
    ]
    folds = [[origin+h,origin+h+w,origin+h+l,origin+h+w], [origin+h,origin+w,origin+h+l,origin+w], [origin+h,origin+h+2*w,origin+h+l,origin+h+2*w], [origin+h,origin+h+w,origin+h,origin+h+2*w], [origin+h+l,origin+h+w,origin+h+l,origin+h+2*w]]
    return dict(length=l, width=w, height=h, thickness=thickness, inner_length=l-2*thickness, inner_width=w-2*thickness, inner_height=h-2*thickness, faces=faces, folds=folds,
                seam_allowance=seam_allowance, bend_allowance=bend_allowance, net_origin=origin,
                net_width=l+2*h+2*origin, net_height=2*w+2*h+2*origin,
                surface_area=2*(l*w+l*h+w*h), volume=l*w*h)

def project_pad(g, p):
    o=g.get('net_origin', 0)
    return dict(x=o+g['height']+g['length']/2+p['x']-p['length']/2,
                y=o+g['height']+1.5*g['width']+p['z']-p['width']/2)

def to_svg(g, pads=None):
    pads = pads or []
    projections = [(p, project_pad(g,p)) for p in pads]
    min_x = min([0]+[q['x'] for p,q in projections])
    min_y = min([0]+[q['y'] for p,q in projections])
    max_x = max([g['net_width']]+[q['x']+p['length'] for p,q in projections])
    max_y = max([g['net_height']]+[q['y']+p['width'] for p,q in projections])
    pad = max(max_x-min_x, max_y-min_y) * .13
    font = max(g['net_width'], g['net_height']) * .024
    def n(x): return f'{x:g}'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{min_x-pad} {min_y-pad} {max_x-min_x+2*pad} {max_y-min_y+2*pad+len(pads)*font*1.7}">', '<rect x="-100000" y="-100000" width="200000" height="200000" fill="#ffffff"/>']
    for f in g['faces']:
        x,y,w,h = (f[k] for k in ('x','y','width','height'))
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f0f6ff" stroke="#264b73" stroke-width="{font*.065}"/>')
        parts.append(f'<text x="{x+w/2}" y="{y+h/2}" text-anchor="middle" dominant-baseline="middle" font-family="sans-serif" font-size="{font}" fill="#264b73">{f["label"]} · {n(w)} × {n(h)} mm</text>')
    for x1,y1,x2,y2 in g['folds']:
        parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="white" stroke-width="{font*.16}"/>')
        parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#397fdf" stroke-width="{font*.09}" stroke-dasharray="{font*.35} {font*.22}"/>')
    for index, (p, q) in enumerate(projections, 1):
        parts.append(f'<rect data-pad="{index}" x="{q["x"]}" y="{q["y"]}" width="{p["length"]}" height="{p["width"]}" fill="#ffc879" fill-opacity=".65" stroke="#b87924" stroke-width="{font*.1}" stroke-dasharray="{font*.35} {font*.15}"/>')
        parts.append(f'<text x="{q["x"]+p["length"]/2}" y="{q["y"]+p["width"]/2}" text-anchor="middle" font-size="{font}" fill="#8a5312">{index}</text>')
        label = f'{index}. {p["name"]} · {n(p["length"])} × {n(p["width"])} × {n(p["height"])} mm · 底高 {n(p["y"])} mm（底面投影）'
        parts.append(f'<text x="{min_x}" y="{max_y+pad+index*font*1.5}" font-family="sans-serif" font-size="{font}" fill="#8a5312">{escape(label)}</text>')
    seam, bend = g.get('seam_allowance', 0), g.get('bend_allowance', 0)
    parts.append(f'<path d="M0,0 H{g["net_width"]} V{g["net_height"]} H0 Z" fill="none" stroke="#d99a3e" stroke-width="{font*.08}" stroke-dasharray="{font*.4} {font*.25}"/>')
    parts.append(f'<text x="{g["net_width"]/2}" y="{-pad*.4}" text-anchor="middle" font-family="sans-serif" font-size="{font}" fill="#64748b">t={n(g.get("thickness",0))} mm · seam={n(seam)} mm · bend={n(bend)} mm · net {n(g["net_width"])} × {n(g["net_height"])} mm</text></svg>')
    return ''.join(parts)
