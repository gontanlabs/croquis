"""Encaja una nube de puntos LiDAR de otra sesión (p. ej. 3d Scanner App) sobre el escaneo de RoomPlan de la casa.

Las dos tienen el eje Y hacia arriba (ARKit), así que basta un giro en planta, un desplazamiento y la altura del suelo.
Se busca con las paredes: los puntos de la nube entre 1,3 y 2,2 m sobre su suelo, contra las paredes de RoomPlan
(probando los cuatro giros de 90° respecto a la orientación dominante y afinando con ICP en planta).

    python alinear.py <room.json> <nube.ply|obj>  → nube alineada (npy) y el informe de huecos y techos
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree


def leer_nube(ruta: Path):
    ruta = Path(ruta)
    if ruta.suffix.lower() == '.ply':
        from reconstruir import leer_ply
        P = leer_ply(ruta)
    else:                                                     # OBJ: los vértices
        P = np.array([[float(v) for v in l.split()[1:4]] for l in ruta.read_text(errors='ignore').splitlines()
                      if l.startswith('v ')])
    P = P[np.isfinite(P).all(1)]
    return vertical_y(P)


def vertical_y(P):
    """Pone el eje vertical en Y: el eje con más puntos acumulados en sus dos extremos (suelo y techo). Algunas
    exportaciones PLY vienen con Z hacia arriba."""
    mejor = None
    for k in range(3):
        v = P[:, k]; lo, hi = np.percentile(v, [1, 99])
        if hi - lo < 1.5:
            continue
        cerca = ((np.abs(v - lo) < 0.05) | (np.abs(v - hi) < 0.05)).mean()
        if mejor is None or cerca > mejor[0]:
            mejor = (cerca, k)
    k = mejor[1] if mejor else 1
    if k == 1:
        return P
    if k == 2:                                   # Z arriba → Y arriba (x, z, -y)
        return np.c_[P[:, 0], P[:, 2], -P[:, 1]]
    return np.c_[P[:, 1], P[:, 0], P[:, 2]]


def _T(s):
    return np.array(s['transform'], float).reshape(4, 4).T


def segmentos(r):
    out = []
    for w in r['walls']:
        T = _T(w); c = T[:3, 3]; u = T[:3, 0]; L = w['dimensions'][0]
        a, b = c - u * L / 2, c + u * L / 2
        out.append(LineString([(a[0], a[2]), (b[0], b[2])]))
    return out


def _orient(pts2):
    """Orientación dominante (mod 90°) de unos puntos de pared: la que hace más picudo el histograma."""
    mejor = None
    for t in np.radians(np.arange(0, 90, 0.5)):
        d = np.array([math.cos(t), math.sin(t)]); n = np.array([-d[1], d[0]])
        s = 0
        for v in (d, n):
            pr = pts2 @ v
            h, _ = np.histogram(pr, bins=np.arange(pr.min(), pr.max() + 0.03, 0.03))
            s += (h.astype(float) ** 2).sum()
        if mejor is None or s > mejor[0]:
            mejor = (s, t)
    return mejor[1]


def alinear(r, P):
    suelo_r = min(_T(f)[1, 3] for f in r['floors'])
    suelo_p = float(np.percentile(P[:, 1], 1))
    h = P[:, 1] - suelo_p
    banda = P[(h > 1.3) & (h < 2.2)][:, [0, 2]]
    if len(banda) > 60000:
        banda = banda[np.random.default_rng(0).choice(len(banda), 60000, replace=False)]
    segs = segmentos(r)
    arbol = STRtree(segs)
    # Orientaciones dominantes de las dos
    pared_r = np.vstack([np.array(s.interpolate(t, normalized=True).coords[0]) for s in segs for t in np.linspace(0, 1, 20)])
    giro0 = _orient(pared_r) - _orient(banda)

    def coste(pts):
        d = np.array([arbol.geometries[arbol.nearest(Point(*q))].distance(Point(*q)) for q in pts[::20]])
        return float(np.median(np.minimum(d, 0.5)))

    mejor = None
    centro_r = pared_r.mean(0)
    for k in range(4):
        g = giro0 + k * math.pi / 2
        R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
        q = banda @ R.T
        # Desplazamiento inicial: probar sobre una rejilla gruesa alrededor del centro de la casa
        for dx in np.arange(-4, 4.01, 0.5):
            for dz in np.arange(-4, 4.01, 0.5):
                t = centro_r - q.mean(0) + [dx, dz]
                c = coste(q + t)
                if mejor is None or c < mejor[0]:
                    mejor = (c, g, t)
    c, g, t = mejor
    # ICP en planta (punto a recta)
    for _ in range(30):
        R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
        q = banda @ R.T + t
        A, b = [], []
        for p in q[::5]:
            s = arbol.geometries[arbol.nearest(Point(*p))]
            if s.distance(Point(*p)) > 0.3:
                continue
            (x1, y1), (x2, y2) = s.coords
            u = np.array([x2 - x1, y2 - y1]); u /= np.linalg.norm(u); n = np.array([-u[1], u[0]])
            res = (p - [x1, y1]) @ n
            jac = [n @ np.array([-p[1] + t[1], p[0] - t[0]]), n[0], n[1]]   # d(res)/d(giro, tx, tz)
            A.append(jac); b.append(-res)
        if len(A) < 50:
            break
        dg, dtx, dtz = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)[0]
        g += dg; t = t + [dtx, dtz]
        if abs(dg) < 1e-5 and abs(dtx) + abs(dtz) < 1e-4:
            break
    R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
    xz = P[:, [0, 2]] @ R.T + t
    alineada = np.c_[xz[:, 0], P[:, 1] - suelo_p + suelo_r, xz[:, 1]]
    return alineada, {'giro_grados': round(math.degrees(g), 2), 'desplazamiento': [round(float(v), 3) for v in t],
                      'error_mediano_m': round(coste(xz[(h > 1.3) & (h < 2.2)][:20000]), 3)}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    import detectar
    r = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    P = leer_nube(Path(sys.argv[2]))
    print('puntos', len(P))
    Q, info = alinear(r, P)
    print('alineado:', info)
    np.save(Path(sys.argv[2]).with_suffix('.alineada.npy'), Q.astype(np.float32))
    for p in detectar.paredes(r, Q):
        if p.get('tramos') and p['puntos'] > 500:
            print(p)
    print(detectar.techos(r, Q))
