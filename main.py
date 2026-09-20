# SERGIO 2026-09-20: rutas reestructuradas en capitulo -> subcapitulo -> tema, con
# 5 tabs por tema (teoria, ejemplos, ejercicios, fotos, evaluacion)
# (feature/estructura-capitulo-subcapitulo-tema)
import shutil
from pathlib import Path

import markdown
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
import database
import exif_utils
import progreso

app = FastAPI(title="Aprender Fotografia de Cero")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=config.UPLOADS_DIR), name="uploads")


@app.on_event("startup")
def on_startup():
    database.init_db()


def _contexto_menu():
    return {"arbol": progreso.arbol_con_estado()}


def _tema_de_ejercicio(ejercicio_id):
    conn = database.get_connection()
    fila = conn.execute(
        "SELECT temas.* FROM temas JOIN ejercicios ON ejercicios.tema_id = temas.id WHERE ejercicios.id = ?",
        (ejercicio_id,),
    ).fetchone()
    conn.close()
    return fila


def _tema_de_evaluacion(evaluacion_id):
    conn = database.get_connection()
    fila = conn.execute(
        "SELECT temas.* FROM temas JOIN evaluaciones ON evaluaciones.tema_id = temas.id WHERE evaluaciones.id = ?",
        (evaluacion_id,),
    ).fetchone()
    conn.close()
    return fila


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", _contexto_menu())


@app.get("/capitulo/{slug}")
def ver_capitulo(request: Request, slug: str):
    capitulo = database.obtener_capitulo_por_slug(slug)
    if not capitulo:
        return templates.TemplateResponse(
            request, "index.html", {**_contexto_menu(), "error": "Capitulo no encontrado"}, status_code=404
        )
    contexto = {
        **_contexto_menu(),
        "capitulo": capitulo,
        "introduccion_html": markdown.markdown(capitulo["introduccion_md"] or ""),
        "active_capitulo_id": capitulo["id"],
        # SERGIO 2026-09-20: distingue "acordeon abierto" de "pagina que se esta viendo"
        "pagina_actual_tipo": "capitulo",
        "pagina_actual_id": capitulo["id"],
    }
    return templates.TemplateResponse(request, "capitulo.html", contexto)


@app.get("/subcapitulo/{slug}")
def ver_subcapitulo(request: Request, slug: str):
    subcapitulo = database.obtener_subcapitulo_por_slug(slug)
    if not subcapitulo:
        return templates.TemplateResponse(
            request, "index.html", {**_contexto_menu(), "error": "Subcapitulo no encontrado"}, status_code=404
        )
    contexto = {
        **_contexto_menu(),
        "subcapitulo": subcapitulo,
        "introduccion_html": markdown.markdown(subcapitulo["introduccion_md"] or ""),
        "active_capitulo_id": subcapitulo["capitulo_id"],
        "active_subcapitulo_id": subcapitulo["id"],
        "pagina_actual_tipo": "subcapitulo",
        "pagina_actual_id": subcapitulo["id"],
    }
    return templates.TemplateResponse(request, "subcapitulo.html", contexto)


@app.get("/tema/{slug}")
def ver_tema(request: Request, slug: str, tab: str = "teoria"):
    tema = database.obtener_tema_por_slug(slug)
    if not tema:
        return templates.TemplateResponse(
            request, "index.html", {**_contexto_menu(), "error": "Tema no encontrado"}, status_code=404
        )

    conn = database.get_connection()
    capitulo_id_fila = conn.execute(
        "SELECT capitulo_id FROM subcapitulos WHERE id = ?", (tema["subcapitulo_id"],)
    ).fetchone()
    conn.close()

    desbloqueado = progreso.tema_desbloqueado(slug)
    contexto = {
        **_contexto_menu(),
        "tema": tema,
        "active_tema_id": tema["id"],
        # SERGIO 2026-09-20: sin esto el <details> del capitulo quedaba cerrado y
        # ocultaba el subcapitulo abierto que tiene adentro
        "active_capitulo_id": capitulo_id_fila["capitulo_id"] if capitulo_id_fila else None,
        "active_subcapitulo_id": tema["subcapitulo_id"],
        "bloqueado": not desbloqueado,
        "tab": tab,
    }
    if not desbloqueado:
        return templates.TemplateResponse(request, "tema.html", contexto)

    contexto["teoria_html"] = markdown.markdown(tema["teoria_md"] or "")
    contexto["ejemplos"] = database.listar_ejemplos(tema["id"])

    ejercicios = []
    for ejercicio in database.listar_ejercicios(tema["id"]):
        ejercicios.append(
            {
                "ejercicio": ejercicio,
                "completado": database.ejercicio_completado(ejercicio["id"]),
                "fotos": database.listar_fotos(ejercicio["id"]),
            }
        )
    contexto["ejercicios"] = ejercicios

    evaluaciones = []
    for evaluacion in database.listar_evaluaciones(tema["id"]):
        evaluaciones.append(
            {
                "evaluacion": evaluacion,
                "aprobada": database.evaluacion_aprobada(evaluacion["id"]),
                "preguntas": database.obtener_preguntas(evaluacion["id"]),
                "ultimo_intento": database.ultimo_intento(evaluacion["id"]),
            }
        )
    contexto["evaluaciones"] = evaluaciones

    return templates.TemplateResponse(request, "tema.html", contexto)


@app.post("/ejercicios/{ejercicio_id}/foto")
async def subir_foto(ejercicio_id: int, foto: UploadFile = File(...)):
    tema = _tema_de_ejercicio(ejercicio_id)

    carpeta_ejercicio = config.UPLOADS_DIR / str(ejercicio_id)
    carpeta_ejercicio.mkdir(parents=True, exist_ok=True)
    destino = carpeta_ejercicio / foto.filename
    with destino.open("wb") as archivo_destino:
        shutil.copyfileobj(foto.file, archivo_destino)

    exif_json = exif_utils.extraer_exif_json(destino)
    ruta_relativa = f"{ejercicio_id}/{foto.filename}"
    database.guardar_foto(ejercicio_id, ruta_relativa, exif_json)

    return RedirectResponse(url=f"/tema/{tema['slug']}?tab=fotos", status_code=303)


@app.post("/fotos/{foto_id}/aprobar")
def aprobar_foto(foto_id: int):
    conn = database.get_connection()
    foto = conn.execute("SELECT * FROM fotos WHERE id = ?", (foto_id,)).fetchone()
    conn.close()
    tema = _tema_de_ejercicio(foto["ejercicio_id"]) if foto else None

    database.aprobar_foto(foto_id)

    if tema:
        return RedirectResponse(url=f"/tema/{tema['slug']}?tab=fotos", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.post("/evaluaciones/{evaluacion_id}/responder")
async def responder_evaluacion(request: Request, evaluacion_id: int):
    tema = _tema_de_evaluacion(evaluacion_id)
    preguntas = database.obtener_preguntas(evaluacion_id)

    formulario = await request.form()
    total = len(preguntas)
    correctas = 0
    for item in preguntas:
        pregunta = item["pregunta"]
        alternativa_elegida = formulario.get(f"pregunta_{pregunta['id']}")
        for alternativa in item["alternativas"]:
            if alternativa["es_correcta"] and str(alternativa["id"]) == alternativa_elegida:
                correctas += 1

    # SERGIO 2026-09-20: se aprueba solo si TODAS las preguntas quedan correctas
    aprobado = total > 0 and correctas == total
    database.registrar_intento_quiz(evaluacion_id, correctas, total, aprobado)

    return RedirectResponse(url=f"/tema/{tema['slug']}?tab=evaluacion", status_code=303)
