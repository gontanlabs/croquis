"""Referencia completa: las nubes del láser Faro de ARKitScenes, muestreadas y encajadas en el sistema del iPad.

Cada nube del Faro pesa unos 2 GB (43 millones de puntos de 44 bytes). Se leen trozos repartidos por todo el fichero
(peticiones HTTP por rangos): una muestra de un 5 %, en trozos cortos para que quede repartida. Los puntos ya vienen en el sistema común de la visita
(comprobado: las coordenadas crudas coinciden con la traslación de su `_pose.txt`, que no hay que volver a aplicar).

Para pasarlas al sistema del iPad se encajan, con un movimiento rígido, sobre la nube del iPad: el sesgo del sensor
(todas las caras hacia dentro) no se puede absorber con un movimiento rígido y sigue midiéndose.

    python banco/faro.py <escaneo>     → <escaneo>/faro.npy (x, y arriba, z; sistema del iPad) e informe del encaje
"""
from __future__ import annotations

import csv
import math
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.signal import fftconvolve
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arkit  # noqa: E402

URL = 'https://docs-assets.developer.apple.com/ml-research/datasets/arkitscenes/v1/raw/laser_scanner_point_clouds'
RAIZ = Path(__file__).resolve().parents[2] / 'levantamientos' / 'arkitscenes'
DT = np.dtype([('x', '<f8'), ('y', '<f8'), ('z', '<f8'), ('r', 'u1'), ('g', 'u1'), ('b', 'u1'), ('a', 'u1'),
               ('q', '<f8'), ('rad', '<f8')])


def _get(url, rango=None):
    req = urllib.request.Request(url, headers={'Range': f'bytes={rango[0]}-{rango[1]}'} if rango else {})
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception:
            if intento == 3:
                raise


def muestra(visita, ident, trozos=12000, por_trozo=200):
    dst = RAIZ / 'faro' / str(visita) / f'{ident}.npy'
    if dst.exists():
        return np.load(dst).astype(float)
    dst.parent.mkdir(parents=True, exist_ok=True)
    url = f'{URL}/{visita}/{ident}.ply'
    cab = _get(url, (0, 4000))
    fin = cab.index(b'\n', cab.index(b'end_header')) + 1
    texto = cab[:fin].decode('ascii')
    n = int(next(l.split()[2] for l in texto.splitlines() if l.startswith('element vertex')))
    assert 'property double quality' in texto and 'property double radius' in texto and DT.itemsize == 44
    inicios = np.linspace(0, n - por_trozo, trozos).astype(np.int64)

    def leer(i0):
        v = np.frombuffer(_get(url, (fin + i0 * 44, fin + (i0 + por_trozo) * 44 - 1)), DT)
        return np.c_[v['x'], v['y'], v['z']]
    with ThreadPoolExecutor(16) as ex:
        P = np.vstack(list(ex.map(leer, inicios)))
    np.save(dst, P.astype(np.float32))
    return P


def visita_de(video):
    for r in csv.DictReader(open(RAIZ / 'metadata.csv')):
        if r['video_id'] == str(video):
            return r['visit_id']


def nubes_visita(visita):
    ids = [r['laser_scanner_point_clouds_id'] for r in csv.DictReader(open(RAIZ / 'mapping.csv'))
           if r['visit_id'] == str(visita)]
    return np.vstack([muestra(visita, i) for i in ids]), ids


def _rot_y(g):
    return np.array([[math.cos(g), 0, math.sin(g)], [0, 1, 0], [-math.sin(g), 0, math.cos(g)]])


def _vox(P, v):
    _, i = np.unique(np.floor(P / v).astype(np.int64), axis=0, return_index=True)
    return P[i]


def encajar(F, Lref, voxel=0.02):
    """F: Faro (Y arriba, sistema de la visita); Lref: láser proyectado (sistema del iPad). Se busca el movimiento
    referencia → Faro: giro en Y de 2 en 2° con la planta por correlación de rejillas y la altura por el suelo; después
    ICP punto a punto con giro libre. Devuelve el Faro en el sistema del iPad."""
    Fv, Lv = _vox(F, voxel), _vox(Lref, voxel)
    arbol = cKDTree(Fv)
    rng = np.random.default_rng(0)
    Ls = Lv[rng.choice(len(Lv), min(20000, len(Lv)), replace=False)]
    dy = 0.0                                                  # la altura se busca después de la planta
    celda = 0.10
    x0, z0 = Fv[:, 0].min() - 4, Fv[:, 2].min() - 4
    nx, nz = int((Fv[:, 0].max() + 4 - x0) / celda) + 1, int((Fv[:, 2].max() + 4 - z0) / celda) + 1

    def rejilla(P, ax, az, mx, mz):
        g = np.zeros((mx, mz)); i = ((P[:, 0] - ax) / celda).astype(int); k = ((P[:, 2] - az) / celda).astype(int)
        ok = (i >= 0) & (i < mx) & (k >= 0) & (k < mz); np.add.at(g, (i[ok], k[ok]), 1)
        return np.minimum(g, 5)
    GF = rejilla(Fv, x0, z0, nx, nz)
    arbol2 = cKDTree(Fv[:, [0, 2]])                           # en la búsqueda, solo la planta (la altura va luego)
    mejor = None
    for gdeg in np.arange(0, 360, 2):
        R = _rot_y(math.radians(gdeg))
        Lr = Ls @ R.T
        c = np.array([Lr[:, 0].min(), Lr[:, 2].min()])
        mx, mz = int((Lr[:, 0].max() - c[0]) / celda) + 1, int((Lr[:, 2].max() - c[1]) / celda) + 1
        if mx >= nx or mz >= nz:
            continue
        GL = rejilla(Lr, c[0], c[1], mx, mz)
        corr = fftconvolve(GF, GL[::-1, ::-1], mode='valid')
        i, k = np.unravel_index(np.argmax(corr), corr.shape)
        t = np.array([x0 + i * celda - c[0], dy, z0 + k * celda - c[1]])
        d, _ = arbol2.query((Lr + t)[:, [0, 2]], distance_upper_bound=0.10)
        nota = float(np.isfinite(d).mean())
        if mejor is None or nota > mejor[0]:
            mejor = (nota, gdeg, t)
    nota, gdeg, t = mejor
    Rt, tt = _rot_y(math.radians(gdeg)), t
    # Altura: correlación de los histogramas de altura (cm) del Faro bajo la huella de la referencia y de la referencia
    Lr = Lv @ Rt.T + tt
    huella = cKDTree(Lr[:, [0, 2]])
    dh, _ = huella.query(Fv[:, [0, 2]], distance_upper_bound=0.05)
    Fh = Fv[np.isfinite(dh)][:, 1]
    lo = min(Fh.min(), Lr[:, 1].min()) - 1; hi = max(Fh.max(), Lr[:, 1].max()) + 1
    b = np.arange(lo, hi, 0.01)
    hF, _ = np.histogram(Fh, b); hL, _ = np.histogram(Lr[:, 1], b)
    cc = np.correlate(hF.astype(float), hL.astype(float), 'full')
    tt = tt + np.array([0, (np.argmax(cc) - (len(hL) - 1)) * 0.01, 0])
    d, _ = arbol.query(Ls @ Rt.T + tt, distance_upper_bound=0.15)
    nota = float(np.isfinite(d).mean())
    A = Lv[rng.choice(len(Lv), min(80000, len(Lv)), replace=False)]
    for umbral in (0.20, 0.10, 0.05, 0.03, 0.02, 0.015):
        for _ in range(10):
            Q = A @ Rt.T + tt
            d, j = arbol.query(Q, distance_upper_bound=umbral)
            ok = np.isfinite(d)
            if ok.sum() < 500:
                break
            X, Y = Q[ok], Fv[j[ok]]
            mx_, my_ = X.mean(0), Y.mean(0)
            U, _, Vt = np.linalg.svd((X - mx_).T @ (Y - my_))
            D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
            dR = Vt.T @ D @ U.T
            Rt = dR @ Rt; tt = dR @ (tt - mx_) + my_
    Q = A @ Rt.T + tt
    _, vec = arbol.query(Q, k=12, distance_upper_bound=0.1)
    d = np.full(len(Q), np.inf)
    for i in range(len(Q)):
        v = vec[i][vec[i] < len(Fv)]
        if len(v) < 6:
            continue
        N = Fv[v]; m = N.mean(0); _, _, vt = np.linalg.svd(N - m, full_matrices=False)
        d[i] = abs((Q[i] - m) @ vt[2])                         # distancia al plano local del Faro
    fin = d[np.isfinite(d)]
    info = {'giro_inicial': int(gdeg), 'solape_inicial': round(nota, 2), 'dentro_1cm': round(float((d < 0.01).mean()), 2),
            'dentro_2cm': round(float((d < 0.02).mean()), 2), 'mediana_mm': round(float(np.median(fin)) * 1000, 1)}
    return (F - tt) @ Rt, info


def preparar(c: Path):
    c = Path(c)
    visita = visita_de(c.name)
    F, ids = nubes_visita(visita)
    F = F[np.isfinite(F).all(1)]
    F = np.c_[F[:, 0], F[:, 2], -F[:, 1]]                     # el Faro, como el iPad: Z arriba → Y arriba
    _, P = arkit.cargar(c)
    # Encaje rígido del Faro sobre la nube del iPad (completa). Un movimiento rígido no puede absorber que el iPad
    # meta todas las caras hacia dentro, así que el sesgo del sensor sigue midiéndose. (Encajar con el láser
    # proyectado en los fotogramas dejaba ~1 cm de incertidumbre y fallaba en 42444946.)
    Fi, info = encajar(F, P.astype(float))
    np.save(c / 'faro.npy', Fi.astype(np.float32))
    info.update({'visita': visita, 'nubes_faro': len(ids), 'puntos': len(Fi)})
    return info


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for a in sys.argv[1:]:
        print(Path(a).name, preparar(Path(a)), flush=True)
