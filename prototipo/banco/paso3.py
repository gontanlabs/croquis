"""Prueba del paso 3 (cara real de cada pared) con ARKitScenes, simulando el esqueleto de RoomPlan.

ARKitScenes no trae RoomPlan. Se toman las paredes del láser (el Faro completo encajado, `faro.py`, si está; si no,
el láser proyectado en los fotogramas) que limitan la estancia (estancia a un solo lado) y se
estropean como lo haría RoomPlan: desplazadas hasta ±15 cm y giradas hasta ±3°. El algoritmo, con la nube del iPad,
tiene que devolver cada cara a su sitio; se mide su error frente al láser en el centro y en los extremos del tramo.

    python banco/paso3.py <escaneo> [...]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arkit          # noqa: E402
import detectar       # noqa: E402


def paredes_limite(L, paredes, banda=(0.2, 1.5)):
    """Las paredes de referencia con la estancia a un solo lado. Devuelve (pared, lado interior ±1)."""
    s, t = np.percentile(L[:, 1], [1, 99])
    Q = L[(L[:, 1] > s + 0.1) & (L[:, 1] < t - 0.1)][:, [0, 2]]
    out = []
    for w in paredes:
        n, o = w['n'], w['o']; u = np.array([n[1], -n[0]])
        d = Q @ n - o; tt = Q @ u
        en = (tt > w['t0']) & (tt < w['t1'])
        mas = int((en & (d > banda[0]) & (d < banda[1])).sum()); menos = int((en & (d < -banda[0]) & (d > -banda[1])).sum())
        if max(mas, menos) > 5000 and min(mas, menos) < 0.05 * max(mas, menos):
            out.append((w, 1 if mas > menos else -1))
    return out


def probar(c: Path, semilla=0, repeticiones=3):
    rng = np.random.default_rng(semilla)
    L, P = arkit.cargar(c); L, P = L.astype(float), P.astype(float)
    if (Path(c) / 'faro.npy').exists():                           # referencia completa: el Faro encajado (faro.py)
        F = np.load(Path(c) / 'faro.npy').astype(float)
        from scipy.spatial import cKDTree
        d, _ = cKDTree(P).query(F, distance_upper_bound=0.10)
        L = F[np.isfinite(d)]                                     # lo que también ve el iPad
    suelo = float(np.percentile(P[:, 1], 1))
    Qp = np.c_[P[:, 0], P[:, 2], P[:, 1] - suelo]                 # planta: x, z; altura sobre el suelo
    res = []
    for w, lado_in in paredes_limite(L, arkit.paredes_referencia(L)):
        n, o = w['n'], w['o']; u = np.array([n[1], -n[0]])
        verdad = lambda t: n * o + u * t                           # punto de la cara real en la posición t
        for _ in range(repeticiones):
            desp = rng.uniform(-0.15, 0.15); giro = math.radians(rng.uniform(-3, 3))
            a = verdad(w['t0']) + n * desp; b = verdad(w['t1']) + n * desp
            m = (a + b) / 2; R = np.array([[math.cos(giro), -math.sin(giro)], [math.sin(giro), math.cos(giro)]])
            a, b = m + R @ (a - m), m + R @ (b - m)
            caras = detectar.caras_de_pared(a, b, Qp)
            # lado de detectar: +1 = izquierda de a→b (n_izq); el interior real es n·lado_in
            ab = (b - a) / np.linalg.norm(b - a); nizq = np.array([-ab[1], ab[0]])
            lado = 1 if nizq @ (n * lado_in) > 0 else -1
            fila = {'largo': round(w['t1'] - w['t0'], 2), 'desplazado_cm': round(desp * 100, 1),
                    'girado_grados': round(math.degrees(giro), 2)}
            if lado not in caras:
                fila['resultado'] = 'sin cara'; res.append(fila); continue
            cc = caras[lado]; Lab = np.linalg.norm(b - a)
            errores = []
            for t in (0.1 * Lab, 0.5 * Lab, 0.9 * Lab):
                p = a + ab * t + nizq * lado * (cc['c0'] + cc['c1'] * t)   # cara según el algoritmo
                errores.append(float((p - n * o) @ n) * lado_in)          # + hacia dentro de la estancia
            fila.update({'error_mm': [round(e * 1000, 1) for e in errores], 'ajuste_mm': cc['error_mm'],
                         'tramos': [tr['tipo'] for tr in cc['tramos']]})
            res.append(fila)
    return res


def resumen(res):
    ok = [r for r in res if 'error_mm' in r]
    e = np.abs([x for r in ok for x in r['error_mm']])
    return {'paredes_probadas': len(res), 'con_cara': len(ok),
            'error_mediano_mm': round(float(np.median(e)), 1) if len(e) else None,
            'p90_mm': round(float(np.percentile(e, 90)), 1) if len(e) else None,
            'max_mm': round(float(e.max()), 1) if len(e) else None,
            'dentro_2cm': round(float((e <= 20).mean()), 2) if len(e) else None}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for a in sys.argv[1:]:
        r = probar(Path(a))
        (Path(a) / 'paso3.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
        print(Path(a).name, resumen(r))
