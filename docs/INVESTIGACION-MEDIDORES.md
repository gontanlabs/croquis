# El aparato «que se pone en el medio de la habitación» (investigación, 2026-11-26)

Encargo: precio mínimo, viabilidad y precisión de los aparatos de trípode o «todo en uno», frente al plan actual de
Croquis (iPad/iPhone con LiDAR más un láser de mano con Bluetooth). Criterios del estudio: cotas a ±5 mm y perímetro
de estancia a menos de 10 cm. Todas las fuentes se consultaron el 2026-11-26. Lo que es estimación de Claude se dice.

## Resumen

- **Ningún aparato saca los planos solo.** Los escáneres dan una nube de puntos; los planos se siguen dibujando a mano
  (o con Croquis). La obra son 8 de las 38 h del levantamiento; el dibujo, 30.
- **El mínimo que de verdad «lo hace todo» en obra** (escanea solo, sin apuntar): Leica BLK360 SE, **16.000 € + IVA
  (19.360 €)** en la tienda de Leica España; el G2, 21.000 € + IVA. Usado, un BLK360 G1 sale por unos 6.500 € + IVA.
  Precisión publicada: 4 mm a 10 m. Es probable que llegue a ±5 mm en una vivienda, pero ninguna prueba independiente
  lo mide así.
- **Matterport Pro3** (1.845 € más una suscripción obligatoria de 245 $/mes durante 24 meses): ±20 mm, confirmado por
  terceros (RMS de 11–16 mm). **No llega a ±5 mm.**
- **DISTO X4 + DST 360**: no es automático, hay que apuntar a cada punto. Cuesta unos 1.560 € nuevo (el «kit de 840 €»
  no existe). Su P2P (de punto a punto) da ±5 mm a 5 m: es peor que medir directo con el láser de mano (±1–2 mm).
- **Cuenta al sueldo mínimo del convenio (16,4 €/h de coste para la empresa):** un aparato que solo acelera la obra
  ahorra 131 € por levantamiento como mucho (7.090 € en 3 años). No paga ningún escáner de 16.000–21.000 €. Con la
  referencia del INE (29,9 €/h), tampoco.
- **Recomendación:** seguir con iPad + láser Bluetooth (unos 400 € de equipo, y el ahorro está en el dibujo). No comprar
  ningún aparato «del medio» ahora. Si Croquis llega a dibujar solo a partir de una nube, volver a echar la cuenta con
  un BLK360 usado.

## Lo que se ha comprobado de la búsqueda rápida

| Dato de la búsqueda rápida | Comprobación |
|---|---|
| DISTO X4 a unos 420 € | Más o menos: el X4 solo, 368–436 € con IVA en Alemania (comparadores) |
| «Kit» X4 + DST 360 por unos 840 € | **No.** 420 € es el precio de un adaptador DST 360 con trípode **reacondicionado, sin IVA y agotado** (Leica CPEC). El paquete nuevo X4 + DST 360 cuesta unos 1.563 € con IVA |
| ±2 mm a 2 m, ±5 mm a 5 m, ±10 mm a 10 m | Correcto (tienda de Leica Australia y distribuidor). Leica añade que el error de apuntar se suma |
| Matterport Pro3 a 3.995–5.995 $ más una suscripción | Ha cambiado: hoy se vende a 1.845 € **con** 24 meses obligatorios de un plan a 245 $/mes. ±20 mm a 10 m, confirmado |
| BLK360 G2/SE: 4 mm a 10 m, precio no publicado | La precisión es correcta. El precio **sí está publicado**: 21.000 € y 16.000 € sin IVA (Leica España) |
| Leica 3D Disto, descatalogado | Correcto: Leica dice que ya no está disponible ([Leica](https://lasers.leica-geosystems.com/de/measurement-tools/3d-disto/overview)) |

## Tabla comparativa

Precios con IVA (21 %) salvo que se indique. «Cumple ±5 mm» se refiere a una cota sacada solo del aparato, sin el láser
de mano.

| Opción | Qué hace | Precisión publicada | Medida por terceros | Precio (fecha) | Obligatorio aparte | Exporta | ¿±5 mm? | ¿Perímetro <10 cm? |
|---|---|---|---|---|---|---|---|---|
| **Plan actual:** iPhone/iPad Pro con LiDAR + láser BT | LiDAR andando (forma) + láser en las cotas | LiDAR ~2 cm; láser ±2 mm | Banco ARKitScenes (Croquis): con 2 medidas de láser por estancia, 100 % por debajo de 10 cm | ~290–390 € + ~100 € (doc. del 24-11) | Nada (Bluefy gratis; 99 $/año solo si hay app nativa) | room.json, PLY | Sí, con el láser | Sí (simulado; falta probarlo en casa) |
| Leica DISTO X4 + DST 360 | Trípode; **se apunta a mano** a cada punto | ±2 mm a 2 m, ±5 a 5 m, ±10 a 10 m | No hay | ~1.563 € el paquete nuevo; DST usado 420 € + IVA (agotado) | DISTO Plan: el P2P y el CAD, de pago según Leica (precio sin verificar) | DXF/DWG 2D, PDF | Justo a 5 m; peor que el láser directo | Sí |
| Leica DISTO X6 + DST 360-X | Igual que el anterior, con el X6 | Igual (sin verificar para el X6) | No hay | ~2.056 € con IVA (Letonia); £1.610 + IVA en Reino Unido | Igual | Igual | Igual | Sí |
| Leica DISTO S910 (P2P integrado) | Igual, con base propia | ±1 mm la distancia | No hay | ~2.960–3.330 € con IVA (RS Irlanda/Benelux) | Igual | Igual | Igual | Sí |
| **Leica BLK360 SE** | Escáner láser de trípode, automático | 4 mm a 10 m (1σ) | No hay ninguna del SE | **16.000 € + IVA = 19.360 €** (Leica España) | Cyclone REGISTER 360 PLUS (BLK) para registrar y exportar: precio sin verificar | E57, PTS, PLY, RCP, DXF, OBJ | Probable, sin verificar | Sí |
| **Leica BLK360 G2** | Ídem, <20 s por estación, se registra solo (VIS) | 4 mm a 10 m (1σ) | KIT 2025 (BLK360, sin decir la generación): desviación de punto a plano de 1–7 mm | **21.000 € + IVA = 25.410 €** (Leica España); unidad de demostración 18.990 € + IVA (agotada) | Igual | Igual | Probable, sin verificar | Sí |
| Leica BLK360 G1 usado | Ídem, más lento, sin VIS | 6 mm a 10 m (ficha antigua) | No hay | ~5.800–6.500 € + IVA (Global Geosystems, eBay); reacondicionado por Leica 8.995 € + IVA | Igual | Igual | Dudoso | Sí |
| FARO Focus Core / Blink | Escáner de trípode | Core: hasta 2 mm; Blink: 4 mm a 10 m | No hay | No publicado; el Blink, ~32.500 $ (deducido de una oferta) | FARO Sphere/Scene | E57 | — | Sí |
| Stonex X150 | Escáner de trípode | ~1 cm | No hay | 30.000 $ (distribuidor de Canadá) | — | — | No | Sí |
| **Matterport Pro3** | Cámara 360 con LiDAR, automática | ±20 mm a 10 m | Honti 2025: RMS 11–16 mm, máximo 23 mm. Grešla 2025: la peor de las probadas, más de 35 mm en vertical | 1.845 € + 245 $/mes × 24 meses (Matterport Italia y España) | Plan Professional o superior; E57 y planos, de pago aparte | E57; planos esquemáticos, de pago | **No** | Sí |
| XGRIDS Lixel K1/K2 (SLAM, de mano) | Escáner andando | 1–1,2 cm relativa; 3 cm absoluta (K2) | Pavía 2026 (K1): RMS 6 mm, perfiles de 5–7 mm de grosor | K2 £6.499; K1 £10.918 (Heliguy) | LixelStudio | Nube | No | Sí |
| Leica BLK2GO (SLAM) | Escáner andando | 6–15 mm relativa | Pavía 2026: RMS 7 mm, perfiles de ~15 mm | Demostración 23.995 € + IVA | Cyclone | Nube | No | Sí |
| 3DMakerpro Eagle Max (SLAM) | Escáner andando | 2 cm a 10 m | Pavía 2026: RMS 18 mm, perfiles de 40–50 mm | £4.247 con IVA (3DJake Reino Unido) | — | Nube | No | Dudoso |
| Escaneo como servicio | Lo hace una empresa | Según el equipo | — | 6–10 €/m² (portal de presupuestos) | — | Planos o nube | Según el contrato | Según el contrato |

## Detalle por opción

### 1. Medición de punto a punto desde trípode (Leica DISTO + DST 360)

- **Qué hace:** el DST 360 es un adaptador con sensores de ángulo y un trípode. Convierte el DISTO X3/X4 en una
  «estación»: desde un sitio, se apunta con la mano (y las ruedas de ajuste fino) a cada punto, y la app DISTO Plan
  guarda sus coordenadas. **No escanea: cada esquina, hueco o altura es un disparo.** Leica: «la precisión de apuntar
  se refleja directamente en la precisión»
  ([blog de Leica, 13-01-2025](https://shop.leica-geosystems.com/blog/p2p-adapter-technology);
  [DST 360](https://leica-geosystems.com/es-pe/products/disto-and-leica-lino/leica-disto/leica-dst-360)).
- **Precisión:** del P2P, ±2 mm a 2 m, ±5 mm a 5 m y ±10 mm a 10 m
  ([tienda de Leica Australia](https://shop.leica-geosystems.com/au/buy/package/x4);
  [CR Kennedy](https://survey.crkennedy.com.au/products/LG855107)). Los ángulos, ±0,1°. Según el blog de Leica, la
  desviación es «típicamente de 5 mm a 5 m» y aumenta con la distancia; si el láser llega oblicuo a la pared, más.
  **Conclusión:** para una cota entre dos paredes es peor que el propio láser apoyado en la pared (±1 mm el X4, ±2 mm
  el D1). Lo que aporta son los ángulos y los puntos que no se alcanzan con la mano.
- **Precio:** el X4 solo, 435,61 € con IVA ([billiger.de](https://www.billiger.de/pricelist/1349481457-leica-disto-x4)).
  El paquete X4 P2P (art. 887891: X4, DST 360, trípode TRI 120 y maletín), 1.563 € con IVA
  ([eBay.de, vendedor profesional](https://www.ebay.de/p/19061641559)); 1.470 $ en EE. UU.
  ([Benchmark Supply](https://benchmarksupply.com/products/leica-887891-disto-x4-laser-distance-meter-outdoor-p2p-package)).
  El adaptador DST 360 con trípode, reacondicionado por Leica en Barcelona, 420 € + IVA, **agotado**
  ([Leica CPEC](https://cpec.leica-geosystems.com/producto/dst-360-adapter-tri120/)). X6 P2P: 2.056,49 € con IVA
  ([aio.lv](https://aio.lv/en/product--leica-950878--10978458)); reacondicionado, 1.050 € + IVA, agotado
  ([Leica CPEC](https://cpec.leica-geosystems.com/producto/leica-disto-x6/)). S910 P2P: 2.961 € con IVA en RS Irlanda y
  3.328 € en RS Benelux ([RS](https://ie.rs-online.com/web/p/laser-measures/2230924)). No se ha encontrado precio en
  ninguna tienda española.
- **Software:** DISTO Plan exporta JPG, PDF y DXF/DWG 2D y 2D con alturas
  ([tutorial de Leica](https://shop.leica-geosystems.com/sites/default/files/2024-04/06_DISTO%20Plan%20App%20-%20Smart%20Room_ES.pdf)).
  Las fuentes de Leica se contradicen: la página de preguntas frecuentes dice que el P2P, el CAD y el PDF Pro solo van
  con suscripción, y un blog de abril de 2026 dice que Smart Room es gratis. Precio de la suscripción: sin verificar.
- **Equivalentes:** no se ha encontrado nada de Bosch con P2P desde trípode (búsqueda no exhaustiva). El Leica S910
  lleva el P2P integrado.
- **Tiempo (estimación de Claude):** una persona, unos 150–250 disparos por vivienda, con el trípode cambiado de sitio
  en cada estancia: 4–5 h. Ahorra al menos una persona en la obra; el dibujo sigue a mano (de la app sale el contorno
  2D, no los alzados ni las secciones).
- **Para Croquis:** el DXF de puntos podría servir de esqueleto, pero no da nada que no den ya el iPad y el láser.

### 2. Escáneres láser de trípode

**Leica BLK360 G2 y SE** (tienda de Leica España, leída con curl el 26-11:
[G2](https://shop.leica-geosystems.com/es/reality-capture/blk360/buy),
[SE](https://shop.leica-geosystems.com/es/reality-capture/blk360-se/buy)):
- Precio sin IVA: G2 21.000 € (Hardware Pack: escáner, 3 baterías, cargador, maletín y 6 meses de Hexagon GeoCloud),
  21.500 € el Field Pack y 22.500 € los Starter y Essentials Pack. SE: 16.000 €. Trípode BLK360, 380 €. Ampliar la
  garantía un año (CCP Bronze), 1.127 €.
- Precisión: 4 mm a 10 m de precisión 3D de punto, 1σ y con un albedo del 78 % (las dos fichas). Alcance: 45 m el SE.
- Velocidad: el G2 hace una estación completa en menos de 20 s y registra las estaciones mientras se mueve (VIS); el
  SE tarda menos de 1 min.
- Software: el G2 trae la app BLK Live, gratis. Para registrar y exportar, Cyclone REGISTER 360 PLUS (BLK Edition).
  La ficha del SE dice que Cyclone FIELD 360 «solo va incluido en el paquete Essentials». Exporta E57, PTS, PLY, RCP,
  JPG, PNG, DXF, OBJ, STL y SVG. Precio de la licencia de REGISTER 360: **sin verificar**.
- Medido por terceros: en el banco lineal del KIT (Karlsruhe, ISPRS 2025), el BLK360 dio una desviación de punto a
  plano de 1–7 mm según la distancia, el ángulo y el color del blanco, y peor en superficies negras
  ([Song y Harmening, 2025](https://isprs-archives.copernicus.org/articles/XLVIII-1-W6-2025/219/2025/isprs-archives-XLVIII-1-W6-2025-219-2025.pdf)).
  Concluyen que es fiable «para medidas de precisión centimétrica». **No se ha encontrado ninguna prueba independiente
  del G2 ni del SE que mida distancias entre paredes en viviendas.** Grešla (ISPRS 2025) observa que la precisión real
  se acerca a la del fabricante multiplicada por 2,5
  ([artículo](https://isprs-archives.copernicus.org/articles/XLVIII-5-W3-2025/23/2025/isprs-archives-XLVIII-5-W3-2025-23-2025.pdf)).
- **Para Croquis (estimación de Claude):** ajustando un plano con miles de puntos por pared, el ruido se promedia y la
  cota entre dos paredes vistas desde la misma estación debería quedar a pocos milímetros. Es probable que cumpla ±5 mm;
  el registro entre estaciones añade error. Habría que comprobarlo con el banco de Croquis. Croquis lee cualquier PLY,
  así que la nube del BLK360 le serviría de entrada, y mejor que la del iPad.
- Usado: BLK360 G1 de 2020, 6.500 € sin IVA, con certificado y 6 meses de garantía
  ([Global Geosystems](https://global-geosystems.com/en/product/leica-blk360-g1-3505862/)); unos 5.859 € en eBay.de;
  reacondicionado por Leica, 8.995 € + IVA. G2 de demostración en Leica CPEC, 18.990 € + IVA, agotado
  ([CPEC](https://cpec.leica-geosystems.com/producto/blk360-g2-refurbished-unit/)).

**FARO Focus Core y Blink:** el Core, «hasta 2 mm» y 100 m
([FARO](https://www.faro.com/products/construction-bim/faro-focus/)); el Blink, 4 mm a 10 m
([DiCarlo](https://www.dicarlotech.com/products/3d/faro-blink)). No tienen precio publicado. El del Blink, unos
32.500 $, sale de una oferta a mitad de precio (16.249 $ de descuento)
([DiCarlo](https://content.dicarlotech.com/blink-half-off)). Un Focus Premium se anuncia por 34.999 € + IVA. Quedan
fuera de presupuesto.

**Escáneres chinos o de entrada, de trípode:** Stonex X150, 30.000 $ y ~1 cm
([measur.ca](https://measur.ca/products/stonex-x150-laser-scanner)). **No se ha encontrado ningún escáner de trípode
nuevo por debajo del BLK360 SE.** Lo barato chino (FJD Trion P1, CHCNAV RS10, Geosun, Shining 3D) es de mano (SLAM) o
de piezas, no de trípode. El FJD Trion P1, por ejemplo, es de mano, da 2 cm y cuesta unos 5.200–9.900 € en su tienda
europea ([FJD](https://fjdynamics.com/product/fjd-trion-p1-lidar-scanner)).

### 3. «Todo en uno» para inmobiliaria: Matterport Pro3 y alternativas

- **Qué hace:** cámara 360 con LiDAR en trípode: se pone, se pulsa y se mueve. Procesa en la nube de Matterport.
- **Precio:** «Pro3 por 1.845 € más el coste de la suscripción». El paquete incluye el plan Professional desde 50
  espacios a 245 $/mes, con 24 meses **sin cancelación anticipada** y renovación por 12
  ([Matterport Italia](https://matterport.com/it/store/product/pro3-plus-package),
  [España](https://matterport.com/es/store/product/pro3-plus-package)). En 24 meses salen 5.880 $ de suscripción, más
  la cámara. Impuestos, «al finalizar la compra». La Pro3 no funciona con el plan gratuito.
- **Extras:** E57, 150 $ por espacio; planos esquemáticos, 50 $; MatterPak, 100 $
  ([guía de THE FUTURE 3D, 02-03-2026](https://www.thefuture3d.com/blog/matterport-pricing-guide-2026/); no es tarifa
  oficial).
- **Precisión publicada:** ±20 mm a 10 m ([Matterport](https://matterport.com/store/product/cam-mc300-x)).
- **Medida por terceros:**
  - Honti, Erdélyi y Funtík (Bratislava, 2025), en cuatro interiores contra un escáner topográfico: diferencias de
    −23 a +23 mm, RMS de 11–16 mm, apenas dependen de la separación entre estaciones (1,5–5 m). En una oficina, entre
    2 y 8 estaciones y de 1 a 5 min
    ([Acta Polytechnica Hungarica](https://acta.uni-obuda.hu/Honti_Erdelyi_Funtik_160.pdf)).
  - Grešla (Praga, ISPRS 2025): la que más se desvía de las probadas, con ruido y errores de registro, más de 35 mm en
    vertical, y «no apta para levantamientos de alta precisión»
    ([artículo](https://isprs-archives.copernicus.org/articles/XLVIII-5-W3-2025/23/2025/isprs-archives-XLVIII-5-W3-2025-23-2025.pdf)).
- **Para Croquis:** el E57 se puede leer, pero con un error de 1–2 cm las cotas siguen necesitando el láser, como con
  el iPad, que ya se tiene. Sale más cara que el iPad y no es más precisa que lo que Croquis ya resuelve con el láser.
- **Alternativas:** iGUIDE PLANIX: el fabricante anuncia un 0,5 % en distancias (5 mm por metro); sin prueba
  independiente ni precio en euros ([iGUIDE](https://goiguide.com/compare/iguide-vs-manual-measurement)). Las de
  cámara 360 sin LiDAR (Ricoh Theta, Insta360 con Matterport) dan menos: RMS de 115–149 mm en el estudio de Honti.

### 4. Escáneres de mano (SLAM) de precio medio

Solo como contraste: **ninguno llega a ±5 mm en lo publicado ni en lo medido**, aunque todos cumplen de sobra el
perímetro de 10 cm. Prueba de la Universidad de Pavía (ISPRS 2026, sala controlada, capturas de 60 s, contra un Riegl
VZ-600i) ([artículo](https://isprs-archives.copernicus.org/articles/XLIX-B2-2026/1207/2026/isprs-archives-XLIX-B2-2026-1207-2026.pdf)):

| Equipo | RMS en los puntos de control | Grosor de las paredes en sección | Precio |
|---|---|---|---|
| Riegl VZ-600i (referencia, trípode) | 2 mm | — | — |
| XGRIDS Lixel K1 | 6 mm | 5–7 mm | £10.918 ([Heliguy](https://www.heliguy.com/blogs/posts/xgrids-lixel-k2-lixelstudio-4-launch/)); el K2, £6.499 |
| Leica BLK2GO | 7 mm | ~15 mm | 23.995 € + IVA, de demostración ([Leica CPEC](https://cpec.leica-geosystems.com/producto/blk2go-laser-scanner/)) |
| Share S20 | 8 mm | 6–8 mm | — |
| 3DMakerpro Eagle Max RTK | 18 mm | 40–50 mm | £4.247 con IVA ([3DJake](https://www.3djake.uk/3dmakerpro/eagle)) |

### 5. Alquiler, segunda mano y servicio

- **Alquiler en España:** Instop alquila escáneres Leica (RTC360, P40, P50) con el precio «a consultar» y envío al día
  siguiente ([Instop](https://www.instop.es/scanner-3d/leica-pegasus-backpack.php)). No se ha encontrado ninguna tarifa
  del BLK360 en España. En EE. UU., el BLK360 G2 se alquila por 250–400 $ al día y 800–900 $ a la semana
  ([Kwipped](https://www.kwipped.com/rentals/product/leica-blk360--g2-3d-imaging-laser-scanner/29385)). En Reino Unido,
  £980 al día **con operario** ([Hygglo](https://hygglo.com/uk/i/hire-leica-geosystems-blk360-g2--scanner-and-operator-surveyor-92550830)).
  Laserscanning Europe dejó de alquilar el BLK360 en 2022.
- **Segunda mano:** ver el BLK360 G1 en el apartado 2. Matterport y Global Geosystems ofrecen alquiler y renting de la
  Pro3 en España, sin precio publicado ([Global Geosystems](https://global-geosystems.com/en/matterport/)).
- **Contratarlo como servicio:** según un portal de presupuestos, 6–10 €/m² el escaneo láser con documentación en las
  capitales, y 500–900 € los planos 2D de una vivienda de 60–90 m²
  ([Cronoshare](https://www.cronoshare.com/cuanto-cuesta/levantamiento-planos)). Habitissimo da una media de 3 €/m²
  (0,5–6) para levantar planos, sin decir con qué ([Habitissimo](https://www.habitissimo.es/presupuestos/realizar-levantamiento-de-planos/madrid)).
  Son cifras de portales, no tarifas, y no garantizan ±5 mm ni la plantilla del estudio.

## Coste de la hora del estudio

**El dato real lo tiene que dar el estudio** (sueldos y jornada reales). Mientras tanto, la cuenta usa **el sueldo
mínimo de convenio** que corresponde a arquitectos e interioristas, como pidió el dueño, y deja el resto como
contraste.

**Convenio aplicable.** El XX Convenio colectivo nacional de empresas de ingeniería y oficinas de estudios técnicos
incluye expresamente la CNAE 7111, «Servicios técnicos de arquitectura»
([BOE-A-2023-6346](https://boe.es/boe/dias/2023/03/10/pdfs/BOE-A-2023-6346.pdf)). Encuadra a quien tiene arquitectura
con máster habilitante en el nivel 1 (titulado superior) y a quien tiene un grado universitario en el nivel 2. En el
nivel 2 se coloca aquí también a quien tiene un título superior de Diseño de Interiores (equivalente a grado), y esa
**asimilación es de Claude**. La jornada es de 1.792 h de trabajo efectivo al año (art. 22).
- Tablas en vigor: las de 2024 ([BOE-A-2024-5873](https://BOE.ES/boe/dias/2024/03/23/pdfs/BOE-A-2024-5873.pdf)). El
  convenio está prorrogado. El 02-07-2026, CCOO anunció un principio de acuerdo para el XXI convenio, con atrasos de
  2025 y 2026 y subidas que favorecen al nivel 2
  ([CCOO, comunicado 18](https://www.ccoo-servicios.es/archivos/Comunicado%2018%20Convenio%20Ingenier%C3%ADas.pdf)). No
  se ha encontrado publicado en el BOE: los mínimos reales de 2026 serán algo más altos.
- Nivel 1: 28.664,12 €/año. Nivel 2: 22.224,26 €/año (tabla más plus de convenio).
- En Valencia, el Convenio de Oficinas y Despachos 2024-2026 da para 2026 23.099,91 € al titulado medio y 25.870,72 €
  al titulado superior, con 1.750 h al año
  ([CCOO PV, tablas definitivas](https://www.ccoo-servicios.es/archivos/paisvalenciano/11%C2%BAOOyDD.pdf)). Si el estudio
  se rigiera por él, la hora mínima saldría algo más cara (ver la tabla).
- Ninguna cifra baja del SMI de 2026, que es de 17.094 €/año
  ([Real Decreto 126/2026](https://www.boe.es/eli/es/rd/2026/02/18/126/con)).

**Seguridad social a cargo de la empresa (2026), sobre el sueldo bruto:** contingencias comunes, 23,60 %; desempleo
(contrato indefinido), 5,50 %; FOGASA, 0,20 %; formación profesional, 0,60 %; MEI, 0,75 %
([Asepeyo, bases y tipos 2026](https://www.asepeyo.es/wp-content/uploads/Bases-tipos-cotizacion-2026-ES.pdf)).
Accidentes de trabajo de la CNAE 71: 1,65 %
([tarifa de primas, Fraternidad-Muprespa](https://www.fraternidad.com/gl-ES/descargar-archivo/tarifas-y-cotizaciones-cuadro-i-y-ii-codigos-cnae-y-tipos-aplicables-18ec7fcc0f994f79a2f9baef5420bfaf.pdf)).
**En total, el 32,3 %.** No cuenta las bases máximas, que no se alcanzan con estos sueldos.

| Referencia | Sueldo bruto anual | Horas al año | Coste para la empresa por hora efectiva | Uso |
|---|---|---|---|---|
| **Mínimo: convenio de ingeniería, nivel 2 (graduado o interiorista)** | 22.224,26 € | 1.792 | **16,41 €/h** | **Cifra principal** |
| Convenio de ingeniería, nivel 1 (arquitecto) | 28.664,12 € | 1.792 | 21,16 €/h | Contraste (≈ +30 %) |
| Oficinas y Despachos de Valencia 2026, titulado medio / superior | 23.099,91 € / 25.870,72 € | 1.750 | 17,46 / 19,56 €/h | Contraste |
| Portales de empleo, arquitecto (media de 35.000 €) ([calculadornomina](https://calculadornomina.es/salarios/sueldo-arquitecto-espana-2026/)) | 35.000 € | 1.792 | 25,84 €/h | Contraste (dato débil) |
| INE, ETCL, CNAE 71: coste laboral total por hora efectiva, media del 3T 2025 al 2T 2026 (29,91 · 31,31 · 29,28 · 29,14) ([INE, tabla 6037](https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/6037?nult=4); [nota del 2T 2026](https://www.ine.es/dyngs/Prensa/ETCL2T26.htm)) | — | — | 29,91 €/h | Contraste (media nacional; la Comunitat Valenciana va un 9 % por debajo en servicios) |
| SMI de 2026, como suelo | 17.094 € | 1.792 | 12,62 €/h | Solo comprobación |

No se ha encontrado ningún estudio salarial de colegios profesionales (COACV, CSCAE, CDICV ni el Consejo de
Diseñadores de Interior). Las cifras de interioristas en blogs y agregadores (18.000–40.000 €/año) son poco fiables y no
se usan.

## La cuenta

**Supuestos.**
- 1,5 levantamientos al mes durante 3 años: 54 levantamientos.
- Hoy, 38 h por levantamiento: 8 h-persona de obra y 30 de dibujo. El estudio escribió: «8 horas de trabajo (dos
  personas 4 horas)». Si fueran 16 h-persona (8 h con dos personas), hoy serían 46 h y 755 € por levantamiento al
  mínimo, y todo lo que ahorra la obra pesaría el doble. **Conviene confirmarlo con el estudio.**
- Los equipos se amortizan **sin IVA** (el estudio lo deduce); si no pudiera, súmese un 21 %.
- 1 $ = 0,87 € y 1 £ = 1,16 €, supuestos.
- Las horas con cada aparato son estimaciones de Claude, sin probar.

**Qué automatiza cada opción.**
- Escáneres (BLK360, Matterport, SLAM) y P2P: **solo la toma de datos.** El dibujo (plantas, alzados y secciones en la
  plantilla) sigue siendo de 30 h, salvo que se dibuje sobre la nube o que Croquis lo automatice; esas dos variantes
  van aparte.
- Plan de Croquis: obra de una persona durante 1–1,5 h y dibujo de 3–5 h de revisión, **siempre que el software de
  Croquis funcione**, que hoy está en desarrollo. Sin contar las horas de desarrollo.

**Tope de cualquier aparato que solo acelere la obra:** 8 h × 16,41 € = **131 € por levantamiento**, 7.090 € en 3 años.
Con 21,16 €/h, 9.140 €; con la referencia del INE (29,91 €/h), 12.920 €. Por debajo del precio de un BLK360 en los tres
casos.

**Resultado a la hora mínima (16,41 €/h).** Hoy: 38 h × 16,41 = **623 € por levantamiento** (935 € al mes).

| Opción | Equipo sin IVA (+ cuotas en 3 años) | Equipo por levantamiento | Horas (obra + dibujo) | Horas ahorradas | Coste total por levantamiento | Ahorro por levantamiento | Ahorro al mes |
|---|---|---|---|---|---|---|---|
| Hoy | — | 0 € | 8 + 30 | — | 623 € | — | — |
| **A. iPad/iPhone + láser BT, con Croquis** | ~405 € | 8 € | 1,25 + 4 | 32,75 | **94 €** | **530 €** | **795 €** |
| A'. El mismo equipo, dibujo a mano | ~405 € | 8 € | 1,25 + 30 | 6,75 | 520 € | 103 € | 155 € |
| B. DISTO X4 + DST 360 | ~1.313 € (+ DISTO Plan, sin precio) | 24 € | 4,5 + 30 | 3,5 | 590 € | 33 € | 50 € |
| C1. BLK360 SE | 16.000 € (+ Cyclone, sin precio) | 296 € | 2 + 30 | 6 | 821 € | −198 € | −297 € |
| C2. BLK360 G2 | 21.000 € (+ Cyclone, sin precio) | 389 € | 1,5 + 30 | 6,5 | 906 € | −282 € | −423 € |
| C3. BLK360 G1 usado | 6.500 € (+ Cyclone, sin precio) | 120 € | 2,5 + 30 | 5,5 | 654 € | −30 € | −45 € |
| D. Matterport Pro3 | 1.845 € + 36 meses × 245 $ (≈ 9.520 €) + 200 $ de extras por vivienda | 350 € | 1 + 30 | 7 | 859 € | −235 € | −353 € |
| E. Lixel K2 (SLAM; no cumple ±5 mm) | ~6.280 € | 116 € | 1 + 30 | 7 | 625 € | −1 € | −2 € |
| F. Servicio externo (vivienda de 90 m², supuesta) | 720 € por vivienda | 720 € | 0 + 4 (revisar y pasar a la plantilla) | 34 | 786 € | −162 € | −243 € |
| G. Alquilar un BLK360 G2 dos días (sin tarifa española) | ~520 € por vivienda | 520 € | 1,5 + 30 | 6,5 | 1.037 € | −413 € | −620 € |

**Con las otras dos referencias (ahorro por levantamiento):**

| Opción | 16,41 €/h (mínimo) | 21,16 €/h (arquitecto) | 29,91 €/h (INE CNAE 71) |
|---|---|---|---|
| A. iPad + láser, con Croquis | 530 € | 686 € | 972 € |
| A'. Ídem, dibujo a mano | 103 € | 135 € | 194 € |
| B. DISTO X4 + DST 360 | 33 € | 50 € | 80 € |
| C1. BLK360 SE | −198 € | −169 € | −117 € |
| C2. BLK360 G2 | −282 € | −251 € | −194 € |
| C3. BLK360 G1 usado | −30 € | −4 € | +44 € |
| D. Matterport Pro3 | −235 € | −202 € | −141 € |
| F. Servicio externo | −162 € | 0 € | +297 € |

**Si dibujar sobre la nube ahorrara un tercio del dibujo (30 → 20 h; estimación sin fuente), a 16,41 €/h:** BLK360 SE,
−34 €; G2, −118 €; G1 usado, +134 €; Matterport, −71 €.
**Si Croquis dibujara solo a partir de la nube (dibujo de 4 h), a 16,41 €/h:** BLK360 SE, +229 €; G2, +144 €; G1 usado,
+396 €; Matterport, +191 € (pero sin ±5 mm). Ni así ganan al plan A (+530 €), que no necesita un aparato de miles de
euros.

Script de la cuenta: `cuenta.py`, en el directorio temporal de la sesión (no en el repo). Los números se rehacen solos
cambiando la hora o las horas.

## Recomendación

1. **¿Cuál cumple ±5 mm?** Con seguridad, solo el láser de mano apoyado en la pared (±1–2 mm). El P2P del DST 360 da
   ±5 mm a 5 m: justo en estancias normales y peor en las grandes. El BLK360 probablemente sí (4 mm a 10 m, 1σ, y miles
   de puntos por pared), pero no hay ninguna prueba independiente de cotas entre paredes; habría que medirlo. Matterport
   y los escáneres de mano, no.
2. **¿El mínimo que de verdad «lo hace todo»?** En obra, el BLK360 SE nuevo (19.360 € con IVA) o un G1 usado (unos
   7.900 € con IVA, con garantía de 6 meses). Ninguno saca los planos: da la nube, y el dibujo sigue siendo de 30 h.
3. **¿Compensa frente al plan iPad + láser Bluetooth?** No. El 79 % de las horas está en el dibujo. Un aparato que solo
   mide ahorra como mucho 131 € por levantamiento al sueldo mínimo, y los escáneres que cumplen cuestan 16.000–21.000 €
   sin IVA: no se pagan en 3 años ni con la referencia del INE. El plan A cuesta unos 400 € y ataca el dibujo.
4. **Qué haría Claude:** no comprar ahora ningún aparato «del medio». Terminar la prueba del iPad + láser en la casa de
   Jose. Si un día se quiere comprobar el BLK360, pedir presupuesto de alquiler de un día (Instop o un distribuidor de
   Leica) para una sola vivienda y pasar su nube por el banco de Croquis, antes de gastar 7.000–25.000 €.

## Lo que no se ha podido verificar

- **Precio en tiendas españolas** del DISTO X4 P2P, el X6 P2P y el S910: solo hay precios de Alemania, Letonia,
  Irlanda, Benelux y EE. UU. La tienda de Leica España bloquea las páginas de DISTO (403).
- **Precio de la suscripción de DISTO Plan** (P2P y CAD), y si hace falta: las fuentes de Leica se contradicen.
- **Precio de Cyclone REGISTER 360 PLUS (BLK Edition)** y qué software lleva exactamente cada paquete del BLK360.
- **Precisión del BLK360 G2/SE en cotas entre paredes de una vivienda:** no hay estudio independiente (solo el del KIT,
  con el BLK360 en banco, y sin decir la generación).
- **Precisión del DST 360 medida por terceros:** no hay.
- **Matterport:** si los 1.845 € llevan IVA, el precio en euros del plan (solo se publica en dólares), si el E57 va
  incluido en el plan Professional y el precio oficial de los extras (los 150 $ y 50 $ son de un tercero). El precio de
  la cámara sola en euros tampoco se ha encontrado.
- **Precio del FARO Focus Core y del Blink**, que no se publican.
- **Alquiler del BLK360 en España:** ninguna tarifa publicada; los 520 € de la cuenta salen de tarifas de EE. UU.
- **Servicio externo:** los 6–10 €/m² son de un portal de presupuestos; la superficie de 90 m² es un supuesto.
- **Horas con cada aparato** (obra y dibujo): estimaciones de Claude, sin probar en ninguna vivienda.
- **Hora del estudio:** sueldos reales, convenio que aplica de verdad (ingeniería u oficinas y despachos), dónde se
  encuadra al interiorista y si la obra son 8 o 16 h-persona. Las tablas de 2025 y 2026 del convenio de ingeniería no
  están publicadas en el BOE.
- **Equivalente de Bosch al DST 360:** no se ha encontrado; la búsqueda no fue exhaustiva.
- **Tablas numéricas de Grešla (ISPRS 2025):** van como imagen en el PDF; solo se ha usado lo que dice el texto.
