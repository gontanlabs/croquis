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


def _dist_segs(Q, A, B):
    """Distancia de cada punto Q (n×2) al segmento más cercano (A, B: m×2) y la normal de ese segmento."""
    AB = B - A; L2 = (AB ** 2).sum(1)
    t = np.clip(((Q[:, None, :] - A[None]) * AB[None]).sum(2) / L2[None], 0, 1)
    proy = A[None] + t[..., None] * AB[None]
    d = np.linalg.norm(Q[:, None, :] - proy, axis=2)
    k = d.argmin(1)
    u = AB[k] / np.sqrt(L2[k])[:, None]
    return d[np.arange(len(Q)), k], np.c_[-u[:, 1], u[:, 0]], A[k]


def alinear(r, P):
    suelo_r = min(_T(f)[1, 3] for f in r['floors'])
    suelo_p = float(np.percentile(P[:, 1], 1))
    h = P[:, 1] - suelo_p
    banda = P[(h > 1.3) & (h < 2.2)][:, [0, 2]]
    rng = np.random.default_rng(0)
    if len(banda) > 20000:
        banda = banda[rng.choice(len(banda), 20000, replace=False)]
    segs = segmentos(r)
    A = np.array([s.coords[0] for s in segs]); B = np.array([s.coords[1] for s in segs])
    pared_r = np.vstack([A + (B - A) * t for t in np.linspace(0, 1, 20)])
    giro0 = _orient(pared_r) - _orient(banda)
    muestra = banda[rng.choice(len(banda), 1500, replace=False)]

    def coste(q):
        d, _, _ = _dist_segs(q, A, B)
        return float(np.median(np.minimum(d, 0.5)))

    mejor = None
    centro_r = pared_r.mean(0)
    for k in range(4):
        g = giro0 + k * math.pi / 2
        R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
        q = muestra @ R.T
        base = centro_r - q.mean(0)
        for dx in np.arange(-5, 5.01, 0.25):
            for dz in np.arange(-5, 5.01, 0.25):
                t = base + [dx, dz]
                c = coste(q + t)
                if mejor is None or c < mejor[0]:
                    mejor = (c, g, t)
    c, g, t = mejor
    for _ in range(40):                                   # ICP punto a recta, en planta
        R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
        q = banda @ R.T + t
        d, n, a = _dist_segs(q, A, B)
        ok = d < 0.25
        if ok.sum() < 100:
            break
        qq, nn, aa = q[ok], n[ok], a[ok]
        res = ((qq - aa) * nn).sum(1)
        rel = qq - t
        jac = np.c_[nn[:, 0] * -rel[:, 1] + nn[:, 1] * rel[:, 0], nn[:, 0], nn[:, 1]]
        dg, dtx, dtz = np.linalg.lstsq(jac, -res, rcond=None)[0]
        g += dg; t = t + [dtx, dtz]
        if abs(dg) < 1e-6 and abs(dtx) + abs(dtz) < 1e-5:
            break
    R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
    xz = P[:, [0, 2]] @ R.T + t
    alineada = np.c_[xz[:, 0], P[:, 1] - suelo_p + suelo_r, xz[:, 1]]
    final = banda @ R.T + t
    d, _, _ = _dist_segs(final, A, B)
    return alineada, {'giro_grados': round(math.degrees(g) % 360, 2), 'desplazamiento': [round(float(v), 3) for v in t],
                      'error_mediano_m': round(float(np.median(d)), 3), 'dentro_de_3cm': round(float((d < 0.03).mean()), 2)}


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


# ---------------------------------------------------------------------------------------------------------------
# Encaje con una estancia de la planta limpia (roomplan.importar): más fiable que buscar a ciegas en toda la casa
# ---------------------------------------------------------------------------------------------------------------
def rect_orientado(q2):
    """Rectángulo principal de unos puntos de pared en planta: ángulo, centro y medidas (percentiles 2–98)."""
    th = _orient(q2)
    R = np.array([[math.cos(-th), -math.sin(-th)], [math.sin(-th), math.cos(-th)]])
    q = q2 @ R.T
    lo, hi = np.percentile(q, 2, axis=0), np.percentile(q, 98, axis=0)
    c = R.T @ ((lo + hi) / 2)
    return th, c, hi - lo


def alinear_a_planta(pl, P):
    """P: nube (Y arriba). Devuelve la nube en coordenadas de la planta (x, y, altura sobre el suelo), la estancia
    con la que encaja y la calidad del encaje."""
    suelo_p = float(np.percentile(P[:, 1], 1))
    h = P[:, 1] - suelo_p
    q_todo = np.c_[P[:, 0], -P[:, 2]]                   # planta: x, -z (como roomplan)
    banda = q_todo[(h > 1.3) & (h < 2.2)]
    rng = np.random.default_rng(0)
    if len(banda) > 20000:
        banda = banda[rng.choice(len(banda), 20000, replace=False)]
    th, c, (w, l) = rect_orientado(banda)
    A = np.array([p.a for p in pl.paredes]); B = np.array([p.b for p in pl.paredes])
    mejor = None
    for nom, est in pl.estancias.items():
        x0, y0, x1, y1 = est.bounds
        for k in range(4):
            g = -th + k * math.pi / 2                       # la planta está a escuadra con los ejes
            dims = (w, l) if k % 2 == 0 else (l, w)
            err = abs(dims[0] - (x1 - x0)) + abs(dims[1] - (y1 - y0))
            if err > 1.2:
                continue
            R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
            t = np.array([(x0 + x1) / 2, (y0 + y1) / 2]) - R @ c
            for _ in range(40):                             # ICP punto a recta
                q = banda @ R.T + t
                d, n, a = _dist_segs(q, A, B)
                ok = d < 0.25
                if ok.sum() < 100:
                    break
                qq, nn, aa = q[ok], n[ok], a[ok]
                res = ((qq - aa) * nn).sum(1); rel = qq - t
                jac = np.c_[nn[:, 0] * -rel[:, 1] + nn[:, 1] * rel[:, 0], nn[:, 0], nn[:, 1]]
                dg, dtx, dty = np.linalg.lstsq(jac, -res, rcond=None)[0]
                g += dg; t = t + [dtx, dty]
                R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
                if abs(dg) < 1e-6 and abs(dtx) + abs(dty) < 1e-5:
                    break
            d, _, _ = _dist_segs(banda @ R.T + t, A, B)
            nota = float((d < 0.03).mean())
            if mejor is None or nota > mejor[0]:
                mejor = (nota, nom, g, t, float(np.median(d)))
    nota, nom, g, t, med = mejor
    R = np.array([[math.cos(g), -math.sin(g)], [math.sin(g), math.cos(g)]])
    xy = q_todo @ R.T + t
    return np.c_[xy, h], {'estancia': nom, 'dentro_de_3cm': round(nota, 2), 'error_mediano_m': round(med, 3),
                          'medidas_escaneo': [round(float(w), 2), round(float(l), 2)]}
