"""Ajuste de una vivienda entera: varias estancias unidas por sus puertas.

Datos de un levantamiento (JSON, ver `leer`):
- estancias: esquinas en orden (vuelta a la habitación), posición aproximada de cada una (croquis) y altura libre;
- medidas: distancias entre esquinas (paredes, diagonales, y de una estancia a otra a través de una puerta abierta);
- puertas: por cada lado, la pared (dos esquinas) y la distancia desde la primera esquina a cada jamba; el grosor del
  tabique en la puerta; altura, hacia dónde abre y bisagra. Las jambas de los dos lados atan las estancias entre sí;
- ventanas: pared, distancia a cada jamba, antepecho, dintel y grosor de fachada.

La red se ajusta por mínimos cuadrados (como `ajuste.Planta`, generalizado): cada medida con su margen según cómo se
tomó, las jambas sobre su pared, y la hipótesis débil de escuadra en cada esquina. «Cerrado» = todas las distancias
entre esquinas de la casa cumplen 2·sigma <= tolerancia.
"""
from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from ajuste import MARGENES, TOLERANCIA

SIGMA_LINEA = 0.0005          # la jamba está en el plano de su pared
SIGMA_ESCUADRA = math.radians(3.0)


# ---------------------------------------------------------------------------------------------------------------
# Red genérica: puntos y observaciones
# ---------------------------------------------------------------------------------------------------------------
def _dist(p):
    return float(np.hypot(p[2] - p[0], p[3] - p[1]))


def _linea(p):
    # distancia con signo del punto (p0,p1) a la recta (p2,p3)-(p4,p5)
    ax, ay, bx, by = p[2], p[3], p[4], p[5]
    return float(((bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax)) / math.hypot(bx - ax, by - ay))


def _angulo(p):
    # ángulo interior en k = (p2,p3) entre la esquina anterior (p0,p1) y la siguiente (p4,p5)
    a = (p[0] - p[2], p[1] - p[3])
    b = (p[4] - p[2], p[5] - p[3])
    return math.atan2(b[0] * a[1] - b[1] * a[0], b[0] * a[0] + b[1] * a[1]) % (2 * math.pi)


def _perp(p):
    # avance de q=(p2,p3) respecto de p=(p0,p1) a lo largo de la pared (p4,p5)-(p6,p7): 0 si la jamba va a escuadra
    ux, uy = p[6] - p[4], p[7] - p[5]
    return float(((p[2] - p[0]) * ux + (p[3] - p[1]) * uy) / math.hypot(ux, uy))


def _paralelo(p):
    # giro entre la cara (p0,p1)-(p2,p3) y la cara opuesta (p4,p5)-(p6,p7), que va en sentido contrario
    ux, uy = p[2] - p[0], p[3] - p[1]
    vx, vy = p[4] - p[6], p[5] - p[7]
    return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)


FUNCIONES = {'dist': _dist, 'linea': _linea, 'angulo': _angulo, 'perp': _perp, 'paralelo': _paralelo}
SIGMA_TABIQUE = 0.003        # un tabique tiene el mismo grueso de punta a punta (±3 mm)
MAX_TABIQUE = 0.40           # caras de dos estancias a menos de esto: las dos caras de un mismo tabique
SIGMA_JAMBA = 0.003          # la jamba atraviesa el tabique a escuadra


@dataclass
class Obs:
    tipo: str
    puntos: tuple[str, ...]
    valor: float
    sigma: float
    etiqueta: str = ''
    modo: str = ''


@dataclass
class Red:
    inicial: dict[str, tuple[float, float]]
    obs: list[Obs] = field(default_factory=list)
    fijo: tuple[str, str] | None = None     # (origen, punto sobre el eje X)

    def __post_init__(self):
        self.nombres = list(self.inicial)
        if self.fijo is None:
            self.fijo = (self.nombres[0], self.nombres[1])
        o, b = self.fijo
        self.libres = [(n, k) for n in self.nombres for k in (0, 1) if n != o and not (n == b and k == 1)]
        self.col = {nk: i for i, nk in enumerate(self.libres)}

    def x0(self):
        c = {n: np.array(v, float) for n, v in self.inicial.items()}
        o, b = c[self.fijo[0]], c[self.fijo[1]]
        ang = -math.atan2(b[1] - o[1], b[0] - o[0])
        r = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
        c = {n: r @ (v - o) for n, v in c.items()}
        return np.array([c[n][k] for n, k in self.libres])

    def puntos(self, x):
        p = {n: [0.0, 0.0] for n in self.nombres}
        for (n, k), v in zip(self.libres, x):
            p[n][k] = float(v)
        return p

    def _evaluar(self, x, obs):
        p = self.puntos(x)
        f = np.empty(len(obs))
        j = np.zeros((len(obs), len(x)))
        h = 1e-7
        for i, o in enumerate(obs):
            v = [c for n in o.puntos for c in p[n]]
            fn = FUNCIONES[o.tipo]
            f[i] = fn(v)
            for q, n in enumerate(o.puntos):
                for k in (0, 1):
                    c = self.col.get((n, k))
                    if c is None:
                        continue
                    vp, vm = list(v), list(v)
                    vp[2 * q + k] += h
                    vm[2 * q + k] -= h
                    d = fn(vp) - fn(vm)
                    if o.tipo == 'angulo':
                        d = (d + math.pi) % (2 * math.pi) - math.pi
                    j[i, c] += d / (2 * h)
        return f, j

    def _residuos(self, f, obs):
        r = np.array([o.valor for o in obs]) - f
        for i, o in enumerate(obs):
            if o.tipo == 'angulo':
                r[i] = (r[i] + math.pi) % (2 * math.pi) - math.pi
        return r

    def resolver(self):
        x = self.x0()
        sig = np.array([o.sigma for o in self.obs])
        for _ in range(60):
            f, j = self._evaluar(x, self.obs)
            dx = np.linalg.lstsq(j / sig[:, None], self._residuos(f, self.obs) / sig, rcond=None)[0]
            x = x + dx
            if np.max(np.abs(dx)) < 1e-9:
                break
        f, j = self._evaluar(x, self.obs)
        jw = j / sig[:, None]
        self.x, self.jw, self.r = x, jw, self._residuos(f, self.obs) / sig
        self.cov = np.linalg.inv(jw.T @ jw)
        return self.puntos(x)

    def grad_dist(self, a, b):
        p = self.puntos(self.x)
        u = np.array(p[b]) - np.array(p[a])
        u /= np.linalg.norm(u)
        g = np.zeros(len(self.x))
        for n, s in ((b, 1), (a, -1)):
            for k in (0, 1):
                c = self.col.get((n, k))
                if c is not None:
                    g[c] += s * u[k]
        return g

    def sospechosas(self, umbral=3.0):
        h = np.einsum('ij,jk,ik->i', self.jw, self.cov, self.jw)
        out = []
        for i, o in enumerate(self.obs):
            if o.tipo == 'angulo':
                continue
            red = 1 - h[i]
            if red > 0.05:
                w = abs(self.r[i]) / math.sqrt(red)
                if w > umbral:
                    out.append((o, w))
        return sorted(out, key=lambda t: -t[1])


# ---------------------------------------------------------------------------------------------------------------
# Vivienda
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class Vivienda:
    datos: dict

    @classmethod
    def leer(cls, ruta) -> 'Vivienda':
        return cls(json.loads(Path(ruta).read_text(encoding='utf-8')))

    # --- construcción de la red ---
    def _croquis(self):
        c = {}
        for e in self.datos['estancias'].values():
            for n in e['esquinas']:
                c[n] = tuple(e['croquis'][n])
        return c

    def _sobre_pared(self, c, pared, s):
        a, b = np.array(c[pared[0]], float), np.array(c[pared[1]], float)
        u = (b - a) / np.linalg.norm(b - a)
        return tuple(a + u * s)

    def red(self) -> Red:
        c = self._croquis()
        ini = dict(c)
        obs = []
        for m in self.datos['medidas']:
            modo = m.get('modo', 'laser')
            obs.append(Obs('dist', (m['de'], m['a']), m['valor'], MARGENES[modo], f"{m['de']}–{m['a']}", modo))
        self.jambas = {}     # (puerta, lado) -> (nombre j1, nombre j2)
        for pu in self.datos['puertas']:
            nombres_lado = []
            for i, lado in enumerate(pu['lados']):
                pared = lado['pared']
                nom = []
                for j, s in enumerate(lado['jambas']):
                    n = f"{pu['id']}.{i}.{j}"
                    ini[n] = self._sobre_pared(c, pared, s)
                    modo = 'laser' if s >= 0.15 else 'cinta'
                    obs.append(Obs('dist', (pared[0], n), s, MARGENES[modo], f"{pared[0]}–jamba {pu['id']}", modo))
                    obs.append(Obs('linea', (n, pared[0], pared[1]), 0.0, SIGMA_LINEA))
                    nom.append(n)
                self.jambas[(pu['id'], i)] = nom
                nombres_lado.append(nom)
            if len(nombres_lado) == 2 and pu.get('grosor'):
                # Empareja cada jamba de un lado con la del otro lado que tiene enfrente (la izquierda de uno es la
                # derecha del otro).
                (a1, a2), (b1, b2) = nombres_lado
                d = lambda p, q: math.dist(ini[p], ini[q])
                pares = [(a1, b1), (a2, b2)] if d(a1, b1) + d(a2, b2) <= d(a1, b2) + d(a2, b1) else [(a1, b2), (a2, b1)]
                pu['_pares'] = pares
                pared = pu['lados'][0]['pared']
                for p, q in pares:
                    obs.append(Obs('dist', (p, q), pu['grosor'], MARGENES['cinta'], f"grosor {pu['id']}", 'cinta'))
                    obs.append(Obs('perp', (p, q, pared[0], pared[1]), 0.0, SIGMA_JAMBA))
        for e in self.datos['estancias'].values():
            es = e['esquinas']
            for i in range(len(es)):
                tri = (es[i - 1], es[i], es[(i + 1) % len(es)])
                nominal = round(_angulo([v for n in tri for v in c[n]]) / (math.pi / 2)) * (math.pi / 2)
                obs.append(Obs('angulo', tri, nominal, SIGMA_ESCUADRA))
        self.tabiques = self._tabiques(c)
        for (a, b), (c2, d), solape in self.tabiques:
            obs.append(Obs('paralelo', (a, b, c2, d), 0.0, SIGMA_TABIQUE / solape))
        primera = next(iter(self.datos['estancias'].values()))['esquinas']
        return Red(ini, obs, (primera[0], primera[1]))

    def _tabiques(self, c):
        """Parejas de caras de estancias distintas, paralelas y enfrentadas a menos de MAX_TABIQUE."""
        caras = []
        for nom, e in self.datos['estancias'].items():
            es = e['esquinas']
            caras += [(nom, (es[i], es[(i + 1) % len(es)])) for i in range(len(es))]
        out = []
        for (e1, (a, b)), (e2, (c2, d)) in itertools.combinations(caras, 2):
            if e1 == e2:
                continue
            pa, pb, pc, pd = (np.array(c[n], float) for n in (a, b, c2, d))
            u = (pb - pa) / np.linalg.norm(pb - pa)
            v = (pd - pc) / np.linalg.norm(pd - pc)
            if u @ v > -0.99:                       # enfrentadas: sentidos opuestos
                continue
            sep = abs(u[0] * (pc - pa)[1] - u[1] * (pc - pa)[0])
            if sep > MAX_TABIQUE:
                continue
            t = sorted([0.0, float(np.linalg.norm(pb - pa))])
            q = sorted([float((pc - pa) @ u), float((pd - pa) @ u)])
            solape = min(t[1], q[1]) - max(t[0], q[0])
            if solape > 0.3:
                out.append(((a, b), (c2, d), solape))
        return out

    # --- ajuste e informe ---
    def ajustar(self):
        self._red = self.red()
        self.p = self._red.resolver()
        return self.p

    def esquinas(self):
        return [n for e in self.datos['estancias'].values() for n in e['esquinas']]

    def margenes(self):
        r = self._red
        return {(a, b): float(math.sqrt(r.grad_dist(a, b) @ r.cov @ r.grad_dist(a, b)))
                for a, b in itertools.combinations(self.esquinas(), 2)}

    def cerrado(self, tol=TOLERANCIA):
        return all(2 * s <= tol for s in self.margenes().values())

    def pares_estancia(self):
        """Lo que se mide dentro de cada estancia: pares de sus esquinas y de las jambas de sus puertas."""
        out = []
        for nom, e in self.datos['estancias'].items():
            pts = list(e['esquinas'])
            for (pid, lado), nombres in self.jambas.items():
                pu = next(p for p in self.datos['puertas'] if p['id'] == pid)
                if pu['lados'][lado]['pared'][0] in e['esquinas']:
                    pts += nombres
            out += list(itertools.combinations(pts, 2))
        return out

    def poligonos(self, p=None):
        p = p or self.p
        return {nom: Polygon([p[n] for n in e['esquinas']]) for nom, e in self.datos['estancias'].items()}

    def huecos_puertas(self, p=None):
        p = p or self.p
        out = {}
        for pu in self.datos['puertas']:
            if '_pares' in pu:
                (a, b), (c, d) = pu['_pares']
                out[pu['id']] = Polygon([p[a], p[c], p[d], p[b]])
        return out

    def libre(self, p=None):
        """Espacio por el que pasa la línea del láser: estancias y huecos de puerta."""
        return unary_union(list(self.poligonos(p).values()) + list(self.huecos_puertas(p).values())).buffer(1e-4)

    def siguiente(self, tol=TOLERANCIA, modo='laser', mejora_minima=0.001):
        """La medida que más ayuda, entre esquinas o jambas a la vista una de otra (también de una estancia a otra
        por una puerta abierta). Primero, que cada estancia cumpla la tolerancia; después, que la casa entera mejore
        mientras cada medida baje el peor margen al menos `mejora_minima`. None si no queda nada útil que medir."""
        r = self._red
        objetivo_estancias = self.pares_estancia()
        g_est = np.array([r.grad_dist(a, b) for a, b in objetivo_estancias])
        var_est = np.einsum('ij,jk,ik->i', g_est, r.cov, g_est)
        if np.any(2 * np.sqrt(var_est) > tol):
            pares, g, var, minimo = objetivo_estancias, g_est, var_est, 0.0
        else:
            pares = list(itertools.combinations(self.esquinas(), 2))
            g = np.array([r.grad_dist(a, b) for a, b in pares])
            var = np.einsum('ij,jk,ik->i', g, r.cov, g)
            if np.all(2 * np.sqrt(var) <= tol):
                return None
            minimo = mejora_minima / 2
        puntos = self.esquinas() + [n for nom in self.jambas.values() for n in nom]
        hechas = {frozenset(o.puntos) for o in r.obs if o.tipo == 'dist'}
        libre = self.libre()
        s2 = MARGENES[modo] ** 2
        mejor = None
        for a, b in itertools.combinations(puntos, 2):
            if frozenset((a, b)) in hechas or ('.' in a and a.split('.')[0] == b.split('.')[0]):
                continue
            if math.dist(self.p[a], self.p[b]) < 0.5:
                continue
            if not libre.contains(LineString([self.p[a], self.p[b]])):
                continue
            gi = r.grad_dist(a, b)
            cg = r.cov @ gi
            nueva = var - (g @ cg) ** 2 / (s2 + gi @ cg)
            peor = float(np.sqrt(nueva.max()))
            if mejor is None or peor < mejor[1]:
                mejor = ((a, b), peor)
        if mejor is None or float(np.sqrt(var.max())) - mejor[1] <= minimo:
            return None
        return mejor

    def resumen(self, tol=TOLERANCIA):
        """Peor margen dentro de las estancias y en la casa entera (2·sigma, metros)."""
        r = self._red
        est = max(self.pares_estancia(), key=lambda ab: r.grad_dist(*ab) @ r.cov @ r.grad_dist(*ab))
        m = self.margenes()
        casa = max(m, key=m.get)
        s_est = math.sqrt(r.grad_dist(*est) @ r.cov @ r.grad_dist(*est))
        return {'estancias': (est, 2 * s_est), 'casa': (casa, 2 * m[casa])}

    def nombre_punto(self, n):
        """«S3» o «jamba de Psal (lado PASILLO)»."""
        if '.' not in n:
            return n
        pid, lado, _ = n.split('.')
        pu = next(p for p in self.datos['puertas'] if p['id'] == pid)
        est = self.estancia_de(pu['lados'][int(lado)]['pared'][0])
        return f'jamba de {pid} ({est.lower()})'

    def estancia_punto(self, n):
        if '.' not in n:
            return self.estancia_de(n)
        pid, lado, _ = n.split('.')
        pu = next(p for p in self.datos['puertas'] if p['id'] == pid)
        return self.estancia_de(pu['lados'][int(lado)]['pared'][0])

    def estancia_de(self, esquina):
        return next(nom for nom, e in self.datos['estancias'].items() if esquina in e['esquinas'])
