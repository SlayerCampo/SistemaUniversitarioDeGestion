from __future__ import annotations
# ==============================================================================
# ARCHIVO: pages/2_📊_Notas_y_Boletin.py
# PROPÓSITO: Portal de Consulta de Calificaciones y Expedición del Boletín
#            Oficial de Notas en PDF con cálculo del Promedio Ponderado
#            Semestral (PPS), diseño paso a paso y responsivo para celular.
# ==============================================================================

import html
import streamlit as st
import pandas as pd
from database import repo
from database.estilos_web import (
    configurar_pagina_ucc,
    banner_ucc,
    encabezado_paso,
    renderizar_kpis,
    tarjeta_estudiante_html,
    obtener_sesion_estudiante,
    iniciar_sesion_estudiante,
    cerrar_sesion_estudiante,
)

configurar_pagina_ucc("Notas y Boletín Oficial", "📊")

banner_ucc(
    "📊 Consulta de Calificaciones y Boletín Oficial",
    "Revise paso a paso el rendimiento académico por corte, el Promedio Ponderado Semestral (PPS) y descargue el certificado en PDF.",
)

estudiantes = repo.obtener_datos("Estudiantes")
programas_lista = repo.obtener_datos("Programas")
mapa_programas = {str(p[0]).strip(): str(p[1]) for p in programas_lista}

if not estudiantes:
    st.warning("💡 No hay estudiantes registrados. Diríjase a **⚙️ Administración** para registrar o importar el archivo Excel.")
    st.stop()

# ==============================================================================
# PASO 1: SELECCIÓN DEL ESTUDIANTE / SESIÓN ACTIVA
# ==============================================================================
sesion = obtener_sesion_estudiante()

if sesion:
    encabezado_paso(
        "PASO 1",
        f"Estudiante en Sesión: {sesion['nombre']}",
        "Ha iniciado sesión con sus credenciales institucionales. Solo puede consultar sus propias calificaciones.",
    )
    col_info_ses, col_btn_ses = st.columns([3, 1])
    with col_info_ses:
        st.success(f"🔒 Sesión activa: **{sesion['cedula']} — {sesion['nombre']}** ({sesion['programa']})")
    with col_btn_ses:
        if st.button("🚪 Cerrar Sesión", key="btn_logout_boletin", use_container_width=True):
            cerrar_sesion_estudiante()
            st.rerun()

    cedula = sesion["cedula"]
    nombre_est = sesion["nombre"]
    id_prog = sesion["id_programa"]
    nom_prog = sesion["programa"]
    semestre_est = sesion["semestre"]
else:
    encabezado_paso(
        "PASO 1",
        "Seleccione el Estudiante a Consultar (Modo Abierto / Simulador)",
        "Elija un estudiante de la lista o inicie sesión con su ID y contraseña 1234 para bloquear su portal individual.",
    )

    opciones_est = {
        f"{e[0]} — {e[1]} {e[2]} ({mapa_programas.get(str(e[6]).strip(), e[6])})": e
        for e in estudiantes
    }
    col_sel_est, col_btn_sim = st.columns([2.5, 1.5])
    with col_sel_est:
        etiqueta_est = st.selectbox("👨‍🎓 Estudiante:", list(opciones_est.keys()))
        est = opciones_est[etiqueta_est]
        cedula = str(est[0]).strip()
        nombre_est = f"{est[1]} {est[2]}"
        id_prog = str(est[6]).strip()
        nom_prog = mapa_programas.get(id_prog, id_prog)
        semestre_est = int(est[5])

    with col_btn_sim:
        st.write("")
        if st.button("🔑 Simular Ingreso (Clave: 1234)", key="btn_sim_login_bol", use_container_width=True):
            iniciar_sesion_estudiante(
                cedula=cedula,
                nombre=nombre_est,
                id_prog=id_prog,
                nom_prog=nom_prog,
                semestre=semestre_est,
            )
            st.rerun()

st.markdown(
    tarjeta_estudiante_html(
        cedula=cedula,
        nombre_completo=nombre_est,
        codigo_prog=id_prog,
        nombre_prog=nom_prog,
        semestre=semestre_est,
        periodo="2026-2",
    ),
    unsafe_allow_html=True,
)

matriculas = [
    m for m in repo.obtener_datos("Matriculas")
    if str(m[1]).strip() == cedula and (len(m) < 7 or str(m[6]).strip().lower() == "activa")
]

if not matriculas:
    st.info("ℹ️ El estudiante seleccionado no tiene asignaturas activas matriculadas en este periodo.")
    st.stop()

mapa_materias = {str(m[0]): m for m in repo.obtener_datos("Materias")}
mapa_notas = {str(n[1]): n for n in repo.obtener_datos("Notas")}

filas_boletin = []
suma_ponderada = 0.0
creditos_calificados = 0
creditos_aprobados = 0
materias_aprobadas = 0

for m in matriculas:
    id_mat = str(m[0])
    cod_curso = str(m[2])
    creditos = int(m[3])
    info_m = mapa_materias.get(cod_curso)
    nombre_m = str(info_m[1]) if info_m else cod_curso
    docente_m = str(info_m[4]) if info_m else "Por asignar"
    nota = mapa_notas.get(id_mat)

    if nota:
        n1, n2, n3 = float(nota[3]), float(nota[4]), float(nota[5])
        definitiva = float(nota[6])
        estado = str(nota[7])
        suma_ponderada += definitiva * creditos
        creditos_calificados += creditos
        if definitiva >= repo.NOTA_APROBATORIA:
            creditos_aprobados += creditos
            materias_aprobadas += 1
    else:
        n1, n2, n3, definitiva, estado = None, None, None, None, "Sin calificar"

    filas_boletin.append({
        "Código": cod_curso,
        "Asignatura": nombre_m,
        "Docente": docente_m,
        "Créditos": creditos,
        "Corte 1": f"{n1:.2f}" if n1 is not None else "—",
        "Corte 2": f"{n2:.2f}" if n2 is not None else "—",
        "Corte 3": f"{n3:.2f}" if n3 is not None else "—",
        "Definitiva": f"{definitiva:.2f}" if definitiva is not None else "—",
        "Estado": estado,
    })

pps = round(suma_ponderada / creditos_calificados, 2) if creditos_calificados > 0 else 0.0
total_cred_mat = sum(int(m[3]) for m in matriculas)

# ==============================================================================
# PASO 2: INDICADORES DE RENDIMIENTO ACADÉMICO (PPS)
# ==============================================================================
encabezado_paso(
    "PASO 2",
    "Resumen de Rendimiento y Promedio Ponderado Semestral (PPS)",
    "El PPS pondera la nota definitiva de cada asignatura por su número de créditos académicos.",
)

renderizar_kpis([
    ("Promedio (PPS)", f"{pps:.2f} / 5.00", "verde" if pps >= repo.NOTA_APROBATORIA else "ambar"),
    ("Materias Activas", str(len(matriculas)), "azul"),
    ("Materias Aprobadas", str(materias_aprobadas), "verde"),
    ("Créditos Inscritos", f"{total_cred_mat} Cr.", "celeste"),
    ("Créditos Aprobados", f"{creditos_aprobados} Cr.", "morado"),
])

# ==============================================================================
# PASO 3: DETALLE POR ASIGNATURA Y DESCARGA DE BOLETÍN OFICIAL PDF
# ==============================================================================
encabezado_paso(
    "PASO 3",
    "Detalle de Calificaciones por Corte y Certificado PDF",
    "Consulte las notas de cada corte en tarjetas adaptables a celular o descargue el boletín oficial en PDF.",
)

for fb in filas_boletin:
    chip_estado = "verde" if fb["Estado"] == "Aprobado" else ("rojo" if fb["Estado"] == "Reprobado" else "ambar")
    cls_card = "inscrita" if fb["Estado"] == "Aprobado" else ("carrito" if fb["Estado"] == "Sin calificar" else "")
    st.markdown(
        f'<div class="ucc-course-card {cls_card}">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">'
        f'<div class="ucc-course-title">{html.escape(fb["Código"])} — {html.escape(fb["Asignatura"])} ({fb["Créditos"]} Cr.)</div>'
        f'<span class="ucc-chip {chip_estado}">{html.escape(fb["Estado"])} · Definitiva: {html.escape(fb["Definitiva"])}</span>'
        f'</div>'
        f'<div class="ucc-course-meta" style="margin-top:0.25rem;">'
        f'<span>👨‍🏫 {html.escape(fb["Docente"])}</span>'
        f'<span>📝 <b>Corte 1:</b> {html.escape(fb["Corte 1"])}</span>'
        f'<span>📝 <b>Corte 2:</b> {html.escape(fb["Corte 2"])}</span>'
        f'<span>📝 <b>Corte 3:</b> {html.escape(fb["Corte 3"])}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

with st.expander("📋 Ver Tabla Resumen Consolidada"):
    st.dataframe(pd.DataFrame(filas_boletin), use_container_width=True, hide_index=True)

pdf_boletin = repo.generar_pdf_boletin_bytes(cedula)
if pdf_boletin:
    st.download_button(
        label="📥 Descargar Boletín Oficial de Calificaciones (PDF)",
        data=pdf_boletin,
        file_name=f"Reporte_Notas_{cedula}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
