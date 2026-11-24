from __future__ import annotations
from datetime import date
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    usuario: str = Field(..., min_length=1, max_length=60)
    password: str = Field(..., min_length=1, max_length=128)


class DemoSwitchRequest(BaseModel):
    perfil: str = Field(..., description="'admin', 'profe' o id_estudiante (ej. '1001')")


class UserInfo(BaseModel):
    usuario: str
    rol: str
    nombre_completo: str
    documento_asociado: str = ""
    es_demo: bool = False
    id_programa: str | None = None
    nombre_programa: str | None = None
    semestre: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class FacultadCreate(BaseModel):
    id_facultad: str = Field(..., min_length=2, max_length=30)
    nombre_facultad: str = Field(..., min_length=3, max_length=150)
    decano: str = Field(default="Por asignar", max_length=150)


class ProgramaCreate(BaseModel):
    id_programa: str = Field(..., min_length=2, max_length=30)
    nombre_programa: str = Field(..., min_length=3, max_length=150)
    id_facultad: str = Field(..., min_length=2, max_length=30)
    semestres_duracion: int = Field(default=10, ge=1, le=14)


class HorarioCreate(BaseModel):
    dia_semana: int = Field(..., ge=1, le=6)
    hora_inicio: int = Field(..., ge=6, le=20)
    hora_fin: int = Field(..., ge=8, le=22)


class GrupoOfertaCreate(BaseModel):
    id_grupo: str = Field(..., min_length=3, max_length=40, description="Ej: SIS101-G1")
    id_asignatura: str | None = Field(default=None, max_length=30, description="Ej: SIS101")
    nombre_curso: str = Field(..., min_length=3, max_length=200)
    creditos: int = Field(..., ge=2, le=4)
    id_programa: str = Field(..., min_length=2, max_length=30)
    docente: str = Field(..., min_length=3, max_length=150)
    cupos_totales: int = Field(default=30, ge=1, le=200)
    horarios: list[HorarioCreate] = Field(..., min_length=1)


class EstudianteCreate(BaseModel):
    id_estudiante: str = Field(..., min_length=2, max_length=30)
    nombre: str = Field(..., min_length=2, max_length=100)
    apellidos: str = Field(..., min_length=2, max_length=100)
    correo: str = Field(..., min_length=5, max_length=150)
    telefono: str = Field(..., min_length=5, max_length=30)
    semestre: int = Field(..., ge=1, le=14)
    id_programa: str = Field(..., min_length=2, max_length=30)
    password: str = Field(default="1234", min_length=4, max_length=64)


class MatriculaValidarRequest(BaseModel):
    id_estudiante: str
    id_periodo: str = "2026-2"
    grupos_ids: list[str]


class CalificacionItem(BaseModel):
    id_matricula: str
    nota1: float = Field(..., ge=0.0, le=5.0)
    nota2: float = Field(..., ge=0.0, le=5.0)
    nota3: float = Field(..., ge=0.0, le=5.0)


class CalificarLoteRequest(BaseModel):
    calificaciones: list[CalificacionItem] = Field(..., min_length=1)


class VaciarBDRequest(BaseModel):
    confirmacion: str = Field(..., description="Debe ser exactamente 'VACIAR'")
