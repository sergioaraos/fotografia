// SERGIO 2026-09-20: acceso a SQLite con better-sqlite3 (sincrono), igual patron que
// TecnoRegistros: crea la carpeta data/ y aplica el schema si hace falta, para que el
// servidor arranque solo en un despliegue nuevo en Cloudways (feature/port-a-nodejs)
const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'data', 'aprender_fotografia.db');
const SCHEMA_PATH = path.join(__dirname, 'migrations', 'schema.sql');

// SERGIO 2026-09-20: acepta una ruta alternativa para que los tests puedan usar
// una base de datos temporal propia, sin tocar la real
function abrirBaseDeDatos(rutaPersonalizada) {
  const rutaFinal = rutaPersonalizada || DB_PATH;
  fs.mkdirSync(path.dirname(rutaFinal), { recursive: true });
  const db = new Database(rutaFinal);
  db.pragma('foreign_keys = ON');
  db.exec(fs.readFileSync(SCHEMA_PATH, 'utf8'));
  return db;
}

// --- Arbol capitulo / subcapitulo / tema ---

function obtenerCapituloPorSlug(db, slug) {
  return db.prepare('SELECT * FROM capitulos WHERE slug = ?').get(slug);
}

function obtenerSubcapituloPorSlug(db, slug) {
  return db.prepare('SELECT * FROM subcapitulos WHERE slug = ?').get(slug);
}

function obtenerTemaPorSlug(db, slug) {
  return db.prepare('SELECT * FROM temas WHERE slug = ?').get(slug);
}

function obtenerTema(db, temaId) {
  return db.prepare('SELECT * FROM temas WHERE id = ?').get(temaId);
}

function arbolCompleto(db) {
  const capitulos = db.prepare('SELECT * FROM capitulos ORDER BY orden').all();
  return capitulos.map((capitulo) => {
    const subcapitulos = db
      .prepare('SELECT * FROM subcapitulos WHERE capitulo_id = ? ORDER BY orden')
      .all(capitulo.id);
    const subcapitulosConTemas = subcapitulos.map((subcapitulo) => {
      const temas = db
        .prepare('SELECT * FROM temas WHERE subcapitulo_id = ? ORDER BY orden')
        .all(subcapitulo.id);
      return { subcapitulo, temas };
    });
    return { capitulo, subcapitulos: subcapitulosConTemas };
  });
}

// --- Ejemplos ---

function listarEjemplos(db, temaId) {
  return db.prepare('SELECT * FROM ejemplos WHERE tema_id = ? ORDER BY orden').all(temaId);
}

// --- Ejercicios y fotos ---

function listarEjercicios(db, temaId) {
  return db.prepare('SELECT * FROM ejercicios WHERE tema_id = ? ORDER BY orden').all(temaId);
}

function obtenerEjercicio(db, ejercicioId) {
  return db.prepare('SELECT * FROM ejercicios WHERE id = ?').get(ejercicioId);
}

function listarFotos(db, ejercicioId) {
  return db
    .prepare('SELECT * FROM fotos WHERE ejercicio_id = ? ORDER BY fecha_subida DESC')
    .all(ejercicioId);
}

function guardarFoto(db, ejercicioId, rutaArchivo, exifJson) {
  db.prepare('INSERT INTO fotos (ejercicio_id, ruta_archivo, exif_json) VALUES (?, ?, ?)').run(
    ejercicioId,
    rutaArchivo,
    exifJson
  );
}

function aprobarFoto(db, fotoId) {
  db.prepare("UPDATE fotos SET estado = 'aprobada' WHERE id = ?").run(fotoId);
}

function ejercicioCompletado(db, ejercicioId) {
  const fila = db
    .prepare("SELECT COUNT(*) AS c FROM fotos WHERE ejercicio_id = ? AND estado = 'aprobada'")
    .get(ejercicioId);
  return fila.c > 0;
}

// --- Evaluaciones y quiz ---

function listarEvaluaciones(db, temaId) {
  return db.prepare('SELECT * FROM evaluaciones WHERE tema_id = ? ORDER BY orden').all(temaId);
}

function obtenerPreguntas(db, evaluacionId) {
  const preguntas = db
    .prepare('SELECT * FROM preguntas_quiz WHERE evaluacion_id = ? ORDER BY orden')
    .all(evaluacionId);
  return preguntas.map((pregunta) => ({
    pregunta,
    alternativas: db.prepare('SELECT * FROM alternativas WHERE pregunta_id = ?').all(pregunta.id),
  }));
}

function registrarIntentoQuiz(db, evaluacionId, correctas, total, aprobado) {
  db.prepare(
    'INSERT INTO intentos_quiz (evaluacion_id, aprobado, correctas, total) VALUES (?, ?, ?, ?)'
  ).run(evaluacionId, aprobado ? 1 : 0, correctas, total);
}

function evaluacionAprobada(db, evaluacionId) {
  const fila = db
    .prepare('SELECT COUNT(*) AS c FROM intentos_quiz WHERE evaluacion_id = ? AND aprobado = 1')
    .get(evaluacionId);
  return fila.c > 0;
}

function ultimoIntento(db, evaluacionId) {
  return db
    .prepare('SELECT * FROM intentos_quiz WHERE evaluacion_id = ? ORDER BY fecha DESC LIMIT 1')
    .get(evaluacionId);
}

// --- Completitud de un tema ---

function temaCompletado(db, temaId) {
  const ejercicios = listarEjercicios(db, temaId);
  const evaluaciones = listarEvaluaciones(db, temaId);
  if (ejercicios.length === 0 && evaluaciones.length === 0) {
    return true;
  }
  const ejerciciosOk = ejercicios.every((e) => ejercicioCompletado(db, e.id));
  const evaluacionesOk = evaluaciones.every((ev) => evaluacionAprobada(db, ev.id));
  return ejerciciosOk && evaluacionesOk;
}

module.exports = {
  DB_PATH,
  abrirBaseDeDatos,
  obtenerCapituloPorSlug,
  obtenerSubcapituloPorSlug,
  obtenerTemaPorSlug,
  obtenerTema,
  arbolCompleto,
  listarEjemplos,
  listarEjercicios,
  obtenerEjercicio,
  listarFotos,
  guardarFoto,
  aprobarFoto,
  ejercicioCompletado,
  listarEvaluaciones,
  obtenerPreguntas,
  registrarIntentoQuiz,
  evaluacionAprobada,
  ultimoIntento,
  temaCompletado,
};
