"""Servidor local de la app de Croquis (solo en este PC: 127.0.0.1).

El móvil llega por el cable USB con `adb reverse tcp:8765 tcp:8765` y abre http://localhost:8765 (la cámara en
realidad aumentada exige una dirección segura, y localhost lo es). Cada respuesta se guarda en
`../levantamientos/<nombre>/datos.json`, para que no se pierda nada.

    python servidor.py
"""
from __future__ import annotations

import json
import re
import sys
import traceback
import unicodedata
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import levantamiento as lev

AQUI = Path(__file__).parent
APP = AQUI / 'app'
DATOS = AQUI.parent / 'levantamientos'
PUERTO = 8765


def carpeta(nombre: str) -> Path:
    s = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-') or 'vivienda'
    c = DATOS / s
    c.mkdir(parents=True, exist_ok=True)
    return c


def guardar(datos):
    c = carpeta(datos.get('nombre', 'vivienda'))
    (c / 'datos.json').write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding='utf-8')
    return c


class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(APP), **k)

    def log_message(self, fmt, *args):
        sys.stderr.write('%s\n' % (fmt % args))

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def _json(self, obj, codigo=200):
        cuerpo = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/api/datos':
            nombre = parse_qs(url.query).get('nombre', ['vivienda'])[0]
            f = carpeta(nombre) / 'datos.json'
            return self._json(json.loads(f.read_text(encoding='utf-8')) if f.exists() else None)
        if url.path == '/api/levantamientos':
            return self._json(sorted(p.parent.name for p in DATOS.glob('*/datos.json')))
        if url.path.startswith('/planos/'):
            _, _, nombre, fichero = unquote(url.path).split('/', 3)
            f = DATOS / nombre / fichero
            if f.suffix == '.pdf' and f.exists() and DATOS in f.resolve().parents:
                cuerpo = f.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/pdf')
                self.send_header('Content-Length', str(len(cuerpo)))
                self.end_headers()
                self.wfile.write(cuerpo)
                return
            return self._json({'error': 'no existe'}, 404)
        return super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        try:
            pedido = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            if url.path == '/api/crear':
                datos = lev.crear(pedido['captura'])
                guardar(datos)
                return self._json({'datos': datos, **lev.tareas(datos)})
            if url.path == '/api/tareas':
                return self._json(lev.tareas(pedido['datos']))
            if url.path == '/api/responder':
                datos = lev.responder(pedido['datos'], pedido['id'], pedido['valor'], pedido.get('modo'))
                guardar(datos)
                return self._json({'datos': datos, **lev.tareas(datos)})
            if url.path == '/api/registro':
                print('MÓVIL:', json.dumps(pedido, ensure_ascii=False), flush=True)
                return self._json({'ok': True})
            if url.path == '/api/barrido':
                import time
                from barrido import paredes
                c = carpeta(pedido.get('nombre', 'vivienda')) / 'barridos'
                c.mkdir(exist_ok=True)
                (c / f"{pedido.get('estancia', 'estancia')}-{time.strftime('%H%M%S')}.json").write_text(
                    json.dumps(pedido), encoding='utf-8')
                return self._json(paredes(pedido['puntos'], pedido.get('suelo'), pedido.get('centro', (0, 0))))
            if url.path == '/api/planos':
                datos = pedido['datos']
                c = guardar(datos)
                pdfs = lev.planos(datos, c)
                return self._json({'pdfs': [f'/planos/{c.name}/{p.name}' for p in pdfs]})
            return self._json({'error': 'no existe'}, 404)
        except Exception as e:                          # el error, a la pantalla del móvil
            traceback.print_exc()
            return self._json({'error': f'{type(e).__name__}: {e}'}, 500)


if __name__ == '__main__':
    DATOS.mkdir(exist_ok=True)
    print(f'Croquis en http://localhost:{PUERTO}')
    ThreadingHTTPServer(('127.0.0.1', PUERTO), Manejador).serve_forever()
