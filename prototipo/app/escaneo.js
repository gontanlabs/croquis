'use strict';
// Escaneo guiado de la casa: en cada habitación, uno o dos puntos; en cada punto, fotos hacia unos objetivos que
// cubren todo alrededor (como una foto esférica). Cada foto lleva la posición y orientación exactas del móvil
// (seguimiento de ARCore), todas en el mismo sistema de coordenadas: las habitaciones quedan unidas solas.
// Las fotos se guardan en el móvil (IndexedDB) y se suben al PC en cuanto se puede.

// [inclinación, cuántos, desfase]. En vertical la cámara abarca unos 33° de ancho y 66° de alto: objetivos cada 24°
// en horizontal (las fotos se solapan ~9°, lo justo para que COLMAP encuentre puntos comunes); el suelo, con menos.
const ANILLOS = [[0, 15, 0], [35, 12, 15], [-32, 8, 0], [66, 5, 0]];
const PANO_W = 720; const PANO_H = 360;                                      // panorámica en directo
const ACIERTO = Math.cos((6 * Math.PI) / 180);                               // a menos de 6° del objetivo
const QUIETO = Math.cos((0.12 * Math.PI) / 180);                             // menos de 0,12° entre cuadros (~4°/s)
const QUIETO_MS = 500;                                                        // y así durante medio segundo: foto nítida

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
      const q = `nombre=${encodeURIComponent(f.meta.levantamiento)}&fichero=${encodeURIComponent(f.meta.fichero)}`;
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
function nuevaPano() {
  const c = document.createElement('canvas'); c.width = PANO_W; c.height = PANO_H;
  const g = c.getContext('2d'); g.fillStyle = '#2a2d33'; g.fillRect(0, 0, PANO_W, PANO_H);
  esc.pano = c; esc.panoDatos = g.getImageData(0, 0, PANO_W, PANO_H); esc.panoPeso = new Float32Array(PANO_W * PANO_H);
}
function empezarPunto(hab, punto) {
  nuevaPano();
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
  esc.idEscaneo = Date.now().toString(36);          // que un escaneo nuevo no pise las fotos de otro
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
  const pos0 = [m[12], m[13], m[14]];
  const sinGiro = esc.previo ? punto3(f, esc.previo) > QUIETO : false;
  const sinMover = esc.prevPos ? Math.hypot(pos0[0] - esc.prevPos[0], pos0[1] - esc.prevPos[1], pos0[2] - esc.prevPos[2]) < 0.002 : false;
  if (!(sinGiro && sinMover)) esc.quietoDesde = t;
  const quieto = t - (esc.quietoDesde || t) > QUIETO_MS;
  esc.previo = f; esc.prevPos = pos0;
  if (!esc.hab) return;
  if (esc.esperandoPunto) {                                    // segundo punto: cuando se haya separado 80 cm
    const [x0, z0] = esc.esperandoPunto.desde;
    const dist = Math.hypot(m[12] - x0, m[14] - z0);
    $('#e-cuenta').textContent = `Te has movido ${dist.toFixed(1).replace('.', ',')} m`;
    if (dist < 0.8) return;
    esc.esperandoPunto = null;
    empezarPunto(esc.hab, esc.punto + 1);
    if (navigator.vibrate) navigator.vibrate([40, 60, 40]);
    return;
  }
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
  // Hacia dónde ir: flecha al objetivo pendiente más cercano (o línea, si ya está en pantalla)
  if (mejor) {
    const d = direccion(mejor.o);
    const v = porMatriz(inv, pos[0] + d[0] * 2, pos[1] + d[1] * 2, pos[2] + d[2] * 2, 1);
    const clip = porMatriz(pr, v[0], v[1], v[2], 1);
    const enPantalla = clip[3] > 0 && Math.abs(clip[0] / clip[3]) < 0.85 && Math.abs(clip[1] / clip[3]) < 0.85;
    let dx = v[0]; let dy = -v[1];
    if (v[2] > 0) dx = dx >= 0 ? 1 : -1, dy = 0;          // detrás: girar hacia el lado más corto
    const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
    if (!esc.perdido && !esc.esperandoPunto) {
      const pista = enPantalla ? 've al círculo y quédate quieto'
        : Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'gira a la derecha →' : '← gira a la izquierda')
          : (dy < 0 ? 'apunta más arriba ↑' : 'apunta más abajo ↓');
      $('#e-pista').textContent = pista;
    }
    if (enPantalla) {
      const x = ((clip[0] / clip[3]) * 0.5 + 0.5) * w; const y = (1 - ((clip[1] / clip[3]) * 0.5 + 0.5)) * h;
      g.setLineDash([8, 8]); g.strokeStyle = 'rgba(255,255,255,.8)'; g.lineWidth = 3;
      g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(x, y); g.stroke(); g.setLineDash([]);
    } else {
      const r = Math.min(w, h) * 0.22; const cx = w / 2 + dx * r; const cy = h / 2 + dy * r;
      const a = Math.atan2(dy, dx);
      g.save(); g.translate(cx, cy); g.rotate(a);
      g.beginPath(); g.moveTo(34, 0); g.lineTo(-14, -26); g.lineTo(-4, 0); g.lineTo(-14, 26); g.closePath();
      g.fillStyle = 'rgba(255,255,255,.92)'; g.fill(); g.restore();
    }
  }
  // Centro de la pantalla y, si apunta a un objetivo, el anillo que se llena mientras está quieto
  g.beginPath(); g.arc(w / 2, h / 2, 6, 0, 7); g.fillStyle = '#e4572e'; g.fill();
  if (mejor && mejor.c > ACIERTO) {
    const prog = Math.min(1, (t - (esc.quietoDesde || t)) / QUIETO_MS);
    g.beginPath(); g.arc(w / 2, h / 2, 22, -Math.PI / 2, -Math.PI / 2 + prog * 2 * Math.PI);
    g.strokeStyle = '#5bb98c'; g.lineWidth = 5; g.stroke();
    if (prog < 1) $('#e-pista').textContent = 'quieto…';
  }
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
    levantamiento: esc.nombre, fichero: `${esc.idEscaneo}-${n}.jpg`, escaneo: esc.idEscaneo, habitacion: esc.hab, punto: esc.punto, n: esc.total,
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
      coserEnPano(lienzo, meta);
      const jpeg = await new Promise((ok) => lienzo.toBlob(ok, 'image/jpeg', 0.88));
      await almacen.poner({ fichero: `${esc.nombre}-${meta.fichero}`, jpeg, meta: { ...meta, fichero: meta.fichero } });
    } catch (e) { registrar('foto', e); } finally { esc.ocupado = false; }
    subirPendientes();
  }, 0);
}

function coserEnPano(lienzo, meta) {
  if (!esc.pano) return;
  const pw = 120; const ph = Math.round((pw * meta.alto) / meta.ancho);          // la foto, pequeña
  const pc = document.createElement('canvas'); pc.width = pw; pc.height = ph;
  pc.getContext('2d').drawImage(lienzo, 0, 0, pw, ph);
  const src = pc.getContext('2d').getImageData(0, 0, pw, ph).data;
  const M = meta.vista; const P = meta.proyeccion; const out = esc.panoDatos.data;
  for (let j = 0; j < PANO_H; j++) {
    const lat = Math.PI / 2 - ((j + 0.5) / PANO_H) * Math.PI;
    const cl = Math.cos(lat); const sl = Math.sin(lat);
    for (let i = 0; i < PANO_W; i++) {
      const lon = ((i + 0.5) / PANO_W) * 2 * Math.PI - Math.PI;
      const dx = cl * Math.sin(lon); const dy = sl; const dz = -cl * Math.cos(lon);
      const cx = M[0] * dx + M[1] * dy + M[2] * dz;            // a ejes de la cámara: R^T · d
      const cy = M[4] * dx + M[5] * dy + M[6] * dz;
      const cz = M[8] * dx + M[9] * dy + M[10] * dz;
      if (cz > -1e-3) continue;
      const nx = (P[0] * cx + P[8] * cz) / -cz; const ny = (P[5] * cy + P[9] * cz) / -cz;
      if (nx <= -1 || nx >= 1 || ny <= -1 || ny >= 1) continue;
      const peso = (1 - nx * nx) * (1 - ny * ny);
      const k = j * PANO_W + i;
      if (peso <= esc.panoPeso[k]) continue;                    // se queda la foto que lo vio más de frente
      esc.panoPeso[k] = peso;
      const u = Math.floor((nx * 0.5 + 0.5) * (pw - 1)); const v = Math.floor((1 - (ny * 0.5 + 0.5)) * (ph - 1));
      const a = (v * pw + u) * 4; const b = k * 4;
      out[b] = src[a]; out[b + 1] = src[a + 1]; out[b + 2] = src[a + 2]; out[b + 3] = 255;
    }
  }
  esc.pano.getContext('2d').putImageData(esc.panoDatos, 0, 0);
}

function pintarMapa(pr) {
  const { g, w, h } = prepararLienzo($('#e-mapa'));
  if (!esc.hab || !esc.pano) return;
  g.drawImage(esc.pano, 0, 0, w, h);
  const X = (lonRad) => ((((lonRad + Math.PI) / (2 * Math.PI)) % 1 + 1) % 1) * w;
  const Y = (incl) => ((90 - incl) / 180) * h;
  for (const o of esc.objetivos) {
    const lon = esc.yaw0 === null ? 0 : esc.yaw0 + (o.yaw * Math.PI) / 180;
    g.beginPath(); g.arc(X(lon), Y(o.incl), o.hecho ? 2 : 3.5, 0, 7);
    if (o.hecho) { g.fillStyle = 'rgba(91,185,140,.9)'; g.fill(); } else { g.strokeStyle = '#fff'; g.lineWidth = 1.5; g.stroke(); }
  }
  if (esc.previo) {                                            // hacia dónde miras ahora
    const f = esc.previo; const lon = Math.atan2(f[0], -f[2]); const lat = (Math.asin(f[1]) * 180) / Math.PI;
    g.strokeStyle = '#e4572e'; g.lineWidth = 2; g.strokeRect(X(lon) - 7, Y(lat) - 12, 14, 24);
  }
}

$('#e-punto').onclick = () => {
  if (!esc.hab || !esc.fotosPunto.length) return;
  const m = esc.fotosPunto.map((f) => [f.vista[12], f.vista[14]]);
  esc.esperandoPunto = { desde: [m.reduce((a, b) => a + b[0], 0) / m.length, m.reduce((a, b) => a + b[1], 0) / m.length] };
  $('#e-pista').textContent = '';
  $('#e-estado').textContent = `${esc.hab}: muévete 1 o 2 m a otro sitio de la habitación. Empezará solo.`;
};
$('#e-habitacion').onclick = () => { esc.esperandoPunto = null; esc.hab = null; elegirHabitacion(); contar(); };
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
