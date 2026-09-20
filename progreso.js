// SERGIO 2026-09-20: bloqueo secuencial a nivel de tema, cruzando subcapitulos y
// capitulos en un unico orden (feature/port-a-nodejs, portado de progreso.py)
const db = require('./db');

function temasEnOrden(conn) {
  const lista = [];
  for (const cap of db.arbolCompleto(conn)) {
    for (const sub of cap.subcapitulos) {
      for (const tema of sub.temas) {
        lista.push({ tema, capitulo: cap.capitulo, subcapitulo: sub.subcapitulo });
      }
    }
  }
  return lista;
}

function estadoTemas(conn) {
  const resultado = [];
  let anteriorCompletado = true;
  for (const item of temasEnOrden(conn)) {
    const completado = db.temaCompletado(conn, item.tema.id);
    const desbloqueado = anteriorCompletado;
    resultado.push({ ...item, completado, desbloqueado });
    anteriorCompletado = completado;
  }
  return resultado;
}

function temaDesbloqueado(conn, slug) {
  const item = estadoTemas(conn).find((it) => it.tema.slug === slug);
  return item ? item.desbloqueado : false;
}

function arbolConEstado(conn) {
  const estados = new Map(estadoTemas(conn).map((it) => [it.tema.id, it]));
  return db.arbolCompleto(conn).map((cap) => ({
    capitulo: cap.capitulo,
    subcapitulos: cap.subcapitulos.map((sub) => ({
      subcapitulo: sub.subcapitulo,
      temas: sub.temas.map((tema) => {
        const info = estados.get(tema.id) || { completado: false, desbloqueado: false };
        return { tema, completado: info.completado, desbloqueado: info.desbloqueado };
      }),
    })),
  }));
}

module.exports = { temasEnOrden, estadoTemas, temaDesbloqueado, arbolConEstado };
