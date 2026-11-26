"""Ningún dato de clientes en git (condición del traspaso a VLANC: CLAUDE.md).

Mira lo guardado (git ls-files) y lo preparado para el commit (git diff --cached) y falla si encuentra:
- algo dentro de levantamientos/ (por la ruta, también con tildes: se lee con -z, sin comillas de git);
- una copia exacta de un fichero de ~/.croquis (la plantilla y la configuración del estudio), con cualquier nombre:
  se compara el contenido con git hash-object. En la CI no hay ~/.croquis y esa parte no hace nada.
Sale con 1 si encuentra algo. Lo llama scripts/comprobar.py, también en el pre-commit.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CLAVES = Path.home() / ".croquis"


def git(raiz, *args, entrada=None):
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, input=entrada, check=True)
    return r.stdout


def rutas_z(salida):
    return [p.decode("utf-8", "surrogateescape") for p in salida.split(b"\0") if p]


def revisar(raiz=RAIZ, claves=CLAVES):
    """Devuelve la lista de problemas (vacía si todo está bien)."""
    guardadas = rutas_z(git(raiz, "ls-files", "-z"))
    preparadas = rutas_z(git(raiz, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"))
    problemas = [f"datos de clientes en git: {p}" for p in sorted(set(guardadas) | set(preparadas))
                 if p.startswith("levantamientos/") or "/levantamientos/" in p]

    ficheros = [f for f in claves.rglob("*") if f.is_file()] if claves.is_dir() else []
    if ficheros:
        # Contenido de cada fichero del índice (lo guardado más lo preparado): modo, blob, etapa y ruta.
        indice = {}
        for linea in rutas_z(git(raiz, "ls-files", "-s", "-z")):
            datos, ruta = linea.split("\t", 1)
            indice.setdefault(datos.split()[1], []).append(ruta)
        hashes = git(raiz, "hash-object", "--stdin-paths", entrada="\n".join(map(str, ficheros)).encode()).split()
        for f, h in zip(ficheros, hashes):
            for ruta in indice.get(h.decode(), []):
                problemas.append(f"copia de ~/.croquis/{f.relative_to(claves).as_posix()} en git: {ruta}")
    return problemas


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    problemas = revisar()
    for p in problemas:
        print(p)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
