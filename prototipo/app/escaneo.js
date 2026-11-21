'use strict';
// Escaneo de la casa: en cada habitación, uno o dos puntos. En cada punto se barre alrededor despacio; cuando el
// móvil está quieto y mira a algo que aún no se ha fotografiado, la foto se hace sola. La panorámica se va montando
// en directo y lo gris es lo que falta. Cada foto lleva la posición y orientación del móvil (ARCore), todas en el
// mismo sistema: las habitaciones quedan unidas solas. Las fotos se guardan en el móvil y se suben al PC.

const CELDA = 10;                                     // rejilla de cobertura: celdas de 10° × 10°
const LAT_MIN = -40; const LAT_MAX = 80;              // lo que hace falta ver: paredes y techo (el suelo, poco)
const QUIETO = Math.cos((0.15 * Math.PI) / 180);      // menos de 0,15° entre cuadros (~5°/s)…
const QUIETO_MS = 250;                                // …durante un cuarto de segundo: foto nítida
const NUEVO = 0.35;                                   // la foto tiene que añadir al menos un 35 % de zona nueva
const MEDIO_ANCHO = 16; const MEDIO_ALTO = 32;        // lo que abarca una foto con el móvil en vertical (grados)

const esc = {
  sesion: null, gl: null, binding: null, ref: null, fb: null,
  hab: null, punto: 1, cubierto: null, fotosPunto: [], previo: null, prevPos: null, quietoDesde: 0,
  ocupado: false, total: 0, subidas: 0, nombre: 'Mi casa', idEscaneo: '', perdido: false, panoBmp: null,
  esperandoPunto: null, usados: [],
};

const trabajador = new Worker('trabajador.js');
trabajador.onmessage = async (e) => {
  const m = e.data;
  if (m.tipo === 'pano') { if (esc.panoBmp) esc.panoBmp.close(); esc.panoBmp = m.bmp; return; }
  if (m.tipo === 'foto') {
    try { await almacen.poner({ fichero: `${m.meta.levantamiento}-${m.meta.fichero}`, jpeg: m.jpeg, meta: m.meta }); } catch (err) { registrar('guardar', err); }
    esc.ocupado = false;
    subirPendientes();
  }
};

// --- Almacén local (IndexedDB) y subida al PC ---
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
      const t = d.transaction('fotos', modo); const res = fn(t.objectStore('fotos'));
      t.oncomplete = () => ok(res && res.result); t.onerror = () => mal(t.error);
    });
  };
  return { poner: (f) => tx('readwrite', (s) => s.put(f)), quitar: (k) => tx('readwrite', (s) => s.delete(k)), todas: () => tx('readonly', (s) => s.getAll()) };
})();

let subiendo = false;
async function subirPendientes() {
  if (subiendo) return;
  subiendo = true;
  try {
    for (const f of await almacen.todas()) {
      const q = `nombre=${encodeURIComponent(f.meta.levantamiento)}&fichero=${encodeURIComponent(f.meta.fichero)}`;
      if (!(await fetch('/api/foto?' + q, { method: 'POST', body: f.jpeg })).ok) throw new Error('foto');
      const r = await fetch('/api/captura', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: f.meta.levantamiento, fotos: [f.meta] }) });
      if (!r.ok) throw new Error('datos');
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

// --- Cobertura: celdas de la esfera ya fotografiadas ---
const N_LON = 360 / CELDA; const N_LAT = 180 / CELDA;
const celda = (lonDeg, latDeg) => [Math.floor((((lonDeg + 180) % 360) + 360) % 360 / CELDA), Math.min(N_LAT - 1, Math.floor((90 - latDeg) / CELDA))];
function celdasDe(lonDeg, latDeg) {
  const out = [];
  const ancho = MEDIO_ANCHO / Math.max(0.2, Math.cos((latDeg * Math.PI) / 180));
  for (let la = latDeg - MEDIO_ALTO + CELDA / 2; la <= latDeg + MEDIO_ALTO; la += CELDA) {
    for (let lo = lonDeg - ancho + CELDA / 2; lo <= lonDeg + ancho; lo += CELDA) {
      if (la > 90 || la < -90) continue;
      const [i, j] = celda(lo, la); out.push(j * N_LON + i);
    }
  }
  return [...new Set(out)];
}
const necesarias = (() => {
  const s = [];
  for (let j = 0; j < N_LAT; j++) {
    const lat = 90 - (j + 0.5) * CELDA;
    if (lat >= LAT_MIN && lat <= LAT_MAX) for (let i = 0; i < N_LON; i++) s.push(j * N_LON + i);
  }
  return s;
})();
const porcentaje = () => Math.round((necesarias.filter((k) => esc.cubierto[k]).length / necesarias.length) * 100);
const lonLat = (f) => [Math.atan2(f[0], -f[2]) * 180 / Math.PI, Math.asin(Math.max(-1, Math.min(1, f[1]))) * 180 / Math.PI];

// --- Pantalla ---
function elegirHabitacion() {
  const chips = $('#e-chips'); chips.innerHTML = '';
  for (const n of NOMBRES) {
    const b = document.createElement('button'); b.textContent = n;
    b.onclick = () => {
      let nombre = n.toUpperCase(); let k = 2;
      while (esc.usados.includes(nombre)) nombre = `${n.toUpperCase()} ${k++}`;
      esc.usados.push(nombre);
      empezarPunto(nombre, 1);
    };
    chips.appendChild(b);
  }
  $('#e-pista').textContent = '';
  $('#e-estado').textContent = '¿En qué habitación estás? Ponte donde se vea casi todo.';
}
function empezarPunto(hab, punto) {
  $('#e-chips').innerHTML = '';
  esc.hab = hab; esc.punto = punto; esc.fotosPunto = []; esc.cubierto = new Uint8Array(N_LON * N_LAT);
  trabajador.postMessage({ tipo: 'reiniciar' });
  $('#e-estado').textContent = `${hab} · punto ${punto}: barre despacio alrededor, paredes y techo. Las fotos se hacen solas.`;
}
function contar() {
  if (!esc.hab) { $('#e-cuenta').textContent = ''; return; }
  const p = porcentaje();
  $('#e-cuenta').textContent = `${p} % visto · ${esc.fotosPunto.length} fotos aquí · ${esc.total} en total · ${esc.subidas} subidas`;
  if (p >= 92) {
    $('#e-estado').textContent = esc.punto === 1
      ? `${esc.hab}: hecho. Pulsa «Segundo punto» y muévete 1 o 2 m, o pasa a «Otra habitación».`
      : `${esc.hab}: completa. Pulsa «Otra habitación» o «Terminar».`;
  }
}

$('#b-escanear').onclick = async () => {
  esc.nombre = $('#nombre').value.trim() || 'Mi casa';
  esc.idEscaneo = Date.now().toString(36);
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
  if (!pose) return;                                      // sin posición: se queda lo último dibujado
  if (pose.emulatedPosition !== esc.perdido) {
    esc.perdido = pose.emulatedPosition;
    $('#e-pista').textContent = esc.perdido ? 'Posición perdida: apunta a algo ya visto y muévete despacio' : '';
  }
  const vista = pose.views[0];
  const m = vista.transform.matrix;
  const f = [-m[8], -m[9], -m[10]];
  const pos = [m[12], m[13], m[14]];
  const sinGiro = esc.previo ? f[0] * esc.previo[0] + f[1] * esc.previo[1] + f[2] * esc.previo[2] > QUIETO : false;
  const sinMover = esc.prevPos ? Math.hypot(pos[0] - esc.prevPos[0], pos[1] - esc.prevPos[1], pos[2] - esc.prevPos[2]) < 0.003 : false;
  if (!(sinGiro && sinMover)) esc.quietoDesde = t;
  esc.previo = f; esc.prevPos = pos;
  const { g, w, h } = prepararLienzo($('#e-lienzo'));
  if (!esc.hab) return;
  if (esc.esperandoPunto) {                               // segundo punto: empieza solo al separarse 80 cm
    const [x0, z0] = esc.esperandoPunto;
    const d = Math.hypot(pos[0] - x0, pos[2] - z0);
    $('#e-cuenta').textContent = `Te has movido ${d.toFixed(1).replace('.', ',')} m de 0,8`;
    if (d >= 0.8) { esc.esperandoPunto = null; empezarPunto(esc.hab, esc.punto + 1); if (navigator.vibrate) navigator.vibrate([40, 60, 40]); }
    pintarMapa(f);
    return;
  }
  const [lon, lat] = lonLat(f);
  const mias = celdasDe(lon, lat);
  const nuevas = mias.filter((k) => !esc.cubierto[k]).length / mias.length;
  const quieto = t - esc.quietoDesde > QUIETO_MS;
  // Foto automática: quieto, mirando algo nuevo y sin otra foto en proceso
  if (quieto && nuevas >= NUEVO && !esc.perdido && !esc.ocupado && vista.camera) {
    capturar(vista, capa, mias, t);
  }
  // Centro: punto y, si hay algo nuevo delante, anillo que se llena mientras está quieto
  g.beginPath(); g.arc(w / 2, h / 2, 6, 0, 7); g.fillStyle = '#e4572e'; g.fill();
  if (nuevas >= NUEVO && !esc.ocupado) {
    const prog = Math.min(1, (t - esc.quietoDesde) / QUIETO_MS);
    g.beginPath(); g.arc(w / 2, h / 2, 22, -Math.PI / 2, -Math.PI / 2 + prog * 2 * Math.PI);
    g.strokeStyle = '#5bb98c'; g.lineWidth = 5; g.stroke();
  }
  guiar(g, w, h, f, lon, lat, nuevas);
  pintarMapa(f);
}

// Flecha hacia lo que falta (la celda pendiente más cercana a donde se mira)
function guiar(g, w, h, f, lon, lat, nuevas) {
  if (esc.perdido) return;
  if (nuevas >= NUEVO) { $('#e-pista').textContent = 'quieto un momento…'; return; }
  let mejor = null;
  for (const k of necesarias) {
    if (esc.cubierto[k]) continue;
    const i = k % N_LON; const j = Math.floor(k / N_LON);
    const lo = ((i + 0.5) * CELDA - 180) * Math.PI / 180; const la = (90 - (j + 0.5) * CELDA) * Math.PI / 180;
    const d = [Math.cos(la) * Math.sin(lo), Math.sin(la), -Math.cos(la) * Math.cos(lo)];
    const c = d[0] * f[0] + d[1] * f[1] + d[2] * f[2];
    if (!mejor || c > mejor.c) mejor = { c, lo: lo * 180 / Math.PI, la: la * 180 / Math.PI };
  }
  if (!mejor) { $('#e-pista').textContent = 'todo visto'; return; }
  let dLon = mejor.lo - lon; dLon = ((dLon + 540) % 360) - 180;
  const dLat = mejor.la - lat;
  const a = Math.atan2(-dLat, dLon);
  const r = Math.min(w, h) * 0.2;
  g.save(); g.translate(w / 2 + Math.cos(a) * r, h / 2 + Math.sin(a) * r); g.rotate(a);
  g.beginPath(); g.moveTo(34, 0); g.lineTo(-14, -26); g.lineTo(-4, 0); g.lineTo(-14, 26); g.closePath();
  g.fillStyle = 'rgba(255,255,255,.92)'; g.fill(); g.restore();
  $('#e-pista').textContent = Math.abs(dLon) > Math.abs(dLat) ? (dLon > 0 ? 'gira a la derecha →' : '← gira a la izquierda')
    : (dLat > 0 ? 'más arriba ↑' : 'más abajo ↓');
}

function capturar(vista, capa, mias, t) {
  const gl = esc.gl; const cam = vista.camera;
  const tex = esc.binding.getCameraImage(cam);
  const w = cam.width; const h = cam.height;
  gl.bindFramebuffer(gl.FRAMEBUFFER, esc.fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
  const px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
  gl.bindFramebuffer(gl.FRAMEBUFFER, capa.framebuffer);
  for (const k of mias) esc.cubierto[k] = 1;
  esc.total++;
  const meta = {
    levantamiento: esc.nombre, fichero: `${esc.idEscaneo}-${String(esc.total).padStart(4, '0')}.jpg`, escaneo: esc.idEscaneo,
    habitacion: esc.hab, punto: esc.punto, n: esc.total, hora: Date.now(), ancho: w, alto: h,
    vista: Array.from(vista.transform.matrix), proyeccion: Array.from(vista.projectionMatrix),
  };
  esc.fotosPunto.push(meta);
  esc.ocupado = true;
  esc.quietoDesde = t;
  if (navigator.vibrate) navigator.vibrate(25);
  trabajador.postMessage({ tipo: 'foto', px: px.buffer, w, h, meta }, [px.buffer]);
  contar();
}

function pintarMapa(f) {
  const { g, w, h } = prepararLienzo($('#e-mapa'));
  if (!esc.hab) return;
  if (esc.panoBmp) g.drawImage(esc.panoBmp, 0, 0, w, h); else { g.fillStyle = '#2a2d33'; g.fillRect(0, 0, w, h); }
  const yTop = ((90 - LAT_MAX) / 180) * h; const yBot = ((90 - LAT_MIN) / 180) * h;
  g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(0, 0, w, yTop); g.fillRect(0, yBot, w, h - yBot);
  const [lon, lat] = lonLat(f);
  const x = ((lon + 180) / 360) * w; const y = ((90 - lat) / 180) * h;
  g.strokeStyle = '#e4572e'; g.lineWidth = 2;
  g.strokeRect(x - (MEDIO_ANCHO / 360) * w, y - (MEDIO_ALTO / 180) * h, (2 * MEDIO_ANCHO / 360) * w, (2 * MEDIO_ALTO / 180) * h);
}

$('#e-punto').onclick = () => {
  if (!esc.hab || !esc.fotosPunto.length) return;
  const m = esc.fotosPunto.map((x) => [x.vista[12], x.vista[14]]);
  esc.esperandoPunto = [m.reduce((a, b) => a + b[0], 0) / m.length, m.reduce((a, b) => a + b[1], 0) / m.length];
  $('#e-pista').textContent = '';
  $('#e-estado').textContent = `${esc.hab}: muévete 1 o 2 m a otro sitio de la habitación. Empezará solo.`;
};
$('#e-habitacion').onclick = () => { esc.esperandoPunto = null; esc.hab = null; elegirHabitacion(); contar(); };
$('#e-terminar').onclick = async () => {
  if (esc.sesion) await esc.sesion.end().catch(() => {});
  esc.sesion = null; esc.hab = null;
  mostrar('inicio');
  await new Promise((ok) => setTimeout(ok, 800));
  await subirPendientes();
  const n = await pintarPendientes();
  alert(n ? `Escaneo guardado: ${esc.total} fotos. Quedan ${n} por subir; se subirán solas cuando haya conexión con el PC.`
    : `Escaneo terminado: ${esc.total} fotos, todas en el PC.`);
};
pintarPendientes();
