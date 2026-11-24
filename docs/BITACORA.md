# Bitácora — Croquis

Una entrada por sesión, la más reciente arriba.

## 2026-11-23 / 2026-11-24 · C-014 y viabilidad para el Black Friday

- **Decisión:** C-014 («lo más automático y sencillo posible», frase del 21-11 que faltaba).
- **Viabilidad** (`docs/INVESTIGACION-CAPTURA.md`): con el banco (43 paredes de 10 casas), el perímetro de una estancia queda bajo 10 cm en el 24 % de los casos con solo LiDAR, el 62 % con una medida de láser y el 100 % con dos (p95 8 mm). Viable si las cotas las da el láser.
- **Equipo:** el iPad es de Jose; para el estudio, el más barato con LiDAR es un iPhone 13 Pro reacondicionado (~290–390 €). Láser con Bluetooth: Leica D1 o Bosch AdvancedDistance 50C (~110 €), legibles desde una web con el navegador Bluefy; comprar solo si bajan de ~100 €. Quest 3 del estudio: posible pero menos precisa; sin probar.
- **Pendiente de Jose:** la prueba en su casa (salón y comedor, cada pared con láser) y sus tiempos de levantamiento para saber si compensa.

## 2026-11-21 (tarde y noche) · Del escaneo del iPad al banco de pruebas

- **Hecho:** escaneo de la casa de Jose con el iPad (OpenPlan3D Capture) y del salón con SiteScape; la nube LiDAR se
  encaja con la planta. Los parches para corregir la planta salieron poco fiables y Jose pidió parar (C-011): diseño
  en `docs/DISENO.md` y banco de pruebas con ARKitScenes (iPad Pro con LiDAR y láser Faro de referencia).
- **Resultados:** el LiDAR del iPad mide unos 2 cm corto en todas las casas probadas (corregible); el paso 3 aún no
  cumple (entre el 42 y el 78 % de las paredes a 2 cm o menos). Detalle en `docs/DISENO.md` › Resultados del banco.
- **Decisiones:** C-011 (herramienta para cualquier casa), C-012 (fase sin pagar; SiteScape solo para datos de prueba;
  Stray Scanner descartada).
- **Limpieza:** unos 17,6 GB de pruebas descartadas de Croquis, a la Papelera (Jose: «tambien ves limpiando archivos
  pesados inutiles cuando puedas»).
- **Ampliado a diez casas** antes de cerrar: sesgo del sensor confirmado en todas; paso 3 entre el 33 y el 78 % de
  paredes a 2 cm o menos. Decisión C-013 (combinar RoomPlan y la nube LiDAR; método del banco aprobado).
- **Cierre (2026-11-22):** código del banco guardado como `wip`; banco parado con diez de once casas.
- **Siguiente paso:** mirar las paredes que fallan casa por casa; corregir el sesgo y el caso de cristales y espejos;
  volver a medir.

## 2026-11-21 · Nace el proyecto

- **Sesión:** abierta en `C:\Users\jgont\GontanLabs` con `/abrir-lab` («tengo un proyecto nuevo en mente»).
  Conversación: `~/.claude/projects/c--Users-jgont-GontanLabs/97dee3df-7fb6-426d-9325-e9c483634e5f.jsonl`.
- **Hecho:** investigación de partida (ARCore, RoomPlan, magicplan, el Bosch GLM 40-31; en `docs/ROADMAP.md`); carpeta,
  `git init`, `CLAUDE.md`, `README.md` y documentos; fila en `LAB.md`; regla de Ampolleta.
- **Decisiones:** C-001 a C-005.
- **Más tarde, el mismo día:** plumillas y plantilla del estudio leídas (AutoCAD 2027 por consola); repo en GitHub;
  prueba A con una estancia inventada; vivienda completa con un piso inventado (red de toda la casa, láminas EA.01–EA.04
  impresas con AutoCAD y revisadas una a una: muros, puertas, ventanas, cotas, sección en el sentido correcto, nombres
  sin pisar nada). Decisiones C-006 a C-008.
- **Siguiente paso:** las medidas de la casa de Jose (las está tomando) → `levantar.py` → láminas.
