"""Panorámica 360 (equirectangular) de un punto del escaneo, cosida con la orientación de cada foto (ARCore).

No busca puntos comunes entre fotos: cada píxel de la panorámica sale de la foto que lo vio más de frente, con la
orientación exacta que dio el móvil. Las costuras quedan donde el móvil se movió entre fotos (girando a mano).

    python panoramica.py ../levantamientos/<casa> [--escaneo=ID]      # una panorámica por habitación y punto
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from reconstruir import _fotos


def coser(captura: Path, fotos, ancho=4096):
    alto = ancho // 2
    lon = (np.arange(ancho) + 0.5) / ancho * 2 * np.pi - np.pi
    lat = np.pi / 2 - (np.arange(alto) + 0.5) / alto * np.pi
    LON, LAT = np.meshgrid(lon, lat)
    d = np.stack([np.cos(LAT) * np.sin(LON), np.sin(LAT), -np.cos(LAT) * np.cos(LON)], -1).reshape(-1, 3)
    suma = np.zeros((d.shape[0], 3))
    peso = np.zeros(d.shape[0])
    for f in fotos:
        img = np.asarray(Image.open(captura / f['fichero']).convert('RGB'), float)
        H, W = img.shape[:2]
        M = np.array(f['vista'], float).reshape(4, 4).T
        c = d @ M[:3, :3]                    # dirección en ejes de la cámara (x derecha, y arriba, z atrás)
        P = f['proyeccion']
        delante = c[:, 2] < -1e-6
        w = -c[:, 2]
        nx = (P[0] * c[:, 0] + P[8] * c[:, 2]) / np.where(delante, w, 1)
        ny = (P[5] * c[:, 1] + P[9] * c[:, 2]) / np.where(delante, w, 1)
        dentro = delante & (np.abs(nx) < 1) & (np.abs(ny) < 1)
        u = ((nx[dentro] * 0.5 + 0.5) * (W - 1)).astype(int)
        v = ((1 - (ny[dentro] * 0.5 + 0.5)) * (H - 1)).astype(int)
        pw = (1 - nx[dentro] ** 2) * (1 - ny[dentro] ** 2)        # más peso al centro de cada foto
        pw = pw ** 4
        suma[dentro] += img[v, u] * pw[:, None]
        peso[dentro] += pw
    out = np.zeros_like(suma)
    hay = peso > 0
    out[hay] = suma[hay] / peso[hay, None]
    out[~hay] = 40
    return Image.fromarray(out.reshape(alto, ancho, 3).clip(0, 255).astype(np.uint8))


if __name__ == '__main__':
    casa = Path(sys.argv[1])
    esc = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--escaneo=')), None)
    fotos = _fotos(casa / 'captura', esc)
    grupos = collections.defaultdict(list)
    for f in fotos:
        grupos[(f['habitacion'], f['punto'])].append(f)
    salida = casa / 'panoramicas'
    salida.mkdir(exist_ok=True)
    for (hab, punto), fs in grupos.items():
        ruta = salida / f'{hab.lower()}-punto{punto}.jpg'
        coser(casa / 'captura', fs).save(ruta, quality=90)
        print(ruta, len(fs), 'fotos')
