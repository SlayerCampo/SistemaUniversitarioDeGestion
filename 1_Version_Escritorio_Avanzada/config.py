from __future__ import annotations
# ==============================================================================
# ARCHIVO: config.py
# PROPÓSITO: Centralizar todas las constantes, rutas de archivos, paleta de
#            colores corporativos UCC, reglas de negocio y parámetros de
#            conexión a base de datos (Excel y PostgreSQL).
# ==============================================================================

import os
from pathlib import Path

# ------------------------------------------------------------------------------
# 1. RUTAS DEL SISTEMA DE ARCHIVOS (Usando pathlib para compatibilidad multi-OS)
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RUTA_ARCHIVO_EXCEL = BASE_DIR / "Registro_Matricula_Pro.xlsx"
RUTA_LOGO_UCC = BASE_DIR / "logo_ucc.png"
CARPETA_REPORTES_PDF = BASE_DIR / "Reportes_PDF"
CARPETA_PLANTILLAS_EXCEL = BASE_DIR / "Plantillas_Excel"

# Aseguramos que las carpetas de salida existan al iniciar el módulo
CARPETA_REPORTES_PDF.mkdir(exist_ok=True)
CARPETA_PLANTILLAS_EXCEL.mkdir(exist_ok=True)

# ------------------------------------------------------------------------------
# 2. REGLAS DE NEGOCIO ACADÉMICAS (Universidad Cooperativa de Colombia)
# ------------------------------------------------------------------------------
CREDITOS_MINIMOS = 6
CREDITOS_MAXIMOS = 19
NOTA_MINIMA = 0.0
NOTA_MAXIMA = 5.0
NOTA_APROBATORIA = 3.0
CUPOS_POR_DEFECTO = 25
PERIODO_ACTUAL_DEFECTO = "2026-2"

# Reglas de horario institucional (en horas, formato 24h)
HORA_APERTURA = 6            # Las clases pueden iniciar desde las 06:00
HORA_CIERRE = 22             # Ninguna clase puede terminar después de las 22:00
HORA_ALMUERZO_INICIO = 13    # Franja de almuerzo: de 13:00 a 14:00 no hay clases
HORA_ALMUERZO_FIN = 14
DURACIONES_PERMITIDAS = (2, 3, 4)  # Horas seguidas por sesión de clase

# Ponderación de cortes académicos (30%, 30%, 40% o promedio aritmético)
USAR_PROMEDIO_PONDERADO = False  # Si es False, calcula promedio simple (N1+N2+N3)/3
PESOS_NOTAS = (0.30, 0.30, 0.40)

# ------------------------------------------------------------------------------
# 3. PALETA DE COLORES E IDENTIDAD VISUAL INSTITUCIONAL UCC
# ------------------------------------------------------------------------------
COLOR_AZUL_UCC = "#1F6AA5"       # Azul corporativo principal
COLOR_AZUL_OSCURO = "#154B75"    # Azul hover / énfasis
COLOR_CELESTE_UCC = "#36B5C6"    # Turquesa / Celeste institucional
COLOR_CELESTE_HOVER = "#2A919F"  # Hover botones de acción
COLOR_MORADO_UCC = "#3B1C7A"     # Fondo institucional secundario
COLOR_VERDE_EXITO = "#2E8B57"    # Estado aprobado / válido
COLOR_VERDE_HOVER = "#246B43"
COLOR_AMARILLO_AVISO = "#F0AD4E" # Botones secundarios / advertencias
COLOR_AMARILLO_HOVER = "#EC971F"
COLOR_ROJO_ERROR = "#D9534F"     # Estado reprobado / alerta / salir
COLOR_ROJO_HOVER = "#C9302C"
COLOR_FONDO_CLARO = "#F4F7FA"    # Fondo de contenedores y tarjetas
COLOR_CAJA_TEXTO = "#EEEEEE"     # Fondo de entradas de formulario

FUENTE_PRINCIPAL = "Century Gothic"
FUENTE_FORMULARIOS = "Roboto"

# ------------------------------------------------------------------------------
# 4. ESTRUCTURA DEL MODELO DE DATOS (Hojas y Columnas del Excel)
# ------------------------------------------------------------------------------
ENCABEZADOS_BD = {
    "Facultades": [
        "ID_Facultad",
        "Nombre_Facultad",
        "Decano"
    ],
    "Programas": [
        "ID_Programa",
        "Nombre_Programa",
        "ID_Facultad",
        "Semestres_Duracion"
    ],
    "Materias": [
        "ID_Materia",
        "Nombre_Curso",
        "Creditos",
        "Cupos",
        "Docente",
        "ID_Programa",
        "Horario"
    ],
    "Estudiantes": [
        "ID_Estudiante",
        "Nombre",
        "Apellidos",
        "Correo",
        "Telefono",
        "Semestre",
        "ID_Programa"
    ],
    "Matriculas": [
        "ID_Matricula",
        "Cedula",
        "ID_Materia",
        "Creditos",
        "Periodo",
        "Fecha_Matricula",
        "Estado"
    ],
    "Notas": [
        "ID_Nota",
        "ID_Matricula",
        "ID_Materia",
        "Nota1",
        "Nota2",
        "Nota3",
        "Definitiva",
        "Estado"
    ],
    "Usuarios": [
        "Usuario",
        "Password_Hash",
        "Rol",
        "Nombre_Completo",
        "Documento_Asociado"
    ]
}

# ------------------------------------------------------------------------------
# 5. CONFIGURACIÓN DE CONEXIÓN A POSTGRESQL (Opcional / Híbrido con clase)
# ------------------------------------------------------------------------------
# Permite alternar o sincronizar con PostgreSQL tal como se vio en Practica2_Postgres.py
MODO_PERSISTENCIA = os.getenv("UCC_DB_MODE", "EXCEL")  # "EXCEL" o "POSTGRES"

POSTGRES_CONFIG = {
    "host": os.getenv("UCC_DB_HOST", "localhost"),
    "port": int(os.getenv("UCC_DB_PORT", "5432")),
    "dbname": os.getenv("UCC_DB_NAME", "UniversidadUCC"),
    "user": os.getenv("UCC_DB_USER", "postgres"),
    "password": os.getenv("UCC_DB_PASSWORD", "Admin123"),
    "connect_timeout": 5
}


# Aliases de compatibilidad para acceso directo
PG_HOST = POSTGRES_CONFIG["host"]
PG_PORT = POSTGRES_CONFIG["port"]
PG_DATABASE = POSTGRES_CONFIG["dbname"]
PG_USER = POSTGRES_CONFIG["user"]
