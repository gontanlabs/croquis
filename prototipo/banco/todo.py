"""Pasa el banco entero por todas las casas descargadas y deja el resumen en levantamientos/arkitscenes/resumen.json.

Por casa: error del sensor por distancia (fotograma a fotograma), encaje del Faro y prueba del paso 3.

    python banco/todo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arkit   # noqa: E402
import faro    # noqa: E402
import paso3   # noqa: E402

RAIZ = faro.RAIZ


def casa(c: Path):
    r = {'escaneo': c.name}
    arkit.cargar(c)
    r['sensor'] = arkit.por_fotograma(c)
    if not (c / 'faro.npy').exists():
        r['encaje'] = faro.preparar(c)
    pr = paso3.probar(c)
    (c / 'paso3.json').write_text(json.dumps(pr, ensure_ascii=False, indent=1), encoding='utf-8')
    r['paso3'] = paso3.resumen(pr)
    ok = [x for x in pr if 'error_mm' in x]
    r['paso3']['sesgo_mm'] = round(float(np.median([x['error_mm'][1] for x in ok])), 1) if ok else None
    return r


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    f = RAIZ / 'resumen.json'
    todo = json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}
    for c in sorted(p for p in RAIZ.iterdir() if p.is_dir() and p.name.isdigit()):
        if c.name in todo and '--de-nuevo' not in sys.argv:
            continue
        try:
            todo[c.name] = casa(c)
        except Exception as e:                       # una casa que falla no para las demás
            todo[c.name] = {'escaneo': c.name, 'error': repr(e)}
        f.write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding='utf-8')
        print(json.dumps(todo[c.name], ensure_ascii=False), flush=True)
