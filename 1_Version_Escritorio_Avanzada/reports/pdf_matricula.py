from __future__ import annotations
# ==============================================================================
# ARCHIVO: reports/pdf_matricula.py
# PROPÓSITO: Generar el Recibo / Comprobante Oficial de Matrícula Académica en
#            formato PDF utilizando ReportLab Platypus, permitiendo guardar el
#            documento en la ubicación y con el nombre que el usuario elija.
# ==============================================================================

from datetime import date
from pathlib import Path
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

import config
import data.db_excel as db


def generar_pdf_matricula(cedula: str, ruta_destino: str | Path | None = None) -> tuple[bool, str]:
    """
    Construye y exporta el PDF del comprobante de matrícula de un estudiante
    en `ruta_destino` (o en la carpeta por defecto si no se especifica).
    Retorna (exito: bool, ruta_o_mensaje_error: str).
    """
    libro = db.cargar_libro(solo_lectura=True)
    fila_est = db.buscar_fila(libro["Estudiantes"], 0, cedula)
    if not fila_est:
        libro.close()
        return False, f"No existe ningún estudiante registrado con la cédula '{cedula}'."

    todas_matriculas = db.buscar_filas(libro["Matriculas"], 1, cedula)
    matriculas_activas = [
        m for m in todas_matriculas
        if len(m) < 7 or str(m[6]).strip().lower() == "activa"
    ]

    if not matriculas_activas:
        libro.close()
        return False, "El estudiante no tiene asignaturas activas matriculadas actualmente."

    id_prog = str(fila_est[6]) if len(fila_est) > 6 else ""
    fila_prog = db.buscar_fila(libro["Programas"], 0, id_prog)
    nombre_programa = fila_prog[1] if fila_prog else id_prog

    encabezado_tabla = [["Código", "Asignatura", "Docente", "Horario", "Créd.", "Periodo"]]
    filas_tabla = []
    total_creditos = 0

    for m in matriculas_activas:
        id_materia = str(m[2])
        fila_mat = db.buscar_fila(libro["Materias"], 0, id_materia)
        nombre_mat = str(fila_mat[1]) if fila_mat else id_materia
        docente_mat = str(fila_mat[4]) if fila_mat and len(fila_mat) > 4 else "Por asignar"
        horario_mat = str(fila_mat[6]) if fila_mat and len(fila_mat) > 6 else "Por definir"
        creditos = int(m[3]) if m[3] is not None else 0
        periodo = str(m[4])
        total_creditos += creditos

        filas_tabla.append([id_materia, nombre_mat, docente_mat, horario_mat, str(creditos), periodo])

    libro.close()

    filas_tabla.append(["", "TOTAL CRÉDITOS MATRICULADOS", "", "", str(total_creditos), ""])
    datos_tabla = encabezado_tabla + filas_tabla

    ruta_pdf = Path(ruta_destino) if ruta_destino else (config.CARPETA_REPORTES_PDF / f"Recibo_Matricula_{cedula}.pdf")
    doc = SimpleDocTemplate(
        str(ruta_pdf),
        pagesize=letter,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloUCC",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor(config.COLOR_AZUL_UCC),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloUCC",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#526579"),
        alignment=TA_CENTER,
        spaceAfter=14
    )
    estilo_info = ParagraphStyle(
        "InfoEstudiante",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14
    )
    estilo_pie = ParagraphStyle(
        "PieVerificacion",
        parent=estilos["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_RIGHT
    )

    elementos = []

    if config.RUTA_LOGO_UCC.exists():
        img_logo = Image(str(config.RUTA_LOGO_UCC), width=2.8 * cm, height=2.8 * cm)
        img_logo.hAlign = "CENTER"
        elementos.append(img_logo)
        elementos.append(Spacer(1, 0.3 * cm))

    elementos.append(Paragraph("UNIVERSIDAD COOPERATIVA DE COLOMBIA", estilo_titulo))
    elementos.append(Paragraph("COMPROBANTE OFICIAL DE MATRÍCULA ACADÉMICA — SEDE CALI", estilo_subtitulo))

    fecha_hoy = date.today().strftime("%Y-%m-%d")
    codigo_verificacion = str(uuid.uuid4()).upper()[:12]
    info_html = (
        f"<b>Estudiante:</b> {fila_est[1]} {fila_est[2]} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
        f"<b>Documento (Cédula):</b> {cedula}<br/>"
        f"<b>Programa Académico:</b> {nombre_programa} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
        f"<b>Semestre:</b> {fila_est[5]}<br/>"
        f"<b>Correo Institucional:</b> {fila_est[3]} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
        f"<b>Fecha de Expedición:</b> {fecha_hoy}"
    )
    elementos.append(Paragraph(info_html, estilo_info))
    elementos.append(Spacer(1, 0.6 * cm))

    tabla = Table(
        datos_tabla,
        colWidths=[2.0 * cm, 4.8 * cm, 3.6 * cm, 4.4 * cm, 1.5 * cm, 1.8 * cm]
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(config.COLOR_VERDE_EXITO)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F5E9")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.8 * cm))

    elementos.append(Paragraph(
        f"Código Único de Verificación Electrónica UCC: {codigo_verificacion} — Estado: MATRÍCULA ACTIVA",
        estilo_pie
    ))

    doc.build(elementos)
    return True, str(ruta_pdf)
