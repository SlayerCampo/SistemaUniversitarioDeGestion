from __future__ import annotations
"""
Servicio transaccional de Matrícula Académica UCC sobre PostgreSQL.
- Valida pertenencia al Programa del estudiante.
- Valida no repetición de asignatura base.
- Valida tope de créditos (6 a 19).
- Valida cruces de horario en servidor (fuente única de verdad).
- Actualiza cupos de forma ATÓMICA (`UPDATE ... WHERE cupos_disponibles > 0`).
"""

from datetime import date
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.horarios import BloqueHorario, detectar_cruce_grupos, formatear_horarios
from app.db.models import Asignatura, Estudiante, Grupo, Matricula, Periodo, Programa


def _bloques_de_grupo(grupo: Grupo) -> list[BloqueHorario]:
    return [
        BloqueHorario(dia_semana=h.dia_semana, hora_inicio=h.hora_inicio, hora_fin=h.hora_fin)
        for h in grupo.horarios
    ]


def serializar_grupo(grupo: Grupo, programa_nombre: str | None = None) -> dict:
    bloques = _bloques_de_grupo(grupo)
    asig = grupo.asignatura
    return {
        "id_grupo": grupo.id_grupo,
        "id_asignatura": grupo.id_asignatura,
        "nombre_curso": asig.nombre_curso,
        "creditos": asig.creditos,
        "id_programa": asig.id_programa,
        "nombre_programa": programa_nombre or (asig.programa.nombre_programa if asig.programa else asig.id_programa),
        "id_periodo": grupo.id_periodo,
        "docente": grupo.docente,
        "cupos_totales": grupo.cupos_totales,
        "cupos_disponibles": grupo.cupos_disponibles,
        "horario_texto": formatear_horarios(bloques),
        "horarios": [
            {
                "dia_semana": b.dia_semana,
                "dia_nombre": b.dia_nombre,
                "hora_inicio": b.hora_inicio,
                "hora_fin": b.hora_fin,
            }
            for b in bloques
        ],
    }


def obtener_resumen_matricula(db: Session, id_estudiante: str, id_periodo: str) -> dict:
    est = db.execute(
        select(Estudiante)
        .options(selectinload(Estudiante.programa))
        .where(Estudiante.id_estudiante == id_estudiante)
    ).scalar_one_or_none()
    if not est:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Estudiante '{id_estudiante}' no encontrado.")

    matriculas_activas = db.execute(
        select(Matricula)
        .options(
            selectinload(Matricula.grupo)
            .selectinload(Grupo.asignatura)
            .selectinload(Asignatura.programa),
            selectinload(Matricula.grupo).selectinload(Grupo.horarios),
        )
        .where(
            Matricula.id_estudiante == id_estudiante,
            Matricula.id_periodo == id_periodo,
            Matricula.estado == "Activa",
        )
    ).scalars().all()

    inscritas = []
    asignaturas_inscritas: set[str] = set()
    creditos_inscritos = 0
    for mat in matriculas_activas:
        g_info = serializar_grupo(mat.grupo, est.programa.nombre_programa if est.programa else None)
        inscritas.append({
            "id_matricula": mat.id_matricula,
            "fecha_matricula": mat.fecha_matricula.isoformat(),
            "estado": mat.estado,
            **g_info,
        })
        asignaturas_inscritas.add(mat.grupo.id_asignatura)
        creditos_inscritos += mat.creditos

    # Oferta filtrada EXCLUSIVAMENTE al programa del estudiante
    grupos_programa = db.execute(
        select(Grupo)
        .join(Asignatura, Grupo.id_asignatura == Asignatura.id_asignatura)
        .options(
            selectinload(Grupo.asignatura).selectinload(Asignatura.programa),
            selectinload(Grupo.horarios),
        )
        .where(
            Asignatura.id_programa == est.id_programa,
            Grupo.id_periodo == id_periodo,
        )
        .order_by(Grupo.id_grupo)
    ).scalars().all()

    oferta_por_asignatura: dict[str, dict] = {}
    for g in grupos_programa:
        if g.id_asignatura in asignaturas_inscritas:
            continue
        if g.id_asignatura not in oferta_por_asignatura:
            oferta_por_asignatura[g.id_asignatura] = {
                "id_asignatura": g.id_asignatura,
                "nombre_curso": g.asignatura.nombre_curso,
                "creditos": g.asignatura.creditos,
                "grupos": [],
            }
        oferta_por_asignatura[g.id_asignatura]["grupos"].append(
            serializar_grupo(g, est.programa.nombre_programa if est.programa else None)
        )

    return {
        "estudiante": {
            "id_estudiante": est.id_estudiante,
            "nombre_completo": f"{est.nombre} {est.apellidos}",
            "correo": est.correo,
            "semestre": est.semestre,
            "id_programa": est.id_programa,
            "nombre_programa": est.programa.nombre_programa if est.programa else est.id_programa,
        },
        "periodo": id_periodo,
        "reglas": {
            "creditos_minimos": settings.CREDITOS_MINIMOS,
            "creditos_maximos": settings.CREDITOS_MAXIMOS,
            "almuerzo": f"{settings.HORA_ALMUERZO_INICIO:02d}:00 - {settings.HORA_ALMUERZO_FIN:02d}:00",
        },
        "creditos_inscritos": creditos_inscritos,
        "inscritas": inscritas,
        "oferta_disponible": list(oferta_por_asignatura.values()),
    }


def validar_carrito_matricula(
    db: Session,
    id_estudiante: str,
    id_periodo: str,
    grupos_ids: list[str],
    exigir_minimo: bool = False,
) -> dict:
    est = db.get(Estudiante, id_estudiante)
    if not est:
        raise HTTPException(status_code=404, detail=f"Estudiante '{id_estudiante}' no encontrado.")

    if not grupos_ids:
        return {"valido": False, "errores": ["Debe seleccionar al menos un grupo en el carrito."], "creditos_totales": 0}

    # Cargar matrículas activas actuales
    activas = db.execute(
        select(Matricula)
        .options(
            selectinload(Matricula.grupo).selectinload(Grupo.asignatura),
            selectinload(Matricula.grupo).selectinload(Grupo.horarios),
        )
        .where(
            Matricula.id_estudiante == id_estudiante,
            Matricula.id_periodo == id_periodo,
            Matricula.estado == "Activa",
        )
    ).scalars().all()

    errores: list[str] = []
    creditos_existentes = sum(m.creditos for m in activas)
    asigs_ocupadas = {m.grupo.id_asignatura for m in activas}
    bloques_ocupados: list[tuple[str, str, list[BloqueHorario]]] = [
        (m.grupo.id_grupo, m.grupo.asignatura.nombre_curso, _bloques_de_grupo(m.grupo))
        for m in activas
    ]

    # Cargar grupos solicitados
    grupos_sol = db.execute(
        select(Grupo)
        .options(selectinload(Grupo.asignatura), selectinload(Grupo.horarios))
        .where(Grupo.id_grupo.in_(grupos_ids))
    ).scalars().all()
    mapa_grupos = {g.id_grupo: g for g in grupos_sol}

    creditos_carrito = 0
    grupos_ordenados: list[Grupo] = []

    for gid in grupos_ids:
        g = mapa_grupos.get(gid)
        if not g:
            errores.append(f"El grupo '{gid}' no existe.")
            continue
        if g.id_periodo != id_periodo:
            errores.append(f"El grupo '{gid}' no pertenece al periodo '{id_periodo}'.")
            continue
        if g.asignatura.id_programa != est.id_programa:
            errores.append(
                f"La asignatura '{g.asignatura.nombre_curso}' no pertenece a tu programa académico ({est.id_programa})."
            )
            continue
        if g.cupos_disponibles <= 0:
            errores.append(f"El grupo '{g.id_grupo} ({g.asignatura.nombre_curso})' no tiene cupos disponibles.")
            continue
        if g.id_asignatura in asigs_ocupadas:
            errores.append(
                f"Asignatura duplicada: ya tienes inscrita o en carrito '{g.id_asignatura} - {g.asignatura.nombre_curso}'."
            )
            continue

        bloques_g = _bloques_de_grupo(g)
        hay_cruce, msg_cruce = detectar_cruce_grupos(g.asignatura.nombre_curso, bloques_g, bloques_ocupados)
        if hay_cruce:
            errores.append(msg_cruce)
            continue

        asigs_ocupadas.add(g.id_asignatura)
        bloques_ocupados.append((g.id_grupo, g.asignatura.nombre_curso, bloques_g))
        creditos_carrito += g.asignatura.creditos
        grupos_ordenados.append(g)

    creditos_totales = creditos_existentes + creditos_carrito
    if creditos_totales > settings.CREDITOS_MAXIMOS:
        errores.append(
            f"Se excede el tope de {settings.CREDITOS_MAXIMOS} créditos permitidos "
            f"(Ya inscritos: {creditos_existentes} + Carrito: {creditos_carrito} = {creditos_totales})."
        )
    if exigir_minimo and creditos_totales < settings.CREDITOS_MINIMOS:
        errores.append(
            f"Debe completar mínimo {settings.CREDITOS_MINIMOS} créditos en el periodo "
            f"(Total actual: {creditos_totales} créditos)."
        )

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "creditos_inscritos": creditos_existentes,
        "creditos_carrito": creditos_carrito,
        "creditos_totales": creditos_totales,
        "grupos": grupos_ordenados,
    }


def confirmar_matricula_transaccional(
    db: Session,
    id_estudiante: str,
    id_periodo: str,
    grupos_ids: list[str],
) -> dict:
    """Confirma la matrícula de forma atómica en PostgreSQL."""
    # Asegurar periodo existe
    if not db.get(Periodo, id_periodo):
        db.add(Periodo(id_periodo=id_periodo, activo=True))
        db.flush()

    validacion = validar_carrito_matricula(db, id_estudiante, id_periodo, grupos_ids, exigir_minimo=True)
    if not validacion["valido"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=" | ".join(validacion["errores"]),
        )

    creadas: list[str] = []
    hoy = date.today()
    try:
        for g in validacion["grupos"]:
            # Actualización atómica que impide sobreventa concurrente de cupos
            res = db.execute(
                update(Grupo)
                .where(Grupo.id_grupo == g.id_grupo, Grupo.cupos_disponibles > 0)
                .values(cupos_disponibles=Grupo.cupos_disponibles - 1)
            )
            if res.rowcount != 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El último cupo del grupo '{g.id_grupo}' acaba de agotarse. Seleccione otro grupo.",
                )

            id_mat = f"MAT-{str(uuid.uuid4())[:8].upper()}"
            db.add(
                Matricula(
                    id_matricula=id_mat,
                    id_estudiante=id_estudiante,
                    id_grupo=g.id_grupo,
                    id_periodo=id_periodo,
                    creditos=g.asignatura.creditos,
                    fecha_matricula=hoy,
                    estado="Activa",
                )
            )
            creadas.append(id_mat)

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error transaccional al matricular: {exc}") from exc

    return {
        "mensaje": f"¡Matrícula oficial asentada! {len(creadas)} asignatura(s) confirmadas.",
        "matriculas_creadas": creadas,
        "creditos_totales": validacion["creditos_totales"],
    }


def retirar_matricula(db: Session, id_matricula: str, id_estudiante_forzado: str | None = None) -> dict:
    mat = db.execute(
        select(Matricula)
        .options(selectinload(Matricula.grupo).selectinload(Grupo.asignatura))
        .where(Matricula.id_matricula == id_matricula)
    ).scalar_one_or_none()
    if not mat:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada.")
    if id_estudiante_forzado and mat.id_estudiante != id_estudiante_forzado:
        raise HTTPException(status_code=403, detail="No puede retirar asignaturas de otro estudiante.")
    if mat.estado != "Activa":
        raise HTTPException(status_code=400, detail="Esta matrícula ya no se encuentra activa.")

    mat.estado = "Cancelada"
    db.execute(
        update(Grupo)
        .where(Grupo.id_grupo == mat.id_grupo, Grupo.cupos_disponibles < Grupo.cupos_totales)
        .values(cupos_disponibles=Grupo.cupos_disponibles + 1)
    )
    db.commit()
    return {
        "mensaje": f"Asignatura '{mat.grupo.asignatura.nombre_curso}' retirada y +1 cupo restituido.",
        "id_matricula": id_matricula,
        "id_grupo": mat.id_grupo,
    }
