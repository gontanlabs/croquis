# Plantilla del estudio: lo que Croquis tiene que entregar

Leído del plano base A3 del estudio (DWG que Jose dejó en el escritorio el 2026-11-21; exportado a DXF con la consola de
AutoCAD 2027 sobre una copia). El plano no se copia al repo: lleva la marca y el cajetín del estudio. Grosores de cada
color: `PLUMILLAS.md`.

## Las láminas de estado actual

El plano base trae la serie completa de un proyecto de reforma interior (EA estado actual, ER estado reformado, C
acabados, I instalaciones, M carpintería y mobiliario, N normativa, S situación). Croquis hace la serie **EA**, todas en
A3 a 1/50:

| Lámina | Subtítulo del cajetín | Qué lleva |
|---|---|---|
| EA.01 | Distribución y usos | Planta: muros, tabiques, pilares, carpintería, sanitarios, nombres y usos |
| EA.02 | Cotas y superficies | La misma planta con cotas y superficies útiles y construidas |
| EA.03 | Alzado norte | Alzado |
| EA.04 | Sección A-A' | Sección |
| EA.05 | Demoliciones | Lo que se derriba (parte del proyecto nuevo; Croquis da la base) |

## Capas que tiene que usar Croquis

Modelo en **metros**. Cada capa con su color, que es el que fija la plumilla.

| Capa | Color (ACI) | Plumilla | Para |
|---|---|---|---|
| `Viv+Muros` | 5 | 0,30 negro | muros y fachadas seccionados |
| `Viv+Tabiques` | 52 | 0,25 negro | tabiques seccionados |
| `Viv+Pilares` | 5 | 0,30 negro | pilares |
| `Sombreados` | 254 | 0,10 gris #DBDBDB | relleno sólido de lo seccionado |
| `Viv+Ventanas` | 1 | 0,13 negro | ventanas |
| `Viv+Puertas` | 2 | 0,15 negro | puertas |
| `Viv+Proyecciones` | 253 | 0,10 gris #BABABA | vigas, falsos techos y lo que queda por encima |
| `Viv+Balcones` | 14 | 0,13 negro | balcones |
| `Viv+Escalera` | 252 | 0,10 gris #989898 | escaleras |
| `Viv+Sanitarios` | 4 | 0,09 negro | sanitarios |
| `Viv+Radiadores y caldera` | 253 | 0,10 gris | radiadores y caldera existentes |
| `Viv+Mobiliario fijo` | 1 | 0,13 negro | armarios y muebles de obra |
| `Viv+Cotas` | 250 | 0,10 gris #545454 | cotas (estilo `VLANC 50`) |
| `Viv+Superf UTIL` / `Viv+Superf CONST` | 3 / 11 | 0,07 verde / 0,05 | superficies útiles y construidas |
| `For+Txt planos` | 251 | 0,10 gris | nombres de estancias (estilos `TEXTOS VLANC 50`, Century Gothic) |
| `Alz+01` … `Alz+05` | 4, 1, 2, 94, 5 | 0,09 · 0,13 · 0,15 · 0,25 · 0,30 | alzados y secciones, de lo más lejano a lo cortado |

Cajetín: bloque `Cajetin_VLANC_A3`, con los atributos `NUM`, `ESCALA`, `DD/MM/AAAA`, `REFERENCIA`, `NOMBRE_PROYECTISTA`,
`NOMBRE_PROMOTOR`, `TÍTULO_PLANO`, `SUBTÍTULO_PLANO`, `DIRECCIÓN` y `PROYECTO`.

## Cómo encaja en Croquis (propuesta de Claude)

- **Croquis escribe dentro de la plantilla del estudio, no la imita.** Coge una copia del plano base, dibuja la vivienda
  en sus capas, rellena el cajetín de las láminas EA y la guarda como DXF (o DWG con AutoCAD). Capas, estilos, cajetín y
  presentaciones salen del propio estudio.
- **La plantilla es configurable:** el código no lleva nombres del estudio; cada estudio carga la suya. Es lo que deja
  el código neutro (`../CLAUDE.md`) y sirve a cualquier estudio.
- El PDF aplica las mismas plumillas para salir como un plano impreso en el estudio.

## Alzados y secciones (C-006, C-007)

- Alzados **interiores** siempre (cada pared que haga falta: cocina, baños…); **exteriores** solo en unifamiliares.
- Secciones: las suficientes para que se entienda todo y no quede ninguna medida por obtener. Croquis puede avisar de
  lo que ninguna sección explica todavía (cambios de altura de techo, vigas, escalones).
