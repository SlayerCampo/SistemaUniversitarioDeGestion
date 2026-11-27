# 📐 Especificación Completa de Diagramas UML 2.5 y MER (15 Modelos)
### **Sistema Integral de Gestión Académica, Matrículas y Calificaciones — UCC (v2.0)**

> Documento técnico-gráfico elaborado conforme a la **Guía de Especificación de Diagramas UML y MER** (1 MER + 7 UML de Estructura + 7 UML de Comportamiento = **15 Modelos**), modelando fielmente la arquitectura real del sistema (`FastAPI` + `PostgreSQL 16/17` + `React/Tauri/Capacitor`).

---

## 📑 Índice de Modelos

| # | Diagrama | Categoría |
| :-: | :--- | :--- |
| 1 | [Modelo Entidad-Relación (MER)](#1-modelo-entidad-relación-mer) | Base de Datos |
| 2 | [Diagrama de Clases](#2-diagrama-de-clases) | UML Estructura |
| 3 | [Diagrama de Objetos](#3-diagrama-de-objetos) | UML Estructura |
| 4 | [Diagrama de Componentes](#4-diagrama-de-componentes) | UML Estructura |
| 5 | [Diagrama de Despliegue (Local)](#5-diagrama-de-despliegue-local) | UML Estructura |
| 6 | [Diagrama de Paquetes](#6-diagrama-de-paquetes) | UML Estructura |
| 7 | [Diagrama de Estructura Compuesta](#7-diagrama-de-estructura-compuesta) | UML Estructura |
| 8 | [Diagrama de Perfiles](#8-diagrama-de-perfiles) | UML Estructura |
| 9 | [Diagrama de Casos de Uso](#9-diagrama-de-casos-de-uso) | UML Comportamiento |
| 10 | [Diagrama de Actividades](#10-diagrama-de-actividades) | UML Comportamiento |
| 11 | [Diagrama de Máquina de Estados](#11-diagrama-de-máquina-de-estados) | UML Comportamiento |
| 12 | [Diagrama de Secuencia](#12-diagrama-de-secuencia) | UML Comportamiento |
| 13 | [Diagrama de Comunicación](#13-diagrama-de-comunicación) | UML Comportamiento |
| 14 | [Diagrama de Temporización](#14-diagrama-de-temporización) | UML Comportamiento |
| 15 | [Diagrama de Vista General de Interacciones](#15-diagrama-de-vista-general-de-interacciones) | UML Comportamiento |

---

## 1. MODELO RELACIONAL / BASE DE DATOS (1 DIAGRAMA)

### 1. Modelo Entidad-Relación (MER)
Esquema físico normalizado en **3FN** con las **10 tablas reales** de PostgreSQL (`backend/app/db/models.py`), llaves primarias (`PK`), foráneas (`FK`) y cardinalidades en notación pata de gallo.

```mermaid
erDiagram
    FACULTADES {
        varchar id_facultad PK
        varchar nombre_facultad
        varchar decano
        timestamptz created_at
    }
    PROGRAMAS {
        varchar id_programa PK
        varchar nombre_programa
        varchar id_facultad FK
        smallint semestres_duracion
    }
    PERIODOS {
        varchar id_periodo PK
        boolean activo
        date fecha_inicio
        date fecha_fin
    }
    ASIGNATURAS {
        varchar id_asignatura PK
        varchar nombre_curso
        smallint creditos
        varchar id_programa FK
    }
    GRUPOS {
        varchar id_grupo PK
        varchar id_asignatura FK
        varchar id_periodo FK
        varchar docente
        int cupos_totales
        int cupos_disponibles
    }
    HORARIOS_GRUPO {
        bigint id_horario PK
        varchar id_grupo FK
        smallint dia_semana
        smallint hora_inicio
        smallint hora_fin
    }
    ESTUDIANTES {
        varchar id_estudiante PK
        varchar nombre
        varchar apellidos
        varchar correo
        varchar telefono
        smallint semestre
        varchar id_programa FK
    }
    MATRICULAS {
        varchar id_matricula PK
        varchar id_estudiante FK
        varchar id_grupo FK
        varchar id_periodo FK
        smallint creditos
        date fecha_matricula
        varchar estado
    }
    NOTAS {
        varchar id_nota PK
        varchar id_matricula FK "UNIQUE"
        numeric nota1
        numeric nota2
        numeric nota3
        numeric definitiva
        varchar estado
        timestamptz updated_at
    }
    USUARIOS {
        varchar usuario PK
        varchar password_hash
        varchar rol
        varchar nombre_completo
        varchar documento_asociado
        timestamptz created_at
    }

    FACULTADES ||--o{ PROGRAMAS : "agrupa"
    PROGRAMAS ||--o{ ASIGNATURAS : "contiene"
    PROGRAMAS ||--o{ ESTUDIANTES : "inscribe"
    ASIGNATURAS ||--o{ GRUPOS : "oferta"
    PERIODOS ||--o{ GRUPOS : "vigente_en"
    GRUPOS ||--|{ HORARIOS_GRUPO : "tiene_bloques"
    ESTUDIANTES ||--o{ MATRICULAS : "registra"
    GRUPOS ||--o{ MATRICULAS : "asigna_cupo"
    PERIODOS ||--o{ MATRICULAS : "corresponde_a"
    MATRICULAS ||--o| NOTAS : "evalua"
    USUARIOS |o--o| ESTUDIANTES : "autentica_por_documento"
```

---

## 2. DIAGRAMAS UML DE ESTRUCTURA (7 DIAGRAMAS)

### 2. Diagrama de Clases
Representación estática de las clases de dominio y servicios principales del backend con modificadores de visibilidad (`+`, `-`, `#`), tipos de datos, métodos y multiplicidades.

```mermaid
classDiagram
    class Facultad {
        +String id_facultad
        +String nombre_facultad
        +String decano
        +DateTime created_at
    }
    class Programa {
        +String id_programa
        +String nombre_programa
        +String id_facultad
        +int semestres_duracion
    }
    class Asignatura {
        +String id_asignatura
        +String nombre_curso
        +int creditos
        +String id_programa
    }
    class Grupo {
        +String id_grupo
        +String id_asignatura
        +String id_periodo
        +String docente
        +int cupos_totales
        +int cupos_disponibles
        +reservarCupo() bool
        +liberarCupo() void
    }
    class HorarioGrupo {
        +int id_horario
        +String id_grupo
        +int dia_semana
        +int hora_inicio
        +int hora_fin
        +validarSinAlmuerzo() bool
    }
    class Estudiante {
        +String id_estudiante
        +String nombre
        +String apellidos
        +String correo
        +String telefono
        +int semestre
        +String id_programa
        +calcularPPS() Decimal
    }
    class Matricula {
        +String id_matricula
        +String id_estudiante
        +String id_grupo
        +String id_periodo
        +int creditos
        +Date fecha_matricula
        +String estado
        +cancelar() void
    }
    class Nota {
        +String id_nota
        +String id_matricula
        +Decimal nota1
        +Decimal nota2
        +Decimal nota3
        +Decimal definitiva
        +String estado
        +calcularDefinitiva() Decimal
    }
    class Usuario {
        +String usuario
        -String password_hash
        +String rol
        +String nombre_completo
        +String documento_asociado
        +verificarPassword(plain: String) bool
    }
    class MatriculaService {
        +validarCreditos(grupos: List) bool
        +detectarCruces(bloques: List) bool
        +procesarMatricula(id_est: String, grupos: List) Matricula
    }

    Facultad "1" *-- "1..*" Programa
    Programa "1" o-- "1..*" Asignatura
    Programa "1" -- "0..*" Estudiante
    Asignatura "1" *-- "1..*" Grupo
    Grupo "1" *-- "1..*" HorarioGrupo
    Estudiante "1" -- "0..*" Matricula
    Grupo "1" -- "0..*" Matricula
    Matricula "1" *-- "0..1" Nota
    MatriculaService ..> Matricula : gestiona
    MatriculaService ..> Grupo : reserva cupo
```

---

### 3. Diagrama de Objetos
Instancia estática en tiempo de ejecución mostrando el estado real en memoria de una matrícula activa del estudiante `1001` (Alejandro Campo Solarte).

```mermaid
flowchart LR
    est["<b>est1001 : Estudiante</b><br/>id_estudiante = '1001'<br/>nombre = 'Alejandro'<br/>apellidos = 'Campo Solarte'<br/>semestre = 6<br/>id_programa = 'P01'"]
    prog["<b>progP01 : Programa</b><br/>id_programa = 'P01'<br/>nombre_programa = 'Ingeniería de Software y Sistemas'<br/>semestres_duracion = 10"]
    mat["<b>mat1 : Matricula</b><br/>id_matricula = 'MAT1001_SIS101-G1'<br/>id_periodo = '2026-2'<br/>creditos = 4<br/>estado = 'Activa'"]
    grp["<b>grpG1 : Grupo</b><br/>id_grupo = 'SIS101-G1'<br/>docente = 'Ing. Carlos Andrés Pérez'<br/>cupos_totales = 35<br/>cupos_disponibles = 28"]
    hor["<b>hor1 : HorarioGrupo</b><br/>dia_semana = 1 (Lunes)<br/>hora_inicio = 8<br/>hora_fin = 12"]
    nota["<b>nota1 : Nota</b><br/>id_nota = 'NOT_MAT1001_SIS101-G1'<br/>nota1 = 4.80 | nota2 = 4.60 | nota3 = 5.00<br/>definitiva = 4.82<br/>estado = 'Aprobado'"]

    est --- prog
    est --- mat
    mat --- grp
    grp --- hor
    mat --- nota
```

---

### 4. Diagrama de Componentes
Organización modular del software, dependencias e interfaces provistas (`I*`) y requeridas entre Frontend, API FastAPI, Servicios y Base de Datos.

```mermaid
flowchart TB
    subgraph FRONT ["«component» Frontend Unificado (React + Vite + Tailwind)"]
        UI_WEB["Web / Tauri / Capacitor UI"]
        API_CLI["Cliente HTTP Axios/Fetch"]
        UI_WEB --> API_CLI
    end

    I_REST(("«interface»<br/>IAuth / IMatricula<br/>INotas / IReportes"))
    API_CLI -. "requiere (HTTPS/JSON)" .-> I_REST

    subgraph BACK ["«component» Backend FastAPI (Python 3.11)"]
        R_AUTH["AuthRouter"]
        R_MAT["MatriculaRouter"]
        R_NOT["NotasRouter"]
        R_ETL["ETLDemoRouter"]
        S_MAT["MatriculaService"]
        S_PDF["PDFService (ReportLab)"]
        S_ETL["ETLExcelService (OpenPyXL)"]
        R_MAT --> S_MAT
        R_NOT --> S_PDF
        R_ETL --> S_ETL
    end

    I_REST --- R_AUTH & R_MAT & R_NOT & R_ETL

    I_SQL(("«interface»<br/>ISQLAlchemySession"))
    S_MAT & S_PDF & S_ETL -. "requiere (TCP/5432)" .-> I_SQL

    subgraph DB ["«component» Motor de Base de Datos"]
        PG[("PostgreSQL 16/17<br/>Esquema 3FN + Alembic")]
    end

    I_SQL --- PG
```

---

### 5. Diagrama de Despliegue (Local)
Topología física y entorno de ejecución en el equipo local (`AS-IS`) mediante Docker Compose, Vite y clientes nativos.

```mermaid
flowchart TB
    subgraph HOST ["«device» Equipo Local (Windows 11 / localhost)"]
        subgraph CLIENT_NODE ["«executionEnvironment» Cliente Navegador / App Nativa"]
            ART_HTML["«artifact» index.html + bundle.js (Vite :5173)"]
            ART_EXE["«artifact» Instalador_UCC_Academico_v2_Setup.exe (Tauri)"]
        end

        subgraph DOCKER_API ["«executionEnvironment» Contenedor Docker: ucc-backend"]
            ART_PY["«artifact» app/main.py (FastAPI + Uvicorn :8000)"]
        end

        subgraph DOCKER_DB ["«executionEnvironment» Contenedor Docker: ucc-postgres"]
            ART_PG["«artifact» PostgreSQL 16 Engine (:5432)"]
            VOL_DB[("«artifact» Volumen pgdata")]
            ART_PG --- VOL_DB
        end

        CLIENT_NODE -- "HTTP/REST + JWT<br/>Puerto 8000" --> DOCKER_API
        DOCKER_API -- "TCP / psycopg3<br/>Puerto 5432" --> DOCKER_DB
    end
```

---

### 6. Diagrama de Paquetes
Organización en capas lógicas del proyecto y sus relaciones de dependencia (`«import»` / `«access»`).

```mermaid
flowchart TD
    subgraph P_UI ["«package» frontend::src"]
        P_PAGES["«package» pages"]
        P_COMP["«package» components"]
        P_CTX["«package» context & api"]
        P_PAGES -. "«import»" .-> P_COMP
        P_PAGES -. "«import»" .-> P_CTX
    end

    subgraph P_BACK ["«package» backend::app"]
        P_ROUTERS["«package» routers<br/>(auth, catalogo, matricula, notas, reportes, etl_demo)"]
        P_SERVICES["«package» services<br/>(matricula_service, pdf_service, etl_excel_service)"]
        P_CORE["«package» core<br/>(config, security, horarios)"]
        P_DB["«package» db<br/>(models, session, seed)"]
        P_SCHEMAS["«package» schemas"]
    end

    P_CTX -. "«access» HTTP/REST" .-> P_ROUTERS
    P_ROUTERS -. "«import»" .-> P_SERVICES
    P_ROUTERS -. "«import»" .-> P_SCHEMAS
    P_ROUTERS -. "«import»" .-> P_CORE
    P_SERVICES -. "«import»" .-> P_DB
    P_SERVICES -. "«import»" .-> P_CORE
    P_DB -. "«import»" .-> P_CORE
```

---

### 7. Diagrama de Estructura Compuesta
Estructura interna del componente principal **`BackendAPI`** mostrando sus partes internas, conectores y puertos explícitos de entrada/salida.

```mermaid
flowchart LR
    P_IN["[Puerto: HTTP_In :8000]"]
    P_DB["[Puerto: SQL_Out :5432]"]
    P_FILE["[Puerto: File_Out PDF/XLSX]"]

    subgraph COMP ["«component» BackendAPI (FastAPI)"]
        JWT["part authGuard : SecurityMiddleware"]
        VAL["part horarioVal : HorariosEngine"]
        MAT["part matCtrl : MatriculaService"]
        PDF["part docGen : PDFService"]
        ORM["part repo : SQLAlchemySession"]

        JWT --> MAT
        MAT <--> VAL
        MAT --> ORM
        MAT --> PDF
        PDF --> ORM
    end

    P_IN <--> JWT
    ORM <--> P_DB
    PDF --> P_FILE
```

---

### 8. Diagrama de Perfiles
Extensión del metamodelo UML adaptada al dominio web de FastAPI + SQLAlchemy + React mediante estereotipos personalizados.

```mermaid
classDiagram
    class UML_Class {
        <<metaclass>>
    }
    class UML_Component {
        <<metaclass>>
    }
    class APIRouter {
        <<stereotype>>
        +String prefix
        +List tags
    }
    class DomainService {
        <<stereotype>>
        +bool transactional
    }
    class ORMEntity {
        <<stereotype>>
        +String tablename
        +String normalForm
    }
    class PydanticDTO {
        <<stereotype>>
        +bool from_attributes
    }
    class MultiPlatformUI {
        <<stereotype>>
        +String targets
    }

    APIRouter --|> UML_Class : extension
    DomainService --|> UML_Class : extension
    ORMEntity --|> UML_Class : extension
    PydanticDTO --|> UML_Class : extension
    MultiPlatformUI --|> UML_Component : extension
```

---

## 3. DIAGRAMAS UML DE COMPORTAMIENTO (7 DIAGRAMAS)

### 9. Diagrama de Casos de Uso
Límites del sistema, actores externos (`Estudiante`, `Docente`, `Administrador`) y relaciones (`«include»`, `«extend»`).

```mermaid
flowchart LR
    EST(["👤 Estudiante"])
    DOC(["👤 Docente"])
    ADM(["👤 Administrador"])

    subgraph SYS ["Sistema Universitario UCC v2.0"]
        UC_LOGIN(("Iniciar Sesión JWT"))
        UC_MAT(("Matricular Asignaturas"))
        UC_VAL(("Validar Créditos y Cruces"))
        UC_REC(("Descargar Recibo PDF"))
        UC_BOL(("Consultar Boletín y PPS"))
        UC_CAL(("Registrar Notas por Cortes"))
        UC_CAT(("Gestionar Catálogo Académico"))
        UC_ETL(("Importar / Exportar Excel ETL"))
        UC_DEMO(("Poblar 50+ Estudiantes / Vaciar BD"))

        UC_MAT -. "«include»" .-> UC_VAL
        UC_MAT -. "«include»" .-> UC_LOGIN
        UC_REC -. "«extend»" .-> UC_MAT
        UC_CAL -. "«include»" .-> UC_LOGIN
        UC_ETL -. "«include»" .-> UC_LOGIN
    end

    EST --> UC_LOGIN & UC_MAT & UC_REC & UC_BOL
    DOC --> UC_LOGIN & UC_CAL
    ADM --> UC_LOGIN & UC_CAT & UC_ETL & UC_DEMO
```

---

### 10. Diagrama de Actividades
Flujo de trabajo operativo del proceso de **Matrícula Inteligente** dividido en carriles (swimlanes) por actor/componente.

```mermaid
flowchart TD
    subgraph SW_EST ["Carril: Estudiante (UI)"]
        A1(["Inicio"]) --> A2["Seleccionar grupos de su Programa"]
        A2 --> A3["Enviar solicitud de matrícula"]
        A9["Visualizar horario y descargar Recibo PDF"] --> A10(["Fin"])
    end

    subgraph SW_API ["Carril: Backend FastAPI"]
        A4{"¿Créditos entre 6 y 19?"}
        A5{"¿Existen cruces de horario o materia repetida?"}
        A6["Mostrar error de validación"]
        A7["Ejecutar reserva atómica de cupos"]
    end

    subgraph SW_DB ["Carril: PostgreSQL"]
        A8["UPDATE grupos SET cupos_disponibles = cupos_disponibles - 1<br/>INSERT INTO matriculas"]
    end

    A3 --> A4
    A4 -- "No" --> A6 --> A2
    A4 -- "Sí" --> A5
    A5 -- "Sí" --> A6
    A5 -- "No" --> A7 --> A8 --> A9
```

---

### 11. Diagrama de Máquina de Estados
Ciclo de vida y transiciones de estado de la entidad principal **`Matricula`** y su relación con la evaluación (`Nota`).

```mermaid
stateDiagram-v2
    [*] --> Borrador : Estudiante selecciona grupos
    Borrador --> Activa : Confirmar matrícula [6 <= créditos <= 19 && sin cruces && cupos > 0] / Descontar cupo
    Borrador --> [*] : Descartar selección

    Activa --> Cancelada : Solicitar retiro [periodo abierto] / Liberar cupo en grupo
    Activa --> Finalizada : Cierre de periodo [3 cortes registrados] / Calcular definitiva y PPS

    Cancelada --> [*]
    Finalizada --> [*]
```

---

### 12. Diagrama de Secuencia
Intercambio ordenado temporalmente de mensajes en el flujo de **Registro de Matrícula** entre Navegador, Frontend, API FastAPI y PostgreSQL.

```mermaid
sequenceDiagram
    actor U as Usuario / Navegador
    participant FE as Frontend (React)
    participant API as Backend (FastAPI)
    participant DB as PostgreSQL 16

    U->>FE: Clic en "Confirmar Matrícula"
    FE->>API: POST /api/v1/matriculas (Bearer JWT + grupos[])
    activate API
    API->>API: Verificar JWT y rol Estudiante
    API->>DB: SELECT grupos + horarios_grupo WHERE id_grupo IN (...)
    DB-->>API: Registros de grupos y bloques horarios
    API->>API: Validar 6..19 créditos y cero cruces
    alt Validación exitosa
        API->>DB: BEGIN TRANSACTION
        API->>DB: UPDATE grupos SET cupos_disponibles = cupos_disponibles - 1 WHERE cupos_disponibles > 0
        API->>DB: INSERT INTO matriculas (...)
        DB-->>API: COMMIT OK
        API-->>FE: 201 Created (Recibo JSON)
        FE-->>U: Mostrar confirmación + botón Descargar PDF
    else Error de reglas o sin cupo
        API-->>FE: 400 Bad Request (Detalle del conflicto)
        FE-->>U: Mostrar alerta visual
    end
    deactivate API
```

---

### 13. Diagrama de Comunicación
Organización estructural de los objetos que colaboran en el **Registro de Calificaciones** con mensajería numerada secuencialmente.

```mermaid
flowchart LR
    DOC["docenteUI : PanelDocente"]
    CTRL["notasRouter : NotasRouter"]
    NOTA["notaObj : Nota"]
    DB["pgSession : Session"]

    DOC -- "1: PUT /notas/{id_matricula} (n1, n2, n3)" --> CTRL
    CTRL -- "1.1: validarRango(0.0..5.0)" --> NOTA
    CTRL -- "1.2: calcularDefinitiva(30%, 30%, 40%)" --> NOTA
    CTRL -- "1.3: commit(notaObj)" --> DB
    DB -. "1.4: OK" .-> CTRL
    CTRL -. "2: 200 OK (Nota actualizada + PPS)" .-> DOC
```

---

### 14. Diagrama de Temporización
Cambios de estado y restricciones de tiempo de respuesta en una transacción de matrícula típica (`t` en milisegundos).

```mermaid
gantt
    title Diagrama de Temporización — Transacción de Matrícula (Escala en ms)
    dateFormat X
    axisFormat %L ms

    section Frontend UI
    Inactivo / Selección          :a1, 0, 50
    Esperando API (Loading)       :active, a2, 50, 260
    Render Confirmación           :done, a3, 260, 300

    section FastAPI Backend
    Validación JWT + Reglas       :b1, 60, 120
    Transacción Atómica           :crit, b2, 120, 230
    Serialización JSON            :b3, 230, 255

    section PostgreSQL
    Lock + UPDATE Cupos + INSERT  :c1, 130, 220
```

---

### 15. Diagrama de Vista General de Interacciones
Encadenamiento global de marcos de interacción (`sd`) con rutas alternativas y decisiones del sistema académico completo.

```mermaid
flowchart TD
    START(("●")) --> SD1["<b>sd</b> Autenticación JWT<br/>(Usuario -> API -> PostgreSQL)"]
    SD1 --> DEC{"¿Rol del Usuario?"}

    DEC -- "Estudiante" --> SD2["<b>sd</b> Matrícula Inteligente<br/>(Selección + Cupos Atómicos)"]
    SD2 --> SD3["<b>sd</b> Consulta Boletín y PDF<br/>(ReportLab + Descarga)"]

    DEC -- "Docente" --> SD4["<b>sd</b> Registro de Notas<br/>(Cortes 30/30/40 + PPS)"]

    DEC -- "Administrador" --> SD5["<b>sd</b> Gestión Catálogo / ETL / Modo Demo<br/>(Seed 50+ Estudiantes / Excel)"]

    SD3 & SD4 & SD5 --> END(("◉"))
```
