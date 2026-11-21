"""De un escaneo de Apple RoomPlan (room.json, el que exporta OpenPlan3D Capture) a la planta de Croquis, limpia.

Correcciones automáticas (lo que el escaneo hace mal y un delineante corregiría sin preguntar):
- Gira la casa para que sus paredes queden a escuadra con los ejes, y pone exactamente a escuadra las que se desvían
  menos de 6° (las que se desvían más se respetan: pueden ser de verdad).
- Une los tramos alineados de una misma pared y alarga o recorta los extremos hasta la pared vecina (sin huecos entre
  habitaciones ni zigzags).
- Grosores: los tabiques (pared entre dos estancias) 10 cm centrados; las fachadas (con una estancia a un lado) 30 cm
  hacia fuera. Son supuestos: se confirman con las medidas guiadas (grosor en las puertas y ventanas).
- Estancias: las caras que forman las paredes, con el nombre que da RoomPlan (en castellano) y la altura de sus paredes.
- Puertas, ventanas y pasos: en su pared, con su ancho y alturas; el sentido de apertura es un supuesto (hacia el
  dormitorio, baño o cocina) que se confirma después.

Devuelve una planta con la misma forma que `planos.Planta`, para dibujar las láminas con la plantilla del estudio.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

ESCUADRA = 6.0          # grados: por debajo, la pared se pone a escuadra
ALINEADAS = 0.06        # m: dos tramos paralelos a menos de esto son la misma pared
HUECO = 0.40            # m: huecos entre tramos o hasta la pared vecina que se cierran
TABIQUE = 0.10
FACHADA = 0.30
NOMBRES = {'livingRoom': 'SALÓN', 'kitchen': 'COCINA', 'bathroom': 'BAÑO', 'bedroom': 'DORMITORIO',
           'diningRoom': 'COMEDOR', 'unidentified': 'ESTANCIA'}


def _T(s):
    return np.array(s['transform'], float).reshape(4, 4).T


def leer(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


class Pared:
    def __init__(self, a, b, alto, ident):
        self.a, self.b, self.alto, self.ids = np.array(a, float), np.array(b, float), alto, [ident]

    @property
    def u(self):
        d = self.b - self.a
        return d / np.linalg.norm(d)

    @property
    def largo(self):
        return float(np.linalg.norm(self.b - self.a))

    def linea(self):
        return LineString([tuple(self.a), tuple(self.b)])


def _orientacion(r):
    """Ángulo dominante de las paredes (módulo 90°), ponderado por su largo."""
    angs, pesos = [], []
    for w in r['walls']:
        T = _T(w)
        angs.append(math.atan2(-T[2, 0], T[0, 0]) % (math.pi / 2))
        pesos.append(w['dimensions'][0])
    # media circular con periodo 90°
    z = sum(p * complex(math.cos(4 * a), math.sin(4 * a)) for a, p in zip(angs, pesos))
    return math.atan2(z.imag, z.real) / 4


def _girar(p, ang):
    c, s = math.cos(-ang), math.sin(-ang)
    return np.array([c * p[0] - s * p[1], s * p[0] + c * p[1]])


def importar(r, desplazar=(0.0, 0.0), correcciones=None):
    """`correcciones`: lo que detecta `detectar.paredes` (huecos y salientes por pared), para aplicarlo solo."""
    ang = _orientacion(r)
    suelo = min(_T(f)[1, 3] for f in r['floors']) if r.get('floors') else None
    paredes = {}
    for w in r['walls']:
        T = _T(w); c = T[:3, 3]; u = T[:3, 0]; L, alto = w['dimensions'][0], w['dimensions'][1]
        a = _girar((c - u * L / 2)[[0, 2]] * [1, -1], ang); b = _girar((c + u * L / 2)[[0, 2]] * [1, -1], ang)
        p = Pared(a, b, alto, w['identifier'])
        # A escuadra si se desvía poco
        d = p.b - p.a; t = math.degrees(math.atan2(d[1], d[0])) % 90
        desv = min(t, 90 - t)
        if desv < ESCUADRA:
            m = (p.a + p.b) / 2
            horizontal = abs(d[0]) >= abs(d[1])
            if horizontal:
                p.a, p.b = np.array([m[0] - p.largo / 2, m[1]]), np.array([m[0] + p.largo / 2, m[1]])
            else:
                p.a, p.b = np.array([m[0], m[1] - p.largo / 2]), np.array([m[0], m[1] + p.largo / 2])
        paredes[w['identifier']] = p
        if suelo is None:
            suelo = c[1] - alto / 2
    lista = _unir(list(paredes.values()))
    _cerrar(lista)
    lista += _puentes(lista)
    # Estancias: caras de las paredes (cada pared prolongada 2 cm, para que los cruces no dependan de un redondeo)
    lineas = unary_union([LineString([tuple(p.a - p.u * 0.02), tuple(p.b + p.u * 0.02)]) for p in lista])
    caras = [c for c in polygonize(lineas) if c.area > 0.8]
    secciones = []
    for sc in r.get('sections', []):
        q = _girar(np.array([sc['center'][0], -sc['center'][2]]), ang)
        secciones.append((NOMBRES.get(sc['label'], 'ESTANCIA'), Point(q)))
    # El pasillo y lo que no cierra: lo que queda dentro de la casa entre estancias
    casa = unary_union(caras).buffer(1.2, join_style='mitre').buffer(-1.2, join_style='mitre')
    resto = casa.difference(unary_union(caras).buffer(0.05)).difference(lineas.buffer(0.06))
    for g in (resto.geoms if hasattr(resto, 'geoms') else [resto]):
        if g.area > 1.0:
            caras.append(g.buffer(0.05))
    # Muebles que da RoomPlan: dicen qué es cada estancia mejor que su etiqueta
    muebles = []
    for o in r.get('objects', []):
        cat = next(iter(o['category'].keys()))
        q = _girar(np.array([_T(o)[0, 3], -_T(o)[2, 3]]), ang)
        muebles.append((cat, Point(q)))
    ventanas_pt = [Point(*_girar(np.array([_T(v)[0, 3], -_T(v)[2, 3]]), ang)) for v in r.get('windows', [])]
    POR_MUEBLE = [('bed', 'DORMITORIO'), ('toilet', 'BAÑO'), ('bathtub', 'BAÑO'), ('stove', 'COCINA'),
                  ('oven', 'COCINA'), ('refrigerator', 'COCINA'), ('sofa', 'SALÓN')]
    estancias, cuenta = {}, {}
    for cara in sorted(caras, key=lambda c: -c.area):
        nombre = next((n for n, pt in secciones if cara.buffer(0.05).contains(pt)), None)
        dentro = [c for c, pt in muebles if cara.contains(pt)]
        por_mueble = next((n for m, n in POR_MUEBLE if m in dentro), None)
        if por_mueble and (nombre in (None, 'ESTANCIA') or nombre != por_mueble):
            nombre = por_mueble
        if cara.area < 2.0:
            nombre = 'ARMARIO'
        if nombre is None or nombre == 'ESTANCIA':
            lados = sorted(_lados_rect(cara))
            ancho_medio = cara.area / max(cara.length / 2, 0.1)
            con_ventana = any(cara.exterior.distance(v) < 0.4 for v in ventanas_pt)
            estrecho = ancho_medio < 1.4 or (lados[0] < 1.6 and lados[1] / max(lados[0], 0.1) > 2.2)
            nombre = 'PASILLO' if estrecho and not con_ventana else 'ESTANCIA'
        cuenta[nombre] = cuenta.get(nombre, 0) + 1
        estancias[f'{nombre} {cuenta[nombre]}' if cuenta[nombre] > 1 or nombre in ('DORMITORIO', 'ESTANCIA') else nombre] = cara
    # Numerar bien los que se repiten (DORMITORIO 1, 2…)
    estancias = _renumerar(estancias)
    # Alturas por estancia: la mediana de las paredes que la tocan
    alturas = {}
    for n, cara in estancias.items():
        hs = [p.alto for p in lista if cara.exterior.buffer(0.08).intersects(p.linea())]
        alturas[n] = float(np.median(hs)) if hs else 2.5
    pl = _Planta(r, ang, suelo, lista, paredes, estancias, alturas, desplazar)
    if correcciones:
        pl.aplicar(r, ang, correcciones, desplazar)
    return pl


def _lados_rect(pol):
    c = list(pol.minimum_rotated_rectangle.exterior.coords)
    return [math.dist(c[0], c[1]), math.dist(c[1], c[2])]


def _renumerar(est):
    base = {}
    for n in est:
        b = n.rsplit(' ', 1)[0] if n.rsplit(' ', 1)[-1].isdigit() else n
        base.setdefault(b, []).append(n)
    out = {}
    for b, ns in base.items():
        for i, n in enumerate(ns, 1):
            out[b if len(ns) == 1 else f'{b} {i}'] = est[n]
    return out


def _unir(lista):
    """Une tramos colineales (misma recta, huecos pequeños)."""
    cambiado = True
    while cambiado:
        cambiado = False
        for i in range(len(lista)):
            for j in range(i + 1, len(lista)):
                p, q = lista[i], lista[j]
                if abs(p.u @ q.u) < math.cos(math.radians(2)):
                    continue
                n = np.array([-p.u[1], p.u[0]])
                if abs((q.a - p.a) @ n) > ALINEADAS or abs((q.b - p.a) @ n) > ALINEADAS:
                    continue
                t = sorted([0.0, p.largo, float((q.a - p.a) @ p.u), float((q.b - p.a) @ p.u)])
                tp = sorted([0.0, p.largo]); tq = sorted([float((q.a - p.a) @ p.u), float((q.b - p.a) @ p.u)])
                hueco = max(tq[0] - tp[1], tp[0] - tq[1])
                if hueco > HUECO:
                    continue
                nueva = Pared(p.a + p.u * t[0], p.a + p.u * t[-1], max(p.alto, q.alto), None)
                nueva.ids = p.ids + q.ids
                lista[i] = nueva
                del lista[j]
                cambiado = True
                break
            if cambiado:
                break
    return lista


def _cerrar(lista):
    """Alarga o recorta cada extremo suelto hasta cruzar la pared más cercana (a menos de HUECO), sin dejar paredes
    de largo nulo."""
    for p in lista:
        for extremo in ('a', 'b'):
            e = getattr(p, extremo)
            otro = p.b if extremo == 'a' else p.a
            sentido = (e - otro) / np.linalg.norm(e - otro)          # hacia fuera por este extremo
            mejor = None
            for q in lista:
                if q is p:
                    continue
                den = sentido[0] * q.u[1] - sentido[1] * q.u[0]
                if abs(den) < math.sin(math.radians(20)):            # casi paralelas: no se cortan
                    continue
                w = q.a - e
                s = (w[0] * q.u[1] - w[1] * q.u[0]) / den           # e + sentido·s está sobre la recta de q
                x = e + sentido * s
                t = float((x - q.a) @ q.u)                           # posición sobre q
                if abs(s) <= HUECO and -HUECO <= t <= q.largo + HUECO:
                    if np.linalg.norm(x - otro) < 0.2:
                        continue
                    if mejor is None or abs(s) < abs(mejor[0]):
                        mejor = (s, x)
            if mejor is not None:
                setattr(p, extremo, mejor[1])


def _puentes(lista, maximo=0.6):
    """Extremos sueltos (que no tocan otra pared) cerca de otro extremo suelto: se unen con un tramo nuevo."""
    def suelto(e, p):
        return all(q is p or q.linea().distance(Point(*e)) > 0.03 for q in lista)
    sueltos = [(e, p) for p in lista for e in (p.a, p.b) if suelto(e, p)]
    nuevos, usados = [], set()
    for i, (e, p) in enumerate(sueltos):
        if i in usados:
            continue
        cand = [(np.linalg.norm(e - f), j) for j, (f, q) in enumerate(sueltos) if j != i and j not in usados and q is not p]
        if not cand:
            continue
        dist, j = min(cand)
        if dist <= maximo:
            nuevo = Pared(e, sueltos[j][0], p.alto, None)
            nuevo.ids = []
            nuevos.append(nuevo)
            usados.update({i, j})
    return nuevos


class _Planta:
    """Misma forma que planos.Planta (estancias, puertas, ventanas, macizo, exterior, p, viv)."""

    def __init__(self, r, ang, suelo, paredes, por_id, estancias, alturas, desplazar):
        dx, dy = desplazar
        mover = lambda v: np.array([v[0] + dx, v[1] + dy])
        for p in paredes:
            p.a, p.b = mover(p.a), mover(p.b)
        self.estancias = {n: Polygon([(x + dx, y + dy) for x, y in c.exterior.coords]) for n, c in estancias.items()}
        self.fachada = FACHADA
        self.paredes = paredes
        union = unary_union(list(self.estancias.values()))
        # Tipo de cada pared: tabique si tiene estancia a los dos lados; si no, fachada (grosor hacia fuera)
        macizo = []
        for p in paredes:
            n = np.array([-p.u[1], p.u[0]]); m = (p.a + p.b) / 2
            izq = union.contains(Point(*(m + n * 0.15))); der = union.contains(Point(*(m - n * 0.15)))
            if izq and der:
                macizo.append(p.linea().buffer(TABIQUE / 2, cap_style='flat'))
                p.tipo = 'tabique'
            else:
                lado = -1 if izq else 1               # hacia fuera
                macizo.append(p.linea().buffer(FACHADA * lado, single_sided=True, cap_style='flat'))
                p.tipo = 'fachada'
                p.fuera = n * lado
        macizo_bruto = unary_union(macizo).buffer(0.02).buffer(-0.02)
        # Estancias a cara interior (quitando el grueso de las paredes)
        self.estancias = {n: _mayor(c.difference(macizo_bruto)) for n, c in self.estancias.items()}
        self.puertas, self.ventanas, huecos = [], [], []
        idx = {i: p for p in paredes for i in p.ids}
        for tipo, lista in (('puerta', r.get('doors', [])), ('paso', r.get('openings', []))):
            for d in lista:
                p = idx.get(d.get('parentIdentifier'))
                if p is None:
                    continue
                c = mover(_girar(_T(d)[:3, 3][[0, 2]] * [1, -1], ang))
                s = float((c - p.a) @ p.u); w = d['dimensions'][0]
                j1, j2 = p.a + p.u * (s - w / 2), p.a + p.u * (s + w / 2)
                g = TABIQUE if p.tipo == 'tabique' else FACHADA
                pol = LineString([tuple(j1), tuple(j2)]).buffer(g + 0.02, cap_style='flat')
                huecos.append(pol)
                if tipo == 'paso' or w > 1.25:       # más ancho que una puerta: armario o paso, sin hoja
                    continue
                n = np.array([-p.u[1], p.u[0]])
                lados = [(nom, est) for nom, est in self.estancias.items() if est.distance(LineString([tuple(j1), tuple(j2)])) < 0.25]
                abre = _hacia_donde(lados, c, n)
                sgn = 1 if abre and abre[1].contains(Point(*(c + n * 0.3))) else -1
                off = n * sgn * (TABIQUE / 2 if p.tipo == 'tabique' else 0.0)
                self.puertas.append({'id': d['identifier'][:6], 'poligono': pol, 'jambas': [tuple(j1 + off), tuple(j2 + off)],
                                     'estancia': abre[0] if abre else (lados[0][0] if lados else None), 'bisagra': 0,
                                     'altura': d['dimensions'][1], 'grosor': g, 'todas': [[tuple(j1 + off), tuple(j2 + off)]],
                                     'supuesto': True})
        for v in r.get('windows', []):
            p = idx.get(v.get('parentIdentifier'))
            if p is None:
                continue
            c = mover(_girar(_T(v)[:3, 3][[0, 2]] * [1, -1], ang))
            s = float((c - p.a) @ p.u); w, h = v['dimensions'][0], v['dimensions'][1]
            j = [p.a + p.u * (s - w / 2), p.a + p.u * (s + w / 2)]
            fuera = getattr(p, 'fuera', np.array([-p.u[1], p.u[0]]))
            o = [q + fuera * FACHADA for q in j]
            pol = Polygon([tuple(j[0]), tuple(j[1]), tuple(o[1]), tuple(o[0])])
            huecos.append(pol.buffer(0.01))
            y = _T(v)[1, 3]
            est = min(self.estancias, key=lambda n: self.estancias[n].distance(Point(*c)))
            self.ventanas.append({'id': v['identifier'][:6], 'estancia': est, 'poligono': pol, 'dentro': j, 'fuera': o,
                                  'normal': fuera, 'antepecho': round(y - h / 2 - suelo, 3), 'dintel': round(y + h / 2 - suelo, 3),
                                  'fachada': FACHADA})
        self.macizo = macizo_bruto.difference(unary_union(huecos)) if huecos else macizo_bruto
        self.exterior = Polygon(unary_union(list(self.estancias.values()) + [macizo_bruto]).buffer(0.01).exterior)
        self.p = {}
        self.viv = type('V', (), {'datos': {'estancias': {n: {'altura': round(alturas[n], 3)} for n in self.estancias}}})()

    def aplicar(self, r, ang, correcciones, desplazar):
        """Huecos: se suman a la estancia de al lado (entrando en el muro); salientes (pilares): se restan."""
        from shapely.geometry import Polygon as Pol
        dx, dy = desplazar
        por_id = {w['identifier']: w for w in r['walls']}
        self.aplicadas = []
        for c in correcciones:
            w = por_id.get(c['pared'])
            if not w or not c.get('tramos'):
                continue
            T = _T(w); centro = T[:3, 3]; u = T[:3, 0]; L = w['dimensions'][0]
            a3 = centro - u * L / 2
            for tr in c['tramos']:
                p1 = _girar((a3 + u * tr['desde'])[[0, 2]] * [1, -1], ang) + [dx, dy]
                p2 = _girar((a3 + u * (tr['desde'] + tr['ancho']))[[0, 2]] * [1, -1], ang) + [dx, dy]
                d = p2 - p1; d = d / np.linalg.norm(d); n = np.array([-d[1], d[0]])
                m = (p1 + p2) / 2
                est = min(self.estancias.items(), key=lambda kv: kv[1].distance(Point(*m)))
                dentro = n if est[1].contains(Point(*(m + n * 0.15))) else -n
                f = tr['fondo']
                if tr['tipo'] == 'hueco':        # hacia fuera de la estancia, dentro del muro
                    rect = Pol([tuple(p1 + dentro * 0.06), tuple(p2 + dentro * 0.06), tuple(p2 - dentro * (0.06 + f)),
                                tuple(p1 - dentro * (0.06 + f))])
                    self.estancias[est[0]] = _mayor(est[1].union(rect.buffer(0)))
                    self.macizo = self.macizo.difference(rect)
                else:                            # pilar o saliente: hacia dentro de la estancia
                    rect = Pol([tuple(p1 - dentro * 0.06), tuple(p2 - dentro * 0.06), tuple(p2 + dentro * f),
                                tuple(p1 + dentro * f)])
                    self.estancias[est[0]] = _mayor(est[1].difference(rect))
                    self.macizo = self.macizo.union(rect)
                self.aplicadas.append({'estancia': est[0], **tr})

    def resumen(self):
        return {n: (round(c.area, 2)) for n, c in self.estancias.items()}


def _mayor(g):
    if hasattr(g, 'geoms'):
        return max(g.geoms, key=lambda x: x.area)
    return g


def _hacia_donde(lados, c, n):
    """Supuesto del sentido de apertura: hacia el dormitorio, baño o cocina; si no, hacia la estancia más pequeña."""
    if not lados:
        return None
    prioridad = ('BAÑO', 'DORMITORIO', 'COCINA')
    for pref in prioridad:
        for nom, est in lados:
            if nom.startswith(pref):
                return nom, est
    return min(lados, key=lambda t: t[1].area)
