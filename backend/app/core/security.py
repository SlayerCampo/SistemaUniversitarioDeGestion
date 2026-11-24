from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Estudiante, Programa, Usuario
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password_plano: str) -> str:
    """Genera hash bcrypt seguro con salt aleatorio."""
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password_plano.strip().encode("utf-8"), salt).decode("utf-8")


def verify_password(password_plano: str, password_hash: str) -> bool:
    """Verifica contraseña contra hash bcrypt."""
    try:
        return bcrypt.checkpw(password_plano.strip().encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def crear_access_token(payload: dict[str, Any], expires_minutes: int | None = None) -> str:
    """Firma un token JWT HS256 con expiración."""
    exp_delta = timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES)
    to_encode = {
        **payload,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + exp_delta,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o token inválido. Inicie sesión nuevamente.",
        ) from exc


def construir_payload_usuario(
    usuario: str,
    rol: str,
    nombre_completo: str,
    documento_asociado: str | None,
    db: Session,
    es_demo: bool = False,
) -> dict[str, Any]:
    info: dict[str, Any] = {
        "sub": usuario,
        "usuario": usuario,
        "rol": rol,
        "nombre_completo": nombre_completo,
        "documento_asociado": documento_asociado or "",
        "es_demo": es_demo,
        "id_programa": None,
        "nombre_programa": None,
        "semestre": None,
    }
    if rol == "Estudiante" and documento_asociado:
        est = db.get(Estudiante, documento_asociado)
        if est:
            prog = db.get(Programa, est.id_programa)
            info["id_programa"] = est.id_programa
            info["nombre_programa"] = prog.nombre_programa if prog else est.id_programa
            info["semestre"] = est.semestre
    return info


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida.",
        )
    payload = decodificar_token(credentials.credentials)
    usuario = payload.get("sub")
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token malformado.")

    # Si es estudiante o usuario real, refrescar datos actuales del programa si existe
    user_db = db.get(Usuario, usuario)
    if user_db:
        return construir_payload_usuario(
            usuario=user_db.usuario,
            rol=user_db.rol,
            nombre_completo=user_db.nombre_completo,
            documento_asociado=user_db.documento_asociado,
            db=db,
            es_demo=bool(payload.get("es_demo", False)),
        )

    # Permitir sesiones de estudiante registrado directamente en tabla estudiantes
    if payload.get("rol") == "Estudiante" and payload.get("documento_asociado"):
        est = db.get(Estudiante, payload["documento_asociado"])
        if est:
            return construir_payload_usuario(
                usuario=est.id_estudiante,
                rol="Estudiante",
                nombre_completo=f"{est.nombre} {est.apellidos}",
                documento_asociado=est.id_estudiante,
                db=db,
                es_demo=bool(payload.get("es_demo", False)),
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="El usuario ya no existe en la base de datos.",
    )


def require_roles(*roles: str):
    """Dependencia RBAC para restringir endpoints por rol."""
    def _checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user.get("rol") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {', '.join(roles)}.",
            )
        return current_user
    return _checker
