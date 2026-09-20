// SERGIO 2026-09-20: pruebas de integracion de las rutas HTTP (feature/port-a-nodejs,
// portado de test_main.py). Se fija DB_PATH y PORT antes de requerir server.js para
// que use una base de datos temporal propia y no choque con la real.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const DB_TEST_PATH = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'foto-test-server-')), 'test.db');
process.env.DB_PATH = DB_TEST_PATH;
process.env.PORT = '0';
process.env.APP_LOGIN_USER = 'test';
process.env.APP_LOGIN_PASSWORD = 'test1234';
process.env.SESSION_SECRET = 'secreto-de-test';

const request = require('supertest');
const app = require('../server');
const db = require('../db');

const conn = db.abrirBaseDeDatos(DB_TEST_PATH);

async function agenteAutenticado() {
  const agente = request.agent(app);
  await agente.post('/login').send({ usuario: 'test', password: 'test1234' });
  return agente;
}

test('sin sesion, el contenido redirige al login', async () => {
  const respuesta = await request(app).get('/');
  assert.equal(respuesta.status, 302);
  assert.match(respuesta.headers.location, /\/login/);
});

test('login con credenciales correctas da acceso', async () => {
  const agente = await agenteAutenticado();
  const respuesta = await agente.get('/');
  assert.equal(respuesta.status, 200);
  assert.match(respuesta.text, /Aprender Fotografia de Cero/);
});

test('login con credenciales incorrectas no da acceso', async () => {
  const respuesta = await request(app).post('/login').send({ usuario: 'test', password: 'mala' });
  assert.match(respuesta.text, /incorrectos/);
});

test('tema inexistente da 404', async () => {
  const agente = await agenteAutenticado();
  const respuesta = await agente.get('/tema/no-existe');
  assert.equal(respuesta.status, 404);
});

test('capitulo muestra su introduccion', async () => {
  conn.exec(
    "INSERT INTO capitulos (orden, titulo, slug, introduccion_md) VALUES (1, 'Cap 1', 'cap-http-1', 'resumen del capitulo')"
  );
  const agente = await agenteAutenticado();
  const respuesta = await agente.get('/capitulo/cap-http-1');
  assert.equal(respuesta.status, 200);
  assert.match(respuesta.text, /resumen del capitulo/);
});

test('segundo tema bloqueado no muestra su teoria, y el capitulo padre queda marcado como abierto', async () => {
  conn.exec("INSERT INTO capitulos (orden, titulo, slug) VALUES (2, 'Cap 2', 'cap-http-2')");
  const capituloId = conn.prepare("SELECT id FROM capitulos WHERE slug = 'cap-http-2'").get().id;
  conn
    .prepare("INSERT INTO subcapitulos (capitulo_id, orden, titulo, slug) VALUES (?, 1, 'Sub 1', 'sub-http-1')")
    .run(capituloId);
  const subcapituloId = conn.prepare("SELECT id FROM subcapitulos WHERE slug = 'sub-http-1'").get().id;
  conn
    .prepare(
      "INSERT INTO temas (subcapitulo_id, orden, titulo, slug, teoria_md) VALUES (?, 1, 'Tema 1', 'tema-http-1', 'texto')"
    )
    .run(subcapituloId);
  conn
    .prepare(
      "INSERT INTO temas (subcapitulo_id, orden, titulo, slug, teoria_md) VALUES (?, 2, 'Tema 2', 'tema-http-2', 'secreto')"
    )
    .run(subcapituloId);
  const tema1Id = conn.prepare("SELECT id FROM temas WHERE slug = 'tema-http-1'").get().id;
  // SERGIO 2026-09-20: sin esto el tema 1 se considera completo por no tener nada que
  // hacer, y el tema 2 quedaria desbloqueado sin querer en este test
  conn.prepare("INSERT INTO evaluaciones (tema_id, orden, titulo) VALUES (?, 1, 'Evaluacion 1')").run(tema1Id);

  const agente = await agenteAutenticado();
  const respuesta = await agente.get('/tema/tema-http-2');
  assert.equal(respuesta.status, 200);
  assert.match(respuesta.text.toLowerCase(), /bloqueado/);
  assert.doesNotMatch(respuesta.text, /secreto/);
  // SERGIO 2026-09-20: regresion del bug donde el <details> del capitulo padre no
  // quedaba abierto y ocultaba el subcapitulo/tema activo
  assert.match(respuesta.text, /<details class="capitulo" open>/);
});
