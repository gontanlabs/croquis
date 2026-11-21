# Roadmap — Croquis

Última actualización: 2026-11-21 (vivienda completa con un piso inventado; a la espera de la casa de Jose).

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

## Plan

1. ✖ Probar magicplan: descartado por Jose (C-008), app propia desde cero.
2. ⏳ **Prueba A, el ajuste sin cámara:** ✅ con una estancia inventada (2026-11-21); ☐ con una habitación real medida
   por Jose con el GLM 40-31: sustituida por la casa entera (Jose: «estoy en casa y quiero sacar los planos completos,
   eso nos servira de prueba»).
2b. ⏳ **Vivienda completa:** ✅ con un piso inventado; ☐ con la casa de Jose (`levantamientos/`, fuera de git;
   `python prototipo/levantar.py <datos.json> --laminas`).
3. ☐ **Prueba B, la cámara:** qué saca ARCore (Raw Depth) en el móvil de pruebas (Huawei P30, sin sensor de
   profundidad); primero, comprobar si lo admite.
4. ☐ **App mínima:** croquis a mano en la pantalla, medidas tecleadas, ajuste y planta en DXF y PDF.
5. ☐ Alzados y secciones (alturas, antepechos, dinteles, falsos techos, vigas).
6. ☐ Cámara como primera aproximación de la forma.
7. ☐ Láser por Bluetooth (Bosch, Leica…), como un modo de medir más.
8. ☐ Modelo 3D exportable.
9. ☐ Traspaso a VLANC.

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

## Pendiente de Jose

1. Medir su casa con el protocolo de campo (en la conversación del 2026-11-21 y en `prototipo/README.md`).

## Procesos abiertos

Ninguno.
