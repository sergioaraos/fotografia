// SERGIO 2026-09-20: servidor Express, portado desde main.py (FastAPI)
// (feature/port-a-nodejs)
// SERGIO 2026-09-20: carga el archivo .env a process.env. Sin esto, Node ignora el .env
// por completo y PORT/APP_LOGIN_USER/APP_LOGIN_PASSWORD/SESSION_SECRET quedan siempre
// undefined (esto causo el bug donde PORT=3010 en .env no tenia ningun efecto y el
// servidor seguia intentando usar el puerto 3000 por defecto).
require('dotenv').config();
const express = require('express');
const session = require('express-session');
const path = require('path');

const db = require('./db');
const { COMMIT, INICIO_SERVIDOR } = require('./version');
const { requireAuth } = require('./middleware/auth');

const conn = db.abrirBaseDeDatos();

const SqliteStore = require('better-sqlite3-session-store')(session);
const crearRutasContenido = require('./routes/contenido');

const app = express();
const PORT = process.env.PORT || 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use((req, res, next) => {
  res.locals.version = COMMIT;
  res.locals.inicioServidor = INICIO_SERVIDOR;
  next();
});

app.use('/static', express.static(path.join(__dirname, 'public')));
app.use(
  '/uploads',
  requireAuth,
  express.static(process.env.UPLOADS_DIR || path.join(__dirname, 'uploads'))
);

app.use(
  session({
    store: new SqliteStore({
      client: conn,
      expired: { clear: true, intervalMs: 15 * 60 * 1000 },
    }),
    secret: process.env.SESSION_SECRET || 'cambiar-este-secreto-en-produccion',
    resave: false,
    saveUninitialized: false,
    cookie: { maxAge: 30 * 24 * 60 * 60 * 1000 },
  })
);

app.get('/login', (req, res) => {
  if (req.session && req.session.autenticado) {
    return res.redirect('/');
  }
  res.render('login', { error: null });
});

app.post('/login', (req, res) => {
  const { usuario, password } = req.body || {};
  const usuarioOk = process.env.APP_LOGIN_USER;
  const passwordOk = process.env.APP_LOGIN_PASSWORD;

  if (!usuarioOk || !passwordOk) {
    return res.render('login', { error: 'El servidor no tiene configurado el login (variables de entorno faltantes)' });
  }
  if (usuario !== usuarioOk || password !== passwordOk) {
    return res.render('login', { error: 'Usuario o contrasena incorrectos' });
  }

  req.session.autenticado = true;
  res.redirect('/');
});

app.post('/logout', (req, res) => {
  req.session.destroy(() => res.redirect('/login'));
});

app.use('/', requireAuth, crearRutasContenido(conn));

// SERGIO 2026-09-20: solo escucha si se ejecuta directamente (npm start), no cuando
// los tests hacen require('../server') para usar supertest, asi el proceso de tests
// puede terminar solo en vez de quedar colgado esperando que el puerto se cierre
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Servidor escuchando en el puerto ${PORT}`);
  });
}

module.exports = app;
