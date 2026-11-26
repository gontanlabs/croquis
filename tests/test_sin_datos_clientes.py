"""El guardián de datos de clientes, sobre un repo de git temporal (necesita git en el PATH)."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from sin_datos_clientes import revisar  # noqa: E402


def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "prototipo").mkdir()
    (tmp_path / "prototipo" / "ajuste.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    return tmp_path


def test_limpio(tmp_path):
    assert revisar(repo(tmp_path), tmp_path / "no-hay-claves") == []


def test_levantamiento_con_tilde(tmp_path):
    r = repo(tmp_path)
    f = r / "levantamientos" / "mi-casa" / "Habitación 1.json"
    f.parent.mkdir(parents=True)
    f.write_text("{}", encoding="utf-8")
    subprocess.run(["git", "-C", str(r), "add", "-f", str(f)], check=True)
    problemas = revisar(r, tmp_path / "no-hay-claves")
    assert problemas == ["datos de clientes en git: levantamientos/mi-casa/Habitación 1.json"]


def test_copia_de_las_claves_con_otro_nombre(tmp_path):
    r = repo(tmp_path / "repo")
    claves = tmp_path / "claves"
    claves.mkdir()
    (claves / "estudio.json").write_text('{"estudio": "real"}', encoding="utf-8")
    (r / "prototipo" / "config.json").write_text('{"estudio": "real"}', encoding="utf-8")
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    assert revisar(r, claves) == ["copia de ~/.croquis/estudio.json en git: prototipo/config.json"]
