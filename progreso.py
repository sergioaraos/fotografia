# SERGIO 2026-09-20: logica de bloqueo/desbloqueo de capitulos (feature/esqueleto-app)
# Un capitulo esta desbloqueado si es el primero (por orden) o si el capitulo
# anterior quedo completo (todos sus ejercicios completados).
import database


def estado_capitulos():
    capitulos = database.listar_capitulos()
    resultado = []
    anterior_completado = True
    for capitulo in capitulos:
        completado = database.capitulo_completado(capitulo["id"])
        desbloqueado = anterior_completado
        resultado.append(
            {
                "capitulo": capitulo,
                "completado": completado,
                "desbloqueado": desbloqueado,
            }
        )
        anterior_completado = completado
    return resultado


def capitulo_desbloqueado(slug):
    for item in estado_capitulos():
        if item["capitulo"]["slug"] == slug:
            return item["desbloqueado"]
    return False
