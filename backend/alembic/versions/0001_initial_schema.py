"""Esquema inicial normalizado 3FN — Sistema Universitario UCC v2.0

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-23
"""
from __future__ import annotations
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "facultades",
        sa.Column("id_facultad", sa.String(30), primary_key=True),
        sa.Column("nombre_facultad", sa.String(150), nullable=False),
        sa.Column("decano", sa.String(150), nullable=False, server_default="Por asignar"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "programas",
        sa.Column("id_programa", sa.String(30), primary_key=True),
        sa.Column("nombre_programa", sa.String(150), nullable=False),
        sa.Column(
            "id_facultad",
            sa.String(30),
            sa.ForeignKey("facultades.id_facultad", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("semestres_duracion", sa.SmallInteger(), nullable=False, server_default="10"),
        sa.CheckConstraint("semestres_duracion >= 1 AND semestres_duracion <= 14", name="ck_programa_semestres"),
    )
    op.create_index("ix_programas_id_facultad", "programas", ["id_facultad"])

    op.create_table(
        "periodos",
        sa.Column("id_periodo", sa.String(20), primary_key=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
    )

    op.create_table(
        "asignaturas",
        sa.Column("id_asignatura", sa.String(30), primary_key=True),
        sa.Column("nombre_curso", sa.String(200), nullable=False),
        sa.Column("creditos", sa.SmallInteger(), nullable=False),
        sa.Column(
            "id_programa",
            sa.String(30),
            sa.ForeignKey("programas.id_programa", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.CheckConstraint("creditos >= 1 AND creditos <= 12", name="ck_asignatura_creditos"),
    )
    op.create_index("ix_asignaturas_id_programa", "asignaturas", ["id_programa"])

    op.create_table(
        "grupos",
        sa.Column("id_grupo", sa.String(40), primary_key=True),
        sa.Column(
            "id_asignatura",
            sa.String(30),
            sa.ForeignKey("asignaturas.id_asignatura", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "id_periodo",
            sa.String(20),
            sa.ForeignKey("periodos.id_periodo", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("docente", sa.String(150), nullable=False),
        sa.Column("cupos_totales", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("cupos_disponibles", sa.Integer(), nullable=False, server_default="30"),
        sa.CheckConstraint("cupos_totales >= 0", name="ck_grupo_cupos_totales"),
        sa.CheckConstraint("cupos_disponibles >= 0 AND cupos_disponibles <= cupos_totales", name="ck_grupo_cupos_disp"),
    )
    op.create_index("ix_grupos_id_asignatura", "grupos", ["id_asignatura"])
    op.create_index("ix_grupos_id_periodo", "grupos", ["id_periodo"])

    op.create_table(
        "horarios_grupo",
        sa.Column("id_horario", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "id_grupo",
            sa.String(40),
            sa.ForeignKey("grupos.id_grupo", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dia_semana", sa.SmallInteger(), nullable=False),
        sa.Column("hora_inicio", sa.SmallInteger(), nullable=False),
        sa.Column("hora_fin", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("dia_semana BETWEEN 1 AND 6", name="ck_horario_dia"),
        sa.CheckConstraint("hora_inicio >= 6 AND hora_fin <= 22", name="ck_horario_jornada"),
        sa.CheckConstraint("(hora_fin - hora_inicio) IN (2, 3, 4)", name="ck_horario_duracion"),
        sa.CheckConstraint("NOT (hora_inicio < 14 AND hora_fin > 13)", name="ck_horario_sin_almuerzo"),
    )
    op.create_index("ix_horarios_grupo_id_grupo", "horarios_grupo", ["id_grupo"])

    op.create_table(
        "estudiantes",
        sa.Column("id_estudiante", sa.String(30), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("apellidos", sa.String(100), nullable=False),
        sa.Column("correo", sa.String(150), nullable=False),
        sa.Column("telefono", sa.String(30), nullable=False),
        sa.Column("semestre", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column(
            "id_programa",
            sa.String(30),
            sa.ForeignKey("programas.id_programa", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.CheckConstraint("semestre >= 1 AND semestre <= 14", name="ck_estudiante_semestre"),
    )
    op.create_index("ix_estudiantes_id_programa", "estudiantes", ["id_programa"])

    op.create_table(
        "matriculas",
        sa.Column("id_matricula", sa.String(40), primary_key=True),
        sa.Column(
            "id_estudiante",
            sa.String(30),
            sa.ForeignKey("estudiantes.id_estudiante", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "id_grupo",
            sa.String(40),
            sa.ForeignKey("grupos.id_grupo", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "id_periodo",
            sa.String(20),
            sa.ForeignKey("periodos.id_periodo", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("creditos", sa.SmallInteger(), nullable=False),
        sa.Column("fecha_matricula", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Activa"),
        sa.CheckConstraint("creditos > 0", name="ck_matricula_creditos"),
        sa.CheckConstraint("estado IN ('Activa', 'Cancelada', 'Finalizada')", name="ck_matricula_estado"),
    )
    op.create_index("ix_matriculas_id_estudiante", "matriculas", ["id_estudiante"])
    op.create_index("ix_matriculas_id_grupo", "matriculas", ["id_grupo"])
    op.create_index("ix_matriculas_id_periodo", "matriculas", ["id_periodo"])
    op.create_index(
        "uq_matricula_activa_est_grupo",
        "matriculas",
        ["id_estudiante", "id_grupo", "id_periodo"],
        unique=True,
        postgresql_where=sa.text("estado = 'Activa'"),
    )

    op.create_table(
        "notas",
        sa.Column("id_nota", sa.String(40), primary_key=True),
        sa.Column(
            "id_matricula",
            sa.String(40),
            sa.ForeignKey("matriculas.id_matricula", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("nota1", sa.Numeric(4, 2), nullable=False, server_default="0.00"),
        sa.Column("nota2", sa.Numeric(4, 2), nullable=False, server_default="0.00"),
        sa.Column("nota3", sa.Numeric(4, 2), nullable=False, server_default="0.00"),
        sa.Column("definitiva", sa.Numeric(4, 2), nullable=False, server_default="0.00"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="Sin calificar"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("nota1 >= 0.0 AND nota1 <= 5.0", name="ck_nota1_rango"),
        sa.CheckConstraint("nota2 >= 0.0 AND nota2 <= 5.0", name="ck_nota2_rango"),
        sa.CheckConstraint("nota3 >= 0.0 AND nota3 <= 5.0", name="ck_nota3_rango"),
        sa.CheckConstraint("definitiva >= 0.0 AND definitiva <= 5.0", name="ck_definitiva_rango"),
        sa.CheckConstraint("estado IN ('Aprobado', 'Reprobado', 'Sin calificar')", name="ck_nota_estado"),
    )
    op.create_index("ix_notas_id_matricula", "notas", ["id_matricula"])

    op.create_table(
        "usuarios",
        sa.Column("usuario", sa.String(60), primary_key=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("nombre_completo", sa.String(150), nullable=False),
        sa.Column("documento_asociado", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rol IN ('Administrador', 'Profesor', 'Estudiante')", name="ck_usuario_rol"),
    )


def downgrade() -> None:
    for tbl in (
        "usuarios",
        "notas",
        "matriculas",
        "estudiantes",
        "horarios_grupo",
        "grupos",
        "asignaturas",
        "periodos",
        "programas",
        "facultades",
    ):
        op.drop_table(tbl)
