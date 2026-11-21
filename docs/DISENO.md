# Diseño — Croquis

Última actualización: 2026-11-21. Propuesta de Claude para que Jose la revise; nada de esto está decidido hasta que él
lo diga (lo decidido está en `DECISIONES.md`).

## Qué tiene que hacer

De una vivienda cualquiera (piso, unifamiliar, buhardilla, con muebles) al estado actual en la plantilla del estudio
(plantas, alzados y secciones, DXF y PDF), a ±5 mm (C-004), con el mínimo trabajo de quien mide:
1. Escanear andando con el iPad, sin ir esquina a esquina.
2. Lo que el escáner hace mal se corrige solo: paredes, huecos, pilares, vigas, techos.
3. Con el láser, solo las medidas que hacen falta, guiadas por la app y tecleadas (el GLM 40-31 no tiene Bluetooth).
4. Los planos salen solos.

**Principio de trabajo:** nada se da por bueno con una sola habitación. Cada paso se mide contra una referencia (láser)
en muchos casos distintos y tiene un criterio de aceptación con números. Si no lo cumple, no pasa al siguiente.

## Las piezas

| Paso | Entra | Sale | Hoy |
|---|---|---|---|
| 1. Esqueleto | `room.json` de RoomPlan | paredes, puertas, ventanas, estancias con nombre | `roomplan.py`: saca el esqueleto de la casa de Jose, con los fallos que él vio (huecos, techos, la diagonal) |
| 2. Encaje | nube LiDAR + esqueleto | nube en coordenadas de la planta | `alinear.py`: 42 % de puntos a <3 cm, error mediano 3,6 cm en el salón |
| 3. Corrección | nube encajada + esqueleto | caras reales de cada pared y sus extras | `detectar.py`: primer intento, **no fiable** (puertas tomadas por huecos, un mueble por pilar) |
| 4. Medidas guiadas | planta corregida + confianza de cada dato | la lista mínima de medidas; ajuste a ±5 mm | `ipad.py` pide medidas fijas por estancia; aún no ajustan el dibujo |
| 5. Planos | planta ajustada | EA.01–EA.04 en la plantilla, DXF y PDF | `planos.py` + `imprimir.py` (AutoCAD) |

**Entradas en esta fase (sin pagar nada):** el iPad captura con OpenPlan3D Capture (`room.json`) y con SiteScape (nube
PLY). Lo sube al PC con la página del servidor local. SiteScape solo pone datos de prueba: el programa lee un PLY
cualquiera y no depende de esa app.

**Más adelante, la app propia** grabará las dos cosas en una sola pasada. Lo primero que hay que probar es si RoomPlan
y la profundidad del LiDAR funcionan a la vez: Apple lo permite desde iOS 17
([init(arSession:)](https://developer.apple.com/documentation/roomplan/roomcapturesession/init(arsession:).md)), pero
hay desarrolladores que cuentan que la profundidad se pierde al arrancar RoomPlan
([foro](https://developer.apple.com/forums/thread/763400)). Si no funcionara, el plan B son dos pasadas.

## Paso 3, la corrección: qué tiene que resolver en cualquier casa

En cada pared de cada estancia, sin nada particular de una casa:
- **Cara real:** la superficie más exterior con puntos densos. Los muebles siempre quedan por dentro. No cuentan las
  puertas ni las ventanas (sus jambas parecen huecos).
- **Giro:** las diagonales falsas de RoomPlan se enderezan. Las de verdad se respetan.
- **Grosor:** si se ven las dos caras (casa escaneada entera), el grosor medido. Si no, el supuesto, y se pregunta.
- **Huecos y hornacinas:** ancho, fondo y alturas. Si cortan el plano de la planta, se dibujan; si no, salen en
  alzados y secciones.
- **Pilares y salientes:** solo si llegan al techo. Un mueble alto pegado a la pared no se distingue de un pilar, así
  que se pregunta con una pulsación («¿pilar o mueble?»).
- **Techos:** altura por estancia, vigas, descuelgues, falsos techos, techos inclinados.
- **Cada dato con su confianza.** Lo dudoso pasa al paso 4, como pregunta o como medida.

**Catálogo de casos que tiene que cubrir** (cada uno con al menos un escaneo de prueba):
- paredes fuera de escuadra, de verdad y falsas;
- estancias en L y estancias sin puerta (pasos);
- hornacinas y huecos de puerta tapiados;
- pilares exentos y adosados, vigas y descuelgues;
- falsos techos y techos inclinados;
- armarios empotrados, chimeneas, muebles altos pegados a la pared;
- espejos y cristales (dan puntos falsos detrás de la pared);
- puertas correderas y ventanas en esquina;
- dobles alturas, escaleras y varias plantas;
- fachadas exteriores en unifamiliar (C-006).

## Cómo se comprueba

1. **ARKitScenes, de Apple** ([GitHub](https://github.com/apple/ARKitScenes)): escaneos con iPad Pro con LiDAR
   (profundidad, poses y calibración, el mismo tipo de datos que la app). Una parte trae además la referencia de un
   escáner láser Faro proyectada en cada fotograma
   ([DATA.md](https://github.com/apple/ARKitScenes/blob/main/DATA.md)). Sirve para medir en cientos de habitaciones
   distintas cuánto se equivoca el paso 3 frente al láser.
   - **Licencia:** propia de Apple, no comercial
     ([LICENSE](https://github.com/apple/ARKitScenes/blob/main/LICENSE)). Vale para las pruebas mientras Croquis sea
     para Jose (C-009). Antes de VLANC o de vender, consultarlo con Apple (ARKitScenes-license@group.apple.com).
   - No trae RoomPlan: los pasos 1 y 2 se prueban con escaneos propios.
2. **Casas reales con medidas de láser de control:** la de Jose (comedor: 4,12 × 3,48 × 2,47 m), y más adelante obras
   de VLANC (los datos, fuera del repo, en `levantamientos/`).

**Criterios de aceptación (propuesta, por decidir con Jose):**
- **Paso 2:** error mediano del encaje por debajo de 1 cm. Si no, aviso y no se corrige nada.
- **Paso 3, caras de pared:** error de 2 cm o menos en el 95 % de las paredes. Es lo que da el LiDAR del iPad: unos
  2 cm de precisión y 4 cm de exactitud, según los estudios de `INVESTIGACION-CAPTURA.md`.
- **Paso 3, huecos y pilares de 20 cm o más de ancho y 4 cm o más de fondo:** se encuentra el 95 %, con un 5 % o menos
  de falsos.
- **Paso 4:** planta final a ±5 mm en las cotas que se acotan, con el menor número de medidas. Se cuenta cuántas pide
  por estancia.

## Resultados del banco (2026-11-21, primera tanda)

Código en `prototipo/banco/` (`arkit.py`: nubes y error del sensor; `faro.py`: muestra del láser Faro y su encaje en el
sistema del iPad; `paso3.py`: prueba del paso 3 con el esqueleto simulado). Datos en `levantamientos/arkitscenes/`,
fuera del repo. Tres escaneos de casas distintas (42444946, 42444966, 42445021).

- **El LiDAR del iPad mide corto, unos 2 cm, en las tres casas** (fotograma a fotograma, frente a la profundidad del
  láser en el mismo fotograma; no depende de la posición): −15 a −22 mm hasta 1 m, −19 a −21 mm de 1 a 2 m, −23 a
  −28 mm de 2 a 3 m. Cada cara de pared queda unos 2 cm hacia dentro, así que las estancias salen unos 4 cm pequeñas.
  Cuadra con el comedor de Jose: SiteScape da 4,03 m y el láser 4,12 m. **Se puede corregir**: es un sesgo, no ruido;
  una medida de láser por estancia lo calibra. Pendiente: confirmarlo en más casas.
- **Paso 3 (cara real de cada pared), contra el Faro en dos casas:** da lo mismo sea cual sea el error de partida del
  esqueleto (±15 cm, ±3°). Error mediano de 12 a 24 mm; entre el 47 y el 60 % de las paredes a 2 cm o menos. **No
  cumple** el criterio (95 %). Los fallos grandes (+94 y −119 mm) son superficies que el iPad ve por detrás de la cara
  real (cristal, espejo o un hueco que el Faro no ve): el «pico más exterior» se va a ellas.
- **Límite del propio banco:** la referencia tiene alrededor de 1 cm de incertidumbre. El encaje del Faro con la parte
  del láser proyectada en los fotogramas del iPad da una mediana de 11–13 mm de punto a plano, y en la primera casa el
  encaje falla (78 cm de altura); esa casa queda fuera hasta arreglarlo.
- **Lo que esto dice del método:** el LiDAR del iPad, solo, da del orden de ±2 cm, no ±5 mm, como ya decían los
  estudios. Su papel es la forma y los detalles (huecos, pilares, techos), corregir RoomPlan y decidir qué pocas medidas
  de láser hacen falta. Los ±5 mm salen del láser.

**Siguiente, por este orden:** corregir el sesgo de 2 cm y volver a medir; que el paso 3 no se vaya a superficies vistas
a través de cristales o espejos (exigir que la cara llegue al techo o al suelo y sea continua); arreglar el encaje de la
primera casa; bajar más casas (el banco ya es automático) hasta tener decenas de paredes por caso del catálogo.

## Orden de trabajo

1. Descargar unos pocos escaneos de ARKitScenes, variados y con referencia láser, y montar el banco de pruebas, que
   da el error de cada paso en milímetros.
2. Rehacer el paso 3 contra el banco hasta que cumpla. Después, la casa de Jose.
3. Paso 4: que las medidas guiadas salgan de la confianza de cada dato y ajusten el dibujo.
4. App propia (una pasada) cuando todo lo anterior funcione con el método actual.
