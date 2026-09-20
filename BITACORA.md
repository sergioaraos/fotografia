# Bitácora — Aprender Fotografia de Cero

Instrucciones para la herramienta que trabaje en este proyecto: antes de empezar, revisa la última entrada para saber en qué se quedó. Al terminar una sesión de trabajo con cambios relevantes, agrega una entrada nueva al final de este archivo (no edites entradas anteriores) con este formato exacto:

## AAAA-MM-DD HH:MM — <herramienta>
Estado: <en progreso | bloqueado | terminado>
Resumen: <2 a 4 líneas de qué se hizo>
Archivos/carpetas tocados: <lista breve>
Recursos/URLs/config: <si aplica, si no, omitir la línea>
Pendientes: <qué queda para la próxima sesión>

---

## 2026-09-20 15:14 — Claude
Estado: en progreso
Resumen: esqueleto inicial de la app (FastAPI + SQLite + Jinja2), sin contenido de fotografia todavia. Modelo de datos: capitulos -> ejercicios (quiz o foto) -> progreso. Un capitulo se desbloquea solo cuando el anterior queda completo. Un quiz se aprueba solo con las 5 preguntas correctas (sin reintentos en los primeros 10 minutos, para obligar a releer la teoria). Una foto queda "pendiente" hasta que se revisa en el chat y se aprueba manualmente. Branch feature/esqueleto-app, 7 tests automatizados escritos, pendiente correrlos y probar en el navegador.
Archivos/carpetas tocados: main.py, database.py, progreso.py, exif_utils.py, config.py, templates/base.html, templates/index.html, templates/capitulo.html, static/style.css, requirements.txt, .gitignore, tests/test_database.py, tests/test_main.py
Pendientes: correr los tests y probar manualmente en el navegador (Sergio), luego commit. Cargar el capitulo 1 con teoria, ejercicios y quiz. Ver mas adelante contenido de post produccion en Lightroom y modo escena de la Z5 II.

## 2026-09-20 16:10 — Claude
Estado: en progreso
Resumen: se reestructuro el modelo a capitulo -> subcapitulo -> tema (menu en acordeon), con 5 tabs por tema (Teoria, Ejemplos, Ejercicios, Fotos, Evaluacion). Capitulo y subcapitulo solo muestran introduccion. Desbloqueo secuencial por tema en todo el arbol. Se aplico diseno moderno (tabs de colores con icono por seccion, chevrons animados, tarjetas con sombra) y se corrigieron dos bugs de navegacion en el acordeon (capitulo padre no quedaba abierto al ver un tema; pagina activa no se resaltaba en capitulo/subcapitulo). Se cargaron datos de prueba locales (no versionados) para revisar la interfaz: 1 capitulo, 1 subcapitulo, 2 temas. 11 tests automatizados. Branch feature/estructura-capitulo-subcapitulo-tema mergeado a main.
Archivos/carpetas tocados: database.py, main.py, progreso.py, static/style.css, templates/base.html, templates/capitulo.html, templates/subcapitulo.html, templates/tema.html, tests/test_database.py, tests/test_main.py, tests/test_progreso.py
Pendientes: cargar el contenido real del capitulo 1 (reemplazando los datos de prueba), definir con Sergio el primer tema (apertura y profundidad de campo, segun lo conversado), y armar las evaluaciones reales de 5 preguntas.

## 2026-09-20 17:24 — Claude
Estado: en progreso
Resumen: se porto la app completa de Python/FastAPI a Node.js/Express (Cloudways Velocity Server no soporta Python), manteniendo la misma logica de negocio (desbloqueo secuencial, quiz todo-o-nada, aprobacion de fotos), siguiendo el patron del proyecto TecnoRegistros (Express + EJS + better-sqlite3 + express-session). Se agrego login con variables de entorno (APP_LOGIN_USER/APP_LOGIN_PASSWORD/SESSION_SECRET) para el despliegue en fotografia.araos.net. Se agregaron 12 tests automatizados (node --test + supertest). Bug encontrado y corregido durante la prueba manual: faltaba la dependencia dotenv, asi que server.js nunca leia el archivo .env (PORT/credenciales quedaban siempre en su valor por defecto). Tambien se recupero un script para recargar los datos de prueba (scripts/seed-datos-ejemplo.js, "npm run seed"), despues de que se perdieran por un borrado accidental de data/aprender_fotografia.db durante pruebas en un ambiente aislado. Probado manualmente por Sergio en su navegador: login, menu en acordeon y los 5 tabs de colores funcionando. Branch feature/port-a-nodejs mergeado a main y pusheado a github.com/sergioaraos/fotografia.
Archivos/carpetas tocados: se eliminaron main.py, database.py, progreso.py, exif_utils.py, config.py, requirements.txt, templates/*.html, static/style.css, tests/test_*.py; se agregaron package.json, server.js, db.js, progreso.js, version.js, middleware/auth.js, routes/contenido.js, migrations/schema.sql, scripts/seed-datos-ejemplo.js, views/*.ejs, public/style.css, tests/db.test.js, tests/server.test.js, .env.example
Recursos/URLs/config: repo github.com/sergioaraos/fotografia (main); destino de despliegue fotografia.araos.net en Cloudways Velocity Server
Pendientes: crear la app en Cloudways (tipo Express/Node, Node v24, variables de entorno APP_LOGIN_USER/APP_LOGIN_PASSWORD/SESSION_SECRET/PORT via la UI de Cloudways), configurar el dominio fotografia.araos.net y verificar que el deploy automatico con git push funcione. Despues, reemplazar los datos de prueba por el contenido real del capitulo 1 (apertura y profundidad de campo). Pendiente tambien Lightroom Classic y modo escena de la Z5 II.
