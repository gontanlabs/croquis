"""VGGT con fotogramas de un vídeo normal (carpeta fotogramas/ en el directorio actual). Uso no comercial (C-009).

    cd <casa>/video && ~/herramientas/vggt-env/Scripts/python <ruta>/vggt_video.py 24
"""
import sys, glob
import numpy as np, torch
from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images
from vggt.utils.pose_enc import pose_encoding_to_extri_intri
from vggt.utils.geometry import unproject_depth_map_to_point_map
fs = sorted(glob.glob('fotogramas/*.jpg'))
n = int(sys.argv[1]) if len(sys.argv) > 1 else 24
sel = [fs[i] for i in np.linspace(0, len(fs) - 1, n).round().astype(int)]
m = VGGT.from_pretrained('facebook/VGGT-1B').to('cuda').eval()
imgs = load_and_preprocess_images(sel).to('cuda')
with torch.no_grad(), torch.autocast('cuda', dtype=torch.bfloat16):
    p = m(imgs)
E, K = pose_encoding_to_extri_intri(p['pose_enc'], imgs.shape[-2:])
d = p['depth'][0].float().cpu().numpy(); c = p['depth_conf'][0].float().cpu().numpy()
pts = unproject_depth_map_to_point_map(d, E[0].float().cpu().numpy(), K[0].float().cpu().numpy())
P = pts.reshape(-1, 3); cc = c.reshape(-1); P = P[cc > np.percentile(cc, 50)]
cams = np.array([-e[:, :3].T @ e[:, 3] for e in E[0].float().cpu().numpy()])
np.save('vggt_puntos.npy', P.astype(np.float32)); np.save('vggt_camaras.npy', cams)
print('puntos', len(P))
