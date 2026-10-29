from __future__ import annotations
# ==============================================================================
# ARCHIVO: data/db_postgres.py
# PROPÓSITO: Conector a PostgreSQL utilizando la librería `psycopg` (tal como se
#            implementó en Practica2_Postgres.py). Permite verificar el estado
#            del servidor PostgreSQL, inicializar las tablas desde
#            `schema_universidad.sql` y sincronizar los datos del archivo Excel
#            hacia el motor relacional PostgreSQL.
# ==============================================================================

from pathlib import Path
import config
import data.db_excel as db_excel

try:
    import psycopg
    PSYCOPG_DISPONIBLE = True
except ImportError:
    PSYCOPG_DISPONIBLE = False


def conectar_postgres():
    """Establece y devuelve una conexión activa a PostgreSQL usando `config.POSTGRES_CONFIG`."""
    if not PSYCOPG_DISPONIBLE:
        raise RuntimeError(
            "La librería 'psycopg' no está instalada en este entorno Python.\n"
            "Puede instalarla con: pip install psycopg[binary]"
        )
    return psycopg.connect(**config.POSTGRES_CONFIG)


def inicializar_esquema_postgres() -> tuple[bool, str]:
    """Ejecuta el archivo `schema_universidad.sql` en la base de datos PostgreSQL."""
    ruta_sql = config.BASE_DIR / "schema_universidad.sql"
    if not ruta_sql.exists():
        return False, "No se encontró el archivo schema_universidad.sql."

    try:
        script_sql = ruta_sql.read_text(encoding="utf-8")
        with conectar_postgres() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(script_sql)
        return True, "Tablas verificadas/creadas exitosamente en PostgreSQL."
    except Exception as error:
        return False, f"No fue posible conectar a PostgreSQL: {error}"


def sincronizar_excel_a_postgres() -> tuple[bool, str]:
    """
    Exporta/sincroniza todos los registros actuales del archivo Excel hacia
    la base de datos PostgreSQL utilizando cláusulas `ON CONFLICT DO UPDATE`
    para garantizar idempotencia e integridad referencial.
    """
    exito_init, msg_init = inicializar_esquema_postgres()
    if not exito_init:
        return False, msg_init

    try:
        facultades = db_excel.obtener_datos("Facultades")
        programas = db_excel.obtener_datos("Programas")
        materias = db_excel.obtener_datos("Materias")
        estudiantes = db_excel.obtener_datos("Estudiantes")
        matriculas = db_excel.obtener_datos("Matriculas")
        notas = db_excel.obtener_datos("Notas")

        with conectar_postgres() as conexion:
            with conexion.cursor() as cursor:
                for f in facultades:
                    decano = f[2] if len(f) > 2 and f[2] else "Por asignar"
                    cursor.execute(
                        """
                        INSERT INTO facultades (id_facultad, nombre_facultad, decano)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id_facultad) DO UPDATE
                        SET nombre_facultad = EXCLUDED.nombre_facultad,
                            decano = EXCLUDED.decano
                        """,
                        (str(f[0]), str(f[1]), str(decano))
                    )

                for p in programas:
                    duracion = int(p[3]) if len(p) > 3 and p[3] else 10
                    cursor.execute(
                        """
                        INSERT INTO programas (id_programa, nombre_programa, id_facultad, semestres_duracion)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id_programa) DO UPDATE
                        SET nombre_programa = EXCLUDED.nombre_programa,
                            id_facultad = EXCLUDED.id_facultad,
                            semestres_duracion = EXCLUDED.semestres_duracion
                        """,
                        (str(p[0]), str(p[1]), str(p[2]), duracion)
                    )

                for m in materias:
                    cursor.execute(
                        """
                        INSERT INTO materias (id_materia, nombre_curso, creditos, cupos, docente, id_programa, horario)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id_materia) DO UPDATE
                        SET nombre_curso = EXCLUDED.nombre_curso,
                            creditos = EXCLUDED.creditos,
                            cupos = EXCLUDED.cupos,
                            docente = EXCLUDED.docente,
                            id_programa = EXCLUDED.id_programa,
                            horario = EXCLUDED.horario
                        """,
                        (str(m[0]), str(m[1]), int(m[2]), int(m[3]), str(m[4]), str(m[5]), str(m[6]))
                    )

                for e in estudiantes:
                    cursor.execute(
                        """
                        INSERT INTO estudiantes (id_estudiante, nombre, apellidos, correo, telefono, semestre, id_programa)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id_estudiante) DO UPDATE
                        SET nombre = EXCLUDED.nombre,
                            apellidos = EXCLUDED.apellidos,
                            correo = EXCLUDED.correo,
                            telefono = EXCLUDED.telefono,
                            semestre = EXCLUDED.semestre,
                            id_programa = EXCLUDED.id_programa
                        """,
                        (str(e[0]), str(e[1]), str(e[2]), str(e[3]), str(e[4]), int(e[5]), str(e[6]))
                    )

                for mat in matriculas:
                    cursor.execute(
                        """
                        INSERT INTO matriculas (id_matricula, cedula, id_materia, creditos, periodo, fecha_matricula, estado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id_matricula) DO UPDATE
                        SET estado = EXCLUDED.estado
                        """,
                        (str(mat[0]), str(mat[1]), str(mat[2]), int(mat[3]), str(mat[4]), str(mat[5]), str(mat[6]))
                    )

                for n in notas:
                    cursor.execute(
                        """
                        INSERT INTO notas (id_nota, id_matricula, id_materia, nota1, nota2, nota3, definitiva, estado)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id_matricula) DO UPDATE
                        SET nota1 = EXCLUDED.nota1,
                            nota2 = EXCLUDED.nota2,
                            nota3 = EXCLUDED.nota3,
                            definitiva = EXCLUDED.definitiva,
                            estado = EXCLUDED.estado
                        """,
                        (str(n[0]), str(n[1]), str(n[2]), float(n[3]), float(n[4]), float(n[5]), float(n[6]), str(n[7]))
                    )

        return True, (
            f"Sincronización exitosa con PostgreSQL:\n"
            f"• {len(facultades)} Facultades\n"
            f"• {len(programas)} Programas\n"
            f"• {len(materias)} Materias\n"
            f"• {len(estudiantes)} Estudiantes\n"
            f"• {len(matriculas)} Matrículas\n"
            f"• {len(notas)} Registros de Notas"
        )
    except Exception as error:
        return False, f"Error durante la sincronización con PostgreSQL:\n{error}"

