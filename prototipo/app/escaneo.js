'use strict';
// Escaneo guiado de la casa: en cada habitación, uno o dos puntos; en cada punto, fotos hacia unos objetivos que
// cubren todo alrededor (como una foto esférica). Cada foto lleva la posición y orientación exactas del móvil
// (seguimiento de ARCore), todas en el mismo sistema de coordenadas: las habitaciones quedan unidas solas.
// Las fotos se guardan en el móvil (IndexedDB) y se suben al PC en cuanto se puede.

const ANILLOS = [[0, 12, 0], [40, 8, 22.5], [-40, 8, 22.5], [72, 4, 45]];    // [inclinación, cuántos, desfase]
const ACIERTO = Math.cos((6 * Math.PI) / 180);                               // a menos de 6° del objetivo
const QUIETO = Math.cos((0.7 * Math.PI) / 180);                              // menos de 0,7° entre cuadros

const esc = {
  sesion: null, gl: null, binding: null, ref: null, fb: null,
  hab: null, punto: 1, yaw0: 0, objetivos: [], fotosPunto: [], previo: null, ultima: 0, ocupado: false,
  total: 0, subidas: 0, nombre: 'Mi casa', perdido: false,
};

// --- Almacén local (IndexedDB): fotos pendientes de subir ---
const almacen = (() => {
  let db = null;
  const abrir = () => new Promise((ok, mal) => {
    if (db) return ok(db);
    const r = indexedDB.open('croquis', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('fotos', { keyPath: 'fichero' });
    r.onsuccess = () => { db = r.result; ok(db); };
    r.onerror = () => mal(r.error);
  });
  const tx = async (modo, fn) => {
    const d = await abrir();
    return new Promise((ok, mal) => {
      const t = d.transaction('fotos', modo); const s = t.objectStore('fotos'); const res = fn(s);
      t.oncomplete = () => ok(res && res.result); t.onerror = () => mal(t.error);
    });
  };
  return {
    poner: (f) => tx('readwrite', (s) => s.put(f)),
    quitar: (k) => tx('readwrite', (s) => s.delete(k)),
    todas: () => tx('readonly', (s) => s.getAll()),
  };
})();

let subiendo = false;
async function subirPendientes() {
  if (subiendo) return;
  subiendo = true;
  try {
    const pendientes = await almacen.todas();
    for (const f of pendientes) {
      const q = `nombre=${encodeURIComponent(f.meta.levantamiento)}&fichero=${encodeURIComponent(f.fichero)}`;
      const r = await fetch('/api/foto?' + q, { method: 'POST', body: f.jpeg });
      if (!r.ok) throw new Error('foto ' + r.status);
      const m = await fetch('/api/captura', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: f.meta.levantamiento, fotos: [f.meta] }) });
      if (!m.ok) throw new Error('datos ' + m.status);
      await almacen.quitar(f.fichero);
      esc.subidas++;
    }
  } catch (e) { /* sin conexión: se reintenta luego */ } finally { subiendo = false; }
  pintarPendientes();
}
async function pintarPendientes() {
  const n = (await almacen.todas().catch(() => [])).length;
  const p = document.getElementById('e-pendientes');
  if (p) p.textContent = n ? `${n} fotos guardadas en el móvil, pendientes de subir al PC.` : '';
  return n;
}
setInterval(() => { if (!esc.ocupado) subirPendientes(); }, 5000);

// --- Objetivos de un punto ---
function prepararObjetivos() {
  esc.objetivos = [];
  for (const [incl, n, desfase] of ANILLOS) {
    for (let k = 0; k < n; k++) esc.objetivos.push({ yaw: (k * 360) / n + desfase, incl, hecho: false });
  }
}
function direccion(o) {
  const y = esc.yaw0 + (o.yaw * Math.PI) / 180; const p = (o.incl * Math.PI) / 180;
  return [Math.sin(y) * Math.cos(p), Math.sin(p), -Math.cos(y) * Math.cos(p)];
}
const adelante = (m) => [-m[8], -m[9], -m[10]];
const punto3 = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

// --- Pantalla ---
function elegirHabitacion() {
  const chips = $('#e-chips'); chips.innerHTML = '';
  for (const n of NOMBRES) {
    const b = document.createElement('button'); b.textContent = n;
    b.onclick = () => {
      let nombre = n.toUpperCase(); let k = 2;
      const usados = new Set(esc.usados || []);
      while (usados.has(nombre)) nombre = `${n.toUpperCase()} ${k++}`;
      esc.usados = [...usados, nombre];
      empezarPunto(nombre, 1);
    };
    chips.appendChild(b);
  }
  $('#e-estado').textContent = '¿En qué habitación estás? Ponte en un sitio desde el que se vea casi todo.';
}
function empezarPunto(hab, punto) {
  $('#e-chips').innerHTML = '';
  esc.hab = hab; esc.punto = punto; esc.fotosPunto = []; esc.yaw0 = null;
  prepararObjetivos();
  $('#e-estado').textContent = `${hab} · punto ${punto}: apunta a los círculos blancos y quédate quieto un instante en cada uno.`;
}
function contar() {
  const h = esc.objetivos.filter((o) => o.hecho).length;
  $('#e-cuenta').textContent = esc.hab ? `${h} de ${esc.objetivos.length} en este punto · ${esc.total} fotos en total · ${esc.subidas} subidas` : '';
  if (esc.hab && h === esc.objetivos.length) {
    $('#e-estado').textContent = esc.punto === 1
      ? `${esc.hab}: punto completo. Muévete 1 o 2 m y pulsa «Segundo punto», o pasa a «Otra habitación».`
      : `${esc.hab}: completa. Pulsa «Otra habitación» o «Terminar».`;
  }
}

$('#b-escanear').onclick = async () => {
  esc.nombre = $('#nombre').value.trim() || 'Mi casa';
  try {
    const sesion = await navigator.xr.requestSession('immersive-ar', {
      requiredFeatures: ['camera-access'], optionalFeatures: ['dom-overlay'], domOverlay: { root: $('#escaneo') },
    });
    esc.sesion = sesion;
    mostrar('escaneo');
    $('#escaneo').addEventListener('beforexrselect', (e) => e.preventDefault());
    const gl = document.createElement('canvas').getContext('webgl', { xrCompatible: true });
    esc.gl = gl;
    sesion.updateRenderState({ baseLayer: new XRWebGLLayer(sesion, gl) });
    esc.binding = new XRWebGLBinding(sesion, gl);
    esc.ref = await sesion.requestReferenceSpace('local');
    esc.fb = gl.createFramebuffer();
    sesion.addEventListener('end', () => { esc.sesion = null; });
    elegirHabitacion();
    sesion.requestAnimationFrame(cuadro);
  } catch (e) {
    registrar('escaneo', e);
    alert('No se pudo abrir la cámara: ' + e.message);
  }
};

function cuadro(t, frame) {
  const s = esc.sesion; if (!s) return;
  s.requestAnimationFrame(cuadro);
  const gl = esc.gl; const capa = s.renderState.baseLayer;
  gl.bindFramebuffer(gl.FRAMEBUFFER, capa.framebuffer);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
  const pose = frame.getViewerPose(esc.ref);
  const { g, w, h } = prepararLienzo($('#e-lienzo'));
  if (!pose) return;
  if (pose.emulatedPosition !== esc.perdido) {
    esc.perdido = pose.emulatedPosition;
    if (esc.perdido) $('#e-estado').textContent = 'Se ha perdido la posición: apunta a algo ya escaneado y muévete despacio.';
    else contar();
  }
  const vista = pose.views[0];
  const m = vista.transform.matrix;
  const f = adelante(m);
  if (esc.hab && esc.yaw0 === null) esc.yaw0 = Math.atan2(f[0], -f[2]);     // el primer objetivo, de frente
  const quieto = esc.previo ? punto3(f, esc.previo) > QUIETO : false;
  esc.previo = f;
  if (!esc.hab) return;
  // Objetivos en pantalla
  const inv = vista.transform.inverse.matrix; const pr = vista.projectionMatrix;
  const pos = [m[12], m[13], m[14]];
  let mejor = null;
  for (const o of esc.objetivos) {
    const d = direccion(o);
    const c = punto3(d, f);
    if (!o.hecho && (!mejor || c > mejor.c)) mejor = { o, c };
    const P = [pos[0] + d[0] * 2, pos[1] + d[1] * 2, pos[2] + d[2] * 2];
    const v = porMatriz(inv, P[0], P[1], P[2], 1);
    const clip = porMatriz(pr, v[0], v[1], v[2], 1);
    if (clip[3] <= 0) continue;
    const x = ((clip[0] / clip[3]) * 0.5 + 0.5) * w; const y = (1 - ((clip[1] / clip[3]) * 0.5 + 0.5)) * h;
    g.beginPath(); g.arc(x, y, o.hecho ? 9 : 16, 0, 7);
    if (o.hecho) { g.fillStyle = 'rgba(91,185,140,.85)'; g.fill(); } else { g.strokeStyle = '#fff'; g.lineWidth = 3; g.stroke(); }
  }
  // Centro de la pantalla
  g.beginPath(); g.arc(w / 2, h / 2, 6, 0, 7); g.fillStyle = '#e4572e'; g.fill();
  // Foto automática: apuntando a un objetivo pendiente y quieto
  if (mejor && mejor.c > ACIERTO && quieto && !esc.perdido && !esc.ocupado && t - esc.ultima > 350 && vista.camera) {
    esc.ultima = t;
    capturar(vista, mejor.o, capa);
  }
  pintarMapa(pr);
}

function capturar(vista, objetivo, capa) {
  const gl = esc.gl; const cam = vista.camera;
  const tex = esc.binding.getCameraImage(cam);
  const w = cam.width; const h = cam.height;
  gl.bindFramebuffer(gl.FRAMEBUFFER, esc.fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
  const px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
  gl.bindFramebuffer(gl.FRAMEBUFFER, capa.framebuffer);
  objetivo.hecho = true;
  esc.total++;
  const n = String(esc.total).padStart(4, '0');
  const meta = {
    levantamiento: esc.nombre, fichero: `${n}.jpg`, habitacion: esc.hab, punto: esc.punto, n: esc.total,
    objetivo: [objetivo.yaw, objetivo.incl], hora: Date.now(), ancho: w, alto: h,
    vista: Array.from(vista.transform.matrix), proyeccion: Array.from(vista.projectionMatrix),
  };
  esc.fotosPunto.push(meta);
  if (navigator.vibrate) navigator.vibrate(25);
  contar();
  esc.ocupado = true;
  setTimeout(async () => {          // fuera del cuadro: invertir filas y pasar a JPEG
    try {
      const lienzo = document.createElement('canvas'); lienzo.width = w; lienzo.height = h;
      const c = lienzo.getContext('2d'); const img = c.createImageData(w, h);
      const fila = w * 4;
      for (let y = 0; y < h; y++) img.data.set(px.subarray((h - 1 - y) * fila, (h - y) * fila), y * fila);
      c.putImageData(img, 0, 0);
      const jpeg = await new Promise((ok) => lienzo.toBlob(ok, 'image/jpeg', 0.88));
      await almacen.poner({ fichero: `${esc.nombre}-${meta.fichero}`, jpeg, meta: { ...meta, fichero: meta.fichero } });
    } catch (e) { registrar('foto', e); } finally { esc.ocupado = false; }
    subirPendientes();
  }, 0);
}

function pintarMapa(pr) {
  const { g, w, h } = prepararLienzo($('#e-mapa'));
  if (!esc.hab) return;
  const fx = 2 * Math.atan(1 / pr[0]) * (180 / Math.PI); const fy = 2 * Math.atan(1 / pr[5]) * (180 / Math.PI);
  const X = (yaw) => (((yaw % 360) + 360) % 360) / 360 * w; const Y = (incl) => (90 - incl) / 180 * h;
  g.fillStyle = 'rgba(91,185,140,.45)';
  for (const o of esc.objetivos) {
    if (!o.hecho) continue;
    const x0 = X(o.yaw - fx / 2); const ww = (fx / 360) * w; const y0 = Y(o.incl + fy / 2); const hh = (fy / 180) * h;
    g.fillRect(x0, y0, ww, hh);
    if (x0 + ww > w) g.fillRect(x0 - w, y0, ww, hh);
  }
  for (const o of esc.objetivos) {
    g.beginPath(); g.arc(X(o.yaw), Y(o.incl), 2.5, 0, 7); g.fillStyle = o.hecho ? '#5bb98c' : '#fff'; g.fill();
  }
}

$('#e-punto').onclick = () => { if (esc.hab) empezarPunto(esc.hab, esc.punto + 1); };
$('#e-habitacion').onclick = () => { esc.hab = null; elegirHabitacion(); contar(); };
$('#e-terminar').onclick = async () => {
  if (esc.sesion) await esc.sesion.end().catch(() => {});
  esc.sesion = null; esc.hab = null;
  mostrar('inicio');
  await subirPendientes();
  const n = await pintarPendientes();
  alert(n ? `Escaneo guardado: ${esc.total} fotos. Quedan ${n} por subir; se subirán solas cuando haya conexión con el PC.`
    : `Escaneo terminado: ${esc.total} fotos, todas en el PC.`);
};
pintarPendientes();
