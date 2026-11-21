"""Levantamiento guiado: de un recorrido con la cámara a la lista de medidas y a los planos.

1. `crear(captura)`: el recorrido de la cámara (esquinas de cada estancia y dos puntos por puerta y por ventana, en
   metros) se convierte en una vivienda: cada puerta y ventana se asigna a su pared, y la forma de la cámara entra como
   primera aproximación (medidas «camara», ±3 cm).
2. `tareas(datos)`: lo que falta medir, en orden (cada estancia: paredes, una diagonal y altura; cada puerta: jambas
   por los dos lados, grosor, altura, hacia dónde abre y bisagra; cada ventana: jambas, antepecho, dintel y fachada).
   Al terminar, las medidas extra que pida el ajuste.
3. `responder(datos, id, valor, modo)`: guarda una respuesta.
4. `planos(datos, carpeta)`: sección y alzado elegidos solos, láminas en DXF y PDF.
"""
from __future__ import annotations

import copy
import datetime
import itertools
import math
import re
import unicodedata

import numpy as np
from shapely.geometry import LineString, Polygon

from vivienda import Vivienda

ALTURA_SUPUESTA = 2.50
GROSOR_TABIQUE = 0.10
FACHADA = 0.30


# ---------------------------------------------------------------------------------------------------------------
# 1. Del recorrido a la vivienda
# ---------------------------------------------------------------------------------------------------------------
def _abreviatura(nombre, usadas):
    limpio = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode().upper()
    partes = re.findall(r'[A-Z]+|\d+', limpio)
    ab = ''.join(p[0] if p.isalpha() else p for p in partes) or 'E'
    base, n = ab, 2
    while ab in usadas:
        ab = f'{base}{n}'
        n += 1
    usadas.add(ab)
    return ab


def _proyectar(p, a, b):
    a, b, p = (np.array(v, float) for v in (a, b, p))
    u = (b - a) / np.linalg.norm(b - a)
    s = float((p - a) @ u)
    d = float(abs(u[0] * (p - a)[1] - u[1] * (p - a)[0]))
    return s, d, float(np.linalg.norm(b - a))


def _paredes_cercanas(datos, puntos, maximo=0.45):
    """Por cada estancia, la pared que tiene más cerca los dos puntos (si los tiene a menos de `maximo`)."""
    out = []
    for nom, e in datos['estancias'].items():
        es = e['esquinas']
        mejor = None
        for a, b in zip(es, es[1:] + es[:1]):
            ca, cb = e['croquis'][a], e['croquis'][b]
            proy = [_proyectar(p, ca, cb) for p in puntos]
            if all(-0.15 <= s <= L + 0.15 and d <= maximo for s, d, L in proy):
                dist = sum(d for _, d, _ in proy)
                if mejor is None or dist < mejor[0]:
                    mejor = (dist, nom, (a, b), [min(max(s, 0.0), L) for s, _, L in proy])
        if mejor:
            out.append(mejor)
    return sorted(out)


def crear(captura: dict) -> dict:
    datos = {'nombre': captura.get('nombre', 'Vivienda'), 'fachada': FACHADA, 'estancias': {}, 'medidas': [],
             'puertas': [], 'ventanas': [], 'hechas': []}
    usadas = set()
    for est in captura['estancias']:
        pts = [tuple(map(float, p)) for p in est['puntos']]
        if len(pts) < 3:
            continue
        if Polygon(pts).exterior.is_ccw is False:
            pass                                    # el sentido da igual: el ajuste lo tiene en cuenta
        ab = _abreviatura(est['nombre'], usadas)
        ids = [f'{ab}{i + 1}' for i in range(len(pts))]
        datos['estancias'][est['nombre']] = {'esquinas': ids, 'croquis': {i: list(p) for i, p in zip(ids, pts)},
                                             'altura': ALTURA_SUPUESTA}
        for a, b in itertools.combinations(ids, 2):        # la cámara: primera aproximación de toda la forma
            datos['medidas'].append({'de': a, 'a': b, 'valor': round(math.dist(datos['estancias'][est['nombre']]
                                     ['croquis'][a], datos['estancias'][est['nombre']]['croquis'][b]), 3),
                                     'modo': 'camara'})
    for k, pu in enumerate(captura.get('puertas', [])):
        cerca = _paredes_cercanas(datos, pu['puntos'])[:2]
        if not cerca:
            continue
        lados = []
        for _, nom, pared, s in cerca:
            lados.append({'pared': list(pared), 'jambas': sorted(round(v, 3) for v in s), 'modos': ['camara'] * 2})
        grosor = (round(cerca[0][0] / 2 + cerca[1][0] / 2, 3) if len(cerca) == 2 else FACHADA) or GROSOR_TABIQUE
        datos['puertas'].append({'id': f'P{k + 1}', 'lados': lados, 'grosor': max(grosor, 0.05),
                                 'grosor_modo': 'camara', 'altura': 2.03, 'abre': cerca[0][1], 'bisagra': 0})
    for k, ve in enumerate(captura.get('ventanas', [])):
        cerca = _paredes_cercanas(datos, ve['puntos'], maximo=0.6)
        if not cerca:
            continue
        _, nom, pared, s = cerca[0]
        datos['ventanas'].append({'id': f'V{k + 1}', 'estancia': nom, 'pared': list(pared),
                                  'jambas': sorted(round(v, 3) for v in s), 'antepecho': 0.90, 'dintel': 2.10,
                                  'fachada': FACHADA})
    return datos


# ---------------------------------------------------------------------------------------------------------------
# 2. Lo que falta medir
# ---------------------------------------------------------------------------------------------------------------
def _diagonales(e):
    """Diagonales que fijan la forma (n-3), desde esquinas que se ven una a otra."""
    es = e['esquinas']
    pol = Polygon([e['croquis'][n] for n in es]).buffer(1e-6)
    out = []
    for a, b in itertools.combinations(range(len(es)), 2):
        if (b - a) % len(es) in (1, len(es) - 1):
            continue
        if pol.contains(LineString([e['croquis'][es[a]], e['croquis'][es[b]]])):
            out.append((es[a], es[b]))
        if len(out) >= max(1, len(es) - 3):
            break
    return out


def _protocolo(datos):
    t = []
    for nom, e in datos['estancias'].items():
        es = e['esquinas']
        for a, b in zip(es, es[1:] + es[:1]):
            t.append({'id': f'pared:{a}:{b}', 'estancia': nom, 'tipo': 'distancia', 'puntos': [a, b],
                      'texto': f'{nom.capitalize()}: pared {a} – {b}', 'modo': 'laser',
                      'ayuda': 'Apoya la trasera del láser en una esquina y apunta a la otra, a la altura de siempre.'})
        for a, b in _diagonales(e):
            t.append({'id': f'diag:{a}:{b}', 'estancia': nom, 'tipo': 'distancia', 'puntos': [a, b],
                      'texto': f'{nom.capitalize()}: diagonal {a} – {b}', 'modo': 'laser',
                      'ayuda': 'De esquina a esquina, cruzando la estancia.'})
        t.append({'id': f'altura:{nom}', 'estancia': nom, 'tipo': 'valor', 'puntos': [],
                  'texto': f'{nom.capitalize()}: altura libre (suelo a techo)', 'modo': 'laser',
                  'ayuda': 'En el centro de la estancia, con el láser en el suelo apuntando al techo.'})
    for pu in datos['puertas']:
        ests = [_estancia_de(datos, l['pared'][0]) for l in pu['lados']]
        for i, lado in enumerate(pu['lados']):
            a = lado['pared'][0]
            for j, cual in enumerate(('más cercana', 'más lejana')):
                t.append({'id': f'jamba:{pu["id"]}:{i}:{j}', 'estancia': ests[i], 'tipo': 'jamba',
                          'puntos': [a, f'{pu["id"]}.{i}.{j}'],
                          'texto': f'Puerta {pu["id"]} ({ests[i].lower()}): de {a} a la jamba {cual}',
                          'modo': 'laser', 'ayuda': 'Hasta donde acaba la pared (no el tapajuntas). '
                          'Si son menos de 15 cm, con cinta.'})
        if len(pu['lados']) == 2:
            t.append({'id': f'grosor:{pu["id"]}', 'estancia': ests[0], 'tipo': 'valor', 'puntos': [],
                      'texto': f'Puerta {pu["id"]}: grosor de la pared en la puerta', 'modo': 'cinta',
                      'ayuda': 'Con cinta, de cara a cara de la pared, en la jamba.'})
        t.append({'id': f'alto:{pu["id"]}', 'estancia': ests[0], 'tipo': 'valor', 'puntos': [],
                  'texto': f'Puerta {pu["id"]}: altura del hueco', 'modo': 'laser', 'ayuda': 'Del suelo al dintel.'})
        t.append({'id': f'abre:{pu["id"]}', 'estancia': ests[0], 'tipo': 'opcion', 'puntos': [],
                  'texto': f'Puerta {pu["id"]}: ¿hacia dónde abre?', 'opciones': ests})
        lado = ests.index(pu['abre']) if pu['abre'] in ests else 0
        a, b = pu['lados'][lado]['pared']
        t.append({'id': f'bisagra:{pu["id"]}', 'estancia': pu['abre'], 'tipo': 'opcion', 'puntos': [],
                  'texto': f'Puerta {pu["id"]}: ¿dónde está la bisagra (mirando desde {pu["abre"].lower()})?',
                  'opciones': [f'En la jamba más cercana a {a}', f'En la jamba más cercana a {b}']})
    for v in datos['ventanas']:
        a = v['pared'][0]
        for j, cual in enumerate(('más cercano', 'más lejano')):
            t.append({'id': f'vjamba:{v["id"]}:{j}', 'estancia': v['estancia'], 'tipo': 'valor', 'puntos': [a],
                      'texto': f'Ventana {v["id"]} ({v["estancia"].lower()}): de {a} al borde {cual} del hueco',
                      'modo': 'laser', 'ayuda': 'Por dentro, hasta donde acaba la pared.'})
        for clave, texto, ayuda, modo in (
                ('antepecho', 'antepecho', 'Del suelo al alféizar.', 'laser'),
                ('dintel', 'dintel', 'Del suelo a lo alto del hueco.', 'laser'),
                ('fachada', 'grosor de la fachada', 'Con cinta, de la cara interior a la exterior.', 'cinta')):
            t.append({'id': f'{clave}:{v["id"]}', 'estancia': v['estancia'], 'tipo': 'valor', 'puntos': [],
                      'texto': f'Ventana {v["id"]}: {texto}', 'modo': modo, 'ayuda': ayuda})
    return t


def _estancia_de(datos, esquina):
    return next(n for n, e in datos['estancias'].items() if esquina in e['esquinas'])


def tareas(datos: dict) -> dict:
    viv = Vivienda(copy.deepcopy(datos))
    viv.ajustar()
    hechas = set(datos.get('hechas', []))
    pendientes = [t for t in _protocolo(datos) if t['id'] not in hechas]
    if not pendientes:
        sig = viv.siguiente()
        if sig:
            (a, b), _ = sig
            ea, eb = viv.estancia_punto(a), viv.estancia_punto(b)
            pendientes.append({'id': f'extra:{a}:{b}', 'estancia': ea, 'tipo': 'distancia', 'puntos': [a, b],
                               'texto': f'Medida extra: {viv.nombre_punto(a)} – {viv.nombre_punto(b)}',
                               'modo': 'laser', 'ayuda': 'Croquis la necesita para cuadrar la casa.' if ea == eb else
                               f'De {ea.lower()} a {eb.lower()}, con la puerta abierta.'})
    res = viv.resumen()
    sosp, vistas = [], set()
    for o, w in viv._red.sospechosas():
        if o.tipo == 'dist' and o.modo != 'camara':
            texto = f'«{o.etiqueta or "–".join(o.puntos)}» = {o.valor:.3f}'.replace('.', ',') + \
                    ' no cuadra con el resto: vuelve a medirla.'
        elif o.tipo == 'perp':
            texto = f'Las jambas de la puerta {o.puntos[0].split(".")[0]} no cuadran entre un lado y otro: ' \
                    'vuelve a medirlas.'
        else:
            continue
        if texto not in vistas:
            vistas.add(texto)
            sosp.append({'texto': texto, 'veces': round(w, 1)})
    return {'tareas': pendientes, 'total': len(_protocolo(datos)), 'hechas': len(hechas),
            'resumen': {'estancias_mm': round(res['estancias'][1] * 1000, 1),
                        'casa_mm': round(res['casa'][1] * 1000, 1)},
            'sospechosas': sosp[:3], 'puntos': {n: list(p) for n, p in viv.p.items()},
            'estancias': {n: e['esquinas'] for n, e in datos['estancias'].items()},
            'puertas': [{'id': p['id'], 'jambas': [list(viv.p[n]) for n in viv.jambas[(p['id'], 0)]]}
                        for p in datos['puertas']],
            'ventanas': [{'id': v['id'], 'pared': [list(viv.p[n]) for n in v['pared']], 'jambas': v['jambas']}
                         for v in datos['ventanas']]}


# ---------------------------------------------------------------------------------------------------------------
# 3. Respuestas
# ---------------------------------------------------------------------------------------------------------------
def responder(datos: dict, tid: str, valor, modo: str | None = None) -> dict:
    d = datos
    partes = tid.split(':')
    tipo = partes[0]
    if tipo in ('pared', 'diag', 'extra'):
        a, b = partes[1], partes[2]
        d['medidas'] = [m for m in d['medidas'] if not ({m['de'], m['a']} == {a, b} and m.get('modo') != 'camara')]
        d['medidas'].append({'de': a, 'a': b, 'valor': float(valor), 'modo': modo or 'laser'})
    elif tipo == 'altura':
        d['estancias'][partes[1]]['altura'] = float(valor)
    elif tipo == 'jamba':
        pu = _puerta(d, partes[1])
        lado = pu['lados'][int(partes[2])]
        j = int(partes[3])
        if j == 1 and f'jamba:{partes[1]}:{partes[2]}:0' in d.get('hechas', []):
            ancho = float(valor) - lado['jambas'][0]
            if not 0.45 <= ancho <= 2.5:
                raise ValueError(f'Con esa medida la puerta tendría {ancho:.2f} m de ancho: revisa las dos jambas.'
                                 .replace('.', ',', 1))
        lado['jambas'][j] = float(valor)
        lado.setdefault('modos', ['camara', 'camara'])[j] = modo or ('laser' if float(valor) >= 0.15 else 'cinta')
    elif tipo == 'grosor':
        pu = _puerta(d, partes[1])
        pu['grosor'], pu['grosor_modo'] = float(valor), modo or 'cinta'
    elif tipo == 'alto':
        _puerta(d, partes[1])['altura'] = float(valor)
    elif tipo == 'abre':
        _puerta(d, partes[1])['abre'] = valor
    elif tipo == 'bisagra':
        _puerta(d, partes[1])['bisagra'] = int(valor)
    elif tipo == 'vjamba':
        _ventana(d, partes[1])['jambas'][int(partes[2])] = float(valor)
    elif tipo in ('antepecho', 'dintel', 'fachada'):
        _ventana(d, partes[1])[tipo] = float(valor)
    if tid not in d.setdefault('hechas', []):
        d['hechas'].append(tid)
    return d


def _puerta(d, pid):
    return next(p for p in d['puertas'] if p['id'] == pid)


def _ventana(d, vid):
    return next(v for v in d['ventanas'] if v['id'] == vid)


# ---------------------------------------------------------------------------------------------------------------
# 4. Planos
# ---------------------------------------------------------------------------------------------------------------
def _elegir_seccion(viv):
    """La línea (vertical u horizontal) que corta más estancias y ventanas."""
    pols = viv.poligonos()
    pts = np.array(list(viv.p.values()))
    (x0, y0), (x1, y1) = pts.min(0), pts.max(0)
    ventanas = []
    for v in viv.datos['ventanas']:
        a, b = (np.array(viv.p[n]) for n in v['pared'])
        u = (b - a) / np.linalg.norm(b - a)
        ventanas.append(LineString([tuple(a + u * v['jambas'][0]), tuple(a + u * v['jambas'][1])]).buffer(0.4))
    mejor = None
    for vertical in (True, False):
        for t in np.linspace(0.15, 0.85, 29):
            if vertical:
                x = x0 + (x1 - x0) * t
                linea = [(x, y0 - 1.2), (x, y1 + 1.2)]
                mirando = (1, 0)
            else:
                y = y0 + (y1 - y0) * t
                linea = [(x0 - 1.2, y), (x1 + 1.2, y)]
                mirando = (0, 1)
            ls = LineString(linea)
            nota = sum(ls.intersects(p) for p in pols.values()) + sum(ls.intersects(v) for v in ventanas) * 0.6
            if mejor is None or nota > mejor[0]:
                mejor = (nota, {'linea': linea, 'mirando': mirando, 'titulo': "Sección A-A'"})
    return mejor[1]


def _elegir_alzado(viv):
    """La pared con más huecos (ventanas y puertas); a igualdad, la más larga."""
    mejor = None
    for nom, e in viv.datos['estancias'].items():
        es = e['esquinas']
        for a, b in zip(es, es[1:] + es[:1]):
            huecos = sum(v['pared'] == [a, b] or v['pared'] == [b, a] for v in viv.datos['ventanas'])
            huecos += sum(l['pared'] in ([a, b], [b, a]) for p in viv.datos['puertas'] for l in p['lados'])
            nota = (huecos, math.dist(viv.p[a], viv.p[b]))
            if mejor is None or nota > mejor[0]:
                mejor = (nota, {'estancia': nom, 'pared': (a, b), 'titulo': f'Alzado interior {nom.lower()}'})
    return mejor[1]


def planos(datos: dict, carpeta) -> list:
    from estudio import leer_config
    from imprimir import imprimir
    from planos import laminas
    from pathlib import Path
    viv = Vivienda(copy.deepcopy(datos))
    viv.ajustar()
    caj = {'fecha': datetime.date.today().strftime('%d/%m/%Y'), 'promotor': '', 'referencia': '',
           'direccion': datos.get('nombre', ''), **datos.get('cajetin', {})}
    seccion = datos.get('seccion') or _elegir_seccion(viv)
    alzado = datos.get('alzado') or _elegir_alzado(viv)
    dxf = laminas(viv, Path(carpeta) / 'estado-actual.dxf', caj, seccion, alzado)
    lam = leer_config()['laminas']
    return imprimir(dxf, [lam[k] for k in ('distribucion', 'cotas', 'alzado', 'seccion')])
