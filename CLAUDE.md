# CLAUDE.md — Notas del proyecto

## Reglas de trabajo (INNEGOCIABLES)

> ⚠️ Estas reglas se aplican siempre, sin excepción. No ejecutar nada sin seguirlas.

### 1. Flujo de trabajo con Git

- **Nunca trabajar directo en `main` o `master`**. Todo cambio va en un feature branch.
- Nombre del branch: `feature/<descripcion-corta>` (ej: `feature/user-country-password`)
- Crear el branch antes de tocar cualquier archivo: `git checkout -b feature/...`
- Un commit por grupo lógico de cambios, no todo junto al final.
- Formato de commit: `tipo(scope): descripción` — ej: `feat(users): add country selector`
- Antes de commitear, verificar con `git diff` que solo van los archivos correctos.
- Al terminar, hacer push y abrir PR hacia `main`: `git push origin feature/...`

### 2. Comentarios en el código

- **Todo bloque de código nuevo o modificado debe tener un comentario** que empiece con:
  ```
  // SERGIO YYYY-MM-DD: explicación del cambio y por qué se hizo
  ```
- Sin fecha = comentario incompleto. No commitear sin revisarlo.

### 3. Planificación antes de ejecutar

- Ante cualquier tarea que involucre más de un archivo o más de un paso, **primero presentar el plan completo** (qué archivos, qué cambios, en qué orden).
- **Esperar autorización explícita** ("dale", "autorizado", "sí") antes de ejecutar cualquier cambio.
- No asumir que una respuesta afirmativa sobre el plan autoriza pasos adicionales no discutidos.

### 4. Verificación antes de commitear

- Revisar que todos los archivos modificados tienen comentarios `SERGIO + fecha`.
- Ejecutar `git diff` y leer el resultado completo antes de proponer el commit.
- Si hay dudas sobre algún cambio, preguntar antes de incluirlo.
- **Probar el cambio antes de comitear.** Este paso es siempre obligatorio: esperar la prueba (manual y/o automatizada) y el OK explícito del usuario antes de proponer el commit.
- Dar instrucciones claras de cómo probar manualmente el cambio (pasos, endpoint o pantalla a usar, datos de prueba).

### 5. Un cambio a la vez

- No acumular múltiples features sin commitear.
- Si surge algo nuevo mientras se trabaja en una feature, anotarlo y terminarlo después — no mezclar.

### 6. Pruebas automatizadas

- **Siempre** preparar un set de pruebas unitarias y pruebas de integración para los cambios realizados.
- Adaptar los tests existentes a los nuevos cambios cuando un cambio modifique un comportamiento ya cubierto por tests previos.

### 7. Idioma de comunicación

- Comunicarse siempre en **español neutro** (no argentino, sin voseo ni regionalismos).

### 8. Autoverificación

- Siempre verificar las respuestas y contrastarlas contra las reglas de este documento antes de entregarlas.

---



## Bitácora del proyecto

Este proyecto se sigue en el gestor de proyectos personal. Al cerrar una sesión de trabajo con cambios relevantes, agrega una entrada a BITACORA.md siguiendo el formato descrito en su encabezado.
