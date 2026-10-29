from __future__ import annotations
# ==============================================================================
# ARCHIVO: app.py
# PROPÓSITO: Portal Académico Principal de la Universidad Cooperativa de
#            Colombia (Sede Cali). Diseño responsivo para celular y escritorio,
#            100% en español y con guía paso a paso.
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
    obtener_sesion_estudiante,
    cerrar_sesion_estudiante,
)

configurar_pagina_ucc("Portal Académico UCC", "🎓")

banner_ucc(
    "🏛️ Universidad Cooperativa de Colombia — Portal Académico",
    "Sistema Integral de Matrículas por Programa, Control de Cupos en Vivo, Validador de Horarios y Certificados PDF",
)

# Indicadores Clave (KPIs) en tiempo real con cuadrícula responsiva (5 en PC, 2x2+1 en celular)
facultades = repo.obtener_datos("Facultades")
programas = repo.obtener_datos("Programas")
materias = repo.obtener_datos("Materias")
estudiantes = repo.obtener_datos("Estudiantes")
matriculas_activas = [
    m for m in repo.obtener_datos("Matriculas")
    if len(m) < 7 or str(m[6]).strip().lower() == "activa"
]
notas = repo.obtener_datos("Notas")
promedio_inst = (
    round(sum(float(n[6]) for n in notas) / len(notas), 2)
    if notas else 0.0
)

renderizar_kpis([
    ("Estudiantes", str(len(estudiantes)), "azul"),
    ("Grupos Ofertados", str(len(materias)), "celeste"),
    ("Matrículas Activas", str(len(matriculas_activas)), "verde"),
    ("Programas", str(len(programas)), "morado"),
    ("Promedio Global", f"{promedio_inst:.2f} / 5.0", "ambar"),
])

# Aviso inteligente cuando se accede desde un teléfono celular
st.markdown(
    '<div class="ucc-aviso-mobile-solo">'
    '<div style="font-weight:700; color:#b45309; font-size:0.95rem;">📱 Dispositivo Móvil Detectado</div>'
    '<div style="font-size:0.85rem; color:#78350f; margin-top:0.25rem; line-height:1.4;">'
    'Ha ingresado desde un celular o tablet. El <b>Instalador ejecutable para PC (.exe)</b> está diseñado '
    'exclusivamente para computadores con sistema operativo <b>Windows</b>. Para instalar la aplicación de escritorio '
    'y crear el icono oficial en su Escritorio, por favor abra este mismo enlace desde su computador.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

# Tarjeta y botones de descarga de la aplicación para computador (Escritorio)
st.markdown(
    '<div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:12px; padding:0.95rem 1.1rem; margin-bottom:0.75rem;">'
    '<div style="font-weight:700; color:#0f172a; font-size:1.02rem;">💻 ¿Desea instalar la Versión de Escritorio en su Computador?</div>'
    '<div style="font-size:0.86rem; color:#475569; margin-top:0.2rem; line-height:1.4;">'
    'Descargue el instalador oficial para Windows. Al ejecutarlo, se abrirá el asistente profesional con opción '
    'de <b>crear automáticamente el icono de acceso directo en el Escritorio</b> con el logotipo de la UCC, '
    'sin necesidad de descomprimir archivos a mano ni tener Python instalado.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

exe_desk = repo.obtener_instalador_exe_bytes()
col_desk_desc, col_desk_gh = st.columns([1.7, 1])
with col_desk_desc:
    if exe_desk:
        st.download_button(
            label="💻 Descargar Instalador Oficial para Windows (.exe — 21 MB)",
            data=exe_desk,
            file_name="Instalador_Sistema_Universitario_UCC_Setup.exe",
            mime="application/vnd.microsoft.portable-executable",
            use_container_width=True,
            key="btn_home_descargar_exe",
        )
    else:
        zip_desk = repo.generar_zip_escritorio_bytes()
        if zip_desk:
            st.download_button(
                label="💻 Descargar Versión de Escritorio (.zip)",
                data=zip_desk,
                file_name="Sistema_Universitario_UCC_Escritorio.zip",
                mime="application/zip",
                use_container_width=True,
                key="btn_home_descargar_pc",
            )
with col_desk_gh:
    st.link_button(
        "🐙 Ver Proyecto en GitHub",
        "https://github.com/SlayerCampo/SistemaUniversitarioDeGestion",
        use_container_width=True,
    )

sesion_activa = obtener_sesion_estudiante()
if sesion_activa:
    st.info(
        f"👤 **Sesión Estudiantil Activa:** {sesion_activa['nombre']} (ID: {sesion_activa['cedula']} · {sesion_activa['programa']}). "
        f"Puede ir directamente a **🎓 Matrícula** o **📊 Notas y Boletín** para gestionar sus asignaturas personales."
    )

if not estudiantes and not materias:
    st.warning(
        "💡 **Base de datos en blanco (Primera visita):** Actualmente hay 0 registros cargados. "
        "Diríjase al módulo **⚙️ Administración** en el menú lateral para registrar datos desde cero "
        "o generar e importar el archivo Excel con los **50 estudiantes y 240 grupos**."
    )

# ==============================================================================
# PASO 1: RUTA RÁPIDA DE NAVEGACIÓN POR MÓDULOS
# ==============================================================================
encabezado_paso(
    "GUÍA PASO A PASO",
    "Módulos del Sistema Académico",
    "Seleccione cualquiera de las secciones en el menú lateral (o toque el botón ❯ arriba a la izquierda desde su celular).",
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        '<div class="ucc-course-card">'
        '<div class="ucc-course-title">🎓 1. Matrícula</div>'
        '<div class="ucc-course-meta">Flujo de 4 pasos por Programa, detector de cruces y recibo PDF.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        '<div class="ucc-course-card inscrita">'
        '<div class="ucc-course-title">📊 2. Notas y Boletín</div>'
        '<div class="ucc-course-meta">Consulta de cortes, Promedio Ponderado (PPS) y certificado PDF.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        '<div class="ucc-course-card carrito">'
        '<div class="ucc-course-title">👨‍🏫 3. Panel Docente</div>'
        '<div class="ucc-course-meta">Planilla interactiva por grupo para calificar en segundos.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        '<div class="ucc-course-card">'
        '<div class="ucc-course-title">⚙️ 4. Administración</div>'
        '<div class="ucc-course-meta">Registros desde cero, Excel de 50+ estudiantes y analítica.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ==============================================================================
# PASO 2: EXPLORADOR DE OFERTA ACADÉMICA POR PROGRAMA
# ==============================================================================
encabezado_paso(
    "CATÁLOGO EN VIVO",
    "Oferta Académica por Programa y Disponibilidad de Cupos",
    "Filtre por Programa Académico o busque por nombre de asignatura, código, docente o día de clase.",
)

if materias:
    mapa_prog = {str(p[0]): str(p[1]) for p in programas}
    opciones_filtro_prog = ["Todos los Programas Académicos"] + [
        f"{p[0]} — {p[1]}" for p in programas
    ]

    col_f1, col_f2, col_f3 = st.columns([1.4, 1.6, 1])
    with col_f1:
        prog_sel = st.selectbox("🎓 Filtrar por Programa Académico:", opciones_filtro_prog)
    with col_f2:
        busqueda = st.text_input(
            "🔍 Buscar por nombre, código, docente o día:",
            value="",
            placeholder="Ej: Programación, SIS101 o Viernes",
        )
    with col_f3:
        modo_vista = st.selectbox(
            "📱 Modo de Visualización:",
            ["Tarjetas Responsivas (Ideal Celular/PC)", "Tabla Completa"],
        )

    cod_prog_filtro = prog_sel.split(" — ")[0].strip() if " — " in prog_sel else None

    filtradas = []
    for m in materias:
        cod_p = str(m[5]).strip()
        nom_p = mapa_prog.get(cod_p, cod_p)
        if cod_prog_filtro and cod_p != cod_prog_filtro:
            continue
        texto_busqueda = f"{m[0]} {m[1]} {m[4]} {cod_p} {nom_p} {m[6]}".lower()
        if busqueda.strip().lower() in texto_busqueda:
            filtradas.append((m, nom_p))

    st.caption(f"Mostrando **{len(filtradas)}** grupo(s) ofertados (sin clases en hora de almuerzo 13:00 a 14:00).")

    if not filtradas:
        st.info("No se encontraron asignaturas que coincidan con el filtro seleccionado.")
    elif "Tarjetas" in modo_vista:
        # Mostrar primeras 30 tarjetas para mantener fluidez en celulares
        for m, nom_p in filtradas[:30]:
            st.markdown(
                tarjeta_materia_html(
                    codigo=f"{m[0]} ({m[5]} · {nom_p})",
                    nombre=str(m[1]),
                    creditos=int(m[2]),
                    docente=str(m[4]),
                    horario=str(m[6]),
                    cupos=int(m[3]),
                    variante="inscrita" if int(m[3]) > 0 else "carrito",
                ),
                unsafe_allow_html=True,
            )
        if len(filtradas) > 30:
            st.caption(f"Mostrando los primeros 30 de {len(filtradas)} grupos. Use el filtro de Programa o el buscador para acotar resultados.")
    else:
        filas_cat = [
            {
                "Código / Grupo": m[0],
                "Asignatura": m[1],
                "Créditos (Horas)": int(m[2]),
                "Cupos": int(m[3]),
                "Docente Titular": m[4],
                "Programa Académico": f"{m[5]} - {nom_p}",
                "Horario": m[6],
            }
            for m, nom_p in filtradas
        ]
        st.dataframe(pd.DataFrame(filas_cat), use_container_width=True, hide_index=True)
