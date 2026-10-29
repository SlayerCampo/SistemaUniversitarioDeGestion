from __future__ import annotations
# ==============================================================================
# ARCHIVO: ui/matricula_views.py
# PROPÓSITO: Módulos de Matrícula Inteligente para el rol Estudiante:
#            1. La matrícula se realiza SIEMPRE para el estudiante en sesión
#               (no se puede ver ni registrar en nombre de otra persona).
#            2. Solo se ofrecen las asignaturas del PROGRAMA del estudiante,
#               eligiendo primero la asignatura y luego el grupo/horario.
#            3. Muestra las asignaturas ya matriculadas y el carrito de nuevas
#               asignaturas con validación de créditos (6 a 19), cupos en tiempo
#               real, cruces de horario y repetición de la misma asignatura.
#            4. Retiro / cancelación de asignaturas con devolución de cupo.
#            5. Barra inferior fija: el botón "Confirmar Matrícula" siempre es visible.
# ==============================================================================

from datetime import date
import uuid
from tkinter import messagebox
import customtkinter as ctk
import config
import data.db_excel as db
from core.validador_horarios import validar_cruce_con_lista, codigo_base_materia
from core.gestor_cupos import descontar_cupo, restituir_cupo
from ui import (
    crear_ventana_modal,
    crear_campo_formulario,
    crear_combo_formulario,
    estilo_entrada,
    estilo_combobox,
    agregar_botones_accion,
)
from ui.componentes import TextoDeslizable


def _obtener_materias_activas_estudiante(cedula: str, periodo: str) -> list[dict]:
    """
    Devuelve la lista detallada de asignaturas que el estudiante ya tiene
    matriculadas en estado 'Activa' para el periodo indicado.
    """
    matriculas = db.obtener_datos("Matriculas")
    mapa_materias = {str(m[0]): m for m in db.obtener_datos("Materias")}
    inscritas = []

    for mat in matriculas:
        est_mat = str(mat[1]).strip()
        id_curso = str(mat[2]).strip()
        per_mat = str(mat[4]).strip()
        estado = str(mat[6]).strip().lower() if len(mat) > 6 and mat[6] else "activa"

        if est_mat == cedula and per_mat == periodo and estado == "activa":
            info_m = mapa_materias.get(id_curso)
            inscritas.append({
                "id_matricula": str(mat[0]),
                "id": id_curso,
                "nombre": str(info_m[1]) if info_m else id_curso,
                "creditos": int(mat[3]) if mat[3] is not None else 0,
                "docente": str(info_m[4]) if info_m and len(info_m) > 4 else "Por asignar",
                "horario": str(info_m[6]) if info_m and len(info_m) > 6 else ""
            })
    return inscritas


def _nombre_grupo(id_materia: str) -> str:
    """Convierte 'SIS101-G2' en 'Grupo 2' (o 'Grupo único' si no tiene sufijo de grupo)."""
    texto = str(id_materia).strip().upper()
    if "-G" in texto:
        return f"Grupo {texto.rsplit('-G', 1)[1]}"
    return "Grupo único"


def abrir_ventana_matricula(callback_refrescar=None, cedula_fija: str | None = None):
    """
    Ventana de Matrícula Académica del estudiante en sesión (`cedula_fija`).
    No existe selector de estudiantes: solo se opera sobre la propia cuenta.
    """
    if not cedula_fija:
        return messagebox.showwarning(
            "Estudiante no seleccionado",
            "Seleccione o inicie sesión con un estudiante para realizar la matrícula."
        )

    fila_est = db.obtener_estudiante(cedula_fija)
    if not fila_est:
        return messagebox.showwarning(
            "Estudiante no registrado",
            f"El documento '{cedula_fija}' no figura en la base de datos.\n"
            "Ingrese como Administrador para registrarlo o importar un archivo Excel."
        )

    cedula = str(fila_est[0]).strip()
    nombre_est = f"{fila_est[1]} {fila_est[2]}"
    id_programa = str(fila_est[6]).strip()
    nombre_programa = db.obtener_nombre_programa(id_programa)

    if not db.obtener_materias_programa(id_programa):
        return messagebox.showwarning(
            "Programa sin asignaturas",
            f"El programa '{id_programa} - {nombre_programa}' aún no tiene asignaturas registradas.\n"
            "Ingrese como Administrador para crearlas o importar un archivo Excel."
        )

    vent = crear_ventana_modal("Matrícula Académica Inteligente", 680, 720, permitir_redimensionar=True)

    # ==========================================================================
    # BARRA INFERIOR FIJA (SIEMPRE VISIBLE EN PANTALLA)
    # ==========================================================================
    frame_fijo_inf = ctk.CTkFrame(vent, fg_color="#F8FAFC", corner_radius=0, height=105)
    frame_fijo_inf.pack(side="bottom", fill="x")

    lbl_resumen = ctk.CTkLabel(
        frame_fijo_inf,
        text="Ya Inscritos: 0 Cr.  |  En Carrito: 0 Cr.  |  Total Semestre: 0 / 19 Cr.",
        font=(config.FUENTE_FORMULARIOS, 12, "bold"),
        text_color=config.COLOR_ROJO_ERROR
    )
    lbl_resumen.pack(pady=(6, 4))

    frame_botones_accion = ctk.CTkFrame(frame_fijo_inf, fg_color="transparent")
    frame_botones_accion.pack(pady=(0, 8))

    btn_confirmar = ctk.CTkButton(
        frame_botones_accion,
        text="✅ Confirmar Matrícula",
        width=230,
        height=38,
        corner_radius=16,
        font=(config.FUENTE_FORMULARIOS, 13, "bold"),
        fg_color=config.COLOR_VERDE_EXITO,
        hover_color=config.COLOR_VERDE_HOVER,
        text_color="white"
    )
    btn_confirmar.pack(side="left", padx=8)

    ctk.CTkButton(
        frame_botones_accion,
        text="Cerrar",
        command=vent.destroy,
        width=120,
        height=38,
        corner_radius=16,
        font=(config.FUENTE_FORMULARIOS, 12, "bold"),
        fg_color="#E2E8F0",
        hover_color="#CBD5E1",
        text_color="#1E293B"
    ).pack(side="left", padx=8)

    # ==========================================================================
    # CUERPO CON DESPLAZAMIENTO VERTICAL
    # ==========================================================================
    cuerpo = ctk.CTkScrollableFrame(vent, fg_color="white", corner_radius=0)
    cuerpo.pack(fill="both", expand=True, padx=6, pady=(6, 0))

    ctk.CTkLabel(
        cuerpo,
        text=f"Matrícula Académica ({config.CREDITOS_MINIMOS} a {config.CREDITOS_MAXIMOS} Créditos)",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(6, 4))

    # Paso 1: Datos del estudiante en sesión y periodo
    ctk.CTkLabel(
        cuerpo,
        text="1. Estudiante en Sesión y Periodo Académico:",
        font=(config.FUENTE_FORMULARIOS, 12, "bold"),
        text_color="#475569"
    ).pack(anchor="w", padx=25, pady=(4, 0))

    frame_est = ctk.CTkFrame(cuerpo, fg_color="transparent")
    frame_est.pack(pady=3, padx=25, fill="x")

    frame_datos = ctk.CTkFrame(frame_est, fg_color="#F1F5F9", corner_radius=10)
    frame_datos.pack(side="left", fill="x", expand=True, padx=(0, 8))
    TextoDeslizable(
        frame_datos, texto=f"👤 {cedula} - {nombre_est}",
        fuente=(config.FUENTE_FORMULARIOS, 12, "bold"), color_texto="#1E3A8A", fondo="#F1F5F9"
    ).pack(fill="x", padx=8, pady=(6, 0))
    TextoDeslizable(
        frame_datos, texto=f"🎓 {id_programa} - {nombre_programa}   |   Semestre {fila_est[5]}",
        fuente=(config.FUENTE_FORMULARIOS, 11), color_texto="#475569", fondo="#F1F5F9"
    ).pack(fill="x", padx=8, pady=(0, 6))

    frame_per = ctk.CTkFrame(frame_est, fg_color="transparent")
    frame_per.pack(side="right")
    ctk.CTkLabel(
        frame_per,
        text="Periodo:",
        font=(config.FUENTE_FORMULARIOS, 10, "bold"),
        text_color="#475569"
    ).pack(anchor="w")
    caja_periodo = ctk.CTkEntry(
        frame_per,
        placeholder_text="Ej: 2026-2",
        width=120,
        height=36,
        font=(config.FUENTE_FORMULARIOS, 12)
    )
    caja_periodo.insert(0, config.PERIODO_ACTUAL_DEFECTO)
    caja_periodo.pack()

    # Paso 2: Asignaturas YA matriculadas en este periodo
    lbl_inscritas = ctk.CTkLabel(
        cuerpo,
        text="2. Asignaturas Ya Matriculadas en este Periodo:",
        font=(config.FUENTE_FORMULARIOS, 12, "bold"),
        text_color=config.COLOR_AZUL_UCC
    )
    lbl_inscritas.pack(anchor="w", padx=25, pady=(8, 2))

    frame_inscritas = ctk.CTkFrame(cuerpo, fg_color="#EFF6FF", corner_radius=10)
    frame_inscritas.pack(pady=2, padx=25, fill="x")

    # Paso 3: Elegir asignatura del programa y luego su grupo/horario
    ctk.CTkLabel(
        cuerpo,
        text="3. Paso A — Asignatura del Plan de Estudios:",
        font=(config.FUENTE_FORMULARIOS, 11, "bold"),
        text_color="#334155"
    ).pack(anchor="w", padx=25, pady=(8, 2))

    combo_curso = ctk.CTkComboBox(cuerpo, **estilo_combobox(["Cargando..."], ancho=580))
    combo_curso.pack(pady=2, padx=25, fill="x")

    ctk.CTkLabel(
        cuerpo,
        text="Paso B — Grupo y Horario Ofertado:",
        font=(config.FUENTE_FORMULARIOS, 11, "bold"),
        text_color="#334155"
    ).pack(anchor="w", padx=25, pady=(6, 2))

    combo_grupo = ctk.CTkComboBox(cuerpo, **estilo_combobox(["—"], ancho=580))
    combo_grupo.pack(pady=2, padx=25, fill="x")

    detalle_grupo = TextoDeslizable(
        cuerpo, texto="", fuente=(config.FUENTE_FORMULARIOS, 11), color_texto="#475569", fondo="white"
    )
    detalle_grupo.pack(padx=25, pady=(2, 2), fill="x")

    btn_agregar = ctk.CTkButton(
        cuerpo,
        text="➕ Agregar Asignatura al Carrito",
        fg_color=config.COLOR_AMARILLO_AVISO,
        hover_color=config.COLOR_AMARILLO_HOVER,
        text_color="black",
        font=(config.FUENTE_FORMULARIOS, 12, "bold"),
        width=260,
        height=36,
        corner_radius=14
    )
    btn_agregar.pack(pady=(4, 8))

    carrito = []
    cursos_por_etiqueta = {}   # 'SIS101 - Nombre (4 Cr.)' -> lista de grupos disponibles
    grupo_por_etiqueta = {}    # 'Grupo 1 · Lunes ... · Cupos: 30' -> dict del grupo

    # Paso 4: Carrito de compras
    lbl_carrito = ctk.CTkLabel(
        cuerpo,
        text="4. Carrito de Asignaturas Seleccionadas (Nuevas por Confirmar):",
        font=(config.FUENTE_FORMULARIOS, 12, "bold"),
        text_color="#475569"
    )
    lbl_carrito.pack(anchor="w", padx=25, pady=(4, 2))

    frame_carrito = ctk.CTkFrame(cuerpo, fg_color="#F8FAFC", corner_radius=10)
    frame_carrito.pack(pady=2, padx=25, fill="x")

    # --------------------------------------------------------------------------
    # Lógica de estado y renderizado
    # --------------------------------------------------------------------------
    def obtener_estado_creditos():
        periodo = caja_periodo.get().strip() or config.PERIODO_ACTUAL_DEFECTO
        ya_inscritas = _obtener_materias_activas_estudiante(cedula, periodo)
        cred_previos = sum(item["creditos"] for item in ya_inscritas)
        cred_carrito = sum(item["creditos"] for item in carrito)
        return ya_inscritas, cred_previos, cred_carrito, cred_previos + cred_carrito

    def al_elegir_grupo(_=None):
        grupo = grupo_por_etiqueta.get(combo_grupo.get())
        if not grupo:
            detalle_grupo.configurar("")
            return
        detalle_grupo.configurar(
            f"👨‍🏫 {grupo['docente']}   |   🕒 {grupo['horario']}   |   "
            f"Créditos: {grupo['creditos']}   |   Cupos disponibles: {grupo['cupos']}"
        )

    def al_elegir_curso(_=None):
        grupos = cursos_por_etiqueta.get(combo_curso.get(), [])
        grupo_por_etiqueta.clear()
        etiquetas = []
        for g in grupos:
            etiqueta = f"{g['grupo']} · {g['horario']} · Cupos: {g['cupos']}"
            grupo_por_etiqueta[etiqueta] = g
            etiquetas.append(etiqueta)
        combo_grupo.configure(values=etiquetas or ["—"])
        combo_grupo.set(etiquetas[0] if etiquetas else "—")
        al_elegir_grupo()

    def cargar_oferta(ya_inscritas: list[dict]):
        """Carga solo las asignaturas del programa del estudiante que aún no tiene ni en el carrito."""
        bases_ocupadas = {codigo_base_materia(x["id"]) for x in ya_inscritas}
        bases_ocupadas |= {codigo_base_materia(x["id"]) for x in carrito}

        agrupadas = {}
        for m in sorted(db.obtener_materias_programa(id_programa), key=lambda r: str(r[0])):
            base = codigo_base_materia(m[0])
            if base in bases_ocupadas:
                continue
            agrupadas.setdefault(base, []).append({
                "id": str(m[0]).strip(),
                "nombre": str(m[1]).strip(),
                "creditos": int(m[2]),
                "cupos": int(m[3]),
                "docente": str(m[4]).strip(),
                "horario": str(m[6]).strip(),
                "grupo": _nombre_grupo(m[0]),
            })

        cursos_por_etiqueta.clear()
        for base, grupos in agrupadas.items():
            etiqueta = f"{base} - {grupos[0]['nombre']} ({grupos[0]['creditos']} Cr.)"
            cursos_por_etiqueta[etiqueta] = grupos

        etiquetas = list(cursos_por_etiqueta.keys())
        vacio = "No hay más asignaturas disponibles para su programa"
        combo_curso.configure(values=etiquetas or [vacio])
        actual = combo_curso.get()
        combo_curso.set(actual if actual in cursos_por_etiqueta else (etiquetas[0] if etiquetas else vacio))
        al_elegir_curso()

    def actualizar_ui_completa():
        ya_inscritas, cred_prev, cred_carr, total = obtener_estado_creditos()

        # A. Asignaturas ya matriculadas
        for widget in frame_inscritas.winfo_children():
            widget.destroy()

        lbl_inscritas.configure(
            text=f"2. Asignaturas Ya Matriculadas en este Periodo ({len(ya_inscritas)} materias | {cred_prev} Créditos):"
        )

        if not ya_inscritas:
            ctk.CTkLabel(
                frame_inscritas,
                text="Aún no tiene asignaturas inscritas en este periodo.",
                text_color="#64748B",
                font=(config.FUENTE_FORMULARIOS, 11)
            ).pack(pady=10)
        else:
            for mat_ins in ya_inscritas:
                fila_ins = ctk.CTkFrame(frame_inscritas, fg_color="white", corner_radius=8)
                fila_ins.pack(fill="x", padx=6, pady=3)
                TextoDeslizable(
                    fila_ins,
                    texto=f"✅ {mat_ins['id']} - {mat_ins['nombre']} ({mat_ins['creditos']} Cr.)",
                    fuente=(config.FUENTE_FORMULARIOS, 11, "bold"), color_texto="#1E3A8A", fondo="white"
                ).pack(fill="x", padx=8, pady=(4, 0))
                TextoDeslizable(
                    fila_ins,
                    texto=f"Docente: {mat_ins['docente']}   |   Horario: {mat_ins['horario']}",
                    fuente=(config.FUENTE_FORMULARIOS, 10), color_texto="#475569", fondo="white"
                ).pack(fill="x", padx=8, pady=(0, 4))

        # B. Carrito de nuevas asignaturas
        for widget in frame_carrito.winfo_children():
            widget.destroy()

        if not carrito:
            ctk.CTkLabel(
                frame_carrito,
                text="El carrito está vacío. Elija una asignatura y pulse '➕ Agregar Asignatura al Carrito'.",
                text_color="gray",
                font=(config.FUENTE_FORMULARIOS, 11)
            ).pack(pady=10)
        else:
            for idx, item in enumerate(carrito):
                fila_f = ctk.CTkFrame(frame_carrito, fg_color="white", corner_radius=8)
                fila_f.pack(fill="x", padx=6, pady=3)

                btn_quitar = ctk.CTkButton(
                    fila_f,
                    text="Quitar",
                    width=65,
                    height=26,
                    fg_color=config.COLOR_ROJO_ERROR,
                    hover_color=config.COLOR_ROJO_HOVER,
                    font=(config.FUENTE_FORMULARIOS, 10, "bold"),
                    command=lambda i=idx: quitar_del_carrito(i)
                )
                btn_quitar.pack(side="right", padx=8, pady=4)

                frame_txt_item = ctk.CTkFrame(fila_f, fg_color="transparent")
                frame_txt_item.pack(side="left", fill="x", expand=True, padx=8, pady=2)
                TextoDeslizable(
                    frame_txt_item,
                    texto=f"🛒 {item['id']} - {item['nombre']} ({item['creditos']} Cr.)",
                    fuente=(config.FUENTE_FORMULARIOS, 11, "bold"), color_texto="#1E293B", fondo="white"
                ).pack(fill="x")
                TextoDeslizable(
                    frame_txt_item,
                    texto=f"Horario: {item['horario']}   |   Docente: {item['docente']}",
                    fuente=(config.FUENTE_FORMULARIOS, 10), color_texto="#64748B", fondo="white"
                ).pack(fill="x")

        # C. Resumen de créditos y estado del botón
        color_texto = config.COLOR_ROJO_ERROR
        if config.CREDITOS_MINIMOS <= total <= config.CREDITOS_MAXIMOS:
            color_texto = config.COLOR_VERDE_EXITO
        elif total > config.CREDITOS_MAXIMOS:
            color_texto = config.COLOR_ROJO_ERROR

        lbl_resumen.configure(
            text=(
                f"Ya Inscritos: {cred_prev} Cr.  |  "
                f"En Carrito: {cred_carr} Cr.  |  "
                f"Total Semestre: {total} / {config.CREDITOS_MAXIMOS} Cr. "
                f"(Mínimo requerido: {config.CREDITOS_MINIMOS})"
            ),
            text_color=color_texto
        )

        cargar_oferta(ya_inscritas)

    def quitar_del_carrito(indice: int):
        if 0 <= indice < len(carrito):
            carrito.pop(indice)
            actualizar_ui_completa()

    def agregar_al_carrito():
        curso_sel = combo_curso.get()
        grupos = cursos_por_etiqueta.get(curso_sel, [])
        if not grupos:
            return messagebox.showwarning("Selección vacía", "No hay grupos disponibles para agregar.", parent=vent)

        grupo = grupo_por_etiqueta.get(combo_grupo.get())
        if not grupo:
            return messagebox.showwarning("Selección requerida", "Elija un grupo y horario de la lista.", parent=vent)

        if grupo["cupos"] <= 0:
            return messagebox.showerror(
                "Cupo Agotado",
                f"No hay cupos disponibles para el grupo '{grupo['id']}' de {grupo['nombre']}.",
                parent=vent
            )

        base_elegida = codigo_base_materia(grupo["id"])
        ya_inscritas, _, _, total_actual = obtener_estado_creditos()

        if any(codigo_base_materia(x["id"]) == base_elegida for x in ya_inscritas):
            return messagebox.showwarning("Ya Matriculada", f"Ya tienes matriculada la asignatura '{grupo['nombre']}'.", parent=vent)

        if any(codigo_base_materia(x["id"]) == base_elegida for x in carrito):
            return messagebox.showwarning("En Carrito", f"La asignatura '{grupo['nombre']}' ya está en tu carrito.", parent=vent)

        if total_actual + grupo["creditos"] > config.CREDITOS_MAXIMOS:
            return messagebox.showerror(
                "Límite de Créditos Superado",
                f"Agregar esta asignatura ({grupo['creditos']} créditos) superaría el límite de {config.CREDITOS_MAXIMOS} créditos.\n"
                f"Créditos actuales: {total_actual}.",
                parent=vent
            )

        hay_cruce, msg_cruce = validar_cruce_con_lista(grupo, ya_inscritas + carrito)
        if hay_cruce:
            return messagebox.showerror("Conflicto de Horario Detectado", msg_cruce, parent=vent)

        carrito.append(dict(grupo))
        actualizar_ui_completa()

    btn_agregar.configure(command=agregar_al_carrito)
    combo_curso.configure(command=al_elegir_curso)
    combo_grupo.configure(command=al_elegir_grupo)
    caja_periodo.bind("<KeyRelease>", lambda _: actualizar_ui_completa())
    actualizar_ui_completa()

    def confirmar_matricula():
        periodo = caja_periodo.get().strip()
        if not periodo:
            return messagebox.showwarning("Periodo requerido", "Ingrese el periodo académico (Ej: 2026-2).", parent=vent)
        if not carrito:
            return messagebox.showwarning("Carrito vacío", "Agregue al menos una nueva asignatura al carrito para guardar.", parent=vent)

        _, _, _, total_creditos = obtener_estado_creditos()
        if total_creditos < config.CREDITOS_MINIMOS:
            return messagebox.showerror(
                "Créditos Insuficientes",
                f"Debe completar mínimo {config.CREDITOS_MINIMOS} créditos en el periodo.\n"
                f"Total actual (Inscritos + Carrito): {total_creditos} créditos.",
                parent=vent
            )

        fecha_actual = date.today().strftime("%Y-%m-%d")

        matriculadas_ok = 0
        for item in carrito:
            ok_cupo, msg_cupo = descontar_cupo(item["id"], 1)
            if not ok_cupo:
                messagebox.showwarning("Cupo agotado", msg_cupo, parent=vent)
                continue

            id_matricula = str(uuid.uuid4())[:8].upper()
            db.insertar_en_hoja(
                "Matriculas",
                [id_matricula, cedula, item["id"], item["creditos"], periodo, fecha_actual, "Activa"]
            )
            matriculadas_ok += 1

        if callback_refrescar:
            callback_refrescar()

        messagebox.showinfo(
            "Matrícula Confirmada",
            f"Se registraron exitosamente {matriculadas_ok} nueva(s) asignatura(s) para {nombre_est}\n"
            f"y se actualizaron los cupos disponibles.",
            parent=vent
        )
        vent.destroy()

    btn_confirmar.configure(command=confirmar_matricula)


def abrir_ventana_cancelar_materia(callback_refrescar=None, cedula_fija: str | None = None):
    """
    Módulo para consultar las asignaturas matriculadas activas del estudiante en
    sesión y retirar/cancelar una materia, devolviendo automáticamente +1 cupo.
    """
    if not cedula_fija:
        return messagebox.showwarning(
            "Estudiante no seleccionado",
            "Seleccione o inicie sesión con un estudiante para retirar asignaturas."
        )

    fila_est = db.obtener_estudiante(cedula_fija)
    if not fila_est:
        return messagebox.showwarning(
            "Estudiante no registrado",
            f"El documento '{cedula_fija}' no figura en la base de datos."
        )

    cedula = str(fila_est[0]).strip()
    nombre_est = f"{fila_est[1]} {fila_est[2]}"

    vent = crear_ventana_modal("Retiro / Cancelación de Asignaturas", 560, 490)
    ctk.CTkLabel(
        vent,
        text="Cancelación de Asignaturas",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(18, 6))

    TextoDeslizable(
        vent, texto=f"👤 Estudiante: {cedula} - {nombre_est}",
        fuente=(config.FUENTE_FORMULARIOS, 12, "bold"), color_texto="#1E3A8A", fondo="white"
    ).pack(padx=50, pady=(0, 6), fill="x")

    caja_periodo = crear_campo_formulario(
        vent,
        "Periodo Académico:",
        placeholder="Ej: 2026-2",
        ancho=460,
        padx=50,
        valor_inicial=config.PERIODO_ACTUAL_DEFECTO
    )

    combo_materias_activas = crear_combo_formulario(
        vent,
        "Asignatura Activa que Desea Retirar:",
        [],
        ancho=460,
        padx=50
    )

    detalle = TextoDeslizable(
        vent, texto="", fuente=(config.FUENTE_FORMULARIOS, 11), color_texto="#475569", fondo="white"
    )
    detalle.pack(padx=50, pady=(4, 4), fill="x")

    mapa_activas = {}

    def mostrar_detalle(_=None):
        info = mapa_activas.get(combo_materias_activas.get())
        if info:
            detalle.configurar(f"Docente: {info['docente']}   |   Horario: {info['horario']}")
        else:
            detalle.configurar("")

    def refrescar_materias_activas(_=None):
        periodo = caja_periodo.get().strip() or config.PERIODO_ACTUAL_DEFECTO
        activas = _obtener_materias_activas_estudiante(cedula, periodo)
        mapa_activas.clear()
        opciones = []
        for m in activas:
            etiqueta = f"{m['id_matricula']} - {m['id']} {m['nombre']} ({m['creditos']} Cr.)"
            mapa_activas[etiqueta] = m
            opciones.append(etiqueta)
        combo_materias_activas.configure(values=opciones or ["Sin asignaturas activas"])
        combo_materias_activas.set(opciones[0] if opciones else "Sin asignaturas activas")
        mostrar_detalle()

    combo_materias_activas.configure(command=mostrar_detalle)
    caja_periodo.bind("<KeyRelease>", lambda _: refrescar_materias_activas())
    refrescar_materias_activas()

    def cancelar_materia():
        sel = combo_materias_activas.get()
        info = mapa_activas.get(sel)
        if not info:
            return messagebox.showwarning("Selección vacía", "No tiene asignaturas activas para retirar.", parent=vent)

        id_matricula = info["id_matricula"]
        fila_mat = None
        for fila in db.obtener_datos("Matriculas"):
            if str(fila[0]).strip() == id_matricula:
                fila_mat = fila
                break
        if not fila_mat or str(fila_mat[1]).strip() != cedula:
            return messagebox.showerror("No encontrada", "No se encontró el registro de matrícula.", parent=vent)

        id_materia = str(fila_mat[2]).strip()

        confirmar = messagebox.askyesno(
            "Confirmar Retiro",
            f"¿Desea retirar la asignatura '{info['nombre']}' ({id_materia})?\n\n"
            f"• Se liberará 1 cupo para que otro estudiante pueda matricularla.",
            parent=vent
        )
        if not confirmar:
            return

        db.actualizar_fila(
            "Matriculas", 0, id_matricula,
            [fila_mat[0], fila_mat[1], fila_mat[2], fila_mat[3], fila_mat[4], fila_mat[5], "Cancelada"]
        )
        restituir_cupo(id_materia, 1)

        if callback_refrescar:
            callback_refrescar()

        messagebox.showinfo(
            "Materia Retirada",
            f"La asignatura '{info['nombre']}' ha sido retirada y se devolvió 1 cupo al sistema.",
            parent=vent
        )
        refrescar_materias_activas()

    agregar_botones_accion(vent, cancelar_materia, vent, texto_guardar="Retirar Asignatura")
