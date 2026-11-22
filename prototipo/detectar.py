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


def estancia(pol, Q, paso=0.05, umbral=0.04, min_tramo=0.20):
    """Paredes de una estancia (polígono de la planta) contra una nube LiDAR ya en coordenadas de planta
    (x, y, altura). Para cada lado: dónde está de verdad su cara (desvío respecto al dibujo), y tramos de hueco
    (la cara real se va hacia fuera) o saliente (hacia dentro), ignorando muebles (solo puntos por encima de 1,6 m
    o que llegan cerca del techo)."""
    from shapely.geometry import Point as Pt
    cs = list(pol.exterior.coords)[:-1]
    if pol.exterior.is_ccw is False:
        cs = cs[::-1]
    techo = float(np.percentile(Q[:, 2], 99))
    out = []
    for a, b in zip(cs, cs[1:] + cs[:1]):
        a, b = np.array(a), np.array(b); L = np.linalg.norm(b - a)
        if L < 0.25:
            continue
        u = (b - a) / L; n = np.array([u[1], -u[0]])             # contorno antihorario: n apunta hacia fuera
        rel = Q[:, :2] - a
        t = rel @ u; d = rel @ n; h = Q[:, 2]
        sel = (t > 0.03) & (t < L - 0.03) & (np.abs(d) < 0.5) & (h > 1.6) & (h < techo - 0.15)
        if sel.sum() < 50:
            out.append({'lado': [a.round(3).tolist(), b.round(3).tolist()], 'largo': round(L, 3), 'veredicto': 'sin datos'})
            continue
        ts, ds = t[sel], d[sel]
        bins = np.arange(0, L + paso, paso)
        perfil = np.array([np.median(ds[(ts >= x0) & (ts < x1)]) if ((ts >= x0) & (ts < x1)).sum() >= 8 else np.nan
                           for x0, x1 in zip(bins, bins[1:])])
        cara = float(np.nanmedian(perfil))                         # > 0: la pared real está más afuera que el dibujo
        tramos = []
        for clase, cond in (('hueco', perfil - cara > umbral), ('saliente', cara - perfil > umbral)):
            cond = np.nan_to_num(cond.astype(float)) > 0
            i = 0
            while i < len(cond):
                if cond[i]:
                    j = i
                    while j + 1 < len(cond) and cond[j + 1]:
                        j += 1
                    if (j - i + 1) * paso >= min_tramo:
                        tramos.append({'tipo': clase, 'desde': round(float(bins[i]), 2), 'ancho': round((j - i + 1) * paso, 2),
                                       'fondo': round(float(np.nanmedian(np.abs(perfil[i:j + 1] - cara))), 3)})
                    i = j + 1
                else:
                    i += 1
        out.append({'lado': [a.round(3).tolist(), b.round(3).tolist()], 'largo': round(L, 3), 'puntos': int(sel.sum()),
                    'desvio_cara': round(cara, 3), 'tramos': tramos})
    # Techo dentro de la estancia: altura dominante y zonas más bajas (vigas, descuelgues)
    dentro = np.array([pol.buffer(-0.15).contains(Pt(x, y)) for x, y in Q[::7, :2]])
    sub = Q[::7][dentro]
    alto = sub[sub[:, 2] > techo - 0.6]
    techo_info = {}
    if len(alto) > 200:
        k = np.floor(alto[:, :2] / 0.1).astype(int)
        celdas = {}
        for key, z in zip(map(tuple, k), alto[:, 2]):
            celdas.setdefault(key, []).append(z)
        tc = {c: float(np.percentile(v, 90)) for c, v in celdas.items() if len(v) >= 5}
        moda = float(np.median(list(tc.values())))
        bajas = [c for c, z in tc.items() if moda - z > 0.06]
        techo_info = {'altura': round(moda, 3), 'celdas': len(tc), 'celdas_bajas': len(bajas),
                      'zona_baja': ([round(min(c[0] for c in bajas) * 0.1, 2), round(min(c[1] for c in bajas) * 0.1, 2),
                                     round((max(c[0] for c in bajas) + 1) * 0.1, 2), round((max(c[1] for c in bajas) + 1) * 0.1, 2)]
                                    if bajas else None)}
    return out, techo_info


def contorno_real(pol_dibujo, Q, celda=0.02):
    """La forma real de una estancia con la nube LiDAR: los puntos de la franja pegada al techo (donde no llegan los
    muebles) dibujan sus paredes; se rellena desde dentro y se simplifica a tramos rectos a escuadra."""
    from shapely.geometry import Polygon as Pol, box
    from shapely.ops import unary_union
    techo = float(np.percentile(Q[:, 2], 99))
    franja = Q[(Q[:, 2] > techo - 0.30) & (Q[:, 2] < techo - 0.05)][:, :2]
    x0, y0, x1, y1 = pol_dibujo.buffer(0.6).bounds
    nx, ny = int((x1 - x0) / celda) + 1, int((y1 - y0) / celda) + 1
    rejilla = np.zeros((ny, nx), bool)
    ij = np.floor((franja - [x0, y0]) / celda).astype(int)
    ok = (ij[:, 0] >= 0) & (ij[:, 0] < nx) & (ij[:, 1] >= 0) & (ij[:, 1] < ny)
    cuenta = np.zeros((ny, nx), int)
    np.add.at(cuenta, (ij[ok, 1], ij[ok, 0]), 1)
    rejilla = cuenta >= 3
    # cerrar huecos pequeños de la pared (3 celdas)
    from numpy.lib.stride_tricks import sliding_window_view as ventana
    def dilatar(m, r):
        p = np.pad(m, r); return ventana(p, (2 * r + 1, 2 * r + 1)).any(axis=(2, 3))
    def erosionar(m, r):
        p = np.pad(m, r, constant_values=True); return ventana(p, (2 * r + 1, 2 * r + 1)).all(axis=(2, 3))
    muro = erosionar(dilatar(rejilla, 4), 2)
    # relleno desde el centro de la estancia
    c = pol_dibujo.representative_point()          # semilla: la celda libre más cercana (no una lámpara del techo)
    jj, ii = np.nonzero(~muro)
    k = np.argmin((jj - (c.y - y0) / celda) ** 2 + (ii - (c.x - x0) / celda) ** 2)
    sj, si = int(jj[k]), int(ii[k])
    dentro = np.zeros_like(muro); pila = [(sj, si)]
    while pila:
        j, i = pila.pop()
        if j < 0 or j >= ny or i < 0 or i >= nx or dentro[j, i] or muro[j, i]:
            continue
        dentro[j, i] = True
        pila += [(j + 1, i), (j - 1, i), (j, i + 1), (j, i - 1)]
    if dentro[0, :].any() or dentro[-1, :].any() or dentro[:, 0].any() or dentro[:, -1].any():
        return None, 'el contorno no cierra'
    filas = []
    for j in range(ny):
        fila = dentro[j]
        if not fila.any():
            continue
        cambios = np.flatnonzero(np.diff(np.r_[0, fila.astype(int), 0]))
        for a, b in zip(cambios[::2], cambios[1::2]):
            filas.append(box(x0 + a * celda, y0 + j * celda, x0 + b * celda, y0 + (j + 1) * celda))
    forma = unary_union(filas).buffer(celda / 2).buffer(-celda / 2)
    if forma.geom_type != 'Polygon':
        forma = max(forma.geoms, key=lambda g: g.area)
    # el relleno llega hasta la cara de los puntos de pared (medio grueso de la franja de puntos): se compensa
    forma = forma.buffer(celda * 1.5, join_style='mitre')
    simple = forma.simplify(0.03)
    return _a_escuadra(simple), 'ok'


def _a_escuadra(pol, tol=8.0, minimo=0.04):
    """Lados casi horizontales o verticales, a escuadra: cada lado es una recta (y = cte o x = cte, la media de sus
    extremos) y las esquinas son los cruces de rectas vecinas; los lados consecutivos iguales se unen y los de menos
    de `minimo` se quitan."""
    from shapely.geometry import Polygon as Pol
    cs = np.array(pol.exterior.coords)[:-1]
    lados = []
    for i in range(len(cs)):
        a, b = cs[i], cs[(i + 1) % len(cs)]
        d = b - a
        if np.linalg.norm(d) < 1e-9:
            continue
        ang = abs(math.degrees(math.atan2(d[1], d[0]))) % 180
        if min(ang, 180 - ang) < tol:
            lados.append(['H', (a[1] + b[1]) / 2, np.linalg.norm(d)])
        elif abs(ang - 90) < tol:
            lados.append(['V', (a[0] + b[0]) / 2, np.linalg.norm(d)])
        else:
            lados.append(['D', (a, b), np.linalg.norm(d)])
    # unir consecutivos del mismo tipo (media ponderada por largo)
    cambiado = True
    while cambiado and len(lados) > 3:
        cambiado = False
        for i in range(len(lados)):
            j = (i + 1) % len(lados)
            if lados[i][0] == lados[j][0] and lados[i][0] in 'HV':
                L = lados[i][2] + lados[j][2]
                lados[i] = [lados[i][0], (lados[i][1] * lados[i][2] + lados[j][1] * lados[j][2]) / L, L]
                del lados[j]; cambiado = True; break
    pts = []
    for i in range(len(lados)):
        p, q = lados[i - 1], lados[i]
        if p[0] == 'H' and q[0] == 'V':
            pts.append((q[1], p[1]))
        elif p[0] == 'V' and q[0] == 'H':
            pts.append((p[1], q[1]))
        else:                                          # con una diagonal: el extremo original
            pts.append(tuple(q[1][0]) if q[0] == 'D' else tuple(p[1][1]))
    poly = Pol(pts).buffer(0)
    if poly.is_empty:
        return pol
    if poly.geom_type != 'Polygon':
        poly = max(poly.geoms, key=lambda g: g.area)
    return poly.simplify(0.005)


# ---------------------------------------------------------------------------------------------------------------
# Corregir el esqueleto de RoomPlan con una nube LiDAR (en coordenadas de planta: x, y, altura sobre el suelo)
# ---------------------------------------------------------------------------------------------------------------
def _picos(v, rejilla):
    """Picos de un histograma de distancias a la pared (de fuera a dentro), con su centro afinado. Del pico y no del
    borde: el ruido del sensor ensancha la banda de puntos y el borde la sacaba 1–2 cm hacia fuera (banco)."""
    hist, _ = np.histogram(v, rejilla)
    if hist.sum() < 10:
        return []
    h = np.convolve(hist, [1, 2, 3, 2, 1], 'same') / 9
    umbral = max(2.0, 0.15 * h.max())
    out = []
    for j in range(1, len(h) - 1):
        if h[j] >= umbral and h[j] >= h[j - 1] and h[j] > h[j + 1]:
            a, b = max(0, j - 2), min(len(hist), j + 3)
            out.append(float((hist[a:b] * (rejilla[a:b] + 0.005)).sum() / max(hist[a:b].sum(), 1)))
    return out


def caras_de_pared(a, b, Q, aberturas=(), techo=None, paso=0.05):
    """Para un tramo de pared a→b: en cada lado donde hay estancia escaneada, la recta de su cara real y los tramos
    donde la cara se va hacia fuera (huecos) o hacia dentro hasta el techo (pilares).

    La cara es la superficie MÁS EXTERIOR con puntos densos (los muebles siempre quedan por dentro), sin contar las
    puertas y ventanas (`aberturas`: tramos (t0, t1) a lo largo de la pared). Devuelve {lado: {...}} con lado = +1
    (hacia n = giro a la izquierda de a→b) o -1; e = distancia hacia el lado, medida desde la línea a→b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    if L < 0.3:
        return {}
    u = (b - a) / L; n = np.array([-u[1], u[0]])
    if techo is None:
        techo = float(np.percentile(Q[:, 2], 99))
    rel = Q[:, :2] - a
    t = rel @ u; en = rel @ n; h = Q[:, 2]
    cerca = (t > 0.05) & (t < L - 0.05) & (np.abs(en) < 1.2)
    t, en, h = t[cerca], en[cerca], h[cerca]
    fuera_ab = np.ones(len(t), bool)
    for t0, t1 in aberturas:
        fuera_ab &= ~((t > t0 - 0.05) & (t < t1 + 0.05))
    res = {}
    for lado in (1, -1):
        e = en * lado
        # ¿Hay estancia escaneada a este lado? Suelo o techo entre 0,2 y 1 m de la pared
        indicio = int(((e > 0.2) & (e < 1.0) & ((h < 0.06) | (h > techo - 0.08))).sum())
        if indicio < 300:
            continue
        sel = fuera_ab & (e > -0.45) & (e < 0.40) & (h > 0.15) & (h < techo - 0.05)
        ts, es, hs = t[sel], e[sel], h[sel]
        arriba = hs > techo - 0.30
        bins = np.arange(0.05, L - 0.05 + 1e-9, paso)
        tb, eb, eb_top, todos = [], [], [], []
        k = np.digitize(ts, bins)
        rejilla = np.arange(-0.45, 0.405, 0.01)
        for i in range(1, len(bins)):
            m = k == i
            if m.sum() < 15:
                continue
            tb.append((bins[i - 1] + bins[i]) / 2)
            pk = _picos(es[m], rejilla); eb.append(pk[0] if pk else np.nan); todos.append(pk)
            pt = _picos(es[m & arriba], rejilla); eb_top.append(pt[0] if pt else np.nan)
        tb, eb, eb_top = np.array(tb), np.array(eb), np.array(eb_top)
        if len(tb) < max(4, 0.4 * L / paso):
            continue
        # Recta de la cara: la que apoyan más tramos de la pared (algún pico a menos de 2,5 cm); entre las casi
        # empatadas (≥ 70 % del mejor apoyo), la más exterior. Un mueble o lo que se ve a través de un cristal o en un
        # espejo ocupan un trozo de la pared; la pared se ve casi a todo lo largo, aunque sea por encima de los muebles.
        cand = [(t, e) for t, pk in zip(tb, todos) for e in pk]
        if len(cand) < 3:
            continue
        T_ = np.array([c[0] for c in cand]); E_ = np.array([c[1] for c in cand])
        rng = np.random.default_rng(0)
        lineas = [(0.0, float(e)) for e in E_]                     # paralelas al esqueleto…
        for _ in range(300):                                     # …y con algo de giro
            a_, b_ = rng.integers(len(cand), size=2)
            if abs(T_[a_] - T_[b_]) > 0.5:
                c1_ = (E_[b_] - E_[a_]) / (T_[b_] - T_[a_])
                if abs(c1_) < 0.09:                              # hasta ~5°
                    lineas.append((float(c1_), float(E_[a_] - c1_ * T_[a_])))
        apoyos = []
        for c1_, c0_ in lineas:
            pred = c0_ + c1_ * tb
            apoyos.append(sum(1 for pk, pr in zip(todos, pred) if any(abs(e - pr) < 0.025 for e in pk)))
        apoyos = np.array(apoyos); mejor_ap = apoyos.max()
        buenas = [l for l, ap in zip(lineas, apoyos) if ap >= 0.7 * mejor_ap]
        c1, c0 = min(buenas, key=lambda l: l[1] + l[0] * L / 2)  # la más exterior en el centro de la pared
        for _ in range(3):                                       # afinar con los picos que la apoyan
            pred = c0 + c1 * tb
            sel_t, sel_e = [], []
            for t_, pk, pr in zip(tb, todos, pred):
                cerca = [e for e in pk if abs(e - pr) < 0.025]
                if cerca:
                    sel_t.append(t_); sel_e.append(min(cerca, key=lambda e: abs(e - pr)))
            if len(sel_t) < 3:
                break
            c1, c0 = np.polyfit(sel_t, sel_e, 1)
        ok = np.array([any(abs(e - (c0 + c1 * t_)) < 0.025 for e in pk) for t_, pk in zip(tb, todos)])
        if ok.sum() < max(3, 0.35 * len(tb)) or (tb[ok].max() - tb[ok].min()) < 0.4 * L:
            continue
        resid = eb - (c0 + c1 * tb)
        tramos = []
        for clase, cond in (('hueco', resid < -0.04), ('pilar', (resid > 0.04) & (eb_top - (c0 + c1 * tb) > 0.04))):
            i = 0
            while i < len(cond):
                if not cond[i]:
                    i += 1; continue
                j = i
                while j + 1 < len(cond) and cond[j + 1] and tb[j + 1] - tb[j] < paso * 1.5:
                    j += 1
                ancho = tb[j] - tb[i] + paso
                fondo = float(np.median(np.abs(resid[i:j + 1])))
                if ancho >= 0.20 and fondo < 0.45 and (clase == 'hueco' or fondo >= 0.06):
                    t0, t1 = tb[i] - paso / 2, tb[j] + paso / 2
                    sentido = -1 if clase == 'hueco' else 1
                    dentro = (ts >= t0) & (ts <= t1) & (sentido * (es - (c0 + c1 * ts)) > 0.03)
                    alt = [round(float(v), 2) for v in np.percentile(hs[dentro], [2, 98])] if dentro.sum() > 30 else None
                    tramos.append({'tipo': clase, 't0': round(float(t0), 3), 't1': round(float(t1), 3),
                                   'fondo': round(fondo, 3), 'alturas': alt})
                i = j + 1
        cerca = [min(abs(e - (c0 + c1 * t_)) for e in pk) for t_, pk, o_ in zip(tb, todos, ok) if o_]
        res[lado] = {'c0': float(c0), 'c1': float(c1), 'bins': int(len(tb)), 'ajuste': int(ok.sum()),
                     'error_mm': round(float(np.median(cerca)) * 1000, 1), 'tramos': tramos}
    return res
