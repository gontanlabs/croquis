"""Descarga escaneos de ARKitScenes para el banco: solo lo que usa (profundidad del iPad y su confianza, trayectoria,
intrínsecos y profundidad del láser proyectada), unos 450 MB por escaneo, en levantamientos/arkitscenes/<video>/.

    python banco/descargar.py 8          → 8 escaneos más, cada uno de una casa distinta, con láser Faro
    python banco/descargar.py 42444966   → ese escaneo
"""
from __future__ import annotations

import csv
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = 'https://docs-assets.developer.apple.com/ml-research/datasets/arkitscenes/v1/raw'
RAIZ = Path(__file__).resolve().parents[2] / 'levantamientos' / 'arkitscenes'


def bajar(video, fold='Validation'):
    d = RAIZ / str(video); d.mkdir(parents=True, exist_ok=True)
    for f in ('lowres_wide.traj', 'lowres_wide_intrinsics.zip', 'wide_intrinsics.zip', 'confidence.zip',
              'highres_depth.zip', 'lowres_depth.zip'):
        carpeta = d / f.replace('.zip', '')
        if (d / f).exists() or (f.endswith('.zip') and carpeta.is_dir()):
            continue
        tmp = d / (f + '.tmp')
        urllib.request.urlretrieve(f'{URL}/{fold}/{video}/{f}', tmp)
        if f.endswith('.zip'):
            with zipfile.ZipFile(tmp) as z:
                z.extractall(d)
            tmp.unlink()
        else:
            tmp.rename(d / f)
    return d


def elegir(n):
    filas = list(csv.DictReader(open(RAIZ / 'metadata.csv')))
    hechas = {r['visit_id'] for r in filas if (RAIZ / r['video_id']).is_dir()}
    out = []
    for r in filas:
        if (r['fold'] == 'Validation' and r['is_in_upsampling'] == 'True' and r['has_laser_scanner_point_clouds'] == 'True'
                and r['visit_id'] not in hechas):
            out.append(r['video_id']); hechas.add(r['visit_id'])
        if len(out) == n:
            break
    return out


if __name__ == '__main__':
    a = sys.argv[1]
    videos = elegir(int(a)) if len(a) < 4 else [a]
    for v in videos:
        bajar(v)
        print(v, 'listo', flush=True)
