"""Imprime láminas de un DXF a PDF con la consola de AutoCAD (sin abrir AutoCAD), con la configuración de página de
cada lámina (impresora «DWG To PDF» y las plumillas del estudio).

    python imprimir.py salida/vivienda.dxf "EA01 - Distribucion" "EA02 - Cotas" ...
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ACCORE = Path(os.environ.get('ACCORECONSOLE', r'C:\Program Files\Autodesk\AutoCAD 2027\accoreconsole.exe'))


def imprimir(dxf, laminas, carpeta=None) -> list[Path]:
    dxf = Path(dxf).resolve()
    carpeta = Path(carpeta or dxf.parent).resolve()
    pdfs = []
    lineas = ['FILEDIA', '0']
    for lam in laminas:
        corto = re.sub(r'[^A-Za-z0-9]+', '-', lam).strip('-').lower()
        pdf = carpeta / f'{dxf.stem}-{corto}.pdf'
        pdf.unlink(missing_ok=True)
        pdfs.append(pdf)
        ruta = str(pdf).replace('\\', '/')
        lineas += [f'(setvar "CTAB" "{lam}")',
                   f'(command "_-PLOT" "_N" "" "" "DWG To PDF.pc3" "{ruta}" "_N" "_Y")']
    lineas.append('(command "_.QUIT" "_Y")')
    with tempfile.TemporaryDirectory() as tmp:
        scr = Path(tmp) / 'imprimir.scr'
        scr.write_text('\r\n'.join(lineas) + '\r\n', encoding='cp1252', newline='')
        subprocess.run([str(ACCORE), '/i', str(dxf), '/s', str(scr), '/l', 'es-ES'], cwd=tmp,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
        # AutoCAD deja un informe de error al salir de la consola: no se guarda
        shutil.rmtree(Path(tmp) / 'ErrorReports', ignore_errors=True)
    return [p for p in pdfs if p.exists()]


if __name__ == '__main__':
    for p in imprimir(sys.argv[1], sys.argv[2:]):
        print(p)
