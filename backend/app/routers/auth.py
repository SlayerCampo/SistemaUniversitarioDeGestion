from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.security import (
    construir_payload_usuario,
    crear_access_token,
    get_current_user,
    verify_password,
)
from app.db.models import Estudiante, Usuario
from app.db.session import get_db
from app.schemas import DemoSwitchRequest, LoginRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    usr_in = body.usuario.strip()
    pwd_in = body.password.strip()

    user_db = db.get(Usuario, usr_in)
    if user_db and verify_password(pwd_in, user_db.password_hash):
        payload = construir_payload_usuario(
            usuario=user_db.usuario,
            rol=user_db.rol,
            nombre_completo=user_db.nombre_completo,
            documento_asociado=user_db.documento_asociado,
            db=db,
            es_demo=False,
        )
        token = crear_access_token(payload)
        return TokenResponse(access_token=token, user=UserInfo(**payload))

    # Respaldo solo en DEMO_MODE para estudiantes registrados ingresando con su propio ID o '1234'
    if settings.DEMO_MODE:
        est = db.get(Estudiante, usr_in)
        if est and pwd_in in (est.id_estudiante, "1234"):
            payload = construir_payload_usuario(
                usuario=est.id_estudiante,
                rol="Estudiante",
                nombre_completo=f"{est.nombre} {est.apellidos}",
                documento_asociado=est.id_estudiante,
                db=db,
                es_demo=True,
            )
            token = crear_access_token(payload)
            return TokenResponse(access_token=token, user=UserInfo(**payload))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario o contraseña incorrectos.",
    )


@router.get("/me", response_model=UserInfo)
def me(current_user: dict = Depends(get_current_user)):
    return UserInfo(**current_user)


@router.get("/demo-perfiles")
def listar_perfiles_demo(db: Session = Depends(get_db)):
    if not settings.DEMO_MODE:
        return {"demo_mode": False, "perfiles": []}

    estudiantes = db.execute(
        select(Estudiante)
        .options(selectinload(Estudiante.programa))
        .order_by(Estudiante.id_estudiante)
        .limit(15)
    ).scalars().all()

    return {
        "demo_mode": True,
        "cuentas_base": [
            {"perfil": "admin", "rol": "Administrador", "etiqueta": "Administrador General UCC", "detalle": "Control total, ETL y Analítica"},
            {"perfil": "profe", "rol": "Profesor", "etiqueta": "Docente Titular UCC", "detalle": "Planillas y Calificación por Cortes"},
        ],
        "estudiantes": [
            {
                "perfil": e.id_estudiante,
                "rol": "Estudiante",
                "etiqueta": f"{e.id_estudiante} — {e.nombre} {e.apellidos}",
                "detalle": f"{e.programa.nombre_programa if e.programa else e.id_programa} · Sem. {e.semestre}",
            }
            for e in estudiantes
        ],
    }


@router.post("/demo-switch", response_model=TokenResponse)
def demo_switch(body: DemoSwitchRequest, db: Session = Depends(get_db)):
    """Cambio rápido de rol para el Centro de Exposición (solo activo si DEMO_MODE=true)."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="El Modo Exposición está desactivado en este entorno.")

    perfil = body.perfil.strip()
    user_db = db.get(Usuario, perfil)
    if user_db:
        payload = construir_payload_usuario(
            usuario=user_db.usuario,
            rol=user_db.rol,
            nombre_completo=user_db.nombre_completo,
            documento_asociado=user_db.documento_asociado,
            db=db,
            es_demo=True,
        )
        return TokenResponse(access_token=crear_access_token(payload), user=UserInfo(**payload))

    est = db.get(Estudiante, perfil)
    if est:
        payload = construir_payload_usuario(
            usuario=est.id_estudiante,
            rol="Estudiante",
            nombre_completo=f"{est.nombre} {est.apellidos}",
            documento_asociado=est.id_estudiante,
            db=db,
            es_demo=True,
        )
        return TokenResponse(access_token=crear_access_token(payload), user=UserInfo(**payload))

    raise HTTPException(status_code=404, detail=f"Perfil de demostración '{perfil}' no encontrado.")
