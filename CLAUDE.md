# Croquis — ficha del proyecto

App Android para hacer el **estado actual de una vivienda** y sacar planos verídicos y exactos: plantas, alzados y
secciones en **DXF y PDF** (el modelo 3D, opcional, más adelante). La cámara da una primera aproximación de la forma y
las medidas la van puliendo hasta **±5 mm** en toda la casa.

**Proyecto para VLANC desarrollado en Gontan Labs** (L-024 del ecosistema, C-002): es una herramienta del estudio, se
desarrolla aquí «al menos en inicio» y se traspasa a VLANC cuando toque. Sus horas cuentan para VLANC (Ampolleta:
«Herramientas internas · Desarrollo»). Reglas comunes en `../../CLAUDE.md`.

**Idioma: SIEMPRE castellano**: respuestas, documentación, commits, textos de la app.

## Para que el traspaso a VLANC sea limpio

- **Nombre neutro:** ni «gontanlabs» ni «vlanc» en el código, en el identificador de la app ni en los textos.
- **Sin Google Play:** se instala el APK en los móviles del estudio. Clave de firma propia, fuera del repo
  (`~/.croquis`), nunca la de DeCA10 ni la de Kipp.
- **Sin datos de clientes de VLANC en el repo:** las pruebas, con viviendas propias o medidas inventadas.
- Git con la identidad de Gontan Labs, como todo el laboratorio. Al traspasar se decide si se reescribe la autoría.
- En el portfolio de gontanlabs.com, solo con el visto bueno de VLANC.

## Cómo funciona (idea de partida, ver `docs/ROADMAP.md`)

- **Modelo interno en 3D desde el primer día:** paredes con su altura y grosor, huecos con antepecho y dintel, falsos
  techos y vigas. Plantas, alzados y secciones son vistas de ese modelo; el 3D sale casi solo.
- **Cada medida guarda su origen y su margen** (cámara, cinta, láser tecleado, láser por Bluetooth). Cada usuario mide
  como pueda (C-005).
- **Ajuste de toda la casa**, como el de los topógrafos: las medidas fiables pesan más; paredes que no van a 90°,
  grosores de muro y habitaciones que encajan entre sí por las puertas.
- **La app dice qué medir después** y el plano marca qué cotas cumplen ya los ±5 mm y cuáles son estimadas.

## Documentos

`docs/ROADMAP.md` (estado, plan, por decidir, pendiente de Jose), `docs/DECISIONES.md` (con la frase de Jose),
`docs/BITACORA.md` (una entrada por sesión).
