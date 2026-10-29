from __future__ import annotations
# ==============================================================================
# ARCHIVO: core/validador_horarios.py
# PROPÓSITO: Algoritmo detector de cruces de horarios académicos.
#            Analiza expresiones de texto como "Lunes 08:00 - 10:00",
#            "Martes y Jueves 10:00am - 12:00m" o "Viernes 14:00 - 17:00"
#            y verifica matemáticamente si dos asignaturas se solapan en el
#            mismo día y franja horaria.
# ==============================================================================

import re
import unicodedata
import config

# Mapa de normalización de nombres y abreviaturas de días de la semana
MAPA_DIAS = {
    "lunes": "Lunes",
    "lun": "Lunes",
    "martes": "Martes",
    "mar": "Martes",
    "miercoles": "Miércoles",
    "mie": "Miércoles",
    "jueves": "Jueves",
    "jue": "Jueves",
    "viernes": "Viernes",
    "vie": "Viernes",
    "sabado": "Sábado",
    "sab": "Sábado",
    "domingo": "Domingo",
    "dom": "Domingo",
}

DIAS_SEMANA_ORDEN = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

FRANJAS_HORARIAS_SUGERIDAS = [
    "06:00 - 08:00",
    "08:00 - 10:00",
    "10:00 - 12:00",
    "14:00 - 16:00",
    "16:00 - 18:00",
    "18:00 - 20:00",
    "20:00 - 22:00",
]


def _quitar_acentos(texto: str) -> str:
    """Elimina tildes de una cadena para facilitar comparaciones insensibles a acentos."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _convertir_hora_a_minutos(cadena_hora: str) -> int:
    """
    Convierte una representación de hora (ej. '8:00am', '14:30', '2:00pm', '12:00m')
    en el total de minutos transcurridos desde las 00:00.
    """
    limpia = cadena_hora.strip().lower().replace(" ", "")
    patron = re.match(r"^(\d{1,2})(?::(\d{2}))?(am|pm|m)?$", limpia)
    if not patron:
        raise ValueError(f"Formato de hora no reconocido: '{cadena_hora}'")

    horas = int(patron.group(1))
    minutos = int(patron.group(2)) if patron.group(2) else 0
    sufijo = patron.group(3)

    if sufijo == "pm" and horas < 12:
        horas += 12
    elif sufijo == "am" and horas == 12:
        horas = 0
    elif sufijo == "m" and horas == 12:
        horas = 12

    return horas * 60 + minutos


def _formatear_minutos_a_hora(minutos_totales: int) -> str:
    """Convierte minutos desde las 00:00 a formato legible HH:MM (24h)."""
    horas = minutos_totales // 60
    minutos = minutos_totales % 60
    return f"{horas:02d}:{minutos:02d}"


def parsear_horario(texto_horario: str) -> list[dict]:
    """
    Analiza una cadena de horario y devuelve una lista de bloques:
    [{"dia": "Lunes", "inicio": 480, "fin": 600}, ...]

    Soporta múltiples días (ej. 'Martes y Jueves 10:00 - 12:00') o segmentos
    separados por ';' o '/' (ej. 'Lunes 08:00 - 10:00 / Miércoles 10:00 - 12:00').
    """
    if not texto_horario or not str(texto_horario).strip():
        return []

    bloques = []
    segmentos = re.split(r"[;/|]", str(texto_horario))

    for segmento in segmentos:
        segmento_norm = _quitar_acentos(segmento.lower())

        # 1. Extraer todos los días mencionados en este segmento
        dias_encontrados = []
        palabras = re.findall(r"[a-z]+", segmento_norm)
        for palabra in palabras:
            if palabra in MAPA_DIAS:
                dia_canonico = MAPA_DIAS[palabra]
                if dia_canonico not in dias_encontrados:
                    dias_encontrados.append(dia_canonico)

        # 2. Extraer el rango de horas (inicio - fin)
        match_rango = re.search(
            r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|m)?)\s*[-a–]\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm|m)?)",
            segmento_norm
        )

        if dias_encontrados and match_rango:
            try:
                inicio_min = _convertir_hora_a_minutos(match_rango.group(1))
                fin_min = _convertir_hora_a_minutos(match_rango.group(2))
                # Si alguien escribió "2:00 - 5:00" sin am/pm y el inicio es menor que 7am,
                # asumimos jornada de la tarde (14:00 - 17:00)
                if inicio_min < 360 and "am" not in match_rango.group(1):
                    inicio_min += 12 * 60
                if fin_min <= inicio_min:
                    fin_min += 12 * 60

                for dia in dias_encontrados:
                    bloques.append({
                        "dia": dia,
                        "inicio": inicio_min,
                        "fin": fin_min
                    })
            except ValueError:
                continue

    return bloques


def verificar_cruce_entre_dos(horario_a: str, horario_b: str) -> tuple[bool, str]:
    """
    Compara dos cadenas de horario y determina si existe solapamiento temporal.
    Dos intervalos [inicio_A, fin_A) y [inicio_B, fin_B) se cruzan si y solo si:
        max(inicio_A, inicio_B) < min(fin_A, fin_B)
    """
    bloques_a = parsear_horario(horario_a)
    bloques_b = parsear_horario(horario_b)

    for ba in bloques_a:
        for bb in bloques_b:
            if ba["dia"] == bb["dia"]:
                inicio_solapado = max(ba["inicio"], bb["inicio"])
                fin_solapado = min(ba["fin"], bb["fin"])
                if inicio_solapado < fin_solapado:
                    rango_txt = f"{_formatear_minutos_a_hora(inicio_solapado)} a {_formatear_minutos_a_hora(fin_solapado)}"
                    return True, f"{ba['dia']} de {rango_txt}"

    return False, ""


def validar_cruce_con_lista(nueva_materia: dict, materias_existentes: list[dict]) -> tuple[bool, str]:
    """
    Verifica si una materia candidata (`{"id": ..., "nombre": ..., "horario": ...}`)
    presenta cruce de horario con cualquiera de las materias en `materias_existentes`.
    """
    horario_nuevo = nueva_materia.get("horario", "")
    nombre_nuevo = nueva_materia.get("nombre", nueva_materia.get("id", "Materia"))

    for existente in materias_existentes:
        hay_cruce, detalle = verificar_cruce_entre_dos(horario_nuevo, existente.get("horario", ""))
        if hay_cruce:
            nombre_ex = existente.get("nombre", existente.get("id", "Materia inscrita"))
            mensaje = (
                f"Cruce de horario detectado:\n"
                f"• '{nombre_nuevo}' ({horario_nuevo})\n"
                f"choca con:\n"
                f"• '{nombre_ex}' ({existente.get('horario', '')})\n"
                f"Conflicto el día {detalle}."
            )
            return True, mensaje

    return False, ""



# ==============================================================================
# REGLAS DE HORARIO INSTITUCIONAL (jornada, duración y hora de almuerzo)
# ==============================================================================

def _prefijo_hora(hora: int) -> str:
    """Devuelve una hora entera en formato HH:00 (Ej: 8 -> '08:00')."""
    return f"{hora:02d}:00"


def inicios_validos(duracion: int) -> list[int]:
    """
    Lista las horas de inicio posibles para una sesión de `duracion` horas seguidas:
    debe empezar desde la apertura, terminar antes del cierre y NO invadir la
    franja de almuerzo (13:00 a 14:00).
    """
    validos = []
    for inicio in range(config.HORA_APERTURA, config.HORA_CIERRE - duracion + 1):
        fin = inicio + duracion
        invade_almuerzo = inicio < config.HORA_ALMUERZO_FIN and fin > config.HORA_ALMUERZO_INICIO
        if not invade_almuerzo:
            validos.append(inicio)
    return validos


def construir_horario(dia: str, hora_inicio: int, duracion: int) -> str:
    """Construye el texto estándar de horario. Ej: ('Lunes', 8, 3) -> 'Lunes 08:00 - 11:00'."""
    return f"{dia} {_prefijo_hora(hora_inicio)} - {_prefijo_hora(hora_inicio + duracion)}"


def validar_horario_institucional(texto_horario: str) -> tuple[bool, str]:
    """
    Verifica que un horario sea reconocible y cumpla las reglas institucionales:
    - Dentro de la jornada (06:00 a 22:00).
    - Ninguna sesión puede cruzar la hora de almuerzo (13:00 a 14:00).
    Retorna (es_valido, mensaje_de_error).
    """
    bloques = parsear_horario(texto_horario)
    if not bloques:
        return False, "Formato de horario no reconocido. Ejemplo válido: 'Lunes 08:00 - 10:00'."

    ini_alm = config.HORA_ALMUERZO_INICIO * 60
    fin_alm = config.HORA_ALMUERZO_FIN * 60
    for b in bloques:
        if b["inicio"] < config.HORA_APERTURA * 60 or b["fin"] > config.HORA_CIERRE * 60:
            return False, (
                f"{b['dia']}: las clases deben estar entre las "
                f"{_prefijo_hora(config.HORA_APERTURA)} y las {_prefijo_hora(config.HORA_CIERRE)}."
            )
        if b["inicio"] < fin_alm and b["fin"] > ini_alm:
            return False, (
                f"{b['dia']} {_formatear_minutos_a_hora(b['inicio'])} - {_formatear_minutos_a_hora(b['fin'])}: "
                f"no se permiten clases en el almuerzo "
                f"({_prefijo_hora(config.HORA_ALMUERZO_INICIO)} a {_prefijo_hora(config.HORA_ALMUERZO_FIN)})."
            )
    return True, ""


def codigo_base_materia(id_materia: str) -> str:
    """
    Devuelve el código base de una asignatura sin el sufijo de grupo.
    Ej: 'SIS101-G2' -> 'SIS101'. Sirve para impedir matricular dos grupos de la misma materia.
    """
    texto = str(id_materia).strip().upper()
    if "-G" in texto:
        return texto.rsplit("-G", 1)[0]
    return texto
