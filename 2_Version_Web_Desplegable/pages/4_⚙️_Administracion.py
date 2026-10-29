from __future__ import annotations
# ==============================================================================
# ARCHIVO: pages/4_⚙️_Administracion.py
# PROPÓSITO: Portal Administrativo, ETL Excel y Analítico en Streamlit.
#            Diseño paso a paso y responsivo para celular y PC. Todos los
#            formularios cuentan con etiqueta en negrita arriba y ejemplo
#            (placeholder) dentro de cada caja de texto.
# ==============================================================================

import streamlit as st
import pandas as pd
from database import repo
from database.estilos_web import (
    configurar_pagina_ucc,
    banner_ucc,
    encabezado_paso,
    renderizar_kpis,
)

configurar_pagina_ucc("Administración y ETL", "⚙️")

banner_ucc(
    "⚙️ Panel de Administración Académica, ETL Excel y Analítica",
    "Gestione paso a paso el catálogo institucional, genere o importe el Excel de 50+ estudiantes, consulte tablas y vacíe la base de datos.",
)

facs_tot = len(repo.obtener_datos("Facultades"))
progs_tot = len(repo.obtener_datos("Programas"))
mats_tot = len(repo.obtener_datos("Materias"))
ests_tot = len(repo.obtener_datos("Estudiantes"))
matr_tot = len([m for m in repo.obtener_datos("Matriculas") if len(m) < 7 or str(m[6]).strip().lower() == "activa"])

renderizar_kpis([
    ("Facultades", str(facs_tot), "azul"),
    ("Programas", str(progs_tot), "morado"),
    ("Grupos Materia", str(mats_tot), "celeste"),
    ("Estudiantes", str(ests_tot), "verde"),
    ("Matrículas Activas", str(matr_tot), "ambar"),
])

tab_simulador, tab_fac_prog, tab_mat_est, tab_explorador, tab_stats = st.tabs([
    "📦 1. Centro ETL / 50+ Estudiantes",
    "🏛️ 2. Registrar Facultad / Programa",
    "📘 3. Registrar Asignatura / Estudiante",
    "🔍 4. Explorar Tablas BD",
    "📈 5. Analítica y Gráficos",
])

with tab_simulador:
    # ==========================================================================
    # PASO 1: GENERAR ARCHIVO EXCEL DE 50+ ESTUDIANTES
    # ==========================================================================
    encabezado_paso(
        "PASO 1",
        "Generar Archivo Excel de 50+ Estudiantes (Sin sobrescribir la BD activa)",
        "Descargue el archivo en su celular o computador para revisarlo e importarlo manualmente en el Paso 2.",
    )
    st.write(
        "El archivo incluye **5 Facultades, 8 Programas Académicos, 120 Asignaturas (240 grupos con horario sin clases de 13:00 a 14:00) "
        "y 50 Estudiantes** (encabezados por **Alejandro Campo Solarte**, **Juan Esteban Cardona Calambas** y **Diego Fernando Gómez Rivera**)."
    )
    st.download_button(
        label="📥 Generar y Guardar Excel de 50+ Estudiantes (.xlsx)",
        data=repo.generar_excel_simulacion_bytes(50),
        file_name="Universidad_50_Estudiantes_UCC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )

    # ==========================================================================
    # PASO 2: IMPORTAR ARCHIVO EXCEL MANUALMENTE
    # ==========================================================================
    encabezado_paso(
        "PASO 2",
        "Importar Archivo Excel Manualmente a la Base de Datos Activa",
        "Seleccione el archivo Excel que acaba de descargar (o cualquier plantilla compatible) y pulse Importar.",
    )
    archivo_subido = st.file_uploader("📂 Seleccione el archivo Excel (.xlsx) desde su dispositivo:", type=["xlsx"])
    if archivo_subido is not None:
        if st.button("🚀 Importar Archivo Excel Seleccionado Ahora", type="primary", use_container_width=True):
            res = repo.importar_excel_subido_web(archivo_subido.getvalue())
            ins = res["insertados"]
            st.success(
                f"🎉 ¡Archivo Excel importado exitosamente!\n\n"
                f"• Facultades: {ins.get('Facultades', 0)} | Programas: {ins.get('Programas', 0)}\n"
                f"• Grupos de Asignaturas: {ins.get('Materias', 0)} | Estudiantes: {ins.get('Estudiantes', 0)}\n"
                f"• Matrículas: {ins.get('Matriculas', 0)} | Notas: {ins.get('Notas', 0)}\n"
                f"• Duplicados omitidos: {res['duplicados']}"
            )
            st.rerun()

    # ==========================================================================
    # PASO 3: VACIAR BASE DE DATOS (DEJAR EN BLANCO)
    # ==========================================================================
    encabezado_paso(
        "PASO 3",
        "Vaciar Base de Datos y Dejar Todo en Blanco",
        "Elimina todos los registros cargados para dejar el sistema en blanco como en la primera visita.",
    )
    if st.button("🗑️ Vaciar Base de Datos (Dejar en Blanco)", use_container_width=True):
        repo.reiniciar_base_datos_vacia_web()
        st.success("✅ Base de datos vaciada por completo (0 registros). Lista para registrar desde cero o importar un Excel.")
        st.rerun()

with tab_fac_prog:
    c1, c2 = st.columns(2)

    with c1:
        encabezado_paso("REGISTRO A", "Nueva Facultad", "Complete los datos con su etiqueta superior y ejemplo interno.")
        with st.form("form_facultad", clear_on_submit=True):
            id_fac = st.text_input("Código de la Facultad:", placeholder="Ej: F01")
            nom_fac = st.text_input("Nombre de la Facultad:", placeholder="Ej: Facultad de Ingeniería")
            dec_fac = st.text_input("Nombre del Decano(a):", placeholder="Ej: Dr. Hernán Darío Gómez")
            if st.form_submit_button("💾 Guardar Facultad", type="primary", use_container_width=True):
                if not id_fac.strip() or not nom_fac.strip():
                    st.warning("Complete el código y el nombre de la facultad.")
                elif repo.buscar_fila("Facultades", 0, id_fac.strip()):
                    st.error("El código de facultad ya está registrado.")
                else:
                    repo.insertar_fila("Facultades", [id_fac.strip().upper(), nom_fac.strip(), dec_fac.strip() or "Por asignar"])
                    st.success(f"Facultad '{nom_fac.strip()}' registrada correctamente.")
                    st.rerun()

    with c2:
        encabezado_paso("REGISTRO B", "Nuevo Programa Académico", "Adscriba el nuevo programa a una Facultad existente.")
        facs = repo.obtener_datos("Facultades")
        if not facs:
            st.info("ℹ️ Registre primero al menos una Facultad en el formulario anterior.")
        else:
            ops_f = {f"{f[0]} — {f[1]}": str(f[0]) for f in facs}
            with st.form("form_programa", clear_on_submit=True):
                id_prog = st.text_input("Código del Programa Académico:", placeholder="Ej: P01")
                nom_prog = st.text_input("Nombre del Programa Académico:", placeholder="Ej: Ingeniería de Software y Sistemas")
                sem_prog = st.number_input("Duración en Semestres (1 a 14):", min_value=1, max_value=14, value=10)
                fac_sel = st.selectbox("Facultad a la que pertenece:", list(ops_f.keys()))
                if st.form_submit_button("💾 Guardar Programa Académico", type="primary", use_container_width=True):
                    if not id_prog.strip() or not nom_prog.strip():
                        st.warning("Complete el código y el nombre del programa.")
                    elif repo.buscar_fila("Programas", 0, id_prog.strip()):
                        st.error("El código de programa ya existe.")
                    else:
                        repo.insertar_fila("Programas", [id_prog.strip().upper(), nom_prog.strip(), ops_f[fac_sel], int(sem_prog)])
                        st.success(f"Programa '{nom_prog.strip()}' registrado exitosamente.")
                        st.rerun()

with tab_mat_est:
    c3, c4 = st.columns(2)

    with c3:
        encabezado_paso(
            "REGISTRO C",
            "Nueva Asignatura (Adscrita a un Programa)",
            "Sesiones de 2, 3 o 4 horas continuas sin tocar el almuerzo (13:00 a 14:00).",
        )
        progs = repo.obtener_datos("Programas")
        if not progs:
            st.info("ℹ️ Registre primero al menos un Programa Académico.")
        else:
            ops_p = {f"{p[0]} — {p[1]}": str(p[0]) for p in progs}
            id_m = st.text_input("Código de Asignatura con Grupo:", placeholder="Ej: SIS101-G1")
            nom_m = st.text_input("Nombre de la Asignatura:", placeholder="Ej: Fundamentos de Programación")
            dur_m = st.selectbox("Créditos Académicos (Duración en horas continuas):", [2, 3, 4], index=1)
            cup_m = st.number_input("Cupos Totales Disponibles:", min_value=1, max_value=100, value=35)
            doc_m = st.text_input("Nombre del Docente Titular:", placeholder="Ej: Ing. Carlos Andrés Ortiz")
            prog_m = st.selectbox("Programa Académico al que pertenece:", list(ops_p.keys()))
            dia_m = st.selectbox("Día de Clase:", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"])
            horas_validas = repo.inicios_validos(int(dur_m))
            opciones_franja = {f"{h:02d}:00 - {h + int(dur_m):02d}:00 ({dur_m}h seguidas)": h for h in horas_validas}
            franja_lbl = st.selectbox("Franja Horaria (Sin clases de 13:00 a 14:00):", list(opciones_franja.keys()))

            if st.button("💾 Guardar Asignatura", type="primary", use_container_width=True):
                if not id_m.strip() or not nom_m.strip():
                    st.warning("Complete el código y el nombre de la asignatura.")
                elif repo.buscar_fila("Materias", 0, id_m.strip()):
                    st.error("El código de asignatura/grupo ya está registrado.")
                else:
                    h_ini = opciones_franja[franja_lbl]
                    horario_str = repo.construir_horario(dia_m, h_ini, int(dur_m))
                    repo.insertar_fila(
                        "Materias",
                        [id_m.strip().upper(), nom_m.strip(), int(dur_m), int(cup_m), doc_m.strip() or "Por asignar", ops_p[prog_m], horario_str],
                    )
                    st.success(f"Asignatura '{nom_m.strip()}' creada en el programa {ops_p[prog_m]} ({horario_str}).")
                    st.rerun()

    with c4:
        encabezado_paso(
            "REGISTRO D",
            "Nuevo Estudiante",
            "Registra al estudiante y lo asocia a su Programa Académico.",
        )
        progs = repo.obtener_datos("Programas")
        if not progs:
            st.info("ℹ️ Registre primero al menos un Programa Académico.")
        else:
            ops_p = {f"{p[0]} — {p[1]}": str(p[0]) for p in progs}
            with st.form("form_estudiante", clear_on_submit=True):
                ced_e = st.text_input("Documento / Cédula del Estudiante:", placeholder="Ej: 1004")
                nom_e = st.text_input("Nombres del Estudiante:", placeholder="Ej: Laura Sofía")
                ape_e = st.text_input("Apellidos del Estudiante:", placeholder="Ej: Restrepo Henao")
                cor_e = st.text_input("Correo Institucional UCC:", placeholder="Ej: laura.restrepo4@campusucc.edu.co")
                tel_e = st.text_input("Teléfono / Celular:", placeholder="Ej: 3151234567")
                sem_e = st.number_input("Semestre Actual (1 a 14):", min_value=1, max_value=14, value=1)
                prog_e = st.selectbox("Programa Académico:", list(ops_p.keys()), key="prog_est_form")
                if st.form_submit_button("💾 Guardar Estudiante", type="primary", use_container_width=True):
                    if not ced_e.strip() or not nom_e.strip() or not ape_e.strip():
                        st.warning("Complete cédula, nombres y apellidos.")
                    elif repo.buscar_fila("Estudiantes", 0, ced_e.strip()):
                        st.error("Ya existe un estudiante registrado con ese documento.")
                    else:
                        repo.insertar_fila(
                            "Estudiantes",
                            [ced_e.strip(), nom_e.strip(), ape_e.strip(), cor_e.strip(), tel_e.strip() or "Sin teléfono", int(sem_e), ops_p[prog_e]],
                        )
                        st.success(f"Estudiante {nom_e.strip()} {ape_e.strip()} registrado con éxito.")
                        st.rerun()

with tab_explorador:
    encabezado_paso(
        "EXPLORADOR EN VIVO",
        "Consulta de Tablas de la Base de Datos",
        "Inspeccione y filtre cualquiera de las hojas del libro Excel activo.",
    )
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        tabla_sel = st.selectbox("📋 Seleccione la Tabla:", list(repo.ENCABEZADOS.keys()))
    with col_t2:
        filtro_txt = st.text_input("🔍 Filtrar registros:", placeholder="Escriba código, cédula o nombre...")

    filas_t = repo.obtener_datos(tabla_sel)
    cols_t = repo.ENCABEZADOS[tabla_sel]
    if filtro_txt.strip():
        q = filtro_txt.strip().lower()
        filas_t = [f for f in filas_t if q in " ".join(str(x) for x in f if x is not None).lower()]

    st.caption(f"Mostrando **{len(filas_t)}** registro(s) en la tabla **{tabla_sel}**.")
    if filas_t:
        df_exp = pd.DataFrame([list(f[:len(cols_t)]) for f in filas_t], columns=cols_t)
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay registros para mostrar en la tabla '{tabla_sel}'.")

with tab_stats:
    encabezado_paso(
        "ANALÍTICA INSTITUCIONAL",
        "Gráficos de Cupos y Matrículas por Programa",
        "Visualización automática adaptada al ancho de pantalla de celular o computador.",
    )
    materias = repo.obtener_datos("Materias")
    matriculas = [
        m for m in repo.obtener_datos("Matriculas")
        if len(m) < 7 or str(m[6]).strip().lower() == "activa"
    ]

    if not materias:
        st.info("ℹ️ No hay asignaturas registradas aún para graficar. Importe el Excel de 50+ estudiantes en la pestaña 1.")
    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 📊 Cupos Disponibles (Primeros 25 Grupos)")
            df_cupos = pd.DataFrame(
                [{"Grupo": f"{m[0]} ({str(m[1])[:16]})", "Cupos Disponibles": int(m[3])} for m in materias[:25]]
            ).set_index("Grupo")
            st.bar_chart(df_cupos)

        with col_g2:
            st.markdown("##### 📈 Matrículas Activas por Programa Académico")
            programas_map = {str(p[0]): str(p[1]) for p in repo.obtener_datos("Programas")}
            mat_prog_map = {str(m[0]): str(m[5]) for m in materias}
            conteo_prog = {nom: 0 for nom in programas_map.values()}
            for mat in matriculas:
                cod_p = mat_prog_map.get(str(mat[2]), "")
                nom_p = programas_map.get(cod_p, cod_p or "Otro")
                conteo_prog[nom_p] = conteo_prog.get(nom_p, 0) + 1
            if conteo_prog:
                df_insc = pd.DataFrame(
                    [{"Programa": k, "Matrículas Activas": v} for k, v in conteo_prog.items()]
                ).set_index("Programa")
                st.bar_chart(df_insc)
