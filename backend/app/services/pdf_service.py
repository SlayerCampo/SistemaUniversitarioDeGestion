from __future__ import annotations
"""Generación centralizada de Certificados Oficiales PDF con ReportLab desde PostgreSQL."""

from datetime import date
from io import BytesIO

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.horarios import BloqueHorario, formatear_horarios
from app.db.models import Asignatura, Estudiante, Grupo, Matricula, Nota


def _encabezado_pdf(elems: list, estilos):
    ruta_logo = settings.ruta_logo_ucc
    if ruta_logo.exists():
        img = Image(str(ruta_logo), width=2.5 * cm, height=2.1 * cm)
        img.hAlign = "CENTER"
        elems.append(img)
        elems.append(Spacer(1, 0.2 * cm))
    elems.append(
        Paragraph(
            "UNIVERSIDAD COOPERATIVA DE COLOMBIA — SEDE CALI",
            ParagraphStyle(
                "T_UCC",
                parent=estilos["Heading1"],
                alignment=TA_CENTER,
                textColor=colors.HexColor("#1F6AA5"),
                fontSize=14,
            ),
        )
    )
    elems.append(Spacer(1, 0.25 * cm))


def generar_pdf_matricula_bytes(db: Session, id_estudiante: str, id_periodo: str) -> bytes:
    est = db.execute(
        select(Estudiante).options(selectinload(Estudiante.programa)).where(Estudiante.id_estudiante == id_estudiante)
    ).scalar_one_or_none()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado.")

    mats = db.execute(
        select(Matricula)
        .options(
            selectinload(Matricula.grupo).selectinload(Grupo.asignatura),
            selectinload(Matricula.grupo).selectinload(Grupo.horarios),
        )
        .where(
            Matricula.id_estudiante == id_estudiante,
            Matricula.id_periodo == id_periodo,
            Matricula.estado == "Activa",
        )
    ).scalars().all()
    if not mats:
        raise HTTPException(status_code=400, detail="El estudiante no tiene asignaturas activas en este periodo.")

    nom_prog = est.programa.nombre_programa if est.programa else est.id_programa
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=1.8 * cm, leftMargin=1.8 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    estilos = getSampleStyleSheet()
    elems: list = []
    _encabezado_pdf(elems, estilos)

    elems.append(
        Paragraph(
            f"<b>Comprobante Oficial de Matrícula Académica</b><br/>"
            f"<b>Estudiante:</b> {est.nombre} {est.apellidos} &nbsp;&nbsp;|&nbsp;&nbsp; <b>ID:</b> {est.id_estudiante}<br/>"
            f"<b>Programa:</b> {est.id_programa} - {nom_prog} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Semestre:</b> {est.semestre}<br/>"
            f"<b>Periodo:</b> {id_periodo} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Emisión:</b> {date.today().isoformat()}",
            estilos["Normal"],
        )
    )
    elems.append(Spacer(1, 0.45 * cm))

    datos = [["Grupo", "Asignatura", "Cr.", "Docente", "Horario"]]
    total_cred = 0
    for m in mats:
        bloques = [BloqueHorario(h.dia_semana, h.hora_inicio, h.hora_fin) for h in m.grupo.horarios]
        datos.append([
            m.id_grupo,
            m.grupo.asignatura.nombre_curso,
            str(m.creditos),
            m.grupo.docente,
            formatear_horarios(bloques),
        ])
        total_cred += m.creditos
    datos.append(["", "TOTAL CRÉDITOS MATRICULADOS", str(total_cred), "", ""])

    tabla = Table(datos, colWidths=[2.6 * cm, 5.4 * cm, 1.2 * cm, 4.4 * cm, 4.4 * cm])
    tabla.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F6AA5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.2),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -2), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E0F2FE")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ])
    )
    elems.append(tabla)
    doc.build(elems)
    return buf.getvalue()


def generar_pdf_boletin_bytes(db: Session, id_estudiante: str, id_periodo: str) -> bytes:
    est = db.execute(
        select(Estudiante).options(selectinload(Estudiante.programa)).where(Estudiante.id_estudiante == id_estudiante)
    ).scalar_one_or_none()
    if not est:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado.")

    mats = db.execute(
        select(Matricula)
        .options(
            selectinload(Matricula.grupo).selectinload(Grupo.asignatura),
            selectinload(Matricula.nota),
        )
        .where(
            Matricula.id_estudiante == id_estudiante,
            Matricula.id_periodo == id_periodo,
            Matricula.estado == "Activa",
        )
    ).scalars().all()
    if not mats:
        raise HTTPException(status_code=400, detail="El estudiante no tiene materias activas para emitir boletín.")

    nom_prog = est.programa.nombre_programa if est.programa else est.id_programa
    datos = [["Grupo", "Asignatura", "Cr.", "C1 (30%)", "C2 (30%)", "C3 (40%)", "Def.", "Estado"]]
    suma_pond = 0.0
    cred_calif = 0

    for m in mats:
        n: Nota | None = m.nota
        if n and n.estado != "Sin calificar":
            n1, n2, n3, df, estado = float(n.nota1), float(n.nota2), float(n.nota3), float(n.definitiva), n.estado
            suma_pond += df * m.creditos
            cred_calif += m.creditos
            fila = [m.id_grupo, m.grupo.asignatura.nombre_curso, str(m.creditos), f"{n1:.2f}", f"{n2:.2f}", f"{n3:.2f}", f"{df:.2f}", estado]
        else:
            fila = [m.id_grupo, m.grupo.asignatura.nombre_curso, str(m.creditos), "—", "—", "—", "—", "Pendiente"]
        datos.append(fila)

    pps = round(suma_pond / cred_calif, 2) if cred_calif > 0 else 0.0
    datos.append(["", "PROMEDIO PONDERADO SEMESTRAL (PPS)", str(cred_calif), "", "", "", f"{pps:.2f}", "Aprobado" if pps >= settings.NOTA_APROBATORIA else "En curso"])

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=1.6 * cm, leftMargin=1.6 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    estilos = getSampleStyleSheet()
    elems: list = []
    _encabezado_pdf(elems, estilos)

    elems.append(
        Paragraph(
            f"<b>Boletín Oficial de Calificaciones</b><br/>"
            f"<b>Estudiante:</b> {est.nombre} {est.apellidos} &nbsp;&nbsp;|&nbsp;&nbsp; <b>ID:</b> {est.id_estudiante}<br/>"
            f"<b>Programa:</b> {est.id_programa} - {nom_prog} &nbsp;&nbsp;|&nbsp;&nbsp; <b>PPS:</b> {pps:.2f} / 5.00<br/>"
            f"<b>Periodo:</b> {id_periodo} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Emisión:</b> {date.today().isoformat()}",
            estilos["Normal"],
        )
    )
    elems.append(Spacer(1, 0.45 * cm))

    tabla = Table(datos, colWidths=[2.3 * cm, 5.5 * cm, 1.1 * cm, 1.7 * cm, 1.7 * cm, 1.7 * cm, 1.7 * cm, 2.3 * cm])
    tabla.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F6AA5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.2),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -2), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E0F2FE")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ])
    )
    elems.append(tabla)
    doc.build(elems)
    return buf.getvalue()
