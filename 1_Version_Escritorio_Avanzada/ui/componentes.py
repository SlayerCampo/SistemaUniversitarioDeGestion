from __future__ import annotations
# ==============================================================================
# ARCHIVO: ui/componentes.py
# PROPÓSITO: Componentes visuales reutilizables de la interfaz.
#
#            TextoDeslizable: etiqueta de una sola línea para textos largos que
#            no caben en su espacio. En lugar de mostrar una barra de
#            desplazamiento, ofrece una interacción suave:
#              • Si el texto es más largo que el espacio, aparece un indicador
#                discreto "›" en el borde (y "‹" cuando hay texto oculto a la izquierda).
#              • Al pasar el mouse por encima, el texto se desliza con una
#                animación suave hasta mostrar el final; al retirar el mouse,
#                vuelve a su posición inicial.
#              • También puede arrastrarse con el mouse o con Shift + rueda.
#              • En reposo permanece quieto (no hay movimiento continuo).
# ==============================================================================

import time
import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk
import config


class TextoDeslizable(ctk.CTkFrame):
    """Etiqueta de una línea con desplazamiento horizontal animado al pasar el mouse."""

    MARGEN = 4                 # Espacio interno a izquierda y derecha (px)
    ANCHO_INDICADOR = 22       # Ancho de la zona con degradado/indicador en los bordes (px)
    MS_POR_FRAME = 16          # ~60 fotogramas por segundo
    MS_POR_PIXEL = 5           # Velocidad base de la animación

    def __init__(
        self,
        master,
        texto: str = "",
        fuente: tuple = (config.FUENTE_FORMULARIOS, 11),
        color_texto: str = "#1E293B",
        fondo: str = "white",
        color_indicador: str = config.COLOR_AZUL_UCC,
        **kwargs
    ):
        super().__init__(master, fg_color=fondo, corner_radius=0, **kwargs)
        self._texto = str(texto)
        self._fondo = fondo
        self._color_indicador = color_indicador
        self._offset = 0.0
        self._max_offset = 0.0
        self._id_animacion = None
        self._arrastrando = False
        self._x_inicio_arrastre = 0
        self._offset_inicio_arrastre = 0.0

        peso = fuente[2] if len(fuente) > 2 else "normal"
        self._fuente = tkfont.Font(family=fuente[0], size=fuente[1], weight=peso)
        altura = self._fuente.metrics("linespace") + 8

        self._canvas = tk.Canvas(self, height=altura, bg=fondo, highlightthickness=0, bd=0)
        self._canvas.pack(fill="x", expand=True)
        self._y_centro = altura // 2

        self._id_texto = self._canvas.create_text(
            self.MARGEN, self._y_centro, text=self._texto, anchor="w",
            font=self._fuente, fill=color_texto
        )

        # Indicadores de borde (se crean encima del texto)
        self._rect_der = self._canvas.create_rectangle(0, 0, 0, altura, fill=fondo, outline=fondo, state="hidden")
        self._flecha_der = self._canvas.create_text(
            0, self._y_centro, text="›", anchor="e", fill=color_indicador,
            font=(fuente[0], fuente[1] + 5, "bold"), state="hidden"
        )
        self._rect_izq = self._canvas.create_rectangle(0, 0, 0, altura, fill=fondo, outline=fondo, state="hidden")
        self._flecha_izq = self._canvas.create_text(
            0, self._y_centro, text="‹", anchor="w", fill=color_indicador,
            font=(fuente[0], fuente[1] + 5, "bold"), state="hidden"
        )

        self._canvas.bind("<Configure>", self._recalcular)
        self._canvas.bind("<Enter>", self._al_entrar)
        self._canvas.bind("<Leave>", self._al_salir)
        self._canvas.bind("<ButtonPress-1>", self._iniciar_arrastre)
        self._canvas.bind("<B1-Motion>", self._arrastrar)
        self._canvas.bind("<ButtonRelease-1>", self._terminar_arrastre)
        self._canvas.bind("<Shift-MouseWheel>", self._rueda_horizontal)

    # --------------------------------------------------------------------------
    # API pública
    # --------------------------------------------------------------------------
    def configurar(self, texto: str | None = None, color_texto: str | None = None):
        """Actualiza el texto y/o color mostrado y reinicia la posición."""
        self._cancelar_animacion()
        if texto is not None:
            self._texto = str(texto)
            self._canvas.itemconfigure(self._id_texto, text=self._texto)
        if color_texto is not None:
            self._canvas.itemconfigure(self._id_texto, fill=color_texto)
        self._offset = 0.0
        self._recalcular()

    def destroy(self):
        self._cancelar_animacion()
        super().destroy()

    # --------------------------------------------------------------------------
    # Cálculo de desborde e indicadores
    # --------------------------------------------------------------------------
    def _recalcular(self, _evento=None):
        try:
            ancho = max(1, self._canvas.winfo_width())
            ancho_texto = self._fuente.measure(self._texto)
            self._max_offset = float(max(0, ancho_texto + 2 * self.MARGEN - ancho))
            self._offset = min(self._offset, self._max_offset)

            self._canvas.coords(self._rect_der, ancho - self.ANCHO_INDICADOR, 0, ancho, 200)
            self._canvas.coords(self._flecha_der, ancho - 3, self._y_centro)
            self._canvas.coords(self._rect_izq, 0, 0, self.ANCHO_INDICADOR, 200)
            self._canvas.coords(self._flecha_izq, 3, self._y_centro)

            self._canvas.configure(cursor="sb_h_double_arrow" if self._max_offset > 0 else "")
            self._aplicar_offset()
        except tk.TclError:
            pass

    def _aplicar_offset(self):
        try:
            self._canvas.coords(self._id_texto, self.MARGEN - self._offset, self._y_centro)
            hay_mas_derecha = self._max_offset > 0 and self._offset < self._max_offset - 1
            hay_mas_izquierda = self._offset > 1
            self._canvas.itemconfigure(self._rect_der, state="normal" if hay_mas_derecha else "hidden")
            self._canvas.itemconfigure(self._flecha_der, state="normal" if hay_mas_derecha else "hidden")
            self._canvas.itemconfigure(self._rect_izq, state="normal" if hay_mas_izquierda else "hidden")
            self._canvas.itemconfigure(self._flecha_izq, state="normal" if hay_mas_izquierda else "hidden")
        except tk.TclError:
            pass

    # --------------------------------------------------------------------------
    # Animación suave (solo se mueve al pasar el mouse)
    # --------------------------------------------------------------------------
    def _cancelar_animacion(self):
        if self._id_animacion is not None:
            try:
                self.after_cancel(self._id_animacion)
            except (tk.TclError, ValueError):
                pass
            self._id_animacion = None

    def _animar_hasta(self, destino: float):
        self._cancelar_animacion()
        origen = self._offset
        distancia = abs(destino - origen)
        if distancia < 0.5:
            return
        duracion_ms = max(350.0, min(2400.0, distancia * self.MS_POR_PIXEL))
        inicio = time.monotonic()

        def paso():
            try:
                t = min(1.0, (time.monotonic() - inicio) * 1000.0 / duracion_ms)
                suave = t * t * (3 - 2 * t)  # Interpolación suave (ease in-out)
                self._offset = origen + (destino - origen) * suave
                self._aplicar_offset()
                if t < 1.0:
                    self._id_animacion = self.after(self.MS_POR_FRAME, paso)
                else:
                    self._id_animacion = None
            except tk.TclError:
                self._id_animacion = None

        paso()

    def _al_entrar(self, _evento=None):
        if self._max_offset > 0 and not self._arrastrando:
            self._animar_hasta(self._max_offset)

    def _al_salir(self, _evento=None):
        if self._max_offset > 0 and not self._arrastrando:
            self._animar_hasta(0.0)

    # --------------------------------------------------------------------------
    # Desplazamiento manual (arrastrar con el mouse o Shift + rueda)
    # --------------------------------------------------------------------------
    def _iniciar_arrastre(self, evento):
        if self._max_offset <= 0:
            return
        self._cancelar_animacion()
        self._arrastrando = True
        self._x_inicio_arrastre = evento.x
        self._offset_inicio_arrastre = self._offset

    def _arrastrar(self, evento):
        if not self._arrastrando:
            return
        nuevo = self._offset_inicio_arrastre - (evento.x - self._x_inicio_arrastre)
        self._offset = max(0.0, min(self._max_offset, nuevo))
        self._aplicar_offset()

    def _terminar_arrastre(self, _evento=None):
        self._arrastrando = False

    def _rueda_horizontal(self, evento):
        if self._max_offset <= 0:
            return
        self._cancelar_animacion()
        paso = -(evento.delta / 120.0) * 40.0
        self._offset = max(0.0, min(self._max_offset, self._offset + paso))
        self._aplicar_offset()

