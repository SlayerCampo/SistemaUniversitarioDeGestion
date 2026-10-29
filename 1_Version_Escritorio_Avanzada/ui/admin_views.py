from __future__ import annotations
# ==============================================================================
# ARCHIVO: ui/admin_views.py
# PROPÓSITO: Ventanas de administración académica:
#            • Registro de Facultades, Programas, Asignaturas (adscritas a un
#              PROGRAMA, con constructor de horario que respeta la jornada y la
#              hora de almuerzo) y Estudiantes con campos organizados (etiqueta
#              arriba y ejemplo interior).
#            • Explorador visual de tablas con búsqueda en vivo, detalle de la
#              fila seleccionada con texto deslizable y eliminación controlada.
#            • Panel de sincronización con PostgreSQL.
# ==============================================================================

from tkinter import messagebox, ttk
import customtkinter as ctk
import config
import data.db_excel as db
import data.db_postgres as db_pg
from core.seguridad import encriptar_password
from core.validador_horarios import (
    DIAS_SEMANA_ORDEN,
    inicios_validos,
    construir_horario,
    validar_horario_institucional,
)
from ui import (
    crear_ventana_modal,
    crear_campo_formulario,
    crear_combo_formulario,
    estilo_entrada,
    estilo_combobox,
    agregar_botones_accion,
    crear_cuerpo_con_barra_fija,
)
from ui.componentes import TextoDeslizable


def abrir_ventana_facultad(callback_refrescar=None):
    """Formulario modal para registrar una nueva Facultad en la universidad."""
    vent = crear_ventana_modal("Registrar Facultad", 440, 440)
    ctk.CTkLabel(
        vent,
        text="Registro de Facultad",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(18, 6))

    c_id = crear_campo_formulario(vent, "Código de la Facultad:", placeholder="Ej: F01", ancho=350, padx=45)
    c_nom = crear_campo_formulario(vent, "Nombre de la Facultad:", placeholder="Ej: Facultad de Ingeniería", ancho=350, padx=45)
    c_dec = crear_campo_formulario(vent, "Nombre del Decano(a):", placeholder="Ej: Dr. Hernán Darío Gómez", ancho=350, padx=45)

    def guardar():
        id_fac = c_id.get().strip().upper()
        nom_fac = c_nom.get().strip()
        decano = c_dec.get().strip() or "Por asignar"

        if not id_fac or not nom_fac:
            return messagebox.showwarning("Campos obligatorios", "Complete el código y nombre de la facultad.", parent=vent)

        libro = db.cargar_libro()
        if db.buscar_fila(libro["Facultades"], 0, id_fac):
            libro.close()
            return messagebox.showerror("Duplicado", f"La facultad '{id_fac}' ya está registrada.", parent=vent)

        db.guardar_datos(libro["Facultades"], [id_fac, nom_fac, decano])
        libro.close()
        if callback_refrescar:
            callback_refrescar()
        messagebox.showinfo("Facultad Registrada", f"Se registró la facultad '{nom_fac}' correctamente.", parent=vent)
        vent.destroy()

    agregar_botones_accion(vent, guardar, vent)


def abrir_ventana_programa(callback_refrescar=None):
    """Formulario modal para registrar un Programa Académico adscrito a una Facultad."""
    opciones_fac = db.obtener_opciones("Facultades", 0, 1)
    if not opciones_fac:
        return messagebox.showwarning("Requisito previo", "Registre primero al menos una Facultad.")

    vent = crear_ventana_modal("Registrar Programa Académico", 460, 520)
    ctk.CTkLabel(
        vent,
        text="Registro de Programa Académico",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(18, 6))

    c_id = crear_campo_formulario(vent, "Código del Programa:", placeholder="Ej: P01", ancho=360, padx=50)
    c_nom = crear_campo_formulario(vent, "Nombre del Programa:", placeholder="Ej: Ingeniería de Software y Sistemas", ancho=360, padx=50)
    c_sem = crear_campo_formulario(vent, "Duración en Semestres:", placeholder="Ej: 10", ancho=360, padx=50, valor_inicial="10")
    combo_fac = crear_combo_formulario(vent, "Facultad a la que pertenece:", opciones_fac, ancho=360, padx=50)

    def guardar():
        id_prog = c_id.get().strip().upper()
        nom_prog = c_nom.get().strip()
        sem_txt = c_sem.get().strip() or "10"

        if not id_prog or not nom_prog:
            return messagebox.showwarning("Campos incompletos", "Ingrese el código y nombre del programa.", parent=vent)

        try:
            semestres = int(sem_txt)
            if not (1 <= semestres <= 14):
                raise ValueError
        except ValueError:
            return messagebox.showerror("Dato inválido", "La duración en semestres debe ser un entero entre 1 y 14.", parent=vent)

        libro = db.cargar_libro()
        if db.buscar_fila(libro["Programas"], 0, id_prog):
            libro.close()
            return messagebox.showerror("Duplicado", f"El programa '{id_prog}' ya existe.", parent=vent)

        id_facultad = db.extraer_id(combo_fac.get())
        db.guardar_datos(libro["Programas"], [id_prog, nom_prog, id_facultad, semestres])
        libro.close()
        if callback_refrescar:
            callback_refrescar()
        messagebox.showinfo("Programa Registrado", f"Programa '{nom_prog}' guardado con éxito.", parent=vent)
        vent.destroy()

    agregar_botones_accion(vent, guardar, vent)


def abrir_ventana_materia(callback_refrescar=None):
    """
    Formulario modal para registrar una Asignatura (grupo con horario) adscrita a
    un PROGRAMA ACADÉMICO. Incluye un constructor de horario que solo ofrece
    horas de inicio válidas: dentro de la jornada (06:00 a 22:00) y sin invadir
    la hora de almuerzo (13:00 a 14:00), con sesiones de 2, 3 o 4 horas seguidas.
    """
    opciones_prog = db.obtener_opciones("Programas", 0, 1)
    if not opciones_prog:
        return messagebox.showwarning("Requisito previo", "Registre primero al menos un Programa Académico.")

    vent = crear_ventana_modal("Registrar Asignatura / Materia", 500, 680, permitir_redimensionar=True)
    cuerpo = crear_cuerpo_con_barra_fija(vent, lambda: guardar(), "Guardar Asignatura")

    ctk.CTkLabel(
        cuerpo,
        text="Registro de Asignatura",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(12, 6))

    c_id = crear_campo_formulario(cuerpo, "Código con Grupo:", placeholder="Ej: SIS101-G1", ancho=390, padx=45)
    c_nom = crear_campo_formulario(cuerpo, "Nombre de la Asignatura:", placeholder="Ej: Fundamentos de Programación", ancho=390, padx=45)
    c_cred = crear_campo_formulario(cuerpo, "Créditos Académicos (Horas de clase):", placeholder="Ej: 3", ancho=390, padx=45, valor_inicial="3")
    c_cupos = crear_campo_formulario(cuerpo, "Cupos Totales Disponibles:", placeholder="Ej: 35", ancho=390, padx=45, valor_inicial=str(config.CUPOS_POR_DEFECTO))
    c_doc = crear_campo_formulario(cuerpo, "Nombre del Docente Titular:", placeholder="Ej: Ing. Carlos Andrés Ortiz", ancho=390, padx=45)
    combo_prog = crear_combo_formulario(cuerpo, "Programa Académico al que pertenece:", opciones_prog, ancho=390, padx=45)

    # ---------------- Constructor asistido de horario ----------------
    ctk.CTkLabel(
        cuerpo,
        text="Constructor de Horario (sin clases entre 13:00 y 14:00):",
        font=(config.FUENTE_FORMULARIOS, 11, "bold"),
        text_color="#334155"
    ).pack(anchor="w", padx=45, pady=(10, 2))

    frame_hor1 = ctk.CTkFrame(cuerpo, fg_color="transparent")
    frame_hor1.pack(pady=2, padx=45, fill="x")
    combo_dia = ctk.CTkComboBox(frame_hor1, **estilo_combobox(DIAS_SEMANA_ORDEN, ancho=190))
    combo_dia.pack(side="left", padx=(0, 6))
    combo_duracion = ctk.CTkComboBox(
        frame_hor1,
        **estilo_combobox([f"{d} horas" for d in config.DURACIONES_PERMITIDAS], ancho=190)
    )
    combo_duracion.set("3 horas")
    combo_duracion.pack(side="left")

    frame_hor2 = ctk.CTkFrame(cuerpo, fg_color="transparent")
    frame_hor2.pack(pady=4, padx=45, fill="x")
    combo_inicio = ctk.CTkComboBox(frame_hor2, **estilo_combobox(["08:00"], ancho=190))
    combo_inicio.pack(side="left", padx=(0, 6))

    def duracion_actual() -> int:
        try:
            return int(combo_duracion.get().split()[0])
        except (ValueError, IndexError):
            return 3

    def actualizar_inicios(_=None):
        """Recalcula las horas de inicio válidas según la duración elegida."""
        inicios = [f"{h:02d}:00" for h in inicios_validos(duracion_actual())]
        combo_inicio.configure(values=inicios)
        if combo_inicio.get() not in inicios:
            combo_inicio.set(inicios[0] if inicios else "")

    combo_duracion.configure(command=actualizar_inicios)

    c_horario = crear_campo_formulario(cuerpo, "Horario Institucional Resultante:", placeholder="Ej: Viernes 09:00 - 12:00", ancho=390, padx=45)

    def aplicar_franja():
        try:
            hora = int(combo_inicio.get().split(":")[0])
        except (ValueError, IndexError):
            return messagebox.showwarning("Hora no válida", "Elija una hora de inicio.", parent=vent)
        c_horario.delete(0, "end")
        c_horario.insert(0, construir_horario(combo_dia.get(), hora, duracion_actual()))

    ctk.CTkButton(
        frame_hor2,
        text="Usar esta franja",
        width=190,
        height=38,
        fg_color=config.COLOR_AZUL_UCC,
        hover_color=config.COLOR_AZUL_OSCURO,
        command=aplicar_franja
    ).pack(side="left")

    actualizar_inicios()
    aplicar_franja()

    def guardar():
        id_mat = c_id.get().strip().upper()
        nom_mat = c_nom.get().strip()
        cred_txt = c_cred.get().strip()
        cupos_txt = c_cupos.get().strip() or str(config.CUPOS_POR_DEFECTO)
        docente = c_doc.get().strip() or "Docente por asignar"
        horario = c_horario.get().strip()

        if not id_mat or not nom_mat or not cred_txt or not horario:
            return messagebox.showwarning("Campos obligatorios", "Complete código, nombre, créditos y horario.", parent=vent)

        try:
            creditos = int(cred_txt)
            cupos = int(cupos_txt)
            if creditos <= 0 or cupos < 0:
                raise ValueError
        except ValueError:
            return messagebox.showerror("Valores numéricos inválidos", "Créditos y cupos deben ser números enteros positivos.", parent=vent)

        valido, motivo = validar_horario_institucional(horario)
        if not valido:
            return messagebox.showwarning("Horario no permitido", motivo, parent=vent)

        libro = db.cargar_libro()
        if db.buscar_fila(libro["Materias"], 0, id_mat):
            libro.close()
            return messagebox.showerror("Código duplicado", f"La asignatura '{id_mat}' ya está registrada.", parent=vent)

        id_programa = db.extraer_id(combo_prog.get())
        db.guardar_datos(libro["Materias"], [id_mat, nom_mat, creditos, cupos, docente, id_programa, horario])
        libro.close()
        if callback_refrescar:
            callback_refrescar()
        messagebox.showinfo("Asignatura Registrada", f"Asignatura '{nom_mat}' creada exitosamente.", parent=vent)
        vent.destroy()


def abrir_ventana_estudiante(callback_refrescar=None):
    """Formulario modal para registrar un Estudiante y crear su acceso automático."""
    opciones_prog = db.obtener_opciones("Programas", 0, 1)
    if not opciones_prog:
        return messagebox.showwarning("Requisito previo", "Registre primero al menos un Programa Académico.")

    vent = crear_ventana_modal("Registrar Estudiante", 480, 680, permitir_redimensionar=True)
    cuerpo = crear_cuerpo_con_barra_fija(vent, lambda: guardar(), "Guardar Estudiante")

    ctk.CTkLabel(
        cuerpo,
        text="Registro de Estudiante",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(12, 6))

    c_ced = crear_campo_formulario(cuerpo, "Documento / Cédula del Estudiante:", placeholder="Ej: 1004", ancho=370, padx=45)
    c_nom = crear_campo_formulario(cuerpo, "Nombres del Estudiante:", placeholder="Ej: Laura Sofía", ancho=370, padx=45)
    c_ape = crear_campo_formulario(cuerpo, "Apellidos del Estudiante:", placeholder="Ej: Restrepo Henao", ancho=370, padx=45)
    c_cor = crear_campo_formulario(cuerpo, "Correo Institucional (@campusucc.edu.co):", placeholder="Ej: laura.restrepo4@campusucc.edu.co", ancho=370, padx=45)
    c_tel = crear_campo_formulario(cuerpo, "Teléfono / Celular:", placeholder="Ej: 3151234567", ancho=370, padx=45)
    c_sem = crear_campo_formulario(cuerpo, "Semestre Actual (1 a 12):", placeholder="Ej: 1", ancho=370, padx=45, valor_inicial="1")
    combo_prog = crear_combo_formulario(cuerpo, "Programa Académico:", opciones_prog, ancho=370, padx=45)

    def guardar():
        ced = c_ced.get().strip()
        nom = c_nom.get().strip()
        ape = c_ape.get().strip()
        cor = c_cor.get().strip()
        tel = c_tel.get().strip() or "Sin teléfono"
        sem_txt = c_sem.get().strip()

        if not ced or not nom or not ape or not cor or not sem_txt:
            return messagebox.showwarning("Campos obligatorios", "Complete todos los datos del estudiante.", parent=vent)

        try:
            semestre = int(sem_txt)
            if not (1 <= semestre <= 14):
                raise ValueError
        except ValueError:
            return messagebox.showerror("Semestre inválido", "El semestre debe ser un número entero entre 1 y 14.", parent=vent)

        libro = db.cargar_libro()
        if db.buscar_fila(libro["Estudiantes"], 0, ced):
            libro.close()
            return messagebox.showerror("Duplicado", f"Ya existe un estudiante con documento '{ced}'.", parent=vent)

        id_prog = db.extraer_id(combo_prog.get())
        db.guardar_datos(libro["Estudiantes"], [ced, nom, ape, cor, tel, semestre, id_prog])
        # Crea la cuenta de acceso del estudiante (usuario = cédula, clave inicial 1234)
        if "Usuarios" in libro.sheetnames and not db.buscar_fila(libro["Usuarios"], 0, ced):
            db.guardar_datos(libro["Usuarios"], [ced, encriptar_password("1234"), "Estudiante", f"{nom} {ape}", ced])
        libro.close()
        if callback_refrescar:
            callback_refrescar()
        messagebox.showinfo(
            "Estudiante Registrado",
            f"Estudiante {nom} {ape} guardado con éxito.\n"
            f"Puede iniciar sesión con su cédula ({ced}) y clave '1234'.",
            parent=vent
        )
        vent.destroy()


def abrir_ventana_explorador_bd(
    callback_refrescar=None,
    tablas: list[str] | None = None,
    permitir_eliminar: bool = True,
    id_programa_filtro: str | None = None,
):
    """
    Explorador interactivo de la base de datos.
    - `tablas`: hojas que el usuario puede consultar (por defecto todas las académicas).
    - `permitir_eliminar`: habilita o no el botón de eliminación (solo Administrador).
    - `id_programa_filtro`: si se indica, la tabla 'Materias' solo muestra las
      asignaturas de ese programa (usado en la sesión de un estudiante).
    Los textos largos se consultan en el panel de detalle inferior, que se desliza
    suavemente al pasar el mouse (sin barras de desplazamiento horizontales).
    """
    tablas_disponibles = tablas or ["Estudiantes", "Materias", "Matriculas", "Notas", "Programas", "Facultades"]

    vent = crear_ventana_modal("Explorador y Visor de Base de Datos en Vivo", 880, 600, permitir_redimensionar=True)

    ctk.CTkLabel(
        vent,
        text="Explorador Interactivo de Tablas de la Universidad",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(14, 4))

    # Barra superior de selección de tabla y filtro
    frame_top = ctk.CTkFrame(vent, fg_color="#F8FAFC", corner_radius=12)
    frame_top.pack(padx=20, pady=6, fill="x")

    ctk.CTkLabel(
        frame_top, text="Tabla:", font=(config.FUENTE_FORMULARIOS, 12, "bold"), text_color="#1E293B"
    ).pack(side="left", padx=(14, 6), pady=10)

    combo_tabla = ctk.CTkComboBox(
        frame_top,
        values=tablas_disponibles,
        width=165,
        height=34,
        state="readonly",
        font=(config.FUENTE_FORMULARIOS, 12)
    )
    combo_tabla.set(tablas_disponibles[0])
    combo_tabla.pack(side="left", padx=4, pady=10)

    ctk.CTkLabel(
        frame_top, text="Buscar:", font=(config.FUENTE_FORMULARIOS, 12, "bold"), text_color="#1E293B"
    ).pack(side="left", padx=(14, 6), pady=10)

    entrada_filtro = ctk.CTkEntry(
        frame_top,
        placeholder_text="Escriba nombre, código o cédula...",
        width=260,
        height=34,
        font=(config.FUENTE_FORMULARIOS, 12)
    )
    entrada_filtro.pack(side="left", padx=4, pady=10)

    lbl_conteo = ctk.CTkLabel(
        frame_top, text="0 registros", font=(config.FUENTE_FORMULARIOS, 12, "bold"), text_color=config.COLOR_AZUL_UCC
    )
    lbl_conteo.pack(side="right", padx=16, pady=10)

    # Panel de botones inferior (se empaqueta primero para quedar siempre visible)
    frame_inf = ctk.CTkFrame(vent, fg_color="transparent")
    frame_inf.pack(side="bottom", padx=20, pady=10, fill="x")

    # Panel de detalle de la fila seleccionada (texto deslizable)
    frame_detalle = ctk.CTkFrame(vent, fg_color="#EFF6FF", corner_radius=10)
    frame_detalle.pack(side="bottom", padx=20, pady=(0, 4), fill="x")
    ctk.CTkLabel(
        frame_detalle, text="Detalle del registro seleccionado:",
        font=(config.FUENTE_FORMULARIOS, 11, "bold"), text_color=config.COLOR_AZUL_UCC
    ).pack(anchor="w", padx=10, pady=(6, 0))
    detalle_fila = TextoDeslizable(
        frame_detalle, texto="Seleccione una fila de la tabla para ver todos sus datos.",
        fuente=(config.FUENTE_FORMULARIOS, 11), color_texto="#334155", fondo="#EFF6FF"
    )
    detalle_fila.pack(fill="x", padx=10, pady=(0, 8))

    # Contenedor del Treeview con barra vertical moderna
    frame_tabla = ctk.CTkFrame(vent, fg_color="white", corner_radius=10)
    frame_tabla.pack(padx=20, pady=6, fill="both", expand=True)

    estilo_tv = ttk.Style()
    estilo_tv.theme_use("clam")
    estilo_tv.configure(
        "UCC.Treeview",
        background="white",
        foreground="#1E293B",
        rowheight=28,
        fieldbackground="white",
        font=("Segoe UI", 10)
    )
    estilo_tv.configure(
        "UCC.Treeview.Heading",
        background=config.COLOR_AZUL_UCC,
        foreground="white",
        font=("Segoe UI", 10, "bold")
    )

    scroll_y = ctk.CTkScrollbar(frame_tabla, orientation="vertical")
    tree = ttk.Treeview(
        frame_tabla,
        style="UCC.Treeview",
        yscrollcommand=scroll_y.set,
        selectmode="browse"
    )
    scroll_y.configure(command=tree.yview)
    scroll_y.pack(side="right", fill="y", padx=(0, 2), pady=4)
    tree.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)

    columnas_actuales = []

    def filas_de_tabla(nombre_hoja: str) -> list[tuple]:
        filas = db.obtener_datos(nombre_hoja)
        if nombre_hoja == "Materias" and id_programa_filtro:
            filas = [f for f in filas if len(f) > 5 and str(f[5]).strip() == str(id_programa_filtro).strip()]
        return filas

    def cargar_tabla(*_):
        nombre_hoja = combo_tabla.get()
        filtro = entrada_filtro.get().strip().lower()
        columnas = config.ENCABEZADOS_BD.get(nombre_hoja, [])
        columnas_actuales[:] = columnas

        tree.delete(*tree.get_children())
        tree["columns"] = columnas
        tree["show"] = "headings"

        filas = filas_de_tabla(nombre_hoja)
        visibles = []
        for f in filas:
            valores = [str(x) if x is not None else "" for x in f[:len(columnas)]]
            if filtro and filtro not in " ".join(valores).lower():
                continue
            visibles.append(valores)

        pesos = []
        for idx, col in enumerate(columnas):
            largo = max([len(col)] + [len(v[idx]) for v in visibles[:80] if idx < len(v)])
            pesos.append(max(6, min(largo, 34)))
        total_pesos = sum(pesos) or 1
        ancho_total = 800
        for idx, col in enumerate(columnas):
            tree.heading(col, text=col)
            tree.column(col, width=max(60, int(ancho_total * pesos[idx] / total_pesos)),
                        minwidth=50, stretch=True, anchor="center")

        for valores in visibles:
            tree.insert("", "end", values=valores)

        lbl_conteo.configure(text=f"{len(visibles)} registro(s)")
        detalle_fila.configurar("Seleccione una fila de la tabla para ver todos sus datos.")

    def al_seleccionar_fila(_=None):
        sel = tree.selection()
        if not sel:
            return
        valores = tree.item(sel[0], "values")
        texto = "   ·   ".join(f"{col}: {val}" for col, val in zip(columnas_actuales, valores))
        detalle_fila.configurar(texto)

    tree.bind("<<TreeviewSelect>>", al_seleccionar_fila)
    combo_tabla.configure(command=cargar_tabla)
    entrada_filtro.bind("<KeyRelease>", cargar_tabla)

    def eliminar_seleccion():
        sel = tree.selection()
        if not sel:
            return messagebox.showwarning("Sin selección", "Seleccione una fila de la tabla para eliminarla.", parent=vent)
        valores = tree.item(sel[0], "values")
        if not valores:
            return
        id_llave = valores[0]
        nombre_hoja = combo_tabla.get()
        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Desea eliminar el registro '{id_llave}' de la tabla '{nombre_hoja}'?\n\n"
            f"Esta acción no restituye cupos ni elimina datos relacionados.",
            parent=vent
        )
        if confirmar:
            if db.eliminar_fila(nombre_hoja, 0, id_llave):
                cargar_tabla()
                if callback_refrescar:
                    callback_refrescar()
                messagebox.showinfo("Eliminado", f"Registro '{id_llave}' eliminado correctamente.", parent=vent)

    ctk.CTkButton(
        frame_inf,
        text="🔄 Actualizar Vista",
        command=cargar_tabla,
        width=160,
        height=36,
        fg_color=config.COLOR_CELESTE_UCC,
        hover_color=config.COLOR_CELESTE_HOVER
    ).pack(side="left", padx=6)

    if permitir_eliminar:
        ctk.CTkButton(
            frame_inf,
            text="🗑️ Eliminar Fila Seleccionada",
            command=eliminar_seleccion,
            width=220,
            height=36,
            fg_color=config.COLOR_ROJO_ERROR,
            hover_color=config.COLOR_ROJO_HOVER
        ).pack(side="left", padx=6)

    ctk.CTkButton(
        frame_inf,
        text="Cerrar",
        command=vent.destroy,
        width=130,
        height=36,
        fg_color="#E2E8F0",
        text_color="#1E293B"
    ).pack(side="right", padx=6)

    cargar_tabla()


def abrir_ventana_postgres():
    """Ventana modal para verificar y sincronizar la base de datos Excel con PostgreSQL."""
    vent = crear_ventana_modal("Conexión y Sincronización PostgreSQL", 500, 440)
    ctk.CTkLabel(
        vent,
        text="Motor Relacional PostgreSQL (psycopg)",
        font=(config.FUENTE_FORMULARIOS, 18, "bold"),
        text_color=config.COLOR_AZUL_UCC
    ).pack(pady=(18, 6))

    info = (
        "Este módulo implementa la arquitectura híbrida vista en clase:\n"
        "• Crea automáticamente las tablas desde 'schema_universidad.sql'.\n"
        "• Sincroniza Facultades, Programas, Materias, Estudiantes,\n"
        "  Matrículas y Notas desde el Excel hacia PostgreSQL.\n\n"
        "Configuración por defecto (ver config.py):\n"
        f"Host: {config.PG_HOST} | Puerto: {config.PG_PORT} | BD: {config.PG_DATABASE}"
    )
    ctk.CTkLabel(
        vent,
        text=info,
        font=(config.FUENTE_FORMULARIOS, 11),
        text_color="#475569",
        justify="left"
    ).pack(padx=30, pady=10)

    lbl_estado = ctk.CTkLabel(
        vent,
        text="Estado: Esperando prueba de conexión...",
        font=(config.FUENTE_FORMULARIOS, 11, "bold"),
        text_color="gray"
    )
    lbl_estado.pack(pady=6)

    def probar_conexion():
        lbl_estado.configure(text="Probando conexión con PostgreSQL...", text_color=config.COLOR_AZUL_UCC)
        vent.update()
        ok, msg = db_pg.probar_conexion()
        color = config.COLOR_VERDE_EXITO if ok else config.COLOR_ROJO_ERROR
        lbl_estado.configure(text=f"Resultado: {msg}", text_color=color)

    def ejecutar_sincronizacion():
        lbl_estado.configure(text="Sincronizando todas las tablas hacia PostgreSQL...", text_color=config.COLOR_AZUL_UCC)
        vent.update()
        ok, msg = db_pg.sincronizar_desde_excel()
        color = config.COLOR_VERDE_EXITO if ok else config.COLOR_ROJO_ERROR
        lbl_estado.configure(text=f"Resultado: {msg}", text_color=color)
        if ok:
            messagebox.showinfo("Sincronización Exitosa", msg, parent=vent)
        else:
            messagebox.showerror("Error de Sincronización", msg, parent=vent)

    frame_btns = ctk.CTkFrame(vent, fg_color="transparent")
    frame_btns.pack(pady=16)

    ctk.CTkButton(
        frame_btns,
        text="🔌 Probar Conexión",
        command=probar_conexion,
        width=170,
        height=38,
        corner_radius=16,
        fg_color=config.COLOR_CELESTE_UCC,
        hover_color=config.COLOR_CELESTE_HOVER
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        frame_btns,
        text="🚀 Sincronizar Ahora",
        command=ejecutar_sincronizacion,
        width=170,
        height=38,
        corner_radius=16,
        fg_color=config.COLOR_AZUL_UCC,
        hover_color=config.COLOR_AZUL_OSCURO
    ).pack(side="left", padx=8)
