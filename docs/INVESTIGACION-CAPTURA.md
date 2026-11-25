# Cómo capturar una vivienda con el móvil para sacar el croquis (investigación, 2026-11-21)

Por qué: los primeros intentos (esquina a esquina, giro con profundidad, fotos desde un punto fijo) fallaron. Jose:
«estas haciendo chapuzas y no consultando fuentes ni investigando lo suficiente». Esto es lo que dicen las fuentes.

## 1. Girar desde un punto fijo no sirve para reconstruir en 3D

- Con todas las fotos tomadas desde el mismo centro óptico, la triangulación de la fotogrametría «queda mal definida y
  suele fallar» ([MASt3R-SfM](https://arxiv.org/pdf/2409.19152), apéndice).
- Las escenas aptas para panorámica están mal condicionadas para la fotogrametría: el giro domina, el solape entre
  fotos es poco y la distancia entre posiciones es pequeña frente a la profundidad; en el móvil empeora por el campo de
  visión estrecho, las fotos movidas y el obturador «rolling shutter»
  ([Ventura, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/papers/Ventura_Uncalibrated_Structure_from_Motion_on_a_Sphere_ICCV_2025_paper.pdf)).
- Es exactamente lo que pasó con el comedor (2026-11-21): 108 fotos desde dos puntos, 351 puntos 3D.

## 2. Cómo se captura bien un interior

- COLMAP: mucho solape (cada cosa en al menos 3 fotos), **desde puntos de vista distintos**, buena textura (las paredes
  blancas lisas no sirven), luz pareja, evitar fotos contra ventanas y brillos
  ([tutorial de COLMAP](https://colmap.github.io/_sources/tutorial.rst.txt)).
- Polycam (interiores por fotogrametría): primera pasada recorriendo el perímetro, segunda en anillo por el centro de la
  habitación mirando hacia fuera, esquinas de frente y a 45°/90°, movimiento lento, solape del 70–75 %
  ([Polycam, interiores](https://learn.poly.cam/hc/en-us/articles/48339214285844)).
- Quietos: no mover muebles ni cortinas durante la captura ([Polycam](https://poly.cam/blog/high-resolution-interior-photogrammetry-full-walkthrough-polycam-tutorial)).

## 3. Qué hacen las apps comerciales en Android (sin LiDAR)

- **CubiCasa:** un **vídeo continuo** recorriendo toda la vivienda (todas las habitaciones y armarios), el móvil en
  vertical algo inclinado hacia abajo, en una sola pasada; el plano se hace después en sus servidores
  ([CRMLS, consejos](https://kb.crmls.org/knowledgebase/cubicasa-tips-for-scanning/); precisión anunciada 95–97 %:
  [ARMLS](https://armls.com/how-accurate-are-cubicasa-floorplan-scans)).
- **Matterport:** con el móvil solo usa una IA propia (Cortex); en Android, lo publicado habla sobre todo de cámaras 360
  conectadas ([Matterport para Android](https://matterport.com/blog/matterport-capture-app-android-officially-here)).
- **Polycam:** los planos y el DXF exigen LiDAR (iPhone/iPad Pro) ([Polycam, planos](https://poly.cam/floor-plans)).

## 4. Del modelo 3D a la planta

- RoomFormer (CVPR 2023): de una nube de puntos (vista cenital de densidad) a los polígonos de las estancias; código en
  github.com/ywyue/RoomFormer ([artículo](https://arxiv.org/pdf/2211.15658)). PolyRoom (ECCV 2024), código en
  github.com/3dv-casia/PolyRoom. Hereda el ruido y los huecos de la nube. **Licencias por comprobar** antes de usarlos.
- Alternativa sin aprendizaje: ajustar las paredes en la nube por encima de los muebles (`prototipo/barrido.py`).

## Conclusión (propuesta de Claude, pendiente de Jose)

- **Captura:** vídeo andando, como CubiCasa: perímetro de cada habitación y una vuelta por el centro, despacio. Con la
  gran angular (0,6×) si Chrome la da: abarca el triple y el solape sobra. Nada de girar en un punto.
- **Proceso, al final y en el PC:** fotogramas nítidos del vídeo → COLMAP (emparejamiento secuencial) → nube densa →
  planta (paredes por encima de los muebles; RoomFormer si su licencia lo permite) → medidas guiadas con láser → planos.
- **Escala:** una medida de láser (sin realidad aumentada no hay metros).
- La vista previa con imágenes dobles era de unir fotos tomadas desde sitios distintos sin alinearlas; con vídeo no hace
  falta.

## 5. Código abierto que ya existe (búsqueda del 2026-11-21, después de que Jose preguntara)

- **Apps de Android que hacen planos con la cámara** (magicplan, Plotlay Scan, vPlan AR): cerradas, y por esquinas.
  **openPlan3D** (MIT, [github.com/laanlabs/openPlan3D](https://github.com/laanlabs/openPlan3D)): solo iPhone con
  LiDAR; su editor de planos podría reutilizarse. **RTAB-Map** ([introlab.github.io/rtabmap](https://introlab.github.io/rtabmap)):
  motor abierto de escaneo 3D con versión Android y ARCore; sin probar en un móvil sin sensor de profundidad.
- **VGGT** (Meta, CVPR 2025, [artículo](https://arxiv.org/abs/2503.11651)): de una, pocas o cientos de fotos saca las
  cámaras, los mapas de puntos y la profundidad, en segundos. **VGGT-1B-Commercial** admite uso comercial salvo militar
  ([Hugging Face](https://huggingface.co/facebook/VGGT-1B-Commercial)); los pesos están restringidos (cuenta de Hugging
  Face, petición y aprobación manual de Meta). El VGGT-1B original es no comercial.
- **SpatialLM** (NeurIPS 2025, [github.com/manycore-research/SpatialLM](https://github.com/manycore-research/SpatialLM)):
  de una nube de puntos saca paredes, puertas y ventanas; pesos CC-BY-NC (no comercial): no vale para VLANC tal cual.
- **MASt3R-SLAM** (CVPR 2025): reconstrucción en directo desde vídeo; puntos de control no comerciales.

**Camino comercial posible:** vídeo o fotos → VGGT-1B-Commercial (geometría) → paredes por encima de los muebles
(`prototipo/barrido.py`) o RoomFormer si su licencia lo permite → medidas guiadas → planos.

## 6. Pruebas en el comedor de Jose (2026-11-21)

| Captura | Método | Resultado |
|---|---|---|
| 108 fotos desde 2 puntos fijos (app, realidad aumentada) | COLMAP con posiciones del móvil | 351 puntos; fotos movidas y sin desplazamiento: no sirve |
| Las mismas 30 | VGGT | nube a trozos: no sirve |
| Vídeo normal, 0,6×, andando, 61 s | COLMAP sin posiciones | 10 trozos sin unir |
| Grabación andando en la app (realidad aumentada), 26 fotogramas | COLMAP con posiciones | 215 puntos: los fotogramas de la realidad aumentada salen movidos y con poco detalle |
| **Vídeo normal, 24 fotogramas nítidos** | **VGGT**, escala con la altura medida (2,47 m) | **forma del comedor correcta; 3,92 × 3,68 m frente a 4,12 × 3,48 m reales (~5 %)** |

Conclusión: la captura que funciona es un vídeo normal y nítido andando; la geometría, VGGT; la escala, una medida de
láser. Un ~5 % es nivel de croquis (CubiCasa anuncia 95–97 %); las cotas exactas las da después el láser.
Pendiente: usar todo el vídeo por tandas (8 GB de memoria gráfica: ~25 fotogramas cada vez), detectar las paredes
sin confundirlas con muebles o con lo que se ve por una puerta, y una app de captura guiada que grabe vídeo normal.

## Viabilidad para el perímetro y láser con Bluetooth (2026-11-24)

Encargo de Jose: saber antes del viernes 27 (Black Friday) si Croquis es viable y qué hay que comprar; «si el perimetro
de una vivienda se nos va 10 cm la hemos cagado».

**Perímetro de una estancia, con el banco de ARKitScenes** (43 paredes de 10 casas contra el láser Faro; 20.000
estancias rectangulares simuladas con los errores reales de cada casa; script en la bitácora de la sesión):

| Método | Error típico | 95 % menos de | Estancias bajo 10 cm |
|---|---|---|---|
| Solo LiDAR del iPad | 164 mm | 693 mm | 24 % |
| LiDAR + 1 medida de láser por estancia | 63 mm | 409 mm | 62 % |
| LiDAR + 2 medidas de láser (largo y ancho) | 3 mm | 8 mm | 100 % |

Conclusión: viable si las cotas las da el láser; el iPad da la forma y dice qué medidas hacen falta. Falta la prueba en
la casa de Jose (salón y comedor, cada pared con su láser).

**Láser con Bluetooth** (investigación del 24-11, con fuentes):
- Ninguno por debajo de 150 € tiene modo teclado (escribir la medida en cualquier campo). El más barato que lo tiene es
  el Leica DISTO X3 (más de 300 €).
- Safari en iPadOS no tiene Web Bluetooth; el navegador gratuito **Bluefy** sí (exige HTTPS). Con él, una web app puede
  leer un láser BLE de protocolo conocido sin app nativa ni cuota de Apple (sin probar todavía en el iPad).
- Protocolo conocido por ingeniería inversa: **Leica DISTO D1** (~114 €, ±2 mm) y **Bosch AdvancedDistance 50C**
  (~109 €, ±2 mm, sin disparo remoto); Bosch GLM 50-27 C (±1,5 mm) cuesta 160–271 €. Stabila LD 250 BT, sin protocolo
  publicado.
- Una app nativa en el iPad (Expo + EAS, sin Mac) exige la cuenta de desarrollador de Apple (99 USD al año).
- Recomendación: comprar solo si el D1 o el AdvancedDistance 50C bajan de unos 100 € el viernes, en una tienda con
  devolución, y probarlo con Bluefy en los 14 días; si no, el GLM 40-31 sigue valiendo, tecleando las medidas.

## Lo que cuesta hoy un levantamiento en VLANC (datos del estudio, 2026-11-25)

Respuesta del estudio a Jose: «1) 8 horas de trabajo (dos personas 4 horas) de media; 2) 30h de media; 3) 1,5
levantamientos de media al mes». Es decir, unas **38 horas por levantamiento** (8 en la obra y 30 dibujando) y unas
**57 horas al mes**.

Cuenta provisional (Claude; los tiempos con Croquis son estimaciones por comprobar en la prueba): si la obra baja a una
persona 1–1,5 h (escaneo y 2 medidas de láser por estancia) y el dibujo a 3–5 h de revisión, el ahorro sería de unas 30
horas por levantamiento, unas 45 horas al mes. El equipo (iPhone con LiDAR reacondicionado, unos 290–390 €, más un láser
con Bluetooth de unos 100 €) se pagaría con el primer levantamiento. Sin contar las horas de desarrollo, y solo si la
prueba en casa confirma la precisión.
