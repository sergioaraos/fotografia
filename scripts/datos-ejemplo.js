// SERGIO 2026-09-20: contenido de prueba (capitulos, temas, ejercicios, evaluacion),
// portado 1:1 desde la version Python (database.py). Se expone como funcion para poder
// llamarla tanto desde scripts/seed-datos-ejemplo.js (npm run seed, uso manual en
// desarrollo) como desde server.js al arrancar, cuando la base de datos esta vacia
// (necesario en Cloudways, donde no hay acceso SSH para correr comandos a mano).
// No inserta nada si ya hay capitulos, para no duplicar datos en cada reinicio.
function cargarDatosEjemplo(db) {
  const yaHayDatos = db.prepare('SELECT COUNT(*) AS c FROM capitulos').get().c;
  if (yaHayDatos > 0) {
    return false;
  }

  const insertarCapitulo = db.prepare(
    'INSERT INTO capitulos (orden, titulo, slug, introduccion_md) VALUES (?, ?, ?, ?)'
  );
  const capId = insertarCapitulo.run(
    1,
    'Fundamentos de la exposicion',
    'fundamentos-exposicion',
    '**Datos de prueba.** Este capitulo cubre el triangulo de exposicion: apertura, velocidad e ISO, y como se relacionan para lograr una foto bien expuesta.'
  ).lastInsertRowid;

  const insertarSubcapitulo = db.prepare(
    'INSERT INTO subcapitulos (capitulo_id, orden, titulo, slug, introduccion_md) VALUES (?, ?, ?, ?, ?)'
  );
  const subId = insertarSubcapitulo.run(
    capId,
    1,
    'El triangulo de exposicion',
    'triangulo-exposicion',
    'Datos de prueba. Aqui vemos como interactuan apertura, velocidad e ISO.'
  ).lastInsertRowid;

  const insertarTema = db.prepare(
    'INSERT INTO temas (subcapitulo_id, orden, titulo, slug, teoria_md) VALUES (?, ?, ?, ?, ?)'
  );
  const tema1Id = insertarTema.run(
    subId,
    1,
    'Apertura y profundidad de campo',
    'apertura-profundidad-campo',
    'Datos de prueba.\n\nLa apertura (f/1.8, f/4, f/16...) controla cuanto se desenfoca el fondo. Un numero f bajo (f/1.8) desenfoca mucho el fondo, un numero f alto (f/16) mantiene todo nitido.'
  ).lastInsertRowid;

  db.prepare(
    'INSERT INTO ejemplos (tema_id, orden, descripcion, url_o_fuente) VALUES (?, ?, ?, ?)'
  ).run(tema1Id, 1, 'Dato de prueba: ejemplo de foto con fondo muy desenfocado (f/1.8)', 'https://example.com/ejemplo1');

  db.prepare(
    'INSERT INTO ejercicios (tema_id, orden, titulo, descripcion) VALUES (?, ?, ?, ?)'
  ).run(tema1Id, 1, 'Retrato con fondo desenfocado', 'Dato de prueba: fotografia un objeto con el diafragma mas abierto que tenga tu lente (f/1.8 con el 35mm).');

  const ev1Id = db.prepare(
    'INSERT INTO evaluaciones (tema_id, orden, titulo) VALUES (?, ?, ?)'
  ).run(tema1Id, 1, 'Evaluacion: apertura').lastInsertRowid;

  const p1Id = db.prepare(
    'INSERT INTO preguntas_quiz (evaluacion_id, orden, texto) VALUES (?, ?, ?)'
  ).run(ev1Id, 1, 'Dato de prueba: para desenfocar mas el fondo, uso...').lastInsertRowid;

  db.prepare(
    'INSERT INTO alternativas (pregunta_id, texto, es_correcta) VALUES (?, ?, ?)'
  ).run(p1Id, 'Un numero f bajo, como f/1.8', 1);
  db.prepare(
    'INSERT INTO alternativas (pregunta_id, texto, es_correcta) VALUES (?, ?, ?)'
  ).run(p1Id, 'Un numero f alto, como f/16', 0);

  db.prepare(
    'INSERT INTO temas (subcapitulo_id, orden, titulo, slug, teoria_md) VALUES (?, ?, ?, ?, ?)'
  ).run(subId, 2, 'Velocidad de obturacion', 'velocidad-obturacion', 'Datos de prueba. Este tema esta bloqueado hasta completar el anterior.');

  return true;
}

module.exports = { cargarDatosEjemplo };
