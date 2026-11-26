# Prototipo (prueba A)

El ajuste de Croquis en Python, antes de llevarlo a Android.

- `ajuste.py`: esquinas a partir del croquis y las medidas (cada una con su margen según cómo se tomó); hipótesis débil
  de escuadra; margen de cada distancia; medidas sospechosas (errores de tecleo); qué medir después.
- `estudio.py`: dibuja la planta dentro de una copia de la plantilla del estudio (muros y tabiques con su relleno,
  cotas con «≈» si no cumplen ±5 mm, nombre y superficie útil, cajetín de la lámina de cotas).
- `prueba_a.py`: estancia inventada en L, medidas simuladas de un láser de mano, bucle de «mide esto», error de tecleo
  y lámina. Escribe `salida/informe.txt` y `salida/prueba_a.dxf`.
- Pruebas del ajuste: `../tests/test_ajuste.py` (`python scripts/comprobar.py` desde la raíz del repo).
- `vivienda.py`: la casa entera. Estancias unidas por las jambas de sus puertas (jamba a escuadra, ±3 mm) y caras de
  tabique paralelas (±3 mm, detectadas solas); qué medir después, también de una estancia a otra por una puerta.
- `planos.py`: láminas de distribución, cotas, alzado interior y sección dentro de la plantilla del estudio.
- `prueba_vivienda.py`: piso inventado de seis estancias medido con el protocolo de campo; láminas en `salida/`.
- `levantar.py <datos.json> [--laminas]`: un levantamiento real (en `../levantamientos/`, fuera de git).
- `imprimir.py <dxf> <láminas…>`: PDF con la consola de AutoCAD y las plumillas del estudio.

## Protocolo de campo (láser de mano y cinta)

1. Croquis a mano; cada estancia con nombre y sus esquinas numeradas dando la vuelta (S1, S2…). Salientes de más de 2 cm
   (pilares, bajantes) son esquinas.
2. En cada estancia: cada pared de esquina a esquina (a la misma altura en toda la casa), una diagonal (dos si es en L)
   y la altura libre (falsos techos, vigas y descuelgues, con su altura y dónde).
3. En cada puerta, por los dos lados: de una esquina a cada jamba; grosor de la pared en la puerta (con cinta); altura
   del hueco, hacia dónde abre y dónde está la bisagra.
4. En cada ventana: de una esquina a cada jamba (por dentro), antepecho, dintel y grosor de fachada (con cinta).
5. Croquis pide después lo que falte (diagonales o medidas de una estancia a otra con la puerta abierta).

Configuración del estudio, fuera del repo: `~/.croquis/estudio.json` (ejemplo: `estudio.ejemplo.json`) y la plantilla
en DXF, `~/.croquis/plantilla.dxf`. Requisitos: `numpy`, `ezdxf`.

## Ver la lámina como la imprime el estudio

Con AutoCAD 2027 y su consola, sin abrir AutoCAD (el `.ctb` del estudio tiene que estar en la carpeta
`%APPDATA%\Autodesk\AutoCAD 2027\R26.0\esp\Plotters\Plot Styles`; copiado el 2026-11-21):

    accoreconsole.exe /i salida\prueba_a.dxf /s salida\imprimir.scr /l es-ES

`imprimir.scr` pone la lámina de cotas, hace `AUDIT` y la imprime con «DWG To PDF.pc3». AUDIT da dos avisos de un
bloque anónimo (`*E32`) que ya trae el plano base.
