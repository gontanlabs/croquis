# Decisiones — Croquis

Solo lo que Jose decidió o aprobó, con su frase literal y la hora. No se vuelven a discutir. Lo propuesto por Claude sin
aprobar va a «Por decidir» del roadmap.

**C-001 · 2026-11-21 · Qué es: app Android de medición para el estado actual de viviendas, con planos verídicos.**
- Jose (09:17): «una herramienta de medicion para hacer los estados actuales de las viviendas y obtener planos veridicos
  exactos de cada una, he pensado en android, algo como nubes de puntos con la camara de alguna manera como primera
  aproximacion, y despues puede que medidas a mano e introduccion de estas mediante la interfaz de la aplicacion con tal
  de ir puliendolas hasta que sean practicamente perfectas para toda la casa».
- Salidas (09:34): «tienen que salir planos (plantas, alzados, secciones si son necesarias...) en dxf y pdf esta bien, el
  modelo 3d podria estar bien tambien pero es mas opcional ya que lo primero que se suele trabajar en estos casos es la
  distribucion nueva en planta antes de levantar el 3d, aunque no lo vamos a descartar».

**C-002 · 2026-11-21 · Herramienta para VLANC, desarrollada en Gontan Labs (`proyectos/croquis`); horas para VLANC.**
- Jose (09:34): «es para uso de un estudio claro, pero lo desarrollaremos aqui y luego podemos pasarlo a vlanc
  facilmente, contamos las horas porque es claramente una herramienta para vlanc, aunque este dentro del entorno
  gontanlabs (al menos en inicio)».
- Dónde (respuesta, 09:41): «proyectos/ en GontanLabs (Recomendado)». Condiciones del traspaso (Claude, en `CLAUDE.md`):
  nombre e identificador neutros, sin Google Play, firma propia, sin datos de clientes en el repo.
- Ecosistema: L-024.

**C-003 · 2026-11-21 · Nombre: Croquis.**
- Claude propuso escuadra, croquis, levanta y plomada; Jose (respuesta, 09:43): «croquis».

**C-004 · 2026-11-21 · Precisión del plano final: ±5 mm.**
- Jose (respuesta, 09:41): «±5 mm».

**C-005 · 2026-11-21 · Cada usuario elige cómo mide.**
- Jose (09:34, mientras Claude trabajaba): «en cuanto al laser tengo un bosch glm 40-31, no se si se puede conectar de
  alguna manera, no creo, pero mas bien deberiamos dejar que cada usuario elija su modo de medir?». Claude estuvo de
  acuerdo: cada medida guarda su origen y su margen, y el ajuste da más peso a las fiables.

**C-006 · 2026-11-21 · Alzados: interiores siempre; exteriores, solo en vivienda unifamiliar.**
- Jose: «los alzados suelen ser interiores pero tambien serian exteriores si es una vivienda unifamilair, en el caso de
  pisos o apartamentos no es tan importante porque no se va a tocar la fachada».

**C-007 · 2026-11-21 · Secciones: las suficientes para que se entienda todo y no quede ninguna medida por obtener.**
- Jose: «en cuanto al numero las suficientes para que se entienda todo y no se queden medidas por obtener, claro».

**C-008 · 2026-11-21 · App propia desde cero; magicplan no se prueba.**
- Jose: «ya es una app, no, porque ademas estara limitada con planes de pago etc, si lo podemos hacer nosotros
  igualmente con una app propia, pues mejor, no se si se basa en un sistema de codigo abierto o lo han desarrollado
  ellos, pero prefiero que empecemos de cero». (magicplan es de código cerrado, de Sensopia.) Desde cero no quita usar
  librerías abiertas para lo que no es propio (leer y escribir DXF, álgebra).

**C-009 · 2026-11-21 · Por ahora, Croquis es para uso de Jose.**
- Jose, al preguntarle si la licencia de VGGT la aceptaría él o VLANC: «es para mi por el momento». Las pruebas se hacen
  con modelos de uso no comercial cuando no haya otra cosa (VGGT-1B); antes de pasar a VLANC, cambiar a los comerciales
  (VGGT-1B-Commercial) o a otros con licencia que lo permita. Matiza C-002 mientras dure.

**C-010 · 2026-11-21 · Croquis es un producto para vender: app para iPhone Pro / iPad Pro con LiDAR y panel web; Android, fuera.**
- Jose: «lo que quiero es al final no solo un modo de hacer las mediciones para el estudio sino un sistema o app lo mas
  sencillo e integrado posible que vender, por eso te pregunto el mejor formato posible»; ante la propuesta (app iOS con
  escaneo RoomPlan y medidas guiadas en la misma app, panel web donde el estudio sube su plantilla y descarga DXF/PDF,
  suscripción por estudio, Android fuera por no tener LiDAR ni RoomPlan, VLANC como primer cliente, construcción sin Mac
  con Expo y expo-roomplan): «me encaja». Antes: «para que necesitamos el android entonces? noe s mejor un pc?».
- Cambia C-001 («he pensado en android»): el campo es el iPad o iPhone Pro; la oficina, el PC o la web.
- Sus diferencias (Dunford, pasos 4–5; Christensen, el «trabajo» como progreso en una situación): planos en la plantilla
  de cada estudio, precisión comprobada con láser donde importa, serie completa del estado actual.
- Pendiente para venderlo: generar los PDF sin AutoCAD, aplicando las plumillas del estudio.

**C-011 · 2026-11-21 · Una herramienta para cualquier tipo de casa, no para un caso.**
- Jose (2026-11-21, 21:06, mientras Claude corregía el salón de su casa): «no se si vas a sacar el comedor o corregir la planta pero desde
  luego sera para un caso aislado, te estas centrando en algo concreto cuando lo que queremos es una herramienta tan
  versatil como cualquier tipo de casa». Y (21:07): «estas haciendo chapuzas, monton sobre monton».
- Consecuencia: se para el código y se escribe el diseño (`docs/DISENO.md`), con un catálogo de casos y una
  comprobación con referencia láser en muchas habitaciones antes de dar nada por bueno.

**C-012 · 2026-11-21 · Esta fase, sin pagar: servidor local y apps que ya existen; SiteScape solo para datos de prueba.**
- Jose (2026-11-21, 21:11): «para probar con navegador hace falta pagar desarrollo?? no podemos hacerlo con el metodo que estamos siguiendo
  del localhost???????????». Después (21:12): «por que no podemos usar una app de codigo abierto en vez de una de codigo cerrado
  para ponernos mas facil luego el camino?». Claude propuso Stray Scanner (abierta, MIT); Jose (21:21): «stray scanner es una
  mierda». Ante seguir con SiteScape solo como fuente de datos de prueba (exporta PLY, nada depende de ella), 21:22:
  «vale».
- La app propia (Expo, cuenta de desarrollador de Apple, 99 €/año) se decide cuando el sistema funcione con este
  método.

**C-013 · 2026-11-21 · La clave es combinar RoomPlan (la forma) y la nube LiDAR (el detalle); método del banco de pruebas, adelante.**
- Jose (21:05, mientras Claude trabajaba): «lo que hacen estos dos programas que hemos probado combinados debe ser la
  clave para lo que queremos». Los dos programas: OpenPlan3D Capture (RoomPlan) y SiteScape (nube LiDAR).
- Ante el diseño (`docs/DISENO.md`: catálogo de casos y comprobación contra láser en muchas habitaciones con
  ARKitScenes antes de dar nada por bueno), 21:27: «si tienes un metodo vamos con el».
- Sin decidir todavía: los números de los criterios de aceptación del diseño (propuesta de Claude).
