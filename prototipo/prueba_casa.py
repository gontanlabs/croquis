"""Prueba de viabilidad en la casa de Jose (2026-11-25): ¿el perímetro de cada estancia queda bajo 10 cm?

Jose (24-11): «si el perimetro de una vivienda se nos va 10 cm la hemos cagado». Se compara, estancia a estancia, con
cada pared medida con el láser (la verdad):
  A. solo el iPad (RoomPlan, escaneo del 21-11);
  B. el iPad corregido con 2 medidas de láser por estancia (las luces de pared a pared en las dos direcciones), que es
     lo que Croquis pide hoy (`ipad._tareas`): la forma del iPad, estirada en cada dirección hasta esas dos medidas.

    python prueba_casa.py hoja          → salida/prueba-casa/plano.png y hoja.html (paredes numeradas, luces)
    python prueba_casa.py veredicto     → lee salida/prueba-casa/medidas.txt y da el resultado

medidas.txt, una por línea, en metros (coma o punto): «12: 3,412» para la pared 12, «L-SALÓN-x: 4,10» y «L-SALÓN-y: …»
para las luces. Las paredes que no se midan no cuentan; una estancia entra en el veredicto si tiene todas sus paredes.
"""
from __future__ import annotations

import html
import math
import re
import sys
from pathlib import Path

import roomplan

AQUI = Path(__file__).resolve().parent
ESCANEO = AQUI.parent / 'levantamientos' / 'mi-casa' / 'ipad' / 'casa' / 'payload' / 'file_03455.json'
SALIDA = AQUI / 'salida' / 'prueba-casa'
MINIMO = 0.30      # tramos más cortos no son paredes (esquinas redondeadas del polígono)
UMBRAL = 0.10      # el criterio de Jose: 10 cm de perímetro
POLIGONOS = {}     # estancia → polígono (para saber de qué lado de cada pared está dentro)


def estancias():
    """{nombre: (paredes [(a, b, largo)], (x0, y0, x1, y1))} con las paredes de más de MINIMO, en orden."""
    pl = roomplan.importar(roomplan.leer(ESCANEO))
    out = {}
    for n, e in sorted(pl.estancias.items(), key=lambda kv: -kv[1].area):
        if n.startswith('ARMARIO'):
            continue
        p = e.simplify(0.03, preserve_topology=True)
        c = list(p.exterior.coords)[:-1]
        paredes = [(c[i], c[(i + 1) % len(c)], math.dist(c[i], c[(i + 1) % len(c)])) for i in range(len(c))]
        out[n] = ([w for w in paredes if w[2] >= MINIMO], e.bounds)
        POLIGONOS[n] = e
    return out


def numerar(est):
    """Número global de cada pared: [(n, estancia, a, b, largo)]."""
    lista, k = [], 1
    for nombre, (paredes, _) in est.items():
        for a, b, l in paredes:
            lista.append((k, nombre, a, b, l)); k += 1
    return lista


def hoja():
    from PIL import Image, ImageDraw, ImageFont
    est = estancias(); lista = numerar(est)
    SALIDA.mkdir(parents=True, exist_ok=True)
    xs = [p[0] for _, _, a, b, _ in lista for p in (a, b)]; ys = [p[1] for _, _, a, b, _ in lista for p in (a, b)]
    esc, m = 120, 60   # píxeles por metro y margen
    W, H = int((max(xs) - min(xs)) * esc) + 2 * m, int((max(ys) - min(ys)) * esc) + 2 * m
    pt = lambda p: (m + (p[0] - min(xs)) * esc, H - m - (p[1] - min(ys)) * esc)   # y hacia arriba, como en el plano
    im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
    try:
        f, fg = ImageFont.truetype('arialbd.ttf', 18), ImageFont.truetype('arial.ttf', 16)
    except OSError:
        f = fg = ImageFont.load_default()
    for n, nombre, a, b, l in lista:
        d.line([pt(a), pt(b)], fill='#151515', width=4)
    for nombre, (paredes, (x0, y0, x1, y1)) in est.items():
        d.text(pt(((x0 + x1) / 2, (y0 + y1) / 2)), nombre, fill='#666', font=fg, anchor='mm')
    for n, nombre, a, b, l in lista:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        nx, ny = -(b[1] - a[1]) / l, (b[0] - a[0]) / l          # normal de la pared, hacia dentro de su estancia
        from shapely.geometry import Point
        if not POLIGONOS[nombre].contains(Point(mx + 0.2 * nx, my + 0.2 * ny)):
            nx, ny = -nx, -ny
        c = pt((mx + 0.28 * nx, my + 0.28 * ny))
        d.ellipse([c[0] - 15, c[1] - 15, c[0] + 15, c[1] + 15], fill='#ffd400', outline='#151515', width=2)
        d.text(c, str(n), fill='#151515', font=f, anchor='mm')
    im.save(SALIDA / 'plano.png')
    filas = []
    for nombre, (paredes, (x0, y0, x1, y1)) in est.items():
        filas.append(f'<tr class="est"><td colspan="3">{html.escape(nombre)}</td></tr>')
        for n, nom, a, b, l in lista:
            if nom == nombre:
                filas.append(f'<tr><td>Pared {n}</td><td>{l:.2f} m</td><td class="h"></td></tr>')
        filas.append(f'<tr><td>L-{html.escape(nombre)}-x (luz de izquierda a derecha en el plano)</td><td>{x1 - x0:.2f} m</td><td class="h"></td></tr>')
        filas.append(f'<tr><td>L-{html.escape(nombre)}-y (luz de abajo a arriba en el plano)</td><td>{y1 - y0:.2f} m</td><td class="h"></td></tr>')
    (SALIDA / 'hoja.html').write_text(f'''<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Prueba de Croquis en casa</title>
<style>body{{font:15px/1.45 system-ui,sans-serif;margin:16px;color:#151515;background:#fff}} img{{max-width:100%}}
table{{border-collapse:collapse;width:100%;max-width:720px}} td{{border-bottom:1px solid #ddd;padding:6px 4px}}
.est td{{background:#151515;color:#fff;font-weight:600}} .h{{width:30%}} li{{margin:4px 0}}</style>
<h1>Prueba de Croquis en casa</h1>
<ol><li>Mide con el láser <b>cada pared numerada</b>: de esquina a esquina, a media altura, por donde no haya muebles. Si no se puede (un mueble que no se mueve), sáltala.</li>
<li>Mide en cada estancia las dos <b>luces</b>: apoya el láser en una pared y apunta a la de enfrente (izquierda-derecha y abajo-arriba según el plano).</li>
<li>Apunta cada medida así: <code>12: 3,412</code> o <code>L-SALÓN-x: 4,10</code>, y pásaselas a Claude.</li></ol>
<p>La columna central es lo que dice el iPad; no la mires al medir.</p>
<img src="plano.png" alt="Plano con las paredes numeradas">
<table>{"".join(filas)}</table></html>''', encoding='utf-8')
    print(f'{len(lista)} paredes en {len(est)} estancias → {SALIDA / "hoja.html"}')


def leer_medidas():
    m = {}
    for linea in (SALIDA / 'medidas.txt').read_text(encoding='utf-8').splitlines():
        r = re.match(r'\s*([^:]+):\s*([\d.,]+)', linea)
        if r:
            m[r.group(1).strip().upper()] = float(r.group(2).replace(',', '.'))
    return m


def veredicto():
    est = estancias(); lista = numerar(est); med = leer_medidas()
    filas, dentro_a, dentro_b, total = [], 0, 0, 0
    for nombre, (paredes, (x0, y0, x1, y1)) in est.items():
        mias = [(n, a, b, l) for n, nom, a, b, l in lista if nom == nombre]
        if not all(str(n) in med for n, *_ in mias):
            continue
        verdad = sum(med[str(n)] for n, *_ in mias)
        ipad = sum(l for *_, l in mias)
        lx, ly = med.get(f'L-{nombre}-X'), med.get(f'L-{nombre}-Y')
        if lx and ly:   # B: la forma del iPad estirada en x y en y hasta las dos luces
            sx, sy = lx / (x1 - x0), ly / (y1 - y0)
            corr = sum(math.hypot((b[0] - a[0]) * sx, (b[1] - a[1]) * sy) for n, a, b, l in mias)
        else:
            corr = None
        ea, eb = ipad - verdad, (corr - verdad if corr is not None else None)
        total += 1; dentro_a += abs(ea) < UMBRAL; dentro_b += eb is not None and abs(eb) < UMBRAL
        filas.append(f'{nombre:14} verdad {verdad:6.3f} m · iPad {ea * 1000:+6.0f} mm' + (f' · iPad + 2 láser {eb * 1000:+5.0f} mm' if eb is not None else ' · (faltan las luces)'))
    print('\n'.join(filas))
    print(f'\nEstancias completas: {total}. Perímetro bajo 10 cm: solo iPad {dentro_a}/{total}; iPad + 2 medidas de láser {dentro_b}/{total}.')


if __name__ == '__main__':
    {'hoja': hoja, 'veredicto': veredicto}[sys.argv[1] if len(sys.argv) > 1 else 'hoja']()
