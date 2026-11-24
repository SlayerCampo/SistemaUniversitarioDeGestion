from __future__ import annotations
"""
Módulo ETL Excel (OpenPyXL) sobre PostgreSQL:
Excel ya NO es la base de datos principal; cumple su rol profesional:
1. Generar archivo Excel de simulación (50+ estudiantes, 240 grupos) para revisión/importación manual.
2. Importar archivos `.xlsx` hacia PostgreSQL de forma idempotente (sin duplicados),
   normalizando automáticamente asignaturas, grupos y horarios.
3. Exportar la sábana consolidada desde PostgreSQL a `.xlsx`.
"""

from datetime import date
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.horarios import (
    BloqueHorario,
    codigo_base_asignatura,
    formatear_horarios,
    parsear_texto_horario,
    validar_bloque_institucional,
)
from app.core.security import hash_password
from app.db.models import (
    Asignatura,
    Estudiante,
    Facultad,
    Grupo,
    HorarioGrupo,
    Matricula,
    Nota,
    Periodo,
    Programa,
    Usuario,
)
from app.db.seed import asegurar_base_inicial, calcular_definitiva_y_estado, construir_dataset_simulacion

ENCABEZADOS_EXCEL = {
    "Facultades": ["ID_Facultad", "Nombre_Facultad", "Decano"],
    "Programas": ["ID_Programa", "Nombre_Programa", "ID_Facultad", "Semestres_Duracion"],
    "Materias": ["ID_Materia", "Nombre_Curso", "Creditos", "Cupos", "Docente", "ID_Programa", "Horario"],
    "Estudiantes": ["ID_Estudiante", "Nombre", "Apellidos", "Correo", "Telefono", "Semestre", "ID_Programa"],
    "Matriculas": ["ID_Matricula", "Cedula", "ID_Materia", "Creditos", "Periodo", "Fecha_Matricula", "Estado"],
    "Notas": ["ID_Nota", "ID_Matricula", "ID_Materia", "Nota1", "Nota2", "Nota3", "Definitiva", "Estado"],
}


def _crear_libro_con_formato() -> Workbook:
    libro = Workbook()
    primera = True
    fill_ucc = PatternFill(start_color="1F6AA5", end_color="1F6AA5", fill_type="solid")
    font_ucc = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

    for nombre_hoja, cols in ENCABEZADOS_EXCEL.items():
        hoja = libro.active if primera else libro.create_sheet(nombre_hoja)
        hoja.title = nombre_hoja
        primera = False
        hoja.append(cols)
        for idx in range(1, len(cols) + 1):
            celda = hoja.cell(row=1, column=idx)
            celda.fill = fill_ucc
            celda.font = font_ucc
            celda.alignment = Alignment(horizontal="center", vertical="center")
            hoja.column_dimensions[get_column_letter(idx)].width = 22
        hoja.freeze_panes = "A2"
    return libro


def generar_excel_simulacion_bytes(total_estudiantes: int = 50) -> bytes:
    """Construye en memoria el archivo Excel de 50+ estudiantes sin alterar la BD activa."""
    data = construir_dataset_simulacion(total_estudiantes=total_estudiantes)
    libro = _crear_libro_con_formato()

    for f in data["facultades"]:
        libro["Facultades"].append(list(f))
    for p in data["programas"]:
        libro["Programas"].append(list(p))
    for g in data["grupos"]:
        libro["Materias"].append([
            g["id_grupo"],
            g["nombre_curso"],
            g["creditos"],
            g["cupos_disponibles"],
            g["docente"],
            g["id_programa"],
            g["bloque"].formato_texto(),
        ])
    for e in data["estudiantes"]:
        libro["Estudiantes"].append([
            e["id_estudiante"], e["nombre"], e["apellidos"],
            e["correo"], e["telefono"], e["semestre"], e["id_programa"],
        ])
    for m in data["matriculas"]:
        libro["Matriculas"].append([
            m["id_matricula"], m["id_estudiante"], m["id_grupo"],
            m["creditos"], m["id_periodo"], m["fecha_matricula"].isoformat(), m["estado"],
        ])
    mapa_mat_grupo = {m["id_matricula"]: m["id_grupo"] for m in data["matriculas"]}
    for n in data["notas"]:
        libro["Notas"].append([
            n["id_nota"], n["id_matricula"], mapa_mat_grupo.get(n["id_matricula"], ""),
            float(n["nota1"]), float(n["nota2"]), float(n["nota3"]),
            float(n["definitiva"]), n["estado"],
        ])

    buf = BytesIO()
    libro.save(buf)
    libro.close()
    return buf.getvalue()


def exportar_excel_desde_postgres(db: Session) -> bytes:
    """Exporta todos los datos vivos de PostgreSQL a un libro Excel corporativo."""
    libro = _crear_libro_con_formato()

    for f in db.execute(select(Facultad).order_by(Facultad.id_facultad)).scalars().all():
        libro["Facultades"].append([f.id_facultad, f.nombre_facultad, f.decano])

    for p in db.execute(select(Programa).order_by(Programa.id_programa)).scalars().all():
        libro["Programas"].append([p.id_programa, p.nombre_programa, p.id_facultad, p.semestres_duracion])

    grupos = db.execute(
        select(Grupo).options(selectinload(Grupo.asignatura), selectinload(Grupo.horarios)).order_by(Grupo.id_grupo)
    ).scalars().all()
    for g in grupos:
        bloques = [BloqueHorario(h.dia_semana, h.hora_inicio, h.hora_fin) for h in g.horarios]
        libro["Materias"].append([
            g.id_grupo,
            g.asignatura.nombre_curso,
            g.asignatura.creditos,
            g.cupos_disponibles,
            g.docente,
            g.asignatura.id_programa,
            formatear_horarios(bloques),
        ])

    for e in db.execute(select(Estudiante).order_by(Estudiante.id_estudiante)).scalars().all():
        libro["Estudiantes"].append([
            e.id_estudiante, e.nombre, e.apellidos, e.correo, e.telefono, e.semestre, e.id_programa
        ])

    mats = db.execute(select(Matricula).order_by(Matricula.id_matricula)).scalars().all()
    mapa_mat_g = {m.id_matricula: m.id_grupo for m in mats}
    for m in mats:
        libro["Matriculas"].append([
            m.id_matricula, m.id_estudiante, m.id_grupo,
            m.creditos, m.id_periodo, m.fecha_matricula.isoformat(), m.estado,
        ])

    for n in db.execute(select(Nota).order_by(Nota.id_nota)).scalars().all():
        libro["Notas"].append([
            n.id_nota, n.id_matricula, mapa_mat_g.get(n.id_matricula, ""),
            float(n.nota1), float(n.nota2), float(n.nota3), float(n.definitiva), n.estado,
        ])

    buf = BytesIO()
    libro.save(buf)
    libro.close()
    return buf.getvalue()


def importar_excel_a_postgres(db: Session, contenido_bytes: bytes) -> dict:
    """Importa un archivo Excel (.xlsx) a PostgreSQL de forma idempotente sin duplicar registros."""
    asegurar_base_inicial(db)
    libro = load_workbook(BytesIO(contenido_bytes), data_only=True)
    periodo_def = settings.PERIODO_ACTIVO_DEFECTO

    insertados = {
        "Facultades": 0, "Programas": 0, "Asignaturas": 0,
        "Grupos": 0, "Estudiantes": 0, "Matriculas": 0, "Notas": 0,
    }
    duplicados = 0
    errores: list[str] = []

    # 1. Facultades
    if "Facultades" in libro.sheetnames:
        for row in libro["Facultades"].iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            fid = str(row[0]).strip()
            if db.get(Facultad, fid):
                duplicados += 1
                continue
            db.add(Facultad(id_facultad=fid, nombre_facultad=str(row[1]), decano=str(row[2] or "Por asignar")))
            insertados["Facultades"] += 1
        db.flush()

    # 2. Programas
    if "Programas" in libro.sheetnames:
        for row in libro["Programas"].iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            pid = str(row[0]).strip()
            if db.get(Programa, pid):
                duplicados += 1
                continue
            fid = str(row[2]).strip()
            if not db.get(Facultad, fid):
                errores.append(f"Programa '{pid}': Facultad '{fid}' no existe.")
                continue
            db.add(Programa(id_programa=pid, nombre_programa=str(row[1]), id_facultad=fid, semestres_duracion=int(row[3] or 10)))
            insertados["Programas"] += 1
        db.flush()

    # 3. Materias -> Asignaturas + Grupos + HorariosGrupo
    if "Materias" in libro.sheetnames:
        for row in libro["Materias"].iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            gid = str(row[0]).strip()
            nom = str(row[1]).strip()
            cred = int(row[2] or 3)
            cupos = max(0, int(row[3] or 30))
            docente = str(row[4] or "Por asignar").strip()
            pid = str(row[5]).strip()
            horario_txt = str(row[6] or "").strip()

            if not db.get(Programa, pid):
                errores.append(f"Grupo '{gid}': Programa '{pid}' no existe.")
                continue

            cod_asig = codigo_base_asignatura(gid)
            if not db.get(Asignatura, cod_asig):
                db.add(Asignatura(id_asignatura=cod_asig, nombre_curso=nom, creditos=cred, id_programa=pid))
                insertados["Asignaturas"] += 1
                db.flush()

            if db.get(Grupo, gid):
                duplicados += 1
                continue

            bloques = parsear_texto_horario(horario_txt)
            bloques_validos: list[BloqueHorario] = []
            for b in bloques:
                ok, msg = validar_bloque_institucional(b.dia_semana, b.hora_inicio, b.hora_fin)
                if ok:
                    bloques_validos.append(b)
                else:
                    errores.append(f"Horario omitido en '{gid}': {msg}")

            db.add(
                Grupo(
                    id_grupo=gid,
                    id_asignatura=cod_asig,
                    id_periodo=periodo_def,
                    docente=docente,
                    cupos_totales=max(cupos, 30),
                    cupos_disponibles=cupos,
                )
            )
            for b in bloques_validos:
                db.add(HorarioGrupo(id_grupo=gid, dia_semana=b.dia_semana, hora_inicio=b.hora_inicio, hora_fin=b.hora_fin))
            insertados["Grupos"] += 1
        db.flush()

    # 4. Estudiantes (+ cuenta Usuario con bcrypt)
    if "Estudiantes" in libro.sheetnames:
        hash_default = hash_password("1234")
        for row in libro["Estudiantes"].iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            eid = str(row[0]).strip()
            if db.get(Estudiante, eid):
                duplicados += 1
                continue
            pid = str(row[6]).strip()
            if not db.get(Programa, pid):
                errores.append(f"Estudiante '{eid}': Programa '{pid}' no existe.")
                continue
            nom, ape = str(row[1]).strip(), str(row[2]).strip()
            db.add(
                Estudiante(
                    id_estudiante=eid,
                    nombre=nom,
                    apellidos=ape,
                    correo=str(row[3] or f"{eid}@campusucc.edu.co").strip(),
                    telefono=str(row[4] or "3000000000").strip(),
                    semestre=max(1, min(14, int(row[5] or 1))),
                    id_programa=pid,
                )
            )
            if not db.get(Usuario, eid):
                db.add(
                    Usuario(
                        usuario=eid,
                        password_hash=hash_default,
                        rol="Estudiante",
                        nombre_completo=f"{nom} {ape}",
                        documento_asociado=eid,
                    )
                )
            insertados["Estudiantes"] += 1
        db.flush()

    # 5. Matriculas
    if "Matriculas" in libro.sheetnames:
        for row in libro["Matriculas"].iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            mid = str(row[0]).strip()
            if db.get(Matricula, mid):
                duplicados += 1
                continue
            eid = str(row[1]).strip()
            gid = str(row[2]).strip()
            cred = int(row[3] or 3)
            per = str(row[4] or periodo_def).strip()
            estado = str(row[6] or "Activa").strip() if len(row) > 6 else "Activa"
            if estado not in ("Activa", "Cancelada", "Finalizada"):
                estado = "Activa"

            if not db.get(Estudiante, eid) or not db.get(Grupo, gid):
                continue
            if not db.get(Periodo, per):
                db.add(Periodo(id_periodo=per, activo=False))
                db.flush()

            try:
                fecha_m = date.fromisoformat(str(row[5])[:10]) if row[5] else date.today()
            except Exception:
                fecha_m = date.today()

            db.add(
                Matricula(
                    id_matricula=mid,
                    id_estudiante=eid,
                    id_grupo=gid,
                    id_periodo=per,
                    creditos=cred,
                    fecha_matricula=fecha_m,
                    estado=estado,
                )
            )
            insertados["Matriculas"] += 1
        db.flush()

    # 6. Notas
    if "Notas" in libro.sheetnames:
        for row in libro["Notas"].iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            nid = str(row[0]).strip()
            mid = str(row[1]).strip()
            if db.get(Nota, nid) or not db.get(Matricula, mid):
                duplicados += 1
                continue
            ya_existe = db.execute(select(Nota).where(Nota.id_matricula == mid)).scalar_one_or_none()
            if ya_existe:
                duplicados += 1
                continue
            n1 = float(row[3] or 0.0)
            n2 = float(row[4] or 0.0)
            n3 = float(row[5] or 0.0)
            def_val, est_nota = calcular_definitiva_y_estado(n1, n2, n3)
            db.add(
                Nota(
                    id_nota=nid,
                    id_matricula=mid,
                    nota1=Decimal(f"{n1:.2f}"),
                    nota2=Decimal(f"{n2:.2f}"),
                    nota3=Decimal(f"{n3:.2f}"),
                    definitiva=def_val,
                    estado=est_nota,
                )
            )
            insertados["Notas"] += 1

    db.commit()
    libro.close()
    return {"insertados": insertados, "duplicados": duplicados, "errores": errores[:20]}
