// SERGIO 2026-09-20: pruebas del modelo de datos y del desbloqueo secuencial
// (feature/port-a-nodejs, portado de test_database.py y test_progreso.py)
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const db = require('../db');
const progreso = require('../progreso');

function nuevaBaseDeDatos() {
  const archivo = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'foto-test-')), 'test.db');
  return db.abrirBaseDeDatos(archivo);
}

function crearArbolBasico(conn, { conEjercicio = true, conEvaluacion = true } = {}) {
  conn.exec("INSERT INTO capitulos (orden, titulo, slug) VALUES (1, 'Cap 1', 'cap-1')");
  const capituloId = conn.prepare("SELECT id FROM capitulos WHERE slug = 'cap-1'").get().id;
  conn
    .prepare("INSERT INTO subcapitulos (capitulo_id, orden, titulo, slug) VALUES (?, 1, 'Sub 1', 'sub-1')")
    .run(capituloId);
  const subcapituloId = conn.prepare("SELECT id FROM subcapitulos WHERE slug = 'sub-1'").get().id;
  conn
    .prepare("INSERT INTO temas (subcapitulo_id, orden, titulo, slug) VALUES (?, 1, 'Tema 1', 'tema-1')")
    .run(subcapituloId);
  const temaId = conn.prepare("SELECT id FROM temas WHERE slug = 'tema-1'").get().id;

  let ejercicioId = null;
  if (conEjercicio) {
    conn.prepare("INSERT INTO ejercicios (tema_id, orden, titulo) VALUES (?, 1, 'Ejercicio 1')").run(temaId);
    ejercicioId = conn.prepare('SELECT id FROM ejercicios WHERE tema_id = ?').get(temaId).id;
  }

  let evaluacionId = null;
  if (conEvaluacion) {
    conn.prepare("INSERT INTO evaluaciones (tema_id, orden, titulo) VALUES (?, 1, 'Evaluacion 1')").run(temaId);
    evaluacionId = conn.prepare('SELECT id FROM evaluaciones WHERE tema_id = ?').get(temaId).id;
  }

  return { capituloId, subcapituloId, temaId, ejercicioId, evaluacionId };
}

test('init crea todas las tablas', () => {
  const conn = nuevaBaseDeDatos();
  const tablas = conn
    .prepare("SELECT name FROM sqlite_master WHERE type = 'table'")
    .all()
    .map((f) => f.name);
  const esperadas = [
    'capitulos', 'subcapitulos', 'temas', 'ejemplos', 'ejercicios',
    'fotos', 'evaluaciones', 'preguntas_quiz', 'alternativas', 'intentos_quiz',
  ];
  for (const tabla of esperadas) {
    assert.ok(tablas.includes(tabla), `falta la tabla ${tabla}`);
  }
});

test('ejercicio se completa con foto aprobada', () => {
  const conn = nuevaBaseDeDatos();
  const { ejercicioId } = crearArbolBasico(conn, { conEvaluacion: false });

  assert.equal(db.ejercicioCompletado(conn, ejercicioId), false);
  db.guardarFoto(conn, ejercicioId, 'foto.jpg', '{}');
  const fotoId = db.listarFotos(conn, ejercicioId)[0].id;
  assert.equal(db.ejercicioCompletado(conn, ejercicioId), false);

  db.aprobarFoto(conn, fotoId);
  assert.equal(db.ejercicioCompletado(conn, ejercicioId), true);
});

test('evaluacion se aprueba solo con intento correcto', () => {
  const conn = nuevaBaseDeDatos();
  const { evaluacionId } = crearArbolBasico(conn, { conEjercicio: false });

  db.registrarIntentoQuiz(conn, evaluacionId, 4, 5, false);
  assert.equal(db.evaluacionAprobada(conn, evaluacionId), false);

  db.registrarIntentoQuiz(conn, evaluacionId, 5, 5, true);
  assert.equal(db.evaluacionAprobada(conn, evaluacionId), true);
});

test('tema completado requiere ejercicios y evaluaciones', () => {
  const conn = nuevaBaseDeDatos();
  const { temaId, ejercicioId, evaluacionId } = crearArbolBasico(conn);

  assert.equal(db.temaCompletado(conn, temaId), false);

  db.guardarFoto(conn, ejercicioId, 'foto.jpg', '{}');
  db.aprobarFoto(conn, db.listarFotos(conn, ejercicioId)[0].id);
  assert.equal(db.temaCompletado(conn, temaId), false);

  db.registrarIntentoQuiz(conn, evaluacionId, 5, 5, true);
  assert.equal(db.temaCompletado(conn, temaId), true);
});

test('tema sin ejercicios ni evaluacion se considera completo', () => {
  const conn = nuevaBaseDeDatos();
  const { temaId } = crearArbolBasico(conn, { conEjercicio: false, conEvaluacion: false });
  assert.equal(db.temaCompletado(conn, temaId), true);
});

test('segundo tema queda bloqueado hasta completar el primero', () => {
  const conn = nuevaBaseDeDatos();
  conn.exec("INSERT INTO capitulos (orden, titulo, slug) VALUES (1, 'Cap 1', 'cap-1')");
  const capituloId = conn.prepare("SELECT id FROM capitulos WHERE slug = 'cap-1'").get().id;
  conn
    .prepare("INSERT INTO subcapitulos (capitulo_id, orden, titulo, slug) VALUES (?, 1, 'Sub 1', 'sub-1')")
    .run(capituloId);
  const subcapituloId = conn.prepare("SELECT id FROM subcapitulos WHERE slug = 'sub-1'").get().id;
  conn
    .prepare("INSERT INTO temas (subcapitulo_id, orden, titulo, slug) VALUES (?, 1, 'Tema 1', 'tema-1')")
    .run(subcapituloId);
  conn
    .prepare("INSERT INTO temas (subcapitulo_id, orden, titulo, slug) VALUES (?, 2, 'Tema 2', 'tema-2')")
    .run(subcapituloId);
  const tema1Id = conn.prepare("SELECT id FROM temas WHERE slug = 'tema-1'").get().id;
  conn.prepare("INSERT INTO evaluaciones (tema_id, orden, titulo) VALUES (?, 1, 'Evaluacion 1')").run(tema1Id);
  const evaluacionId = conn.prepare('SELECT id FROM evaluaciones WHERE tema_id = ?').get(tema1Id).id;

  assert.equal(progreso.temaDesbloqueado(conn, 'tema-1'), true);
  assert.equal(progreso.temaDesbloqueado(conn, 'tema-2'), false);

  db.registrarIntentoQuiz(conn, evaluacionId, 5, 5, true);
  assert.equal(progreso.temaDesbloqueado(conn, 'tema-2'), true);
});
