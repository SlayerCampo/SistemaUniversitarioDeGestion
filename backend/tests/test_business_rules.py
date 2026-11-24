from __future__ import annotations
"""
Suite automatizada de pruebas (pytest) de las reglas de negocio universitarias UCC
ejecutada directamente contra PostgreSQL real en Docker.
"""

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.horarios import BloqueHorario, detectar_cruce_grupos, validar_bloque_institucional
from app.db.models import HorarioGrupo
from app.db.seed import asegurar_base_inicial, poblar_base_datos_simulacion, vaciar_base_datos
from app.db.session import SessionLocal
from app.main import app

client = TestClient(app)


def _login(usuario: str, password: str = "1234") -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"usuario": usuario, "password": password})
    assert r.status_code == 200, f"Fallo login {usuario}: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module", autouse=True)
def preparar_db():
    db = SessionLocal()
    try:
        asegurar_base_inicial(db)
        poblar_base_datos_simulacion(db, total_estudiantes=50)
    finally:
        db.close()
    yield


def test_health_y_kpis_simulacion():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "postgresql_connected"

    k = client.get("/api/v1/catalogo/kpis").json()
    assert k["facultades"] == 5
    assert k["programas"] == 8
    assert k["asignaturas"] == 120
    assert k["grupos"] == 240
    assert k["estudiantes"] == 50


def test_regla_almuerzo_13_14_en_validador_y_en_postgres():
    # Validador Python rechaza cualquier cruce con 13:00-14:00
    ok1, _ = validar_bloque_institucional(1, 12, 14, 2)
    ok2, _ = validar_bloque_institucional(2, 13, 15, 2)
    ok3, _ = validar_bloque_institucional(3, 11, 14, 3)
    assert not ok1 and not ok2 and not ok3

    # Horarios permitidos justo antes y después del almuerzo
    ok_antes, _ = validar_bloque_institucional(1, 10, 13, 3)
    ok_despues, _ = validar_bloque_institucional(1, 14, 17, 3)
    assert ok_antes and ok_despues

    # Constraint CHECK físico de PostgreSQL impide insertar clase a la hora del almuerzo
    db = SessionLocal()
    try:
        db.add(HorarioGrupo(id_grupo="SIS101-G1", dia_semana=1, hora_inicio=12, hora_fin=14))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_cero_clases_en_almuerzo_en_los_240_grupos():
    grupos = client.get("/api/v1/catalogo/grupos").json()
    assert len(grupos) == 240
    for g in grupos:
        for h in g["horarios"]:
            assert not (h["hora_inicio"] < 14 and h["hora_fin"] > 13), f"Almuerzo violado en {g['id_grupo']}"


def test_detector_cruces_horarios():
    b1 = BloqueHorario(1, 8, 11)
    b2 = BloqueHorario(1, 10, 12)
    b3 = BloqueHorario(1, 11, 13)
    cruce, _ = detectar_cruce_grupos("Nueva", [b2], [("G1", "Existente", [b1])])
    assert cruce is True
    sin_cruce, _ = detectar_cruce_grupos("Adyacente", [b3], [("G1", "Existente", [b1])])
    assert sin_cruce is False


def test_rbac_privacidad_estudiante():
    h_1001 = _login("1001")
    # 1001 sí puede ver su propio resumen y boletín
    assert client.get("/api/v1/matricula/resumen/1001", headers=h_1001).status_code == 200
    assert client.get("/api/v1/notas/boletin/1001", headers=h_1001).status_code == 200
    # 1001 NO puede espiar ni matricular a 1002
    assert client.get("/api/v1/matricula/resumen/1002", headers=h_1001).status_code == 403
    assert client.get("/api/v1/notas/boletin/1002", headers=h_1001).status_code == 403
    assert client.get("/api/v1/reportes/boletin/1002/pdf", headers=h_1001).status_code == 403


def test_matricula_reglas_cupos_y_retiro():
    h_admin = _login("admin")
    # Crear estudiante nuevo sin materias en P01
    r_est = client.post(
        "/api/v1/catalogo/estudiantes",
        headers=h_admin,
        json={
            "id_estudiante": "9999",
            "nombre": "Test",
            "apellidos": "Automatizado",
            "correo": "test.auto@campusucc.edu.co",
            "telefono": "3001112233",
            "semestre": 2,
            "id_programa": "P01",
            "password": "1234",
        },
    )
    assert r_est.status_code == 201
    h_9999 = _login("9999")

    # 1. Prohibir materia de otro programa (P05 Psicología)
    r_prog = client.post(
        "/api/v1/matricula/confirmar",
        headers=h_9999,
        json={"id_estudiante": "9999", "id_periodo": "2026-2", "grupos_ids": ["PSI101-G1", "PSI102-G1"]},
    )
    assert r_prog.status_code == 400

    # 2. Prohibir menos de 6 créditos
    r_min = client.post(
        "/api/v1/matricula/confirmar",
        headers=h_9999,
        json={"id_estudiante": "9999", "id_periodo": "2026-2", "grupos_ids": ["SIS104-G1"]},
    )
    assert r_min.status_code == 400

    # 3. Prohibir asignatura duplicada (G1 y G2 de SIS101)
    r_dup = client.post(
        "/api/v1/matricula/confirmar",
        headers=h_9999,
        json={"id_estudiante": "9999", "id_periodo": "2026-2", "grupos_ids": ["SIS101-G1", "SIS101-G2"]},
    )
    assert r_dup.status_code == 400

    # 4. Elegir 2 grupos de P01 que no se crucen y sumen >= 6 créditos
    resumen = client.get("/api/v1/matricula/resumen/9999", headers=h_9999).json()
    elegidos: list[dict] = []
    bloques_usados: list[tuple[str, str, list[BloqueHorario]]] = []
    cred_sum = 0
    for asig in resumen["oferta_disponible"]:
        for g in asig["grupos"]:
            blqs = [BloqueHorario(h["dia_semana"], h["hora_inicio"], h["hora_fin"]) for h in g["horarios"]]
            hay_cruce, _ = detectar_cruce_grupos(g["nombre_curso"], blqs, bloques_usados)
            if not hay_cruce and g["cupos_disponibles"] > 0:
                elegidos.append(g)
                bloques_usados.append((g["id_grupo"], g["nombre_curso"], blqs))
                cred_sum += g["creditos"]
                break
        if cred_sum >= 6:
            break

    gids = [g["id_grupo"] for g in elegidos]
    cupos_antes = elegidos[0]["cupos_disponibles"]

    r_ok = client.post(
        "/api/v1/matricula/confirmar",
        headers=h_9999,
        json={"id_estudiante": "9999", "id_periodo": "2026-2", "grupos_ids": gids},
    )
    assert r_ok.status_code == 201, r_ok.text
    id_mat_0 = r_ok.json()["matriculas_creadas"][0]

    # Verificar descuento atómico de cupo
    g_post = [g for g in client.get("/api/v1/catalogo/grupos", params={"id_programa": "P01"}).json() if g["id_grupo"] == gids[0]][0]
    assert g_post["cupos_disponibles"] == cupos_antes - 1

    # Verificar retiro y restitución de cupo
    r_ret = client.post(f"/api/v1/matricula/retirar/{id_mat_0}", headers=h_9999)
    assert r_ret.status_code == 200
    g_rest = [g for g in client.get("/api/v1/catalogo/grupos", params={"id_programa": "P01"}).json() if g["id_grupo"] == gids[0]][0]
    assert g_rest["cupos_disponibles"] == cupos_antes


def test_calificacion_docente_y_pdfs():
    h_profe = _login("profe")
    h_1001 = _login("1001")

    bol = client.get("/api/v1/notas/boletin/1001", headers=h_1001).json()
    assert len(bol["asignaturas"]) > 0
    id_mat = bol["asignaturas"][0]["id_matricula"]

    # Upsert calificación: 4.0*0.3 + 4.5*0.3 + 5.0*0.4 = 1.2 + 1.35 + 2.0 = 4.55
    r_cal = client.put(
        "/api/v1/notas/calificar",
        headers=h_profe,
        json={"calificaciones": [{"id_matricula": id_mat, "nota1": 4.0, "nota2": 4.5, "nota3": 5.0}]},
    )
    assert r_cal.status_code == 200

    bol2 = client.get("/api/v1/notas/boletin/1001", headers=h_1001).json()
    item = [a for a in bol2["asignaturas"] if a["id_matricula"] == id_mat][0]
    assert item["definitiva"] == 4.55
    assert item["estado"] == "Aprobado"

    # Verificar PDFs válidos
    pdf_mat = client.get("/api/v1/reportes/matricula/1001/pdf", headers=h_1001)
    assert pdf_mat.status_code == 200 and pdf_mat.content.startswith(b"%PDF")
    pdf_bol = client.get("/api/v1/reportes/boletin/1001/pdf", headers=h_1001)
    assert pdf_bol.status_code == 200 and pdf_bol.content.startswith(b"%PDF")


def test_etl_excel_ciclo_completo():
    h_admin = _login("admin")
    # 1. Generar Excel 50+ estudiantes
    r_xlsx = client.get("/api/v1/etl/generar-simulacion", headers=h_admin)
    assert r_xlsx.status_code == 200
    assert len(r_xlsx.content) > 5000

    # 2. Vaciar BD (primero falla sin confirmación exacta)
    assert client.post("/api/v1/demo/vaciar", headers=h_admin, json={"confirmacion": "NO"}).status_code == 400
    assert client.post("/api/v1/demo/vaciar", headers=h_admin, json={"confirmacion": "VACIAR"}).status_code == 200
    assert client.get("/api/v1/catalogo/kpis").json()["estudiantes"] == 0

    # 3. Importar el Excel generado de vuelta a PostgreSQL
    r_imp = client.post(
        "/api/v1/etl/importar",
        headers=h_admin,
        files={"archivo": ("Universidad_50_Estudiantes_UCC.xlsx", r_xlsx.content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r_imp.status_code == 200, r_imp.text
    assert r_imp.json()["insertados"]["Estudiantes"] == 50
    assert r_imp.json()["insertados"]["Grupos"] == 240

    # 4. Exportar sábana desde PostgreSQL
    r_exp = client.get("/api/v1/etl/exportar-sabana", headers=h_admin)
    assert r_exp.status_code == 200 and len(r_exp.content) > 5000
