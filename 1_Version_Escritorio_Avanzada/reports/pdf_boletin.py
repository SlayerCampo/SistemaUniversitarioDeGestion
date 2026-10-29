from __future__ import annotations
# ==============================================================================
# ARCHIVO: reports/pdf_boletin.py
# PROPÓSITO: Generar el Boletín / Certificado Oficial de Calificaciones en PDF
#            usando ReportLab Platypus, permitiendo elegir la ubicación y nombre
#            del archivo de salida.
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


def generar_pdf_notas(cedula: str, ruta_destino: str | Path | None = None) -> tuple[bool, str]:
    """
    Construye y exporta el Boletín Oficial de Calificaciones de un estudiante
    en `ruta_destino` (o en la carpeta por defecto si no se especifica).
    Retorna (exito: bool, ruta_o_mensaje_error: str).
    """
    libro = db.cargar_libro(solo_lectura=True)
    fila_est = db.buscar_fila(libro["Estudiantes"], 0, cedula)
    if not fila_est:
        libro.close()
        return False, f"El estudiante con documento '{cedula}' no existe."

    todas_matriculas = db.buscar_filas(libro["Matriculas"], 1, cedula)
    matriculas_activas = [
        m for m in todas_matriculas
        if len(m) < 7 or str(m[6]).strip().lower() == "activa"
    ]

    if not matriculas_activas:
        libro.close()
        return False, "El estudiante no registra materias activas para generar boletín."

    id_prog = str(fila_est[6]) if len(fila_est) > 6 else ""
    fila_prog = db.buscar_fila(libro["Programas"], 0, id_prog)
    nombre_programa = fila_prog[1] if fila_prog else id_prog

    encabezado_tabla = [["Código", "Asignatura", "Créd.", "Nota 1", "Nota 2", "Nota 3", "Definitiva", "Estado"]]
    filas_tabla = []

    suma_ponderada = 0.0
    creditos_calificados = 0
    creditos_aprobados = 0

    for m in matriculas_activas:
        id_matricula = str(m[0])
        id_materia = str(m[2])
        creditos = int(m[3]) if m[3] is not None else 0

        fila_materia = db.buscar_fila(libro["Materias"], 0, id_materia)
        nombre_materia = str(fila_materia[1]) if fila_materia else id_materia

        fila_nota = db.buscar_fila(libro["Notas"], 1, id_matricula)
        if fila_nota:
            n1 = f"{float(fila_nota[3]):.2f}"
            n2 = f"{float(fila_nota[4]):.2f}"
            n3 = f"{float(fila_nota[5]):.2f}"
            definitiva_val = float(fila_nota[6])
            definitiva_str = f"{definitiva_val:.2f}"
            estado = str(fila_nota[7])

            suma_ponderada += definitiva_val * creditos
            creditos_calificados += creditos
            if definitiva_val >= config.NOTA_APROBATORIA:
                creditos_aprobados += creditos
        else:
            n1, n2, n3, definitiva_str, estado = "-", "-", "-", "-", "Sin calificar"

        filas_tabla.append([
            id_materia, nombre_materia, str(creditos),
            n1, n2, n3, definitiva_str, estado
        ])

    libro.close()

    pps = round(suma_ponderada / creditos_calificados, 2) if creditos_calificados > 0 else 0.0
    filas_tabla.append([
        "", "PROMEDIO PONDERADO SEMESTRAL (PPS)", str(creditos_calificados),
        "", "", "", f"{pps:.2f}",
        f"Aprobados: {creditos_aprobados} Cr."
    ])

    datos_tabla = encabezado_tabla + filas_tabla

    ruta_pdf = Path(ruta_destino) if ruta_destino else (config.CARPETA_REPORTES_PDF / f"Reporte_Notas_{cedula}.pdf")
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
        "TituloBoletin",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor(config.COLOR_AZUL_UCC),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    estilo_subtitulo = ParagraphStyle(
        "SubBoletin",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#526579"),
        alignment=TA_CENTER,
        spaceAfter=14
    )
    estilo_info = ParagraphStyle(
        "InfoBoletin",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14
    )
    estilo_pie = ParagraphStyle(
        "PieBoletin",
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
    elementos.append(Paragraph("CERTIFICADO Y REPORTE OFICIAL DE CALIFICACIONES", estilo_subtitulo))

    fecha_hoy = date.today().strftime("%Y-%m-%d")
    codigo_verificacion = str(uuid.uuid4()).upper()[:12]
    info_html = (
        f"<b>Estudiante:</b> {fila_est[1]} {fila_est[2]} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
        f"<b>Documento:</b> {cedula}<br/>"
        f"<b>Programa Académico:</b> {nombre_programa} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
        f"<b>Semestre:</b> {fila_est[5]}<br/>"
        f"<b>Promedio Ponderado (PPS):</b> {pps:.2f} / 5.00 &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; "
        f"<b>Fecha de Emisión:</b> {fecha_hoy}"
    )
    elementos.append(Paragraph(info_html, estilo_info))
    elementos.append(Spacer(1, 0.6 * cm))

    tabla = Table(
        datos_tabla,
        colWidths=[2.0 * cm, 5.5 * cm, 1.5 * cm, 1.6 * cm, 1.6 * cm, 1.6 * cm, 2.0 * cm, 2.4 * cm]
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(config.COLOR_AZUL_UCC)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F8FAFC")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E3F2FD")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 0.8 * cm))

    elementos.append(Paragraph(
        f"Documento verificado electrónicamente — Código UCC: {codigo_verificacion}",
        estilo_pie
    ))

    doc.build(elementos)
    return True, str(ruta_pdf)
