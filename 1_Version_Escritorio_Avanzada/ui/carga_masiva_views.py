from __future__ import annotations
# ==============================================================================
# ARCHIVO: ui/carga_masiva_views.py
# PROPÓSITO: Interfaz gráfica para el Centro de Importación, Exportación y
#            Gestión Masiva con Excel (ETL):
#            1. Generación del archivo Excel con 50+ estudiantes (sin cargarlo
#               automáticamente, permitiendo elegir dónde guardarlo con el
#               explorador de archivos de Windows).
#            2. Generación de plantillas individuales eligiendo ruta y nombre.
#            3. Importación manual desde el explorador de archivos (tanto de la
#               base de datos completa de 50+ estudiantes como de lotes de
#               estudiantes o materias).
#            4. Exportación de Sábana Consolidada eligiendo carpeta y nombre.
#            5. Botón para vaciar/reiniciar la base de datos en blanco.
# ==============================================================================

from datetime import date
from tkinter import filedialog, messagebox
import customtkinter as ctk
import config
import data.db_excel as db
from data.etl_excel import (
    generar_plantilla_importacion,
    importar_estudiantes_desde_excel,
    importar_materias_desde_excel,
    importar_base_datos_completa_desde_excel,
    exportar_sabana_consolidada
)
from poblar_datos import generar_simulacion_masiva_universidad
from ui import crear_ventana_modal


def abrir_ventana_etl_excel(callback_refrescar=None):
    """Ventana modal para gestionar procesos de importación, exportación y vaciado Excel."""
    vent = crear_ventana_modal("Centro ETL: Importación, Exportación y Mantenimiento Excel", 600, 620)

    ctk.CTkLabel(
        vent,
        text="Centro de Datos Excel y Simulación (OpenPyXL ETL)",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(14, 2))

    ctk.CTkLabel(
        vent,
        text="Elija dónde guardar sus archivos Excel o cuál archivo importar desde su computador:",
        font=(config.FUENTE_FORMULARIOS, 12),
        text_color="gray"
    ).pack(pady=(0, 8))

    # ==========================================================================
    # SECCIÓN 1: GENERAR ARCHIVOS EXCEL (GUARDAR COMO...)
    # ==========================================================================
    frame_sec1 = ctk.CTkFrame(vent, fg_color="#F8FAFC", corner_radius=12)
    frame_sec1.pack(padx=24, pady=5, fill="x")

    ctk.CTkLabel(
        frame_sec1,
        text="1. Generar Archivos Excel y Plantillas (Guardar como...)",
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        text_color="#1E293B"
    ).pack(anchor="w", padx=14, pady=(8, 4))

    ctk.CTkLabel(
        frame_sec1,
        text="Genera un archivo independiente de simulación con 50 estudiantes para pruebas de importación por lotes:",
        font=(config.FUENTE_FORMULARIOS, 11),
        text_color="#475569"
    ).pack(anchor="w", padx=14, pady=(0, 6))

    def guardar_excel_50_estudiantes():
        ruta_guardar = filedialog.asksaveasfilename(
            parent=vent,
            title="Guardar archivo Excel de Simulación (50+ Estudiantes UCC)",
            initialdir=str(config.CARPETA_PLANTILLAS_EXCEL),
            initialfile="Universidad_50_Estudiantes_UCC.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Archivo de Excel", "*.xlsx")]
        )
        if not ruta_guardar:
            return
        res = generar_simulacion_masiva_universidad(
            total_estudiantes=50,
            silencioso=True,
            ruta_destino=ruta_guardar
        )
        messagebox.showinfo(
            "Archivo Excel de 50+ Estudiantes Creado",
            f"Se generó el archivo Excel correctamente:\n\n"
            f"📁 Ruta: {res['ruta']}\n\n"
            f"Contenido del archivo generado:\n"
            f"• {res['facultades']} Facultades y {res['programas']} Programas\n"
            f"• {res['asignaturas_unicas']} Asignaturas ({res['materias']} grupos con horario, 15 por programa)\n"
            f"• {res['estudiantes']} Estudiantes (incluyendo a Alejandro Campo, Juan Esteban Cardona y Diego Fernando Gómez)\n"
            f"• {res['matriculas']} Matrículas y {res['notas']} Notas\n\n"
            f"Para incorporar estos registros a la base de datos activa, utilice la opción 'Importar Base de Datos Completa (.xlsx)'.",
            parent=vent
        )

    ctk.CTkButton(
        frame_sec1,
        text="📦 Generar Archivo Excel con 50+ Estudiantes (Guardar como...)",
        command=guardar_excel_50_estudiantes,
        width=510,
        height=36,
        fg_color=config.COLOR_VERDE_EXITO,
        hover_color=config.COLOR_VERDE_HOVER,
        font=(config.FUENTE_FORMULARIOS, 12, "bold")
    ).pack(pady=(2, 6))

    frame_btn_plant = ctk.CTkFrame(frame_sec1, fg_color="transparent")
    frame_btn_plant.pack(pady=(0, 10))

    def crear_plantilla(tipo: str):
        nombre_sugerido = f"Plantilla_Importar_{tipo.capitalize()}.xlsx"
        ruta_sel = filedialog.asksaveasfilename(
            parent=vent,
            title=f"Guardar plantilla Excel de {tipo}",
            initialdir=str(config.CARPETA_PLANTILLAS_EXCEL),
            initialfile=nombre_sugerido,
            defaultextension=".xlsx",
            filetypes=[("Archivo de Excel", "*.xlsx")]
        )
        if not ruta_sel:
            return
        ruta = generar_plantilla_importacion(tipo, ruta_destino=ruta_sel)
        messagebox.showinfo(
            "Plantilla Guardada",
            f"Se creó la plantilla de {tipo} en:\n\n{ruta}",
            parent=vent
        )

    ctk.CTkButton(
        frame_btn_plant,
        text="📄 Guardar Plantilla Estudiantes",
        command=lambda: crear_plantilla("estudiantes"),
        width=245,
        height=34,
        fg_color=config.COLOR_CELESTE_UCC,
        hover_color=config.COLOR_CELESTE_HOVER
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        frame_btn_plant,
        text="📄 Guardar Plantilla Materias",
        command=lambda: crear_plantilla("materias"),
        width=245,
        height=34,
        fg_color=config.COLOR_CELESTE_UCC,
        hover_color=config.COLOR_CELESTE_HOVER
    ).pack(side="left", padx=8)

    # ==========================================================================
    # SECCIÓN 2: IMPORTAR ARCHIVOS EXCEL DESDE EL BUSCADOR DE ARCHIVOS
    # ==========================================================================
    frame_sec2 = ctk.CTkFrame(vent, fg_color="#EFF6FF", corner_radius=12)
    frame_sec2.pack(padx=24, pady=5, fill="x")

    ctk.CTkLabel(
        frame_sec2,
        text="2. Importar Archivos Excel al Sistema (Abrir desde su PC...)",
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        text_color="#1E3A8A"
    ).pack(anchor="w", padx=14, pady=(8, 4))

    def importar_bd_completa():
        ruta_sel = filedialog.askopenfilename(
            parent=vent,
            title="Seleccionar archivo Excel de Base de Datos Completa (Ej: Universidad_50_Estudiantes_UCC.xlsx)",
            initialdir=str(config.CARPETA_PLANTILLAS_EXCEL),
            filetypes=[("Archivos de Excel", "*.xlsx")]
        )
        if not ruta_sel:
            return

        res = importar_base_datos_completa_desde_excel(ruta_sel)
        if callback_refrescar:
            callback_refrescar()

        ins = res["por_hoja"]
        errores = res.get("errores", [])
        detalle_err = ""
        if errores:
            detalle_err = f"\n\nFilas omitidas ({len(errores)}):\n" + "\n".join(errores[:4])
            if len(errores) > 4:
                detalle_err += f"\n... y {len(errores) - 4} más."

        messagebox.showinfo(
            "Resultado de la Importación",
            f"Resumen de registros incorporados al sistema:\n\n"
            f"• Facultades nuevas: {ins.get('Facultades', 0)}\n"
            f"• Programas nuevos: {ins.get('Programas', 0)}\n"
            f"• Asignaturas (grupos) nuevas: {ins.get('Materias', 0)}\n"
            f"• Estudiantes nuevos: {ins.get('Estudiantes', 0)}\n"
            f"• Matrículas cargadas: {ins.get('Matriculas', 0)}\n"
            f"• Notas cargadas: {ins.get('Notas', 0)}\n"
            f"• Duplicados omitidos: {res['duplicados']}"
            f"{detalle_err}",
            parent=vent
        )

    ctk.CTkButton(
        frame_sec2,
        text="📥 Importar Base de Datos Completa / 50+ Estudiantes (.xlsx)",
        command=importar_bd_completa,
        width=510,
        height=38,
        fg_color=config.COLOR_AZUL_UCC,
        hover_color=config.COLOR_AZUL_OSCURO,
        font=(config.FUENTE_FORMULARIOS, 12, "bold")
    ).pack(pady=(2, 6))

    frame_btn_imp = ctk.CTkFrame(frame_sec2, fg_color="transparent")
    frame_btn_imp.pack(pady=(0, 10))

    def ejecutar_importacion(tipo: str):
        ruta_sel = filedialog.askopenfilename(
            parent=vent,
            title=f"Seleccionar archivo Excel de {tipo}",
            initialdir=str(config.CARPETA_PLANTILLAS_EXCEL),
            filetypes=[("Archivos de Excel", "*.xlsx")]
        )
        if not ruta_sel:
            return

        if tipo == "Estudiantes":
            res = importar_estudiantes_desde_excel(ruta_sel)
        else:
            res = importar_materias_desde_excel(ruta_sel)

        if callback_refrescar:
            callback_refrescar()

        detalle_err = f"\nErrores ({len(res['errores'])}): " + "; ".join(res["errores"][:3]) if res["errores"] else ""
        messagebox.showinfo(
            f"Resultado de Importación ({tipo})",
            f"Proceso finalizado exitosamente:\n\n"
            f"• Nuevos registros insertados: {res['insertados']}\n"
            f"• Duplicados omitidos: {res['duplicados']}"
            f"{detalle_err}",
            parent=vent
        )

    ctk.CTkButton(
        frame_btn_imp,
        text="📥 Importar Solo Estudiantes (.xlsx)",
        command=lambda: ejecutar_importacion("Estudiantes"),
        width=245,
        height=34,
        fg_color="#2563EB",
        hover_color=config.COLOR_AZUL_OSCURO
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        frame_btn_imp,
        text="📥 Importar Solo Materias (.xlsx)",
        command=lambda: ejecutar_importacion("Materias"),
        width=245,
        height=34,
        fg_color="#2563EB",
        hover_color=config.COLOR_AZUL_OSCURO
    ).pack(side="left", padx=8)

    # ==========================================================================
    # SECCIÓN 3: EXPORTAR SÁBANA CONSOLIDADA Y VACIAR BASE DE DATOS
    # ==========================================================================
    frame_sec3 = ctk.CTkFrame(vent, fg_color="#F1F5F9", corner_radius=12)
    frame_sec3.pack(padx=24, pady=5, fill="x")

    ctk.CTkLabel(
        frame_sec3,
        text="3. Exportar Reporte Consolidado o Vaciar Base de Datos",
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        text_color="#1E293B"
    ).pack(anchor="w", padx=14, pady=(8, 6))

    frame_btn_s3 = ctk.CTkFrame(frame_sec3, fg_color="transparent")
    frame_btn_s3.pack(pady=(0, 10))

    def exportar_consolidado():
        nombre_def = f"Sabana_Academica_UCC_{date.today().strftime('%Y%m%d')}.xlsx"
        ruta_sel = filedialog.asksaveasfilename(
            parent=vent,
            title="Guardar Sábana Académica Consolidada en Excel",
            initialdir=str(config.CARPETA_EXPORTACIONES_PDF),
            initialfile=nombre_def,
            defaultextension=".xlsx",
            filetypes=[("Archivo de Excel", "*.xlsx")]
        )
        if not ruta_sel:
            return
        ruta_rep = exportar_sabana_consolidada(ruta_destino=ruta_sel)
        messagebox.showinfo(
            "Sábana Consolidada Exportada",
            f"El reporte ejecutivo consolidado en Excel fue guardado en:\n\n{ruta_rep}",
            parent=vent
        )

    def vaciar_bd():
        confirmar = messagebox.askyesno(
            "Confirmar Vaciado de Base de Datos",
            "¿Está seguro de que desea borrar TODOS los registros cargados (Facultades, Programas, Materias, Estudiantes, Matrículas y Notas) y dejar el sistema completamente en blanco?\n\n"
            "• Las cuentas base de acceso (admin, estudiante, profesor) se conservarán.\n"
            "• Podrá volver a registrar desde cero o importar un archivo Excel cuando lo desee.",
            parent=vent
        )
        if confirmar:
            db.reiniciar_base_de_datos_vacia()
            if callback_refrescar:
                callback_refrescar()
            messagebox.showinfo(
                "Base de Datos Vaciada",
                "La base de datos ha quedado completamente limpia y en blanco (0 registros).",
                parent=vent
            )

    ctk.CTkButton(
        frame_btn_s3,
        text="📊 Exportar Sábana Consolidada (.xlsx)",
        command=exportar_consolidado,
        width=250,
        height=36,
        fg_color=config.COLOR_VERDE_EXITO,
        hover_color=config.COLOR_VERDE_HOVER,
        font=(config.FUENTE_FORMULARIOS, 12, "bold")
    ).pack(side="left", padx=6)

    ctk.CTkButton(
        frame_btn_s3,
        text="🗑️ Vaciar Base de Datos (Dejar en Blanco)",
        command=vaciar_bd,
        width=250,
        height=36,
        fg_color=config.COLOR_ROJO_ERROR,
        hover_color=config.COLOR_ROJO_HOVER,
        font=(config.FUENTE_FORMULARIOS, 12, "bold")
    ).pack(side="left", padx=6)

    ctk.CTkButton(
        vent,
        text="Cerrar ventana",
        command=vent.destroy,
        width=150,
        height=34,
        fg_color="#E2E8F0",
        text_color="#1E293B"
    ).pack(pady=8)
