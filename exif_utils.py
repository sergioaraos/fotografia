# SERGIO 2026-09-20: extrae los datos EXIF relevantes de una foto (feature/esqueleto-app)
import json
from PIL import Image
from PIL.ExifTags import TAGS

CAMPOS_UTILES = {
    "Model": "camara",
    "LensModel": "lente",
    "FNumber": "apertura",
    "ExposureTime": "velocidad",
    "ISOSpeedRatings": "iso",
    "FocalLength": "distancia_focal",
}


def extraer_exif(ruta_archivo):
    # Devuelve un dict con los campos utiles encontrados, o vacio si no hay EXIF
    try:
        imagen = Image.open(ruta_archivo)
        datos_crudos = imagen.getexif()
    except Exception:
        return {}

    if not datos_crudos:
        return {}

    resultado = {}
    for tag_id, valor in datos_crudos.items():
        nombre = TAGS.get(tag_id, tag_id)
        if nombre in CAMPOS_UTILES:
            resultado[CAMPOS_UTILES[nombre]] = str(valor)
    return resultado


def extraer_exif_json(ruta_archivo):
    return json.dumps(extraer_exif(ruta_archivo))
