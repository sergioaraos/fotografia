# SERGIO 2026-09-20: bloqueo secuencial a nivel de tema, cruzando subcapitulos
# y capitulos en un unico orden (feature/estructura-capitulo-subcapitulo-tema)
import database


def temas_en_orden():
    # Aplana el arbol completo en la secuencia en que se deben ir completando los temas
    lista = []
    for cap in database.arbol_completo():
        for sub in cap["subcapitulos"]:
            for tema in sub["temas"]:
                lista.append({"tema": tema, "capitulo": cap["capitulo"], "subcapitulo": sub["subcapitulo"]})
    return lista


def estado_temas():
    # Devuelve la secuencia de temas con su estado de desbloqueo/completitud
    resultado = []
    anterior_completado = True
    for item in temas_en_orden():
        tema_id = item["tema"]["id"]
        completado = database.tema_completado(tema_id)
        desbloqueado = anterior_completado
        resultado.append({**item, "completado": completado, "desbloqueado": desbloqueado})
        anterior_completado = completado
    return resultado


def tema_desbloqueado(slug):
    for item in estado_temas():
        if item["tema"]["slug"] == slug:
            return item["desbloqueado"]
    return False


def arbol_con_estado():
    # Igual que database.arbol_completo() pero agregando desbloqueado/completado a cada tema,
    # listo para pintar el menu de acordeon
    estados = {item["tema"]["id"]: item for item in estado_temas()}
    resultado = []
    for cap in database.arbol_completo():
        subcapitulos = []
        for sub in cap["subcapitulos"]:
            temas = []
            for tema in sub["temas"]:
                info = estados.get(tema["id"], {"completado": False, "desbloqueado": False})
                temas.append({"tema": tema, "completado": info["completado"], "desbloqueado": info["desbloqueado"]})
            subcapitulos.append({"subcapitulo": sub["subcapitulo"], "temas": temas})
        resultado.append({"capitulo": cap["capitulo"], "subcapitulos": subcapitulos})
    return resultado
