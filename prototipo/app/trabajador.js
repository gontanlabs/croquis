'use strict';
// Trabajo pesado del escaneo, fuera de la pantalla: dar la vuelta a la foto, pasarla a JPEG y coserla en la
// panorámica. Así la cámara y los avisos no se congelan al hacer cada foto.

const PANO_W = 720; const PANO_H = 360;
let pano = null; let peso = null;

function reiniciar() {
  pano = new Uint8ClampedArray(PANO_W * PANO_H * 4);
  for (let k = 0; k < PANO_W * PANO_H; k++) { pano[4 * k] = 42; pano[4 * k + 1] = 45; pano[4 * k + 2] = 51; pano[4 * k + 3] = 255; }
  peso = new Float32Array(PANO_W * PANO_H);
}
reiniciar();

self.onmessage = async (e) => {
  const m = e.data;
  if (m.tipo === 'reiniciar') { reiniciar(); enviarPano(); return; }
  if (m.tipo !== 'foto') return;
  const { w, h, meta } = m;
  const px = new Uint8ClampedArray(m.px);
  // Filas de arriba abajo (readPixels las da de abajo arriba)
  const img = new ImageData(w, h);
  const fila = w * 4;
  for (let y = 0; y < h; y++) img.data.set(px.subarray((h - 1 - y) * fila, (h - y) * fila), y * fila);
  const lienzo = new OffscreenCanvas(w, h);
  lienzo.getContext('2d').putImageData(img, 0, 0);
  const jpeg = await lienzo.convertToBlob({ type: 'image/jpeg', quality: 0.88 });
  coser(lienzo, meta);
  self.postMessage({ tipo: 'foto', jpeg, meta });
  enviarPano();
};

function enviarPano() {
  const c = new OffscreenCanvas(PANO_W, PANO_H);
  c.getContext('2d').putImageData(new ImageData(pano.slice(), PANO_W, PANO_H), 0, 0);
  const bmp = c.transferToImageBitmap();
  self.postMessage({ tipo: 'pano', bmp }, [bmp]);
}

function coser(lienzo, meta) {
  const pw = 120; const ph = Math.round((pw * meta.alto) / meta.ancho);
  const pc = new OffscreenCanvas(pw, ph); const g = pc.getContext('2d');
  g.drawImage(lienzo, 0, 0, pw, ph);
  const src = g.getImageData(0, 0, pw, ph).data;
  const M = meta.vista; const P = meta.proyeccion;
  for (let j = 0; j < PANO_H; j++) {
    const lat = Math.PI / 2 - ((j + 0.5) / PANO_H) * Math.PI;
    const cl = Math.cos(lat); const sl = Math.sin(lat);
    for (let i = 0; i < PANO_W; i++) {
      const lon = ((i + 0.5) / PANO_W) * 2 * Math.PI - Math.PI;
      const dx = cl * Math.sin(lon); const dy = sl; const dz = -cl * Math.cos(lon);
      const cx = M[0] * dx + M[1] * dy + M[2] * dz;
      const cy = M[4] * dx + M[5] * dy + M[6] * dz;
      const cz = M[8] * dx + M[9] * dy + M[10] * dz;
      if (cz > -1e-3) continue;
      const nx = (P[0] * cx + P[8] * cz) / -cz; const ny = (P[5] * cy + P[9] * cz) / -cz;
      if (nx <= -1 || nx >= 1 || ny <= -1 || ny >= 1) continue;
      const pe = (1 - nx * nx) * (1 - ny * ny);
      const k = j * PANO_W + i;
      if (pe <= peso[k]) continue;
      peso[k] = pe;
      const u = Math.floor((nx * 0.5 + 0.5) * (pw - 1)); const v = Math.floor((1 - (ny * 0.5 + 0.5)) * (ph - 1));
      const a = (v * pw + u) * 4; const b = k * 4;
      pano[b] = src[a]; pano[b + 1] = src[a + 1]; pano[b + 2] = src[a + 2];
    }
  }
}
