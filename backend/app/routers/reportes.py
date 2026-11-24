from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.services.pdf_service import generar_pdf_boletin_bytes, generar_pdf_matricula_bytes

router = APIRouter(prefix="/reportes", tags=["Reportes Oficiales PDF"])


@router.get("/matricula/{id_estudiante}/pdf")
def descargar_pdf_matricula(
    id_estudiante: str,
    periodo: str = Query(default=settings.PERIODO_ACTIVO_DEFECTO),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["rol"] == "Estudiante" and current_user["documento_asociado"] != id_estudiante:
        raise HTTPException(status_code=403, detail="Solo puede descargar su propio comprobante de matrícula.")
    pdf_bytes = generar_pdf_matricula_bytes(db, id_estudiante, periodo)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Recibo_Matricula_{id_estudiante}.pdf"'},
    )


@router.get("/boletin/{id_estudiante}/pdf")
def descargar_pdf_boletin(
    id_estudiante: str,
    periodo: str = Query(default=settings.PERIODO_ACTIVO_DEFECTO),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["rol"] == "Estudiante" and current_user["documento_asociado"] != id_estudiante:
        raise HTTPException(status_code=403, detail="Solo puede descargar su propio boletín oficial.")
    pdf_bytes = generar_pdf_boletin_bytes(db, id_estudiante, periodo)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Boletin_Notas_{id_estudiante}.pdf"'},
    )
