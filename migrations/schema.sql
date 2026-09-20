-- SERGIO 2026-09-20: mismo modelo de datos que la version Python, portado a Node
-- (feature/port-a-nodejs)
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
