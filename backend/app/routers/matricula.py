from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas import MatriculaValidarRequest
from app.services.matricula_service import (
    confirmar_matricula_transaccional,
    obtener_resumen_matricula,
    retirar_matricula,
    validar_carrito_matricula,
)

router = APIRouter(prefix="/matricula", tags=["Matrícula Académica"])


def _verificar_acceso_estudiante(id_estudiante: str, current_user: dict) -> None:
    if current_user["rol"] == "Estudiante" and current_user["documento_asociado"] != id_estudiante:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: solo puede consultar o modificar su propia matrícula.",
        )


@router.get("/resumen/{id_estudiante}")
def resumen_matricula(
    id_estudiante: str,
    periodo: str = Query(default=settings.PERIODO_ACTIVO_DEFECTO),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _verificar_acceso_estudiante(id_estudiante, current_user)
    return obtener_resumen_matricula(db, id_estudiante, periodo)


@router.post("/validar")
def validar_carrito(
    body: MatriculaValidarRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _verificar_acceso_estudiante(body.id_estudiante, current_user)
    res = validar_carrito_matricula(db, body.id_estudiante, body.id_periodo, body.grupos_ids, exigir_minimo=False)
    return {
        "valido": res["valido"],
        "errores": res["errores"],
        "creditos_inscritos": res["creditos_inscritos"],
        "creditos_carrito": res["creditos_carrito"],
        "creditos_totales": res["creditos_totales"],
    }


@router.post("/confirmar", status_code=201)
def confirmar_matricula(
    body: MatriculaValidarRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    _verificar_acceso_estudiante(body.id_estudiante, current_user)
    return confirmar_matricula_transaccional(db, body.id_estudiante, body.id_periodo, body.grupos_ids)


@router.post("/retirar/{id_matricula}")
def retirar_asignatura(
    id_matricula: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    forzado = current_user["documento_asociado"] if current_user["rol"] == "Estudiante" else None
    return retirar_matricula(db, id_matricula, id_estudiante_forzado=forzado)
