from __future__ import annotations
# ==============================================================================
# ARCHIVO: pages/1_🎓_Matricula.py
# PROPÓSITO: Portal de Autogestión de Matrícula Estudiantil con flujo guiado
#            Paso a Paso (Paso 1 a Paso 4), idéntico a la versión de escritorio
#            y 100% responsivo para pantallas de celular y computador.
# ==============================================================================

from datetime import date
import uuid
import streamlit as st
from database import repo
from database.estilos_web import (
    configurar_pagina_ucc,
    banner_ucc,
    encabezado_paso,
    renderizar_kpis,
    tarjeta_estudiante_html,
    tarjeta_materia_html,
    obtener_sesion_estudiante,
    iniciar_sesion_estudiante,
    cerrar_sesion_estudiante,
)

configurar_pagina_ucc("Matrícula Académica", "🎓")

banner_ucc(
    "🎓 Matrícula Académica Inteligente (6 a 19 Créditos)",
    "Flujo guiado paso a paso: verifique sus asignaturas actuales, elija materias de su Programa Académico sin cruces de horario y descargue su recibo oficial en PDF.",
)

estudiantes = repo.obtener_datos("Estudiantes")
materias_lista = repo.obtener_datos("Materias")
programas_lista = repo.obtener_datos("Programas")
mapa_programas = {str(p[0]).strip(): str(p[1]) for p in programas_lista}

if not estudiantes or not materias_lista:
    st.warning(
        "💡 La base de datos se encuentra actualmente en blanco (sin estudiantes o sin asignaturas registradas). "
        "Diríjase al módulo de **⚙️ Administración** en el menú izquierdo para registrar datos desde cero o importar el archivo Excel con los 50 estudiantes."
    )
    st.stop()

# ==============================================================================
# PASO 1: ESTUDIANTE EN SESIÓN Y PERIODO ACADÉMICO
# ==============================================================================
sesion = obtener_sesion_estudiante()

if sesion:
    encabezado_paso(
        "PASO 1",
        f"Estudiante en Sesión: {sesion['nombre']}",
        "Ha iniciado sesión con sus credenciales institucionales. Solo puede consultar y matricular asignaturas de su propio Programa.",
    )
    col_info_ses, col_per = st.columns([2.4, 1])
    with col_info_ses:
        st.success(f"🔒 Sesión bloqueada para: **{sesion['cedula']} — {sesion['nombre']}** ({sesion['programa']})")
        if st.button("🚪 Cerrar Sesión (Cambiar de Usuario)", key="btn_logout_paso1"):
            cerrar_sesion_estudiante()
            st.rerun()
    with col_per:
        periodo_activo = st.text_input(
            "📅 Periodo Académico:",
            value="2026-2",
            placeholder="Ej: 2026-2",
        )

    cedula_activa = sesion["cedula"]
    nombre_completo = sesion["nombre"]
    semestre_est = sesion["semestre"]
    id_prog_est = sesion["id_programa"]
    nom_prog_est = sesion["programa"]
else:
    encabezado_paso(
        "PASO 1",
        "Estudiante y Periodo Académico (Modo Abierto / Simulador)",
        "Seleccione un estudiante de la lista o inicie sesión con su ID y clave 1234 para bloquear su portal individual.",
    )

    opciones_est = {
        f"{e[0]} — {e[1]} {e[2]} ({mapa_programas.get(str(e[6]).strip(), e[6])})": e
        for e in estudiantes
    }

    col_est, col_per = st.columns([2.4, 1])
    with col_est:
        etiqueta_est = st.selectbox("👨‍🎓 Seleccione el Estudiante:", list(opciones_est.keys()))
        est_activo = opciones_est[etiqueta_est]
        cedula_activa = str(est_activo[0]).strip()
        nombre_completo = f"{est_activo[1]} {est_activo[2]}"
        semestre_est = int(est_activo[5])
        id_prog_est = str(est_activo[6]).strip()
        nom_prog_est = mapa_programas.get(id_prog_est, id_prog_est)

    with col_per:
        periodo_activo = st.text_input(
            "📅 Periodo Académico:",
            value="2026-2",
            placeholder="Ej: 2026-2",
        )

    col_sim_btn, col_sim_info = st.columns([1.6, 2.4])
    with col_sim_btn:
        if st.button("🔑 Simular Ingreso con este Estudiante (Clave: 1234)", key="btn_simular_paso1", use_container_width=True):
            iniciar_sesion_estudiante(
                cedula=cedula_activa,
                nombre=nombre_completo,
                id_prog=id_prog_est,
                nom_prog=nom_prog_est,
                semestre=semestre_est,
            )
            st.rerun()
    with col_sim_info:
        st.caption("Al simular el ingreso, la sesión se bloquea a este estudiante y no se permitirá ver datos de otros.")

st.markdown(
    tarjeta_estudiante_html(
        cedula=cedula_activa,
        nombre_completo=nombre_completo,
        codigo_prog=id_prog_est,
        nombre_prog=nom_prog_est,
        semestre=semestre_est,
        periodo=periodo_activo.strip() or "2026-2",
    ),
    unsafe_allow_html=True,
)

# Inicializar carrito en session_state por estudiante
clave_carrito = f"carrito_{cedula_activa}"
if clave_carrito not in st.session_state:
    st.session_state[clave_carrito] = []
carrito = st.session_state[clave_carrito]

# Obtener materias ya inscritas activas del estudiante
mapa_materias = {str(m[0]): m for m in materias_lista}
matriculas_est = [
    m for m in repo.obtener_datos("Matriculas")
    if str(m[1]).strip() == cedula_activa
    and str(m[4]).strip() == periodo_activo.strip()
    and (len(m) < 7 or str(m[6]).strip().lower() == "activa")
]

inscritas_detalle = []
for m in matriculas_est:
    info = mapa_materias.get(str(m[2]))
    inscritas_detalle.append({
        "id_matricula": str(m[0]),
        "id": str(m[2]),
        "codigo_base": repo.codigo_base_materia(str(m[2])),
        "nombre": str(info[1]) if info else str(m[2]),
        "creditos": int(m[3]),
        "docente": str(info[4]) if info else "Por asignar",
        "horario": str(info[6]) if info else "",
    })

cred_inscritos = sum(x["creditos"] for x in inscritas_detalle)
cred_carrito = sum(x["creditos"] for x in carrito)
cred_totales = cred_inscritos + cred_carrito

# Indicadores rápidos de carga académica
estado_rango = "En rango válido" if repo.CREDITOS_MINIMOS <= cred_totales <= repo.CREDITOS_MAXIMOS else f"Mínimo {repo.CREDITOS_MINIMOS} Cr."
color_total = "verde" if repo.CREDITOS_MINIMOS <= cred_totales <= repo.CREDITOS_MAXIMOS else "ambar"

renderizar_kpis([
    ("Materias Ya Inscritas", str(len(inscritas_detalle)), "celeste"),
    ("Créditos Ya Inscritos", f"{cred_inscritos} Cr.", "azul"),
    ("Créditos en Carrito", f"{cred_carrito} Cr.", "ambar"),
    ("Total Semestre", f"{cred_totales} / {repo.CREDITOS_MAXIMOS} Cr.", color_total),
    ("Estado de Carga", estado_rango, color_total),
])
st.progress(min(1.0, cred_totales / repo.CREDITOS_MAXIMOS))

tab_flujo, tab_retiro = st.tabs([
    "🛒 Paso a Paso: Matricular Asignaturas",
    "📋 Retirar Asignaturas o Descargar Recibo PDF",
])

with tab_flujo:
    # ==========================================================================
    # PASO 2: ASIGNATURAS YA MATRICULADAS EN ESTE PERIODO
    # ==========================================================================
    encabezado_paso(
        "PASO 2",
        f"Asignaturas Ya Matriculadas en este Periodo ({len(inscritas_detalle)} materias · {cred_inscritos} Créditos)",
        "Estas son las asignaturas que el estudiante ya tiene inscritas activamente en el semestre.",
    )

    if not inscritas_detalle:
        st.info("ℹ️ El estudiante aún no tiene asignaturas inscritas en este periodo académico.")
    else:
        for ins in inscritas_detalle:
            st.markdown(
                tarjeta_materia_html(
                    codigo=ins["id"],
                    nombre=ins["nombre"],
                    creditos=ins["creditos"],
                    docente=ins["docente"],
                    horario=ins["horario"],
                    variante="inscrita",
                ),
                unsafe_allow_html=True,
            )

    # ==========================================================================
    # PASO 3: SELECCIONAR ASIGNATURA DEL PROGRAMA Y GRUPO / HORARIO
    # ==========================================================================
    encabezado_paso(
        "PASO 3",
        f"Elija Asignatura del Programa ({nom_prog_est}) y su Grupo / Horario",
        "Solo se muestran las asignaturas propias de su programa que aún no están inscritas ni en el carrito.",
    )

    bases_ocupadas = {x["codigo_base"] for x in inscritas_detalle} | {x["codigo_base"] for x in carrito}
    materias_prog = [
        m for m in materias_lista
        if str(m[5]).strip().upper() == id_prog_est.upper()
        and repo.codigo_base_materia(str(m[0])) not in bases_ocupadas
    ]

    if not materias_prog:
        st.success("✅ Ya tienes inscritas o en el carrito todas las asignaturas disponibles para tu programa.")
    else:
        por_curso: dict[str, dict] = {}
        for m in sorted(materias_prog, key=lambda r: str(r[0])):
            base = repo.codigo_base_materia(str(m[0]))
            if base not in por_curso:
                por_curso[base] = {
                    "etiqueta": f"{base} — {m[1]} ({m[2]} Créditos / {m[2]}h seguidas)",
                    "grupos": [],
                }
            por_curso[base]["grupos"].append({
                "id": str(m[0]),
                "codigo_base": base,
                "nombre": str(m[1]),
                "creditos": int(m[2]),
                "cupos": int(m[3]),
                "docente": str(m[4]),
                "horario": str(m[6]),
            })

        col_p3a, col_p3b = st.columns(2)
        with col_p3a:
            mapa_cursos = {v["etiqueta"]: k for k, v in por_curso.items()}
            curso_lbl = st.selectbox(
                "📘 Paso 3.A — Asignatura del Plan de Estudios:",
                list(mapa_cursos.keys()),
            )
            base_sel = mapa_cursos[curso_lbl]
            grupos_disp = por_curso[base_sel]["grupos"]

        with col_p3b:
            mapa_grupos = {
                f"{g['id']} · {g['horario']} · Cupos: {g['cupos']}": g
                for g in grupos_disp
            }
            grupo_lbl = st.selectbox(
                "🕒 Paso 3.B — Grupo y Horario Ofertado:",
                list(mapa_grupos.keys()),
            )
            mat_elegida = mapa_grupos[grupo_lbl]

        st.markdown(
            tarjeta_materia_html(
                codigo=mat_elegida["id"],
                nombre=mat_elegida["nombre"],
                creditos=mat_elegida["creditos"],
                docente=mat_elegida["docente"],
                horario=mat_elegida["horario"],
                cupos=mat_elegida["cupos"],
                variante="",
            ),
            unsafe_allow_html=True,
        )

        if st.button("➕ Agregar Asignatura al Carrito (Validar Horario y Cupos)", type="primary", use_container_width=True):
            if mat_elegida["cupos"] <= 0:
                st.error(f"🚫 El grupo '{mat_elegida['id']}' no tiene cupos disponibles.")
            elif cred_totales + mat_elegida["creditos"] > repo.CREDITOS_MAXIMOS:
                st.error(
                    f"🚫 Agregar esta asignatura ({mat_elegida['creditos']} créditos) superaría el tope de "
                    f"{repo.CREDITOS_MAXIMOS} créditos permitidos (Total actual: {cred_totales})."
                )
            else:
                hay_cruce, msg_cruce = repo.validar_cruce_horarios(mat_elegida, inscritas_detalle + carrito)
                if hay_cruce:
                    st.error(f"🚫 Conflicto de Horario: {msg_cruce}")
                else:
                    carrito.append(mat_elegida)
                    st.toast(f"Agregada al carrito: {mat_elegida['nombre']}", icon="🛒")
                    st.rerun()

    # ==========================================================================
    # PASO 4: CARRITO DE ASIGNATURAS SELECCIONADAS Y CONFIRMACIÓN
    # ==========================================================================
    encabezado_paso(
        "PASO 4",
        f"Carrito de Asignaturas por Confirmar ({len(carrito)} en carrito · {cred_carrito} Créditos)",
        "Revise las asignaturas preseleccionadas y pulse 'Confirmar Matrícula' para asentar el registro oficial.",
    )

    if not carrito:
        st.info("🛒 El carrito está vacío. Elija una asignatura en el Paso 3 y pulse '➕ Agregar Asignatura al Carrito'.")
    else:
        for idx, item in enumerate(list(carrito)):
            c_card, c_del = st.columns([4.5, 1])
            with c_card:
                st.markdown(
                    tarjeta_materia_html(
                        codigo=item["id"],
                        nombre=item["nombre"],
                        creditos=item["creditos"],
                        docente=item["docente"],
                        horario=item["horario"],
                        variante="carrito",
                    ),
                    unsafe_allow_html=True,
                )
            with c_del:
                st.write("")
                if st.button("🗑️ Quitar", key=f"quitar_carr_{idx}", use_container_width=True):
                    carrito.pop(idx)
                    st.rerun()

        col_vaciar, col_confirmar = st.columns(2)
        with col_vaciar:
            if st.button("🧹 Vaciar Todo el Carrito", use_container_width=True):
                st.session_state[clave_carrito] = []
                st.rerun()
        with col_confirmar:
            if st.button("✅ Confirmar Matrícula Oficial", type="primary", use_container_width=True):
                if cred_totales < repo.CREDITOS_MINIMOS:
                    st.error(
                        f"⚠️ Debe completar al menos {repo.CREDITOS_MINIMOS} créditos en el semestre "
                        f"(Total entre ya inscritos y carrito: {cred_totales} créditos)."
                    )
                else:
                    hoy = date.today().strftime("%Y-%m-%d")
                    for item in carrito:
                        repo.ajustar_cupo_materia(item["id"], -1)
                        id_mat = str(uuid.uuid4())[:8].upper()
                        repo.insertar_fila(
                            "Matriculas",
                            [id_mat, cedula_activa, item["id"], item["creditos"], periodo_activo.strip(), hoy, "Activa"],
                        )
                    st.session_state[clave_carrito] = []
                    st.success("🎉 ¡Matrícula confirmada exitosamente y cupos actualizados!")
                    st.rerun()

    # Botón directo de descarga del recibo PDF si ya tiene asignaturas activas
    if inscritas_detalle:
        st.divider()
        pdf_bytes = repo.generar_pdf_matricula_bytes(cedula_activa)
        if pdf_bytes:
            st.download_button(
                label="📄 Descargar Recibo Oficial de Matrícula (PDF)",
                data=pdf_bytes,
                file_name=f"Recibo_Matricula_{cedula_activa}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_pdf_matricula_flujo",
            )

with tab_retiro:
    encabezado_paso(
        "RETIRO Y PDF",
        f"Cancelación de Asignaturas y Certificados de {nombre_completo}",
        "Al retirar una asignatura se actualiza su estado a 'Cancelada' y se devuelve automáticamente +1 cupo al grupo.",
    )

    if not inscritas_detalle:
        st.info("El estudiante no tiene asignaturas activas para retirar en este periodo.")
    else:
        opciones_retiro = {
            f"{x['id_matricula']} — {x['id']} · {x['nombre']} ({x['creditos']} Cr. | {x['horario']})": x
            for x in inscritas_detalle
        }
        sel_retiro = st.selectbox("Seleccione la asignatura activa que desea retirar:", list(opciones_retiro.keys()))
        datos_ret = opciones_retiro[sel_retiro]

        st.markdown(
            tarjeta_materia_html(
                codigo=datos_ret["id"],
                nombre=datos_ret["nombre"],
                creditos=datos_ret["creditos"],
                docente=datos_ret["docente"],
                horario=datos_ret["horario"],
                variante="inscrita",
            ),
            unsafe_allow_html=True,
        )

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button("❌ Confirmar Retiro de Asignatura", type="primary", use_container_width=True):
                fila_orig = repo.buscar_fila("Matriculas", 0, datos_ret["id_matricula"])
                if fila_orig:
                    repo.actualizar_fila(
                        "Matriculas",
                        0,
                        datos_ret["id_matricula"],
                        [fila_orig[0], fila_orig[1], fila_orig[2], fila_orig[3], fila_orig[4], fila_orig[5], "Cancelada"],
                    )
                    repo.ajustar_cupo_materia(datos_ret["id"], +1)
                    st.success(f"✅ Asignatura '{datos_ret['nombre']}' retirada y +1 cupo restituido.")
                    st.rerun()

        with col_r2:
            pdf_bytes_tab = repo.generar_pdf_matricula_bytes(cedula_activa)
            if pdf_bytes_tab:
                st.download_button(
                    label="📄 Descargar Recibo Oficial de Matrícula (PDF)",
                    data=pdf_bytes_tab,
                    file_name=f"Recibo_Matricula_{cedula_activa}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_pdf_matricula_retiro",
                )
