from __future__ import annotations
# ==============================================================================
# ARCHIVO: main.py
# PROPÓSITO: Punto de entrada principal de la Aplicación de Escritorio Avanzada
#            del Sistema Integral de Matrículas UCC.
#            Gestiona el ciclo de vida de la ventana, las transiciones entre
#            Login y Panel de Control según el rol del usuario, incluye un
#            tablero de indicadores (KPIs) en tiempo real, explorador visual
#            de tablas, vaciado de base de datos y generación del archivo Excel
#            con más de 50 estudiantes para importación manual.
#
#            Reglas de sesión del rol Estudiante:
#            • Ingreso con cédula y contraseña: todas las operaciones se aplican
#              únicamente a ese estudiante (no hay selector de estudiantes).
#            • Acceso de demostración ("estudiante"): muestra un selector para
#              elegir con cuál estudiante registrado se desea actuar.
# ==============================================================================

from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import config
import data.db_excel as db
from poblar_datos import poblar_base_de_datos, generar_simulacion_masiva_universidad
from ui.login_view import dibujar_login
from ui.admin_views import (
    abrir_ventana_facultad,
    abrir_ventana_programa,
    abrir_ventana_materia,
    abrir_ventana_estudiante,
    abrir_ventana_explorador_bd,
    abrir_ventana_postgres,
)
from ui.matricula_views import abrir_ventana_matricula, abrir_ventana_cancelar_materia
from ui.notas_views import abrir_ventana_notas
from ui.carga_masiva_views import abrir_ventana_etl_excel
from ui.componentes import TextoDeslizable
from ui import abrir_ventana_generar_pdf

# Configuración global de apariencia de CustomTkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class SistemaUniversitarioApp(ctk.CTk):
    """Clase principal de la ventana de escritorio (hereda de ctk.CTk)."""

    def __init__(self):
        super().__init__()
        self.title("Sistema Integral de Gestión Académica y Matrículas — UCC")
        self.update_idletasks()

        ancho, alto = 920, 700
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = max(0, (self.winfo_screenheight() // 2) - (alto // 2) - 20)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.resizable(False, False)

        self.frame_actual = None
        self.sesion_actual = None
        self.mostrar_login()

    def limpiar_pantalla(self):
        """Destruye el contenedor activo antes de renderizar una nueva vista."""
        if self.frame_actual is not None:
            self.frame_actual.destroy()
            self.frame_actual = None

    def mostrar_login(self):
        """Muestra la pantalla dividida de autenticación."""
        self.limpiar_pantalla()
        self.sesion_actual = None
        self.frame_actual = dibujar_login(self, self.mostrar_menu)

    # --------------------------------------------------------------------------
    # BLOQUE DE SESIÓN DEL ESTUDIANTE (selector solo en modo demostración)
    # --------------------------------------------------------------------------
    def _dibujar_bloque_estudiante(self, tarjeta, info_sesion: dict):
        """
        Muestra los datos del estudiante activo. En el acceso de demostración
        agrega un selector para elegir el estudiante; con un ingreso real (cédula
        y contraseña) NO existe selector y la sesión queda fija a esa persona.
        """
        modo_demo = bool(info_sesion.get("modo_demo"))
        frame = ctk.CTkFrame(tarjeta, fg_color="#EFF6FF", corner_radius=12)
        frame.pack(padx=28, pady=(0, 10), fill="x")

        lbl_info = TextoDeslizable(
            frame, texto="", fuente=(config.FUENTE_FORMULARIOS, 11, "bold"),
            color_texto="#1E3A8A", fondo="#EFF6FF"
        )

        def describir(cedula: str) -> str:
            fila = db.obtener_estudiante(cedula) if cedula else None
            if not fila:
                return "⚠ No hay un estudiante activo. Su documento no figura en la base de datos."
            programa = db.obtener_nombre_programa(fila[6])
            return (
                f"👤 {fila[0]} - {fila[1]} {fila[2]}   |   🎓 {fila[6]} - {programa}   |   Semestre {fila[5]}"
            )

        if modo_demo:
            ctk.CTkLabel(
                frame,
                text="Modo demostración: elija el estudiante con el que desea actuar. "
                     "Todo lo que haga se aplicará únicamente a ese estudiante.",
                font=(config.FUENTE_FORMULARIOS, 11),
                text_color="#475569",
                wraplength=780,
                justify="left"
            ).pack(anchor="w", padx=14, pady=(8, 2))

            opciones = db.obtener_opciones("Estudiantes", 0, 1)
            if not opciones:
                info_sesion["documento"] = ""
            else:
                actual = next(
                    (o for o in opciones if db.extraer_id(o) == str(info_sesion.get("documento", ""))),
                    opciones[0]
                )
                info_sesion["documento"] = db.extraer_id(actual)

                def al_cambiar(seleccion: str):
                    info_sesion["documento"] = db.extraer_id(seleccion)
                    lbl_info.configurar(describir(info_sesion["documento"]))

                combo = ctk.CTkComboBox(
                    frame, values=opciones, width=560, height=34, state="readonly",
                    command=al_cambiar, font=(config.FUENTE_FORMULARIOS, 12),
                    button_color=config.COLOR_CELESTE_UCC, button_hover_color=config.COLOR_CELESTE_HOVER
                )
                combo.set(actual)
                combo.pack(padx=14, pady=4, anchor="w")

        lbl_info.configurar(describir(str(info_sesion.get("documento", ""))))
        lbl_info.pack(fill="x", padx=14, pady=(2, 8))

    def mostrar_menu(self, info_sesion: dict):
        """
        Renderiza el Panel de Control principal adaptado al rol autenticado
        ('Administrador', 'Estudiante' o 'Profesor') junto con indicadores KPI.
        """
        self.sesion_actual = info_sesion
        rol = info_sesion.get("rol", "Estudiante")
        nombre_usr = info_sesion.get("nombre", info_sesion.get("usuario", "Usuario"))

        self.limpiar_pantalla()

        self.frame_actual = ctk.CTkScrollableFrame(self, fg_color=config.COLOR_MORADO_UCC, corner_radius=0)
        self.frame_actual.pack(expand=True, fill="both")

        # Tarjeta central blanca
        tarjeta = ctk.CTkFrame(self.frame_actual, fg_color="white", corner_radius=24)
        tarjeta.pack(pady=18, padx=32, fill="x", expand=True)

        # Cabecera con logo y datos de sesión
        if config.RUTA_LOGO_UCC.exists():
            img_ucc = ctk.CTkImage(light_image=Image.open(config.RUTA_LOGO_UCC), size=(76, 76))
            ctk.CTkLabel(tarjeta, image=img_ucc, text="").pack(pady=(12, 2))

        ctk.CTkLabel(
            tarjeta,
            text="UNIVERSIDAD COOPERATIVA DE COLOMBIA",
            font=(config.FUENTE_PRINCIPAL, 19, "bold"),
            text_color=config.COLOR_AZUL_UCC
        ).pack(pady=(2, 2))

        ctk.CTkLabel(
            tarjeta,
            text=f"Panel de Control: {rol}  |  Bienvenido(a): {nombre_usr}",
            font=(config.FUENTE_PRINCIPAL, 13, "bold"),
            text_color="#475569"
        ).pack(pady=(0, 8))

        # Bloque del estudiante activo (con selector únicamente en modo demostración)
        if rol == "Estudiante":
            self._dibujar_bloque_estudiante(tarjeta, info_sesion)

        # Barra de indicadores KPI en vivo
        kpis = db.obtener_estadisticas_sistema()
        frame_kpi = ctk.CTkFrame(tarjeta, fg_color="#F1F5F9", corner_radius=14)
        frame_kpi.pack(padx=28, pady=(0, 10), fill="x")

        texto_kpi = (
            f"📊 Facultades: {kpis['total_facultades']}   |   "
            f"🎓 Programas: {kpis['total_programas']}   |   "
            f"📚 Materias: {kpis['total_materias']}   |   "
            f"👨‍🎓 Estudiantes: {kpis['total_estudiantes']}   |   "
            f"✅ Matrículas Activas: {kpis['matriculas_activas']}   |   "
            f"⭐ Promedio Global: {kpis['promedio_global']}"
        )
        TextoDeslizable(
            frame_kpi,
            texto=texto_kpi,
            fuente=(config.FUENTE_FORMULARIOS, 11, "bold"),
            color_texto="#1E3A8A",
            fondo="#F1F5F9"
        ).pack(fill="x", padx=12, pady=6)

        # Aviso guía si la base de datos está en blanco (primera visita)
        if kpis["total_facultades"] == 0 and kpis["total_estudiantes"] == 0:
            frame_aviso = ctk.CTkFrame(tarjeta, fg_color="#FEF9C3", corner_radius=12)
            frame_aviso.pack(padx=28, pady=(0, 10), fill="x")
            ctk.CTkLabel(
                frame_aviso,
                text=(
                    "💡 Estado del Sistema: La base de datos no contiene registros activos. "
                    "Puede ingresar información mediante los módulos de registro o importar datos a través del 'Centro ETL Excel'."
                ),
                font=(config.FUENTE_FORMULARIOS, 11, "bold"),
                text_color="#854D0E",
                wraplength=760
            ).pack(padx=12, pady=8)

        # Cuadrícula de botones de acción según el rol
        frame_grid = ctk.CTkFrame(tarjeta, fg_color="transparent")
        frame_grid.pack(pady=4, padx=20)

        refrescar = lambda: self.mostrar_menu(self.sesion_actual)

        estilo_btn = {
            "width": 245,
            "height": 42,
            "corner_radius": 14,
            "font": (config.FUENTE_PRINCIPAL, 13, "bold"),
            "fg_color": config.COLOR_CELESTE_UCC,
            "hover_color": config.COLOR_CELESTE_HOVER,
            "text_color": "white"
        }

        estilo_btn_destacado = {
            **estilo_btn,
            "fg_color": config.COLOR_AZUL_UCC,
            "hover_color": config.COLOR_AZUL_OSCURO
        }

        def accion_generar_excel_50():
            ruta_guardar = filedialog.asksaveasfilename(
                parent=self,
                title="Guardar archivo Excel con 50+ Estudiantes (Para Importación Manual)",
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
                "Archivo Excel de 50+ Estudiantes Generado",
                f"Se generó el archivo Excel de simulación en:\n\n"
                f"📁 {res['ruta']}\n\n"
                f"Contenido registrado:\n"
                f"• {res['facultades']} Facultades y {res['programas']} Programas\n"
                f"• {res['asignaturas_unicas']} Asignaturas ({res['materias']} grupos con horario, 15 por programa)\n"
                f"• {res['estudiantes']} Estudiantes (incluye a Alejandro Campo Solarte, Juan Esteban Cardona Calambas y Diego Fernando Gómez Rivera)\n"
                f"• {res['matriculas']} Matrículas y {res['notas']} Calificaciones\n\n"
                f"Para incorporar estos registros a la base de datos activa, utilice la opción '📥 Centro ETL / Importar Excel'.",
                parent=self
            )

        def accion_vaciar_bd():
            confirmar = messagebox.askyesno(
                "Vaciar Base de Datos y Dejar en Blanco",
                "¿Desea borrar todos los datos cargados (Facultades, Programas, Materias, Estudiantes, Matrículas y Notas) y dejar la base de datos completamente en blanco?\n\n"
                "Podrá volver a crear registros desde cero o importar cualquier archivo Excel.",
                parent=self
            )
            if confirmar:
                db.reiniciar_base_de_datos_vacia()
                refrescar()
                messagebox.showinfo(
                    "Base de Datos en Blanco",
                    "Se han eliminado todos los registros. El sistema está completamente limpio y listo para registrar desde cero.",
                    parent=self
                )

        # ---------------- Acciones del Estudiante (siempre sobre el estudiante activo) ----------------
        def cedula_estudiante_activo() -> str:
            cedula = str(self.sesion_actual.get("documento", "")).strip()
            if not cedula or not db.obtener_estudiante(cedula):
                messagebox.showwarning(
                    "Sin estudiante activo",
                    "No hay un estudiante registrado asociado a esta sesión.\n"
                    "Registre o importe estudiantes desde el panel de Administrador.",
                    parent=self
                )
                return ""
            return cedula

        def accion_matricular():
            cedula = cedula_estudiante_activo()
            if cedula:
                abrir_ventana_matricula(refrescar, cedula)

        def accion_cancelar():
            cedula = cedula_estudiante_activo()
            if cedula:
                abrir_ventana_cancelar_materia(refrescar, cedula)

        def accion_pdf_estudiante():
            cedula = cedula_estudiante_activo()
            if cedula:
                abrir_ventana_generar_pdf(cedula)

        def accion_ver_oferta():
            cedula = cedula_estudiante_activo()
            if cedula:
                fila = db.obtener_estudiante(cedula)
                abrir_ventana_explorador_bd(
                    tablas=["Materias"],
                    permitir_eliminar=False,
                    id_programa_filtro=str(fila[6]).strip()
                )

        if rol == "Administrador":
            ctk.CTkButton(frame_grid, text="🏛️ Registrar Facultad", command=lambda: abrir_ventana_facultad(refrescar), **estilo_btn).grid(row=0, column=0, padx=10, pady=5)
            ctk.CTkButton(frame_grid, text="🎓 Registrar Programa", command=lambda: abrir_ventana_programa(refrescar), **estilo_btn).grid(row=0, column=1, padx=10, pady=5)
            ctk.CTkButton(frame_grid, text="📘 Registrar Asignatura", command=lambda: abrir_ventana_materia(refrescar), **estilo_btn).grid(row=1, column=0, padx=10, pady=5)
            ctk.CTkButton(frame_grid, text="👨‍🎓 Registrar Estudiante", command=lambda: abrir_ventana_estudiante(refrescar), **estilo_btn).grid(row=1, column=1, padx=10, pady=5)
            ctk.CTkButton(frame_grid, text="📥 Centro ETL / Importar Excel", command=lambda: abrir_ventana_etl_excel(refrescar), **estilo_btn_destacado).grid(row=2, column=0, padx=10, pady=5)
            ctk.CTkButton(frame_grid, text="🔍 Explorar / Editar Tablas BD", command=lambda: abrir_ventana_explorador_bd(refrescar), **estilo_btn_destacado).grid(row=2, column=1, padx=10, pady=5)
            ctk.CTkButton(frame_grid, text="📄 Exportar Reportes PDF", command=abrir_ventana_generar_pdf, **estilo_btn).grid(row=3, column=0, padx=10, pady=5)
            ctk.CTkButton(frame_grid, text="🐘 Sincronizar PostgreSQL", command=abrir_ventana_postgres, **estilo_btn).grid(row=3, column=1, padx=10, pady=5)

            # Botones inferiores de Simulación en Excel (Guardar como...) y Vaciado de Base de Datos
            ctk.CTkButton(
                frame_grid,
                text="📦 Generar Excel de 50+ Estudiantes",
                command=accion_generar_excel_50,
                width=245,
                height=42,
                corner_radius=14,
                font=(config.FUENTE_PRINCIPAL, 12, "bold"),
                fg_color=config.COLOR_VERDE_EXITO,
                hover_color=config.COLOR_VERDE_HOVER,
                text_color="white"
            ).grid(row=4, column=0, padx=10, pady=8)

            ctk.CTkButton(
                frame_grid,
                text="🗑️ Vaciar Base de Datos (En Blanco)",
                command=accion_vaciar_bd,
                width=245,
                height=42,
                corner_radius=14,
                font=(config.FUENTE_PRINCIPAL, 12, "bold"),
                fg_color="#64748B",
                hover_color="#475569",
                text_color="white"
            ).grid(row=4, column=1, padx=10, pady=8)

        elif rol == "Estudiante":
            ctk.CTkButton(frame_grid, text="🛒 Matricular Asignaturas", command=accion_matricular, **estilo_btn_destacado).grid(row=0, column=0, padx=10, pady=8)
            ctk.CTkButton(frame_grid, text="❌ Cancelar / Retirar Materia", command=accion_cancelar, **estilo_btn).grid(row=0, column=1, padx=10, pady=8)
            ctk.CTkButton(frame_grid, text="📄 Exportar Certificados PDF", command=accion_pdf_estudiante, **estilo_btn).grid(row=1, column=0, padx=10, pady=8)
            ctk.CTkButton(frame_grid, text="📚 Ver Oferta de mi Programa", command=accion_ver_oferta, **estilo_btn).grid(row=1, column=1, padx=10, pady=8)

        elif rol == "Profesor":
            ctk.CTkButton(frame_grid, text="📝 Registrar / Editar Notas", command=lambda: abrir_ventana_notas(refrescar), **estilo_btn_destacado).grid(row=0, column=0, padx=10, pady=8)
            ctk.CTkButton(frame_grid, text="📄 Exportar Boletines PDF", command=abrir_ventana_generar_pdf, **estilo_btn).grid(row=0, column=1, padx=10, pady=8)
            ctk.CTkButton(frame_grid, text="📊 Centro ETL / Sábana Excel", command=lambda: abrir_ventana_etl_excel(refrescar), **estilo_btn).grid(row=1, column=0, padx=10, pady=8)
            ctk.CTkButton(frame_grid, text="🔍 Consultar Tablas BD", command=lambda: abrir_ventana_explorador_bd(permitir_eliminar=False), **estilo_btn).grid(row=1, column=1, padx=10, pady=8)

        # Botón para cerrar sesión
        ctk.CTkButton(
            tarjeta,
            text="Cerrar Sesión",
            command=self.mostrar_login,
            width=210,
            height=36,
            fg_color=config.COLOR_ROJO_ERROR,
            hover_color=config.COLOR_ROJO_HOVER,
            corner_radius=14,
            font=(config.FUENTE_PRINCIPAL, 13, "bold")
        ).pack(pady=(8, 16))


if __name__ == "__main__":
    # Inicializa el archivo Excel en blanco si es la primera visita
    poblar_base_de_datos(silencioso=True)
    app = SistemaUniversitarioApp()
    app.mainloop()
