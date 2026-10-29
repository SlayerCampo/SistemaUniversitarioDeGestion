from __future__ import annotations
# ==============================================================================
# ARCHIVO: database/estilos_web.py
# PROPÓSITO: Motor de diseño responsivo (Escritorio + Celular), componentes
#            visuales paso a paso y eliminación total de elementos en inglés
#            de Streamlit (botón Deploy, menú de tres puntos y textos nativos).
# ==============================================================================

import html
import streamlit as st
from database import repo


CSS_INSTITUCIONAL_UCC = """
<style>
    /* 1. OCULTAR BOTÓN DEPLOY, MENÚ DE 3 PUNTOS Y ELEMENTOS EN INGLÉS DE STREAMLIT */
    .stDeployButton,
    [data-testid="stAppDeployButton"],
    [data-testid="stToolbarActions"],
    [data-testid="stStatusWidget"],
    [data-testid="stMainMenu"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* Mantener visible únicamente el botón para abrir la barra lateral en celulares */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.5rem !important;
    }

    /* Traducir visualmente el área de carga de archivos (File Uploader) al español */
    [data-testid="stFileUploaderDropzoneInstructions"] div span {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] div::before {
        content: "Arrastre y suelte su archivo Excel aquí";
        font-weight: 600;
        color: #1E293B;
        font-size: 0.92rem;
        display: block;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        display: none !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "Formato permitido: .XLSX (Máximo 200 MB)";
        font-size: 0.78rem;
        color: #64748B;
        display: block;
        margin-top: 2px;
    }
    [data-testid="stFileUploaderDropzone"] button {
        font-size: 0 !important;
    }
    [data-testid="stFileUploaderDropzone"] button::after {
        content: "Examinar archivos";
        font-size: 0.88rem !important;
        font-weight: 600;
    }

    /* 2. CONTENEDOR PRINCIPAL Y ESPACIADO EQUILIBRADO */
    .block-container {
        padding-top: 1.4rem !important;
        padding-bottom: 2.8rem !important;
        max-width: 1180px !important;
    }

    /* 3. BANNER INSTITUCIONAL UCC */
    .ucc-banner {
        background: linear-gradient(135deg, #1F6AA5 0%, #3B1C7A 100%);
        padding: 1.35rem 1.75rem;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 1.25rem;
        box-shadow: 0 6px 20px rgba(31, 106, 165, 0.18);
        border-left: 6px solid #36B5C6;
    }
    .ucc-banner h1 {
        color: #FFFFFF !important;
        margin: 0 !important;
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        line-height: 1.25 !important;
    }
    .ucc-banner p {
        color: #E0F2FE !important;
        margin: 0.35rem 0 0 0 !important;
        font-size: 0.94rem !important;
        line-height: 1.4 !important;
    }

    /* 4. REJILLA RESPONSIVA DE INDICADORES (KPIs) */
    .ucc-kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }
    .ucc-kpi-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        border: 1px solid #E2E8F0;
        border-top: 4px solid #1F6AA5;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        text-align: center;
    }
    .ucc-kpi-card.celeste { border-top-color: #36B5C6; }
    .ucc-kpi-card.verde   { border-top-color: #2E8B57; }
    .ucc-kpi-card.morado  { border-top-color: #3B1C7A; }
    .ucc-kpi-card.ambar   { border-top-color: #F0AD4E; }

    .ucc-kpi-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 0.25rem;
    }
    .ucc-kpi-value {
        font-size: 1.45rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.15;
    }

    /* 5. CABECERAS DE PASO A PASO (ESTILO APP DE ESCRITORIO) */
    .ucc-step-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        background: #FFFFFF;
        border: 1px solid #DBEAFE;
        border-left: 5px solid #1F6AA5;
        padding: 0.75rem 1.1rem;
        border-radius: 12px;
        margin-top: 0.85rem;
        margin-bottom: 0.65rem;
        box-shadow: 0 2px 6px rgba(31, 106, 165, 0.06);
    }
    .ucc-step-badge {
        background: #1F6AA5;
        color: #FFFFFF;
        font-weight: 800;
        font-size: 0.82rem;
        padding: 0.28rem 0.68rem;
        border-radius: 999px;
        white-space: nowrap;
        letter-spacing: 0.03em;
    }
    .ucc-step-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #1E3A8A;
        margin: 0;
    }
    .ucc-step-sub {
        font-size: 0.82rem;
        color: #64748B;
        margin: 0;
    }

    /* 6. TARJETA TIPO CARNÉ ESTUDIANTIL Y TARJETAS DE ASIGNATURAS */
    .ucc-id-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 100%);
        border: 1px solid #BFDBFE;
        border-radius: 14px;
        padding: 0.9rem 1.15rem;
        margin-bottom: 0.75rem;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 0.65rem;
    }
    .ucc-id-main {
        font-size: 1rem;
        font-weight: 700;
        color: #1E3A8A;
    }
    .ucc-id-sub {
        font-size: 0.86rem;
        color: #475569;
        margin-top: 0.15rem;
    }

    .ucc-course-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #36B5C6;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.55rem;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
    }
    .ucc-course-card.inscrita {
        border-left-color: #2E8B57;
        background: #F8FAFC;
    }
    .ucc-course-card.carrito {
        border-left-color: #F0AD4E;
        background: #FFFBEB;
    }
    .ucc-course-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .ucc-course-meta {
        font-size: 0.82rem;
        color: #475569;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem 1rem;
    }

    /* 7. CHIPS / INSIGNIAS */
    .ucc-chip {
        display: inline-block;
        padding: 0.18rem 0.6rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 700;
        background: #E0F2FE;
        color: #0369A1;
    }
    .ucc-chip.verde { background: #DCFCE7; color: #15803D; }
    .ucc-chip.ambar { background: #FEF3C7; color: #B45309; }
    .ucc-chip.rojo  { background: #FEE2E2; color: #B91C1C; }

    /* 8. ETIQUETAS DE FORMULARIO SIEMPRE CLARAS ARRIBA Y BOTONES TÁCTILES */
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stFileUploader label {
        font-weight: 700 !important;
        color: #1E293B !important;
        font-size: 0.88rem !important;
    }
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        min-height: 2.65rem !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* 9. ADAPTACIÓN RESPONSIVA PARA CELULARES Y TABLETS */
    @media (max-width: 900px) {
        .ucc-kpi-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    @media (max-width: 640px) {
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: 1rem !important;
        }
        .ucc-banner {
            padding: 1rem 1.1rem;
            border-radius: 12px;
        }
        .ucc-banner h1 {
            font-size: 1.22rem !important;
        }
        .ucc-banner p {
            font-size: 0.83rem !important;
        }
        .ucc-kpi-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.55rem;
        }
        .ucc-kpi-value {
            font-size: 1.2rem;
        }
        .ucc-step-header {
            padding: 0.65rem 0.85rem;
            flex-direction: column;
            align-items: flex-start;
            gap: 0.35rem;
        }
        .ucc-id-card {
            padding: 0.75rem 0.9rem;
        }
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 2.85rem !important;
            font-size: 0.92rem !important;
        }
        .ucc-aviso-mobile-solo {
            display: block !important;
        }
    }

    /* AVISO EXCLUSIVO RESPONSIVO PARA DISPOSITIVOS MÓVILES */
    .ucc-aviso-mobile-solo {
        display: none;
        background: #FEFCE8;
        border: 1px solid #FEF08A;
        border-radius: 10px;
        padding: 0.85rem 1.05rem;
        margin-bottom: 0.9rem;
    }
</style>
"""


def configurar_pagina_ucc(titulo: str, icono: str = "🎓"):
    """Configura la página de Streamlit, asegura la BD e inyecta el diseño responsivo y la barra lateral."""
    st.set_page_config(
        page_title=f"{titulo} — UCC",
        page_icon=icono,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    repo.asegurar_base_datos()
    st.markdown(CSS_INSTITUCIONAL_UCC, unsafe_allow_html=True)
    renderizar_sidebar_ucc()


def obtener_sesion_estudiante() -> dict | None:
    """Devuelve los datos del estudiante logueado si existe sesión activa."""
    return st.session_state.get("estudiante_sesion")


def iniciar_sesion_estudiante(cedula: str, nombre: str, id_prog: str, nom_prog: str, semestre: int):
    """Registra la sesión de un estudiante para simular su portal individual."""
    st.session_state["estudiante_sesion"] = {
        "cedula": str(cedula).strip(),
        "nombre": str(nombre).strip(),
        "id_programa": str(id_prog).strip(),
        "programa": str(nom_prog).strip(),
        "semestre": int(semestre),
    }


def cerrar_sesion_estudiante():
    """Cierra la sesión del estudiante y regresa al modo libre/administrador."""
    if "estudiante_sesion" in st.session_state:
        del st.session_state["estudiante_sesion"]


def renderizar_sidebar_ucc():
    """Dibuja la barra lateral institucional en español con simulador de login estudiantil."""
    with st.sidebar:
        if repo.RUTA_LOGO_WEB.exists():
            st.image(str(repo.RUTA_LOGO_WEB), width=95)
        st.markdown("### 🏛️ Universidad Cooperativa de Colombia")
        st.caption("Sede Cali · Sistema Académico Web")
        st.divider()

        # ======================================================================
        # SIMULADOR DE LOGIN ESTUDIANTIL (Cédula + Contraseña 1234)
        # ======================================================================
        sesion = obtener_sesion_estudiante()
        if sesion:
            st.markdown(
                f'<div style="background:#e8f5e9; border:1px solid #81c784; border-radius:8px; padding:0.65rem; margin-bottom:0.6rem;">'
                f'<div style="font-weight:700; color:#1b5e20; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.5px;">🔒 SESIÓN DE ESTUDIANTE</div>'
                f'<div style="font-size:0.95rem; font-weight:700; color:#0f172a; margin-top:0.25rem;">👤 {html.escape(sesion["nombre"])}</div>'
                f'<div style="font-size:0.8rem; color:#475569; margin-top:0.15rem;"><b>ID:</b> {html.escape(sesion["cedula"])} · Semestre {sesion["semestre"]}</div>'
                f'<div style="font-size:0.8rem; color:#0369a1; font-weight:600; margin-top:0.1rem;">🎓 {html.escape(sesion["programa"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("🚪 Cerrar Sesión (Volver a Modo Libre)", key="btn_sb_logout", use_container_width=True):
                cerrar_sesion_estudiante()
                st.rerun()
        else:
            with st.expander("🔑 Simulador Login Estudiante", expanded=False):
                st.caption("Simule el ingreso individual como un estudiante con su **ID** y la contraseña **1234**:")
                estudiantes = repo.obtener_datos("Estudiantes")
                programas = {str(p[0]).strip(): str(p[1]) for p in repo.obtener_datos("Programas")}
                if estudiantes:
                    opciones_login = {
                        f"{e[0]} — {e[1]} {e[2]}": e
                        for e in estudiantes
                    }
                    sel_login = st.selectbox("Seleccione Estudiante:", list(opciones_login.keys()), key="sb_sel_est_login")
                    est_sel = opciones_login[sel_login]
                    clave_input = st.text_input("Contraseña (Simulación: 1234):", value="1234", type="password", key="sb_pass_login")

                    if st.button("🔐 Iniciar Sesión", type="primary", key="btn_sb_login_do", use_container_width=True):
                        if clave_input == "1234":
                            nom_p = programas.get(str(est_sel[6]).strip(), str(est_sel[6]).strip())
                            iniciar_sesion_estudiante(
                                cedula=str(est_sel[0]),
                                nombre=f"{est_sel[1]} {est_sel[2]}",
                                id_prog=str(est_sel[6]),
                                nom_prog=nom_p,
                                semestre=int(est_sel[5]),
                            )
                            st.success(f"¡Bienvenido(a), {est_sel[1]}!")
                            st.rerun()
                        else:
                            st.error("Contraseña incorrecta. (Para la simulación use 1234)")
                else:
                    st.info("No hay estudiantes registrados para iniciar sesión.")

        st.divider()

        st.markdown(
            "Use el menú superior para navegar paso a paso por los módulos:\n"
            "- **🏠 Inicio:** Oferta y Cupos\n"
            "- **🎓 Matrícula:** Paso 1 a Paso 4\n"
            "- **📊 Notas y Boletín:** PPS y PDF\n"
            "- **👨‍🏫 Panel Docente:** Calificar\n"
            "- **⚙️ Administración:** Registros y ETL"
        )
        st.divider()

        exe_desk = repo.obtener_instalador_exe_bytes()
        if exe_desk:
            st.download_button(
                label="💻 Descargar Instalador PC (.exe)",
                data=exe_desk,
                file_name="Instalador_Sistema_Universitario_UCC_Setup.exe",
                mime="application/vnd.microsoft.portable-executable",
                use_container_width=True,
                key="btn_sb_descargar_desktop_exe",
            )
        else:
            zip_desk = repo.generar_zip_escritorio_bytes()
            if zip_desk:
                st.download_button(
                    label="💻 Descargar App de Escritorio (.zip)",
                    data=zip_desk,
                    file_name="Sistema_Universitario_UCC_Escritorio.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="btn_sb_descargar_desktop_zip",
                )

        st.download_button(
            label="📥 Descargar Base de Datos (.xlsx)",
            data=repo.exportar_excel_bytes(),
            file_name="Base_Datos_Universidad_UCC.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="btn_sb_descargar_bd_xlsx",
        )

        st.link_button(
            "🐙 Repositorio en GitHub",
            "https://github.com/SlayerCampo/SistemaUniversitarioDeGestion",
            use_container_width=True,
        )


def banner_ucc(titulo: str, subtitulo: str):
    """Renderiza el encabezado institucional con proporciones equilibradas en PC y celular."""
    st.markdown(
        f'<div class="ucc-banner">'
        f'<h1>{html.escape(titulo)}</h1>'
        f'<p>{html.escape(subtitulo)}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def encabezado_paso(numero_paso: str, titulo: str, descripcion: str = ""):
    """Dibuja una cabecera de paso numerada idéntica al flujo guiado de la versión de escritorio."""
    sub_html = f'<p class="ucc-step-sub">{html.escape(descripcion)}</p>' if descripcion else ""
    st.markdown(
        f'<div class="ucc-step-header">'
        f'<span class="ucc-step-badge">{html.escape(numero_paso)}</span>'
        f'<div>'
        f'<p class="ucc-step-title">{html.escape(titulo)}</p>'
        f'{sub_html}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def renderizar_kpis(items: list[tuple[str, str, str]]):
    """
    Renderiza una cuadrícula responsiva de indicadores.
    Cada tupla de `items` es `(etiqueta, valor, clase_color)`.
    """
    tarjetas = []
    for etiqueta, valor, color in items:
        tarjetas.append(
            f'<div class="ucc-kpi-card {html.escape(color)}">'
            f'<div class="ucc-kpi-label">{html.escape(etiqueta)}</div>'
            f'<div class="ucc-kpi-value">{html.escape(str(valor))}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="ucc-kpi-grid">{"".join(tarjetas)}</div>', unsafe_allow_html=True)


def tarjeta_estudiante_html(cedula: str, nombre_completo: str, codigo_prog: str, nombre_prog: str, semestre: int, periodo: str = "") -> str:
    """Genera una tarjeta tipo carné estudiantil clara y responsiva sin sangría que rompa el markdown."""
    chip_periodo = f'<span class="ucc-chip">📅 Periodo {html.escape(periodo)}</span>' if periodo else ""
    return (
        f'<div class="ucc-id-card">'
        f'<div>'
        f'<div class="ucc-id-main">👤 {html.escape(cedula)} — {html.escape(nombre_completo)}</div>'
        f'<div class="ucc-id-sub">🎓 Programa: <b>{html.escape(codigo_prog)} - {html.escape(nombre_prog)}</b> &nbsp;|&nbsp; Semestre {int(semestre)}</div>'
        f'</div>'
        f'<div>{chip_periodo}</div>'
        f'</div>'
    )


def tarjeta_materia_html(codigo: str, nombre: str, creditos: int, docente: str, horario: str, cupos: int | None = None, variante: str = "inscrita") -> str:
    """Genera una tarjeta compacta de asignatura para escritorio y celular en una sola cadena HTML pura."""
    info_cupos = f"<span>👥 Cupos: <b>{cupos}</b></span>" if cupos is not None else ""
    chip_cls = "verde" if variante == "inscrita" else ("ambar" if variante == "carrito" else "")
    return (
        f'<div class="ucc-course-card {html.escape(variante)}">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">'
        f'<div class="ucc-course-title">{html.escape(codigo)} — {html.escape(nombre)}</div>'
        f'<span class="ucc-chip {chip_cls}">{int(creditos)} Créditos ({int(creditos)}h)</span>'
        f'</div>'
        f'<div class="ucc-course-meta">'
        f'<span>👨‍🏫 {html.escape(docente)}</span>'
        f'<span>🕒 {html.escape(horario)}</span>'
        f'{info_cupos}'
        f'</div>'
        f'</div>'
    )

