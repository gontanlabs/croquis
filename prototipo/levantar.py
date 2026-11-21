"""Levantamiento real: ajusta la vivienda, dice qué medir después y saca las láminas en PDF.

    python levantar.py ../levantamientos/<casa>/datos.json            # ajuste y siguientes medidas
    python levantar.py ../levantamientos/<casa>/datos.json --laminas  # además, DXF y PDF de las láminas

`datos.json` sigue el formato de `vivienda.Vivienda`; para las láminas lleva además «seccion» ({linea, mirando,
titulo}), «alzado» ({estancia, pared, titulo}) y «cajetin» ({fecha, promotor, direccion, referencia}).
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

from vivienda import Vivienda


def mm(v):
    return f'±{v * 1000:.1f} mm'.replace('.', ',')


def main(ruta, laminas=False, cuantas=5):
    ruta = Path(ruta)
    viv = Vivienda.leer(ruta)
    viv.ajustar()
    res = viv.resumen()
    (pe, me), (pc, mc) = res['estancias'], res['casa']
    print(f'Dentro de cada estancia: {mm(me)} como mucho ({pe[0]}–{pe[1]}).')
    print(f'Casa entera: {mm(mc)} ({pc[0]}–{pc[1]}).')
    sosp = viv._red.sospechosas()
    for o, w in sosp[:5]:
        print(f'  ¡Ojo! {o.etiqueta or "–".join(o.puntos)} = {o.valor:.3f} no cuadra con el resto '
              f'({w:.0f} veces su margen): vuelve a medirla.')
    # Las siguientes medidas, en orden, suponiendo que cada una se toma
    import copy
    prueba = Vivienda(copy.deepcopy(viv.datos))
    prueba.ajustar()
    pedidas = []
    for _ in range(cuantas):
        sig = prueba.siguiente()
        if sig is None:
            break
        (a, b), _peor = sig
        pedidas.append((prueba.nombre_punto(a), prueba.nombre_punto(b), prueba.estancia_punto(a),
                        prueba.estancia_punto(b)))
        import math
        prueba.datos['medidas'].append({'de': a, 'a': b, 'valor': round(math.dist(prueba.p[a], prueba.p[b]), 3)})
        prueba.ajustar()
    if pedidas:
        print('Mide ahora:')
        for a, b, ea, eb in pedidas:
            print(f'  {a} – {b}' + ('' if ea == eb else f'  ({ea} → {eb}, con la puerta abierta)'))
    else:
        print('No hace falta medir nada más.')
    if laminas:
        from imprimir import imprimir
        from planos import laminas as dibujar
        d = viv.datos
        caj = {'fecha': datetime.date.today().strftime('%d/%m/%Y'), **d.get('cajetin', {})}
        dxf = dibujar(viv, ruta.with_name('estado-actual.dxf'), caj, d['seccion'], d['alzado'])
        conf_lam = __import__('estudio').leer_config()['laminas']
        for p in imprimir(dxf, [conf_lam[k] for k in ('distribucion', 'cotas', 'alzado', 'seccion')]):
            print(p)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main(sys.argv[1], '--laminas' in sys.argv)
