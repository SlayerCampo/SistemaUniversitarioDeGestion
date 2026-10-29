from __future__ import annotations
# ==============================================================================
# ARCHIVO: data/etl_excel.py
# PROPÓSITO: Módulo ETL (Extracción, Transformación y Carga Masiva) con OpenPyXL.
#            Permite:
#            1. Generar plantillas de Excel eligiendo dónde guardarlas.
#            2. Importar lotes de Estudiantes, Materias o una Base de Datos
#               Universitaria Completa (50+ estudiantes, matrículas y notas)
#               seleccionando el archivo desde el Explorador de Windows.
#            3. Exportar la Sábana Académica Consolidada eligiendo ruta y nombre.
# ==============================================================================

from pathlib import Path
from datetime import date
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
import config
import data.db_excel as db
from core.validador_horarios import validar_horario_institucional


def generar_plantilla_importacion(tipo: str, ruta_destino: str | Path | None = None) -> Path:
    """
    Crea un archivo Excel de plantilla (`Estudiantes` o `Materias`) con
    encabezados oficiales y filas de muestra en la ruta elegida por el usuario.
    """
    libro = Workbook()
    hoja = libro.active

    if tipo.lower() == "estudiantes":
        hoja.title = "Estudiantes"
        columnas = ["ID_Estudiante", "Nombre", "Apellidos", "Correo", "Telefono", "Semestre", "ID_Programa"]
        ejemplos = [
            ["1001", "Alejandro", "Campo Solarte", "alejandro.campo@campusucc.edu.co", "3158901234", 6, "P01"],
            ["1002", "Juan Esteban", "Cardona Calambas", "juan.cardona@campusucc.edu.co", "3176543210", 6, "P01"],
            ["1003", "Diego Fernando", "Gómez Rivera", "diego.gomez@campusucc.edu.co", "3201122334", 6, "P01"],
        ]
        ruta_salida = Path(ruta_destino) if ruta_destino else (config.CARPETA_PLANTILLAS_EXCEL / "Plantilla_Importar_Estudiantes.xlsx")
    else:
        hoja.title = "Materias"
        columnas = ["ID_Materia", "Nombre_Curso", "Creditos", "Cupos", "Docente", "ID_Programa", "Horario"]
        ejemplos = [
            ["SIS201-G1", "Arquitectura de Software", 3, 25, "Ing. Mauricio Pineda", "P01", "Miércoles 08:00 - 11:00"],
            ["SIS201-G2", "Arquitectura de Software", 3, 25, "Ing. Mauricio Pineda", "P01", "Jueves 14:00 - 17:00"],
            ["SIS202-G1", "Gerencia de Proyectos TI", 2, 30, "Esp. Ricardo Lozano", "P01", "Viernes 10:00 - 12:00"],
        ]
        ruta_salida = Path(ruta_destino) if ruta_destino else (config.CARPETA_PLANTILLAS_EXCEL / "Plantilla_Importar_Materias.xlsx")

    hoja.append(columnas)
    for fila_ej in ejemplos:
        hoja.append(fila_ej)

    for col_idx, titulo in enumerate(columnas, start=1):
        celda = hoja.cell(row=1, column=col_idx)
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill(start_color="1F6AA5", end_color="1F6AA5", fill_type="solid")
        celda.alignment = Alignment(horizontal="center", vertical="center")
        hoja.column_dimensions[get_column_letter(col_idx)].width = max(len(titulo) + 8, 18)

    libro.save(ruta_salida)
    libro.close()
    return ruta_salida


def importar_estudiantes_desde_excel(ruta_origen: str | Path) -> dict:
    """
    Lee un archivo Excel externo e importa en lote los estudiantes hacia la
    base de datos principal, validando duplicados y campos obligatorios.
    """
    libro_origen = load_workbook(ruta_origen, read_only=True, data_only=True)
    hoja_origen = libro_origen["Estudiantes"] if "Estudiantes" in libro_origen.sheetnames else libro_origen.active

    libro_destino = db.cargar_libro()
    hoja_est = libro_destino["Estudiantes"]
    hoja_prog = libro_destino["Programas"]

    insertados = 0
    duplicados = 0
    errores = []

    for idx_fila, fila in enumerate(hoja_origen.iter_rows(min_row=2, values_only=True), start=2):
        if not fila or fila[0] is None or str(fila[0]).strip() == "":
            continue
        try:
            cedula = str(fila[0]).strip()
            nombre = str(fila[1]).strip() if len(fila) > 1 and fila[1] else ""
            apellidos = str(fila[2]).strip() if len(fila) > 2 and fila[2] else ""
            correo = str(fila[3]).strip() if len(fila) > 3 and fila[3] else ""
            telefono = str(fila[4]).strip() if len(fila) > 4 and fila[4] else "Sin teléfono"
            semestre = int(fila[5]) if len(fila) > 5 and fila[5] is not None else 1
            id_programa = str(fila[6]).strip() if len(fila) > 6 and fila[6] else "P01"

            if not cedula or not nombre or not apellidos:
                errores.append(f"Fila {idx_fila}: Cédula, nombre o apellidos vacíos.")
                continue

            if db.buscar_fila(hoja_est, 0, cedula):
                duplicados += 1
                continue

            # Si aún no existe ningún programa en la base de datos, creamos P01 y F01 automáticamente
            if not db.buscar_fila(hoja_prog, 0, id_programa):
                if not db.buscar_fila(libro_destino["Facultades"], 0, "F01"):
                    libro_destino["Facultades"].append(["F01", "Facultad de Ingeniería", "Dr. Hernán Darío Gómez"])
                hoja_prog.append([id_programa, "Ingeniería de Software y Sistemas", "F01", 10])

            hoja_est.append([cedula, nombre, apellidos, correo, telefono, semestre, id_programa])
            insertados += 1
        except Exception as exc:
            errores.append(f"Fila {idx_fila}: {exc}")

    libro_origen.close()
    if insertados > 0:
        libro_destino.save(db.ruta_archivo)
    libro_destino.close()

    return {
        "insertados": insertados,
        "duplicados": duplicados,
        "errores": errores
    }


def importar_materias_desde_excel(ruta_origen: str | Path) -> dict:
    """
    Lee un archivo Excel externo e importa en lote nuevas asignaturas hacia la
    base de datos principal. Cada asignatura debe pertenecer a un Programa
    existente y su horario debe cumplir las reglas institucionales
    (jornada 06:00-22:00 y sin clases entre 13:00 y 14:00).
    """
    libro_origen = load_workbook(ruta_origen, read_only=True, data_only=True)
    hoja_origen = libro_origen["Materias"] if "Materias" in libro_origen.sheetnames else libro_origen.active

    libro_destino = db.cargar_libro()
    hoja_mat = libro_destino["Materias"]
    hoja_prog = libro_destino["Programas"]

    insertados = 0
    duplicados = 0
    errores = []

    for idx_fila, fila in enumerate(hoja_origen.iter_rows(min_row=2, values_only=True), start=2):
        if not fila or fila[0] is None or str(fila[0]).strip() == "":
            continue
        try:
            id_materia = str(fila[0]).strip().upper()
            nombre_curso = str(fila[1]).strip() if len(fila) > 1 and fila[1] else ""
            creditos = int(fila[2]) if len(fila) > 2 and fila[2] is not None else 3
            cupos = int(fila[3]) if len(fila) > 3 and fila[3] is not None else config.CUPOS_POR_DEFECTO
            docente = str(fila[4]).strip() if len(fila) > 4 and fila[4] else "Docente por asignar"
            id_programa = str(fila[5]).strip().upper() if len(fila) > 5 and fila[5] else ""
            horario = str(fila[6]).strip() if len(fila) > 6 and fila[6] else ""

            if not id_materia or not nombre_curso:
                errores.append(f"Fila {idx_fila}: Código o nombre de materia vacío.")
                continue

            if not id_programa or not db.buscar_fila(hoja_prog, 0, id_programa):
                errores.append(f"Fila {idx_fila}: El programa '{id_programa}' no existe. Regístrelo o impórtelo primero.")
                continue

            valido, motivo = validar_horario_institucional(horario)
            if not valido:
                errores.append(f"Fila {idx_fila} ({id_materia}): {motivo}")
                continue

            if db.buscar_fila(hoja_mat, 0, id_materia):
                duplicados += 1
                continue

            hoja_mat.append([id_materia, nombre_curso, creditos, cupos, docente, id_programa, horario])
            insertados += 1
        except Exception as exc:
            errores.append(f"Fila {idx_fila}: {exc}")

    libro_origen.close()
    if insertados > 0:
        libro_destino.save(db.ruta_archivo)
    libro_destino.close()

    return {
        "insertados": insertados,
        "duplicados": duplicados,
        "errores": errores
    }


def importar_base_datos_completa_desde_excel(ruta_origen: str | Path) -> dict:
    """
    Importa un archivo Excel completo (con múltiples hojas: Facultades, Programas,
    Materias, Estudiantes, Matriculas, Notas, Usuarios) hacia la base de datos
    activa `Registro_Matricula_Pro.xlsx`, evitando duplicados por llave primaria.

    Retorna un diccionario con:
      - por_hoja: registros nuevos insertados por cada hoja.
      - total_insertados / duplicados: totales generales.
      - errores: filas omitidas por incumplir reglas (programa inexistente u horario inválido).
    """
    libro_origen = load_workbook(ruta_origen, read_only=True, data_only=True)
    libro_destino = db.cargar_libro()

    conteo_por_hoja = {}
    duplicados_totales = 0
    errores = []

    orden_hojas = ["Facultades", "Programas", "Materias", "Estudiantes", "Matriculas", "Notas", "Usuarios"]

    for nombre_hoja in orden_hojas:
        conteo_por_hoja[nombre_hoja] = 0
        if nombre_hoja not in libro_origen.sheetnames:
            continue

        hoja_orig = libro_origen[nombre_hoja]
        hoja_dest = libro_destino[nombre_hoja]

        for fila in hoja_orig.iter_rows(min_row=2, values_only=True):
            if not fila or fila[0] is None or str(fila[0]).strip() == "":
                continue
            llave_primaria = str(fila[0]).strip()
            if db.buscar_fila(hoja_dest, 0, llave_primaria):
                duplicados_totales += 1
                continue

            if nombre_hoja == "Materias":
                id_programa = str(fila[5]).strip() if len(fila) > 5 and fila[5] else ""
                if not db.buscar_fila(libro_destino["Programas"], 0, id_programa):
                    errores.append(
                        f"Materia {llave_primaria}: el programa '{id_programa}' no existe "
                        f"(el archivo puede tener el formato anterior por facultad)."
                    )
                    continue
                valido, motivo = validar_horario_institucional(str(fila[6]) if len(fila) > 6 and fila[6] else "")
                if not valido:
                    errores.append(f"Materia {llave_primaria}: {motivo}")
                    continue

            hoja_dest.append(list(fila))
            conteo_por_hoja[nombre_hoja] += 1

    libro_origen.close()
    libro_destino.save(db.ruta_archivo)
    libro_destino.close()

    return {
        "por_hoja": conteo_por_hoja,
        "total_insertados": sum(conteo_por_hoja.values()),
        "duplicados": duplicados_totales,
        "errores": errores
    }


def exportar_sabana_consolidada(ruta_destino: str | Path | None = None) -> Path:
    """
    Genera un reporte ejecutivo en Excel (`Sabana_Consolidada_UCC_<fecha>.xlsx`)
    en la ubicación elegida por el usuario, cruzando Estudiantes, Programas,
    Matrículas y Notas en una sola vista analítica formateada.
    """
    estudiantes = {str(e[0]): e for e in db.obtener_datos("Estudiantes")}
    programas = {str(p[0]): p[1] for p in db.obtener_datos("Programas")}
    materias = {str(m[0]): m for m in db.obtener_datos("Materias")}
    matriculas = db.obtener_datos("Matriculas")
    notas_por_matricula = {str(n[1]): n for n in db.obtener_datos("Notas")}

    libro_rep = Workbook()
    hoja = libro_rep.active
    hoja.title = "Consolidado_Academico"

    columnas = [
        "ID Matrícula", "Periodo", "Estado Matrícula", "Cédula",
        "Estudiante", "Programa", "Código Materia", "Asignatura",
        "Créditos", "Docente", "Horario", "Nota 1", "Nota 2",
        "Nota 3", "Definitiva", "Estado Nota"
    ]
    hoja.append(columnas)

    for col_idx, titulo in enumerate(columnas, start=1):
        c = hoja.cell(row=1, column=col_idx)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color="2E8B57", end_color="2E8B57", fill_type="solid")
        c.alignment = Alignment(horizontal="center", vertical="center")
        hoja.column_dimensions[get_column_letter(col_idx)].width = max(len(titulo) + 5, 15)

    for mat in matriculas:
        id_mat = str(mat[0])
        cedula = str(mat[1])
        id_curso = str(mat[2])
        creditos = mat[3]
        periodo = mat[4]
        estado_mat = mat[6] if len(mat) > 6 else "Activa"

        est = estudiantes.get(cedula)
        nombre_est = f"{est[1]} {est[2]}" if est else "No encontrado"
        nom_prog = programas.get(str(est[6]), str(est[6])) if est and len(est) > 6 else "N/A"

        info_curso = materias.get(id_curso)
        nom_curso = info_curso[1] if info_curso else id_curso
        docente = info_curso[4] if info_curso and len(info_curso) > 4 else "N/A"
        horario = info_curso[6] if info_curso and len(info_curso) > 6 else "N/A"

        reg_nota = notas_por_matricula.get(id_mat)
        if reg_nota:
            n1, n2, n3, def_nota, est_nota = reg_nota[3], reg_nota[4], reg_nota[5], reg_nota[6], reg_nota[7]
        else:
            n1, n2, n3, def_nota, est_nota = "-", "-", "-", "-", "Sin calificar"

        hoja.append([
            id_mat, periodo, estado_mat, cedula, nombre_est, nom_prog,
            id_curso, nom_curso, creditos, docente, horario,
            n1, n2, n3, def_nota, est_nota
        ])

    hoja.freeze_panes = "A2"
    fecha_str = date.today().strftime("%Y%m%d")
    ruta_reporte = Path(ruta_destino) if ruta_destino else (config.CARPETA_REPORTES_PDF / f"Sabana_Consolidada_UCC_{fecha_str}.xlsx")
    libro_rep.save(ruta_reporte)
    libro_rep.close()
    return ruta_reporte
