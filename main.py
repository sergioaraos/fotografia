# SERGIO 2026-09-20: esqueleto inicial de la app, sin contenido de fotografia todavia
# (feature/esqueleto-app)
import shutil
from pathlib import Path

import markdown
from fastapi import FastAPI, Request, Form, UploadFile, File
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


def _capitulo_de_ejercicio(ejercicio):
    conn = database.get_connection()
    capitulo = conn.execute(
        "SELECT * FROM capitulos WHERE id = ?", (ejercicio["capitulo_id"],)
    ).fetchone()
    conn.close()
    return capitulo


@app.get("/")
def index(request: Request):
    capitulos = progreso.estado_capitulos()
    return templates.TemplateResponse(request, "index.html", {"capitulos": capitulos})


@app.get("/capitulo/{slug}")
def ver_capitulo(request: Request, slug: str):
    capitulo = database.obtener_capitulo_por_slug(slug)
    if not capitulo:
        return templates.TemplateResponse(
            request, "index.html", {"capitulos": progreso.estado_capitulos(), "error": "Capitulo no encontrado"},
            status_code=404,
        )

    desbloqueado = progreso.capitulo_desbloqueado(slug)
    if not desbloqueado:
        return templates.TemplateResponse(
            request,
            "capitulo.html",
            {"capitulo": capitulo, "bloqueado": True, "capitulos": progreso.estado_capitulos()},
        )

    teoria_html = markdown.markdown(capitulo["teoria_md"] or "")
    ejercicios = []
    for ejercicio in database.obtener_ejercicios(capitulo["id"]):
        item = {"ejercicio": ejercicio, "completado": database.ejercicio_completado(ejercicio["id"])}
        if ejercicio["tipo"] == "quiz":
            item["preguntas"] = database.obtener_preguntas(ejercicio["id"])
        else:
            item["fotos"] = database.listar_fotos(ejercicio["id"])
        ejercicios.append(item)

    return templates.TemplateResponse(
        request,
        "capitulo.html",
        {
            "capitulo": capitulo,
            "bloqueado": False,
            "teoria_html": teoria_html,
            "ejercicios": ejercicios,
            "capitulos": progreso.estado_capitulos(),
        },
    )


@app.post("/ejercicios/{ejercicio_id}/quiz")
async def responder_quiz(request: Request, ejercicio_id: int):
    ejercicio = database.obtener_ejercicio(ejercicio_id)
    capitulo = _capitulo_de_ejercicio(ejercicio)
    preguntas = database.obtener_preguntas(ejercicio_id)

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
    database.registrar_intento_quiz(ejercicio_id, correctas, total, aprobado)

    return RedirectResponse(url=f"/capitulo/{capitulo['slug']}", status_code=303)


@app.post("/ejercicios/{ejercicio_id}/foto")
async def subir_foto(ejercicio_id: int, foto: UploadFile = File(...)):
    ejercicio = database.obtener_ejercicio(ejercicio_id)
    capitulo = _capitulo_de_ejercicio(ejercicio)

    carpeta_ejercicio = config.UPLOADS_DIR / str(ejercicio_id)
    carpeta_ejercicio.mkdir(parents=True, exist_ok=True)
    destino = carpeta_ejercicio / foto.filename
    with destino.open("wb") as archivo_destino:
        shutil.copyfileobj(foto.file, archivo_destino)

    exif_json = exif_utils.extraer_exif_json(destino)
    ruta_relativa = f"{ejercicio_id}/{foto.filename}"
    database.guardar_foto(ejercicio_id, ruta_relativa, exif_json)

    return RedirectResponse(url=f"/capitulo/{capitulo['slug']}", status_code=303)


@app.post("/fotos/{foto_id}/aprobar")
def aprobar_foto(foto_id: int):
    conn = database.get_connection()
    foto = conn.execute("SELECT * FROM fotos WHERE id = ?", (foto_id,)).fetchone()
    conn.close()
    ejercicio = database.obtener_ejercicio(foto["ejercicio_id"]) if foto else None
    capitulo = _capitulo_de_ejercicio(ejercicio) if ejercicio else None

    database.aprobar_foto(foto_id)

    if capitulo:
        return RedirectResponse(url=f"/capitulo/{capitulo['slug']}", status_code=303)
    return RedirectResponse(url="/", status_code=303)
