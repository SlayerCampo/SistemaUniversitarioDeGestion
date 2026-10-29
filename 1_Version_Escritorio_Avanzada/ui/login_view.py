from __future__ import annotations
# ==============================================================================
# ARCHIVO: ui/login_view.py
# PROPÓSITO: Construir la pantalla de Inicio de Sesión (Login) con diseño
#            dividido (panel corporativo azul a la izquierda con logo UCC y
#            formulario de acceso a la derecha con avatar dinámico y botones
#            de autocompletado rápido para sustentación).
# ==============================================================================

from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageDraw
import config
from core.seguridad import autenticar_usuario


def _crear_avatar_usuario():
    """Dibuja en memoria un ícono vectorial de perfil usando Pillow (ImageDraw)."""
    img = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, 110, 110), fill="#EBF3FA")
    draw.ellipse((33, 20, 77, 64), fill=config.COLOR_AZUL_UCC)
    draw.ellipse((18, 70, 92, 145), fill=config.COLOR_AZUL_UCC)
    return img


def dibujar_login(contenedor, callback_exito):
    """
    Renderiza el contenedor completo de inicio de sesión dentro de la ventana
    principal y ejecuta `callback_exito(datos_sesion)` cuando el usuario ingresa.
    """
    frame_fondo = ctk.CTkFrame(contenedor, fg_color=config.COLOR_MORADO_UCC, corner_radius=0)
    frame_fondo.pack(expand=True, fill="both")

    tarjeta = ctk.CTkFrame(frame_fondo, fg_color="white", corner_radius=18, width=820, height=510)
    tarjeta.place(relx=0.5, rely=0.5, anchor="center")
    tarjeta.pack_propagate(False)

    # --------------------------------------------------------------------------
    # PANEL IZQUIERDO: Identidad Institucional UCC
    # --------------------------------------------------------------------------
    frame_izq = ctk.CTkFrame(tarjeta, fg_color=config.COLOR_AZUL_UCC, corner_radius=15, width=350)
    frame_izq.pack(side="left", fill="y", padx=12, pady=12)
    frame_izq.pack_propagate(False)

    frame_logo = ctk.CTkFrame(frame_izq, fg_color="white", corner_radius=15)
    frame_logo.pack(pady=(28, 16))

    if config.RUTA_LOGO_UCC.exists():
        imagen_ucc = ctk.CTkImage(light_image=Image.open(config.RUTA_LOGO_UCC), size=(135, 135))
        ctk.CTkLabel(frame_logo, image=imagen_ucc, text="").pack(padx=16, pady=10)

    ctk.CTkLabel(
        frame_izq,
        text="Portal Universitario",
        font=(config.FUENTE_PRINCIPAL, 23, "bold"),
        text_color="white"
    ).pack(anchor="w", padx=26, pady=(4, 2))

    ctk.CTkLabel(
        frame_izq,
        text="SISTEMA INTEGRAL ACADÉMICO UCC",
        font=(config.FUENTE_PRINCIPAL, 12, "bold"),
        text_color="#B3E5FC"
    ).pack(anchor="w", padx=26, pady=(0, 14))

    descripcion = (
        "Plataforma avanzada de gestión:\n\n"
        "• Carrito de matrícula con detector\n  automático de cruces de horario.\n"
        "• Control de cupos en tiempo real.\n"
        "• Edición y consulta de notas (PPS).\n"
        "• Importación/Exportación Excel y PDF."
    )
    ctk.CTkLabel(
        frame_izq,
        text=descripcion,
        font=(config.FUENTE_PRINCIPAL, 12),
        text_color="white",
        justify="left"
    ).pack(anchor="w", padx=26)

    ctk.CTkLabel(
        frame_izq,
        text="Universidad Cooperativa de Colombia — Cali",
        font=(config.FUENTE_PRINCIPAL, 10),
        text_color="#E1F5FE"
    ).pack(side="bottom", pady=16)

    # --------------------------------------------------------------------------
    # PANEL DERECHO: Formulario de Autenticación
    # --------------------------------------------------------------------------
    frame_der = ctk.CTkFrame(tarjeta, fg_color="white")
    frame_der.pack(side="right", fill="both", expand=True, padx=28, pady=12)

    img_avatar = ctk.CTkImage(light_image=_crear_avatar_usuario(), size=(66, 66))
    ctk.CTkLabel(frame_der, image=img_avatar, text="").pack(pady=(12, 4))

    ctk.CTkLabel(
        frame_der,
        text="Iniciar Sesión",
        font=(config.FUENTE_PRINCIPAL, 22, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(0, 14))

    ctk.CTkLabel(
        frame_der,
        text="Usuario o Cédula *",
        font=(config.FUENTE_PRINCIPAL, 11, "bold"),
        text_color="#64748B"
    ).pack(anchor="w", padx=32)

    caja_usuario = ctk.CTkEntry(
        frame_der,
        placeholder_text="Ej: admin, profe, estudiante o 1001",
        font=(config.FUENTE_PRINCIPAL, 12),
        width=310,
        height=38,
        fg_color="#F1F5F9",
        text_color="black",
        border_width=1,
        border_color="#CBD5E1",
        corner_radius=10
    )
    caja_usuario.pack(pady=(2, 12))

    ctk.CTkLabel(
        frame_der,
        text="Contraseña *",
        font=(config.FUENTE_PRINCIPAL, 11, "bold"),
        text_color="#64748B"
    ).pack(anchor="w", padx=32)

    caja_pass = ctk.CTkEntry(
        frame_der,
        placeholder_text="Contraseña (Ej: 1234)",
        show="*",
        font=(config.FUENTE_PRINCIPAL, 12),
        width=310,
        height=38,
        fg_color="#F1F5F9",
        text_color="black",
        border_width=1,
        border_color="#CBD5E1",
        corner_radius=10
    )
    caja_pass.pack(pady=(2, 16))

    def intentar_login(event=None):
        exito, info = autenticar_usuario(caja_usuario.get(), caja_pass.get())
        if exito:
            callback_exito(info)
        else:
            messagebox.showerror("Acceso Denegado", info.get("mensaje", "Credenciales inválidas."))

    caja_pass.bind("<Return>", intentar_login)

    ctk.CTkButton(
        frame_der,
        text="INGRESAR AL SISTEMA",
        command=intentar_login,
        width=310,
        height=40,
        font=(config.FUENTE_PRINCIPAL, 13, "bold"),
        fg_color=config.COLOR_AZUL_UCC,
        hover_color=config.COLOR_AZUL_OSCURO,
        corner_radius=10
    ).pack(pady=(0, 12))

    # Botones de acceso rápido para agilizar la demostración ante el profesor
    ctk.CTkLabel(
        frame_der,
        text="Acceso rápido de demostración:",
        font=(config.FUENTE_PRINCIPAL, 10),
        text_color="gray"
    ).pack(pady=(2, 4))

    frame_demo = ctk.CTkFrame(frame_der, fg_color="transparent")
    frame_demo.pack(pady=(0, 10))

    def autocompletar(usr, pwd):
        caja_usuario.delete(0, "end")
        caja_usuario.insert(0, usr)
        caja_pass.delete(0, "end")
        caja_pass.insert(0, pwd)
        intentar_login()

    estilo_chip = {
        "width": 96,
        "height": 28,
        "corner_radius": 8,
        "font": (config.FUENTE_PRINCIPAL, 11, "bold"),
        "fg_color": "#E2E8F0",
        "hover_color": "#CBD5E1",
        "text_color": "#1E293B"
    }
    ctk.CTkButton(frame_demo, text="Admin", command=lambda: autocompletar("admin", "1234"), **estilo_chip).pack(side="left", padx=4)
    ctk.CTkButton(frame_demo, text="Estudiante", command=lambda: autocompletar("estudiante", "1234"), **estilo_chip).pack(side="left", padx=4)
    ctk.CTkButton(frame_demo, text="Profesor", command=lambda: autocompletar("profe", "1234"), **estilo_chip).pack(side="left", padx=4)

    ctk.CTkButton(
        frame_der,
        text="Salir del programa",
        command=contenedor.destroy,
        fg_color="transparent",
        text_color="#64748B",
        hover_color="#F1F5F9",
        height=26,
        font=(config.FUENTE_PRINCIPAL, 11, "underline")
    ).pack(pady=(4, 0))

    return frame_fondo

