// SERGIO 2026-09-20: login simple contra variables de entorno, sin tabla de usuarios
// porque la app es solo para Sergio (feature/port-a-nodejs)
function requireAuth(req, res, next) {
  if (req.session && req.session.autenticado) {
    return next();
  }
  return res.redirect('/login');
}

module.exports = { requireAuth };
