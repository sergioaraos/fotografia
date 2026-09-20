// SERGIO 2026-09-20: rutas de capitulo, subcapitulo, tema, ejercicios y evaluaciones
// (feature/port-a-nodejs, portado de main.py)
const express = require('express');
const fs = require('fs');
const path = require('path');
const multer = require('multer');
const { marked } = require('marked');
const exifr = require('exifr');

const db = require('../db');
const progreso = require('../progreso');

const UPLOADS_DIR = process.env.UPLOADS_DIR || path.join(__dirname, '..', 'uploads');

function contextoMenu(conn, extra = {}) {
  return {
    arbol: progreso.arbolConEstado(conn),
    activeCapituloId: null,
    activeSubcapituloId: null,
    activeTemaId: null,
    paginaActualTipo: null,
    paginaActualId: null,
    error: null,
    ...extra,
  };
}

async function extraerExif(rutaArchivo) {
  try {
    const datos = await exifr.parse(rutaArchivo, {
      pick: ['Make', 'Model', 'LensModel', 'FNumber', 'ExposureTime', 'ISO', 'FocalLength'],
    });
    if (!datos) return {};
    return {
      camara: datos.Model,
      lente: datos.LensModel,
      apertura: datos.FNumber ? `f/${datos.FNumber}` : undefined,
      velocidad: datos.ExposureTime ? `${datos.ExposureTime}s` : undefined,
      iso: datos.ISO,
      distancia_focal: datos.FocalLength ? `${datos.FocalLength}mm` : undefined,
    };
  } catch (err) {
    return {};
  }
}

function temaDeEjercicio(conn, ejercicioId) {
  return conn
    .prepare(
      'SELECT temas.* FROM temas JOIN ejercicios ON ejercicios.tema_id = temas.id WHERE ejercicios.id = ?'
    )
    .get(ejercicioId);
}

function temaDeEvaluacion(conn, evaluacionId) {
  return conn
    .prepare(
      'SELECT temas.* FROM temas JOIN evaluaciones ON evaluaciones.tema_id = temas.id WHERE evaluaciones.id = ?'
    )
    .get(evaluacionId);
}

module.exports = function crearRutasContenido(conn) {
  const router = express.Router();

  const storage = multer.diskStorage({
    destination: (req, file, cb) => {
      const carpeta = path.join(UPLOADS_DIR, String(req.params.ejercicioId));
      fs.mkdirSync(carpeta, { recursive: true });
      cb(null, carpeta);
    },
    filename: (req, file, cb) => cb(null, file.originalname),
  });
  const upload = multer({ storage });

  router.get('/', (req, res) => {
    res.render('index', contextoMenu(conn));
  });

  router.get('/capitulo/:slug', (req, res) => {
    const capitulo = db.obtenerCapituloPorSlug(conn, req.params.slug);
    if (!capitulo) {
      return res
        .status(404)
        .render('index', contextoMenu(conn, { error: 'Capitulo no encontrado' }));
    }
    res.render(
      'capitulo',
      contextoMenu(conn, {
        capitulo,
        introduccionHtml: marked.parse(capitulo.introduccion_md || ''),
        activeCapituloId: capitulo.id,
        activeSubcapituloId: null,
        activeTemaId: null,
        paginaActualTipo: 'capitulo',
        paginaActualId: capitulo.id,
      })
    );
  });

  router.get('/subcapitulo/:slug', (req, res) => {
    const subcapitulo = db.obtenerSubcapituloPorSlug(conn, req.params.slug);
    if (!subcapitulo) {
      return res
        .status(404)
        .render('index', contextoMenu(conn, { error: 'Subcapitulo no encontrado' }));
    }
    res.render(
      'subcapitulo',
      contextoMenu(conn, {
        subcapitulo,
        introduccionHtml: marked.parse(subcapitulo.introduccion_md || ''),
        activeCapituloId: subcapitulo.capitulo_id,
        activeSubcapituloId: subcapitulo.id,
        activeTemaId: null,
        paginaActualTipo: 'subcapitulo',
        paginaActualId: subcapitulo.id,
      })
    );
  });

  router.get('/tema/:slug', (req, res) => {
    const tema = db.obtenerTemaPorSlug(conn, req.params.slug);
    if (!tema) {
      return res.status(404).render('index', contextoMenu(conn, { error: 'Tema no encontrado' }));
    }

    const capituloIdFila = conn
      .prepare('SELECT capitulo_id FROM subcapitulos WHERE id = ?')
      .get(tema.subcapitulo_id);

    const desbloqueado = progreso.temaDesbloqueado(conn, req.params.slug);
    const tab = req.query.tab || 'teoria';

    const base = {
      tema,
      activeTemaId: tema.id,
      // SERGIO 2026-09-20: sin esto el <details> del capitulo queda cerrado y oculta
      // el subcapitulo abierto que tiene adentro (bug encontrado en la version Python)
      activeCapituloId: capituloIdFila ? capituloIdFila.capitulo_id : null,
      activeSubcapituloId: tema.subcapitulo_id,
      paginaActualTipo: null,
      paginaActualId: null,
      bloqueado: !desbloqueado,
      tab,
    };

    if (!desbloqueado) {
      return res.render('tema', contextoMenu(conn, base));
    }

    const ejercicios = db.listarEjercicios(conn, tema.id).map((ejercicio) => ({
      ejercicio,
      completado: db.ejercicioCompletado(conn, ejercicio.id),
      fotos: db.listarFotos(conn, ejercicio.id),
    }));

    const evaluaciones = db.listarEvaluaciones(conn, tema.id).map((evaluacion) => ({
      evaluacion,
      aprobada: db.evaluacionAprobada(conn, evaluacion.id),
      preguntas: db.obtenerPreguntas(conn, evaluacion.id),
      ultimoIntento: db.ultimoIntento(conn, evaluacion.id),
    }));

    res.render(
      'tema',
      contextoMenu(conn, {
        ...base,
        teoriaHtml: marked.parse(tema.teoria_md || ''),
        ejemplos: db.listarEjemplos(conn, tema.id),
        ejercicios,
        evaluaciones,
      })
    );
  });

  router.post('/ejercicios/:ejercicioId/foto', upload.single('foto'), async (req, res) => {
    const ejercicioId = Number(req.params.ejercicioId);
    const tema = temaDeEjercicio(conn, ejercicioId);

    const exif = await extraerExif(req.file.path);
    const rutaRelativa = `${ejercicioId}/${req.file.filename}`;
    db.guardarFoto(conn, ejercicioId, rutaRelativa, JSON.stringify(exif));

    res.redirect(`/tema/${tema.slug}?tab=fotos`);
  });

  router.post('/fotos/:fotoId/aprobar', (req, res) => {
    const foto = conn.prepare('SELECT * FROM fotos WHERE id = ?').get(req.params.fotoId);
    const tema = foto ? temaDeEjercicio(conn, foto.ejercicio_id) : null;

    db.aprobarFoto(conn, req.params.fotoId);

    if (tema) {
      return res.redirect(`/tema/${tema.slug}?tab=fotos`);
    }
    res.redirect('/');
  });

  router.post('/evaluaciones/:evaluacionId/responder', (req, res) => {
    const evaluacionId = Number(req.params.evaluacionId);
    const tema = temaDeEvaluacion(conn, evaluacionId);
    const preguntas = db.obtenerPreguntas(conn, evaluacionId);

    let correctas = 0;
    for (const item of preguntas) {
      const elegida = req.body[`pregunta_${item.pregunta.id}`];
      for (const alternativa of item.alternativas) {
        if (alternativa.es_correcta && String(alternativa.id) === elegida) {
          correctas += 1;
        }
      }
    }

    const total = preguntas.length;
    // SERGIO 2026-09-20: se aprueba solo si TODAS las preguntas quedan correctas
    const aprobado = total > 0 && correctas === total;
    db.registrarIntentoQuiz(conn, evaluacionId, correctas, total, aprobado);

    res.redirect(`/tema/${tema.slug}?tab=evaluacion`);
  });

  return router;
};
