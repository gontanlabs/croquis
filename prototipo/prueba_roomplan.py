"""Láminas EA.01–EA.04 de un escaneo de RoomPlan (OpenPlan3D Capture), con la plantilla del estudio.

    python prueba_roomplan.py <room.json> <salida.dxf> [nombre]
"""
import datetime
import math
import sys

import numpy as np
from shapely.geometry import LineString

import roomplan
from imprimir import imprimir
from estudio import leer_config
from planos import laminas


def elegir(pl):
    """Sección por la línea que corta más estancias y ventanas; alzado: la pared con ventana más larga del salón."""
    todo = [c for e in pl.estancias.values() for c in e.exterior.coords]
    (x0, y0), (x1, y1) = np.min(todo, 0), np.max(todo, 0)
    mejor = None
    for vertical in (True, False):
        for t in np.linspace(0.15, 0.85, 29):
            if vertical:
                x = x0 + (x1 - x0) * t; linea = [(x, y0 - 1.2), (x, y1 + 1.2)]; mira = (1, 0)
            else:
                y = y0 + (y1 - y0) * t; linea = [(x0 - 1.2, y), (x1 + 1.2, y)]; mira = (0, 1)
            ls = LineString(linea)
            nota = sum(ls.intersects(e) for e in pl.estancias.values()) + 0.6 * sum(ls.intersects(v['poligono']) for v in pl.ventanas)
            if mejor is None or nota > mejor[0]:
                mejor = (nota, {'linea': linea, 'mirando': mira, 'titulo': "Sección A-A'"})
    seccion = mejor[1]
    est = 'SALÓN' if 'SALÓN' in pl.estancias else max(pl.estancias, key=lambda n: pl.estancias[n].area)
    pol = pl.estancias[est]
    cs = list(pol.exterior.coords)[:-1]
    lados = list(zip(cs, cs[1:] + cs[:1]))
    def con_ventana(ab):
        seg = LineString(ab)
        return sum(seg.distance(LineString([tuple(v['dentro'][0]), tuple(v['dentro'][1])])) < 0.1 for v in pl.ventanas)
    pared = max(lados, key=lambda ab: (con_ventana(ab), math.dist(*ab)))
    return seccion, {'estancia': est, 'pared': pared, 'titulo': f'Alzado interior {est.lower()}'}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    r = roomplan.leer(sys.argv[1])
    pl0 = roomplan.importar(r)
    seccion, alzado = elegir(pl0)
    caj = {'fecha': datetime.date.today().strftime('%d/%m/%Y'), 'promotor': '', 'referencia': '',
           'direccion': sys.argv[3] if len(sys.argv) > 3 else 'Escaneo con iPad'}
    dxf = laminas(None, sys.argv[2], caj, seccion, alzado, crear_planta=lambda d: roomplan.importar(r, d))
    lam = leer_config()['laminas']
    for p in imprimir(dxf, [lam[k] for k in ('distribucion', 'cotas', 'alzado', 'seccion')]):
        print(p)
