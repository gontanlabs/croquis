# Roadmap — Croquis

Última actualización: 2026-11-21 (creación del proyecto).

## Estado

2026-11-21: proyecto creado, sin código. Idea, salidas, precisión y reglas del traspaso a VLANC, decididas
(`docs/DECISIONES.md`).

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

1. ☐ **Probar magicplan** una tarde en una habitación y apuntar qué le falta para un estado actual de ±5 mm
   (propuesta de Claude).
2. ☐ **Prueba A, el ajuste sin cámara:** croquis más medidas de una habitación real → plano cuadrado, con el margen de
   cada cota. Es la parte que vale.
3. ☐ **Prueba B, la cámara:** qué saca ARCore (Raw Depth) en el móvil de pruebas (Huawei P30, sin sensor de
   profundidad); primero, comprobar si lo admite.
4. ☐ **App mínima:** croquis a mano en la pantalla, medidas tecleadas, ajuste y planta en DXF y PDF.
5. ☐ Alzados y secciones (alturas, antepechos, dinteles, falsos techos, vigas).
6. ☐ Cámara como primera aproximación de la forma.
7. ☐ Láser por Bluetooth (Bosch, Leica…), como un modo de medir más.
8. ☐ Modelo 3D exportable.
9. ☐ Traspaso a VLANC.

## Por decidir

- Tecnología de la app (lenguaje y librerías de Android, del ajuste y de la salida DXF/PDF): Claude la propone al
  empezar la prueba A.
- Identificador Android neutro (ni `com.gontanlabs…` ni `com.vlanc…`, o ya el de VLANC).
- **Plantilla DWG de VLANC** (capas, grosores, estilo de cotas): si existe, el DXF sale ya con ella.
- Al traspasar: si se reescribe la autoría de los commits; si sale en el portfolio (con permiso de VLANC).

## Pendiente de Jose

1. Crear el repo vacío y privado `croquis` en la organización `gontanlabs`:
   https://github.com/organizations/gontanlabs/repositories/new (Claude lo sube después por SSH).
2. Decir si VLANC tiene plantilla DWG y pasarla.
3. Decir si se prueba magicplan antes de programar.

## Procesos abiertos

Ninguno.
