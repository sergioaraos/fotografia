# SERGIO 2026-09-20: pruebas basicas de las rutas (feature/esqueleto-app)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database
import main
from fastapi.testclient import TestClient


def test_index_responde_200(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    client = TestClient(main.app)
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert "Aprender Fotografia de Cero" in respuesta.text


def test_capitulo_inexistente_da_404(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    client = TestClient(main.app)
    respuesta = client.get("/capitulo/no-existe")
    assert respuesta.status_code == 404


def test_capitulo_bloqueado_no_muestra_teoria(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    conn.execute("INSERT INTO capitulos (orden, titulo, slug, teoria_md) VALUES (1, 'Cap 1', 'cap-1', 'texto')")
    conn.execute("INSERT INTO capitulos (orden, titulo, slug, teoria_md) VALUES (2, 'Cap 2', 'cap-2', 'secreto')")
    conn.commit()
    conn.close()

    client = TestClient(main.app)
    respuesta = client.get("/capitulo/cap-2")
    assert respuesta.status_code == 200
    assert "bloqueado" in respuesta.text.lower()
    assert "secreto" not in respuesta.text
