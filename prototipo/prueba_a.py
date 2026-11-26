"""Prueba A: el ajuste sin cámara, con una estancia inventada.

Un salón en L con paredes que no van exactamente a 90°. Se «miden» las seis paredes con un láser de mano (con su
error simulado), y Croquis va diciendo qué medida falta hasta que todo el plano cumple ±5 mm. Después se teclea mal
una medida para ver si la detecta, y se dibuja la lámina de cotas dentro de la plantilla del estudio.

    python prueba_a.py            # informe y DXF en salida/
"""
from __future__ import annotations

import datetime
import itertools
import math
import sys
from pathlib import Path

import numpy as np

from ajuste import MARGENES, Planta

AQUI = Path(__file__).parent

# La estancia real (lo que Croquis no sabe): esquinas en orden antihorario, en metros.
REAL = {'A': (0.0, 0.0), 'B': (5.412, 0.0), 'C': (5.437, 2.874), 'D': (3.215, 2.866),
        'E': (3.198, 4.611), 'F': (-0.028, 4.597)}
# Lo que se dibuja a mano en la visita: a escuadra y redondeado.
CROQUIS = {'A': (0, 0), 'B': (5.40, 0), 'C': (5.40, 2.85), 'D': (3.20, 2.85), 'E': (3.20, 4.60), 'F': (0, 4.60)}
GROSORES = [0.30, 0.30, 0.10, 0.10, 0.15, 0.30]   # A-B, B-C, C-D, D-E, E-F, F-A


def distancia_real(de, a):
    (x1, y1), (x2, y2) = REAL[de], REAL[a]
    return math.hypot(x2 - x1, y2 - y1)


def mm(v):
    return f'{v * 1000:.1f} mm'.replace('.', ',')


def m(v):
    return f'{v:.3f} m'.replace('.', ',')


def ejecutar(dibujar_dxf: bool = True, salida=print):
    rng = np.random.default_rng(21112026)

    def tomar(de, a, modo='laser'):
        return round(distancia_real(de, a) + rng.normal(0, MARGENES[modo]), 3)   # el láser da milímetros

    planta = Planta(list(REAL), CROQUIS)
    salida('1. Se miden las seis paredes con el láser:')
    for de, a in zip(planta.contorno, planta.contorno[1:] + planta.contorno[:1]):
        v = tomar(de, a)
        planta.medir(de, a, v)
        salida(f'   {de}–{a}: {m(v)}')

    salida('\n2. Croquis pide medidas hasta que todo el plano cumple ±5 mm:')
    pasos = 0
    while True:
        res = planta.ajustar()
        (p, q), s = res.peor()
        sig = planta.siguiente()
        if sig is None:
            salida(f'   Cerrado: el peor margen es {p}–{q}, ±{mm(2 * s)}.')
            break
        (de, a), despues = sig
        v = tomar(de, a)
        salida(f'   Peor margen ahora: {p}–{q}, ±{mm(2 * s)} → «mide {de}–{a}» ({m(v)}): quedará en ±{mm(2 * despues)}')
        planta.medir(de, a, v)
        pasos += 1
        if pasos > 12:
            raise RuntimeError('no cierra')

    res = planta.ajustar()
    errores = {(de, a): abs(math.dist(res.puntos[de], res.puntos[a]) - distancia_real(de, a))
               for de, a in itertools.combinations(planta.contorno, 2)}
    peor_real = max(errores.values())
    salida(f'\n3. Comparado con la estancia real: el mayor error entre dos esquinas es {mm(peor_real)}.')
    salida('   Ángulos: ' + ', '.join(f'{n} {v:.2f}°'.replace('.', ',') for n, v in res.angulos.items()))
    salida(f'   Superficie útil: {res.area:.2f} m²'.replace('.', ','))

    # Error de tecleo: una medida de comprobación con dos cifras cambiadas.
    de, a = next((d, b) for d, b in itertools.combinations(planta.contorno, 2)
                 if not any({x.de, x.a} == {d, b} for x in planta.medidas) and planta._visible(res.puntos, d, b))
    buena = tomar(de, a)
    s = f'{buena:.3f}'
    mala = float(s[:-3] + s[-2] + s[-3] + s[-1])
    salida(f'\n4. Se teclea mal una comprobación: {de}–{a} = {m(mala)} (era {m(buena)}).')
    medida = planta.medir(de, a, mala)
    sospechosas = planta.ajustar().sospechosas
    detectada = bool(sospechosas) and sospechosas[0][0] is medida
    if sospechosas:
        sm, w = sospechosas[0]
        salida(f'   Croquis avisa: «{sm.de}–{sm.a} no cuadra con el resto (desvío {w:.0f} veces su margen): '
               f'vuelve a medirla».')
    else:
        salida('   Croquis NO la detecta.')
    planta.medidas.remove(medida)
    planta.medir(de, a, buena)
    res = planta.ajustar()

    ruta = None
    if dibujar_dxf:
        from estudio import dibujar
        hoy = datetime.date.today().strftime('%d/%m/%Y')
        ruta = dibujar(planta, res, GROSORES, 'SALÓN-COMEDOR', AQUI / 'salida' / 'prueba_a.dxf',
                       {'fecha': hoy, 'promotor': 'PRUEBA CROQUIS', 'direccion': 'Estancia inventada (prueba A)',
                        'referencia': 'PRUEBA-A'})
        salida(f'\n5. Lámina de cotas dibujada en la plantilla del estudio: {ruta}')

    return {'pasos': pasos, 'medidas': len(planta.medidas), 'cerrado': res.cerrado(),
            'error_max': peor_real, 'detectada': detectada, 'dxf': ruta}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    lineas = []

    def decir(t):
        print(t)
        lineas.append(t)

    r = ejecutar(salida=decir)
    (AQUI / 'salida').mkdir(exist_ok=True)
    (AQUI / 'salida' / 'informe.txt').write_text('\n'.join(lineas) + '\n', encoding='utf-8')
