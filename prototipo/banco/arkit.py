"""Banco de pruebas con ARKitScenes (Apple): escaneos de iPad Pro con LiDAR y, de referencia, el láser Faro.

Cada escaneo (carpeta con lowres_depth/, confidence/, lowres_wide_intrinsics/, lowres_wide.traj y highres_depth/):
- `nube(c, 'ipad')`: la nube del LiDAR del iPad (profundidad 256×192 de ARKit, solo confianza alta), en el sistema
  del mundo del escaneo pasado a Y arriba (ARKitScenes lo da con Z arriba: comprobado con el suelo y el techo), metros.
- `nube(c, 'laser')`: la referencia: la malla del láser Faro proyectada en los fotogramas del iPad (1920×1440), en el
  mismo sistema.
- `paredes_referencia(L)`: las paredes de la referencia (planos verticales).
- `error_paredes(P, paredes)`: para cada pared, dónde pone su cara la nube del iPad respecto a la referencia.

Convenciones, según el código de Apple (threedod/benchmark_scripts/utils/tenFpsDataLoader.py): cada línea de la
trayectoria es tiempo, giro (eje-ángulo, rad) y traslación de mundo a cámara; la pose es su inversa. La cámara es la de
OpenCV (x derecha, y abajo, z adelante). Profundidad en PNG de 16 bits, en milímetros. Licencia de los datos: Apple,
no comercial (docs/DISENO.md).

    python banco/arkit.py <carpeta del escaneo> [...]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree


def _rodrigues(r):
    th = np.linalg.norm(r)
    if th < 1e-12:
        return np.eye(3)
    k = r / th; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def leer_traj(c: Path):
    ts, poses = [], []
    for l in (c / 'lowres_wide.traj').read_text().split('\n'):
        v = l.split()
        if len(v) != 7:
            continue
        E = np.eye(4); E[:3, :3] = _rodrigues(np.array(v[1:4], float)); E[:3, 3] = np.array(v[4:7], float)
        ts.append(float(v[0])); poses.append(np.linalg.inv(E))
    return np.array(ts), np.array(poses)


def _intrinsecos(c: Path, ts, carpeta='lowres_wide_intrinsics'):
    """Los del fotograma más cercano (w, h, fx, fy, cx, cy). Para la referencia (1920×1440), los de `wide_intrinsics`:
    los de lowres escalados ×7,5 tienen la focal un 0,8 % mayor (comprobado en 42444966)."""
    fichs = sorted((c / carpeta).glob('*.pincam'))
    t = np.array([float(f.stem.split('_')[1]) for f in fichs])
    return np.loadtxt(fichs[int(np.argmin(np.abs(t - ts)))])


def nube(c: Path, fuente='ipad', cada=10, voxel=0.01):
    c = Path(c)
    T, poses = leer_traj(c)
    carpeta = c / ('lowres_depth' if fuente == 'ipad' else 'highres_depth')
    fichs = sorted(carpeta.glob('*.png'))[::cada]
    pts = []
    for f in fichs:
        ts = float(f.stem.split('_')[1])
        k = int(np.argmin(np.abs(T - ts)))
        if abs(T[k] - ts) > 0.02:
            continue
        D = np.asarray(Image.open(f), dtype=np.float64) / 1000.0
        carp = 'wide_intrinsics' if fuente != 'ipad' and (c / 'wide_intrinsics').exists() else 'lowres_wide_intrinsics'
        w, h, fx, fy, cx, cy = _intrinsecos(c, ts, carp)
        esc = D.shape[1] / w                             # highres: los intrínsecos de lowres, a escala
        if fuente == 'ipad':
            cf = c / 'confidence' / f.name
            if cf.exists():
                D[np.asarray(Image.open(cf)) < 2] = 0
            paso = 1
        else:
            paso = 4                                     # 480×360 puntos por fotograma bastan
        v, u = np.mgrid[0:D.shape[0]:paso, 0:D.shape[1]:paso]
        d = D[v, u]; ok = (d > 0.1) & (d < 6)
        x = (u[ok] - cx * esc) / (fx * esc) * d[ok]; y = (v[ok] - cy * esc) / (fy * esc) * d[ok]
        Pc = np.c_[x, y, d[ok], np.ones(ok.sum())]
        pts.append((poses[k] @ Pc.T).T[:, :3])
    P = np.vstack(pts)
    P = np.c_[P[:, 0], P[:, 2], -P[:, 1]]               # el mundo de ARKitScenes tiene Z arriba: se pasa a Y arriba
    if voxel:
        _, i = np.unique(np.floor(P / voxel).astype(np.int64), axis=0, return_index=True)
        P = P[i]
    return P


def paredes_referencia(L, tol=0.01, minimo=1.0, max_paredes=20, semilla=0, quitar=0.05):
    """Planos verticales (Y arriba) de la nube de referencia, por RANSAC en planta: normal, distancia, tramo."""
    rng = np.random.default_rng(semilla)
    suelo, techo = np.percentile(L[:, 1], [1, 99])
    Q = L[(L[:, 1] > suelo + 0.3) & (L[:, 1] < techo - 0.3)][:, [0, 2]]
    out = []
    for _ in range(max_paredes):
        if len(Q) < 2000:
            break
        mejor = None
        for _ in range(400):
            a, b = Q[rng.integers(len(Q), size=2)]
            d = b - a; nd = np.linalg.norm(d)
            if nd < 0.3:
                continue
            n = np.array([-d[1], d[0]]) / nd; o = n @ a
            ins = np.abs(Q @ n - o) < tol
            if mejor is None or ins.sum() > mejor[0]:
                mejor = (int(ins.sum()), n, o)
        cnt, n, o = mejor
        ins = np.abs(Q @ n - o) < tol
        # afinar con mínimos cuadrados y quedarse con el tramo continuo más largo
        A = Q[ins]; cen = A.mean(0); _, _, vt = np.linalg.svd(A - cen, full_matrices=False); n = vt[1]; o = n @ cen
        ins = np.abs(Q @ n - o) < tol
        u = np.array([n[1], -n[0]]); t = np.sort(Q[ins] @ u)
        cortes = np.flatnonzero(np.diff(t) > 0.3)
        tramos = np.split(t, cortes + 1)
        tr = max(tramos, key=len)
        if tr[-1] - tr[0] >= minimo:
            out.append({'n': n, 'o': float(o), 't0': float(tr[0]), 't1': float(tr[-1]), 'puntos': len(tr)})
        Q = Q[np.abs(Q @ n - o) >= quitar]                 # fuera la pared entera (que no salga dos veces)
    return out


def error_paredes(P, paredes, banda=0.10):
    """Para cada pared de referencia: los puntos de P a menos de `banda` de su plano, dentro de su tramo. La mediana
    de su distancia con signo es dónde pone la cara P (error), y el percentil 90 de |d|, el grosor de su nube."""
    suelo, techo = np.percentile(P[:, 1], [1, 99])
    Q = P[(P[:, 1] > suelo + 0.3) & (P[:, 1] < techo - 0.3)][:, [0, 2]]
    res = []
    for w in paredes:
        n, o = w['n'], w['o']; u = np.array([n[1], -n[0]])
        d = Q @ n - o; t = Q @ u
        sel = (np.abs(d) < banda) & (t > w['t0'] + 0.1) & (t < w['t1'] - 0.1)
        if sel.sum() < 200:
            res.append(None); continue
        res.append({'largo': round(w['t1'] - w['t0'], 2), 'puntos': int(sel.sum()),
                    'error_mm': round(float(np.median(d[sel])) * 1000, 1),
                    'dispersion_mm': round(float(np.percentile(np.abs(d[sel] - np.median(d[sel])), 90)) * 1000, 1)})
    return res


def por_fotograma(c: Path, cada=5):
    """Error del sensor sin la posición: en cada fotograma con referencia, profundidad del iPad menos la del láser,
    por tramos de distancia."""
    c = Path(c)
    dif, dist = [], []
    for h in sorted((c / 'highres_depth').glob('*.png'))[::cada]:
        l = c / 'lowres_depth' / h.name
        if not l.exists():
            continue
        H = np.asarray(Image.open(h), dtype=float); L = np.asarray(Image.open(l), dtype=float)
        cf = c / 'confidence' / h.name
        Cf = np.asarray(Image.open(cf)) if cf.exists() else np.full(L.shape, 2)
        Hs = H[(np.arange(L.shape[0]) + 0.5).astype(int) * H.shape[0] // L.shape[0]][:, (np.arange(L.shape[1]) + 0.5).astype(int) * H.shape[1] // L.shape[1]]
        m = (Hs > 0) & (L > 0) & (Cf >= 2)
        dif.append(L[m] - Hs[m]); dist.append(Hs[m])
    dif, dist = np.concatenate(dif) / 1000, np.concatenate(dist) / 1000
    out = {}
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (4, 6)):
        m = (dist >= a) & (dist < b)
        if m.sum() > 1000:
            out[f'{a}-{b} m'] = {'sesgo_mm': round(float(np.median(dif[m])) * 1000, 1),
                                'p90_mm': round(float(np.percentile(np.abs(dif[m] - np.median(dif[m])), 90)) * 1000, 1)}
    return out


def cargar(c: Path):
    """Las dos nubes, guardadas en la carpeta del escaneo la primera vez (tardan unos minutos)."""
    c = Path(c); f = c / 'nubes.npz'
    if f.exists():
        z = np.load(f); return z['L'], z['P']
    L = nube(c, 'laser', cada=3); P = nube(c, 'ipad', cada=10)
    np.savez(f, L=L.astype(np.float32), P=P.astype(np.float32))
    return L, P


def informe(c: Path):
    c = Path(c)
    L, P = cargar(c)
    L, P = L.astype(float), P.astype(float)
    res = {'escaneo': c.name, 'puntos_laser': len(L), 'puntos_ipad': len(P)}
    res['sensor_por_distancia'] = por_fotograma(c)
    dist, _ = cKDTree(L).query(P, distance_upper_bound=0.5)
    dist = dist[np.isfinite(dist)]
    res['ipad_a_laser_mm'] = {'mediana': round(float(np.median(dist)) * 1000, 1), 'p90': round(float(np.percentile(dist, 90)) * 1000, 1)}
    paredes = paredes_referencia(L)
    autolaser = [e for e in error_paredes(L, paredes) if e]
    errs = [e for e in error_paredes(P, paredes) if e]
    res['grosor_nube_laser_mm'] = round(float(np.median([e['dispersion_mm'] for e in autolaser])), 1) if autolaser else None
    res['caras'] = errs
    if errs:
        a = np.abs([e['error_mm'] for e in errs])
        res['caras_resumen'] = {'n': len(errs), 'mediana_mm': round(float(np.median(a)), 1),
                                'p90_mm': round(float(np.percentile(a, 90)), 1), 'max_mm': round(float(a.max()), 1)}
    return res


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    import json
    for a in sys.argv[1:]:
        r = informe(Path(a))
        (Path(a) / 'banco.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
        print(json.dumps({k: v for k, v in r.items() if k != 'caras'}, ensure_ascii=False))
