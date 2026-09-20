# SERGIO 2026-09-20: pruebas basicas del modelo de datos (feature/esqueleto-app)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database


def test_init_db_crea_tablas(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    tablas = {fila["name"] for fila in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    esperadas = {"capitulos", "ejercicios", "preguntas_quiz", "alternativas", "intentos_quiz", "fotos", "progreso"}
    assert esperadas.issubset(tablas)


def _crear_capitulo_con_ejercicio_quiz(conn):
    conn.execute("INSERT INTO capitulos (orden, titulo, slug) VALUES (1, 'Cap 1', 'cap-1')")
    capitulo_id = conn.execute("SELECT id FROM capitulos WHERE slug = 'cap-1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO ejercicios (capitulo_id, orden, titulo, tipo) VALUES (?, 1, 'Quiz 1', 'quiz')",
        (capitulo_id,),
    )
    ejercicio_id = conn.execute("SELECT id FROM ejercicios WHERE capitulo_id = ?", (capitulo_id,)).fetchone()["id"]
    conn.commit()
    return capitulo_id, ejercicio_id


def test_ejercicio_se_completa_solo_con_todas_correctas(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    _capitulo_id, ejercicio_id = _crear_capitulo_con_ejercicio_quiz(conn)
    conn.close()

    database.registrar_intento_quiz(ejercicio_id, correctas=4, total=5, aprobado=False)
    assert database.ejercicio_completado(ejercicio_id) is False

    database.registrar_intento_quiz(ejercicio_id, correctas=5, total=5, aprobado=True)
    assert database.ejercicio_completado(ejercicio_id) is True


def test_capitulo_completado_requiere_todos_los_ejercicios(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    capitulo_id, ejercicio_id = _crear_capitulo_con_ejercicio_quiz(conn)
    conn.execute(
        "INSERT INTO ejercicios (capitulo_id, orden, titulo, tipo) VALUES (?, 2, 'Foto 1', 'foto')",
        (capitulo_id,),
    )
    conn.commit()
    ejercicio_foto_id = conn.execute(
        "SELECT id FROM ejercicios WHERE capitulo_id = ? AND tipo = 'foto'", (capitulo_id,)
    ).fetchone()["id"]
    conn.close()

    database.marcar_ejercicio_completado(ejercicio_id)
    assert database.capitulo_completado(capitulo_id) is False

    database.marcar_ejercicio_completado(ejercicio_foto_id)
    assert database.capitulo_completado(capitulo_id) is True


def test_aprobar_foto_marca_ejercicio_completado(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    conn.execute("INSERT INTO capitulos (orden, titulo, slug) VALUES (1, 'Cap 1', 'cap-1')")
    capitulo_id = conn.execute("SELECT id FROM capitulos WHERE slug = 'cap-1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO ejercicios (capitulo_id, orden, titulo, tipo) VALUES (?, 1, 'Foto 1', 'foto')",
        (capitulo_id,),
    )
    ejercicio_id = conn.execute("SELECT id FROM ejercicios WHERE capitulo_id = ?", (capitulo_id,)).fetchone()["id"]
    conn.commit()
    conn.close()

    database.guardar_foto(ejercicio_id, "1/foto.jpg", "{}")
    foto_id = database.listar_fotos(ejercicio_id)[0]["id"]

    assert database.ejercicio_completado(ejercicio_id) is False
    database.aprobar_foto(foto_id)
    assert database.ejercicio_completado(ejercicio_id) is True
    assert database.listar_fotos(ejercicio_id)[0]["estado"] == "aprobada"
