// SERGIO 2026-09-20: mismo patron que TecnoRegistros para confirmar a simple vista
// que un deploy quedo activo (Cloudways no incluye .git en el despliegue, asi que
// el commit no siempre se puede leer) (feature/port-a-nodejs)
const { execSync } = require('child_process');

let commit = 'desconocido';
try {
  commit = execSync('git rev-parse --short HEAD', { cwd: __dirname }).toString().trim();
} catch (err) {
  // sin .git disponible (por ejemplo en un deploy de Cloudways), se deja "desconocido"
}

module.exports = { COMMIT: commit, INICIO_SERVIDOR: new Date().toISOString() };
