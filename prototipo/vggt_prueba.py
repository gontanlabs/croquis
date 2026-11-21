"""Prueba de VGGT con las fotos de un escaneo: nube de puntos, puesta en metros con las posiciones del móvil.

Se ejecuta con el entorno aparte: ~/herramientas/vggt-env/Scripts/python vggt_prueba.py <casa> --escaneo=ID [--n=30]
Deja en <casa>/vggt-<ID>/: puntos.npy (x, y planta; h altura, metros), planta.png y el resultado de las paredes.
VGGT-1B es de uso no comercial (C-009): para VLANC, VGGT-1B-Commercial.
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
from reconstruir import _fotos  # noqa: E402


def umeyama(src, dst):
    """Semejanza (escala, giro, traslación) que lleva src sobre dst, por mínimos cuadrados."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    a, b = src - mu_s, dst - mu_d
    U, S, Vt = np.linalg.svd(b.T @ a / len(src))
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (a ** 2).sum(1).mean()
    return s, R, mu_d - s * R @ mu_s


def main(casa, escaneo, n):
    from vggt.models.vggt import VGGT
    from vggt.utils.geometry import unproject_depth_map_to_point_map
    from vggt.utils.load_fn import load_and_preprocess_images
    from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    casa = Path(casa)
    fotos = _fotos(casa / 'captura', escaneo)
    elegidas = [fotos[i] for i in np.linspace(0, len(fotos) - 1, min(n, len(fotos))).round().astype(int)]
    rutas = [str(casa / 'captura' / f['fichero']) for f in elegidas]
    salida = casa / f'vggt-{escaneo}'
    salida.mkdir(exist_ok=True)
    disp = 'cuda'
    tipo = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    modelo = VGGT.from_pretrained('facebook/VGGT-1B').to(disp).eval()
    imgs = load_and_preprocess_images(rutas).to(disp)
    with torch.no_grad(), torch.autocast('cuda', dtype=tipo):
        pred = modelo(imgs)
    extr, intr = pose_encoding_to_extri_intri(pred['pose_enc'], imgs.shape[-2:])
    prof = pred['depth'][0].float().cpu().numpy()
    conf = pred['depth_conf'][0].float().cpu().numpy()
    E = extr[0].float().cpu().numpy(); K = intr[0].float().cpu().numpy()
    pts = unproject_depth_map_to_point_map(prof, E, K)          # (S, H, W, 3) en el sistema de VGGT
    # Centros de cámara de VGGT (E: mundo → cámara, 3×4) y del móvil (ARCore)
    cv = np.array([-e[:, :3].T @ e[:, 3] for e in E])
    ca = np.array([np.array(f['vista']).reshape(4, 4).T[:3, 3] for f in elegidas])
    s, R, t = umeyama(cv, ca)
    err = np.linalg.norm((s * (R @ cv.T)).T + t - ca, axis=1)
    print(f'escala {s:.3f}; error de las cámaras tras alinear: mediana {np.median(err)*100:.1f} cm, máx {err.max()*100:.1f} cm')
    P = pts.reshape(-1, 3); c = conf.reshape(-1)
    P = P[c > np.percentile(c, 40)]
    Pa = (s * (R @ P.T)).T + t                                  # en metros, sistema ARCore (y arriba)
    plan = np.c_[Pa[:, 0], -Pa[:, 2], Pa[:, 1]]
    np.save(salida / 'puntos.npy', plan.astype(np.float32))
    print('puntos', len(plan))
    return salida


if __name__ == '__main__':
    esc = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--escaneo=')), None)
    n = int(next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--n=')), 30))
    main(sys.argv[1], esc, n)
