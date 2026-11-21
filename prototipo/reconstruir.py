"""Reconstrucción 3D del escaneo con COLMAP, usando las posiciones del móvil (ARCore) como conocidas.

Cada foto trae la matriz de la vista (posición y orientación en metros) y la proyección (de ella salen la focal y el
centro). Con eso no hace falta que COLMAP adivine dónde estaba la cámara: solo busca puntos comunes entre fotos y los
triangula, y el modelo sale en metros y en el mismo sistema que el escaneo (todas las habitaciones juntas).

    python reconstruir.py ../levantamientos/<casa>            # puntos dispersos
    python reconstruir.py ../levantamientos/<casa> --denso    # además, nube densa (paredes, muebles…)

Deja en <casa>/modelo/: database.db, conocido/ (posiciones del móvil), disperso/, denso/ y planta.png.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np

COLMAP = Path(os.environ.get('COLMAP', Path.home() / 'herramientas' / 'colmap' / 'bin' / 'colmap.exe'))


def _colmap(*args):
    exe = COLMAP if COLMAP.exists() else next(Path.home().glob('herramientas/colmap/**/colmap.exe'))
    print('colmap', ' '.join(map(str, args[:1])), flush=True)
    subprocess.run([str(exe), *map(str, args)], check=True)


def _fotos(captura: Path, escaneo=None):
    fotos = {}
    for linea in (captura / 'fotos.jsonl').read_text(encoding='utf-8').splitlines():
        if linea.strip():
            f = json.loads(linea)
            if (captura / f['fichero']).exists() and (escaneo is None or f.get('escaneo') == escaneo):
                fotos[f['fichero']] = f
    return [fotos[k] for k in sorted(fotos)]


def _intrinsecos(f):
    """PINHOLE desde la proyección de WebXR (por columnas) y el tamaño de la imagen (filas de arriba abajo)."""
    P, w, h = f['proyeccion'], f['ancho'], f['alto']
    fx, fy = P[0] * w / 2, P[5] * h / 2
    cx, cy = w * (1 - P[8]) / 2, h * (1 + P[9]) / 2
    return fx, fy, cx, cy


def _pose_colmap(f):
    """De la matriz de la vista de WebXR (cámara → mundo; x derecha, y arriba, z atrás) a COLMAP
    (mundo → cámara; x derecha, y abajo, z adelante): cuaternión y traslación."""
    M = np.array(f['vista'], float).reshape(4, 4).T
    R_wc, t_wc = M[:3, :3], M[:3, 3]
    giro = np.diag([1.0, -1.0, -1.0])
    R = giro @ R_wc.T
    t = -R @ t_wc
    return _cuaternion(R), t


def _cuaternion(R):
    tr = np.trace(R)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        q = [0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s]
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        q = [(R[2, 1] - R[1, 2]) / s, 0.25 * s, (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s]
    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        q = [(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s, 0.25 * s, (R[1, 2] + R[2, 1]) / s]
    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        q = [(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s, (R[1, 2] + R[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def reconstruir(casa: Path, denso=False, escaneo=None):
    casa = Path(casa).resolve()
    captura, modelo = casa / 'captura', casa / 'modelo'
    fotos = _fotos(captura, escaneo)
    print(f'{len(fotos)} fotos', flush=True)
    if modelo.exists():
        shutil.rmtree(modelo)
    modelo.mkdir()
    imagenes = modelo / 'imagenes'
    imagenes.mkdir()
    for f in fotos:
        shutil.copy2(captura / f['fichero'], imagenes / f['fichero'])
    fx, fy, cx, cy = _intrinsecos(fotos[0])
    db = modelo / 'database.db'
    _colmap('feature_extractor', '--database_path', db, '--image_path', imagenes,
            '--ImageReader.single_camera', 1, '--ImageReader.camera_model', 'PINHOLE',
            '--ImageReader.camera_params', f'{fx},{fy},{cx},{cy}', '--FeatureExtraction.use_gpu', 1)
    _colmap('exhaustive_matcher', '--database_path', db, '--FeatureMatching.use_gpu', 1)
    # Modelo «conocido»: las posiciones del móvil, con los números que COLMAP ha dado a cada imagen
    con = sqlite3.connect(db)
    ids = {nombre: (iid, cid) for iid, nombre, cid in con.execute('SELECT image_id, name, camera_id FROM images')}
    cams = con.execute('SELECT camera_id, width, height FROM cameras').fetchall()
    con.close()
    conocido = modelo / 'conocido'
    conocido.mkdir()
    (conocido / 'cameras.txt').write_text(''.join(f'{c} PINHOLE {w} {h} {fx} {fy} {cx} {cy}\n' for c, w, h in cams))
    lineas = []
    for f in fotos:
        iid, cid = ids[f['fichero']]
        q, t = _pose_colmap(f)
        lineas.append(f'{iid} {q[0]} {q[1]} {q[2]} {q[3]} {t[0]} {t[1]} {t[2]} {cid} {f["fichero"]}\n\n')
    (conocido / 'images.txt').write_text(''.join(lineas))
    (conocido / 'points3D.txt').write_text('')
    disperso = modelo / 'disperso'
    disperso.mkdir()
    # Las posiciones del móvil tienen algún milímetro y décima de grado de error: se admite algo más de desvío
    _colmap('point_triangulator', '--database_path', db, '--image_path', imagenes, '--input_path', conocido,
            '--output_path', disperso, '--Mapper.filter_max_reproj_error', 8, '--Mapper.tri_complete_max_reproj_error', 8,
            '--Mapper.tri_merge_max_reproj_error', 8)
    _colmap('model_converter', '--input_path', disperso, '--output_path', disperso / 'puntos.ply',
            '--output_type', 'PLY')
    if denso:
        d = modelo / 'denso'
        _colmap('image_undistorter', '--image_path', imagenes, '--input_path', disperso, '--output_path', d)
        _colmap('patch_match_stereo', '--workspace_path', d, '--PatchMatchStereo.geom_consistency', 1)
        _colmap('stereo_fusion', '--workspace_path', d, '--output_path', d / 'fused.ply')
    return modelo


def leer_ply(ruta: Path):
    """Puntos (x, y, z) de un PLY binario o de texto que escribe COLMAP."""
    datos = ruta.read_bytes()
    fin = datos.index(b'end_header') + len(b'end_header\n')
    cab = datos[:fin].decode('ascii', 'ignore').splitlines()
    n = next(int(l.split()[2]) for l in cab if l.startswith('element vertex'))
    props = [l.split() for l in cab if l.startswith('property')]
    tipos = {'float': 'f4', 'double': 'f8', 'uchar': 'u1', 'int': 'i4', 'uint': 'u4', 'short': 'i2', 'ushort': 'u2'}
    if any('binary_little_endian' in l for l in cab):
        dt = np.dtype([(p[2], '<' + tipos[p[1]]) for p in props])
        v = np.frombuffer(datos[fin:fin + n * dt.itemsize], dtype=dt)
        return np.stack([v['x'], v['y'], v['z']], 1).astype(float)
    filas = datos[fin:].decode().split('\n')[:n]
    return np.array([[float(x) for x in f.split()[:3]] for f in filas])


if __name__ == '__main__':
    esc = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--escaneo=')), None)
    reconstruir(Path(sys.argv[1]), '--denso' in sys.argv, esc)
