import type {
  AnaliticaResponse,
  BoletinResponse,
  DemoPerfilesResponse,
  Estudiante,
  Facultad,
  Grupo,
  HealthStatus,
  KPIs,
  PlanillaGrupoResponse,
  Programa,
  ResumenMatricula,
  TokenResponse,
  UserInfo,
} from "@/types/api";
import { downloadBinaryFile } from "@/lib/platform";

const API_URL_STORAGE_KEY = "ucc_api_base_url";
const TOKEN_STORAGE_KEY = "ucc_jwt_token";

export const DEFAULT_API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1").replace(/\/+$/, "");
export const GITHUB_RELEASES_URL =
  import.meta.env.VITE_GITHUB_RELEASES_URL || "https://github.com/SlayerCampo/SistemaUniversitarioDeGestion/releases";

export function getApiBaseUrl(): string {
  const custom = localStorage.getItem(API_URL_STORAGE_KEY);
  return (custom || DEFAULT_API_URL).replace(/\/+$/, "");
}

export function setApiBaseUrl(url: string): void {
  const cleaned = url.trim().replace(/\/+$/, "");
  if (!cleaned) {
    localStorage.removeItem(API_URL_STORAGE_KEY);
  } else {
    localStorage.setItem(API_URL_STORAGE_KEY, cleaned);
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const base = getApiBaseUrl();
  const token = getStoredToken();
  const headers = new Headers(init.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${base}${path}`, { ...init, headers });
  if (!res.ok) {
    let msg = `Error ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || data.message || msg;
    } catch {
      // ignore json parse error
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

async function downloadEndpoint(path: string, filename: string): Promise<void> {
  const base = getApiBaseUrl();
  const token = getStoredToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${base}${path}`, { headers });
  if (!res.ok) {
    let msg = `No se pudo generar el archivo (${res.status})`;
    try {
      const data = await res.json();
      msg = data.detail || msg;
    } catch {
      // ignore
    }
    throw new Error(msg);
  }
  const blob = await res.blob();
  await downloadBinaryFile(blob, filename);
}

export const api = {
  async health(): Promise<HealthStatus> {
    const base = getApiBaseUrl().replace(/\/api\/v1$/, "");
    const res = await fetch(`${base}/health`);
    if (!res.ok) throw new Error("Servidor no disponible");
    return res.json();
  },

  // Auth
  login: (usuario: string, password: string) =>
    request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify({ usuario, password }) }),
  me: () => request<UserInfo>("/auth/me"),
  demoPerfiles: () => request<DemoPerfilesResponse>("/auth/demo-perfiles"),
  demoSwitch: (perfil: string) =>
    request<TokenResponse>("/auth/demo-switch", { method: "POST", body: JSON.stringify({ perfil }) }),

  // Catálogo y KPIs
  kpis: () => request<KPIs>("/catalogo/kpis"),
  facultades: () => request<Facultad[]>("/catalogo/facultades"),
  crearFacultad: (body: { id_facultad: string; nombre_facultad: string; decano: string }) =>
    request<Facultad>("/catalogo/facultades", { method: "POST", body: JSON.stringify(body) }),
  eliminarFacultad: (id: string) => request<{ mensaje: string }>(`/catalogo/facultades/${encodeURIComponent(id)}`, { method: "DELETE" }),

  programas: () => request<Programa[]>("/catalogo/programas"),
  crearPrograma: (body: { id_programa: string; nombre_programa: string; id_facultad: string; semestres_duracion: number }) =>
    request<Programa>("/catalogo/programas", { method: "POST", body: JSON.stringify(body) }),
  eliminarPrograma: (id: string) => request<{ mensaje: string }>(`/catalogo/programas/${encodeURIComponent(id)}`, { method: "DELETE" }),

  grupos: (params?: { id_programa?: string; search?: string; id_periodo?: string }) => {
    const qs = new URLSearchParams();
    if (params?.id_programa) qs.set("id_programa", params.id_programa);
    if (params?.search) qs.set("search", params.search);
    if (params?.id_periodo) qs.set("id_periodo", params.id_periodo);
    const q = qs.toString();
    return request<Grupo[]>(`/catalogo/grupos${q ? `?${q}` : ""}`);
  },
  crearGrupo: (body: {
    id_grupo: string;
    id_asignatura?: string;
    nombre_curso: string;
    creditos: number;
    id_programa: string;
    docente: string;
    cupos_totales: number;
    horarios: { dia_semana: number; hora_inicio: number; hora_fin: number }[];
  }) => request<Grupo>("/catalogo/grupos", { method: "POST", body: JSON.stringify(body) }),
  eliminarGrupo: (id: string) => request<{ mensaje: string }>(`/catalogo/grupos/${encodeURIComponent(id)}`, { method: "DELETE" }),

  estudiantes: (params?: { id_programa?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.id_programa) qs.set("id_programa", params.id_programa);
    if (params?.search) qs.set("search", params.search);
    const q = qs.toString();
    return request<Estudiante[]>(`/catalogo/estudiantes${q ? `?${q}` : ""}`);
  },
  crearEstudiante: (body: {
    id_estudiante: string;
    nombre: string;
    apellidos: string;
    correo: string;
    telefono: string;
    semestre: number;
    id_programa: string;
    password: string;
  }) => request("/catalogo/estudiantes", { method: "POST", body: JSON.stringify(body) }),
  eliminarEstudiante: (id: string) => request<{ mensaje: string }>(`/catalogo/estudiantes/${encodeURIComponent(id)}`, { method: "DELETE" }),

  analitica: () => request<AnaliticaResponse>("/catalogo/analitica"),

  // Matrícula
  resumenMatricula: (idEstudiante: string, periodo = "2026-2") =>
    request<ResumenMatricula>(`/matricula/resumen/${encodeURIComponent(idEstudiante)}?periodo=${encodeURIComponent(periodo)}`),
  validarCarrito: (id_estudiante: string, id_periodo: string, grupos_ids: string[]) =>
    request<{ valido: boolean; errores: string[]; creditos_inscritos: number; creditos_carrito: number; creditos_totales: number }>(
      "/matricula/validar",
      { method: "POST", body: JSON.stringify({ id_estudiante, id_periodo, grupos_ids }) }
    ),
  confirmarMatricula: (id_estudiante: string, id_periodo: string, grupos_ids: string[]) =>
    request<{ mensaje: string; matriculas_creadas: string[]; creditos_totales: number }>("/matricula/confirmar", {
      method: "POST",
      body: JSON.stringify({ id_estudiante, id_periodo, grupos_ids }),
    }),
  retirarMatricula: (idMatricula: string) =>
    request<{ mensaje: string }>(`/matricula/retirar/${encodeURIComponent(idMatricula)}`, { method: "POST" }),

  // Notas y Docente
  boletin: (idEstudiante: string, periodo = "2026-2") =>
    request<BoletinResponse>(`/notas/boletin/${encodeURIComponent(idEstudiante)}?periodo=${encodeURIComponent(periodo)}`),
  planillaGrupo: (idGrupo: string) => request<PlanillaGrupoResponse>(`/notas/planilla/${encodeURIComponent(idGrupo)}`),
  guardarCalificaciones: (calificaciones: { id_matricula: string; nota1: number; nota2: number; nota3: number }[]) =>
    request<{ mensaje: string; actualizadas: number }>("/notas/calificar", {
      method: "PUT",
      body: JSON.stringify({ calificaciones }),
    }),

  // PDFs
  descargarPdfMatricula: (idEstudiante: string, periodo = "2026-2") =>
    downloadEndpoint(
      `/reportes/matricula/${encodeURIComponent(idEstudiante)}/pdf?periodo=${encodeURIComponent(periodo)}`,
      `Recibo_Matricula_${idEstudiante}.pdf`
    ),
  descargarPdfBoletin: (idEstudiante: string, periodo = "2026-2") =>
    downloadEndpoint(
      `/reportes/boletin/${encodeURIComponent(idEstudiante)}/pdf?periodo=${encodeURIComponent(periodo)}`,
      `Boletin_Notas_${idEstudiante}.pdf`
    ),

  // ETL y Demo
  descargarExcelSimulacion: () => downloadEndpoint("/etl/generar-simulacion", "Universidad_50_Estudiantes_UCC.xlsx"),
  exportarSabanaExcel: () => downloadEndpoint("/etl/exportar-sabana", "Sabana_Academica_UCC_Postgres.xlsx"),
  importarExcel: (file: File) => {
    const fd = new FormData();
    fd.append("archivo", file);
    return request<{ mensaje: string; insertados: Record<string, number>; duplicados: number; errores: string[] }>(
      "/etl/importar",
      { method: "POST", body: fd }
    );
  },
  demoPoblar: () => request<{ mensaje: string; resumen: Record<string, number> }>("/demo/poblar", { method: "POST" }),
  demoVaciar: (confirmacion: string) =>
    request<{ mensaje: string }>("/demo/vaciar", { method: "POST", body: JSON.stringify({ confirmacion }) }),
};
