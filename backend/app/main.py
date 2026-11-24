from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.db.seed import asegurar_base_inicial
from app.db.session import SessionLocal
from app.routers import auth, catalogo, etl_demo, matricula, notas, reportes


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        asegurar_base_inicial(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST centralizada sobre PostgreSQL para el Sistema Universitario UCC (Web, Escritorio y Android).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.pages\.dev",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(catalogo.router, prefix=API_PREFIX)
app.include_router(matricula.router, prefix=API_PREFIX)
app.include_router(notas.router, prefix=API_PREFIX)
app.include_router(reportes.router, prefix=API_PREFIX)
app.include_router(etl_demo.router, prefix=API_PREFIX)


@app.get("/health", tags=["Sistema"])
def health_check():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        db.close()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "postgresql_connected" if db_ok else "disconnected",
        "version": settings.APP_VERSION,
        "demo_mode": settings.DEMO_MODE,
    }
