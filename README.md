<div align="center">

# Sistema Universitario de Gestión

### Matrículas, oferta académica y calificaciones para la Universidad Cooperativa de Colombia

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-brightgreen?style=for-the-badge)](LICENSE)

**Proyecto académico · Ingeniería de Software · UCC Campus Cali**

[Probar versión web](https://sistemauniversitariodegestion.streamlit.app/) ·
[Descargar versión de escritorio](https://github.com/SlayerCampo/SistemaUniversitarioDeGestion/releases)

</div>

## Descripción

El Sistema Universitario de Gestión es una solución académica desarrollada en Python para centralizar procesos de matrícula, consulta de asignaturas, control de cupos, validación de horarios y gestión de calificaciones.

El proyecto ofrece dos formas de uso:

- **Aplicación web responsiva**, construida con Streamlit y accesible desde computadores, tabletas y celulares.
- **Aplicación de escritorio para Windows**, construida con CustomTkinter y distribuida mediante instalador.

Ambas versiones comparten el catálogo académico, las reglas de negocio y la generación de reportes PDF. La persistencia local utiliza archivos Excel, lo que facilita la demostración, el respaldo y la carga masiva de información sin configurar un servidor de base de datos.

> **Contexto:** este repositorio corresponde a un proyecto académico de la Universidad Cooperativa de Colombia, Sede Cali. No representa un sistema oficial de producción de la institución.

## Funcionalidades principales

### Matrícula académica

- Consulta de estudiantes, programas y asignaturas.
- Selección de grupos y horarios por programa académico.
- Carrito de matrícula con validación de cupos y cruces de horario.
- Regla de carga académica entre **6 y 19 créditos**.
- Confirmación y generación de recibo de matrícula en PDF.
- Acceso de demostración con clave `1234`.

### Calificaciones y reportes

- Registro de notas por tres cortes: **30 %, 30 % y 40 %**.
- Cálculo del promedio ponderado semestral.
- Panel docente para calificación individual o por grupo.
- Generación de boletines en PDF.

### Administración y datos

- Gestión de facultades, programas, materias, estudiantes y matrículas.
- Importación y exportación mediante Excel.
- Generación de datos de demostración.
- Exploración de registros y herramientas de respaldo.
- Esquema SQL de referencia en [`schema_universidad.sql`](1_Version_Escritorio_Avanzada/schema_universidad.sql).

## Versiones disponibles

| Versión | Tecnología | Uso recomendado |
| --- | --- | --- |
| Web | Streamlit, pandas, OpenPyXL y ReportLab | Evaluación rápida y acceso desde navegador |
| Escritorio | CustomTkinter, OpenPyXL y ReportLab | Uso local en Windows y demostración sin navegador |

### Versión web en línea

Accede directamente a [sistemauniversitariodegestion.streamlit.app](https://sistemauniversitariodegestion.streamlit.app/).

La aplicación puede iniciar con la base de datos vacía. En ese caso, el módulo **Administración** permite cargar información o generar datos de demostración.

### Versión de escritorio

El instalador para Windows está disponible en [Releases](https://github.com/SlayerCampo/SistemaUniversitarioDeGestion/releases). Como el ejecutable no utiliza un certificado comercial de firma de código, Windows SmartScreen puede mostrar una advertencia preventiva. También es posible ejecutar el proyecto desde el código fuente siguiendo las instrucciones de instalación local.

## Inicio rápido

### Requisitos

- Python 3.9 o superior.
- Windows para la aplicación de escritorio.
- Conexión a Internet únicamente para usar la versión web publicada o descargar el repositorio.

### Instalación

```bash
git clone https://github.com/SlayerCampo/SistemaUniversitarioDeGestion.git
cd SistemaUniversitarioDeGestion
python -m venv .venv
```

Activa el entorno virtual:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Instala las dependencias:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Ejecución

Desde Windows también puedes utilizar `Ejecutar_Escritorio.bat` o `Ejecutar_Web.bat`.

```bash
# Aplicación web
python -m streamlit run "2_Version_Web_Desplegable/app.py"

# Aplicación de escritorio
python "1_Version_Escritorio_Avanzada/main.py"
```

Para crear un acceso directo de la versión de escritorio, ejecuta `Crear_Acceso_Directo.bat` dentro de `1_Version_Escritorio_Avanzada`.

## Flujo de demostración recomendado

1. Abre la [versión web](https://sistemauniversitariodegestion.streamlit.app/) o ejecuta la aplicación localmente.
2. Revisa los indicadores de la página principal.
3. En **Administración**, carga datos o genera el archivo de demostración.
4. En **Matrícula**, selecciona un estudiante y prueba la validación de créditos, cupos y horarios.
5. Consulta el **Boletín** y descarga el PDF.
6. En el **Panel Docente**, registra notas y observa el cálculo del promedio.

La clave `1234` corresponde al modo de demostración incluido en la aplicación. No debe utilizarse como mecanismo de autenticación para un entorno real.

## Estructura del repositorio

```text
SistemaUniversitarioDeGestion/
├── 1_Version_Escritorio_Avanzada/
│   ├── core/                 # Reglas de negocio y validaciones
│   ├── data/                 # Persistencia, catálogo y carga de datos
│   ├── reports/              # Reportes PDF
│   ├── ui/                   # Vistas de la aplicación de escritorio
│   ├── main.py               # Punto de entrada
│   └── schema_universidad.sql
├── 2_Version_Web_Desplegable/
│   ├── database/             # Persistencia y estilos web
│   ├── pages/                # Matrícula, notas, docentes y administración
│   └── app.py                # Punto de entrada web
├── Ejecutar_Escritorio.bat
├── Ejecutar_Web.bat
├── requirements.txt
├── LICENSE
└── README.md
```

## Equipo

- **Alejandro Campo Solarte** — ID Timonel: 938203
- **Juan Esteban Cardona Calambas** — ID Timonel: 939422
- **Diego Fernando Gómez Rivera** — ID Timonel: 937804

**Institución:** Universidad Cooperativa de Colombia · Sede Cali
**Programa:** Ingeniería de Sistemas
**Asignatura:** Ingeniería de Software

## Alcance y consideraciones

- La persistencia basada en Excel está pensada para demostración y uso local; no sustituye una base de datos institucional multiusuario.
- Los datos incluidos o generados son de demostración.
- La clave de demostración y los datos simulados no deben reutilizarse en producción.
- Antes de distribuir el instalador, verifica su procedencia y el contenido de la versión publicada.

## Licencia

Este proyecto se distribuye bajo la [Licencia MIT](LICENSE).

<div align="center">

**Universidad Cooperativa de Colombia — Campus Cali · 2026**

</div>
