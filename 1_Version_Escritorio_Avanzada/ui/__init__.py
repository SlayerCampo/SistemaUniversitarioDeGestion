from __future__ import annotations
# ==============================================================================
# ARCHIVO: ui/__init__.py
# PROPÓSITO: Utilidades compartidas de interfaz gráfica CustomTkinter para todas
#            las ventanas secundarias (modales centradas y protegidas contra
#            recolección de basura / minimización, campos estandarizados con
#            etiqueta superior y ejemplo interior, estilos y selector de PDF).
# ==============================================================================

from tkinter import filedialog, messagebox
import customtkinter as ctk
import config
import data.db_excel as db
from reports.pdf_matricula import generar_pdf_matricula
from reports.pdf_boletin import generar_pdf_notas
from ui.componentes import TextoDeslizable

# Registro global en memoria para evitar que el recolector de basura de Python
# destruya ventanas modales secundarias al salir de la función que las creó
_VENTANAS_ACTIVAS: list[ctk.CTkToplevel] = []


def crear_ventana_modal(
    titulo: str,
    ancho: int,
    alto: int,
    permitir_redimensionar: bool = True
) -> ctk.CTkToplevel:
    """
    Crea una ventana secundaria centrada en pantalla, visible al frente y
    protegida contra recolección de basura o pérdida de foco en Windows.
    """
    ventana = ctk.CTkToplevel()
    _VENTANAS_ACTIVAS.append(ventana)

    def al_destruir(_=None):
        if ventana in _VENTANAS_ACTIVAS:
            try:
                _VENTANAS_ACTIVAS.remove(ventana)
            except ValueError:
                pass

    ventana.bind("<Destroy>", al_destruir, add="+")

    # Ajusta ancho y alto respetando las dimensiones reales de la pantalla del usuario (768p / 1080p con escalado)
    ventana.update_idletasks()
    sw = ventana.winfo_screenwidth()
    sh = ventana.winfo_screenheight()
    ancho_final = min(ancho, max(360, sw - 40))
    alto_final = min(alto, max(340, sh - 80))
    x = max(15, (sw // 2) - (ancho_final // 2))
    y = max(15, (sh // 2) - (alto_final // 2) - 20)

    ventana.geometry(f"{ancho_final}x{alto_final}+{x}+{y}")
    ventana.title(titulo)
    ventana.configure(fg_color="white")
    ventana.resizable(permitir_redimensionar, permitir_redimensionar)

    # Forzar que aparezca al frente sin bloquear diálogos emergentes posteriores
    ventana.lift()
    ventana.attributes("-topmost", True)
    ventana.after(140, lambda: (
        ventana.attributes("-topmost", False) if ventana.winfo_exists() else None,
        ventana.lift() if ventana.winfo_exists() else None,
        ventana.focus_force() if ventana.winfo_exists() else None
    ))
    return ventana


def estilo_entrada(placeholder: str = "", ancho: int = 330) -> dict:
    """Devuelve el diccionario de propiedades visuales para un CTkEntry estándar."""
    return {
        "placeholder_text": placeholder,
        "width": ancho,
        "height": 38,
        "fg_color": config.COLOR_CAJA_TEXTO,
        "text_color": "black",
        "border_width": 1,
        "border_color": "#CBD5E1",
        "corner_radius": 10,
        "font": (config.FUENTE_FORMULARIOS, 12)
    }


def estilo_combobox(valores: list[str], ancho: int = 330) -> dict:
    """Devuelve el diccionario de propiedades visuales para un CTkComboBox estándar."""
    return {
        "values": valores,
        "width": ancho,
        "height": 38,
        "fg_color": config.COLOR_CAJA_TEXTO,
        "text_color": "black",
        "button_color": config.COLOR_CELESTE_UCC,
        "button_hover_color": config.COLOR_CELESTE_HOVER,
        "border_width": 1,
        "border_color": "#CBD5E1",
        "corner_radius": 10,
        "font": (config.FUENTE_FORMULARIOS, 12)
    }


def crear_campo_formulario(
    contenedor,
    etiqueta: str,
    placeholder: str = "",
    ancho: int = 340,
    padx: int = 40,
    valor_inicial: str = "",
    es_password: bool = False
) -> ctk.CTkEntry:
    """
    Crea un campo de formulario con la ETIQUETA descriptiva ARRIBA (en negrita)
    y el EJEMPLO / FORMATO DENTRO de la caja de texto como placeholder.
    """
    ctk.CTkLabel(
        contenedor,
        text=etiqueta,
        font=(config.FUENTE_FORMULARIOS, 11, "bold"),
        text_color="#334155"
    ).pack(anchor="w", padx=padx, pady=(8, 2))

    kwargs = estilo_entrada(placeholder=placeholder, ancho=ancho)
    if es_password:
        kwargs["show"] = "•"
    caja = ctk.CTkEntry(contenedor, **kwargs)
    if valor_inicial:
        caja.insert(0, valor_inicial)
    caja.pack(padx=padx, pady=(0, 2))
    return caja


def crear_combo_formulario(
    contenedor,
    etiqueta: str,
    valores: list[str],
    ancho: int = 340,
    padx: int = 40,
    valor_por_defecto: str | None = None
) -> ctk.CTkComboBox:
    """Crea un selector desplegable con su etiqueta descriptiva en la parte superior."""
    ctk.CTkLabel(
        contenedor,
        text=etiqueta,
        font=(config.FUENTE_FORMULARIOS, 11, "bold"),
        text_color="#334155"
    ).pack(anchor="w", padx=padx, pady=(8, 2))

    combo = ctk.CTkComboBox(contenedor, **estilo_combobox(valores, ancho=ancho))
    if valor_por_defecto and valor_por_defecto in valores:
        combo.set(valor_por_defecto)
    elif valores:
        combo.set(valores[0])
    combo.pack(padx=padx, pady=(0, 2))
    return combo


def agregar_botones_accion(contenedor, comando_guardar, ventana_cerrar, texto_guardar: str = "Guardar"):
    """Inserta los botones 'Guardar' y 'Cancelar' al final de un formulario."""
    frame_btn = ctk.CTkFrame(contenedor, fg_color="transparent")
    frame_btn.pack(pady=(16, 14))

    ctk.CTkButton(
        frame_btn,
        text=texto_guardar,
        command=comando_guardar,
        width=140,
        height=40,
        corner_radius=16,
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        fg_color=config.COLOR_CELESTE_UCC,
        hover_color=config.COLOR_CELESTE_HOVER,
        text_color="white"
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        frame_btn,
        text="Cancelar",
        command=ventana_cerrar.destroy,
        width=125,
        height=40,
        corner_radius=16,
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        fg_color="#E2E8F0",
        hover_color="#CBD5E1",
        text_color="#1E293B"
    ).pack(side="right", padx=8)


def crear_cuerpo_con_barra_fija(ventana, comando_guardar, texto_guardar: str = "Guardar"):
    """
    Estructura una ventana de formulario largo con:
      - Una barra inferior FIJA con los botones de acción (siempre visibles).
      - Un cuerpo con desplazamiento vertical para el contenido del formulario.
    Retorna el contenedor (cuerpo) donde se deben colocar los campos.
    """
    barra = ctk.CTkFrame(ventana, fg_color="#F8FAFC", corner_radius=0)
    barra.pack(side="bottom", fill="x")

    ctk.CTkButton(
        barra,
        text=texto_guardar,
        command=comando_guardar,
        width=150,
        height=38,
        corner_radius=16,
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        fg_color=config.COLOR_CELESTE_UCC,
        hover_color=config.COLOR_CELESTE_HOVER,
        text_color="white"
    ).pack(side="left", padx=(70, 8), pady=10)

    ctk.CTkButton(
        barra,
        text="Cancelar",
        command=ventana.destroy,
        width=125,
        height=38,
        corner_radius=16,
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        fg_color="#E2E8F0",
        hover_color="#CBD5E1",
        text_color="#1E293B"
    ).pack(side="left", padx=8, pady=10)

    cuerpo = ctk.CTkScrollableFrame(ventana, fg_color="white", corner_radius=0)
    cuerpo.pack(fill="both", expand=True)
    return cuerpo


def abrir_ventana_generar_pdf(cedula_fija: str | None = None):
    """
    Ventana modal para exportar Recibo de Matrícula o Boletín de Notas en PDF,
    abriendo el Explorador de Archivos para elegir dónde y con qué nombre guardarlo.

    Si se indica `cedula_fija` (sesión de un estudiante), el documento se genera
    únicamente para esa persona y NO se muestra selector de estudiantes.
    """
    if cedula_fija:
        fila_est = db.obtener_estudiante(cedula_fija)
        if not fila_est:
            return messagebox.showwarning("Estudiante no registrado", "Su documento no figura en la base de datos.")
        opciones_est = [f"{fila_est[0]} - {fila_est[1]} {fila_est[2]}"]
    else:
        opciones_est = db.obtener_opciones("Estudiantes", 0, 1)
        if not opciones_est:
            return messagebox.showwarning("Sin registros", "No hay estudiantes registrados en la base de datos.", parent=None)

    vent = crear_ventana_modal("Exportar Documentos Oficiales en PDF", 460, 390)
    ctk.CTkLabel(
        vent,
        text="Generador de Documentos PDF",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(18, 6))

    if cedula_fija:
        TextoDeslizable(
            vent, texto=f"👤 Estudiante: {opciones_est[0]}", fuente=(config.FUENTE_FORMULARIOS, 12, "bold"),
            color_texto="#1E3A8A", fondo="white"
        ).pack(padx=45, pady=(0, 6), fill="x")

    combo_tipo = crear_combo_formulario(
        vent,
        "Tipo de Documento a Exportar:",
        ["Recibo Oficial de Matrícula", "Boletín Oficial de Calificaciones"],
        ancho=370,
        padx=45
    )

    combo_est = None
    if not cedula_fija:
        combo_est = crear_combo_formulario(
            vent,
            "Seleccione el Estudiante:",
            opciones_est,
            ancho=370,
            padx=45
        )

    def exportar():
        cedula = cedula_fija if cedula_fija else db.extraer_id(combo_est.get())
        es_boletin = "Notas" in combo_tipo.get() or "Calificaciones" in combo_tipo.get()
        nombre_sugerido = f"Reporte_Notas_{cedula}.pdf" if es_boletin else f"Recibo_Matricula_{cedula}.pdf"

        ruta_elegida = filedialog.asksaveasfilename(
            parent=vent,
            title="Guardar Documento PDF Oficial Como...",
            initialdir=str(config.CARPETA_REPORTES_PDF),
            initialfile=nombre_sugerido,
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")]
        )
        if not ruta_elegida:
            return

        if es_boletin:
            exito, resultado = generar_pdf_notas(cedula, ruta_destino=ruta_elegida)
        else:
            exito, resultado = generar_pdf_matricula(cedula, ruta_destino=ruta_elegida)

        if exito:
            messagebox.showinfo(
                "Documento PDF Exportado",
                f"El documento fue guardado exitosamente en:\n\n{resultado}",
                parent=vent
            )
            vent.destroy()
        else:
            messagebox.showwarning("No se pudo generar el PDF", resultado, parent=vent)

    agregar_botones_accion(vent, exportar, vent, texto_guardar="Guardar PDF Como...")
