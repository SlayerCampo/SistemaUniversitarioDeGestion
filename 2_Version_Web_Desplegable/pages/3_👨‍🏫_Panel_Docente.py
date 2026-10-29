from __future__ import annotations
# ==============================================================================
# ARCHIVO: pages/3_👨‍🏫_Panel_Docente.py
# PROPÓSITO: Portal Docente para Registro y Edición de Calificaciones.
#            Incluye modo paso a paso individual (igual a la app de escritorio,
#            ideal para celular) y modo planilla interactiva en lote para PC.
# ==============================================================================

import streamlit as st
import pandas as pd
from database import repo
from database.estilos_web import (
    configurar_pagina_ucc,
    banner_ucc,
    encabezado_paso,
    renderizar_kpis,
    tarjeta_materia_html,
)

configurar_pagina_ucc("Panel Docente", "👨‍🏫")

banner_ucc(
    "👨‍🏫 Panel Docente: Registro y Actualización de Notas",
    "Seleccione el Programa y el grupo ofertado para calificar por corte (0.0 a 5.0) sin duplicar registros.",
)

materias = repo.obtener_datos("Materias")
programas = repo.obtener_datos("Programas")
mapa_prog = {str(p[0]).strip(): str(p[1]) for p in programas}

if not materias:
    st.warning("💡 No existen asignaturas registradas. Diríjase a **⚙️ Administración** para crear o importar el Excel.")
    st.stop()

# ==============================================================================
# PASO 1: SELECCIONAR PROGRAMA Y GRUPO / ASIGNATURA
# ==============================================================================
encabezado_paso(
    "PASO 1",
    "Seleccione Programa Académico y Grupo a Calificar",
    "Filtre por programa para encontrar rápidamente su grupo asignado.",
)

col_p, col_m = st.columns([1.1, 1.9])
with col_p:
    ops_prog = ["Todos los Programas"] + [f"{p[0]} — {p[1]}" for p in programas]
    filtro_p = st.selectbox("🎓 Filtrar Programa:", ops_prog)
    cod_p_sel = filtro_p.split(" — ")[0].strip() if " — " in filtro_p else None

materias_filtradas = [
    m for m in materias
    if not cod_p_sel or str(m[5]).strip() == cod_p_sel
]

with col_m:
    opciones_mat = {
        f"{m[0]} — {m[1]} ({m[4]} | {m[6]})": m
        for m in materias_filtradas
    }
    etiqueta_mat = st.selectbox("📘 Seleccione el Grupo / Asignatura:", list(opciones_mat.keys()))
    info_mat = opciones_mat[etiqueta_mat]
    id_materia_sel = str(info_mat[0]).strip()

st.markdown(
    tarjeta_materia_html(
        codigo=f"{info_mat[0]} ({info_mat[5]} · {mapa_prog.get(str(info_mat[5]).strip(), info_mat[5])})",
        nombre=str(info_mat[1]),
        creditos=int(info_mat[2]),
        docente=str(info_mat[4]),
        horario=str(info_mat[6]),
        cupos=int(info_mat[3]),
        variante="inscrita",
    ),
    unsafe_allow_html=True,
)

# Buscar todos los estudiantes con matrícula activa en esta materia
matriculas_curso = [
    m for m in repo.obtener_datos("Matriculas")
    if str(m[2]).strip() == id_materia_sel
    and (len(m) < 7 or str(m[6]).strip().lower() == "activa")
]

if not matriculas_curso:
    st.info("ℹ️ Aún no hay estudiantes matriculados activamente en este grupo.")
    st.stop()

mapa_est = {str(e[0]): f"{e[1]} {e[2]}" for e in repo.obtener_datos("Estudiantes")}
mapa_notas = {str(n[1]): n for n in repo.obtener_datos("Notas")}

filas_planilla = []
aprobados = 0
for m in matriculas_curso:
    id_mat = str(m[0])
    cedula = str(m[1])
    nota_reg = mapa_notas.get(id_mat)

    n1 = float(nota_reg[3]) if nota_reg else 0.0
    n2 = float(nota_reg[4]) if nota_reg else 0.0
    n3 = float(nota_reg[5]) if nota_reg else 0.0
    def_actual = float(nota_reg[6]) if nota_reg else 0.0
    est_actual = str(nota_reg[7]) if nota_reg else "Sin calificar"
    if est_actual == "Aprobado":
        aprobados += 1

    filas_planilla.append({
        "ID_Matricula": id_mat,
        "Cédula": cedula,
        "Estudiante": mapa_est.get(cedula, cedula),
        "Corte 1": n1,
        "Corte 2": n2,
        "Corte 3": n3,
        "Definitiva": def_actual,
        "Estado": est_actual,
    })

prom_grupo = (
    round(sum(x["Definitiva"] for x in filas_planilla) / len(filas_planilla), 2)
    if filas_planilla else 0.0
)

renderizar_kpis([
    ("Inscritos en Grupo", str(len(filas_planilla)), "azul"),
    ("Cupos Restantes", str(info_mat[3]), "celeste"),
    ("Aprobados", str(aprobados), "verde"),
    ("Reprobados / Pend.", str(len(filas_planilla) - aprobados), "ambar"),
    ("Promedio del Grupo", f"{prom_grupo:.2f}", "morado"),
])

# ==============================================================================
# PASO 2: REGISTRO Y ACTUALIZACIÓN DE CALIFICACIONES
# ==============================================================================
encabezado_paso(
    "PASO 2",
    "Registrar o Actualizar Calificaciones (Cortes 1, 2 y 3)",
    "Elija entre calificación individual guiada (recomendada en celular) o edición de toda la planilla.",
)

tab_ind, tab_lote = st.tabs([
    "📱 Calificación Individual Paso a Paso (Celular / PC)",
    "📋 Planilla Completa Editable en Lote",
])

with tab_ind:
    mapa_ind = {
        f"{f['Cédula']} — {f['Estudiante']} (Actual: {f['Definitiva']:.2f} · {f['Estado']})": f
        for f in filas_planilla
    }
    est_sel_lbl = st.selectbox("👨‍🎓 Seleccione el Estudiante del Grupo:", list(mapa_ind.keys()))
    f_sel = mapa_ind[est_sel_lbl]

    c_n1, c_n2, c_n3 = st.columns(3)
    with c_n1:
        val_n1 = st.number_input(
            "📝 Corte 1 (0.0 a 5.0):",
            min_value=0.0,
            max_value=5.0,
            value=float(f_sel["Corte 1"]),
            step=0.1,
            format="%.2f",
        )
    with c_n2:
        val_n2 = st.number_input(
            "📝 Corte 2 (0.0 a 5.0):",
            min_value=0.0,
            max_value=5.0,
            value=float(f_sel["Corte 2"]),
            step=0.1,
            format="%.2f",
        )
    with c_n3:
        val_n3 = st.number_input(
            "📝 Corte 3 (0.0 a 5.0):",
            min_value=0.0,
            max_value=5.0,
            value=float(f_sel["Corte 3"]),
            step=0.1,
            format="%.2f",
        )

    def_prev = round((val_n1 + val_n2 + val_n3) / 3.0, 2)
    est_prev = "Aprobado" if def_prev >= repo.NOTA_APROBATORIA else "Reprobado"
    chip_cls = "verde" if est_prev == "Aprobado" else "rojo"

    st.markdown(
        f"""
        <div class="ucc-id-card">
            <div class="ucc-id-main">Vista Previa de Definitiva: <b>{def_prev:.2f} / 5.00</b></div>
            <span class="ucc-chip {chip_cls}">{est_prev}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("💾 Guardar Calificaciones del Estudiante", type="primary", use_container_width=True):
        definitiva, estado = repo.guardar_o_actualizar_nota(
            str(f_sel["ID_Matricula"]),
            id_materia_sel,
            round(float(val_n1), 2),
            round(float(val_n2), 2),
            round(float(val_n3), 2),
        )
        st.success(f"✅ Calificaciones guardadas para {f_sel['Estudiante']} — Definitiva: {definitiva:.2f} ({estado}).")
        st.rerun()

with tab_lote:
    df_planilla = pd.DataFrame(filas_planilla)
    st.caption("Edite directamente las celdas de **Corte 1**, **Corte 2** y **Corte 3** (entre 0.0 y 5.0) y pulse Guardar:")

    df_editado = st.data_editor(
        df_planilla,
        use_container_width=True,
        hide_index=True,
        disabled=["ID_Matricula", "Cédula", "Estudiante", "Definitiva", "Estado"],
        column_config={
            "Corte 1": st.column_config.NumberColumn("Corte 1 (0-5)", min_value=0.0, max_value=5.0, step=0.1, format="%.2f"),
            "Corte 2": st.column_config.NumberColumn("Corte 2 (0-5)", min_value=0.0, max_value=5.0, step=0.1, format="%.2f"),
            "Corte 3": st.column_config.NumberColumn("Corte 3 (0-5)", min_value=0.0, max_value=5.0, step=0.1, format="%.2f"),
        },
    )

    if st.button("💾 Guardar Toda la Planilla del Grupo", type="primary", use_container_width=True):
        actualizados = 0
        for _, fila in df_editado.iterrows():
            n1 = round(float(fila["Corte 1"]), 2)
            n2 = round(float(fila["Corte 2"]), 2)
            n3 = round(float(fila["Corte 3"]), 2)
            repo.guardar_o_actualizar_nota(str(fila["ID_Matricula"]), id_materia_sel, n1, n2, n3)
            actualizados += 1

        st.success(f"✅ Se actualizaron correctamente las calificaciones de {actualizados} estudiante(s).")
        st.rerun()
