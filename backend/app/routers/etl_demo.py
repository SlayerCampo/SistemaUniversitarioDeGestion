from __future__ import annotations
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import require_roles
from app.db.seed import poblar_base_datos_simulacion, vaciar_base_datos
from app.db.session import get_db
from app.schemas import VaciarBDRequest
from app.services.etl_excel_service import (
    exportar_excel_desde_postgres,
    generar_excel_simulacion_bytes,
    importar_excel_a_postgres,
)

router = APIRouter(tags=["ETL Excel y Centro de Demostración"])


@router.get("/etl/generar-simulacion")
def descargar_excel_simulacion(
    _: dict = Depends(require_roles("Administrador")),
):
    """Genera el archivo Excel de 50+ estudiantes y 240 grupos sin tocar la BD activa."""
    data = generar_excel_simulacion_bytes(total_estudiantes=50)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Universidad_50_Estudiantes_UCC.xlsx"'},
    )


@router.post("/etl/importar")
async def importar_excel(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    if not archivo.filename or not archivo.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx).")
    contenido = await archivo.read()
    resumen = importar_excel_a_postgres(db, contenido)
    return {"mensaje": "Importación Excel a PostgreSQL completada.", **resumen}


@router.get("/etl/exportar-sabana")
def exportar_sabana(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    data = exportar_excel_desde_postgres(db)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Sabana_Academica_UCC_Postgres.xlsx"'},
    )


@router.post("/demo/poblar")
def demo_poblar(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    """Carga los 50+ estudiantes, 5 facultades, 8 programas y 240 grupos en PostgreSQL (solo DEMO_MODE)."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Acción de demostración deshabilitada (DEMO_MODE=false).")
    resumen = poblar_base_datos_simulacion(db, total_estudiantes=50)
    return {"mensaje": "Base de datos PostgreSQL poblada con la simulación institucional.", "resumen": resumen}


@router.post("/demo/vaciar")
def demo_vaciar(
    body: VaciarBDRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    """Vacía todas las tablas académicas en PostgreSQL exigiendo confirmación explícita 'VACIAR'."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Acción de demostración deshabilitada (DEMO_MODE=false).")
    if body.confirmacion.strip().upper() != "VACIAR":
        raise HTTPException(status_code=400, detail="Debe escribir 'VACIAR' para confirmar esta operación.")
    vaciar_base_datos(db)
    return {"mensaje": "Base de datos académica vaciada correctamente. Cuentas administrativas conservadas."}
