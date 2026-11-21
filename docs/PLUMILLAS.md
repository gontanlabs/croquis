# Plumillas del estudio

Tabla de estilos de trazado del estudio (fichero `.ctb` de AutoCAD, versión del 16-09-2020, que Jose dejó en el
escritorio el 2026-11-21). El fichero no se copia al repo; aquí va lo que hace falta para que Croquis dibuje igual.

**Cómo funciona:** en el estudio el grosor y el color de impresión dependen del **color de AutoCAD (ACI)** de cada
línea, no de la línea en sí. Por eso el DXF de Croquis tiene que poner a cada capa el color ACI adecuado, y el PDF que
genere Croquis tiene que aplicar esta misma tabla para que salga igual que un plano impreso en el estudio.

## Colores principales (los que se usan para dibujar)

| ACI | En pantalla | Grosor (mm) | Imprime en |
|---|---|---|---|
| 1 | rojo | 0,13 | negro |
| 2 | amarillo | 0,15 | negro (escala de grises) |
| 3 | verde | 0,07 | verde #00B800 |
| 4 | cian | 0,09 | negro |
| 5 | azul | 0,30 | negro |
| 6 | magenta | 0,50 | negro |
| 7 | blanco/negro | 0,80 | negro |
| 8 | gris | 0,10 | gris #808080 |
| 9 | gris claro | 0,10 | gris #DCDCDC |
| 10 | rojo | 0,25 | rojo |
| 11 | — | 0,05 | gris #DBDBDB al 10 % |
| 12 | — | 0,45 | rojo |
| 14 | — | 0,13 | negro |
| 250–255 | grises | 0,10 | grises de #545454 a #FAFAFA |

## El resto

- 0,00 mm (la más fina), en negro: casi todos los demás colores (13, 15, 17, 19–29…).
- Con color propio o tramas suaves: 16 y 46 (rojo al 75 %), 18 (rojo 0,10 al 85 %), 30 (rojo 0,20), 33 (verde
  #6EDDA5 0,10 al 80 %), 40 (gris al 50 %), 42 (rojo al 20 %), 50 (azul 0,13 al 60 %), 52 y 94 (negro 0,25), 60 (azul
  0,07 al 25 %), 92 (gris 0,13 al 50 %), 100 (azul 0,18 al 70 %), 110 (naranja 0,05 al 50 %), 114 (rojo 0,18), 130
  (azul 0,18 al 50 %), 132 (verde #5D954A 0,09), 134 (azul 0,13), 150 (azul 0,09), 170 (rojo 0,13), 171 (azul 0,20),
  184 (azul 0,09 al 75 %), 200 y 251 (gris #767676 0,10), 240 (rojo #FF003F 0,09)…
- Color y grosor del propio objeto: 66 y 180 (0,35), 80, 172 y 175.

## Falta

Qué se dibuja con cada color en un estado actual (muro seccionado, tabiques, carpintería, cotas, textos, proyecciones,
mobiliario existente…). Lo dice Jose, o se lee de las capas de un DWG de estado actual del estudio, sin copiarlo al
repo (lleva datos de un cliente).
