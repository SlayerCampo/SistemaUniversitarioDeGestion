from __future__ import annotations
# ==============================================================================
# ARCHIVO: ui/notas_views.py
# PROPÓSITO: Gestión integral de calificaciones para el rol Profesor.
#            Soluciona la limitación del proyecto base: permite consultar si una
#            materia ya fue calificada, precargar las notas actuales en pantalla
#            y ACTUALIZAR la fila existente sin duplicar registros en Excel.
#            Campos con etiqueta superior y ejemplos/placeholders internos.
# ==============================================================================

import uuid
from tkinter import messagebox
import customtkinter as ctk
import config
import data.db_excel as db
from ui import (
    crear_ventana_modal,
    crear_combo_formulario,
    estilo_combobox,
    agregar_botones_accion,
)


def calcular_definitiva(n1: float, n2: float, n3: float) -> tuple[float, str]:
    """Calcula la nota definitiva y determina el estado ('Aprobado' o 'Reprobado')."""
    if config.USAR_PROMEDIO_PONDERADO:
        p1, p2, p3 = config.PESOS_NOTAS
        definitiva = round(n1 * p1 + n2 * p2 + n3 * p3, 2)
    else:
        definitiva = round((n1 + n2 + n3) / 3.0, 2)

    estado = "Aprobado" if definitiva >= config.NOTA_APROBATORIA else "Reprobado"
    return definitiva, estado


def abrir_ventana_notas(callback_refrescar=None):
    """
    Ventana de Registro y Edición de Calificaciones:
    - Permite seleccionar el estudiante de un listado desplegable.
    - Filtra sus asignaturas activas matriculadas.
    - Si la asignatura ya cuenta con notas previas, las carga automáticamente
      en las cajas de texto para su edición/actualización.
    """
    opciones_est = db.obtener_opciones("Estudiantes", 0, 1)
    if not opciones_est:
        return messagebox.showwarning("Sin estudiantes", "No hay estudiantes registrados.")

    vent = crear_ventana_modal("Gestión y Edición de Calificaciones", 500, 560, permitir_redimensionar=True)
    ctk.CTkLabel(
        vent,
        text="Registro y Actualización de Notas",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(16, 6))

    combo_est = crear_combo_formulario(
        vent,
        "1. Seleccione el Estudiante:",
        opciones_est,
        ancho=400,
        padx=50
    )

    combo_materia = crear_combo_formulario(
        vent,
        "2. Asignatura Matriculada Activa:",
        ["Seleccione estudiante"],
        ancho=400,
        padx=50
    )

    lbl_estado_actual = ctk.CTkLabel(
        vent,
        text="Estado: Sin calificar",
        font=(config.FUENTE_FORMULARIOS, 12, "bold"),
        text_color="gray"
    )
    lbl_estado_actual.pack(pady=(8, 4))

    # Cajas para las 3 notas parciales con etiqueta arriba de cada una
    frame_notas_gral = ctk.CTkFrame(vent, fg_color="transparent")
    frame_notas_gral.pack(pady=4)

    estilo_caja_nota = {
        "width": 115,
        "height": 38,
        "fg_color": config.COLOR_CAJA_TEXTO,
        "text_color": "black",
        "border_width": 1,
        "border_color": "#CBD5E1",
        "corner_radius": 10,
        "font": (config.FUENTE_FORMULARIOS, 13, "bold"),
        "justify": "center"
    }

    # Columna Nota 1
    col1 = ctk.CTkFrame(frame_notas_gral, fg_color="transparent")
    col1.pack(side="left", padx=8)
    ctk.CTkLabel(col1, text="Corte 1:", font=(config.FUENTE_FORMULARIOS, 11, "bold"), text_color="#334155").pack(anchor="w")
    caja_n1 = ctk.CTkEntry(col1, placeholder_text="Ej: 4.5", **estilo_caja_nota)
    caja_n1.pack()

    # Columna Nota 2
    col2 = ctk.CTkFrame(frame_notas_gral, fg_color="transparent")
    col2.pack(side="left", padx=8)
    ctk.CTkLabel(col2, text="Corte 2:", font=(config.FUENTE_FORMULARIOS, 11, "bold"), text_color="#334155").pack(anchor="w")
    caja_n2 = ctk.CTkEntry(col2, placeholder_text="Ej: 3.8", **estilo_caja_nota)
    caja_n2.pack()

    # Columna Nota 3
    col3 = ctk.CTkFrame(frame_notas_gral, fg_color="transparent")
    col3.pack(side="left", padx=8)
    ctk.CTkLabel(col3, text="Corte 3:", font=(config.FUENTE_FORMULARIOS, 11, "bold"), text_color="#334155").pack(anchor="w")
    caja_n3 = ctk.CTkEntry(col3, placeholder_text="Ej: 4.2", **estilo_caja_nota)
    caja_n3.pack()

    lbl_preview = ctk.CTkLabel(
        vent,
        text="Definitiva calculada: --",
        font=(config.FUENTE_FORMULARIOS, 14, "bold"),
        text_color=config.COLOR_AZUL_UCC
    )
    lbl_preview.pack(pady=8)

    # Mapa auxiliar en memoria: opcion_combo -> (id_matricula, id_materia)
    mapa_seleccion = {}

    def cargar_notas_de_materia(*_):
        seleccion = combo_materia.get()
        caja_n1.delete(0, "end")
        caja_n2.delete(0, "end")
        caja_n3.delete(0, "end")

        if seleccion not in mapa_seleccion:
            lbl_estado_actual.configure(text="Estado: Sin materias activas", text_color=config.COLOR_ROJO_ERROR)
            lbl_preview.configure(text="Definitiva calculada: --", text_color="gray")
            return

        id_matricula, _ = mapa_seleccion[seleccion]
        libro = db.cargar_libro(solo_lectura=True)
        fila_nota = db.buscar_fila(libro["Notas"], 1, id_matricula)
        libro.close()

        if fila_nota:
            caja_n1.insert(0, str(fila_nota[3]))
            caja_n2.insert(0, str(fila_nota[4]))
            caja_n3.insert(0, str(fila_nota[5]))
            lbl_estado_actual.configure(text=f"Estado: Registrada ({fila_nota[7]})", text_color=config.COLOR_AZUL_UCC)
            actualizar_preview()
        else:
            lbl_estado_actual.configure(text="Estado: Pendiente de Calificar (Sin notas previas)", text_color=config.COLOR_AMARILLO_AVISO)
            lbl_preview.configure(text="Definitiva calculada: --", text_color="gray")

    def actualizar_preview(*_):
        try:
            n1 = float(caja_n1.get().strip().replace(",", "."))
            n2 = float(caja_n2.get().strip().replace(",", "."))
            n3 = float(caja_n3.get().strip().replace(",", "."))
            if all(0.0 <= x <= 5.0 for x in [n1, n2, n3]):
                definitiva, estado = calcular_definitiva(n1, n2, n3)
                color = config.COLOR_VERDE_EXITO if estado == "Aprobado" else config.COLOR_ROJO_ERROR
                lbl_preview.configure(text=f"Definitiva calculada: {definitiva:.2f}  ({estado})", text_color=color)
            else:
                lbl_preview.configure(text="Las notas deben estar entre 0.0 y 5.0", text_color=config.COLOR_ROJO_ERROR)
        except ValueError:
            lbl_preview.configure(text="Definitiva calculada: --", text_color="gray")

    for caja in (caja_n1, caja_n2, caja_n3):
        caja.bind("<KeyRelease>", actualizar_preview)

    def refrescar_materias_del_estudiante(*_):
        cedula = db.extraer_id(combo_est.get())
        matriculas_activas = db.obtener_matriculas_activas(cedula)
        mapa_seleccion.clear()

        if not matriculas_activas:
            combo_materia.configure(values=["El estudiante no tiene asignaturas activas"])
            combo_materia.set("El estudiante no tiene asignaturas activas")
            cargar_notas_de_materia()
            return

        libro = db.cargar_libro(solo_lectura=True)
        opciones_m = []
        for mat in matriculas_activas:
            id_mat, id_curso = str(mat[0]), str(mat[2])
            fila_c = db.buscar_fila(libro["Materias"], 0, id_curso)
            nombre_c = fila_c[1] if fila_c else id_curso
            etiqueta = f"{id_curso} - {nombre_c} (Mat: {id_mat})"
            opciones_m.append(etiqueta)
            mapa_seleccion[etiqueta] = (id_mat, id_curso)
        libro.close()

        combo_materia.configure(values=opciones_m)
        combo_materia.set(opciones_m[0])
        cargar_notas_de_materia()

    combo_est.configure(command=refrescar_materias_del_estudiante)
    combo_materia.configure(command=cargar_notas_de_materia)

    refrescar_materias_del_estudiante()

    def guardar():
        seleccion = combo_materia.get()
        if seleccion not in mapa_seleccion:
            return messagebox.showwarning("Selección requerida", "Seleccione una asignatura válida.", parent=vent)

        id_matricula, id_materia = mapa_seleccion[seleccion]
        try:
            n1 = float(caja_n1.get().strip().replace(",", "."))
            n2 = float(caja_n2.get().strip().replace(",", "."))
            n3 = float(caja_n3.get().strip().replace(",", "."))
            for n in [n1, n2, n3]:
                if not (0.0 <= n <= 5.0):
                    raise ValueError
        except ValueError:
            return messagebox.showerror("Calificación inválida", "Las 3 notas deben ser números entre 0.0 y 5.0.", parent=vent)

        definitiva, estado = calcular_definitiva(n1, n2, n3)
        libro = db.cargar_libro()
        fila_existente = db.buscar_fila(libro["Notas"], 1, id_matricula)

        if fila_existente:
            id_nota = fila_existente[0]
            db.actualizar_fila(
                "Notas", 1, id_matricula,
                [id_nota, id_matricula, id_materia, n1, n2, n3, definitiva, estado]
            )
            accion = "actualizaron"
        else:
            id_nota = f"NOT_{id_matricula}"
            db.guardar_datos(
                libro["Notas"],
                [id_nota, id_matricula, id_materia, n1, n2, n3, definitiva, estado]
            )
            accion = "registraron"

        libro.close()
        if callback_refrescar:
            callback_refrescar()

        messagebox.showinfo(
            "Notas Guardadas",
            f"Se {accion} las calificaciones exitosamente.\n"
            f"Definitiva: {definitiva:.2f} — {estado}",
            parent=vent
        )
        vent.destroy()

    agregar_botones_accion(vent, guardar, vent, texto_guardar="Guardar Calificaciones")
