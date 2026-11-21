"""Paredes de una estancia a partir de un giro con la cámara (profundidad de ARCore), aunque haya muebles.

Puntos en metros: (x, y) en planta y h en altura. Se usan solo los puntos entre la altura de los muebles y el techo
(las paredes se ven por encima de sofás, camas y mesas; la línea del techo casi nunca está tapada). Las paredes se
buscan como rectas en planta (RANSAC sucesivo) y las esquinas salen de cruzar paredes vecinas.
"""
from __future__ import annotations

import math

import numpy as np

UMBRAL = 0.025           # distancia a la recta para contar un punto como de esa pared (m)
ALTURA_MUEBLES = 1.30    # por encima de esto, casi solo hay pared (sobre el suelo)


def _rejilla(p2, lado=0.02):
    """Un punto por celda de 2 cm: que las zonas muy vistas no pesen más."""
    claves = np.floor(p2 / lado).astype(np.int64)
    _, idx = np.unique(claves, axis=0, return_index=True)
    return p2[np.sort(idx)]


def _recta(pts):
    """Recta por mínimos cuadrados totales: punto, dirección unitaria y normal."""
    c = pts.mean(0)
    _, _, vt = np.linalg.svd(pts - c)
    d = vt[0]
    return c, d, np.array([-d[1], d[0]])


def _ransac(pts, rng, intentos=400):
    mejor = None
    n = len(pts)
    for _ in range(intentos):
        i, j = rng.choice(n, 2, replace=False)
        d = pts[j] - pts[i]
        L = np.linalg.norm(d)
        if L < 0.3:
            continue
        nrm = np.array([-d[1], d[0]]) / L
        dentro = np.abs((pts - pts[i]) @ nrm) < UMBRAL
        k = int(dentro.sum())
        if mejor is None or k > mejor[0]:
            mejor = (k, dentro)
    return mejor


def paredes(puntos, suelo=None, centro=(0.0, 0.0), semilla=0):
    P = np.asarray(puntos, float)
    h = P[:, 2]
    suelo = float(np.percentile(h, 2)) if suelo is None else float(suelo)
    altos = h[h > suelo + 2.0]
    techo = None
    if len(altos) > 200:                                   # el techo: el pico de alturas por arriba
        hist, bordes = np.histogram(altos, bins=np.arange(suelo + 2.0, suelo + 4.0, 0.01))
        k = int(np.argmax(hist))
        techo = float((bordes[k] + bordes[k + 1]) / 2)
    tope = (techo - 0.12) if techo else suelo + 2.35
    banda = P[(h > suelo + ALTURA_MUEBLES) & (h < tope)]
    p2 = _rejilla(banda[:, :2])
    rng = np.random.default_rng(semilla)
    rectas = []
    resto = p2
    minimo = max(80, int(0.03 * len(p2)))
    for _ in range(14):
        if len(resto) < minimo:
            break
        r = _ransac(resto, rng)
        if not r or r[0] < minimo:
            break
        sel = resto[r[1]]
        c, d, nrm = _recta(sel)
        t = (sel - c) @ d
        if t.max() - t.min() < 0.4:                        # un trozo suelto, no una pared
            resto = resto[~r[1]]
            continue
        res = (sel - c) @ nrm
        rectas.append({'c': c, 'd': d, 'n': nrm, 'puntos': int(len(sel)), 'rms_mm': float(np.sqrt((res ** 2).mean()) * 1000),
                       't': (float(t.min()), float(t.max()))})
        resto = resto[~r[1]]
    rectas = _fusionar(rectas)
    cen = np.asarray(centro, float)
    # Una pared llega hasta el techo; el frente de un armario o una estantería, no
    for r in rectas:
        cerca = banda[np.abs((banda[:, :2] - r['c']) @ r['n']) < UMBRAL]
        r['h_max'] = float(np.percentile(cerca[:, 2], 98)) if len(cerca) else 0.0
        r['dist'] = float(abs((cen - r['c']) @ r['n']))
    if techo:
        rectas = [r for r in rectas if r['h_max'] > techo - 0.30] or rectas
    # Dos paralelas en el mismo lado: la pared es la de más atrás
    rectas.sort(key=lambda r: -r['dist'])
    quedan = []
    for r in rectas:
        lado = np.sign((r['c'] - cen) @ r['n'])
        if any(abs(r['d'] @ q['d']) > math.cos(math.radians(8)) and np.sign((q['c'] - cen) @ q['n']) * lado *
               np.sign(r['n'] @ q['n']) > 0 for q in quedan):
            continue
        quedan.append(r)
    rectas = quedan
    # Orden alrededor del centro del giro y esquinas = cruce de paredes vecinas
    for r in rectas:
        m = r['c'] + r['d'] * (r['t'][0] + r['t'][1]) / 2
        r['ang'] = math.atan2(m[1] - cen[1], m[0] - cen[0])
    rectas.sort(key=lambda r: r['ang'])
    esquinas = []
    for a, b in zip(rectas, rectas[1:] + rectas[:1]):
        x = _cruce(a, b)
        if x is not None:
            esquinas.append(x)
    return {
        'suelo': suelo, 'techo': techo, 'altura': (techo - suelo) if techo else None,
        'paredes': [{'punto': r['c'].tolist(), 'dir': r['d'].tolist(), 'puntos': r['puntos'], 'rms_mm': round(r['rms_mm'], 1),
                     'tramo': [(r['c'] + r['d'] * t).tolist() for t in r['t']]} for r in rectas],
        'esquinas': [list(map(float, e)) for e in esquinas],
        'usados': int(len(p2)), 'total': int(len(P)),
        'muestra': p2[rng.choice(len(p2), min(2500, len(p2)), replace=False)].round(3).tolist() if len(p2) else [],
    }


def _fusionar(rectas):
    out = []
    for r in rectas:
        for o in out:
            if abs(r['d'] @ o['d']) > math.cos(math.radians(3)) and abs((r['c'] - o['c']) @ o['n']) < 0.05:
                o['puntos'] += r['puntos']
                break
        else:
            out.append(r)
    return out


def _cruce(a, b):
    den = a['d'][0] * b['d'][1] - a['d'][1] * b['d'][0]
    if abs(den) < math.sin(math.radians(20)):              # casi paralelas: no hay esquina entre ellas
        return None
    w = b['c'] - a['c']
    s = (w[0] * b['d'][1] - w[1] * b['d'][0]) / den
    return a['c'] + a['d'] * s
