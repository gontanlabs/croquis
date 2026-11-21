"""Láminas de estado actual de una vivienda ajustada, dentro de una copia de la plantilla del estudio.

- Planta (láminas de distribución y de cotas, que comparten el modelo): muros y tabiques con su relleno, puertas con
  su abatimiento, ventanas, nombre y superficie útil de cada estancia, cotas interiores y la línea de sección.
- Sección: lo cortado (muros, dinteles, antepechos, suelo y techos, falsos techos) y lo que se ve detrás (paredes y
  sus huecos), con cotas de alturas.
- Alzado interior de una pared: contorno, huecos y cotas.

Los nombres del estudio (capas, estilos, láminas, cajetín) vienen de la configuración (`estudio.leer_config`).
"""
from __future__ import annotations

import math
from pathlib import Path

import ezdxf
import numpy as np
from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import unary_union

from estudio import _punto_libre, leer_config
from vivienda import Vivienda

COTA_MINIMA = 0.30          # paredes más cortas no llevan cota (se leen en las vecinas)


# ---------------------------------------------------------------------------------------------------------------
# Geometría de la planta
# ---------------------------------------------------------------------------------------------------------------
def _u(a, b):
    a, b = np.array(a, float), np.array(b, float)
    return (b - a) / np.linalg.norm(b - a)


def _hacia_fuera(estancia: Polygon, a, b):
    """Normal de la pared a-b que sale de la estancia."""
    u = _u(a, b)
    n = np.array([u[1], -u[0]])
    m = (np.array(a) + np.array(b)) / 2
    return n if not estancia.contains(_pt(m + n * 0.02)) else -n


def _pt(v):
    from shapely.geometry import Point
    return Point(float(v[0]), float(v[1]))


class Planta:
    def __init__(self, viv: Vivienda, desplazar=(0.0, 0.0)):
        self.viv = viv
        dx, dy = desplazar
        self.p = {n: (x + dx, y + dy) for n, (x, y) in viv.p.items()}
        self.estancias = viv.poligonos(self.p)
        self.fachada = viv.datos.get('fachada', 0.30)
        self._puertas()
        self._ventanas()
        huecos = [h['poligono'] for h in self.puertas] + [v['poligono'] for v in self.ventanas]
        interiores = [h['poligono'] for h in self.puertas if len(h['todas']) == 2]
        todo = unary_union(list(self.estancias.values()) + interiores)
        exterior = todo.buffer(self.fachada, join_style='mitre', mitre_limit=4.0)
        if isinstance(exterior, MultiPolygon):
            exterior = max(exterior.geoms, key=lambda g: g.area)
        self.exterior = Polygon(exterior.exterior)
        self.macizo = self.exterior.difference(unary_union(list(self.estancias.values()) + huecos))

    def _puertas(self):
        self.puertas = []
        for pu in self.viv.datos['puertas']:
            lados = [[self.p[n] for n in self.viv.jambas[(pu['id'], i)]] for i in range(len(pu['lados']))]
            ests = [self.viv.estancia_de(l['pared'][0]) for l in pu['lados']]
            if '_pares' in pu:
                (a, b), (c, d) = pu['_pares']
                pol = Polygon([self.p[a], self.p[c], self.p[d], self.p[b]])
                grosor = math.dist(self.p[a], self.p[b])
            else:     # puerta a la calle o al rellano: solo se mide por dentro
                j1, j2 = lados[0]
                pared = pu['lados'][0]['pared']
                n = _hacia_fuera(self.estancias[ests[0]], self.p[pared[0]], self.p[pared[1]])
                g = pu.get('grosor', self.fachada)
                pol = Polygon([j1, j2, tuple(np.array(j2) + n * g), tuple(np.array(j1) + n * g)])
                grosor = g
            lado = ests.index(pu['abre']) if pu.get('abre') in ests else 0
            self.puertas.append({'id': pu['id'], 'poligono': pol, 'jambas': lados[lado],
                                 'estancia': ests[lado], 'bisagra': pu.get('bisagra', 0),
                                 'altura': pu.get('altura', 2.03), 'grosor': grosor,
                                 'pared': pu['lados'][lado]['pared'], 'todas': lados, 'ests': ests})

    def _ventanas(self):
        self.ventanas = []
        for v in self.viv.datos['ventanas']:
            a, b = self.p[v['pared'][0]], self.p[v['pared'][1]]
            u = _u(a, b)
            n = _hacia_fuera(self.estancias[v['estancia']], a, b)
            w = [np.array(a) + u * s for s in v['jambas']]
            g = v.get('fachada', self.fachada)
            o = [q + n * g for q in w]
            pol = Polygon([tuple(w[0]), tuple(w[1]), tuple(o[1]), tuple(o[0])])
            self.ventanas.append({**v, 'poligono': pol, 'dentro': w, 'fuera': o, 'normal': n})


# ---------------------------------------------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------------------------------------------
def _sin_huecos(geom):
    """Trozos sin huecos de un polígono (franjas verticales entre vértices), para rellenos sólidos en AutoCAD."""
    polys = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
    out = []
    for poly in polys:
        if poly.is_empty:
            continue
        if not poly.interiors:
            out.append(poly)
            continue
        xs = sorted({round(x, 6) for ring in [poly.exterior, *poly.interiors] for x, _ in ring.coords})
        miny, maxy = poly.bounds[1] - 1, poly.bounds[3] + 1
        for x0, x1 in zip(xs, xs[1:]):
            trozo = poly.intersection(box(x0, miny, x1, maxy))
            for t in (trozo.geoms if hasattr(trozo, 'geoms') else [trozo]):
                if isinstance(t, Polygon) and t.area > 1e-8:
                    out.append(t)
    return out


def _relleno(msp, geom, capa):
    for t in _sin_huecos(geom):
        h = msp.add_hatch(dxfattribs={'layer': capa, 'color': 256})
        h.set_solid_fill(color=256)
        h.paths.add_polyline_path(list(t.exterior.coords)[:-1], is_closed=True)


def _segmentos(geom):
    polys = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
    for poly in polys:
        for ring in [poly.exterior, *poly.interiors]:
            c = list(ring.coords)
            for a, b in zip(c, c[1:]):
                if math.dist(a, b) > 1e-6:
                    yield a, b


def _cota(msp, conf, p1, p2, sep, texto='<>'):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    if dx < -1e-9 or (abs(dx) <= 1e-9 and dy < 0):
        p1, p2, sep = p2, p1, -sep
    d = msp.add_aligned_dim(p1=p1, p2=p2, distance=sep, dimstyle=conf['estilo_cota'], text=texto,
                            dxfattribs={'layer': conf['capas']['cotas']})
    d.render()


def _texto(msp, conf, texto, donde, capa=None, alto=None, rot=0.0):
    mt = msp.add_mtext(texto, dxfattribs={'layer': capa or conf['capas']['textos'], 'style': conf['estilo_texto'],
                                          'char_height': alto or conf['altura_texto'], 'rotation': rot})
    mt.set_location(donde, attachment_point=ezdxf.enums.MTextEntityAlignment.MIDDLE_CENTER)
    return mt


def dibujar_planta(msp, pl: Planta, conf, margenes=None, seccion=None):
    c = conf['capas']
    _relleno(msp, pl.macizo, c['relleno'])
    anillo = pl.exterior.exterior
    for a, b in _segmentos(pl.macizo):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        capa = c['muro'] if anillo.distance(_pt(m)) <= pl.fachada + 0.03 else c['tabique']
        msp.add_line(a, b, dxfattribs={'layer': capa, 'color': 256})
    # Puertas: hoja abierta a 90° y su recorrido
    for pu in pl.puertas:
        bis = np.array(pu['jambas'][pu['bisagra']])
        otra = np.array(pu['jambas'][1 - pu['bisagra']])
        ancho = float(np.linalg.norm(otra - bis))
        est = pl.estancias[pu['estancia']]
        u = (otra - bis) / ancho
        n = np.array([-u[1], u[0]])
        if not est.contains(_pt(bis + u * ancho / 2 + n * 0.05)):
            n = -n
        fin = bis + n * ancho
        msp.add_line(tuple(bis), tuple(fin), dxfattribs={'layer': c['puertas'], 'color': 256})
        a0 = math.degrees(math.atan2(*(otra - bis)[::-1]))
        a1 = math.degrees(math.atan2(*(fin - bis)[::-1]))
        if (a1 - a0) % 360 > 180:
            a0, a1 = a1, a0
        msp.add_arc(tuple(bis), ancho, a0, a1, dxfattribs={'layer': c['puertas'], 'color': 256})
    # Ventanas: alféizar, carpintería y cara interior
    for v in pl.ventanas:
        w, o, nrm = v['dentro'], v['fuera'], v['normal']
        g = float(np.linalg.norm(o[0] - w[0]))
        for t in (0.0, 0.42, 0.58, 1.0):
            msp.add_line(tuple(w[0] + nrm * g * t), tuple(w[1] + nrm * g * t),
                         dxfattribs={'layer': c['ventanas'], 'color': 256})
    # Nombres, superficies y cotas
    barridos = []        # lo que barre cada hoja: un cuarto de círculo dentro de la estancia hacia la que abre
    for pu in pl.puertas:
        bis = np.array(pu['jambas'][pu['bisagra']])
        otra = np.array(pu['jambas'][1 - pu['bisagra']])
        r = float(np.linalg.norm(otra - bis))
        u = (otra - bis) / r
        n = np.array([-u[1], u[0]])
        if not pl.estancias[pu['estancia']].contains(_pt(bis + u * r / 2 + n * 0.05)):
            n = -n
        arco = [tuple(bis + r * (math.cos(t) * u + math.sin(t) * n)) for t in np.linspace(0, math.pi / 2, 12)]
        barridos.append(Polygon([tuple(bis)] + arco).buffer(0.05))
    for nom, est in pl.estancias.items():
        area = f'{est.area:.2f}'.replace('.', ',')
        x0, y0, x1, y1 = est.bounds
        estrecha = (x1 - x0) < 1.6 and (y1 - y0) > (x1 - x0)
        cotas = est.buffer(-conf['separacion_cota'], join_style='mitre')
        lineas_cota = [cotas.exterior.buffer(0.06)] if isinstance(cotas, Polygon) and not cotas.is_empty else []
        ancho = max(len(nom), len(f'S. útil: {area} m²')) * 0.6 * conf['altura_texto']
        alto = 2 * 1.5 * conf['altura_texto']
        tam = (alto, ancho) if estrecha else (ancho, alto)
        _texto(msp, conf, f'{nom}\\PS. útil: {area} m²', _sitio_texto(est, barridos + lineas_cota, tam=tam),
               rot=90.0 if estrecha else 0.0)
        pts = list(est.exterior.coords)[:-1]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            if math.dist(a, b) >= COTA_MINIMA:
                _cota(msp, conf, a, b, conf['separacion_cota'] if not _horario(pts) else -conf['separacion_cota'])
    if seccion:
        (x0, y0), (x1, y1) = seccion['linea']
        u = _u((x0, y0), (x1, y1))
        for (x, y), letra, s in (((x0, y0), 'A', -1), ((x1, y1), "A'", 1)):
            q = np.array((x, y)) + u * s * 0.4
            msp.add_line((x, y), tuple(q), dxfattribs={'layer': c['textos'], 'color': 256, 'lineweight': 50})
            _texto(msp, conf, letra, tuple(q + u * s * 0.25), alto=conf['altura_texto'] * 2)


def _sitio_texto(est: Polygon, obstaculos, paso=0.05, tam=(0.0, 0.0)):
    """Punto de la estancia donde cabe un texto de tamaño `tam` (ancho, alto, ya girado), lo más lejos posible de
    las paredes, las cotas y los abatimientos de las puertas."""
    libre = est.difference(unary_union(obstaculos)) if obstaculos else est
    if libre.is_empty:
        libre = est
    borde = unary_union([est.exterior] + [o.boundary for o in obstaculos if o.intersects(est)])
    x0, y0, x1, y1 = est.bounds
    w, h = tam
    if w:
        cabe = [(float(x), float(y)) for x in np.arange(x0, x1, paso) for y in np.arange(y0, y1, paso)
                if libre.contains(box(x - w / 2, y - h / 2, x + w / 2, y + h / 2))]
        if cabe:
            return max(cabe, key=lambda q: borde.distance(_pt(q)))
    mejor, dist = None, -1.0
    for x in np.arange(x0, x1, paso):
        for y in np.arange(y0, y1, paso):
            q = _pt((x, y))
            if libre.contains(q):
                d = borde.distance(q)
                if d > dist:
                    mejor, dist = (float(x), float(y)), d
    return mejor or _punto_libre(list(est.exterior.coords)[:-1])


def _horario(pts):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) < 0


# ---------------------------------------------------------------------------------------------------------------
# Sección y alzado
# ---------------------------------------------------------------------------------------------------------------
def _intervalos(geom, linea: LineString, origen, u):
    out = []
    g = geom.intersection(linea)
    for s in (g.geoms if hasattr(g, 'geoms') else [g]):
        if s.is_empty or s.length < 1e-6:
            continue
        a, b = list(s.coords)[0], list(s.coords)[-1]
        t0, t1 = sorted([float((np.array(a) - origen) @ u), float((np.array(b) - origen) @ u)])
        out.append((t0, t1))
    return sorted(out)


def dibujar_seccion(msp, pl: Planta, conf, linea, base, mirando):
    """Sección por `linea` (dos puntos de la planta), dibujada con su origen en `base`; `mirando` es el vector
    (en planta) hacia el que se mira."""
    c, cap = conf['capas'], conf['capas_alzado']
    o, f = np.array(linea[0], float), np.array(linea[1], float)
    m = np.array(mirando, float)
    derecha = np.array([m[1], -m[0]])          # lo que queda a la derecha de quien mira
    if (f - o) @ derecha < 0:
        o, f = f, o
    u = (f - o) / np.linalg.norm(f - o)
    ls = LineString([tuple(o), tuple(f)])
    alturas = {n: e['altura'] for n, e in pl.viv.datos['estancias'].items()}
    techo = max(alturas.values())
    bx, by = base

    def P(t, z):
        return (bx + t, by + z)

    def rect(t0, t1, z0, z1, capa_linea, rellenar=True):
        pts = [P(t0, z0), P(t1, z0), P(t1, z1), P(t0, z1)]
        if rellenar:
            h = msp.add_hatch(dxfattribs={'layer': c['relleno'], 'color': 256})
            h.set_solid_fill(color=256)
            h.paths.add_polyline_path(pts, is_closed=True)
        msp.add_lwpolyline(pts, close=True, dxfattribs={'layer': capa_linea, 'color': 256})

    # Lo cortado: muros y tabiques (macizo), huecos de ventana (antepecho y dintel) y de puerta (dintel)
    for t0, t1 in _intervalos(pl.macizo, ls, o, u):
        rect(t0, t1, 0, techo, cap['cortado'])
    for v in pl.ventanas:
        for t0, t1 in _intervalos(v['poligono'], ls, o, u):
            rect(t0, t1, 0, v['antepecho'], cap['cortado'])
            rect(t0, t1, v['dintel'], techo, cap['cortado'])
            tm = (t0 + t1) / 2
            for d in (-0.02, 0.02):
                msp.add_line(P(tm + d, v['antepecho']), P(tm + d, v['dintel']),
                             dxfattribs={'layer': c['ventanas'], 'color': 256})
    for pu in pl.puertas:
        for t0, t1 in _intervalos(pu['poligono'], ls, o, u):
            rect(t0, t1, pu['altura'], techo, cap['cortado'])
    # Cada estancia cortada: suelo, techo (o falso techo), lo que se ve al fondo, nombre y cota de altura
    for nom, est in pl.estancias.items():
        for t0, t1 in _intervalos(est, ls, o, u):
            h = alturas[nom]
            msp.add_line(P(t0, 0), P(t1, 0), dxfattribs={'layer': cap['cortado'], 'color': 256})
            msp.add_line(P(t0, h), P(t1, h), dxfattribs={'layer': cap['cortado'], 'color': 256})
            if h < techo - 0.01:
                rect(t0, t1, h, techo, cap['lejos'], rellenar=False)
            _fondo(msp, pl, conf, nom, est, o, u, np.array(mirando, float), t0, t1, h, P)
            _texto(msp, conf, nom, P((t0 + t1) / 2, -0.35))
            d = msp.add_linear_dim(base=P(t0 + 0.35, 0), p1=P(t0 + 0.15, 0), p2=P(t0 + 0.15, h), angle=90,
                                   dimstyle=conf['estilo_cota'], dxfattribs={'layer': c['cotas']})
            d.render()
    # Ventanas cortadas: cotas de antepecho y dintel
    for v in pl.ventanas:
        for t0, t1 in _intervalos(v['poligono'], ls, o, u):
            fuera = t1 + 0.4 if v['normal'] @ u > 0 else t0 - 0.4      # por fuera de la fachada
            borde = t1 if v['normal'] @ u > 0 else t0
            for z0, z1 in ((0, v['antepecho']), (v['antepecho'], v['dintel'])):
                d = msp.add_linear_dim(base=P(fuera, 0), p1=P(borde, z0), p2=P(borde, z1), angle=90,
                                       dimstyle=conf['estilo_cota'], dxfattribs={'layer': c['cotas']})
                d.render()


def _fondo(msp, pl, conf, nom, est, o, u, mirando, t0, t1, h, P):
    """Paredes de la estancia que se ven detrás del corte, con sus puertas y ventanas."""
    cap = conf['capas_alzado']
    pts = list(est.exterior.coords)[:-1]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        n = _hacia_fuera(est, a, b)
        if n @ mirando < 0.7:                   # solo las paredes de enfrente
            continue
        ta, tb = sorted([float((np.array(a) - o) @ u), float((np.array(b) - o) @ u)])
        ta, tb = max(ta, t0), min(tb, t1)
        if tb - ta < 0.05:
            continue
        msp.add_lwpolyline([P(ta, 0), P(tb, 0), P(tb, h), P(ta, h)], close=True,
                           dxfattribs={'layer': cap['lejos'], 'color': 256})
        pared = LineString([a, b]).buffer(0.02)
        for pu in pl.puertas:
            for jj in pu['todas']:
                if all(pared.contains(_pt(q)) for q in jj):
                    q0, q1 = sorted(float((np.array(q) - o) @ u) for q in jj)
                    msp.add_lwpolyline([P(q0, 0), P(q1, 0), P(q1, pu['altura']), P(q0, pu['altura'])],
                                       close=False, dxfattribs={'layer': cap['huecos'], 'color': 256})
        for v in pl.ventanas:
            if all(pared.contains(_pt(q)) for q in v['dentro']):
                q0, q1 = sorted(float((q - o) @ u) for q in v['dentro'])
                msp.add_lwpolyline([P(q0, v['antepecho']), P(q1, v['antepecho']), P(q1, v['dintel']),
                                    P(q0, v['dintel'])], close=True,
                                   dxfattribs={'layer': cap['huecos'], 'color': 256})


def dibujar_alzado(msp, pl: Planta, conf, estancia, pared, base):
    """Alzado interior de la pared `pared` (dos esquinas) de `estancia`, visto desde dentro."""
    c, cap = conf['capas'], conf['capas_alzado']
    a, b = (np.array(pl.p[n] if isinstance(n, str) else n, float) for n in pared)
    est = pl.estancias[estancia]
    h = pl.viv.datos['estancias'][estancia]['altura']
    n = _hacia_fuera(est, a, b)
    # Visto desde dentro: la izquierda del que mira es la esquina que queda a su izquierda
    u = (b - a) / np.linalg.norm(b - a)
    if u[0] * n[1] - u[1] * n[0] < 0:
        a, b, u = b, a, -u
    L = float(np.linalg.norm(b - a))
    bx, by = base

    def P(t, z):
        return (bx + t, by + z)

    msp.add_lwpolyline([P(0, 0), P(L, 0), P(L, h), P(0, h)], close=True,
                       dxfattribs={'layer': cap['cortado'], 'color': 256})
    pare = LineString([tuple(a), tuple(b)]).buffer(0.02)
    huecos = []
    for pu in pl.puertas:
        for jj in pu['todas']:
            if all(pare.contains(_pt(q)) for q in jj):
                q0, q1 = sorted(float((np.array(q) - a) @ u) for q in jj)
                huecos.append((q0, q1, 0.0, pu['altura']))
    for v in pl.ventanas:
        if all(pare.contains(_pt(q)) for q in v['dentro']):
            q0, q1 = sorted(float((q - a) @ u) for q in v['dentro'])
            huecos.append((q0, q1, v['antepecho'], v['dintel']))
    for q0, q1, z0, z1 in huecos:
        msp.add_lwpolyline([P(q0, z0), P(q1, z0), P(q1, z1), P(q0, z1)], close=True,
                           dxfattribs={'layer': cap['huecos'], 'color': 256})
    # Cotas: posiciones de los huecos a lo largo, la longitud total y las alturas
    xs = sorted({0.0, L, *[q for h_ in huecos for q in h_[:2]]})
    for t0, t1 in zip(xs, xs[1:]):
        d = msp.add_linear_dim(base=P(0, -0.45), p1=P(t0, 0), p2=P(t1, 0), angle=0,
                               dimstyle=conf['estilo_cota'], dxfattribs={'layer': c['cotas']})
        d.render()
    d = msp.add_linear_dim(base=P(0, -0.85), p1=P(0, 0), p2=P(L, 0), angle=0, dimstyle=conf['estilo_cota'],
                           dxfattribs={'layer': c['cotas']})
    d.render()
    zs = sorted({0.0, h, *[z for h_ in huecos for z in h_[2:] if z > 0]})
    for z0, z1 in zip(zs, zs[1:]):
        d = msp.add_linear_dim(base=P(L + 0.45, 0), p1=P(L, z0), p2=P(L, z1), angle=90,
                               dimstyle=conf['estilo_cota'], dxfattribs={'layer': c['cotas']})
        d.render()


# ---------------------------------------------------------------------------------------------------------------
# Láminas
# ---------------------------------------------------------------------------------------------------------------
def _ventana_principal(doc, nombre):
    lay = doc.layouts.get(nombre)
    vps = [v for v in lay.query('VIEWPORT') if v.dxf.width * v.dxf.height > 0]
    def es_hoja(v):          # la ventana de la hoja entera muestra el papel tal cual
        cx, cy = _centro(v)
        return (abs(cx - v.dxf.center[0]) < 1e-3 and abs(cy - v.dxf.center[1]) < 1e-3
                and abs(v.dxf.view_height - v.dxf.height) < 1e-3)
    vps = [v for v in vps if not es_hoja(v)]
    return lay, max(vps, key=lambda v: v.dxf.width * v.dxf.height)


def _centro(v):
    t, c = v.dxf.view_target_point, v.dxf.view_center_point
    return t[0] + c[0], t[1] + c[1]


def _encuadrar(v, centro, escala=50):
    """Centra la ventana en `centro` del modelo a 1/escala (papel en centímetros, modelo en metros)."""
    t = v.dxf.view_target_point
    v.dxf.view_center_point = (centro[0] - t[0], centro[1] - t[1], 0)
    v.dxf.view_height = v.dxf.height * escala / 100


def _descongelar(v, capas):
    fuera = {c.lower() for c in capas}
    v.frozen_layers = [c for c in (v.frozen_layers or []) if c.lower() not in fuera]


def _rotulo(lay, conf, clave, texto):
    """Cambia el rótulo de la plantilla (p. ej. «ALZADO NORTE») por el de la lámina."""
    viejo = conf.get('rotulos', {}).get(clave)
    if not viejo:
        return
    for e in lay.query('TEXT MTEXT'):
        actual = e.text if e.dxftype() == 'MTEXT' else e.dxf.text
        if actual.strip().upper() == viejo.upper():
            if e.dxftype() == 'MTEXT':
                e.text = texto.upper()
            else:
                e.dxf.text = texto.upper()


def _cajetin(lay, conf, valores):
    for ins in lay.query('INSERT'):
        if ins.dxf.name == conf['cajetin']['bloque']:
            for att in ins.attribs:
                for clave, etiqueta in conf['cajetin']['campos'].items():
                    if att.dxf.tag == etiqueta and clave in valores:
                        att.dxf.text = valores[clave]


def laminas(viv: Vivienda, salida, cajetin: dict, seccion: dict, alzado: dict, conf: dict | None = None,
            crear_planta=None):
    """Dibuja planta, sección y alzado en la plantilla y la guarda en `salida` (DXF). `crear_planta(desplazar)`
    sustituye a la planta de una vivienda medida (p. ej. la de un escaneo de RoomPlan, `roomplan.importar`)."""
    conf = conf or leer_config()
    doc = ezdxf.readfile(conf['plantilla'])
    msp = doc.modelspace()
    L = conf['laminas']
    _, vp_planta = _ventana_principal(doc, L['cotas'])
    cx, cy = _centro(vp_planta)
    if crear_planta:
        pl0 = crear_planta((0.0, 0.0))
        pts = np.array([c for e in pl0.estancias.values() for c in e.exterior.coords])
    else:
        pts = np.array(list(viv.p.values()))
    centro_viv = (pts.min(0) + pts.max(0)) / 2
    d = (cx - centro_viv[0], cy - centro_viv[1])
    pl = crear_planta(d) if crear_planta else Planta(viv, d)
    linea = [(x + d[0], y + d[1]) for x, y in seccion['linea']]
    dibujar_planta(msp, pl, conf, seccion={'linea': linea})
    for nom in ('distribucion', 'cotas'):
        lay, v = _ventana_principal(doc, L[nom])
        _encuadrar(v, (cx, cy))
        _cajetin(lay, conf, cajetin)

    # Sección, debajo de la planta
    largo = math.dist(*linea)
    base_s = (cx - largo / 2, cy - 20)
    dibujar_seccion(msp, pl, conf, linea, base_s, seccion['mirando'])
    capas_dibujo = list(conf['capas'].values()) + list(conf['capas_alzado'].values())
    lay, v = _ventana_principal(doc, L['seccion'])
    _encuadrar(v, (cx, base_s[1] + 3.2))   # el dibujo, por debajo del rótulo de la lámina
    _descongelar(v, capas_dibujo)
    _rotulo(lay, conf, 'seccion', seccion.get('titulo', "Sección A-A'"))
    _cajetin(lay, conf, {**cajetin, 'subtitulo': seccion.get('titulo', "Sección A-A'")})

    # Alzado interior, más abajo
    pared = alzado['pared']
    if not isinstance(pared[0], str):                       # coordenadas (de una planta sin nombres de esquinas)
        pared = [(q[0] + d[0], q[1] + d[1]) for q in pared]
    a, b = (pl.p[n] if isinstance(n, str) else n for n in pared)
    base_a = (cx - math.dist(a, b) / 2, cy - 34)
    dibujar_alzado(msp, pl, conf, alzado['estancia'], pared, base_a)
    lay, v = _ventana_principal(doc, L['alzado'])
    _encuadrar(v, (cx, base_a[1] + 3.0))
    _descongelar(v, capas_dibujo)
    _rotulo(lay, conf, 'alzado', alzado.get('titulo', 'Alzado interior'))
    _cajetin(lay, conf, {**cajetin, 'subtitulo': alzado.get('titulo', 'Alzado interior')})

    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(salida)
    return salida
