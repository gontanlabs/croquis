"""Dibuja una planta ajustada dentro de una copia de la plantilla del estudio (DXF).

La plantilla y los nombres del estudio (capas, estilos, lámina, cajetín) se leen de una configuración fuera del repo
(`~/.croquis/estudio.json`; ejemplo en `estudio.ejemplo.json`): el código no lleva nombres de ningún estudio.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import ezdxf

from ajuste import Planta, Resultado, TOLERANCIA

CONFIG = Path(os.path.expanduser('~/.croquis/estudio.json'))


def leer_config(ruta: Path = CONFIG) -> dict:
    conf = json.loads(Path(ruta).read_text(encoding='utf-8'))
    conf['plantilla'] = os.path.expanduser(conf['plantilla'])
    return conf


def _centro_lamina(doc, nombre: str) -> tuple[float, float]:
    """Centro, en el modelo, de la ventana principal de la lámina (la más grande)."""
    lay = doc.layouts.get(nombre)
    vps = [v for v in lay.query('VIEWPORT') if v.dxf.width * v.dxf.height > 0]
    v = max(vps, key=lambda v: v.dxf.width * v.dxf.height)
    t, c = v.dxf.view_target_point, v.dxf.view_center_point
    return t[0] + c[0], t[1] + c[1]


def _desplazar(pts, grosores):
    """Cara exterior de cada pared: cada lado se aparta hacia fuera su grosor y se cortan los vecinos (inglete)."""
    n = len(pts)
    lineas = []
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        l = math.hypot(dx, dy)
        nx, ny = dy / l, -dx / l          # hacia fuera en un contorno antihorario
        t = grosores[i]
        lineas.append(((x1 + nx * t, y1 + ny * t), (dx, dy)))
    fuera = []
    for i in range(n):
        (p, d), (q, e) = lineas[i - 1], lineas[i]
        den = d[0] * e[1] - d[1] * e[0]
        s = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        fuera.append((p[0] + d[0] * s, p[1] + d[1] * s))
    return fuera


def _punto_libre(pts, paso: float = 0.05):
    """El punto de la estancia más alejado de sus paredes: ahí va el nombre, lejos de las cotas."""
    from ajuste import _dentro
    import numpy as np
    p = [np.array(q) for q in pts]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    mejor, dist = None, -1.0
    for x in np.arange(min(xs), max(xs), paso):
        for y in np.arange(min(ys), max(ys), paso):
            q = np.array((x, y))
            if not _dentro(q, p):
                continue
            d = min(_dist_segmento(q, a, b) for a, b in zip(p, p[1:] + p[:1]))
            if d > dist:
                mejor, dist = (float(x), float(y)), d
    return mejor


def _dist_segmento(q, a, b):
    import numpy as np
    ab = b - a
    t = max(0.0, min(1.0, float((q - a) @ ab / (ab @ ab))))
    return float(np.linalg.norm(q - (a + t * ab)))


def dibujar(planta: Planta, res: Resultado, grosores: list[float], nombre: str, salida: Path,
            cajetin: dict[str, str], conf: dict | None = None) -> Path:
    conf = conf or leer_config()
    capas = conf['capas']
    doc = ezdxf.readfile(conf['plantilla'])
    msp = doc.modelspace()

    pts = [res.puntos[n] for n in planta.contorno]
    gx = sum(p[0] for p in pts) / len(pts)
    gy = sum(p[1] for p in pts) / len(pts)
    cx, cy = _centro_lamina(doc, conf['laminas']['cotas'])
    pts = [(x - gx + cx, y - gy + cy) for x, y in pts]
    fuera = _desplazar(pts, grosores)
    n = len(pts)

    # Cada pared: su cara interior y su cara exterior, en su capa (sin líneas de inglete en las esquinas).
    for i in range(n):
        capa = capas['muro'] if grosores[i] >= conf['grosor_muro_desde'] else capas['tabique']
        for cara in (pts, fuera):
            msp.add_line(cara[i], cara[(i + 1) % n], dxfattribs={'layer': capa, 'color': 256})
    # Relleno de lo seccionado, pared por pared (el sombreado con hueco lo rellena entero en AutoCAD).
    for i in range(n):
        h = msp.add_hatch(dxfattribs={'layer': capas['relleno'], 'color': 256})
        h.set_solid_fill(color=256)
        h.paths.add_polyline_path([pts[i], pts[(i + 1) % n], fuera[(i + 1) % n], fuera[i]], is_closed=True)

    # Cotas interiores de cada pared, con su margen: las que no cumplen la tolerancia llevan «≈».
    # Se leen desde abajo o desde la derecha: el primer punto, el de la izquierda (o el de abajo si es vertical).
    for i in range(n):
        de, a = planta.contorno[i], planta.contorno[(i + 1) % n]
        margen = res.margen.get((de, a), res.margen.get((a, de)))
        p1, p2, sep = pts[i], pts[(i + 1) % n], conf['separacion_cota']
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        if dx < -1e-9 or (abs(dx) <= 1e-9 and dy < 0):
            p1, p2, sep = p2, p1, -sep
        dim = msp.add_aligned_dim(p1=p1, p2=p2, distance=sep, dimstyle=conf['estilo_cota'],
                                  text='<>' if 2 * margen <= TOLERANCIA else '≈<>',
                                  dxfattribs={'layer': capas['cotas']})
        dim.render()

    area = f'{res.area:.2f}'.replace('.', ',')
    mt = msp.add_mtext(f'{nombre}\\PS. útil: {area} m²',
                       dxfattribs={'layer': capas['textos'], 'style': conf['estilo_texto'],
                                   'char_height': conf['altura_texto']})
    mt.set_location(_punto_libre(pts), attachment_point=ezdxf.enums.MTextEntityAlignment.MIDDLE_CENTER)

    lam = doc.layouts.get(conf['laminas']['cotas'])
    for ins in lam.query('INSERT'):
        if ins.dxf.name == conf['cajetin']['bloque']:
            for att in ins.attribs:
                for clave, etiqueta in conf['cajetin']['campos'].items():
                    if att.dxf.tag == etiqueta and clave in cajetin:
                        att.dxf.text = cajetin[clave]

    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(salida)
    return salida
