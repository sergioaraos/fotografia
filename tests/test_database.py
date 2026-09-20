# SERGIO 2026-09-20: pruebas del modelo capitulo -> subcapitulo -> tema
# (feature/estructura-capitulo-subcapitulo-tema)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database


def _crear_arbol_basico(conn, con_ejercicio=True, con_evaluacion=True):
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
    tema_id = conn.execute("SELECT id FROM temas WHERE slug = 'tema-1'").fetchone()["id"]

    ejercicio_id = None
    if con_ejercicio:
        conn.execute(
            "INSERT INTO ejercicios (tema_id, orden, titulo) VALUES (?, 1, 'Ejercicio 1')", (tema_id,)
        )
        ejercicio_id = conn.execute("SELECT id FROM ejercicios WHERE tema_id = ?", (tema_id,)).fetchone()["id"]

    evaluacion_id = None
    if con_evaluacion:
        conn.execute(
            "INSERT INTO evaluaciones (tema_id, orden, titulo) VALUES (?, 1, 'Evaluacion 1')", (tema_id,)
        )
        evaluacion_id = conn.execute(
            "SELECT id FROM evaluaciones WHERE tema_id = ?", (tema_id,)
        ).fetchone()["id"]

    conn.commit()
    return capitulo_id, subcapitulo_id, tema_id, ejercicio_id, evaluacion_id


def test_init_db_crea_tablas(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    tablas = {fila["name"] for fila in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    esperadas = {
        "capitulos", "subcapitulos", "temas", "ejemplos", "ejercicios",
        "fotos", "evaluaciones", "preguntas_quiz", "alternativas", "intentos_quiz",
    }
    assert esperadas.issubset(tablas)


def test_ejercicio_se_completa_con_foto_aprobada(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    _cap, _sub, _tema, ejercicio_id, _ev = _crear_arbol_basico(conn, con_evaluacion=False)
    conn.close()

    assert database.ejercicio_completado(ejercicio_id) is False
    database.guardar_foto(ejercicio_id, "foto.jpg", "{}")
    foto_id = database.listar_fotos(ejercicio_id)[0]["id"]
    assert database.ejercicio_completado(ejercicio_id) is False

    database.aprobar_foto(foto_id)
    assert database.ejercicio_completado(ejercicio_id) is True


def test_evaluacion_aprobada_solo_con_intento_correcto(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    _cap, _sub, _tema, _ej, evaluacion_id = _crear_arbol_basico(conn, con_ejercicio=False)
    conn.close()

    database.registrar_intento_quiz(evaluacion_id, correctas=4, total=5, aprobado=False)
    assert database.evaluacion_aprobada(evaluacion_id) is False

    database.registrar_intento_quiz(evaluacion_id, correctas=5, total=5, aprobado=True)
    assert database.evaluacion_aprobada(evaluacion_id) is True


def test_tema_completado_requiere_ejercicios_y_evaluaciones(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    _cap, _sub, tema_id, ejercicio_id, evaluacion_id = _crear_arbol_basico(conn)
    conn.close()

    assert database.tema_completado(tema_id) is False

    database.guardar_foto(ejercicio_id, "foto.jpg", "{}")
    database.aprobar_foto(database.listar_fotos(ejercicio_id)[0]["id"])
    assert database.tema_completado(tema_id) is False

    database.registrar_intento_quiz(evaluacion_id, correctas=5, total=5, aprobado=True)
    assert database.tema_completado(tema_id) is True


def test_tema_sin_ejercicios_ni_evaluacion_se_considera_completo(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    _cap, _sub, tema_id, _ej, _ev = _crear_arbol_basico(conn, con_ejercicio=False, con_evaluacion=False)
    conn.close()
    assert database.tema_completado(tema_id) is True
