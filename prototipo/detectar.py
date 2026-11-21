"""Lo que RoomPlan simplifica, detectado con la nube de puntos de las fotos del mismo escaneo (mismo sistema).

Para cada pared del escaneo: puntos de la nube cerca de su plano, a lo largo de su largo y entre suelo y techo. La
cara real de la pared es donde se acumulan los puntos; donde, en un tramo, se acumulan por detrás del plano hay un
hueco o retranqueo, y donde algo sobresale de suelo a techo, un pilar. En el techo de cada estancia, una franja más
baja es una viga o un descuelgue. Una pared inclinada sin puntos que la respalden es sospechosa.

    python detectar.py <room.json> <nube.ply> [fotos.jsonl]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

PASO = 0.10          # m a lo largo de la pared
UMBRAL = 0.06        # m: más que esto por detrás o por delante del plano cuenta
MIN_TRAMO = 0.30     # m: tramo mínimo de un hueco o un saliente


def _T(s):
    return np.array(s['transform'], float).reshape(4, 4).T


def paredes(r, P, camaras=None, suelo=None):
    suelo = suelo if suelo is not None else min(_T(f)[1, 3] for f in r['floors'])
    out = []
    for w in r['walls']:
        T = _T(w); c = T[:3, 3]; u = T[:3, 0]; n = T[:3, 2]; L, H = w['dimensions'][0], w['dimensions'][1]
        rel = P - c
        t = rel @ u; d = rel @ n; h = P[:, 1] - suelo
        sel = (np.abs(t) < L / 2 - 0.05) & (np.abs(d) < 0.6) & (h > 0.3) & (h < H - 0.2)
        if sel.sum() < 30:
            out.append({'pared': w['identifier'], 'largo': L, 'puntos': int(sel.sum()), 'veredicto': 'sin datos'})
            continue
        # El lado de dentro: hacia donde estaban las cámaras
        signo = 1.0
        if camaras is not None and len(camaras):
            cerca = camaras[np.abs((camaras - c) @ u) < L / 2 + 1]
            if len(cerca):
                signo = 1.0 if np.median((cerca - c) @ n) > 0 else -1.0
        detras = -signo * d[sel]                       # > 0: por detrás del plano (dentro del muro o un hueco)
        ts, hs = t[sel], h[sel]
        cara = float(np.median(detras))                # dónde está de verdad la pared (en conjunto)
        tramos = []
        bins = np.arange(-L / 2, L / 2 + PASO, PASO)
        perfil = []
        for a, b in zip(bins, bins[1:]):
            m = (ts >= a) & (ts < b)
            if m.sum() < 5:
                perfil.append(np.nan); continue
            perfil.append(float(np.median(detras[m])))
        perfil = np.array(perfil)
        # Huecos (por detrás) y salientes (por delante) respecto a la cara
        for clase, cond in (('hueco', perfil - cara > UMBRAL), ('saliente', cara - perfil > UMBRAL)):
            i = 0
            while i < len(cond):
                if cond[i]:
                    j = i
                    while j + 1 < len(cond) and cond[j + 1]:
                        j += 1
                    largo = (j - i + 1) * PASO
                    if largo >= MIN_TRAMO:
                        fondo = float(np.nanmedian(np.abs(perfil[i:j + 1] - cara)))
                        tramos.append({'tipo': clase, 'desde': round(float(bins[i] + L / 2), 2), 'ancho': round(largo, 2),
                                       'fondo': round(fondo, 3)})
                    i = j + 1
                else:
                    i += 1
        out.append({'pared': w['identifier'], 'largo': round(L, 3), 'puntos': int(sel.sum()),
                    'desvio_cara': round(cara, 3), 'tramos': tramos})
    return out


def techos(r, P, suelo=None, celda=0.20):
    """Altura del techo por celdas: devuelve las celdas claramente más bajas que la moda (vigas, descuelgues)."""
    suelo = suelo if suelo is not None else min(_T(f)[1, 3] for f in r['floors'])
    h = P[:, 1] - suelo
    alto = P[h > 1.9]
    if len(alto) < 100:
        return {'veredicto': 'sin datos de techo'}
    k = np.floor(alto[:, [0, 2]] / celda).astype(int)
    celdas = {}
    for key, y in zip(map(tuple, k), alto[:, 1] - suelo):
        celdas.setdefault(key, []).append(y)
    techo = {c: float(np.percentile(v, 95)) for c, v in celdas.items() if len(v) >= 8}
    if not techo:
        return {'veredicto': 'sin datos de techo'}
    moda = float(np.median(list(techo.values())))
    bajas = {c: t for c, t in techo.items() if moda - t > 0.08}
    return {'techo': round(moda, 3), 'celdas': len(techo), 'bajas': len(bajas),
            'zonas_bajas': [[round(c[0] * celda, 2), round(c[1] * celda, 2), round(t, 2)] for c, t in list(bajas.items())[:40]]}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    from reconstruir import leer_ply
    r = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    P = leer_ply(Path(sys.argv[2]))
    P = P[np.isfinite(P).all(1)]
    cams = None
    if len(sys.argv) > 3:
        cams = np.array([np.array(json.loads(l)['vista']).reshape(4, 4).T[:3, 3]
                         for l in Path(sys.argv[3]).read_text(encoding='utf-8').splitlines() if l.strip()])
    for p in paredes(r, P, cams):
        if p.get('tramos') or p.get('veredicto'):
            print(p)
    print(techos(r, P))
