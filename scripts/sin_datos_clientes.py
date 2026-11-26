"""Ningún dato de levantamientos reales en git (condición del traspaso a VLANC: CLAUDE.md).

Mira lo guardado (git ls-files) y lo preparado para el commit (git diff --cached). Sale con 1 si encuentra algo
dentro de levantamientos/ o un fichero de ~/.croquis. Lo llama scripts/comprobar.py, también en el pre-commit.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROHIBIDO = ("levantamientos/", ".croquis/")


def rutas(*args):
    r = subprocess.run(["git", "-C", str(RAIZ), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", check=True)
    return [linea.strip() for linea in r.stdout.splitlines() if linea.strip()]


def main():
    todas = set(rutas("ls-files")) | set(rutas("diff", "--cached", "--name-only", "--diff-filter=ACMR"))
    malas = sorted(p for p in todas if any(p.startswith(x) or f"/{x}" in p for x in PROHIBIDO))
    for p in malas:
        print(f"datos de clientes en git: {p}")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
