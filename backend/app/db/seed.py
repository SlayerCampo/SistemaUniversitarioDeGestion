from __future__ import annotations
"""
Catálogo académico institucional UCC y motor de semilla / reinicio en PostgreSQL.
- Datos 100% sintéticos (cumplimiento Ley 1581 de 2012).
- 5 Facultades, 8 Programas, 120 Asignaturas, 240 Grupos (mañana y tarde/noche),
  sin clases entre 13:00 y 14:00, y 50 estudiantes con matrículas y notas realistas.
"""

from datetime import date
from decimal import Decimal
import random

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.horarios import (
    BloqueHorario,
    detectar_cruce_grupos,
    inicios_validos,
    quitar_acentos,
)
from app.core.security import hash_password
from app.db.models import (
    Asignatura,
    Estudiante,
    Facultad,
    Grupo,
    HorarioGrupo,
    Matricula,
    Nota,
    Periodo,
    Programa,
    Usuario,
)

FACULTADES_OFICIALES = [
    ("F01", "Facultad de Ingeniería", "Dr. Hernán Darío Gómez"),
    ("F02", "Facultad de Ciencias Económicas y Administrativas", "Dra. Claudia Patricia Mejía"),
    ("F03", "Facultad de Psicología y Ciencias Sociales", "Mg. Camilo Andrés Perea"),
    ("F04", "Facultad de Derecho y Ciencias Políticas", "Dra. María Fernanda Morales"),
    ("F05", "Facultad de Ciencias de la Salud", "Dr. Carlos Alberto Osorio"),
]

PROGRAMAS_OFICIALES = [
    ("P01", "Ingeniería de Software y Sistemas", "F01", 10),
    ("P02", "Ingeniería Industrial", "F01", 10),
    ("P03", "Administración de Empresas", "F02", 9),
    ("P04", "Contaduría Pública", "F02", 9),
    ("P05", "Psicología", "F03", 10),
    ("P06", "Derecho", "F04", 10),
    ("P07", "Enfermería", "F05", 8),
    ("P08", "Medicina", "F05", 12),
]

PREFIJOS_PROGRAMA = {
    "P01": "SIS", "P02": "IND", "P03": "ADM", "P04": "CON",
    "P05": "PSI", "P06": "DER", "P07": "ENF", "P08": "MED",
}

PLAN_ESTUDIOS: dict[str, list[tuple[str, int]]] = {
    "P01": [
        ("Fundamentos de Programación", 4), ("Cálculo Diferencial", 4),
        ("Lógica y Matemáticas Discretas", 3), ("Introducción a la Ingeniería de Software", 2),
        ("Programación Orientada a Objetos", 4), ("Cálculo Integral", 3),
        ("Estructuras de Datos y Algoritmos", 4), ("Bases de Datos Relacionales", 3),
        ("Física Mecánica y Laboratorio", 4), ("Ingeniería de Requisitos y UML", 3),
        ("Arquitectura y Patrones de Software", 3), ("Redes de Computadores", 3),
        ("Metodologías Ágiles y Scrum", 2), ("Inteligencia Artificial y Machine Learning", 4),
        ("Calidad y Pruebas de Software", 3),
    ],
    "P02": [
        ("Fundamentos de Ingeniería Industrial", 2), ("Cálculo Diferencial", 4),
        ("Química General", 3), ("Dibujo Técnico y CAD", 3),
        ("Física Mecánica", 4), ("Estadística Descriptiva", 3),
        ("Álgebra Lineal", 3), ("Procesos de Manufactura", 4),
        ("Probabilidad e Inferencia", 3), ("Investigación de Operaciones", 4),
        ("Ergonomía y Seguridad Industrial", 2), ("Gestión de la Calidad", 3),
        ("Logística y Cadena de Suministro", 3), ("Simulación de Procesos", 3),
        ("Gestión de Proyectos Industriales", 3),
    ],
    "P03": [
        ("Fundamentos de Administración", 3), ("Matemáticas Básicas", 3),
        ("Introducción a la Contabilidad", 3), ("Microeconomía", 3),
        ("Comunicación Empresarial", 2), ("Derecho Comercial", 2),
        ("Macroeconomía", 3), ("Estadística Aplicada", 3),
        ("Comportamiento Organizacional", 3), ("Matemáticas Financieras", 4),
        ("Gestión del Talento Humano", 3), ("Mercadeo Estratégico", 3),
        ("Finanzas Corporativas", 4), ("Emprendimiento e Innovación", 2),
        ("Planeación Estratégica", 3),
    ],
    "P04": [
        ("Contabilidad General", 4), ("Matemáticas Financieras", 3),
        ("Fundamentos de Economía", 3), ("Derecho Comercial y Laboral", 2),
        ("Costos y Presupuestos", 4), ("Estadística Descriptiva", 3),
        ("Contabilidad Intermedia", 4), ("Legislación Tributaria", 3),
        ("Sistemas de Información Contable", 3), ("Análisis Financiero", 3),
        ("Auditoría Financiera", 4), ("Revisoría Fiscal", 3),
        ("Contabilidad Pública", 3), ("NIIF y Normas Internacionales", 3),
        ("Ética Profesional del Contador", 2),
    ],
    "P05": [
        ("Introducción a la Psicología", 3), ("Procesos Psicológicos Básicos", 3),
        ("Neuroanatomía y Neurofisiología", 4), ("Epistemología de la Psicología", 2),
        ("Psicología del Desarrollo", 3), ("Estadística para Psicología", 3),
        ("Teorías de la Personalidad", 3), ("Psicología Social", 3),
        ("Psicopatología", 4), ("Evaluación Psicológica", 4),
        ("Metodología de la Investigación", 3), ("Psicología Educativa", 3),
        ("Psicología Clínica", 4), ("Psicología Organizacional", 3),
        ("Ética y Deontología Psicológica", 2),
    ],
    "P06": [
        ("Introducción al Derecho", 3), ("Teoría del Estado", 3),
        ("Historia del Derecho", 2), ("Derecho Romano", 3),
        ("Derecho Constitucional Colombiano", 4), ("Derecho Civil de Personas", 3),
        ("Derecho Penal General", 4), ("Teoría del Delito", 3),
        ("Derecho de Obligaciones", 3), ("Derecho Laboral", 3),
        ("Derecho Comercial", 3), ("Derecho Administrativo", 4),
        ("Derecho Procesal Civil", 4), ("Derechos Humanos y DIH", 2),
        ("Derecho Internacional Público", 3),
    ],
    "P07": [
        ("Fundamentos de Enfermería", 4), ("Anatomía Humana", 4),
        ("Biología Celular", 3), ("Química Orgánica", 3),
        ("Fisiología Humana", 4), ("Microbiología y Parasitología", 3),
        ("Bioquímica", 3), ("Cuidado Básico del Paciente", 4),
        ("Farmacología", 3), ("Salud Pública y Epidemiología", 3),
        ("Enfermería del Adulto", 4), ("Enfermería Materno Infantil", 4),
        ("Enfermería en Salud Mental", 3), ("Gerencia en Servicios de Salud", 2),
        ("Bioética en Enfermería", 2),
    ],
    "P08": [
        ("Biología Médica", 4), ("Anatomía General", 4),
        ("Histología y Embriología", 4), ("Química Médica", 3),
        ("Bioquímica Médica", 4), ("Fisiología Médica", 4),
        ("Microbiología Médica", 3), ("Inmunología", 3),
        ("Patología General", 4), ("Farmacología Médica", 4),
        ("Semiología", 4), ("Salud Pública", 3),
        ("Medicina Interna", 4), ("Pediatría", 4),
        ("Bioética Médica", 2),
    ],
}

_DOCENTES_NOMBRES = [
    ("Carlos Andrés", "M"), ("Ana María", "F"), ("Luis Fernando", "M"), ("Sandra Milena", "F"),
    ("Jorge Eliécer", "M"), ("Patricia", "F"), ("Mauricio", "M"), ("Marcela", "F"),
    ("Ricardo", "M"), ("Claudia", "F"), ("Andrés Felipe", "M"), ("Diana Carolina", "F"),
    ("Hernán", "M"), ("Martha Lucía", "F"), ("Roberto", "M"), ("Gloria Inés", "F"),
    ("Fernando", "M"), ("Liliana", "F"), ("Camilo", "M"), ("Adriana", "F"),
    ("Julián", "M"), ("Paola Andrea", "F"), ("Sergio", "M"), ("Natalia", "F"),
    ("Alexander", "M"), ("Carolina", "F"), ("Óscar", "M"), ("Mónica", "F"),
    ("Gustavo", "M"), ("Yolanda", "F"),
]
_DOCENTES_APELLIDOS = [
    "Pérez Mora", "Gómez Ríos", "Martínez Lenis", "Ortiz Valencia", "Henao Cardona",
    "Trujillo Sanz", "Pineda Cruz", "Lozano Reyes", "Echeverri Soto", "Beltrán Cano",
    "Valencia Mejía", "Caicedo Rojas", "Mina Angulo", "Rosero Paz", "Osorio Duque",
    "Quintero Arias", "Cifuentes Lara", "Zúñiga Mena", "Arboleda Vélez", "Ramírez Tello",
    "Salcedo Perea", "Barona Gil", "Lasso Ibarra", "Tascón Rey", "Sinisterra Lucumí",
]
_TITULOS = ["Ing.", "Mg.", "Esp.", "Lic.", "Dr."]

NOMBRES_POOL = [
    "Laura Sofía", "Mateo Andrés", "Valentina", "Daniel Eduardo", "Mariana",
    "Andrés Felipe", "Camila", "Sebastián", "Isabella", "Nicolás",
    "Gabriela", "Sara Lucía", "Samuel David", "Manuela", "Felipe",
    "Natalia", "Julián", "Paula Andrea", "Esteban", "Carolina",
    "Simón", "Valeria", "Daniela", "David", "Juliana",
    "Emmanuel", "Melissa", "Cristian", "Salomé", "Lucas",
    "Luciana", "Martín", "Vanessa", "Tomás", "Antonia",
    "Jerónimo", "María José", "Juan José", "Adriana", "Carlos Alberto",
    "Tatiana", "Oscar Iván", "Diana Marcela", "Camilo", "Ángela María",
]
APELLIDOS_POOL = [
    "Restrepo Henao", "Pelaez Castro", "Guzmán Osorio", "Vargas Silva", "Herrera Medina",
    "Salazar Duque", "Jaramillo Maya", "Giraldo Cano", "Montoya Zuluaga", "Bermúdez Cárdenas",
    "Londoño Ortiz", "Zapata Carvajal", "Quintero Blandón", "Álvarez Ospina", "Valencia Gallego",
    "Muñoz Agudelo", "Arango Bedoya", "Betancur Chaverra", "Escobar Forero", "Tamayo Villegas",
    "Caicedo Murillo", "Rojas Hurtado", "Castaño Hoyos", "Mejía Barrientos", "Lozano Mosquera",
    "Paredes Rivas", "Cifuentes Balanta", "Rosero Benavides", "Narváez Erazo", "Delgado Guerrero",
    "Chaves Zambrano", "Solano Peñaloza", "Bustos Cuellar", "Gutiérrez Peña", "Pineda Rueda",
]


def _nombre_docente(indice: int) -> str:
    nombre, genero = _DOCENTES_NOMBRES[indice % len(_DOCENTES_NOMBRES)]
    apellido = _DOCENTES_APELLIDOS[(indice * 7 + 3) % len(_DOCENTES_APELLIDOS)]
    titulo = _TITULOS[(indice // 3) % len(_TITULOS)]
    if titulo == "Dr." and genero == "F":
        titulo = "Dra."
    return f"{titulo} {nombre} {apellido}"


def calcular_definitiva_y_estado(n1: float, n2: float, n3: float) -> tuple[Decimal, str]:
    val = round(
        n1 * settings.PESO_CORTE_1 + n2 * settings.PESO_CORTE_2 + n3 * settings.PESO_CORTE_3,
        2,
    )
    dec = Decimal(f"{val:.2f}")
    estado = "Aprobado" if val >= settings.NOTA_APROBATORIA else "Reprobado"
    return dec, estado


def asegurar_base_inicial(db: Session) -> None:
    """Garantiza que exista el periodo activo y las cuentas maestras (admin y profe) con bcrypt."""
    if not db.get(Periodo, settings.PERIODO_ACTIVO_DEFECTO):
        db.add(
            Periodo(
                id_periodo=settings.PERIODO_ACTIVO_DEFECTO,
                activo=True,
                fecha_inicio=date(2026, 8, 1),
                fecha_fin=date(2026, 12, 15),
            )
        )

    cuentas_maestras = [
        ("admin", "1234", "Administrador", "Administrador General UCC", "0000"),
        ("profe", "1234", "Profesor", "Docente Titular UCC", "9001"),
    ]
    for usr, pwd, rol, nom, doc in cuentas_maestras:
        if not db.get(Usuario, usr):
            db.add(
                Usuario(
                    usuario=usr,
                    password_hash=hash_password(pwd),
                    rol=rol,
                    nombre_completo=nom,
                    documento_asociado=doc,
                )
            )
    db.commit()


def construir_dataset_simulacion(total_estudiantes: int = 50, semilla: int = 11) -> dict:
    """Genera en memoria un dataset determinista y 100% sintético para seed o Excel ETL."""
    azar = random.Random(semilla)
    periodo = settings.PERIODO_ACTIVO_DEFECTO

    asignaturas: list[dict] = []
    grupos: list[dict] = []

    for idx_prog, prog in enumerate(PROGRAMAS_OFICIALES):
        id_prog = prog[0]
        pref = PREFIJOS_PROGRAMA[id_prog]
        for idx_c, (nom_c, cred) in enumerate(PLAN_ESTUDIOS[id_prog]):
            cod_asig = f"{pref}{101 + idx_c}"
            asignaturas.append({
                "id_asignatura": cod_asig,
                "nombre_curso": nom_c,
                "creditos": cred,
                "id_programa": id_prog,
            })
            doc1 = _nombre_docente(idx_prog * 15 + idx_c)
            validos = inicios_validos(cred)
            mananas = [h for h in validos if h + cred <= settings.HORA_ALMUERZO_INICIO]
            tardes = [h for h in validos if h >= settings.HORA_ALMUERZO_FIN]

            for g_num in (1, 2):
                bolsa = mananas if g_num == 1 else tardes
                h_ini = azar.choice(bolsa or validos)
                dia = azar.choice([1, 2, 3, 4, 5])
                doc = doc1 if g_num == 1 else _nombre_docente(idx_prog * 15 + idx_c + 61)
                cupos = azar.choice([30, 32, 35, 40])
                bloque = BloqueHorario(dia_semana=dia, hora_inicio=h_ini, hora_fin=h_ini + cred)
                grupos.append({
                    "id_grupo": f"{cod_asig}-G{g_num}",
                    "id_asignatura": cod_asig,
                    "nombre_curso": nom_c,
                    "creditos": cred,
                    "id_programa": id_prog,
                    "id_periodo": periodo,
                    "docente": doc,
                    "cupos_totales": cupos,
                    "cupos_disponibles": cupos,
                    "bloque": bloque,
                })

    estudiantes = [
        {
            "id_estudiante": "1001", "nombre": "Alejandro", "apellidos": "Campo Solarte",
            "correo": "alejandro.campo@campusucc.edu.co", "telefono": "3158901234",
            "semestre": 6, "id_programa": "P01",
        },
        {
            "id_estudiante": "1002", "nombre": "Juan Esteban", "apellidos": "Cardona Calambas",
            "correo": "juan.cardona@campusucc.edu.co", "telefono": "3176543210",
            "semestre": 6, "id_programa": "P01",
        },
        {
            "id_estudiante": "1003", "nombre": "Diego Fernando", "apellidos": "Gómez Rivera",
            "correo": "diego.gomez@campusucc.edu.co", "telefono": "3201122334",
            "semestre": 6, "id_programa": "P01",
        },
    ]

    azar_est = random.Random(42)
    progs_cods = [p[0] for p in PROGRAMAS_OFICIALES]
    for i in range(4, total_estudiantes + 1):
        ced = str(1000 + i)
        nom = NOMBRES_POOL[(i - 4) % len(NOMBRES_POOL)]
        ape = APELLIDOS_POOL[(i - 4) % len(APELLIDOS_POOL)]
        prog_cod = progs_cods[(i - 1) % len(progs_cods)]
        max_sem = next((p[3] for p in PROGRAMAS_OFICIALES if p[0] == prog_cod), 10)
        sem = ((i * 3) % max_sem) + 1
        nl = quitar_acentos(nom.lower().split()[0])
        al = quitar_acentos(ape.lower().split()[0])
        estudiantes.append({
            "id_estudiante": ced,
            "nombre": nom,
            "apellidos": ape,
            "correo": f"{nl}.{al}{i}@campusucc.edu.co",
            "telefono": f"31{azar_est.randint(0, 9)}{azar_est.randint(1000000, 9999999)}",
            "semestre": sem,
            "id_programa": prog_cod,
        })

    por_programa: dict[str, list[dict]] = {}
    for g in grupos:
        por_programa.setdefault(g["id_programa"], []).append(g)

    matriculas: list[dict] = []
    notas: list[dict] = []
    notas_destacadas = [(4.8, 4.6, 5.0), (4.5, 4.7, 4.9), (4.6, 4.8, 4.7)]

    for idx_e, est in enumerate(estudiantes):
        objetivo = 15 if idx_e < 3 else azar_est.choice([12, 14, 15, 16])
        disp = [g for g in por_programa.get(est["id_programa"], []) if g["cupos_disponibles"] > 0]
        por_asig: dict[str, list[dict]] = {}
        for g in disp:
            por_asig.setdefault(g["id_asignatura"], []).append(g)

        codigos = list(por_asig.keys())
        azar_est.shuffle(codigos)

        usados: list[tuple[str, str, list[BloqueHorario]]] = []
        cred_acum = 0
        for cod in codigos:
            cands = list(por_asig[cod])
            azar_est.shuffle(cands)
            for g in cands:
                if cred_acum + g["creditos"] > settings.CREDITOS_MAXIMOS:
                    continue
                hay_cruce, _ = detectar_cruce_grupos(g["nombre_curso"], [g["bloque"]], usados)
                if hay_cruce:
                    continue
                g["cupos_disponibles"] -= 1
                id_mat = f"MAT{est['id_estudiante']}_{g['id_grupo']}"
                matriculas.append({
                    "id_matricula": id_mat,
                    "id_estudiante": est["id_estudiante"],
                    "id_grupo": g["id_grupo"],
                    "id_periodo": periodo,
                    "creditos": g["creditos"],
                    "fecha_matricula": date(2026, 9, 15),
                    "estado": "Activa",
                })
                usados.append((g["id_grupo"], g["nombre_curso"], [g["bloque"]]))
                cred_acum += g["creditos"]

                if idx_e < 3:
                    n1, n2, n3 = notas_destacadas[idx_e]
                    def_val, est_nota = calcular_definitiva_y_estado(n1, n2, n3)
                    notas.append({
                        "id_nota": f"NOT_{id_mat}",
                        "id_matricula": id_mat,
                        "nota1": Decimal(f"{n1:.2f}"),
                        "nota2": Decimal(f"{n2:.2f}"),
                        "nota3": Decimal(f"{n3:.2f}"),
                        "definitiva": def_val,
                        "estado": est_nota,
                    })
                elif azar_est.random() < 0.85:
                    n1 = round(azar_est.uniform(2.8, 4.9), 2)
                    n2 = round(azar_est.uniform(2.7, 4.9), 2)
                    n3 = round(azar_est.uniform(3.0, 5.0), 2)
                    def_val, est_nota = calcular_definitiva_y_estado(n1, n2, n3)
                    notas.append({
                        "id_nota": f"NOT_{id_mat}",
                        "id_matricula": id_mat,
                        "nota1": Decimal(f"{n1:.2f}"),
                        "nota2": Decimal(f"{n2:.2f}"),
                        "nota3": Decimal(f"{n3:.2f}"),
                        "definitiva": def_val,
                        "estado": est_nota,
                    })
                break
            if cred_acum >= objetivo:
                break

    return {
        "facultades": FACULTADES_OFICIALES,
        "programas": PROGRAMAS_OFICIALES,
        "asignaturas": asignaturas,
        "grupos": grupos,
        "estudiantes": estudiantes,
        "matriculas": matriculas,
        "notas": notas,
        "periodo": periodo,
    }


def vaciar_base_datos(db: Session) -> dict[str, int]:
    """Limpia todas las tablas académicas y cuentas de estudiantes, conservando admin/profe y periodo activo."""
    db.execute(delete(Nota))
    db.execute(delete(Matricula))
    db.execute(delete(HorarioGrupo))
    db.execute(delete(Grupo))
    db.execute(delete(Asignatura))
    db.execute(delete(Estudiante))
    db.execute(delete(Programa))
    db.execute(delete(Facultad))
    db.execute(delete(Usuario).where(Usuario.rol == "Estudiante"))
    db.commit()
    asegurar_base_inicial(db)
    return {"status": 1}


def poblar_base_datos_simulacion(db: Session, total_estudiantes: int = 50) -> dict[str, int]:
    """Reinicia y puebla PostgreSQL con la universidad completa (50+ estudiantes, 240 grupos)."""
    vaciar_base_datos(db)
    data = construir_dataset_simulacion(total_estudiantes=total_estudiantes)

    for f_id, f_nom, f_dec in data["facultades"]:
        db.add(Facultad(id_facultad=f_id, nombre_facultad=f_nom, decano=f_dec))
    db.flush()

    for p_id, p_nom, f_id, sems in data["programas"]:
        db.add(Programa(id_programa=p_id, nombre_programa=p_nom, id_facultad=f_id, semestres_duracion=sems))
    db.flush()

    for a in data["asignaturas"]:
        db.add(Asignatura(**a))
    db.flush()

    for g in data["grupos"]:
        db.add(
            Grupo(
                id_grupo=g["id_grupo"],
                id_asignatura=g["id_asignatura"],
                id_periodo=g["id_periodo"],
                docente=g["docente"],
                cupos_totales=g["cupos_totales"],
                cupos_disponibles=g["cupos_disponibles"],
            )
        )
        b: BloqueHorario = g["bloque"]
        db.add(
            HorarioGrupo(
                id_grupo=g["id_grupo"],
                dia_semana=b.dia_semana,
                hora_inicio=b.hora_inicio,
                hora_fin=b.hora_fin,
            )
        )
    db.flush()

    # Reutilizamos un único hash bcrypt de '1234' en el seed sintético para que el seed tome <0.5s
    hash_demo_1234 = hash_password("1234")
    for e in data["estudiantes"]:
        db.add(Estudiante(**e))
        db.add(
            Usuario(
                usuario=e["id_estudiante"],
                password_hash=hash_demo_1234,
                rol="Estudiante",
                nombre_completo=f"{e['nombre']} {e['apellidos']}",
                documento_asociado=e["id_estudiante"],
            )
        )
    db.flush()

    for m in data["matriculas"]:
        db.add(Matricula(**m))
    db.flush()

    for n in data["notas"]:
        db.add(Nota(**n))

    db.commit()
    return {
        "facultades": len(data["facultades"]),
        "programas": len(data["programas"]),
        "asignaturas": len(data["asignaturas"]),
        "grupos": len(data["grupos"]),
        "estudiantes": len(data["estudiantes"]),
        "matriculas": len(data["matriculas"]),
        "notas": len(data["notas"]),
    }
