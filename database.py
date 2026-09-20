# SERGIO 2026-09-20: esqueleto inicial de la base de datos (feature/esqueleto-app)
# Modelo: capitulos -> ejercicios (quiz o foto) -> progreso por ejercicio.
# Un ejercicio de quiz se aprueba solo si las 5 preguntas quedan correctas.
# Un ejercicio de foto queda "pendiente" hasta que se revisa en el chat y se aprueba.
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
            teoria_md TEXT
        );

        CREATE TABLE IF NOT EXISTS ejercicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capitulo_id INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            tipo TEXT NOT NULL CHECK(tipo IN ('quiz', 'foto')),
            FOREIGN KEY (capitulo_id) REFERENCES capitulos(id)
        );

        CREATE TABLE IF NOT EXISTS preguntas_quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ejercicio_id INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            texto TEXT NOT NULL,
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
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
            ejercicio_id INTEGER NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            aprobado INTEGER NOT NULL,
            correctas INTEGER NOT NULL,
            total INTEGER NOT NULL,
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
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

        CREATE TABLE IF NOT EXISTS progreso (
            ejercicio_id INTEGER PRIMARY KEY,
            completado INTEGER NOT NULL DEFAULT 0,
            fecha_completado TEXT,
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
        );
        """
    )
    conn.commit()
    conn.close()


# --- Capitulos ---

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


# --- Ejercicios ---

def obtener_ejercicios(capitulo_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM ejercicios WHERE capitulo_id = ? ORDER BY orden", (capitulo_id,)
    ).fetchall()
    conn.close()
    return filas


def obtener_ejercicio(ejercicio_id):
    conn = get_connection()
    fila = conn.execute("SELECT * FROM ejercicios WHERE id = ?", (ejercicio_id,)).fetchone()
    conn.close()
    return fila


def obtener_preguntas(ejercicio_id):
    conn = get_connection()
    preguntas = conn.execute(
        "SELECT * FROM preguntas_quiz WHERE ejercicio_id = ? ORDER BY orden", (ejercicio_id,)
    ).fetchall()
    resultado = []
    for pregunta in preguntas:
        alternativas = conn.execute(
            "SELECT * FROM alternativas WHERE pregunta_id = ?", (pregunta["id"],)
        ).fetchall()
        resultado.append({"pregunta": pregunta, "alternativas": alternativas})
    conn.close()
    return resultado


# --- Progreso ---

def ejercicio_completado(ejercicio_id):
    conn = get_connection()
    fila = conn.execute(
        "SELECT completado FROM progreso WHERE ejercicio_id = ?", (ejercicio_id,)
    ).fetchone()
    conn.close()
    return bool(fila and fila["completado"])


def marcar_ejercicio_completado(ejercicio_id):
    conn = get_connection()
    conn.execute(
        """INSERT INTO progreso (ejercicio_id, completado, fecha_completado)
           VALUES (?, 1, CURRENT_TIMESTAMP)
           ON CONFLICT(ejercicio_id) DO UPDATE SET completado = 1, fecha_completado = CURRENT_TIMESTAMP""",
        (ejercicio_id,),
    )
    conn.commit()
    conn.close()


def capitulo_completado(capitulo_id):
    ejercicios = obtener_ejercicios(capitulo_id)
    if not ejercicios:
        return False
    return all(ejercicio_completado(ejercicio["id"]) for ejercicio in ejercicios)


# --- Quiz ---

def registrar_intento_quiz(ejercicio_id, correctas, total, aprobado):
    conn = get_connection()
    conn.execute(
        """INSERT INTO intentos_quiz (ejercicio_id, aprobado, correctas, total)
           VALUES (?, ?, ?, ?)""",
        (ejercicio_id, int(aprobado), correctas, total),
    )
    conn.commit()
    conn.close()
    if aprobado:
        marcar_ejercicio_completado(ejercicio_id)


# --- Fotos ---

def guardar_foto(ejercicio_id, ruta_archivo, exif_json):
    conn = get_connection()
    conn.execute(
        """INSERT INTO fotos (ejercicio_id, ruta_archivo, exif_json)
           VALUES (?, ?, ?)""",
        (ejercicio_id, ruta_archivo, exif_json),
    )
    conn.commit()
    conn.close()


def listar_fotos(ejercicio_id):
    conn = get_connection()
    filas = conn.execute(
        "SELECT * FROM fotos WHERE ejercicio_id = ? ORDER BY fecha_subida DESC", (ejercicio_id,)
    ).fetchall()
    conn.close()
    return filas


def aprobar_foto(foto_id):
    conn = get_connection()
    foto = conn.execute("SELECT * FROM fotos WHERE id = ?", (foto_id,)).fetchone()
    if foto:
        conn.execute("UPDATE fotos SET estado = 'aprobada' WHERE id = ?", (foto_id,))
        conn.commit()
    conn.close()
    if foto:
        marcar_ejercicio_completado(foto["ejercicio_id"])
