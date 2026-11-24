import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  BarChart3,
  BookOpen,
  Building2,
  Database,
  Download,
  FileSpreadsheet,
  Plus,
  Trash2,
  Upload,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { AnaliticaResponse, Estudiante, Facultad, Grupo, Programa } from "@/types/api";
import { Badge, Button, Card, Field, Input, Select, StepHeader } from "@/components/ui/Primitives";

const INICIOS_POR_CREDITO: Record<number, number[]> = {
  2: [6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20],
  3: [6, 7, 8, 9, 10, 14, 15, 16, 17, 18, 19],
  4: [6, 7, 8, 9, 14, 15, 16, 17, 18],
};

const PIE_COLORS = ["#15803D", "#DC2626", "#D97706"];

export function AdminPage() {
  const { dataVersion, bumpDataVersion } = useAuth();
  const [tab, setTab] = useState<"etl" | "estructura" | "oferta" | "explorador" | "analitica">("etl");

  const [facultades, setFacultades] = useState<Facultad[]>([]);
  const [programas, setProgramas] = useState<Programa[]>([]);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [estudiantes, setEstudiantes] = useState<Estudiante[]>([]);
  const [analitica, setAnalitica] = useState<AnaliticaResponse | null>(null);

  // Forms
  const [facForm, setFacForm] = useState({ id_facultad: "", nombre_facultad: "", decano: "" });
  const [progForm, setProgForm] = useState({ id_programa: "", nombre_programa: "", id_facultad: "", semestres_duracion: 10 });
  const [grupoForm, setGrupoForm] = useState({
    id_grupo: "",
    nombre_curso: "",
    creditos: 3,
    id_programa: "",
    docente: "",
    cupos_totales: 30,
    dia_semana: 1,
    hora_inicio: 8,
  });
  const [estForm, setEstForm] = useState({
    id_estudiante: "",
    nombre: "",
    apellidos: "",
    correo: "",
    telefono: "",
    semestre: 1,
    id_programa: "",
    password: "1234",
  });

  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [expSearch, setExpSearch] = useState("");
  const [expTabla, setExpTabla] = useState<"estudiantes" | "grupos" | "programas" | "facultades">("estudiantes");

  useEffect(() => {
    Promise.all([api.facultades(), api.programas(), api.grupos(), api.estudiantes(), api.analitica()])
      .then(([f, p, g, e, a]) => {
        setFacultades(f);
        setProgramas(p);
        setGrupos(g);
        setEstudiantes(e);
        setAnalitica(a);
        if (f.length > 0 && !progForm.id_facultad) setProgForm((x) => ({ ...x, id_facultad: f[0].id_facultad }));
        if (p.length > 0) {
          if (!grupoForm.id_programa) setGrupoForm((x) => ({ ...x, id_programa: p[0].id_programa }));
          if (!estForm.id_programa) setEstForm((x) => ({ ...x, id_programa: p[0].id_programa }));
        }
      })
      .catch((e) => toast.error((e as Error).message));
  }, [dataVersion]);

  const handleImportarExcel = async () => {
    if (!excelFile) {
      toast.error("Selecciona primero un archivo .xlsx.");
      return;
    }
    setBusy(true);
    try {
      const res = await api.importarExcel(excelFile);
      toast.success(
        `Importado a PostgreSQL: ${res.insertados.Estudiantes} estudiantes, ${res.insertados.Grupos} grupos (duplicados omitidos: ${res.duplicados}).`
      );
      setExcelFile(null);
      bumpDataVersion();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const crearFacultad = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.crearFacultad(facForm);
      toast.success("Facultad registrada en PostgreSQL.");
      setFacForm({ id_facultad: "", nombre_facultad: "", decano: "" });
      bumpDataVersion();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const crearPrograma = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.crearPrograma(progForm);
      toast.success("Programa académico registrado.");
      setProgForm((prev) => ({ ...prev, id_programa: "", nombre_programa: "" }));
      bumpDataVersion();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const crearGrupo = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.crearGrupo({
        id_grupo: grupoForm.id_grupo,
        nombre_curso: grupoForm.nombre_curso,
        creditos: grupoForm.creditos,
        id_programa: grupoForm.id_programa,
        docente: grupoForm.docente,
        cupos_totales: grupoForm.cupos_totales,
        horarios: [
          {
            dia_semana: grupoForm.dia_semana,
            hora_inicio: grupoForm.hora_inicio,
            hora_fin: grupoForm.hora_inicio + grupoForm.creditos,
          },
        ],
      });
      toast.success("Grupo y horario validados y guardados en PostgreSQL.");
      setGrupoForm((prev) => ({ ...prev, id_grupo: "", nombre_curso: "" }));
      bumpDataVersion();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const crearEstudiante = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.crearEstudiante(estForm);
      toast.success("Estudiante y cuenta bcrypt registrados en PostgreSQL.");
      setEstForm((prev) => ({ ...prev, id_estudiante: "", nombre: "", apellidos: "", correo: "", telefono: "" }));
      bumpDataVersion();
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const iniciosDisp = INICIOS_POR_CREDITO[grupoForm.creditos] || INICIOS_POR_CREDITO[3];

  return (
    <div className="space-y-6">
      {/* SUB-NAVEGACIÓN EN PESTAÑAS */}
      <div className="flex overflow-x-auto gap-2 pb-1">
        {[
          { id: "etl", label: "Centro ETL Excel", icon: FileSpreadsheet },
          { id: "estructura", label: "Facultades y Programas", icon: Building2 },
          { id: "oferta", label: "Grupos y Estudiantes", icon: BookOpen },
          { id: "explorador", label: "Explorador PostgreSQL", icon: Database },
          { id: "analitica", label: "Analítica", icon: BarChart3 },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as typeof tab)}
            className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold whitespace-nowrap transition border ${
              tab === t.id
                ? "bg-[#1F6AA5] text-white border-[#1F6AA5] shadow-sm"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* TAB 1: CENTRO ETL EXCEL */}
      {tab === "etl" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <Card className="p-5 space-y-4">
            <StepHeader step="PASO 1" title="Generar Excel de 50+ Estudiantes" />
            <p className="text-xs text-slate-600 leading-relaxed">
              Genera y descarga el libro <code>.xlsx</code> completo (5 Facultades, 8 Programas, 240 Grupos y 50
              Estudiantes) <b>sin modificar</b> tu base de datos PostgreSQL activa.
            </p>
            <Button
              onClick={async () => {
                try {
                  await api.descargarExcelSimulacion();
                  toast.success("Archivo Excel de simulación descargado.");
                } catch (e) {
                  toast.error((e as Error).message);
                }
              }}
              className="w-full"
            >
              <Download className="w-4 h-4" />
              Descargar Excel 50+ (.xlsx)
            </Button>
          </Card>

          <Card className="p-5 space-y-4">
            <StepHeader step="PASO 2" title="Importar Excel a PostgreSQL" />
            <p className="text-xs text-slate-600 leading-relaxed">
              Carga cualquier plantilla o el archivo generado en el Paso 1. Se normaliza automáticamente a las 10 tablas
              relacionales sin duplicar registros.
            </p>
            <input
              type="file"
              accept=".xlsx"
              onChange={(e) => setExcelFile(e.target.files?.[0] || null)}
              className="block w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-sky-50 file:text-[#154B75] hover:file:bg-sky-100"
            />
            <Button variant="success" onClick={handleImportarExcel} disabled={busy || !excelFile} className="w-full">
              <Upload className="w-4 h-4" />
              {busy ? "Importando a PostgreSQL..." : "Importar Archivo .xlsx"}
            </Button>
          </Card>

          <Card className="p-5 space-y-4">
            <StepHeader step="PASO 3" title="Exportar Sábana Consolidada" />
            <p className="text-xs text-slate-600 leading-relaxed">
              Exporta en tiempo real el estado completo de tu base de datos PostgreSQL a un archivo Excel corporativo
              para auditoría o respaldo.
            </p>
            <Button
              variant="outline"
              onClick={async () => {
                try {
                  await api.exportarSabanaExcel();
                  toast.success("Sábana académica exportada.");
                } catch (e) {
                  toast.error((e as Error).message);
                }
              }}
              className="w-full"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-700" />
              Exportar Sábana (.xlsx)
            </Button>
          </Card>
        </div>
      )}

      {/* TAB 2: FACULTADES Y PROGRAMAS */}
      {tab === "estructura" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-5 sm:p-6 space-y-4">
            <StepHeader step="NUEVA" title="Registrar Facultad" />
            <form onSubmit={crearFacultad} className="space-y-3.5">
              <Field label="Código de Facultad">
                <Input
                  required
                  value={facForm.id_facultad}
                  onChange={(e) => setFacForm({ ...facForm, id_facultad: e.target.value })}
                  placeholder="Ej: F06"
                />
              </Field>
              <Field label="Nombre de la Facultad">
                <Input
                  required
                  value={facForm.nombre_facultad}
                  onChange={(e) => setFacForm({ ...facForm, nombre_facultad: e.target.value })}
                  placeholder="Ej: Facultad de Arquitectura y Diseño"
                />
              </Field>
              <Field label="Decano(a)">
                <Input
                  value={facForm.decano}
                  onChange={(e) => setFacForm({ ...facForm, decano: e.target.value })}
                  placeholder="Ej: Dra. Sofía Benavides"
                />
              </Field>
              <Button type="submit" disabled={busy} className="w-full">
                <Plus className="w-4 h-4" /> Guardar Facultad
              </Button>
            </form>
          </Card>

          <Card className="p-5 sm:p-6 space-y-4">
            <StepHeader step="NUEVO" title="Registrar Programa Académico" />
            <form onSubmit={crearPrograma} className="space-y-3.5">
              <Field label="Código del Programa">
                <Input
                  required
                  value={progForm.id_programa}
                  onChange={(e) => setProgForm({ ...progForm, id_programa: e.target.value })}
                  placeholder="Ej: P09"
                />
              </Field>
              <Field label="Nombre del Programa">
                <Input
                  required
                  value={progForm.nombre_programa}
                  onChange={(e) => setProgForm({ ...progForm, nombre_programa: e.target.value })}
                  placeholder="Ej: Arquitectura"
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Facultad">
                  <Select
                    required
                    value={progForm.id_facultad}
                    onChange={(e) => setProgForm({ ...progForm, id_facultad: e.target.value })}
                  >
                    {facultades.map((f) => (
                      <option key={f.id_facultad} value={f.id_facultad}>
                        {f.id_facultad} — {f.nombre_facultad}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Duración (Semestres)">
                  <Input
                    type="number"
                    min={1}
                    max={14}
                    value={progForm.semestres_duracion}
                    onChange={(e) => setProgForm({ ...progForm, semestres_duracion: Number(e.target.value) })}
                  />
                </Field>
              </div>
              <Button type="submit" disabled={busy || facultades.length === 0} className="w-full">
                <Plus className="w-4 h-4" /> Guardar Programa
              </Button>
            </form>
          </Card>
        </div>
      )}

      {/* TAB 3: GRUPOS Y ESTUDIANTES */}
      {tab === "oferta" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-5 sm:p-6 space-y-4">
            <StepHeader step="OFERTA" title="Registrar Grupo y Horario (Sin Almuerzo 13–14h)" />
            <form onSubmit={crearGrupo} className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Código del Grupo">
                  <Input
                    required
                    value={grupoForm.id_grupo}
                    onChange={(e) => setGrupoForm({ ...grupoForm, id_grupo: e.target.value })}
                    placeholder="Ej: SIS201-G1"
                  />
                </Field>
                <Field label="Programa Académico">
                  <Select
                    value={grupoForm.id_programa}
                    onChange={(e) => setGrupoForm({ ...grupoForm, id_programa: e.target.value })}
                  >
                    {programas.map((p) => (
                      <option key={p.id_programa} value={p.id_programa}>
                        {p.id_programa} — {p.nombre_programa}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <Field label="Nombre de la Asignatura">
                <Input
                  required
                  value={grupoForm.nombre_curso}
                  onChange={(e) => setGrupoForm({ ...grupoForm, nombre_curso: e.target.value })}
                  placeholder="Ej: Computación en la Nube"
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Docente Titular">
                  <Input
                    required
                    value={grupoForm.docente}
                    onChange={(e) => setGrupoForm({ ...grupoForm, docente: e.target.value })}
                    placeholder="Ej: Ing. Carlos Pérez"
                  />
                </Field>
                <Field label="Cupos Totales">
                  <Input
                    type="number"
                    min={1}
                    max={200}
                    value={grupoForm.cupos_totales}
                    onChange={(e) => setGrupoForm({ ...grupoForm, cupos_totales: Number(e.target.value) })}
                  />
                </Field>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <Field label="Créditos (Horas)">
                  <Select
                    value={grupoForm.creditos}
                    onChange={(e) => {
                      const c = Number(e.target.value);
                      const valid = INICIOS_POR_CREDITO[c] || [8];
                      setGrupoForm({ ...grupoForm, creditos: c, hora_inicio: valid[0] });
                    }}
                  >
                    <option value={2}>2 Cr. (2h)</option>
                    <option value={3}>3 Cr. (3h)</option>
                    <option value={4}>4 Cr. (4h)</option>
                  </Select>
                </Field>
                <Field label="Día">
                  <Select
                    value={grupoForm.dia_semana}
                    onChange={(e) => setGrupoForm({ ...grupoForm, dia_semana: Number(e.target.value) })}
                  >
                    <option value={1}>Lunes</option>
                    <option value={2}>Martes</option>
                    <option value={3}>Miércoles</option>
                    <option value={4}>Jueves</option>
                    <option value={5}>Viernes</option>
                    <option value={6}>Sábado</option>
                  </Select>
                </Field>
                <Field label="Franja Válida">
                  <Select
                    value={grupoForm.hora_inicio}
                    onChange={(e) => setGrupoForm({ ...grupoForm, hora_inicio: Number(e.target.value) })}
                  >
                    {iniciosDisp.map((h) => (
                      <option key={h} value={h}>
                        {String(h).padStart(2, "0")}:00 – {String(h + grupoForm.creditos).padStart(2, "0")}:00
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <Button type="submit" disabled={busy || programas.length === 0} className="w-full">
                <Plus className="w-4 h-4" /> Registrar Grupo en PostgreSQL
              </Button>
            </form>
          </Card>

          <Card className="p-5 sm:p-6 space-y-4">
            <StepHeader step="NUEVO" title="Registrar Estudiante (Cuenta bcrypt)" />
            <form onSubmit={crearEstudiante} className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <Field label="ID Estudiante (Sintético)">
                  <Input
                    required
                    value={estForm.id_estudiante}
                    onChange={(e) => setEstForm({ ...estForm, id_estudiante: e.target.value })}
                    placeholder="Ej: 1099"
                  />
                </Field>
                <Field label="Programa">
                  <Select
                    value={estForm.id_programa}
                    onChange={(e) => setEstForm({ ...estForm, id_programa: e.target.value })}
                  >
                    {programas.map((p) => (
                      <option key={p.id_programa} value={p.id_programa}>
                        {p.id_programa} — {p.nombre_programa}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Nombres">
                  <Input
                    required
                    value={estForm.nombre}
                    onChange={(e) => setEstForm({ ...estForm, nombre: e.target.value })}
                    placeholder="Ej: Valentina"
                  />
                </Field>
                <Field label="Apellidos">
                  <Input
                    required
                    value={estForm.apellidos}
                    onChange={(e) => setEstForm({ ...estForm, apellidos: e.target.value })}
                    placeholder="Ej: Restrepo Ortiz"
                  />
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Correo Institucional">
                  <Input
                    required
                    type="email"
                    value={estForm.correo}
                    onChange={(e) => setEstForm({ ...estForm, correo: e.target.value })}
                    placeholder="Ej: valentina@campusucc.edu.co"
                  />
                </Field>
                <Field label="Teléfono">
                  <Input
                    required
                    value={estForm.telefono}
                    onChange={(e) => setEstForm({ ...estForm, telefono: e.target.value })}
                    placeholder="Ej: 3150001122"
                  />
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Semestre">
                  <Input
                    type="number"
                    min={1}
                    max={14}
                    value={estForm.semestre}
                    onChange={(e) => setEstForm({ ...estForm, semestre: Number(e.target.value) })}
                  />
                </Field>
                <Field label="Contraseña Inicial">
                  <Input
                    required
                    value={estForm.password}
                    onChange={(e) => setEstForm({ ...estForm, password: e.target.value })}
                    placeholder="Ej: 1234"
                  />
                </Field>
              </div>
              <Button type="submit" disabled={busy || programas.length === 0} className="w-full">
                <Plus className="w-4 h-4" /> Registrar Estudiante
              </Button>
            </form>
          </Card>
        </div>
      )}

      {/* TAB 4: EXPLORADOR POSTGRESQL */}
      {tab === "explorador" && (
        <Card className="p-5 sm:p-6 space-y-4">
          <StepHeader
            step="POSTGRESQL"
            title="Explorador en Vivo de Tablas Relacionales"
            action={
              <div className="flex gap-2">
                <Select value={expTabla} onChange={(e) => setExpTabla(e.target.value as typeof expTabla)} className="w-40">
                  <option value="estudiantes">Estudiantes ({estudiantes.length})</option>
                  <option value="grupos">Grupos ({grupos.length})</option>
                  <option value="programas">Programas ({programas.length})</option>
                  <option value="facultades">Facultades ({facultades.length})</option>
                </Select>
              </div>
            }
          />
          <Input
            value={expSearch}
            onChange={(e) => setExpSearch(e.target.value)}
            placeholder="Filtrar registros en vivo..."
          />

          <div className="overflow-x-auto rounded-xl border border-slate-200 max-h-[480px]">
            {expTabla === "estudiantes" && (
              <table className="w-full text-xs sm:text-sm text-left">
                <thead className="bg-slate-50 uppercase text-[11px] font-bold text-slate-600 sticky top-0">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Nombre</th>
                    <th className="px-4 py-3">Programa</th>
                    <th className="px-4 py-3 text-center">Sem.</th>
                    <th className="px-4 py-3">Correo</th>
                    <th className="px-4 py-3 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {estudiantes
                    .filter((e) => `${e.id_estudiante} ${e.nombre_completo} ${e.nombre_programa}`.toLowerCase().includes(expSearch.toLowerCase()))
                    .map((e) => (
                      <tr key={e.id_estudiante} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-mono font-bold text-[#1F6AA5]">{e.id_estudiante}</td>
                        <td className="px-4 py-2.5 font-semibold">{e.nombre_completo}</td>
                        <td className="px-4 py-2.5 text-slate-600">{e.nombre_programa}</td>
                        <td className="px-4 py-2.5 text-center">{e.semestre}</td>
                        <td className="px-4 py-2.5 text-slate-500">{e.correo}</td>
                        <td className="px-4 py-2.5 text-right">
                          <button
                            onClick={async () => {
                              try {
                                await api.eliminarEstudiante(e.id_estudiante);
                                toast.success("Estudiante eliminado.");
                                bumpDataVersion();
                              } catch (err) {
                                toast.error((err as Error).message);
                              }
                            }}
                            className="p-1.5 rounded-lg text-rose-600 hover:bg-rose-50"
                            title="Eliminar estudiante"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}

            {expTabla === "grupos" && (
              <table className="w-full text-xs sm:text-sm text-left">
                <thead className="bg-slate-50 uppercase text-[11px] font-bold text-slate-600 sticky top-0">
                  <tr>
                    <th className="px-4 py-3">Grupo</th>
                    <th className="px-4 py-3">Asignatura</th>
                    <th className="px-4 py-3">Horario</th>
                    <th className="px-4 py-3 text-center">Cupos</th>
                    <th className="px-4 py-3 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {grupos
                    .filter((g) => `${g.id_grupo} ${g.nombre_curso} ${g.docente}`.toLowerCase().includes(expSearch.toLowerCase()))
                    .slice(0, 100)
                    .map((g) => (
                      <tr key={g.id_grupo} className="hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-mono font-bold text-[#1F6AA5]">{g.id_grupo}</td>
                        <td className="px-4 py-2.5 font-semibold">{g.nombre_curso}</td>
                        <td className="px-4 py-2.5 text-slate-600">{g.horario_texto}</td>
                        <td className="px-4 py-2.5 text-center">
                          <Badge variant="green">
                            {g.cupos_disponibles}/{g.cupos_totales}
                          </Badge>
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <button
                            onClick={async () => {
                              try {
                                await api.eliminarGrupo(g.id_grupo);
                                toast.success("Grupo eliminado.");
                                bumpDataVersion();
                              } catch (err) {
                                toast.error((err as Error).message);
                              }
                            }}
                            className="p-1.5 rounded-lg text-rose-600 hover:bg-rose-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}

            {expTabla === "programas" && (
              <table className="w-full text-xs sm:text-sm text-left">
                <thead className="bg-slate-50 uppercase text-[11px] font-bold text-slate-600 sticky top-0">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Programa</th>
                    <th className="px-4 py-3">Facultad</th>
                    <th className="px-4 py-3 text-center">Semestres</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {programas.map((p) => (
                    <tr key={p.id_programa}>
                      <td className="px-4 py-2.5 font-mono font-bold text-[#1F6AA5]">{p.id_programa}</td>
                      <td className="px-4 py-2.5 font-semibold">{p.nombre_programa}</td>
                      <td className="px-4 py-2.5 text-slate-600">{p.nombre_facultad}</td>
                      <td className="px-4 py-2.5 text-center">{p.semestres_duracion}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {expTabla === "facultades" && (
              <table className="w-full text-xs sm:text-sm text-left">
                <thead className="bg-slate-50 uppercase text-[11px] font-bold text-slate-600 sticky top-0">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Facultad</th>
                    <th className="px-4 py-3">Decano(a)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {facultades.map((f) => (
                    <tr key={f.id_facultad}>
                      <td className="px-4 py-2.5 font-mono font-bold text-[#1F6AA5]">{f.id_facultad}</td>
                      <td className="px-4 py-2.5 font-semibold">{f.nombre_facultad}</td>
                      <td className="px-4 py-2.5 text-slate-600">{f.decano}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      )}

      {/* TAB 5: ANALÍTICA INSTITUCIONAL */}
      {tab === "analitica" && analitica && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <Card className="lg:col-span-8 p-5 sm:p-6 space-y-4">
            <StepHeader step="GRÁFICA 1" title="Estudiantes Matriculados por Programa Académico" />
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analitica.estudiantes_por_programa} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="id_programa" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="estudiantes" name="Estudiantes" fill="#1F6AA5" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="lg:col-span-4 p-5 sm:p-6 space-y-4">
            <StepHeader step="GRÁFICA 2" title="Rendimiento Académico" />
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={analitica.distribucion_notas}
                    dataKey="cantidad"
                    nameKey="estado"
                    cx="50%"
                    cy="50%"
                    outerRadius={82}
                    label
                  >
                    {analitica.distribucion_notas.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
