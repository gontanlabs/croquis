"""Pruebas del ajuste: python -m pytest (o python scripts/comprobar.py). El prototipo entra por pyproject.toml."""

from ajuste import Planta
from prueba_a import ejecutar


def test_cuadrado_sin_diagonal_no_cierra():
    # Cuatro lados medidos y nada más: la forma depende de la hipótesis de escuadra, no cumple ±5 mm.
    p = Planta(list('ABCD'), {'A': (0, 0), 'B': (4, 0), 'C': (4, 3), 'D': (0, 3)})
    for de, a, v in [('A', 'B', 4.0), ('B', 'C', 3.0), ('C', 'D', 4.0), ('D', 'A', 3.0)]:
        p.medir(de, a, v)
    r = p.ajustar()
    assert not r.cerrado()
    # Con una diagonal queda rígido y cumple.
    p.medir('A', 'C', 5.0)
    assert p.ajustar().cerrado()
    assert p.siguiente() is None


def test_prueba_a_completa():
    r = ejecutar(dibujar_dxf=False, salida=lambda t: None)
    assert r['cerrado']
    assert r['error_max'] < 0.005, r
    assert r['detectada'], 'no detectó el error de tecleo'
