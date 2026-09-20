# SERGIO 2026-09-20: modelo de datos reestructurado en capitulo -> subcapitulo -> tema
# (feature/estructura-capitulo-subcapitulo-tema)
# Cada tema tiene 5 secciones: teoria, ejemplos, ejercicios, fotos, evaluacion.
# Capitulo y subcapitulo solo tienen texto introductorio (sin ejercicios ni evaluacion).
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "aprender_fotografia.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS capitulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            introduccion_md TEXT
        );

        CREATE TABLE IF NOT EXISTS subcapitulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capitulo_id INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            introduccion_md TEXT,
            FOREIGN KEY (capitulo_id) REFERENCES capitulos(id)
        );

        CREATE TABLE IF NOT EXISTS temas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subcapitulo_id INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            teoria_md TEXT,
            FOREIGN KEY (subcapitulo_id) REFERENCES subcapitulos(id)
        );

        CREATE TABLE IF NOT EXISTS ejemplos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema_id INTEGER NOT NULL,
            orden INTEGER NOT NULL DEFAULT 1,
            descripcion TEXT,
            url_o_fuente TEXT,
            FOREIGN KEY (tema_id) REFERENCES temas(id)
        );

        CREATE TABLE IF NOT EXISTS ejercicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema_id INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            FOREIGN KEY (tema_id) REFERENCES temas(id)
        );

        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ejercicio_id INTEGER NOT NULL,
            ruta_archivo TEXT NOT NULL,
            exif_json TEXT,
            fecha_subida TEXT DEFAULT CURRENT_TIMESTAMP,
            estado TEXT NOT NULL DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'aprobada')),
            comentario TEXT,
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
        );

        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema_id INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            FOREIGN KEY (tema_id) REFERENCES temas(id)
        );

        CREATE TABLE IF NOT EXISTS preguntas_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluacion_id INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            texto TEXT NOT NULL,
            FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones(id)
        );

        CREATE TABLE IF NOT EXISTS alternativas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            es_correcta INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (pregunta_id) REFERENCES preguntas_quiz(id)
        );

        CREATE TABLE IF NOT EXISTS intentos_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluacion_id INTEGER NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            aprobado INTEGER NOT NULL,
            correctas INTEGER NOT NULL,
            total INTEGER NOT NULL,
            FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones(id)
        );
        """
    )
    conn.commit()
    conn.close()


# --- Arbol capitulo / subcapitulo / tema ---

def listar_capitulos():
    conn = get_connection()
    filas = conn.execute("SELECT * FROM capitulos ORDER BY orden").fetchall()
    conn.close()
    return filas


def obtener_capitulo_por_slug(slug):
    conn = get_connection()
    fila = conn.execute("SELECT * FROM capitulos WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return fila


def listar_subcapitulos(capitulo_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM subcapitulos WHERE capitulo_id = ? ORDER BY orden", (capitulo_id,)
    ).fetchall()
    conn.close()
    return filas


def obtener_subcapitulo_por_slug(slug):
    conn = get_connection()
    fila = conn.execute("SELECT * FROM subcapitulos WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return fila


def listar_temas(subcapitulo_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM temas WHERE subcapitulo_id = ? ORDER BY orden", (subcapitulo_id,)
    ).fetchall()
    conn.close()
    return filas


def obtener_tema_por_slug(slug):
    conn = get_connection()
    fila = conn.execute("SELECT * FROM temas WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return fila


def obtener_tema(tema_id):
    conn = get_connection()
    fila = conn.execute("SELECT * FROM temas WHERE id = ?", (tema_id,)).fetchone()
    conn.close()
    return fila


def arbol_completo():
    # Devuelve la lista de capitulos, cada uno con sus subcapitulos, cada uno con sus temas
    conn = get_connection()
    capitulos = conn.execute("SELECT * FROM capitulos ORDER BY orden").fetchall()
    resultado = []
    for capitulo in capitulos:
        subcapitulos = conn.execute(
            "SELECT * FROM subcapitulos WHERE capitulo_id = ? ORDER BY orden", (capitulo["id"],)
        ).fetchall()
        subcapitulos_con_temas = []
        for subcapitulo in subcapitulos:
            temas = conn.execute(
                "SELECT * FROM temas WHERE subcapitulo_id = ? ORDER BY orden", (subcapitulo["id"],)
            ).fetchall()
            subcapitulos_con_temas.append({"subcapitulo": subcapitulo, "temas": temas})
        resultado.append({"capitulo": capitulo, "subcapitulos": subcapitulos_con_temas})
    conn.close()
    return resultado


# --- Ejemplos ---

def listar_ejemplos(tema_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM ejemplos WHERE tema_id = ? ORDER BY orden", (tema_id,)
    ).fetchall()
    conn.close()
    return filas


# --- Ejercicios y fotos ---

def listar_ejercicios(tema_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM ejercicios WHERE tema_id = ? ORDER BY orden", (tema_id,)
    ).fetchall()
    conn.close()
    return filas


def obtener_ejercicio(ejercicio_id):
    conn = get_connection()
    fila = conn.execute("SELECT * FROM ejercicios WHERE id = ?", (ejercicio_id,)).fetchone()
    conn.close()
    return fila


def listar_fotos(ejercicio_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM fotos WHERE ejercicio_id = ? ORDER BY fecha_subida DESC", (ejercicio_id,)
    ).fetchall()
    conn.close()
    return filas


def guardar_foto(ejercicio_id, ruta_archivo, exif_json):
    conn = get_connection()
    conn.execute(
        "INSERT INTO fotos (ejercicio_id, ruta_archivo, exif_json) VALUES (?, ?, ?)",
        (ejercicio_id, ruta_archivo, exif_json),
    )
    conn.commit()
    conn.close()


def aprobar_foto(foto_id):
    conn = get_connection()
    conn.execute("UPDATE fotos SET estado = 'aprobada' WHERE id = ?", (foto_id,))
    conn.commit()
    conn.close()


def ejercicio_completado(ejercicio_id):
    conn = get_connection()
    fila = conn.execute(
        "SELECT COUNT(*) AS c FROM fotos WHERE ejercicio_id = ? AND estado = 'aprobada'", (ejercicio_id,)
    ).fetchone()
    conn.close()
    return fila["c"] > 0


# --- Evaluaciones y quiz ---

def listar_evaluaciones(tema_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM evaluaciones WHERE tema_id = ? ORDER BY orden", (tema_id,)
    ).fetchall()
    conn.close()
    return filas


def obtener_evaluacion(evaluacion_id):
    conn = get_connection()
    fila = conn.execute("SELECT * FROM evaluaciones WHERE id = ?", (evaluacion_id,)).fetchone()
    conn.close()
    return fila


def obtener_preguntas(evaluacion_id):
    conn = get_connection()
    preguntas = conn.execute(
        "SELECT * FROM preguntas_quiz WHERE evaluacion_id = ? ORDER BY orden", (evaluacion_id,)
    ).fetchall()
    resultado = []
    for pregunta in preguntas:
        alternativas = conn.execute(
            "SELECT * FROM alternativas WHERE pregunta_id = ?", (pregunta["id"],)
        ).fetchall()
        resultado.append({"pregunta": pregunta, "alternativas": alternativas})
    conn.close()
    return resultado


def registrar_intento_quiz(evaluacion_id, correctas, total, aprobado):
    conn = get_connection()
    conn.execute(
        "INSERT INTO intentos_quiz (evaluacion_id, aprobado, correctas, total) VALUES (?, ?, ?, ?)",
        (evaluacion_id, int(aprobado), correctas, total),
    )
    conn.commit()
    conn.close()


def evaluacion_aprobada(evaluacion_id):
    conn = get_connection()
    fila = conn.execute(
        "SELECT COUNT(*) AS c FROM intentos_quiz WHERE evaluacion_id = ? AND aprobado = 1", (evaluacion_id,)
    ).fetchone()
    conn.close()
    return fila["c"] > 0


def ultimo_intento(evaluacion_id):
    conn = get_connection()
    fila = conn.execute(
        "SELECT * FROM intentos_quiz WHERE evaluacion_id = ? ORDER BY fecha DESC LIMIT 1", (evaluacion_id,)
    ).fetchone()
    conn.close()
    return fila


# --- Completitud de un tema ---

def tema_completado(tema_id):
    ejercicios = listar_ejercicios(tema_id)
    evaluaciones = listar_evaluaciones(tema_id)
    if not ejercicios and not evaluaciones:
        return True
    ejercicios_ok = all(ejercicio_completado(e["id"]) for e in ejercicios)
    evaluaciones_ok = all(evaluacion_aprobada(ev["id"]) for ev in evaluaciones)
    return ejercicios_ok and evaluaciones_ok
