from __future__ import annotations
from decimal import Decimal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.security import get_current_user, require_roles
from app.db.models import Asignatura, Estudiante, Grupo, Matricula, Nota
from app.db.seed import calcular_definitiva_y_estado
from app.db.session import get_db
from app.schemas import CalificarLoteRequest

router = APIRouter(prefix="/notas", tags=["Notas y Panel Docente"])


@router.get("/boletin/{id_estudiante}")
def obtener_boletin(
    id_estudiante: str,
    periodo: str = Query(default=settings.PERIODO_ACTIVO_DEFECTO),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["rol"] == "Estudiante" and current_user["documento_asociado"] != id_estudiante:
        raise HTTPException(status_code=403, detail="Solo puede consultar su propio boletín de calificaciones.")

    est = db.execute(
        select(Estudiante).options(selectinload(Estudiante.programa)).where(Estudiante.id_estudiante == id_estudiante)
    ).scalar_one_or_none()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado.")

    mats = db.execute(
        select(Matricula)
        .options(
            selectinload(Matricula.grupo).selectinload(Grupo.asignatura),
            selectinload(Matricula.nota),
        )
        .where(
            Matricula.id_estudiante == id_estudiante,
            Matricula.id_periodo == periodo,
            Matricula.estado == "Activa",
        )
        .order_by(Matricula.id_grupo)
    ).scalars().all()

    items = []
    suma_pond = 0.0
    cred_calif = 0
    cred_aprob = 0
    aprobadas = 0
    total_cred = 0

    for m in mats:
        total_cred += m.creditos
        n = m.nota
        if n and n.estado != "Sin calificar":
            n1, n2, n3, df, est_n = float(n.nota1), float(n.nota2), float(n.nota3), float(n.definitiva), n.estado
            suma_pond += df * m.creditos
            cred_calif += m.creditos
            if df >= settings.NOTA_APROBATORIA:
                cred_aprob += m.creditos
                aprobadas += 1
        else:
            n1 = n2 = n3 = df = None
            est_n = "Sin calificar"

        items.append({
            "id_matricula": m.id_matricula,
            "id_grupo": m.id_grupo,
            "id_asignatura": m.grupo.id_asignatura,
            "nombre_curso": m.grupo.asignatura.nombre_curso,
            "docente": m.grupo.docente,
            "creditos": m.creditos,
            "nota1": n1,
            "nota2": n2,
            "nota3": n3,
            "definitiva": df,
            "estado": est_n,
        })

    pps = round(suma_pond / cred_calif, 2) if cred_calif > 0 else 0.0
    return {
        "estudiante": {
            "id_estudiante": est.id_estudiante,
            "nombre_completo": f"{est.nombre} {est.apellidos}",
            "semestre": est.semestre,
            "id_programa": est.id_programa,
            "nombre_programa": est.programa.nombre_programa if est.programa else est.id_programa,
        },
        "periodo": periodo,
        "resumen": {
            "pps": pps,
            "materias_activas": len(mats),
            "materias_aprobadas": aprobadas,
            "creditos_inscritos": total_cred,
            "creditos_aprobados": cred_aprob,
        },
        "asignaturas": items,
    }


@router.get("/planilla/{id_grupo}")
def obtener_planilla_grupo(
    id_grupo: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Profesor", "Administrador")),
):
    grupo = db.execute(
        select(Grupo)
        .options(selectinload(Grupo.asignatura).selectinload(Asignatura.programa), selectinload(Grupo.horarios))
        .where(Grupo.id_grupo == id_grupo)
    ).scalar_one_or_none()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado.")

    mats = db.execute(
        select(Matricula)
        .options(selectinload(Matricula.estudiante), selectinload(Matricula.nota))
        .where(Matricula.id_grupo == id_grupo, Matricula.estado == "Activa")
        .order_by(Matricula.id_estudiante)
    ).scalars().all()

    estudiantes = []
    for m in mats:
        n = m.nota
        estudiantes.append({
            "id_matricula": m.id_matricula,
            "id_estudiante": m.id_estudiante,
            "nombre_completo": f"{m.estudiante.nombre} {m.estudiante.apellidos}",
            "correo": m.estudiante.correo,
            "nota1": float(n.nota1) if n else 0.0,
            "nota2": float(n.nota2) if n else 0.0,
            "nota3": float(n.nota3) if n else 0.0,
            "definitiva": float(n.definitiva) if n else 0.0,
            "estado": n.estado if n else "Sin calificar",
        })

    return {
        "id_grupo": grupo.id_grupo,
        "nombre_curso": grupo.asignatura.nombre_curso,
        "creditos": grupo.asignatura.creditos,
        "docente": grupo.docente,
        "id_programa": grupo.asignatura.id_programa,
        "nombre_programa": grupo.asignatura.programa.nombre_programa if grupo.asignatura.programa else grupo.asignatura.id_programa,
        "estudiantes": estudiantes,
    }


@router.put("/calificar")
def guardar_calificaciones(
    body: CalificarLoteRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Profesor", "Administrador")),
):
    actualizadas = 0
    for item in body.calificaciones:
        mat = db.get(Matricula, item.id_matricula)
        if not mat or mat.estado != "Activa":
            continue
        def_val, est_nota = calcular_definitiva_y_estado(item.nota1, item.nota2, item.nota3)
        nota_existente = db.execute(select(Nota).where(Nota.id_matricula == item.id_matricula)).scalar_one_or_none()
        if nota_existente:
            nota_existente.nota1 = Decimal(f"{item.nota1:.2f}")
            nota_existente.nota2 = Decimal(f"{item.nota2:.2f}")
            nota_existente.nota3 = Decimal(f"{item.nota3:.2f}")
            nota_existente.definitiva = def_val
            nota_existente.estado = est_nota
        else:
            db.add(
                Nota(
                    id_nota=f"NOT-{str(uuid.uuid4())[:8].upper()}",
                    id_matricula=item.id_matricula,
                    nota1=Decimal(f"{item.nota1:.2f}"),
                    nota2=Decimal(f"{item.nota2:.2f}"),
                    nota3=Decimal(f"{item.nota3:.2f}"),
                    definitiva=def_val,
                    estado=est_nota,
                )
            )
        actualizadas += 1

    db.commit()
    return {"mensaje": f"Se guardaron {actualizadas} calificación(es) exitosamente.", "actualizadas": actualizadas}
