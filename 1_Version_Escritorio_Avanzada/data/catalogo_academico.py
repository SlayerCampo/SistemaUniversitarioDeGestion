from __future__ import annotations
# ==============================================================================
# ARCHIVO: data/catalogo_academico.py
# PROPÓSITO: Catálogo académico institucional de la Universidad Cooperativa de
#            Colombia (Sede Cali) para la simulación masiva.
#
#            • 5 Facultades y 8 Programas Académicos.
#            • 15 asignaturas distintas por cada programa (120 en total), cada una
#              adscrita a SU programa (no a la facultad).
#            • Cada asignatura se ofrece en 2 grupos con horarios distintos
#              (Grupo 1 en jornada de la mañana y Grupo 2 en jornada de la tarde
#              o noche).
#            • Cada sesión de clase dura 2, 3 o 4 horas seguidas (igual a sus
#              créditos) y NUNCA se programa entre las 13:00 y las 14:00
#              (hora de almuerzo).
# ==============================================================================

import random
import config
from core.validador_horarios import construir_horario, inicios_validos

FACULTADES_OFICIALES = [
    ["F01", "Facultad de Ingeniería", "Dr. Hernán Darío Gómez"],
    ["F02", "Facultad de Ciencias Económicas y Administrativas", "Dra. Claudia Patricia Mejía"],
    ["F03", "Facultad de Psicología y Ciencias Sociales", "Mg. Camilo Andrés Perea"],
    ["F04", "Facultad de Derecho y Ciencias Políticas", "Dra. María Fernanda Morales"],
    ["F05", "Facultad de Ciencias de la Salud", "Dr. Carlos Alberto Osorio"],
]

# [ID_Programa, Nombre, ID_Facultad, Semestres]
PROGRAMAS_OFICIALES = [
    ["P01", "Ingeniería de Software y Sistemas", "F01", 10],
    ["P02", "Ingeniería Industrial", "F01", 10],
    ["P03", "Administración de Empresas", "F02", 9],
    ["P04", "Contaduría Pública", "F02", 9],
    ["P05", "Psicología", "F03", 10],
    ["P06", "Derecho", "F04", 10],
    ["P07", "Enfermería", "F05", 8],
    ["P08", "Medicina", "F05", 12],
]

# Prefijo del código de asignatura de cada programa (Ej: SIS101, IND102...)
PREFIJOS_PROGRAMA = {
    "P01": "SIS", "P02": "IND", "P03": "ADM", "P04": "CON",
    "P05": "PSI", "P06": "DER", "P07": "ENF", "P08": "MED",
}

# Plan de estudios: 15 asignaturas por programa, ordenadas de los primeros
# semestres (1-5) a los últimos (11-15). Formato: (Nombre, Créditos)
PLAN_ESTUDIOS = {
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

# Bolsas de nombres para generar docentes (nombre, género) de forma determinista
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


def _nombre_docente(indice: int) -> str:
    """Genera un nombre de docente coherente (título acorde al género) y repetible."""
    nombre, genero = _DOCENTES_NOMBRES[indice % len(_DOCENTES_NOMBRES)]
    apellido = _DOCENTES_APELLIDOS[(indice * 7 + 3) % len(_DOCENTES_APELLIDOS)]
    titulo = _TITULOS[(indice // 3) % len(_TITULOS)]
    if titulo == "Dr." and genero == "F":
        titulo = "Dra."
    return f"{titulo} {nombre} {apellido}"


def construir_oferta_materias(semilla: int = 11) -> list[list]:
    """
    Construye la oferta completa de asignaturas (120 materias x 2 grupos = 240 filas)
    con la estructura de la hoja 'Materias':
        [ID_Materia, Nombre_Curso, Creditos, Cupos, Docente, ID_Programa, Horario]

    Reglas aplicadas:
    - El ID_Materia incluye el grupo (Ej: 'SIS101-G1', 'SIS101-G2').
    - Cada sesión dura tantas horas seguidas como créditos tiene (2, 3 o 4).
    - Grupo 1 en jornada de la mañana, Grupo 2 en la tarde/noche.
    - Ningún horario toca la franja de almuerzo de 13:00 a 14:00.
    """
    azar = random.Random(semilla)
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    oferta = []

    for idx_prog, programa in enumerate(PROGRAMAS_OFICIALES):
        id_programa = programa[0]
        prefijo = PREFIJOS_PROGRAMA[id_programa]

        for idx_curso, (nombre, creditos) in enumerate(PLAN_ESTUDIOS[id_programa]):
            codigo_base = f"{prefijo}{101 + idx_curso}"
            docente = _nombre_docente(idx_prog * 15 + idx_curso)
            validos = inicios_validos(creditos)
            mananas = [h for h in validos if h + creditos <= config.HORA_ALMUERZO_INICIO]
            tardes = [h for h in validos if h >= config.HORA_ALMUERZO_FIN]

            for grupo in (1, 2):
                bolsa = mananas if grupo == 1 else tardes
                inicio = azar.choice(bolsa or validos)
                dia = azar.choice(dias)
                # El Grupo 2 usa un docente distinto para que el horario sea realista
                docente_grupo = docente if grupo == 1 else _nombre_docente(idx_prog * 15 + idx_curso + 61)
                cupos = azar.choice([30, 32, 35, 40])
                oferta.append([
                    f"{codigo_base}-G{grupo}",
                    nombre,
                    creditos,
                    cupos,
                    docente_grupo,
                    id_programa,
                    construir_horario(dia, inicio, creditos),
                ])
    return oferta

