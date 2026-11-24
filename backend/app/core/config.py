from __future__ import annotations
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalizar_database_url(url: str) -> str:
    """Garantiza driver psycopg3 aunque el usuario pegue una URI estándar de Supabase/Postgres."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Sistema Universitario UCC API"
    APP_VERSION: str = "2.0.0"

    DATABASE_URL: str = "postgresql+psycopg://ucc_admin:ucc_local_dev_2026@postgres:5432/universidad_ucc"
    JWT_SECRET_KEY: str = "ucc-dev-secret-cambiar-en-produccion-2026-clave-segura"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    DEMO_MODE: bool = True
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://tauri.localhost,https://tauri.localhost,"
        "capacitor://localhost,http://localhost,https://localhost"
    )

    # Reglas de negocio institucionales UCC
    CREDITOS_MINIMOS: int = 6
    CREDITOS_MAXIMOS: int = 19
    NOTA_MINIMA: float = 0.0
    NOTA_MAXIMA: float = 5.0
    NOTA_APROBATORIA: float = 3.0
    PERIODO_ACTIVO_DEFECTO: str = "2026-2"

    HORA_APERTURA: int = 6
    HORA_CIERRE: int = 22
    HORA_ALMUERZO_INICIO: int = 13
    HORA_ALMUERZO_FIN: int = 14
    DURACIONES_PERMITIDAS: tuple[int, ...] = (2, 3, 4)

    # Ponderación oficial de cortes (30%, 30%, 40%)
    PESO_CORTE_1: float = 0.30
    PESO_CORTE_2: float = 0.30
    PESO_CORTE_3: float = 0.40

    @property
    def sqlalchemy_database_url(self) -> str:
        return _normalizar_database_url(self.DATABASE_URL)

    @property
    def cors_origins_list(self) -> list[str]:
        raw = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return raw or ["*"]

    @property
    def ruta_logo_ucc(self) -> Path:
        candidatos = [
            Path("/app/assets/logo_ucc.png"),
            Path(__file__).resolve().parents[3] / "assets" / "logo_ucc.png",
        ]
        for p in candidatos:
            if p.exists():
                return p
        return candidatos[0]


settings = Settings()
