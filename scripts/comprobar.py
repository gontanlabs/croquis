"""Comprobar el proyecto con UN comando: lo usan el pre-commit, la CI y Claude antes de dar algo por terminado.

    python scripts/comprobar.py            todo (tests, lint, compilación y documentos)
    python scripts/comprobar.py --rapido   solo lo rápido (antes de cada commit)

Detecta solo lo que hay en el repo (package.json, tests de Python, Gradle). Lo propio del proyecto va en PROPIAS.
Sale con 0 si todo está en verde y con 1 si algo falla.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Comprobaciones propias del proyecto: (nombre, orden, ¿rápida?). Ejemplo: ("render de muestra", ["python", "x.py"], False)
PROPIAS = [
    ("sin datos de clientes en git", [sys.executable, "scripts/sin_datos_clientes.py"], True),
    ("ruff (errores reales)", [sys.executable, "-m", "ruff", "check", "--quiet", "."], True),
]

# Croquis: los tests tardan menos de un segundo, así que también van antes de cada commit.
TESTS_RAPIDOS = True

MAX_LINEAS_CLAUDE = 100  # CLAUDE.md: solo lo que no se deduce del código


def documentos():
    """La plantilla: README, CLAUDE.md corto y los documentos de seguimiento, con «Siguiente paso» escrito."""
    fallos = []
    for rel in ("README.md", "CLAUDE.md", "docs/ROADMAP.md", "docs/DECISIONES.md", "docs/BITACORA.md"):
        if not (RAIZ / rel).is_file():
            fallos.append(f"falta {rel}")
    claude = RAIZ / "CLAUDE.md"
    if claude.is_file():
        n = len(claude.read_text(encoding="utf-8", errors="replace").splitlines())
        if n > MAX_LINEAS_CLAUDE:
            fallos.append(f"CLAUDE.md tiene {n} líneas (máximo {MAX_LINEAS_CLAUDE}: solo lo que no se deduce del código)")
    roadmap = RAIZ / "docs/ROADMAP.md"
    if roadmap.is_file():
        texto = roadmap.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^## Siguiente paso\s*\n(.*?)(?=^## |\Z)", texto, re.M | re.S)
        if not m:
            fallos.append("docs/ROADMAP.md no tiene la sección «## Siguiente paso»")
        elif not m.group(1).strip():
            fallos.append("«Siguiente paso» está vacío")
    return fallos


def ejecutar(orden):
    exe = shutil.which(orden[0])
    if not exe:
        return 127, f"no encuentro «{orden[0]}» (¿está instalado?)"
    r = subprocess.run([exe, *orden[1:]], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    salida = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode, "\n".join(salida[-25:])


def detectadas(rapido):
    """Las comprobaciones que el propio repo declara, sin inventar ninguna."""
    lista = []
    paquete = RAIZ / "package.json"
    if paquete.is_file():
        scripts = json.loads(paquete.read_text(encoding="utf-8")).get("scripts", {})
        for s in ("lint", "typecheck", "test", "build"):
            if s in scripts and (not rapido or s in ("lint", "typecheck")):
                lista.append((f"npm run {s}", ["npm", "run", s]))
    tests_py = list((RAIZ / "tests").glob("test_*.py")) if (RAIZ / "tests").is_dir() else []
    if tests_py and (not rapido or TESTS_RAPIDOS):
        lista.append(("pytest", [sys.executable, "-m", "pytest", "-q"]))
    # Solo los .py guardados en git: compileall recorría también lo ignorado (8 GB de datos en un repo: 9 s).
    py = subprocess.run(["git", "-C", str(RAIZ), "ls-files", "*.py"], capture_output=True, text=True,
                        encoding="utf-8", errors="replace").stdout.split()
    if py:
        lista.append(("python compila", [sys.executable, "-m", "py_compile", *py]))
    if (RAIZ / "gradlew").is_file() and not rapido:
        gradle = RAIZ / ("gradlew.bat" if sys.platform == "win32" else "gradlew")
        lista.append(("gradle test", [str(gradle), "test"]))
    lista += [(n, o) for n, o, r in PROPIAS if r or not rapido]
    return lista


def main():
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true", help="solo lo rápido (antes de cada commit)")
    a = ap.parse_args()

    rojo = False
    fallos = documentos()
    print(("✗" if fallos else "✓") + " documentos")
    for f in fallos:
        print(f"    {f}")
    rojo |= bool(fallos)

    for nombre, orden in detectadas(a.rapido):
        codigo, salida = ejecutar(orden)
        print(("✓ " if codigo == 0 else "✗ ") + nombre)
        if codigo != 0:
            rojo = True
            for linea in salida.splitlines():
                print(f"    {linea}")

    print("\nEN ROJO: no se guarda ni se da por terminado." if rojo else "\nTodo en verde.")
    return 1 if rojo else 0


if __name__ == "__main__":
    sys.exit(main())
