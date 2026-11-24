from __future__ import annotations
"""
Motor centralizado de validación y parsing de horarios académicos UCC.
- Jornada permitida: 06:00 a 22:00.
- Duraciones válidas: 2, 3 o 4 horas seguidas (coincidiendo con créditos).
- Regla estricta de almuerzo: 0 clases entre 13:00 y 14:00.
"""

import re
import unicodedata
from dataclasses import dataclass

from app.core.config import settings

DIA_NUM_A_NOMBRE: dict[int, str] = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
}

NOMBRE_A_DIA_NUM: dict[str, int] = {
    "lunes": 1, "lun": 1,
    "martes": 2, "mar": 2,
    "miercoles": 3, "mie": 3,
    "jueves": 4, "jue": 4,
    "viernes": 5, "vie": 5,
    "sabado": 6, "sab": 6,
}


@dataclass(frozen=True)
class BloqueHorario:
    dia_semana: int
    hora_inicio: int
    hora_fin: int

    @property
    def dia_nombre(self) -> str:
        return DIA_NUM_A_NOMBRE.get(self.dia_semana, f"Día {self.dia_semana}")

    def formato_texto(self) -> str:
        return f"{self.dia_nombre} {self.hora_inicio:02d}:00 - {self.hora_fin:02d}:00"


def quitar_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    )


def codigo_base_asignatura(id_grupo_o_materia: str) -> str:
    """Extrae el código base sin sufijo de grupo (Ej: 'SIS101-G1' -> 'SIS101')."""
    texto = str(id_grupo_o_materia or "").strip().upper()
    return re.sub(r"-G\d+$", "", texto)


def inicios_validos(duracion: int) -> list[int]:
    """Devuelve horas de inicio válidas entre 06:00 y 22:00 sin tocar 13:00-14:00."""
    dur = int(duracion)
    if dur not in settings.DURACIONES_PERMITIDAS:
        return []
    resultado: list[int] = []
    for h in range(settings.HORA_APERTURA, settings.HORA_CIERRE - dur + 1):
        fin = h + dur
        if h < settings.HORA_ALMUERZO_FIN and fin > settings.HORA_ALMUERZO_INICIO:
            continue
        resultado.append(h)
    return resultado


def validar_bloque_institucional(
    dia_semana: int,
    hora_inicio: int,
    hora_fin: int,
    creditos_esperados: int | None = None,
) -> tuple[bool, str]:
    """Valida matemáticamente un bloque horario contra las políticas de la UCC."""
    if dia_semana not in DIA_NUM_A_NOMBRE:
        return False, "Día de la semana inválido (use Lunes=1 a Sábado=6)."
    if hora_inicio < settings.HORA_APERTURA or hora_fin > settings.HORA_CIERRE:
        return False, f"El horario debe estar entre {settings.HORA_APERTURA:02d}:00 y {settings.HORA_CIERRE:02d}:00."
    duracion = hora_fin - hora_inicio
    if duracion <= 0:
        return False, "La hora de fin debe ser mayor a la hora de inicio."
    if duracion not in settings.DURACIONES_PERMITIDAS:
        return False, f"La duración debe ser de 2, 3 o 4 horas continuas (recibido: {duracion}h)."
    if creditos_esperados is not None and creditos_esperados in settings.DURACIONES_PERMITIDAS and duracion != creditos_esperados:
        return False, f"Una asignatura de {creditos_esperados} créditos debe durar {creditos_esperados} horas seguidas."
    if hora_inicio < settings.HORA_ALMUERZO_FIN and hora_fin > settings.HORA_ALMUERZO_INICIO:
        return False, "Prohibido programar clases durante la hora de almuerzo (13:00 a 14:00)."
    return True, "Horario válido."


def bloques_se_cruzan(a: BloqueHorario, b: BloqueHorario) -> bool:
    """Retorna True si dos bloques se solapan el mismo día."""
    if a.dia_semana != b.dia_semana:
        return False
    return a.hora_inicio < b.hora_fin and b.hora_inicio < a.hora_fin


def detectar_cruce_grupos(
    nombre_nuevo: str,
    bloques_nuevos: list[BloqueHorario],
    existentes: list[tuple[str, str, list[BloqueHorario]]],
) -> tuple[bool, str]:
    """
    Comprueba si `bloques_nuevos` se solapa con alguno de `existentes`
    donde cada elemento es `(id_grupo, nombre_curso, bloques)`.
    """
    for bn in bloques_nuevos:
        for id_ex, nom_ex, bloques_ex in existentes:
            for be in bloques_ex:
                if bloques_se_cruzan(bn, be):
                    ini = max(bn.hora_inicio, be.hora_inicio)
                    fin = min(bn.hora_fin, be.hora_fin)
                    return (
                        True,
                        f"Cruce de horario el {bn.dia_nombre} ({ini:02d}:00 - {fin:02d}:00) "
                        f"entre '{nombre_nuevo}' y '{id_ex} - {nom_ex}'.",
                    )
    return False, ""


def formatear_horarios(bloques: list[BloqueHorario]) -> str:
    if not bloques:
        return "Por definir"
    ordenados = sorted(bloques, key=lambda b: (b.dia_semana, b.hora_inicio))
    return " / ".join(b.formato_texto() for b in ordenados)


def parsear_texto_horario(texto: str) -> list[BloqueHorario]:
    """
    Convierte cadenas tipo 'Lunes 08:00 - 11:00' o 'Martes y Jueves 14:00 - 16:00'
    en una lista estructurada de BloqueHorario. Usado en el importador ETL Excel.
    """
    if not texto or not str(texto).strip():
        return []
    bloques: list[BloqueHorario] = []
    segmentos = re.split(r"[;/|]", str(texto))
    for seg in segmentos:
        norm = quitar_acentos(seg.lower())
        dias: list[int] = []
        for token, num in NOMBRE_A_DIA_NUM.items():
            if re.search(rf"\b{token}\b", norm) and num not in dias:
                dias.append(num)
        match_horas = re.search(r"(\d{1,2})(?::\d{2})?\s*[-a]\s*(\d{1,2})(?::\d{2})?", norm)
        if dias and match_horas:
            h_ini = int(match_horas.group(1))
            h_fin = int(match_horas.group(2))
            for d in dias:
                bloques.append(BloqueHorario(dia_semana=d, hora_inicio=h_ini, hora_fin=h_fin))
    return bloques
