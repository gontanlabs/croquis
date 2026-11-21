'use strict';
// Croquis: recorrido (cámara en realidad aumentada o dibujo a mano), medición guiada y planos.
// Toda la geometría en metros, en planta (x, y). La cámara: y = -z del espacio de WebXR.

const $ = (s) => document.querySelector(s);
// Los errores del móvil, al registro del PC
function registrar(que, detalle) {
  fetch('/api/registro', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ que, detalle: String(detalle && detalle.stack || detalle), agente: navigator.userAgent }) }).catch(() => {});
}
window.addEventListener('error', (e) => registrar('error', e.error || e.message));
window.addEventListener('unhandledrejection', (e) => registrar('promesa', e.reason));
const NOMBRES = ['Salón', 'Comedor', 'Cocina', 'Dormitorio', 'Baño', 'Aseo', 'Pasillo', 'Recibidor', 'Terraza', 'Otra'];

const estado = {
  captura: { nombre: 'Mi casa', estancias: [], puertas: [], ventanas: [] },
  actual: null,          // estancia que se está recorriendo
  marcando: null,        // {tipo: 'puerta'|'ventana', puntos: []}
  ultimo: null,          // último punto del suelo bajo la cruz (cámara)
  yo: null,              // posición del móvil en planta (cámara)
  modoAR: false,
  datos: null, info: null, indice: 0, modoMedida: 'laser',
};

function mostrar(id) {
  document.querySelectorAll('.pantalla').forEach((p) => p.classList.toggle('activa', p.id === id));
  if (id === 'medir') requestAnimationFrame(dibujarPlano);
  if (id === 'recorrido') requestAnimationFrame(dibujarRecorrido);
}

function guardarLocal() {
  try { localStorage.setItem('croquis-captura', JSON.stringify(estado.captura)); } catch (e) { /* sin almacenamiento */ }
}

async function api(ruta, cuerpo) {
  $('#ocupado').hidden = false;
  try {
    const r = await fetch(ruta, cuerpo === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cuerpo),
    });
    const j = await r.json();
    if (j && j.error) throw new Error(j.error);
    return j;
  } finally { $('#ocupado').hidden = true; }
}

// ------------------------------------------------------------------------------------------------------------
// Inicio
// ------------------------------------------------------------------------------------------------------------
async function inicio() {
  if (!(navigator.xr && await navigator.xr.isSessionSupported('immersive-ar').catch(() => false))) {
    $('#b-ar').disabled = true;
    $('#aviso-ar').textContent = 'Este móvil o navegador no permite la cámara en realidad aumentada: dibuja el croquis a mano.';
  }
  try {
    const lista = await fetch('/api/levantamientos').then((r) => r.json());
    if (lista.length) {
      $('#seguir').innerHTML = '<p class="nota">Seguir midiendo:</p>';
      for (const n of lista) {
        const b = document.createElement('button');
        b.textContent = n;
        b.onclick = async () => {
          const d = await api('/api/datos?nombre=' + encodeURIComponent(n));
          if (d) empezarMedir(d, await api('/api/tareas', { datos: d }));
        };
        $('#seguir').appendChild(b);
      }
    }
  } catch (e) { /* sin servidor todavía */ }
}

$('#b-ar').onclick = () => { estado.captura.nombre = $('#nombre').value.trim() || 'Mi casa'; iniciarAR(); };
$('#b-dibujar').onclick = () => {
  estado.captura.nombre = $('#nombre').value.trim() || 'Mi casa';
  estado.modoAR = false;
  $('#recorrido').classList.remove('ar');
  $('#cruz').hidden = true;
  mostrar('recorrido');
  pedirEstancia();
};

// ------------------------------------------------------------------------------------------------------------
// Recorrido: estancias, puertas y ventanas
// ------------------------------------------------------------------------------------------------------------
function decir(t) { $('#estado').textContent = t; }

function pedirEstancia() {
  const chips = $('#chips');
  chips.innerHTML = '';
  for (const n of NOMBRES) {
    const b = document.createElement('button');
    b.textContent = n;
    b.onclick = () => nuevaEstancia(n === 'Otra' ? (prompt('Nombre de la estancia') || 'Estancia') : n);
    chips.appendChild(b);
  }
  decir('¿Qué estancia vas a recorrer?');
}

function nombreUnico(base) {
  const usados = estado.captura.estancias.map((e) => e.nombre);
  let n = base.toUpperCase(); let k = 2;
  while (usados.includes(n)) n = `${base.toUpperCase()} ${k++}`;
  return n;
}

function nuevaEstancia(nombre) {
  $('#chips').innerHTML = '';
  estado.actual = { nombre: nombreUnico(nombre), puntos: [] };
  estado.captura.estancias.push(estado.actual);
  decir(`${estado.actual.nombre}: ${estado.modoAR ? 'apunta a cada esquina del suelo y pulsa «Esquina»' : 'toca cada esquina'}, dando la vuelta.`);
  dibujarRecorrido();
}

function anadirPunto(p) {
  if (!p) { decir('No veo el suelo: mueve el móvil despacio hasta que la cruz se ponga blanca.'); return; }
  if (estado.marcando) {
    estado.marcando.puntos.push(p);
    const faltan = 2 - estado.marcando.puntos.length;
    if (faltan > 0) decir(`${estado.marcando.tipo === 'puerta' ? 'Puerta' : 'Ventana'}: ahora la otra jamba.`);
    else {
      const lista = estado.marcando.tipo === 'puerta' ? estado.captura.puertas : estado.captura.ventanas;
      lista.push({ puntos: estado.marcando.puntos });
      decir(`${estado.marcando.tipo === 'puerta' ? 'Puerta' : 'Ventana'} ${lista.length} apuntada.`);
      estado.marcando = null;
    }
  } else if (estado.actual) {
    estado.actual.puntos.push(p);
    decir(`${estado.actual.nombre}: esquina ${estado.actual.puntos.length}.`);
  } else {
    pedirEstancia();
    return;
  }
  if (navigator.vibrate) navigator.vibrate(30);
  guardarLocal();
  dibujarRecorrido();
}

$('#b-esquina').onclick = () => anadirPunto(estado.modoAR ? estado.ultimo : null);
$('#b-cerrar').onclick = () => {
  if (estado.actual && estado.actual.puntos.length < 3) { decir('Una estancia necesita al menos tres esquinas.'); return; }
  estado.actual = null;
  pedirEstancia();
  dibujarRecorrido();
};
function marcar(tipo) {
  estado.marcando = { tipo, puntos: [] };
  decir(tipo === 'puerta'
    ? `Puerta: ${estado.modoAR ? 'apunta al suelo junto a una jamba y pulsa «Esquina»' : 'toca una jamba'}.`
    : `Ventana: ${estado.modoAR ? 'apunta al suelo, pegado a la pared, bajo un borde del hueco, y pulsa «Esquina»' : 'toca un borde del hueco'}.`);
}
$('#b-puerta').onclick = () => marcar('puerta');
$('#b-ventana').onclick = () => marcar('ventana');
$('#b-deshacer').onclick = () => {
  if (estado.marcando && estado.marcando.puntos.length) estado.marcando.puntos.pop();
  else if (estado.marcando) estado.marcando = null;
  else if (estado.actual && estado.actual.puntos.length) estado.actual.puntos.pop();
  else if (estado.actual) { estado.captura.estancias.pop(); estado.actual = null; pedirEstancia(); }
  guardarLocal();
  dibujarRecorrido();
};
$('#b-terminar').onclick = async () => {
  const c = estado.captura;
  c.estancias = c.estancias.filter((e) => e.puntos.length >= 3);
  if (!c.estancias.length) { decir('Todavía no hay ninguna estancia cerrada.'); return; }
  if (estado.sesion) await estado.sesion.end().catch(() => {});
  try {
    const r = await api('/api/crear', { captura: c });
    empezarMedir(r.datos, r);
  } catch (e) { alert('No se pudo crear el levantamiento: ' + e.message); }
};

// Dibujo a mano: un toque es una esquina (o una jamba)
const lienzo = $('#lienzo');
const vista = { escala: 40, ox: 0, oy: 0 };       // píxeles por metro y origen
lienzo.addEventListener('pointerdown', (e) => {
  if (estado.modoAR) return;
  const r = lienzo.getBoundingClientRect();
  const x = (e.clientX - r.left - vista.ox) / vista.escala;
  const y = -(e.clientY - r.top - vista.oy) / vista.escala;
  anadirPunto([Math.round(x * 20) / 20, Math.round(y * 20) / 20]);
});

function prepararLienzo(c) {
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth; const h = c.clientHeight;
  if (c.width !== w * dpr || c.height !== h * dpr) { c.width = w * dpr; c.height = h * dpr; }
  const g = c.getContext('2d');
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, w, h);
  return { g, w, h };
}

function encuadre(puntos, w, h, margen = 30) {
  if (!puntos.length) return { escala: 40, ox: w / 2, oy: h / 2 };
  const xs = puntos.map((p) => p[0]); const ys = puntos.map((p) => p[1]);
  const x0 = Math.min(...xs); const x1 = Math.max(...xs); const y0 = Math.min(...ys); const y1 = Math.max(...ys);
  const escala = Math.min((w - 2 * margen) / Math.max(x1 - x0, 1), (h - 2 * margen) / Math.max(y1 - y0, 1), 120);
  return { escala, ox: w / 2 - escala * (x0 + x1) / 2, oy: h / 2 + escala * (y0 + y1) / 2 };
}

function dibujarRecorrido() {
  const { g, w, h } = prepararLienzo(lienzo);
  const c = estado.captura;
  const todos = c.estancias.flatMap((e) => e.puntos).concat(estado.yo ? [estado.yo] : []);
  if (estado.modoAR || todos.length > 2) Object.assign(vista, encuadre(todos, w, h, 16));
  else Object.assign(vista, { escala: 40, ox: w / 2, oy: h / 2 });
  const P = (p) => [vista.ox + p[0] * vista.escala, vista.oy - p[1] * vista.escala];
  if (!estado.modoAR) {                                  // cuadrícula de 1 m
    g.strokeStyle = '#2a2d33'; g.lineWidth = 1;
    for (let x = vista.ox % vista.escala; x < w; x += vista.escala) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
    for (let y = vista.oy % vista.escala; y < h; y += vista.escala) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
  }
  for (const e of c.estancias) {
    if (!e.puntos.length) continue;
    g.beginPath();
    e.puntos.forEach((p, i) => (i ? g.lineTo(...P(p)) : g.moveTo(...P(p))));
    if (e !== estado.actual) g.closePath();
    g.strokeStyle = e === estado.actual ? '#e4572e' : '#eceae4'; g.lineWidth = 2; g.stroke();
    e.puntos.forEach((p) => { g.fillStyle = g.strokeStyle; g.beginPath(); g.arc(...P(p), 3, 0, 7); g.fill(); });
  }
  for (const [lista, color] of [[c.puertas, '#5bb98c'], [c.ventanas, '#6fb3ff']]) {
    for (const o of lista) { g.strokeStyle = color; g.lineWidth = 5; g.beginPath(); g.moveTo(...P(o.puntos[0])); g.lineTo(...P(o.puntos[1])); g.stroke(); }
  }
  if (estado.marcando) estado.marcando.puntos.forEach((p) => { g.fillStyle = '#5bb98c'; g.beginPath(); g.arc(...P(p), 5, 0, 7); g.fill(); });
  if (estado.ultimo) { g.strokeStyle = '#fff'; g.lineWidth = 1.5; g.beginPath(); g.arc(...P(estado.ultimo), 6, 0, 7); g.stroke(); }
  if (estado.yo) { g.fillStyle = '#6fb3ff'; g.beginPath(); g.arc(...P(estado.yo), 4, 0, 7); g.fill(); }
}

// ------------------------------------------------------------------------------------------------------------
// Cámara: WebXR con detección del suelo (hit-test). Sin dibujo 3D: la cruz es un elemento de la página.
// ------------------------------------------------------------------------------------------------------------
async function iniciarAR() {
  try {
    const sesion = await navigator.xr.requestSession('immersive-ar', {
      requiredFeatures: ['hit-test'], optionalFeatures: ['dom-overlay'], domOverlay: { root: $('#recorrido') },
    });
    estado.sesion = sesion; estado.modoAR = true;
    $('#recorrido').classList.add('ar');
    $('#cruz').hidden = false;
    mostrar('recorrido');
    $('#recorrido').addEventListener('beforexrselect', (e) => e.preventDefault());
    const gl = document.createElement('canvas').getContext('webgl', { xrCompatible: true });
    sesion.updateRenderState({ baseLayer: new XRWebGLLayer(sesion, gl) });
    const ref = await sesion.requestReferenceSpace('local');
    const viewer = await sesion.requestReferenceSpace('viewer');
    const fuente = await sesion.requestHitTestSource({ space: viewer });
    sesion.addEventListener('end', () => { estado.modoAR = false; estado.sesion = null; $('#cruz').hidden = true; });
    let n = 0;
    const cuadro = (t, frame) => {
      sesion.requestAnimationFrame(cuadro);
      const capa = sesion.renderState.baseLayer;
      gl.bindFramebuffer(gl.FRAMEBUFFER, capa.framebuffer);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      const r = frame.getHitTestResults(fuente);
      if (r.length) {
        const p = r[0].getPose(ref).transform.position;
        estado.ultimo = [p.x, -p.z];
      } else estado.ultimo = null;
      $('#cruz').classList.toggle('sin-suelo', !estado.ultimo);
      const yo = frame.getViewerPose(ref);
      if (yo) estado.yo = [yo.transform.position.x, -yo.transform.position.z];
      if (++n % 6 === 0) dibujarRecorrido();
    };
    sesion.requestAnimationFrame(cuadro);
    pedirEstancia();
  } catch (e) {
    alert('No se pudo abrir la cámara en realidad aumentada: ' + e.message + '\nPuedes dibujar el croquis a mano.');
  }
}

// ------------------------------------------------------------------------------------------------------------
// Medición guiada
// ------------------------------------------------------------------------------------------------------------
function empezarMedir(datos, info) {
  estado.datos = datos; estado.info = info; estado.indice = 0;
  mostrar('medir');
  pintarTarea();
}

function tareaActual() {
  const t = estado.info.tareas;
  return t.length ? t[estado.indice % t.length] : null;
}

function pintarTarea() {
  const info = estado.info;
  const t = tareaActual();
  $('#cuenta').textContent = `${info.hechas} de ${info.total} medidas` + (t && t.id.startsWith('extra') ? ' · extra' : '');
  $('#margen').textContent = `estancias ±${String(info.resumen.estancias_mm).replace('.', ',')} mm · casa ±${String(info.resumen.casa_mm).replace('.', ',')} mm`;
  const s = info.sospechosas || [];
  $('#sospechas').hidden = !s.length;
  $('#sospechas').innerHTML = s.map((x) => x.texto).join('<br>');
  if (!t) {
    $('#t-texto').textContent = 'No hace falta medir nada más.';
    $('#t-ayuda').textContent = 'Saca los planos.';
    $('#t-entrada').hidden = true; $('#t-opciones').innerHTML = '';
    $('#b-guardar').disabled = true; $('#b-saltar').disabled = true;
    dibujarPlano();
    return;
  }
  $('#t-texto').textContent = t.texto;
  $('#t-ayuda').textContent = t.ayuda || '';
  $('#b-guardar').disabled = false; $('#b-saltar').disabled = false;
  const opciones = $('#t-opciones');
  opciones.innerHTML = '';
  if (t.tipo === 'opcion') {
    $('#t-entrada').hidden = true;
    $('#b-guardar').disabled = true;
    t.opciones.forEach((o, i) => {
      const b = document.createElement('button');
      b.textContent = o;
      b.onclick = () => responder(t.id.startsWith('bisagra') ? i : o);
      opciones.appendChild(b);
    });
  } else {
    $('#t-entrada').hidden = false;
    estado.modoMedida = t.modo || 'laser';
    document.querySelectorAll('.modo').forEach((b) => b.classList.toggle('elegido', b.dataset.modo === estado.modoMedida));
    $('#valor').value = '';
    $('#valor').focus();
  }
  dibujarPlano();
}

document.querySelectorAll('.modo').forEach((b) => (b.onclick = () => {
  estado.modoMedida = b.dataset.modo;
  document.querySelectorAll('.modo').forEach((x) => x.classList.toggle('elegido', x === b));
}));

async function responder(valor) {
  const t = tareaActual();
  try {
    const r = await api('/api/responder', { datos: estado.datos, id: t.id, valor, modo: estado.modoMedida });
    estado.datos = r.datos; estado.info = r; estado.indice = 0;
    pintarTarea();
  } catch (e) { alert(e.message); }
}

$('#b-guardar').onclick = () => {
  const v = parseFloat($('#valor').value.replace(',', '.'));
  if (!(v > 0 && v < 50)) { $('#valor').focus(); return; }
  responder(v);
};
$('#valor').addEventListener('keydown', (e) => { if (e.key === 'Enter') $('#b-guardar').click(); });
$('#b-saltar').onclick = () => { estado.indice++; pintarTarea(); };
$('#b-planos').onclick = async () => {
  if (estado.info.tareas.length && !estado.info.tareas[0].id.startsWith('extra')
      && !confirm('Faltan medidas: los planos saldrán con lo que vio la cámara en lo que falta. ¿Seguir?')) return;
  try {
    const r = await api('/api/planos', { datos: estado.datos });
    $('#pdfs').innerHTML = r.pdfs.map((u) => `<a href="${u}" target="_blank">${decodeURIComponent(u.split('/').pop())}</a>`).join('');
  } catch (e) { alert('No se pudieron sacar los planos: ' + e.message); }
};

function dibujarPlano() {
  const c = $('#plano');
  if (!estado.info || !c.clientWidth) return;
  const { g, w, h } = prepararLienzo(c);
  const info = estado.info;
  const pts = info.puntos;
  const todos = Object.values(pts);
  const v = encuadre(todos, w, h, 34);
  const P = (p) => [v.ox + p[0] * v.escala, v.oy - p[1] * v.escala];
  const t = tareaActual();
  for (const [nom, esq] of Object.entries(info.estancias)) {
    const activa = t && t.estancia === nom;
    g.beginPath();
    esq.forEach((n, i) => (i ? g.lineTo(...P(pts[n])) : g.moveTo(...P(pts[n]))));
    g.closePath();
    g.fillStyle = activa ? 'rgba(228,87,46,.10)' : 'rgba(255,255,255,.03)'; g.fill();
    g.strokeStyle = activa ? '#eceae4' : '#7d8088'; g.lineWidth = activa ? 2 : 1.2; g.stroke();
    const cx = esq.reduce((s, n) => s + pts[n][0], 0) / esq.length;
    const cy = esq.reduce((s, n) => s + pts[n][1], 0) / esq.length;
    g.fillStyle = activa ? '#eceae4' : '#7d8088'; g.font = '11px system-ui'; g.textAlign = 'center';
    g.fillText(nom, ...P([cx, cy]));
    if (activa) {
      g.font = '12px system-ui';
      esq.forEach((n) => { const [x, y] = P(pts[n]); g.fillStyle = '#eceae4'; g.fillText(n, x + (x < w / 2 ? -12 : 12), y + (y < h / 2 ? -6 : 14)); });
    }
  }
  for (const p of info.puertas) {
    g.strokeStyle = '#5bb98c'; g.lineWidth = 4; g.beginPath(); g.moveTo(...P(p.jambas[0])); g.lineTo(...P(p.jambas[1])); g.stroke();
  }
  if (t && t.puntos && t.puntos.length) {
    const q = t.puntos.map((n) => pts[n]).filter(Boolean);
    g.strokeStyle = '#e4572e'; g.fillStyle = '#e4572e'; g.lineWidth = 4;
    if (q.length === 2) { g.beginPath(); g.moveTo(...P(q[0])); g.lineTo(...P(q[1])); g.stroke(); }
    q.forEach((p) => { g.beginPath(); g.arc(...P(p), 6, 0, 7); g.fill(); });
  }
}
window.addEventListener('resize', () => { dibujarPlano(); dibujarRecorrido(); });

// ------------------------------------------------------------------------------------------------------------
// Giro en el centro: la profundidad de la cámara, para sacar las paredes aunque haya muebles
// ------------------------------------------------------------------------------------------------------------
function invertir(m) {          // inversa de una matriz 4×4 (por columnas)
  const a = m; const inv = new Float32Array(16);
  inv[0] = a[5] * a[10] * a[15] - a[5] * a[11] * a[14] - a[9] * a[6] * a[15] + a[9] * a[7] * a[14] + a[13] * a[6] * a[11] - a[13] * a[7] * a[10];
  inv[4] = -a[4] * a[10] * a[15] + a[4] * a[11] * a[14] + a[8] * a[6] * a[15] - a[8] * a[7] * a[14] - a[12] * a[6] * a[11] + a[12] * a[7] * a[10];
  inv[8] = a[4] * a[9] * a[15] - a[4] * a[11] * a[13] - a[8] * a[5] * a[15] + a[8] * a[7] * a[13] + a[12] * a[5] * a[11] - a[12] * a[7] * a[9];
  inv[12] = -a[4] * a[9] * a[14] + a[4] * a[10] * a[13] + a[8] * a[5] * a[14] - a[8] * a[6] * a[13] - a[12] * a[5] * a[10] + a[12] * a[6] * a[9];
  inv[1] = -a[1] * a[10] * a[15] + a[1] * a[11] * a[14] + a[9] * a[2] * a[15] - a[9] * a[3] * a[14] - a[13] * a[2] * a[11] + a[13] * a[3] * a[10];
  inv[5] = a[0] * a[10] * a[15] - a[0] * a[11] * a[14] - a[8] * a[2] * a[15] + a[8] * a[3] * a[14] + a[12] * a[2] * a[11] - a[12] * a[3] * a[10];
  inv[9] = -a[0] * a[9] * a[15] + a[0] * a[11] * a[13] + a[8] * a[1] * a[15] - a[8] * a[3] * a[13] - a[12] * a[1] * a[11] + a[12] * a[3] * a[9];
  inv[13] = a[0] * a[9] * a[14] - a[0] * a[10] * a[13] - a[8] * a[1] * a[14] + a[8] * a[2] * a[13] + a[12] * a[1] * a[10] - a[12] * a[2] * a[9];
  inv[2] = a[1] * a[6] * a[15] - a[1] * a[7] * a[14] - a[5] * a[2] * a[15] + a[5] * a[3] * a[14] + a[13] * a[2] * a[7] - a[13] * a[3] * a[6];
  inv[6] = -a[0] * a[6] * a[15] + a[0] * a[7] * a[14] + a[4] * a[2] * a[15] - a[4] * a[3] * a[14] - a[12] * a[2] * a[7] + a[12] * a[3] * a[6];
  inv[10] = a[0] * a[5] * a[15] - a[0] * a[7] * a[13] - a[4] * a[1] * a[15] + a[4] * a[3] * a[13] + a[12] * a[1] * a[7] - a[12] * a[3] * a[5];
  inv[14] = -a[0] * a[5] * a[14] + a[0] * a[6] * a[13] + a[4] * a[1] * a[14] - a[4] * a[2] * a[13] - a[12] * a[1] * a[6] + a[12] * a[2] * a[5];
  inv[3] = -a[1] * a[6] * a[11] + a[1] * a[7] * a[10] + a[5] * a[2] * a[11] - a[5] * a[3] * a[10] - a[9] * a[2] * a[7] + a[9] * a[3] * a[6];
  inv[7] = a[0] * a[6] * a[11] - a[0] * a[7] * a[10] - a[4] * a[2] * a[11] + a[4] * a[3] * a[10] + a[8] * a[2] * a[7] - a[8] * a[3] * a[6];
  inv[11] = -a[0] * a[5] * a[11] + a[0] * a[7] * a[9] + a[4] * a[1] * a[11] - a[4] * a[3] * a[9] - a[8] * a[1] * a[7] + a[8] * a[3] * a[5];
  inv[15] = a[0] * a[5] * a[10] - a[0] * a[6] * a[9] - a[4] * a[1] * a[10] + a[4] * a[2] * a[9] + a[8] * a[1] * a[6] - a[8] * a[2] * a[5];
  let det = a[0] * inv[0] + a[1] * inv[4] + a[2] * inv[8] + a[3] * inv[12];
  det = 1 / det;
  for (let i = 0; i < 16; i++) inv[i] *= det;
  return inv;
}
function porMatriz(m, x, y, z, w) {
  return [m[0] * x + m[4] * y + m[8] * z + m[12] * w, m[1] * x + m[5] * y + m[9] * z + m[13] * w,
    m[2] * x + m[6] * y + m[10] * z + m[14] * w, m[3] * x + m[7] * y + m[11] * z + m[15] * w];
}

const giro = { estancia: null, grabando: false, puntos: [], cubierto: new Array(36).fill(false), suelo: null, centro: [], sesion: null };

$('#b-giro').onclick = async () => {
  giro.n = (giro.n || 0) + 1;                 // sin preguntar: un aviso gastaría el toque que abre la cámara
  giro.estancia = `Habitación ${giro.n}`;
  estado.captura.nombre = $('#nombre').value.trim() || 'Mi casa';
  Object.assign(giro, { grabando: false, puntos: [], cubierto: new Array(36).fill(false), suelo: null, centro: [] });
  try {
    let sesion = null; const fallos = [];
    for (const formatos of [['luminance-alpha', 'float32'], ['float32', 'luminance-alpha', 'unsigned-short'], ['unsigned-short']]) {
      try {
        sesion = await navigator.xr.requestSession('immersive-ar', {
          requiredFeatures: ['depth-sensing', 'hit-test'], optionalFeatures: ['dom-overlay'], domOverlay: { root: $('#giro') },
          depthSensing: { usagePreference: ['cpu-optimized'], dataFormatPreference: formatos },
        });
        registrar('giro-ok', JSON.stringify({ formatos, uso: sesion.depthUsage, formato: sesion.depthDataFormat }));
        break;
      } catch (err) { fallos.push(`${formatos.join('/')}: ${err.name} ${err.message}`); }
    }
    if (!sesion) throw new Error(fallos.join(' | '));
    giro.sesion = sesion;
    mostrar('giro');
    $('#g-estado').textContent = 'Ponte en el centro, apunta un momento al suelo y pulsa «Empezar a girar».';
    $('#giro').addEventListener('beforexrselect', (e) => e.preventDefault());
    const gl = document.createElement('canvas').getContext('webgl', { xrCompatible: true });
    sesion.updateRenderState({ baseLayer: new XRWebGLLayer(sesion, gl) });
    const ref = await sesion.requestReferenceSpace('local');
    const viewer = await sesion.requestReferenceSpace('viewer');
    const fuente = await sesion.requestHitTestSource({ space: viewer });
    let n = 0;
    const cuadro = (t, frame) => {
      if (!giro.sesion) return;
      sesion.requestAnimationFrame(cuadro);
      const capa = sesion.renderState.baseLayer;
      gl.bindFramebuffer(gl.FRAMEBUFFER, capa.framebuffer);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      const r = frame.getHitTestResults(fuente);
      if (r.length) {
        const y = r[0].getPose(ref).transform.position.y;
        if (giro.suelo === null || y < giro.suelo) giro.suelo = y;      // el suelo: lo más bajo que se ha visto
      }
      const pose = frame.getViewerPose(ref);
      if (!pose) return;
      // Comprobación: distancia al punto de la cruz según la profundidad y según el seguimiento (hit-test)
      if (!giro.grabando && ++n % 10 === 0) {
        const pv = frame.getDepthInformation(pose.views[0]);
        const dProf = pv ? pv.getDepthInMeters(0.5, 0.5) : null;
        let dSeg = null;
        if (r.length) {
          const a = r[0].getPose(ref).transform.position; const b = pose.transform.position;
          dSeg = Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
        }
        const f = (x) => (x ? x.toFixed(3).replace('.', ',') + ' m' : '—');
        $('#g-estado').textContent = `Apunta a una pared: profundidad ${f(dProf)} · seguimiento ${f(dSeg)}. Mídelo con el láser desde el móvil.`;
        if (n % 60 === 0) registrar('comprobacion', JSON.stringify({ dProf, dSeg }));
        return;
      }
      if (!giro.grabando || ++n % 8) return;
      const vista = pose.views[0];
      const prof = frame.getDepthInformation(vista);
      if (!prof) return;
      const m = vista.transform.matrix;
      const inv = invertir(vista.projectionMatrix);
      giro.centro.push([m[12], -m[14]]);
      const yaw = Math.atan2(-m[8], m[10]);                  // hacia dónde mira, en planta
      giro.cubierto[Math.floor(((yaw + Math.PI) / (2 * Math.PI)) * 36) % 36] = true;
      for (let j = 0; j < 36; j++) {
        for (let i = 0; i < 48; i++) {
          const u = (i + 0.5) / 48; const v = (j + 0.5) / 36;
          const d = prof.getDepthInMeters(u, v);
          if (!(d > 0.3 && d < 7)) continue;
          const c = porMatriz(inv, 2 * u - 1, 1 - 2 * v, -1, 1);
          const s = d / -(c[2] / c[3]);
          const p = porMatriz(m, (c[0] / c[3]) * s, (c[1] / c[3]) * s, -d, 1);
          giro.puntos.push([+p[0].toFixed(3), +(-p[2]).toFixed(3), +p[1].toFixed(3)]);
        }
      }
      const hechos = giro.cubierto.filter(Boolean).length;
      $('#g-estado').textContent = hechos < 36
        ? `Gira despacio, mirando a las paredes y al techo: ${Math.round(hechos / 36 * 100)} % de la vuelta.`
        : 'Vuelta completa. Puedes dar otra mirando más arriba, o pulsar «Terminar».';
      pintarAnillo();
    };
    sesion.requestAnimationFrame(cuadro);
    sesion.addEventListener('end', () => { giro.sesion = null; });
  } catch (e) {
    registrar('giro', e);
    alert('No se pudo abrir la cámara con profundidad: ' + e.message);
  }
};

function pintarAnillo() {
  const { g, w, h } = prepararLienzo($('#g-anillo'));
  const r = Math.min(w, h) / 2 - 10;
  giro.cubierto.forEach((ok, k) => {
    const a0 = (k / 36) * 2 * Math.PI - Math.PI / 2; const a1 = a0 + (2 * Math.PI) / 36 - 0.03;
    g.beginPath(); g.arc(w / 2, h / 2, r, a0, a1);
    g.strokeStyle = ok ? '#5bb98c' : 'rgba(255,255,255,.35)'; g.lineWidth = 12; g.stroke();
  });
}

$('#g-empezar').onclick = () => {
  giro.grabando = !giro.grabando;
  $('#g-empezar').textContent = giro.grabando ? 'Pausar' : 'Seguir girando';
};
$('#g-terminar').onclick = async () => {
  giro.grabando = false;
  if (giro.sesion) await giro.sesion.end().catch(() => {});
  giro.sesion = null;
  if (giro.puntos.length < 1000) { alert('Se han grabado muy pocos puntos: vuelve a probar girando más despacio.'); mostrar('inicio'); return; }
  const xs = giro.centro.map((c) => c[0]); const ys = giro.centro.map((c) => c[1]);
  const centro = [xs.reduce((a, b) => a + b, 0) / xs.length, ys.reduce((a, b) => a + b, 0) / ys.length];
  try {
    const r = await api('/api/barrido', { nombre: estado.captura.nombre, estancia: giro.estancia, puntos: giro.puntos, suelo: giro.suelo, centro });
    mostrarResultado(r);
  } catch (e) { alert('No se pudieron calcular las paredes: ' + e.message); mostrar('inicio'); }
};

function mostrarResultado(r) {
  mostrar('resultado');
  const e = r.esquinas;
  const lados = e.map((p, i) => Math.hypot(e[(i + 1) % e.length][0] - p[0], e[(i + 1) % e.length][1] - p[1]));
  $('#r-titulo').textContent = `${giro.estancia}: ${r.paredes.length} paredes`;
  const coma = (x, d = 2) => x.toFixed(d).replace('.', ',');
  $('#r-detalle').innerHTML = (lados.length ? `Lados: ${lados.map((l) => coma(l) + ' m').join(' · ')}<br>` : '')
    + (r.altura ? `Altura libre: ${coma(r.altura)} m<br>` : 'No he visto el techo: mira más hacia arriba al girar.<br>')
    + `Ruido de las paredes: ${r.paredes.map((p) => coma(p.rms_mm, 0)).join(' · ')} mm · ${r.usados} puntos útiles de ${r.total}`;
  requestAnimationFrame(() => {
    const { g, w, h } = prepararLienzo($('#r-plano'));
    const todos = r.muestra.concat(e);
    const v = encuadre(todos, w, h, 30);
    const P = (p) => [v.ox + p[0] * v.escala, v.oy - p[1] * v.escala];
    g.fillStyle = 'rgba(200,200,200,.45)';
    for (const p of r.muestra) { const [x, y] = P(p); g.fillRect(x, y, 2, 2); }
    g.strokeStyle = '#e4572e'; g.lineWidth = 3;
    if (e.length > 2) { g.beginPath(); e.forEach((p, i) => (i ? g.lineTo(...P(p)) : g.moveTo(...P(p)))); g.closePath(); g.stroke(); }
    g.strokeStyle = '#6fb3ff'; g.lineWidth = 1.5;
    for (const p of r.paredes) { g.beginPath(); g.moveTo(...P(p.tramo[0])); g.lineTo(...P(p.tramo[1])); g.stroke(); }
  });
}
$('#r-otra').onclick = () => mostrar('inicio');

// Lo recorrido antes de un cierre inesperado
try {
  const c = JSON.parse(localStorage.getItem('croquis-captura') || 'null');
  if (c && c.estancias && c.estancias.length) estado.captura = c;
} catch (e) { /* nada guardado */ }
inicio();
