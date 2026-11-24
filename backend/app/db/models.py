from __future__ import annotations
"""
Esquema relacional PostgreSQL normalizado (3FN) siguiendo Supabase Postgres Best Practices:
- 10 tablas: facultades, programas, periodos, asignaturas, grupos, horarios_grupo,
  estudiantes, matriculas, notas, usuarios.
- Índices explícitos en todas las Foreign Keys.
- Restricciones CHECK físicas para la franja de almuerzo (13:00-14:00), cupos >= 0 y notas 0.0-5.0.
- Índice único parcial para impedir doble matrícula activa en el mismo grupo/periodo.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Facultad(Base):
    __tablename__ = "facultades"

    id_facultad: Mapped[str] = mapped_column(String(30), primary_key=True)
    nombre_facultad: Mapped[str] = mapped_column(String(150), nullable=False)
    decano: Mapped[str] = mapped_column(String(150), nullable=False, server_default="Por asignar")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    programas: Mapped[list["Programa"]] = relationship(back_populates="facultad")


class Programa(Base):
    __tablename__ = "programas"
    __table_args__ = (
        CheckConstraint("semestres_duracion >= 1 AND semestres_duracion <= 14", name="ck_programa_semestres"),
        Index("ix_programas_id_facultad", "id_facultad"),
    )

    id_programa: Mapped[str] = mapped_column(String(30), primary_key=True)
    nombre_programa: Mapped[str] = mapped_column(String(150), nullable=False)
    id_facultad: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("facultades.id_facultad", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    semestres_duracion: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="10")

    facultad: Mapped["Facultad"] = relationship(back_populates="programas")
    asignaturas: Mapped[list["Asignatura"]] = relationship(back_populates="programa")
    estudiantes: Mapped[list["Estudiante"]] = relationship(back_populates="programa")


class Periodo(Base):
    __tablename__ = "periodos"

    id_periodo: Mapped[str] = mapped_column(String(20), primary_key=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)


class Asignatura(Base):
    __tablename__ = "asignaturas"
    __table_args__ = (
        CheckConstraint("creditos >= 1 AND creditos <= 12", name="ck_asignatura_creditos"),
        Index("ix_asignaturas_id_programa", "id_programa"),
    )

    id_asignatura: Mapped[str] = mapped_column(String(30), primary_key=True)
    nombre_curso: Mapped[str] = mapped_column(String(200), nullable=False)
    creditos: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    id_programa: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("programas.id_programa", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )

    programa: Mapped["Programa"] = relationship(back_populates="asignaturas")
    grupos: Mapped[list["Grupo"]] = relationship(back_populates="asignatura", cascade="all, delete-orphan")


class Grupo(Base):
    __tablename__ = "grupos"
    __table_args__ = (
        CheckConstraint("cupos_totales >= 0", name="ck_grupo_cupos_totales"),
        CheckConstraint("cupos_disponibles >= 0 AND cupos_disponibles <= cupos_totales", name="ck_grupo_cupos_disp"),
        Index("ix_grupos_id_asignatura", "id_asignatura"),
        Index("ix_grupos_id_periodo", "id_periodo"),
    )

    id_grupo: Mapped[str] = mapped_column(String(40), primary_key=True)
    id_asignatura: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("asignaturas.id_asignatura", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_periodo: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("periodos.id_periodo", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    docente: Mapped[str] = mapped_column(String(150), nullable=False)
    cupos_totales: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    cupos_disponibles: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")

    asignatura: Mapped["Asignatura"] = relationship(back_populates="grupos")
    horarios: Mapped[list["HorarioGrupo"]] = relationship(back_populates="grupo", cascade="all, delete-orphan")


class HorarioGrupo(Base):
    __tablename__ = "horarios_grupo"
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 1 AND 6", name="ck_horario_dia"),
        CheckConstraint("hora_inicio >= 6 AND hora_fin <= 22", name="ck_horario_jornada"),
        CheckConstraint("(hora_fin - hora_inicio) IN (2, 3, 4)", name="ck_horario_duracion"),
        CheckConstraint("NOT (hora_inicio < 14 AND hora_fin > 13)", name="ck_horario_sin_almuerzo"),
        Index("ix_horarios_grupo_id_grupo", "id_grupo"),
    )

    id_horario: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_grupo: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("grupos.id_grupo", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_inicio: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_fin: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    grupo: Mapped["Grupo"] = relationship(back_populates="horarios")


class Estudiante(Base):
    __tablename__ = "estudiantes"
    __table_args__ = (
        CheckConstraint("semestre >= 1 AND semestre <= 14", name="ck_estudiante_semestre"),
        Index("ix_estudiantes_id_programa", "id_programa"),
    )

    id_estudiante: Mapped[str] = mapped_column(String(30), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), nullable=False)
    telefono: Mapped[str] = mapped_column(String(30), nullable=False)
    semestre: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="1")
    id_programa: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("programas.id_programa", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )

    programa: Mapped["Programa"] = relationship(back_populates="estudiantes")
    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="estudiante")


class Matricula(Base):
    __tablename__ = "matriculas"
    __table_args__ = (
        CheckConstraint("creditos > 0", name="ck_matricula_creditos"),
        CheckConstraint("estado IN ('Activa', 'Cancelada', 'Finalizada')", name="ck_matricula_estado"),
        Index("ix_matriculas_id_estudiante", "id_estudiante"),
        Index("ix_matriculas_id_grupo", "id_grupo"),
        Index("ix_matriculas_id_periodo", "id_periodo"),
        Index(
            "uq_matricula_activa_est_grupo",
            "id_estudiante",
            "id_grupo",
            "id_periodo",
            unique=True,
            postgresql_where=text("estado = 'Activa'"),
        ),
    )

    id_matricula: Mapped[str] = mapped_column(String(40), primary_key=True)
    id_estudiante: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("estudiantes.id_estudiante", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_grupo: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("grupos.id_grupo", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    id_periodo: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("periodos.id_periodo", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    creditos: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    fecha_matricula: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="Activa")

    estudiante: Mapped["Estudiante"] = relationship(back_populates="matriculas")
    grupo: Mapped["Grupo"] = relationship()
    nota: Mapped["Nota | None"] = relationship(back_populates="matricula", uselist=False, cascade="all, delete-orphan")


class Nota(Base):
    __tablename__ = "notas"
    __table_args__ = (
        CheckConstraint("nota1 >= 0.0 AND nota1 <= 5.0", name="ck_nota1_rango"),
        CheckConstraint("nota2 >= 0.0 AND nota2 <= 5.0", name="ck_nota2_rango"),
        CheckConstraint("nota3 >= 0.0 AND nota3 <= 5.0", name="ck_nota3_rango"),
        CheckConstraint("definitiva >= 0.0 AND definitiva <= 5.0", name="ck_definitiva_rango"),
        CheckConstraint("estado IN ('Aprobado', 'Reprobado', 'Sin calificar')", name="ck_nota_estado"),
        Index("ix_notas_id_matricula", "id_matricula"),
    )

    id_nota: Mapped[str] = mapped_column(String(40), primary_key=True)
    id_matricula: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("matriculas.id_matricula", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    nota1: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default="0.00")
    nota2: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default="0.00")
    nota3: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default="0.00")
    definitiva: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, server_default="0.00")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default="Sin calificar")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    matricula: Mapped["Matricula"] = relationship(back_populates="nota")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("rol IN ('Administrador', 'Profesor', 'Estudiante')", name="ck_usuario_rol"),
    )

    usuario: Mapped[str] = mapped_column(String(60), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    documento_asociado: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
