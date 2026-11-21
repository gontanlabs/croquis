"""Prueba de vivienda completa con un piso inventado (seis estancias, puertas, ventanas, alturas).

Se «mide» con el protocolo de campo (paredes, una diagonal por estancia, jambas de puertas y ventanas, grosores con
cinta, alturas) y Croquis pide lo que falte hasta que toda la casa cumple ±5 mm. Escribe los datos en el mismo formato
que un levantamiento real (`salida/vivienda.json`) para dibujar las láminas.

    python prueba_vivienda.py
"""
from __future__ import annotations

import copy
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

from ajuste import MARGENES
from vivienda import Vivienda

AQUI = Path(__file__).parent

# Planta nominal (caras interiores, metros). Esquinas en orden antihorario.
NOMINAL = {
    'SALÓN-COMEDOR': {'S1': (0, 0), 'S2': (5.0, 0), 'S3': (5.0, 4.6), 'S4': (0, 4.6)},
    'COCINA': {'C1': (5.1, 0), 'C2': (10.4, 0), 'C3': (10.4, 3.2), 'C4': (5.1, 3.2)},
    'PASILLO': {'P1': (5.1, 3.3), 'P2': (6.3, 3.3), 'P3': (6.3, 7.6), 'P4': (5.1, 7.6)},
    'DORMITORIO 1': {'D1-1': (0, 4.7), 'D1-2': (5.0, 4.7), 'D1-3': (5.0, 7.6), 'D1-4': (0, 7.6)},
    'BAÑO': {'B1': (6.4, 3.3), 'B2': (10.4, 3.3), 'B3': (10.4, 5.2), 'B4': (6.4, 5.2)},
    'DORMITORIO 2': {'D2-1': (6.4, 5.3), 'D2-2': (10.4, 5.3), 'D2-3': (10.4, 7.6), 'D2-4': (6.4, 7.6)},
}
ALTURAS = {'SALÓN-COMEDOR': 2.62, 'COCINA': 2.62, 'PASILLO': 2.45, 'DORMITORIO 1': 2.62, 'BAÑO': 2.45,
           'DORMITORIO 2': 2.62}
# Puertas: (id, [(pared, s desde la primera esquina)…], ancho, abre hacia, bisagra 0|1, altura)
PUERTAS = [
    ('Psal', [(('S2', 'S3'), 3.50), (('P4', 'P1'), None)], 0.82, 'SALÓN-COMEDOR', 0, 2.03),
    ('Pcoc', [(('C3', 'C4'), 4.33), (('P1', 'P2'), None)], 0.82, 'COCINA', 1, 2.03),
    ('Pd1', [(('D1-2', 'D1-3'), 0.30), (('P4', 'P1'), None)], 0.82, 'DORMITORIO 1', 0, 2.03),
    ('Pban', [(('B4', 'B1'), 0.88), (('P2', 'P3'), None)], 0.72, 'BAÑO', 1, 2.03),
    ('Pd2', [(('D2-4', 'D2-1'), 0.18), (('P2', 'P3'), None)], 0.82, 'DORMITORIO 2', 1, 2.03),
    ('Entrada', [(('P3', 'P4'), 0.15)], 0.90, 'PASILLO', 0, 2.10),
]
VENTANAS = [
    ('V1', 'SALÓN-COMEDOR', ('S1', 'S2'), 0.80, 2.20, 0.95, 2.15),
    ('V2', 'SALÓN-COMEDOR', ('S1', 'S2'), 2.90, 4.30, 0.95, 2.15),
    ('V3', 'COCINA', ('C1', 'C2'), 1.90, 3.30, 1.05, 2.15),
    ('V4', 'DORMITORIO 1', ('D1-3', 'D1-4'), 2.10, 3.50, 0.95, 2.15),
    ('V5', 'DORMITORIO 2', ('D2-3', 'D2-4'), 1.50, 2.90, 0.95, 2.15),
    ('V6', 'BAÑO', ('B2', 'B3'), 0.60, 1.20, 1.40, 2.00),
]
FACHADA = 0.30


def deformar(x, y):
    """La obra real: la planta nominal algo fuera de escuadra y un muro combado 2 cm junto al salón."""
    b = 0.02 * math.exp(-((x - 5.0) ** 2 + (y - 4.6) ** 2) / 2.25)
    return x + 0.004 * y + 0.0015 * x * y / 10 + b, y - 0.003 * x + 0.5 * b


def real(rng):
    r = {}
    for est, esq in NOMINAL.items():
        for n, (x, y) in esq.items():
            dx, dy = deformar(x, y)
            r[n] = (dx + rng.normal(0, 0.001), dy + rng.normal(0, 0.001))
    return r


def pie(p, a, b):
    a, b, p = (np.array(v, float) for v in (a, b, p))
    u = (b - a) / np.linalg.norm(b - a)
    return float((p - a) @ u)


def generar(semilla=2026):
    rng = np.random.default_rng(semilla)
    R = real(rng)

    def mide(v, modo='laser'):
        return round(v + rng.normal(0, MARGENES[modo]), 3)

    def d(a, b):
        return math.dist(R[a], R[b])

    datos = {'nombre': 'Piso inventado (prueba de vivienda)', 'fachada': FACHADA, 'estancias': {}, 'medidas': [],
             'puertas': [], 'ventanas': []}
    for est, esq in NOMINAL.items():
        ns = list(esq)
        datos['estancias'][est] = {'esquinas': ns, 'altura': mide(ALTURAS[est]),
                                   'croquis': {n: [round(x * 20) / 20, round(y * 20) / 20] for n, (x, y) in esq.items()}}
        for a, b in zip(ns, ns[1:] + ns[:1]):
            datos['medidas'].append({'de': a, 'a': b, 'valor': mide(d(a, b))})
        datos['medidas'].append({'de': ns[0], 'a': ns[2], 'valor': mide(d(ns[0], ns[2]))})
    for pid, lados, ancho, abre, bisagra, alto in PUERTAS:
        (pa, s), resto = lados[0], lados[1:]
        a, b = (np.array(R[n]) for n in pa)
        u = (b - a) / np.linalg.norm(b - a)
        j = [a + u * s, a + u * (s + ancho)]
        lados_out = [{'pared': list(pa), 'jambas': [mide(s, 'laser' if s >= .15 else 'cinta'),
                                                     mide(s + ancho)]}]
        grosor = None
        for pb, _ in resto:
            s2 = [pie(q, R[pb[0]], R[pb[1]]) for q in j]
            lados_out.append({'pared': list(pb), 'jambas': [mide(v, 'laser' if v >= .15 else 'cinta') for v in s2]})
            # grosor: distancia de la jamba a la otra cara
            a2, b2 = np.array(R[pb[0]]), np.array(R[pb[1]])
            u2 = (b2 - a2) / np.linalg.norm(b2 - a2)
            w = j[0] - a2
            grosor = mide(abs(float(u2[0] * w[1] - u2[1] * w[0])), 'cinta')
        pu = {'id': pid, 'lados': lados_out, 'ancho': ancho, 'altura': alto, 'abre': abre, 'bisagra': bisagra}
        pu['grosor'] = grosor if grosor else 0.30
        datos['puertas'].append(pu)
    for vid, est, pared, s1, s2, ante, dintel in VENTANAS:
        datos['ventanas'].append({'id': vid, 'estancia': est, 'pared': list(pared), 'jambas': [mide(s1), mide(s2)],
                                  'antepecho': mide(ante), 'dintel': mide(dintel), 'fachada': mide(FACHADA, 'cinta')})
    return datos, R


def jambas_reales(R, datos):
    """Las esquinas reales y la posición real de cada jamba (para simular medidas a las jambas)."""
    Rp = dict(R)
    for pid, lados, ancho, *_ in PUERTAS:
        (pa, s) = lados[0]
        a, b = (np.array(R[n]) for n in pa)
        u = (b - a) / np.linalg.norm(b - a)
        j = [a + u * s, a + u * (s + ancho)]
        for i, (pb, _) in enumerate(lados):
            if i == 0:
                pts = j
            else:
                a2, b2 = (np.array(R[n]) for n in pb)
                u2 = (b2 - a2) / np.linalg.norm(b2 - a2)
                pts = [a2 + u2 * pie(q, a2, b2) for q in j]
            for k, q in enumerate(pts):
                Rp[f'{pid}.{i}.{k}'] = tuple(q)
    return Rp


def mm(v):
    return f'{v * 1000:.1f} mm'.replace('.', ',')


def ejecutar(salida=print):
    datos, R = generar()
    rng = np.random.default_rng(7)
    viv = Vivienda(copy.deepcopy(datos))
    n0 = len(datos['medidas'])
    salida(f'1. Primera vuelta con el protocolo: {n0} medidas entre esquinas, '
           f'{len(datos["puertas"])} puertas y {len(datos["ventanas"])} ventanas.')
    viv.ajustar()
    Rp = jambas_reales(R, datos)
    pasos = 0
    salida('\n2. Croquis pide lo que falta (primero cada estancia a ±5 mm; después, lo que mejore la casa):')
    while True:
        res = viv.resumen()
        sig = viv.siguiente()
        if sig is None:
            break
        (a, b), despues = sig
        v = round(math.dist(Rp[a], Rp[b]) + rng.normal(0, MARGENES['laser']), 3)
        ea, eb = viv.estancia_punto(a), viv.estancia_punto(b)
        donde = ea if ea == eb else f'{ea} → {eb}, por la puerta'
        salida(f'   estancias ±{mm(res["estancias"][1])}, casa ±{mm(res["casa"][1])} → mide {viv.nombre_punto(a)} – '
               f'{viv.nombre_punto(b)} ({donde})')
        viv.datos['medidas'].append({'de': a, 'a': b, 'valor': v})
        viv.ajustar()
        pasos += 1
        if pasos > 30:
            raise RuntimeError('no cierra')
    res = viv.resumen()
    (pe, me), (pc, mc) = res['estancias'], res['casa']
    salida(f'   Resultado: dentro de cada estancia, ±{mm(me)} como mucho ({pe[0]}–{pe[1]}); '
           f'en la casa entera, ±{mm(mc)} ({pc[0]}–{pc[1]}).')
    salida(f'   {len(viv.tabiques)} parejas de caras tratadas como tabiques de grueso uniforme (±3 mm).')
    # Comparación con la real (las coordenadas ajustadas están en otro sistema: se comparan distancias)
    es = viv.esquinas()
    err = max(abs(math.dist(viv.p[a], viv.p[b]) - math.dist(R[a], R[b])) for a, b in itertools.combinations(es, 2))
    salida(f'\n3. Comparado con el piso real: el mayor error entre dos esquinas de la casa es {mm(err)}.')
    sup = {n: p.area for n, p in viv.poligonos().items()}
    salida('   Superficies útiles: ' + ', '.join(f'{n} {a:.2f} m²'.replace('.', ',') for n, a in sup.items())
           + f'; total {sum(sup.values()):.2f} m²'.replace('.', ','))
    (AQUI / 'salida').mkdir(exist_ok=True)
    (AQUI / 'salida' / 'vivienda.json').write_text(json.dumps(viv.datos, ensure_ascii=False, indent=1,
                                                              default=lambda o: None), encoding='utf-8')
    return {'pasos': pasos, 'resumen': res, 'error_max': err, 'vivienda': viv}




def laminas_prueba(viv):
    import datetime
    from planos import laminas
    hoy = datetime.date.today().strftime('%d/%m/%Y')
    return laminas(viv, AQUI / 'salida' / 'vivienda.dxf',
                   {'fecha': hoy, 'promotor': 'PRUEBA CROQUIS', 'direccion': 'Piso inventado (prueba de vivienda)',
                    'referencia': 'PRUEBA-V'},
                   seccion={'linea': [(7.8, -1.2), (7.8, 8.8)], 'mirando': (1, 0), 'titulo': "Sección A-A'"},
                   alzado={'estancia': 'COCINA', 'pared': ('C1', 'C2'), 'titulo': 'Alzado interior cocina'})


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    r = ejecutar()
    print()
    print('4. Láminas:', laminas_prueba(r['vivienda']))
