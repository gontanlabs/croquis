"""Escaneos del iPad (OpenPlan3D Capture / RoomPlan) en Croquis: recibir el zip, planta, medidas guiadas y planos.

Medidas que se piden (con el láser apoyado en una pared y apuntando a la de enfrente, sin buscar esquinas):
- en cada estancia, sus dos luces (largo y ancho) y la altura libre;
- en cada puerta entre estancias, el grosor del tabique (con cinta);
- una vez, el grosor de la fachada en una ventana;
- en cada estancia, si tiene huecos, pilares o vigas que el escáner no ve.
"""
from __future__ import annotations

import datetime
import json
import re
import shutil
import unicodedata
import zipfile
from pathlib import Path

import roomplan


def _slug(t):
    s = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-') or 'vivienda'


def recibir(datos: Path, zip_: Path, nombre: str):
    ident = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    carpeta = datos / _slug(nombre) / 'ipad' / ident
    carpeta.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_) as z:
        nombres = z.namelist()
        room = None
        if 'manifest.json' in nombres:
            man = json.loads(z.read('manifest.json'))
            for f in man.get('files', []):
                if f.get('role') == 'original-geometry-json':
                    room = z.read(f['archivePath'])
        if room is None:
            raise ValueError('El zip no trae el modelo del escaneo (room.json). Exporta desde OpenPlan3D Capture '
                             'la captura completa.')
        (carpeta / 'room.json').write_bytes(room)
    shutil.move(str(zip_), carpeta / 'escaneo.zip')
    estado = {'nombre': nombre, 'id': f'{_slug(nombre)}/ipad/{ident}', 'respuestas': {}}
    (carpeta / 'estado.json').write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding='utf-8')
    return vista(datos, estado['id'])


def _carpeta(datos, ident):
    c = (datos / ident).resolve()
    if datos.resolve() not in c.parents:
        raise ValueError('escaneo desconocido')
    return c


def vista(datos: Path, ident: str):
    c = _carpeta(datos, ident)
    estado = json.loads((c / 'estado.json').read_text(encoding='utf-8'))
    pl = roomplan.importar(roomplan.leer(c / 'room.json'))
    tareas = _tareas(pl)
    hechas = estado['respuestas']
    return {
        'id': ident, 'nombre': estado['nombre'],
        'estancias': {n: [list(map(lambda v: round(v, 3), q)) for q in e.exterior.coords] for n, e in pl.estancias.items()},
        'macizo': _poligonos(pl.macizo),
        'puertas': [[list(map(float, q)) for q in p['jambas']] for p in pl.puertas],
        'ventanas': [[list(map(float, q)) for q in v['dentro']] for v in pl.ventanas],
        'tareas': [t for t in tareas if t['id'] not in hechas], 'total': len(tareas), 'hechas': len(hechas),
    }


def _poligonos(g):
    gs = list(g.geoms) if hasattr(g, 'geoms') else [g]
    return [[[round(x, 3), round(y, 3)] for x, y in p.exterior.coords] for p in gs if not p.is_empty]


def _tareas(pl):
    t = []
    for n, e in sorted(pl.estancias.items(), key=lambda kv: -kv[1].area):
        if n.startswith('ARMARIO'):
            continue
        x0, y0, x1, y1 = e.bounds
        t.append({'id': f'luz-x:{n}', 'estancia': n, 'tipo': 'numero', 'segmento': [[x0, (y0 + y1) / 2], [x1, (y0 + y1) / 2]],
                  'texto': f'{n.capitalize()}: luz de pared a pared en esta dirección',
                  'ayuda': f'El escáner dice {x1 - x0:.2f} m. Apoya el láser en una pared, por donde no haya muebles, y apunta a la de enfrente.'.replace('.', ',', 1)})
        t.append({'id': f'luz-y:{n}', 'estancia': n, 'tipo': 'numero', 'segmento': [[(x0 + x1) / 2, y0], [(x0 + x1) / 2, y1]],
                  'texto': f'{n.capitalize()}: luz de pared a pared en esta otra dirección',
                  'ayuda': f'El escáner dice {y1 - y0:.2f} m.'.replace('.', ',', 1)})
        t.append({'id': f'altura:{n}', 'estancia': n, 'tipo': 'numero', 'segmento': None,
                  'texto': f'{n.capitalize()}: altura libre (suelo a techo)',
                  'ayuda': f'El escáner dice {pl.viv.datos["estancias"][n]["altura"]:.2f} m. Si hay falso techo o viga, la altura más baja.'.replace('.', ',', 1)})
        t.append({'id': f'huecos:{n}', 'estancia': n, 'tipo': 'opcion', 'segmento': None,
                  'texto': f'{n.capitalize()}: ¿tiene huecos, pilares o vigas?', 'opciones': ['No', 'Sí']})
    for i, p in enumerate(pl.puertas):
        if p.get('grosor', 0) < 0.2:
            t.append({'id': f'grosor:{i}', 'estancia': p['estancia'], 'tipo': 'numero', 'segmento': [list(p['jambas'][0]), list(p['jambas'][1])],
                      'texto': 'Grosor del tabique en esta puerta', 'ayuda': 'Con cinta, de cara a cara de la pared, en la jamba.'})
    if pl.ventanas:
        v = pl.ventanas[0]
        t.append({'id': 'fachada', 'estancia': v['estancia'], 'tipo': 'numero', 'segmento': [list(v['dentro'][0]), list(v['dentro'][1])],
                  'texto': 'Grosor de la fachada en esta ventana', 'ayuda': 'Con cinta, de la cara interior a la exterior.'})
    for tt in t:
        if tt.get('segmento'):
            tt['segmento'] = [[float(a), float(b)] for a, b in tt['segmento']]
    return t


def responder(datos: Path, pedido):
    c = _carpeta(datos, pedido['id'])
    estado = json.loads((c / 'estado.json').read_text(encoding='utf-8'))
    estado['respuestas'][pedido['tarea']] = pedido['valor']
    (c / 'estado.json').write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding='utf-8')
    return vista(datos, pedido['id'])


def planos(datos: Path, ident: str):
    import sys
    from estudio import leer_config
    from imprimir import imprimir
    from planos import laminas
    from prueba_roomplan import elegir
    c = _carpeta(datos, ident)
    estado = json.loads((c / 'estado.json').read_text(encoding='utf-8'))
    r = roomplan.leer(c / 'room.json')
    pl0 = roomplan.importar(r)
    seccion, alzado = elegir(pl0)
    caj = {'fecha': datetime.date.today().strftime('%d/%m/%Y'), 'promotor': '', 'referencia': '',
           'direccion': estado['nombre']}
    dxf = laminas(None, c / 'estado-actual.dxf', caj, seccion, alzado, crear_planta=lambda d: roomplan.importar(r, d))
    lam = leer_config()['laminas']
    pdfs = imprimir(dxf, [lam[k] for k in ('distribucion', 'cotas', 'alzado', 'seccion')])
    base = c.relative_to(datos.resolve()).as_posix()
    return {'pdfs': [f'/planos/{base}/{p.name}' for p in pdfs]}
