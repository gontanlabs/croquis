"""Dibujos de control del banco: nubes en planta (vista desde arriba, Y arriba) superpuestas en colores."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw


def planta(nubes, salida, esc=150, banda=(0.3, 0.3), colores=((0, 0, 0), (230, 40, 40), (40, 90, 230)), rayas=None,
           minimo=2):
    """nubes: lista de N×3 (x, y arriba, z). Se dibujan los puntos entre suelo+banda[0] y techo-banda[1]."""
    sel = []
    for P in nubes:
        s, t = np.percentile(P[:, 1], [1, 99])
        sel.append(P[(P[:, 1] > s + banda[0]) & (P[:, 1] < t - banda[1])][:, [0, 2]])
    todo = np.vstack(sel)
    x0, y0 = todo.min(0) - 0.3; x1, y1 = todo.max(0) + 0.3
    W, H = int((x1 - x0) * esc), int((y1 - y0) * esc)
    img = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(img)
    for k in np.arange(np.ceil(x0), x1, 1.0):
        d.line([((k - x0) * esc, 0), ((k - x0) * esc, H)], fill=(200, 200, 255))
    for k in np.arange(np.ceil(y0), y1, 1.0):
        d.line([(0, (k - y0) * esc), (W, (k - y0) * esc)], fill=(200, 200, 255))
    arr = np.array(img)
    for Q, col in zip(sel, colores):
        i = ((Q[:, 0] - x0) * esc).astype(int); j = ((Q[:, 1] - y0) * esc).astype(int)
        c = np.zeros((H, W), int); np.add.at(c, (np.clip(j, 0, H - 1), np.clip(i, 0, W - 1)), 1)
        arr[c >= minimo] = col
    img = Image.fromarray(arr); d = ImageDraw.Draw(img)
    for (a, b), col in (rayas or []):
        d.line([((a[0] - x0) * esc, (a[1] - y0) * esc), ((b[0] - x0) * esc, (b[1] - y0) * esc)], fill=col, width=2)
    img.save(salida)
    return (x0, y0, esc)
