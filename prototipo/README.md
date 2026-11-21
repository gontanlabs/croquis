# Prototipo (prueba A)

El ajuste de Croquis en Python, antes de llevarlo a Android.

- `ajuste.py`: esquinas a partir del croquis y las medidas (cada una con su margen según cómo se tomó); hipótesis débil
  de escuadra; margen de cada distancia; medidas sospechosas (errores de tecleo); qué medir después.
- `estudio.py`: dibuja la planta dentro de una copia de la plantilla del estudio (muros y tabiques con su relleno,
  cotas con «≈» si no cumplen ±5 mm, nombre y superficie útil, cajetín de la lámina de cotas).
- `prueba_a.py`: estancia inventada en L, medidas simuladas de un láser de mano, bucle de «mide esto», error de tecleo
  y lámina. Escribe `salida/informe.txt` y `salida/prueba_a.dxf`.
- `test_ajuste.py`: `python test_ajuste.py`.

Configuración del estudio, fuera del repo: `~/.croquis/estudio.json` (ejemplo: `estudio.ejemplo.json`) y la plantilla
en DXF, `~/.croquis/plantilla.dxf`. Requisitos: `numpy`, `ezdxf`.

## Ver la lámina como la imprime el estudio

Con AutoCAD 2027 y su consola, sin abrir AutoCAD (el `.ctb` del estudio tiene que estar en la carpeta
`%APPDATA%\Autodesk\AutoCAD 2027\R26.0\esp\Plotters\Plot Styles`; copiado el 2026-11-21):

    accoreconsole.exe /i salida\prueba_a.dxf /s salida\imprimir.scr /l es-ES

`imprimir.scr` pone la lámina de cotas, hace `AUDIT` y la imprime con «DWG To PDF.pc3». AUDIT da dos avisos de un
bloque anónimo (`*E32`) que ya trae el plano base.
