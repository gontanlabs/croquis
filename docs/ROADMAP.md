# Roadmap — Croquis

Última actualización: 2026-11-21 (diseño completo en `docs/DISENO.md`, a revisar por Jose; C-011 y C-012).

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
2. ☐ **Fase 1, sin app propia:** escaneo con OpenPlan3D Capture (gratis, MIT) → Croquis importa su `plan.json` →
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

Banco de pruebas con ARKitScenes en marcha (Jose: «si tienes un metodo vamos con el»); primeros resultados en
`docs/DISENO.md` › Resultados del banco: el LiDAR del iPad mide ~2 cm corto (corregible) y el paso 3 aún no cumple.
Siguiente: corregir ese sesgo, el caso de cristales y espejos, y más casas.

## Pendiente de Jose

1. Revisar `docs/DISENO.md`.

## Procesos abiertos

- Servidor local de Croquis en la red (`prototipo/servidor.py --red`), arrancado en la sesión del 2026-11-21 para subir
  desde el iPad: pararlo al cerrar la sesión.
- Datos del banco en `levantamientos/arkitscenes/` (unos 2 GB, fuera del repo): se pueden borrar y volver a bajar.
