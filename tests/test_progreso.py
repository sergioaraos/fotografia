# SERGIO 2026-09-20: pruebas del desbloqueo secuencial de temas
# (feature/estructura-capitulo-subcapitulo-tema)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database
import progreso


def _crear_dos_temas(conn):
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
    conn.execute(
        "INSERT INTO temas (subcapitulo_id, orden, titulo, slug) VALUES (?, 2, 'Tema 2', 'tema-2')",
        (subcapitulo_id,),
    )
    tema1_id = conn.execute("SELECT id FROM temas WHERE slug = 'tema-1'").fetchone()["id"]
    conn.execute(
        "INSERT INTO evaluaciones (tema_id, orden, titulo) VALUES (?, 1, 'Evaluacion 1')", (tema1_id,)
    )
    evaluacion_id = conn.execute("SELECT id FROM evaluaciones WHERE tema_id = ?", (tema1_id,)).fetchone()["id"]
    conn.commit()
    return tema1_id, evaluacion_id


def test_segundo_tema_bloqueado_hasta_completar_el_primero(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    conn = database.get_connection()
    tema1_id, evaluacion_id = _crear_dos_temas(conn)
    conn.close()

    assert progreso.tema_desbloqueado("tema-1") is True
    assert progreso.tema_desbloqueado("tema-2") is False

    database.registrar_intento_quiz(evaluacion_id, correctas=5, total=5, aprobado=True)
    assert progreso.tema_desbloqueado("tema-2") is True
