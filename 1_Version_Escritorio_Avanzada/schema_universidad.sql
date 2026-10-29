-- =============================================================================
-- ARCHIVO: schema_universidad.sql
-- PROPÓSITO: Script DDL de creación de tablas relacionales en PostgreSQL para
--            el Sistema de Gestión Académica y Matrículas UCC.
--            Sigue el estándar de integridad referencial visto en Biblioteca.sql.
-- =============================================================================

CREATE TABLE IF NOT EXISTS facultades (
    id_facultad VARCHAR(30) PRIMARY KEY,
    nombre_facultad VARCHAR(150) NOT NULL,
    decano VARCHAR(150) DEFAULT 'Por asignar'
);

CREATE TABLE IF NOT EXISTS programas (
    id_programa VARCHAR(30) PRIMARY KEY,
    nombre_programa VARCHAR(150) NOT NULL,
    id_facultad VARCHAR(30) NOT NULL
        REFERENCES facultades(id_facultad) ON UPDATE CASCADE ON DELETE RESTRICT,
    semestres_duracion INTEGER NOT NULL DEFAULT 10
        CHECK (semestres_duracion > 0 AND semestres_duracion <= 14)
);

CREATE TABLE IF NOT EXISTS materias (
    id_materia VARCHAR(30) PRIMARY KEY,
    nombre_curso VARCHAR(200) NOT NULL,
    creditos INTEGER NOT NULL CHECK (creditos > 0 AND creditos <= 12),
    cupos INTEGER NOT NULL DEFAULT 25 CHECK (cupos >= 0),
    docente VARCHAR(150) NOT NULL,
    id_programa VARCHAR(30) NOT NULL
        REFERENCES programas(id_programa) ON UPDATE CASCADE ON DELETE RESTRICT,
    horario VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS estudiantes (
    id_estudiante VARCHAR(30) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL,
    telefono VARCHAR(30) NOT NULL,
    semestre INTEGER NOT NULL CHECK (semestre >= 1 AND semestre <= 14),
    id_programa VARCHAR(30) NOT NULL
        REFERENCES programas(id_programa) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS matriculas (
    id_matricula VARCHAR(30) PRIMARY KEY,
    cedula VARCHAR(30) NOT NULL
        REFERENCES estudiantes(id_estudiante) ON UPDATE CASCADE ON DELETE RESTRICT,
    id_materia VARCHAR(30) NOT NULL
        REFERENCES materias(id_materia) ON UPDATE CASCADE ON DELETE RESTRICT,
    creditos INTEGER NOT NULL CHECK (creditos > 0),
    periodo VARCHAR(20) NOT NULL,
    fecha_matricula DATE NOT NULL DEFAULT CURRENT_DATE,
    estado VARCHAR(30) NOT NULL DEFAULT 'Activa'
        CHECK (estado IN ('Activa', 'Cancelada', 'Finalizada'))
);

CREATE TABLE IF NOT EXISTS notas (
    id_nota VARCHAR(30) PRIMARY KEY,
    id_matricula VARCHAR(30) NOT NULL UNIQUE
        REFERENCES matriculas(id_matricula) ON UPDATE CASCADE ON DELETE CASCADE,
    id_materia VARCHAR(30) NOT NULL
        REFERENCES materias(id_materia) ON UPDATE CASCADE ON DELETE RESTRICT,
    nota1 NUMERIC(4, 2) NOT NULL DEFAULT 0.0 CHECK (nota1 >= 0.0 AND nota1 <= 5.0),
    nota2 NUMERIC(4, 2) NOT NULL DEFAULT 0.0 CHECK (nota2 >= 0.0 AND nota2 <= 5.0),
    nota3 NUMERIC(4, 2) NOT NULL DEFAULT 0.0 CHECK (nota3 >= 0.0 AND nota3 <= 5.0),
    definitiva NUMERIC(4, 2) NOT NULL DEFAULT 0.0 CHECK (definitiva >= 0.0 AND definitiva <= 5.0),
    estado VARCHAR(30) NOT NULL
        CHECK (estado IN ('Aprobado', 'Reprobado', 'Sin notas'))
);

CREATE TABLE IF NOT EXISTS usuarios (
    usuario VARCHAR(50) PRIMARY KEY,
    password_hash VARCHAR(256) NOT NULL,
    rol VARCHAR(30) NOT NULL CHECK (rol IN ('Administrador', 'Profesor', 'Estudiante')),
    nombre_completo VARCHAR(150) NOT NULL,
    documento_asociado VARCHAR(30)
);

