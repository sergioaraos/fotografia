# SERGIO 2026-09-20: pruebas basicas de las rutas (feature/estructura-capitulo-subcapitulo-tema)
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


def test_tema_inexistente_da_404(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    client = TestClient(main.app)
    respuesta = client.get("/tema/no-existe")
    assert respuesta.status_code == 404


def test_segundo_tema_bloqueado_no_muestra_teoria(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    conn.execute("INSERT INTO capitulos (orden, titulo, slug) VALUES (1, 'Cap 1', 'cap-1')")
    capitulo_id = conn.execute("SELECT id FROM capitulos WHERE slug = 'cap-1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO subcapitulos (capitulo_id, orden, titulo, slug) VALUES (?, 1, 'Sub 1', 'sub-1')",
        (capitulo_id,),
    )
    subcapitulo_id = conn.execute("SELECT id FROM subcapitulos WHERE slug = 'sub-1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO temas (subcapitulo_id, orden, titulo, slug, teoria_md) VALUES (?, 1, 'Tema 1', 'tema-1', 'texto')",
        (subcapitulo_id,),
    )
    conn.execute(
        "INSERT INTO temas (subcapitulo_id, orden, titulo, slug, teoria_md) VALUES (?, 2, 'Tema 2', 'tema-2', 'secreto')",
        (subcapitulo_id,),
    )
    tema1_id = conn.execute("SELECT id FROM temas WHERE slug = 'tema-1'").fetchone()["id"]
    # SERGIO 2026-09-20: sin esto el tema 1 se considera completo por no tener nada
    # que hacer, y el tema 2 quedaria desbloqueado sin querer en este test
    conn.execute(
        "INSERT INTO evaluaciones (tema_id, orden, titulo) VALUES (?, 1, 'Evaluacion 1')", (tema1_id,)
    )
    conn.commit()
    conn.close()

    client = TestClient(main.app)
    respuesta = client.get("/tema/tema-2")
    assert respuesta.status_code == 200
    assert "bloqueado" in respuesta.text.lower()
    assert "secreto" not in respuesta.text


def test_capitulo_muestra_introduccion(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    conn.execute(
        "INSERT INTO capitulos (orden, titulo, slug, introduccion_md) VALUES (1, 'Cap 1', 'cap-1', 'resumen del capitulo')"
    )
    conn.commit()
    conn.close()

    client = TestClient(main.app)
    respuesta = client.get("/capitulo/cap-1")
    assert respuesta.status_code == 200
    assert "resumen del capitulo" in respuesta.text

def test_ver_tema_marca_su_capitulo_como_activo(tmp_path, monkeypatch):
    # SERGIO 2026-09-20: regresion del bug donde el acordeon del capitulo se
    # cerraba y ocultaba el subcapitulo/tema activo al entrar a un tema
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    conn.execute("INSERT INTO capitulos (orden, titulo, slug) VALUES (1, 'Cap 1', 'cap-1')")
    capitulo_id = conn.execute("SELECT id FROM capitulos WHERE slug = 'cap-1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO subcapitulos (capitulo_id, orden, titulo, slug) VALUES (?, 1, 'Sub 1', 'sub-1')",
        (capitulo_id,),
    )
    subcapitulo_id = conn.execute("SELECT id FROM subcapitulos WHERE slug = 'sub-1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO temas (subcapitulo_id, orden, titulo, slug) VALUES (?, 1, 'Tema 1', 'tema-1')",
        (subcapitulo_id,),
    )
    conn.commit()
    conn.close()

    client = TestClient(main.app)
    respuesta = client.get("/tema/tema-1")
    assert respuesta.status_code == 200
    assert '<details class="capitulo" open>' in respuesta.text
