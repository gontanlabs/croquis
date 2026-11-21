"""Ajuste de una planta por mínimos cuadrados (prueba A de Croquis).

Las esquinas de una estancia se calculan a partir de un croquis aproximado y de medidas entre esquinas, cada una con su
margen según cómo se tomó (C-005). Las paredes «casi a escuadra» entran como una hipótesis débil que las medidas
corrigen. Devuelve las coordenadas, el margen de cada distancia, las medidas sospechosas (errores de tecleo) y la
medida que más falta hace para cerrar el plano a la tolerancia pedida (±5 mm, C-004).

Unidades: metros y radianes. El margen (sigma) es una desviación típica; «cumple» quiere decir 2·sigma <= tolerancia.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np

# Desviación típica de cada modo de medir, en metros (C-005). Láser: la gama de medidores de mano da ±1,5 mm.
MARGENES = {'laser': 0.001, 'cinta': 0.002, 'camara': 0.03}
TOLERANCIA = 0.005


@dataclass
class Medida:
    de: str
    a: str
    valor: float
    modo: str = 'laser'
    sigma: float | None = None

    def __post_init__(self):
        if self.sigma is None:
            self.sigma = MARGENES[self.modo]


@dataclass
class Resultado:
    puntos: dict[str, tuple[float, float]]
    margen: dict[tuple[str, str], float]          # sigma de la distancia entre cada par de esquinas
    sospechosas: list[tuple[Medida, float]]       # (medida, residuo normalizado)
    angulos: dict[str, float]                     # ángulo interior de cada esquina, en grados
    area: float

    def peor(self) -> tuple[tuple[str, str], float]:
        par = max(self.margen, key=self.margen.get)
        return par, self.margen[par]

    def cerrado(self, tolerancia: float = TOLERANCIA) -> bool:
        return all(2 * s <= tolerancia for s in self.margen.values())


@dataclass
class Planta:
    """Una estancia: esquinas en orden antihorario y el croquis (posición aproximada de cada una)."""
    contorno: list[str]
    croquis: dict[str, tuple[float, float]]
    sigma_escuadra_grados: float = 3.0
    medidas: list[Medida] = field(default_factory=list)

    def medir(self, de: str, a: str, valor: float, modo: str = 'laser') -> Medida:
        m = Medida(de, a, valor, modo)
        self.medidas.append(m)
        return m

    # --- parámetros: la primera esquina fija en el origen y la segunda sobre el eje X (fija el giro y la posición) ---
    def _libres(self):
        a, b = self.contorno[0], self.contorno[1]
        return [(n, k) for n in self.contorno for k in (0, 1) if n != a and not (n == b and k == 1)]

    def _a_puntos(self, x: np.ndarray) -> dict[str, np.ndarray]:
        p = {n: np.zeros(2) for n in self.contorno}
        for (n, k), v in zip(self._libres(), x):
            p[n][k] = v
        return p

    def _x0(self) -> np.ndarray:
        # El croquis se lleva al mismo sistema: primera esquina en el origen y la segunda sobre el eje X.
        c = {n: np.array(v, float) for n, v in self.croquis.items()}
        o, b = c[self.contorno[0]], c[self.contorno[1]]
        ang = -math.atan2(b[1] - o[1], b[0] - o[0])
        r = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
        c = {n: r @ (v - o) for n, v in c.items()}
        return np.array([c[n][k] for n, k in self._libres()])

    def _angulo(self, p, i: int) -> float:
        n = len(self.contorno)
        k = p[self.contorno[i]]
        a = p[self.contorno[i - 1]] - k
        b = p[self.contorno[(i + 1) % n]] - k
        return math.atan2(b[0] * a[1] - b[1] * a[0], b @ a) % (2 * math.pi)

    def _nominales(self) -> list[float]:
        p = {n: np.array(v, float) for n, v in self.croquis.items()}
        return [round(self._angulo(p, i) / (math.pi / 2)) * (math.pi / 2) for i in range(len(self.contorno))]

    # --- observaciones: medidas + hipótesis de escuadra ---
    def _observaciones(self, x, extra: list[Medida] = ()):
        p = self._a_puntos(x)
        f, obs, sig = [], [], []
        for m in list(self.medidas) + list(extra):
            f.append(float(np.linalg.norm(p[m.a] - p[m.de])))
            obs.append(m.valor)
            sig.append(m.sigma)
        s = math.radians(self.sigma_escuadra_grados)
        for i, nom in enumerate(self._nominales()):
            d = (self._angulo(p, i) - nom + math.pi) % (2 * math.pi) - math.pi
            f.append(nom + d)
            obs.append(nom)
            sig.append(s)
        return np.array(f), np.array(obs), np.array(sig)

    def _jacobiano(self, x, extra=()):
        f0 = self._observaciones(x, extra)[0]
        j = np.zeros((len(f0), len(x)))
        h = 1e-7
        for c in range(len(x)):
            d = np.zeros_like(x)
            d[c] = h
            j[:, c] = (self._observaciones(x + d, extra)[0] - self._observaciones(x - d, extra)[0]) / (2 * h)
        return j

    def _grad_distancia(self, x, de, a):
        p = self._a_puntos(x)
        u = p[a] - p[de]
        u = u / np.linalg.norm(u)
        g = np.zeros(len(x))
        for c, (n, k) in enumerate(self._libres()):
            if n == a:
                g[c] += u[k]
            if n == de:
                g[c] -= u[k]
        return g

    def _resolver(self):
        x = self._x0()
        for _ in range(50):
            f, obs, sig = self._observaciones(x)
            j = self._jacobiano(x) / sig[:, None]
            dx = np.linalg.lstsq(j, (obs - f) / sig, rcond=None)[0]
            x = x + dx
            if np.max(np.abs(dx)) < 1e-10:
                break
        f, obs, sig = self._observaciones(x)
        j = self._jacobiano(x) / sig[:, None]
        normal = j.T @ j
        return x, normal, (obs - f) / sig, j

    def ajustar(self, umbral_sospecha: float = 3.0) -> Resultado:
        x, normal, r, j = self._resolver()
        cov = np.linalg.inv(normal)
        p = self._a_puntos(x)
        margen = {}
        for de, a in itertools.combinations(self.contorno, 2):
            g = self._grad_distancia(x, de, a)
            margen[(de, a)] = float(math.sqrt(g @ cov @ g))
        # Residuos normalizados (prueba de Baarda): solo se puede acusar a una medida que tiene comprobación.
        h = np.einsum('ij,jk,ik->i', j, cov, j)
        sospechosas = []
        for i, m in enumerate(self.medidas):
            redundancia = 1 - h[i]
            if redundancia > 0.05:
                w = abs(r[i]) / math.sqrt(redundancia)
                if w > umbral_sospecha:
                    sospechosas.append((m, w))
        sospechosas.sort(key=lambda t: -t[1])
        angulos = {n: math.degrees(self._angulo(p, i)) for i, n in enumerate(self.contorno)}
        pts = [p[n] for n in self.contorno]
        area = 0.5 * abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])))
        return Resultado({n: (float(v[0]), float(v[1])) for n, v in p.items()}, margen, sospechosas, angulos, area)

    # --- qué medir después ---
    def _visible(self, p, de, a) -> bool:
        """El segmento entre dos esquinas va por dentro de la estancia (se puede medir de esquina a esquina)."""
        pa, pb = np.array(p[de]), np.array(p[a])
        pts = [np.array(p[n]) for n in self.contorno]
        if not _dentro((pa + pb) / 2, pts):
            return False
        for c, d in zip(pts, pts[1:] + pts[:1]):
            if any(np.allclose(q, r) for q in (pa, pb) for r in (c, d)):
                continue
            if _cruzan(pa, pb, c, d):
                return False
        return True

    def siguiente(self, tolerancia: float = TOLERANCIA, modo: str = 'laser'):
        """La medida que, tomada con `modo`, deja más bajo el peor margen. None si el plano ya cumple."""
        x, normal, _, _ = self._resolver()
        actual = self.ajustar()
        if actual.cerrado(tolerancia):
            return None
        hechas = {frozenset((m.de, m.a)) for m in self.medidas if m.modo != 'camara'}
        mejor = None
        for de, a in itertools.combinations(self.contorno, 2):
            if frozenset((de, a)) in hechas or not self._visible(actual.puntos, de, a):
                continue
            g = self._grad_distancia(x, de, a)
            cov = np.linalg.inv(normal + np.outer(g, g) / MARGENES[modo] ** 2)
            peor = max(math.sqrt(self._grad_distancia(x, i, k) @ cov @ self._grad_distancia(x, i, k))
                       for i, k in itertools.combinations(self.contorno, 2))
            if mejor is None or peor < mejor[1]:
                mejor = ((de, a), peor)
        return mejor


def _dentro(q, pts) -> bool:
    c = False
    for a, b in zip(pts, pts[1:] + pts[:1]):
        if (a[1] > q[1]) != (b[1] > q[1]):
            if q[0] < a[0] + (q[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                c = not c
    return c


def _cruzan(p1, p2, p3, p4) -> bool:
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (o(p1, p2, p3) * o(p1, p2, p4) < 0) and (o(p3, p4, p1) * o(p3, p4, p2) < 0)
