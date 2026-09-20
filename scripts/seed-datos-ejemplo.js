// SERGIO 2026-09-20: wrapper de linea de comandos para scripts/datos-ejemplo.js, para
// cargar los datos de ejemplo a mano en desarrollo con "npm run seed". La logica de los
// datos vive en datos-ejemplo.js porque tambien la usa server.js al arrancar (necesario
// en Cloudways, donde no hay acceso SSH para correr este script a mano).
const path = require('path');
const Database = require('better-sqlite3');
const { cargarDatosEjemplo } = require('./datos-ejemplo');

const DB_PATH = path.join(__dirname, '..', 'data', 'aprender_fotografia.db');
const db = new Database(DB_PATH);
db.pragma('foreign_keys = ON');

const inserto = cargarDatosEjemplo(db);
console.log(inserto ? 'Datos de ejemplo cargados.' : 'Ya hay capitulos cargados, no se inserta nada (para no duplicar).');

db.close();
