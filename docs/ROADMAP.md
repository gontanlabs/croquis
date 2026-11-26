# Roadmap — Croquis

Última actualización: 2026-11-22 (cierre: banco de pruebas con diez casas; C-011 a C-013).

## Estado

2026-11-21: proyecto creado; idea, salidas, precisión y reglas del traspaso a VLANC, decididas (`docs/DECISIONES.md`).
**Prueba A hecha con una estancia inventada** (`prototipo/`, en Python): salón en L con paredes fuera de escuadra; con
las seis paredes y cuatro medidas que pide Croquis, el plano cierra a ±4,4 mm y el error real máximo es de 4,1 mm;
detecta una medida mal tecleada; la lámina EA.02 sale dentro de la plantilla del estudio y AutoCAD la imprime con sus
plumillas (`prototipo/README.md`).
**Vivienda completa** (`prototipo/vivienda.py`, `planos.py`): piso inventado de seis estancias; red de toda la casa
unida por las jambas de las puertas (con la jamba a escuadra, ±3 mm) y las dos caras de cada tabique paralelas (±3 mm);
con la primera vuelta del protocolo cada estancia cierra a ±4,2 mm y la casa entera a ±10,7 mm (error real 11,7 mm):
lo que queda es el grosor de los tabiques sin puerta, que no se puede medir desde dentro. Láminas EA.01 (distribución),
EA.02 (cotas), EA.03 (alzado interior) y EA.04 (sección), impresas con AutoCAD y revisadas.

**Tarde del 2026-11-21:** escaneo de la casa de Jose con el iPad (OpenPlan3D Capture) y del salón con SiteScape
(nube LiDAR); la nube se encaja con la planta y ve techo a 2,48 m, la diagonal falsa y el hueco de arriba a la derecha.
La corrección automática (`detectar.py`, cambios sin guardar en git) **no es fiable** todavía. Jose pidió parar los
parches (C-011): diseño en `docs/DISENO.md`, banco de pruebas con ARKitScenes antes de seguir.
**Noche del 2026-11-21:** banco de pruebas (`prototipo/banco/`) con diez casas de ARKitScenes y el láser Faro de
referencia. El LiDAR del iPad mide de 12 a 22 mm corto hasta 2 m en las diez (sesgo corregible); el paso 3 (cara real de
cada pared) deja entre el 33 y el 78 % de las paredes a 2 cm o menos: **no cumple** todavía.

## Lo que se sabe (investigación del 2026-11-21)

- **Android no tiene LiDAR.** La profundidad de ARCore sale de la imagen: en la única prueba con cifras encontrada, error
  medio de 23–30 cm frente a LiDAR ([arXiv 2204.01693](https://arxiv.org/pdf/2204.01693)). Para medir, Google
  recomienda «Raw Depth», más precisa pero con huecos
  ([Google](https://developers.google.com/ar/develop/java/depth/raw-depth)). ARCore no trae una API que devuelva la
  habitación como modelo ([GitHub](https://github.com/google-ar/arcore-android-sdk/issues/1772)).
- **Ni el iPhone con LiDAR llega:** RoomPlan ronda los 15 cm según un desarrollador
  ([foro de Apple](https://developer.apple.com/forums/thread/712500)); falla en alturas si no se ve el techo y en
  ventanas juntas ([TU Delft, 2026](https://3d.bk.tudelft.nl/ken/files/26_giorgos.pdf)).
- **Conclusión:** la cámara da la forma (paredes, huecos, cómo se unen las habitaciones); los ±5 mm salen de las medidas.
- **Alternativa real: magicplan**, en Android, con láser por Bluetooth (Leica DISTO, Bosch GLM «C», Stabila…:
  [PrecisionLink](https://magicplan.app/blog/magicplan-launches-precisionlink)).
- **El láser de Jose, Bosch GLM 40-31** (0601075000): en su ficha oficial no aparece Bluetooth, y en Bosch los que
  conectan llevan «C» en el nombre. Sus medidas se teclean.

## Plan (C-010: producto con app para iPhone/iPad Pro y panel web)

1. ✅ Investigación de captura (`docs/INVESTIGACION-CAPTURA.md`): el móvil Android sin LiDAR no basta; el iPad Pro con
   RoomPlan sí (comedor: −5 mm de ancho; los 18 cm del largo eran un hueco que RoomPlan simplifica).
2. ☐ **Fase 1, sin app propia:** escaneo con OpenPlan3D Capture (gratis; el editor web de openPlan3D es MIT, el código de la app iOS no lo he localizado) y nube LiDAR con SiteScape (solo datos de prueba, C-012) → Croquis importa su `plan.json` →
   medidas guiadas tecleadas (el GLM 40-31 no tiene Bluetooth) con preguntas de huecos y salientes por pared → planos
   EA.01–EA.04 en la plantilla. Primera prueba: el comedor de Jose.
3. ☐ **Fase 2, app propia de iPad/iPhone** con Expo y expo-roomplan (sin Mac): escaneo y medidas en la misma app;
   láser Bluetooth opcional.
4. ☐ **Panel web** del estudio: subir la plantilla, ver las viviendas, descargar DXF/PDF.
5. ☐ PDF sin AutoCAD (plumillas aplicadas por el programa).
6. ☐ Probarlo en VLANC (primer cliente) y preparar la venta (suscripción por estudio).

Lo hecho antes (prototipo en Python, `prototipo/`): ajuste de toda la casa, láminas en la plantilla del estudio,
servidor y app web de pruebas en Android (descartada como captura).

## Por decidir

- **Criterios de aceptación del diseño** (`docs/DISENO.md`): los números son propuesta de Claude; Jose aprobó el método
  (C-013), no los números.

- Cuadro de superficies de la plantilla: hoy queda con sus valores de ejemplo; Croquis debería rellenarlo.
- Casa entera a ±5 mm: entre estancias separadas por un tabique sin puerta no se llega desde dentro (queda en ±1 cm);
  ¿basta con que cada estancia, sus puertas y grosores cumplan ±5 mm y la casa se dé con su margen?
- Dónde cortar las secciones y qué alzados sacar: hoy se eligen a mano; C-007 pide las suficientes.

- Tecnología de la app (lenguaje y librerías de Android, del ajuste y de la salida DXF/PDF): Claude la propone al
  empezar la prueba A.
- Identificador Android neutro (ni `com.gontanlabs…` ni `com.vlanc…`, o ya el de VLANC).
- ✅ Plumillas (`docs/PLUMILLAS.md`) y plantilla del estudio (`docs/PLANTILLA.md`): láminas EA.01–EA.05 en A3 a 1/50,
  capas, cajetín. Propuesta de Claude: Croquis escribe dentro de una copia de la plantilla, que cada estudio carga.
- Al traspasar: si se reescribe la autoría de los commits; si sale en el portfolio (con permiso de VLANC).

## Siguiente paso

**Método (piloto, 26-11):** cada tarea en su sesión abierta en esta carpeta, con `python scripts/comprobar.py` antes de cada commit y el `revisor` al terminar (ver `CLAUDE.md`).

**Veredicto de viabilidad y lista de compra:** ya no llega antes del Black Friday (Jose, 26-11, 17:15: «es de noche ya y no va a dar tiempo para mañana»); si se compra el láser, en tienda con devolución y se prueba dentro del plazo. **Kit de la prueba listo (25-11):** `prototipo/prueba_casa.py hoja` genera `prototipo/salida/prueba-casa/hoja.html` con el plano del escaneo del 21-11 (38 paredes numeradas en 7 estancias; no hace falta escanear otra vez); Jose mide cada pared y las dos luces de cada estancia con el láser, apunta «12: 3,412» y `prueba_casa.py veredicto` da, por estancia, el error del perímetro solo con el iPad y con las 2 medidas de láser. Hecho el 24-11 con el banco: viable si las cotas las da el láser (2 por estancia, p95 8 mm; ver `docs/INVESTIGACION-CAPTURA.md`). Falta la prueba en casa de Jose (salón y comedor, cada pared con láser) **[Jose]** y sus tiempos de levantamiento para la cuenta de si compensa **[Jose]**. Después, seguir con el método del banco (abajo).

Seguir con el método del banco (Jose, C-013: «si tienes un metodo vamos con el»; al pausar: «pausamos y seguimos
mañana»): leer `levantamientos/arkitscenes/resumen.json`, mirar las paredes que fallan casa por casa (dibujos de
control), corregir el sesgo del sensor y las superficies vistas a través de cristales o espejos, y volver a medir hasta
cumplir. Terminar la undécima casa (42446517) con `python banco/todo.py`.

## Pendiente de Jose

1. ✅ Hecho el 24-11: VGGT (modelo y entorno) y el instalador de COLMAP, a la Papelera. El zip del escaneo en Descargas se queda (sin duplicado confirmado).

## Procesos abiertos

- **Banco de ARKitScenes:** parado al cerrar la sesión con diez de once casas hechas (resumen en
  `levantamientos/arkitscenes/resumen.json`). La que falta se hace con `python banco/todo.py` (salta las hechas).
- **Código a medias, guardado como `wip`:** `prototipo/banco/`, `detectar.py` (`caras_de_pared`), `alinear.py`
  (`alinear_a_planta`) y `roomplan.py` (opción `nube=`, **no fiable**: no usar todavía).
- Datos del banco en `levantamientos/arkitscenes/` (unos 5,5 GB, fuera del repo): se pueden borrar y volver a bajar.
- Servidor local de Croquis: parado. El móvil de pruebas quedó con adb por wifi (`adb tcpip`); se quita solo al
  reiniciarlo.
