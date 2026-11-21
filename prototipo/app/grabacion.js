'use strict';
// Grabación andando (docs/INVESTIGACION-CAPTURA.md): se recorre cada habitación despacio, perímetro y vuelta por el
// centro. Se guarda un fotograma cada 25 cm o 12° de giro, solo si el móvil va despacio (que salga nítido), con su
// posición y orientación (ARCore). Un mapa visto desde arriba se pinta con lo que la cámara ya ha visto (profundidad
// aproximada de ARCore: solo para orientarse, no para medir) y con el recorrido.

const GR = {
  PASO: 0.25, GIRO: Math.cos((12 * Math.PI) / 180),        // un fotograma cada 25 cm o 12°
  MAX_GIRO: (0.5 * Math.PI) / 180,                         // y solo si gira menos de 0,5° por cuadro (~15°/s)…
  MAX_PASO: 0.012,                                         // …y avanza menos de 1,2 cm por cuadro (~0,35 m/s)
  CELDA: 0.10,                                             // mapa en celdas de 10 cm
};
const gr = {
  sesion: null, gl: null, binding: null, ref: null, fb: null, fuente: null, grabando: false, ocupado: false,
  ultima: null, previa: null, suelo: null, visto: new Map(), recorrido: [], total: 0, habitacion: '', id: '', nombre: '',
  perdido: false, n: 0,
};
const grTrabajador = new Worker('trabajador.js');
grTrabajador.onmessage = async (e) => {
  const m = e.data;
  if (m.tipo !== 'foto') return;
  try { await almacen.poner({ fichero: `${m.meta.levantamiento}-${m.meta.fichero}`, jpeg: m.jpeg, meta: m.meta }); } catch (err) { registrar('guardar', err); }
  gr.ocupado = false;
  subirPendientes();
};

function grChips() {
  const c = $('#gr-chips'); c.innerHTML = '';
  for (const n of NOMBRES) {
    const b = document.createElement('button'); b.textContent = n;
    b.classList.toggle('accion', gr.habitacion === n.toUpperCase());
    b.onclick = () => { gr.habitacion = n.toUpperCase(); grChips(); };
    c.appendChild(b);
  }
}

$('#b-grabar').onclick = async () => {
  gr.nombre = $('#nombre').value.trim() || 'Mi casa';
  gr.id = 'v' + Date.now().toString(36);
  Object.assign(gr, { visto: new Map(), recorrido: [], total: 0, ultima: null, previa: null, suelo: null, grabando: false });
  try {
    let sesion = null;
    try {
      sesion = await navigator.xr.requestSession('immersive-ar', {
        requiredFeatures: ['camera-access'], optionalFeatures: ['depth-sensing', 'hit-test', 'dom-overlay'],
        domOverlay: { root: $('#grabar') },
        depthSensing: { usagePreference: ['cpu-optimized'], dataFormatPreference: ['luminance-alpha', 'float32'] },
      });
    } catch (e) {
      sesion = await navigator.xr.requestSession('immersive-ar', {
        requiredFeatures: ['camera-access'], optionalFeatures: ['hit-test', 'dom-overlay'], domOverlay: { root: $('#grabar') },
      });
    }
    gr.sesion = sesion;
    mostrar('grabar');
    $('#grabar').addEventListener('beforexrselect', (e) => e.preventDefault());
    gr.gl = document.createElement('canvas').getContext('webgl', { xrCompatible: true });
    sesion.updateRenderState({ baseLayer: new XRWebGLLayer(sesion, gr.gl) });
    gr.binding = new XRWebGLBinding(sesion, gr.gl);
    gr.ref = await sesion.requestReferenceSpace('local');
    gr.fb = gr.gl.createFramebuffer();
    try { gr.fuente = await sesion.requestHitTestSource({ space: await sesion.requestReferenceSpace('viewer') }); } catch (e) { gr.fuente = null; }
    sesion.addEventListener('end', () => { gr.sesion = null; });
    $('#gr-empezar').textContent = 'Empezar';
    $('#gr-estado').textContent = 'Marca la habitación en la que estás y pulsa «Empezar».';
    grChips();
    sesion.requestAnimationFrame(grCuadro);
  } catch (e) {
    registrar('grabar', e);
    alert('No se pudo abrir la cámara: ' + e.message);
  }
};

function grCuadro(t, frame) {
  const s = gr.sesion; if (!s) return;
  s.requestAnimationFrame(grCuadro);
  const gl = gr.gl; const capa = s.renderState.baseLayer;
  gl.bindFramebuffer(gl.FRAMEBUFFER, capa.framebuffer);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
  const pose = frame.getViewerPose(gr.ref);
  if (!pose) return;
  if (gr.fuente) {                                           // el suelo: lo más bajo que se ha encontrado
    const r = frame.getHitTestResults(gr.fuente);
    if (r.length) { const y = r[0].getPose(gr.ref).transform.position.y; if (gr.suelo === null || y < gr.suelo) gr.suelo = y; }
  }
  gr.perdido = pose.emulatedPosition;
  const vista = pose.views[0];
  const m = vista.transform.matrix;
  const pos = [m[12], m[13], m[14]];
  const f = [-m[8], -m[9], -m[10]];
  // Velocidad de este cuadro (para que el fotograma salga nítido)
  let giro = 0; let paso = 0;
  if (gr.previa) {
    giro = Math.acos(Math.min(1, f[0] * gr.previa.f[0] + f[1] * gr.previa.f[1] + f[2] * gr.previa.f[2]));
    paso = Math.hypot(pos[0] - gr.previa.pos[0], pos[1] - gr.previa.pos[1], pos[2] - gr.previa.pos[2]);
  }
  gr.previa = { f, pos };
  let aviso = '';
  if (gr.perdido) aviso = 'Posición perdida: vuelve a mirar algo ya grabado, despacio';
  else if (gr.grabando && (giro > GR.MAX_GIRO * 1.6 || paso > GR.MAX_PASO * 1.6)) aviso = 'Más despacio';
  $('#gr-aviso').textContent = aviso;
  if (gr.grabando && !gr.perdido) {
    const ult = gr.ultima;
    const toca = !ult || Math.hypot(pos[0] - ult.pos[0], pos[2] - ult.pos[2]) >= GR.PASO
      || f[0] * ult.f[0] + f[1] * ult.f[1] + f[2] * ult.f[2] < GR.GIRO;
    if (toca && !gr.ocupado && giro < GR.MAX_GIRO && paso < GR.MAX_PASO && vista.camera) {
      grCapturar(vista, capa, frame, pos, f);
    }
    const r = gr.recorrido; const u = r[r.length - 1];
    if (!u || Math.hypot(pos[0] - u[0], -pos[2] - u[1]) > 0.05) r.push([pos[0], -pos[2]]);
  }
  if (++gr.n % 3 === 0) grMapa(pos, f, vista);
}

function grCapturar(vista, capa, frame, pos, f) {
  const gl = gr.gl; const cam = vista.camera;
  const tex = gr.binding.getCameraImage(cam);
  const w = cam.width; const h = cam.height;
  gl.bindFramebuffer(gl.FRAMEBUFFER, gr.fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
  const px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
  gl.bindFramebuffer(gl.FRAMEBUFFER, capa.framebuffer);
  gr.ultima = { pos, f };
  gr.total++;
  const meta = {
    levantamiento: gr.nombre, fichero: `${gr.id}-${String(gr.total).padStart(5, '0')}.jpg`, escaneo: gr.id, tipo: 'video',
    habitacion: gr.habitacion || null, n: gr.total, hora: Date.now(), ancho: w, alto: h, suelo: gr.suelo,
    vista: Array.from(vista.transform.matrix), proyeccion: Array.from(vista.projectionMatrix),
  };
  gr.ocupado = true;
  grTrabajador.postMessage({ tipo: 'foto', px: px.buffer, w, h, meta, pano: false }, [px.buffer]);
  grVisto(frame, vista);
  $('#gr-cuenta').textContent = `${gr.total} fotogramas · ${esc.subidas} subidos` + (gr.habitacion ? ` · ${gr.habitacion}` : '');
}

// Lo que la cámara ha visto, en el mapa: con la profundidad de ARCore si la hay; si no, un abanico de 3 m.
function grVisto(frame, vista) {
  const m = vista.transform.matrix;
  const marcar = (x, y, tipo) => {
    const k = `${Math.floor(x / GR.CELDA)},${Math.floor(y / GR.CELDA)}`;
    if ((gr.visto.get(k) || 0) < tipo) gr.visto.set(k, tipo);
  };
  let prof = null;
  try { prof = frame.getDepthInformation ? frame.getDepthInformation(vista) : null; } catch (e) { prof = null; }
  const inv = invertir(vista.projectionMatrix);
  const suelo = gr.suelo ?? (m[13] - 1.4);
  for (let j = 0; j < 24; j++) {
    for (let i = 0; i < 18; i++) {
      const u = (i + 0.5) / 18; const v = (j + 0.5) / 24;
      let d = prof ? prof.getDepthInMeters(u, v) : 0;
      const c = porMatriz(inv, 2 * u - 1, 1 - 2 * v, -1, 1);
      const dir = [c[0] / c[3], c[1] / c[3], c[2] / c[3]];
      if (!(d > 0.2 && d < 6)) {                            // sin profundidad: hasta donde corta el suelo, o 3 m
        if (prof) continue;
        d = 3;
      }
      const s = d / -dir[2];
      const p = porMatriz(m, dir[0] * s, dir[1] * s, -d, 1);
      const altura = p[1] - suelo;
      if (altura < -0.15) continue;
      marcar(p[0], -p[2], altura > 0.25 ? 2 : 1);            // 2: pared o mueble; 1: suelo visto
    }
  }
}

function grMapa(pos, f, vista) {
  const { g, w, h } = prepararLienzo($('#g-mapa'));
  const pts = [...gr.visto.keys()].map((k) => k.split(',').map((x) => (+x + 0.5) * GR.CELDA));
  const todos = pts.concat(gr.recorrido, [[pos[0], -pos[2]]]);
  const xs = todos.map((p) => p[0]); const ys = todos.map((p) => p[1]);
  const x0 = Math.min(...xs) - 1; const x1 = Math.max(...xs) + 1; const y0 = Math.min(...ys) - 1; const y1 = Math.max(...ys) + 1;
  const esc_ = Math.min(w / (x1 - x0), h / (y1 - y0), 60);
  const ox = w / 2 - esc_ * (x0 + x1) / 2; const oy = h / 2 + esc_ * (y0 + y1) / 2;
  const P = (x, y) => [ox + x * esc_, oy - y * esc_];
  const lado = Math.max(1.5, GR.CELDA * esc_);
  for (const [k, tipo] of gr.visto) {
    const [i, j] = k.split(',').map(Number);
    const [x, y] = P(i * GR.CELDA, (j + 1) * GR.CELDA);
    g.fillStyle = tipo === 2 ? 'rgba(236,234,228,.9)' : 'rgba(91,185,140,.35)';
    g.fillRect(x, y, lado, lado);
  }
  if (gr.recorrido.length > 1) {
    g.strokeStyle = '#6fb3ff'; g.lineWidth = 2; g.beginPath();
    gr.recorrido.forEach((p, i) => (i ? g.lineTo(...P(...p)) : g.moveTo(...P(...p)))); g.stroke();
  }
  // Tú y hacia dónde miras
  const [cx, cy] = P(pos[0], -pos[2]);
  const ang = Math.atan2(-f[2], f[0]);                       // en planta: x, -z
  g.fillStyle = 'rgba(228,87,46,.35)'; g.beginPath(); g.moveTo(cx, cy);
  g.arc(cx, cy, 2.5 * esc_, -ang - 0.3, -ang + 0.3); g.closePath(); g.fill();
  g.fillStyle = '#e4572e'; g.beginPath(); g.arc(cx, cy, 5, 0, 7); g.fill();
}

$('#gr-empezar').onclick = () => {
  gr.grabando = !gr.grabando;
  $('#gr-empezar').textContent = gr.grabando ? 'Pausar' : 'Seguir';
  $('#gr-estado').textContent = gr.grabando
    ? 'Recorre el perímetro de la habitación y luego una vuelta por el centro, mirando paredes y techo.'
    : 'En pausa. Puedes cambiar de habitación y seguir.';
};
$('#gr-terminar').onclick = async () => {
  gr.grabando = false;
  if (gr.sesion) await gr.sesion.end().catch(() => {});
  gr.sesion = null;
  mostrar('inicio');
  await new Promise((ok) => setTimeout(ok, 800));
  await subirPendientes();
  const n = await pintarPendientes();
  alert(n ? `Grabación guardada: ${gr.total} fotogramas. Quedan ${n} por subir; se subirán solos con conexión al PC.`
    : `Grabación terminada: ${gr.total} fotogramas, todos en el PC.`);
};
