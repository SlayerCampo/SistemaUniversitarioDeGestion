export type RolUsuario = "Administrador" | "Profesor" | "Estudiante";

export interface UserInfo {
  usuario: string;
  rol: RolUsuario;
  nombre_completo: string;
  documento_asociado: string;
  es_demo: boolean;
  id_programa: string | null;
  nombre_programa: string | null;
  semestre: number | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface HealthStatus {
  status: string;
  database: string;
  version: string;
  demo_mode: boolean;
}

export interface KPIs {
  facultades: number;
  programas: number;
  asignaturas: number;
  grupos: number;
  estudiantes: number;
  matriculas_activas: number;
  promedio_global: number;
  periodo_activo: string;
  demo_mode: boolean;
}

export interface Facultad {
  id_facultad: string;
  nombre_facultad: string;
  decano: string;
}

export interface Programa {
  id_programa: string;
  nombre_programa: string;
  id_facultad: string;
  nombre_facultad: string;
  semestres_duracion: number;
}

export interface HorarioBloque {
  dia_semana: number;
  dia_nombre: string;
  hora_inicio: number;
  hora_fin: number;
}

export interface Grupo {
  id_grupo: string;
  id_asignatura: string;
  nombre_curso: string;
  creditos: number;
  id_programa: string;
  nombre_programa: string;
  id_periodo: string;
  docente: string;
  cupos_totales: number;
  cupos_disponibles: number;
  horario_texto: string;
  horarios: HorarioBloque[];
}

export interface MatriculaInscrita extends Grupo {
  id_matricula: string;
  fecha_matricula: string;
  estado: string;
}

export interface OfertaAsignatura {
  id_asignatura: string;
  nombre_curso: string;
  creditos: number;
  grupos: Grupo[];
}

export interface ResumenMatricula {
  estudiante: {
    id_estudiante: string;
    nombre_completo: string;
    correo: string;
    semestre: number;
    id_programa: string;
    nombre_programa: string;
  };
  periodo: string;
  reglas: {
    creditos_minimos: number;
    creditos_maximos: number;
    almuerzo: string;
  };
  creditos_inscritos: number;
  inscritas: MatriculaInscrita[];
  oferta_disponible: OfertaAsignatura[];
}

export interface Estudiante {
  id_estudiante: string;
  nombre: string;
  apellidos: string;
  nombre_completo: string;
  correo: string;
  telefono: string;
  semestre: number;
  id_programa: string;
  nombre_programa: string;
}

export interface BoletinAsignatura {
  id_matricula: string;
  id_grupo: string;
  id_asignatura: string;
  nombre_curso: string;
  docente: string;
  creditos: number;
  nota1: number | null;
  nota2: number | null;
  nota3: number | null;
  definitiva: number | null;
  estado: "Aprobado" | "Reprobado" | "Sin calificar";
}

export interface BoletinResponse {
  estudiante: {
    id_estudiante: string;
    nombre_completo: string;
    semestre: number;
    id_programa: string;
    nombre_programa: string;
  };
  periodo: string;
  resumen: {
    pps: number;
    materias_activas: number;
    materias_aprobadas: number;
    creditos_inscritos: number;
    creditos_aprobados: number;
  };
  asignaturas: BoletinAsignatura[];
}

export interface PlanillaEstudiante {
  id_matricula: string;
  id_estudiante: string;
  nombre_completo: string;
  correo: string;
  nota1: number;
  nota2: number;
  nota3: number;
  definitiva: number;
  estado: string;
}

export interface PlanillaGrupoResponse {
  id_grupo: string;
  nombre_curso: string;
  creditos: number;
  docente: string;
  id_programa: string;
  nombre_programa: string;
  estudiantes: PlanillaEstudiante[];
}

export interface AnaliticaResponse {
  estudiantes_por_programa: { id_programa: string; programa: string; estudiantes: number }[];
  ocupacion_por_programa: {
    id_programa: string;
    programa: string;
    cupos_totales: number;
    cupos_ocupados: number;
    cupos_disponibles: number;
  }[];
  distribucion_notas: { estado: string; cantidad: number }[];
}

export interface DemoPerfilesResponse {
  demo_mode: boolean;
  cuentas_base: { perfil: string; rol: string; etiqueta: string; detalle: string }[];
  estudiantes: { perfil: string; rol: string; etiqueta: string; detalle: string }[];
}
