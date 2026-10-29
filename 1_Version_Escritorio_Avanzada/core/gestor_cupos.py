from __future__ import annotations
# ==============================================================================
# ARCHIVO: core/gestor_cupos.py
# PROPÓSITO: Administrar la disponibilidad de cupos de las asignaturas en tiempo
#            real. Descuenta cupos al confirmar una matrícula y los restituye
#            cuando un estudiante cancela o retira una materia.
# ==============================================================================

import data.db_excel as db


def obtener_cupos_disponibles(id_materia: str) -> int:
    """Consulta la cantidad actual de cupos disponibles para una materia dada."""
    libro = db.cargar_libro()
    fila_materia = db.buscar_fila(libro["Materias"], 0, id_materia)
    libro.close()
    if not fila_materia:
        return 0
    try:
        return max(0, int(fila_materia[3]))
    except (ValueError, TypeError):
        return 0


def descontar_cupo(id_materia: str, cantidad: int = 1) -> tuple[bool, str]:
    """
    Resta `cantidad` cupos a la materia indicada si hay disponibilidad suficiente.
    Retorna (exito: bool, mensaje: str).
    """
    libro = db.cargar_libro()
    hoja = libro["Materias"]
    fila = db.buscar_fila(hoja, 0, id_materia)

    if not fila:
        libro.close()
        return False, f"La materia '{id_materia}' no existe."

    try:
        cupos_actuales = int(fila[3])
    except (ValueError, TypeError):
        cupos_actuales = 0

    if cupos_actuales < cantidad:
        libro.close()
        return False, f"La materia '{fila[1]}' no tiene cupos disponibles (Cupos: {cupos_actuales})."

    nuevos_cupos = cupos_actuales - cantidad
    fila_actualizada = [
        fila[0],
        fila[1],
        int(fila[2]),
        nuevos_cupos,
        fila[4],
        fila[5],
        fila[6]
    ]
    libro.close()

    exito = db.actualizar_fila("Materias", 0, id_materia, fila_actualizada)
    if exito:
        return True, f"Cupo reservado. Cupos restantes en {fila[1]}: {nuevos_cupos}"
    return False, "No se pudo actualizar el cupo en el archivo Excel."


def restituir_cupo(id_materia: str, cantidad: int = 1) -> tuple[bool, str]:
    """
    Incrementa `cantidad` cupos a la materia cuando un estudiante cancela/retira
    la asignatura.
    """
    libro = db.cargar_libro()
    hoja = libro["Materias"]
    fila = db.buscar_fila(hoja, 0, id_materia)

    if not fila:
        libro.close()
        return False, f"La materia '{id_materia}' no fue encontrada."

    try:
        cupos_actuales = int(fila[3])
    except (ValueError, TypeError):
        cupos_actuales = 0

    nuevos_cupos = cupos_actuales + cantidad
    fila_actualizada = [
        fila[0],
        fila[1],
        int(fila[2]),
        nuevos_cupos,
        fila[4],
        fila[5],
        fila[6]
    ]
    libro.close()

    exito = db.actualizar_fila("Materias", 0, id_materia, fila_actualizada)
    if exito:
        return True, f"Cupo liberado. Cupos disponibles en {fila[1]}: {nuevos_cupos}"
    return False, "No se pudo restituir el cupo."

