import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  Award,
  BookOpen,
  Building2,
  Clock,
  Download,
  GraduationCap,
  LayoutGrid,
  List,
  RefreshCw,
  Search,
  Sparkles,
  Users,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { isCapacitorApp, isTauriApp } from "@/lib/platform";
import type { Grupo, KPIs, Programa } from "@/types/api";
import { Badge, Button, Card, Input, Select, StatCard, StepHeader } from "@/components/ui/Primitives";

export function DashboardPage() {
  const { user, dataVersion, bumpDataVersion, demoSwitch } = useAuth();
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [programas, setProgramas] = useState<Programa[]>([]);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [programaFiltro, setProgramaFiltro] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [vista, setVista] = useState<"tarjetas" | "tabla">("tarjetas");
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const [k, p, g] = await Promise.all([api.kpis(), api.programas(), api.grupos()]);
        if (active) {
          setKpis(k);
          setProgramas(p);
          setGrupos(g);
        }
      } catch (err) {
        toast.error((err as Error).message);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [dataVersion]);

  const filtrados = grupos.filter((g) => {
    if (programaFiltro && g.id_programa !== programaFiltro) return false;
    if (busqueda.trim()) {
      const q = busqueda.trim().toLowerCase();
      return (
        g.id_grupo.toLowerCase().includes(q) ||
        g.nombre_curso.toLowerCase().includes(q) ||
        g.docente.toLowerCase().includes(q) ||
        g.horario_texto.toLowerCase().includes(q) ||
        g.nombre_programa.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handlePoblarRapido = async () => {
    setSeeding(true);
    try {
      if (user?.rol !== "Administrador") {
        await demoSwitch("admin");
      }
      const res = await api.demoPoblar();
      toast.success(`Simulación cargada: ${res.resumen.estudiantes} estudiantes y ${res.resumen.grupos} grupos.`);
      bumpDataVersion();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSeeding(false);
    }
  };

  const isNative = isTauriApp() || isCapacitorApp();

  return (
    <div className="space-y-6">
      {/* BANNER INSTITUCIONAL */}
      <div className="rounded-2xl bg-gradient-to-r from-[#1F6AA5] via-[#175587] to-[#3B1C7A] text-white p-5 sm:p-7 shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-white/15 text-[11px] font-bold uppercase tracking-wider">
                Periodo {kpis?.periodo_activo || "2026-2"}
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-white/15 text-[11px] font-semibold">
                {user?.rol}
              </span>
            </div>
            <h2 className="font-display text-xl sm:text-2xl font-extrabold tracking-tight">
              Hola, {user?.nombre_completo}
            </h2>
            <p className="text-xs sm:text-sm text-sky-100/90 max-w-2xl">
              Consulta la oferta académica oficial por Programa, gestiona matrículas sin cruces de horario ni clases en
              la hora de almuerzo (13:00–14:00) y descarga certificados PDF.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 shrink-0">
            {(user?.rol === "Estudiante" || user?.rol === "Administrador") && (
              <Link to="/matricula">
                <Button variant="secondary" className="bg-white text-[#154B75] hover:bg-sky-50">
                  <GraduationCap className="w-4 h-4" />
                  Ir a Matrícula
                </Button>
              </Link>
            )}
            {!isNative && (
              <Link to="/descargas">
                <Button variant="outline" className="bg-white/10 text-white border-white/25 hover:bg-white/20">
                  <Download className="w-4 h-4" />
                  App PC / Android
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* KPIS EN TIEMPO REAL */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        <StatCard label="Estudiantes" value={kpis?.estudiantes ?? 0} icon={<Users className="w-5 h-5" />} accent="blue" />
        <StatCard label="Grupos Ofertados" value={kpis?.grupos ?? 0} sub={`${kpis?.asignaturas ?? 0} materias`} icon={<BookOpen className="w-5 h-5" />} accent="cyan" />
        <StatCard label="Matrículas Activas" value={kpis?.matriculas_activas ?? 0} icon={<GraduationCap className="w-5 h-5" />} accent="green" />
        <StatCard label="Programas" value={kpis?.programas ?? 0} sub={`${kpis?.facultades ?? 0} facultades`} icon={<Building2 className="w-5 h-5" />} accent="purple" />
        <StatCard
          label="Promedio Global"
          value={`${(kpis?.promedio_global ?? 0).toFixed(2)}`}
          sub="Escala 0.0 – 5.0"
          icon={<Award className="w-5 h-5" />}
          accent="amber"
        />
      </div>

      {/* ESTADO VACÍO LIMPIO SI LA BD ARRANCA EN BLANCO */}
      {!loading && kpis && kpis.estudiantes === 0 && kpis.grupos === 0 && (
        <Card className="p-6 sm:p-8 text-center border-dashed border-2 border-sky-300 bg-sky-50/40 space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-100 text-[#1F6AA5] mx-auto flex items-center justify-center">
            <Sparkles className="w-6 h-6" />
          </div>
          <div className="max-w-lg mx-auto space-y-1">
            <h3 className="font-display font-bold text-lg text-slate-900">Base de Datos PostgreSQL en Blanco</h3>
            <p className="text-sm text-slate-600">
              Actualmente hay 0 registros cargados. Puedes registrar facultades y estudiantes manualmente desde{" "}
              <b>Administración</b>, importar un archivo Excel o poblar al instante los 50 estudiantes y 240 grupos de
              simulación.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Button onClick={handlePoblarRapido} disabled={seeding}>
              <RefreshCw className={`w-4 h-4 ${seeding ? "animate-spin" : ""}`} />
              Poblar 50+ Estudiantes Ahora
            </Button>
            {user?.rol === "Administrador" && (
              <Link to="/admin">
                <Button variant="outline">Ir a Administración / ETL Excel</Button>
              </Link>
            )}
          </div>
        </Card>
      )}

      {/* EXPLORADOR DE OFERTA ACADÉMICA */}
      <Card className="p-5 sm:p-6 space-y-5">
        <StepHeader
          step="CATÁLOGO EN VIVO"
          title="Oferta Académica por Programa y Disponibilidad de Cupos"
          subtitle="Todas las asignaturas duran 2, 3 o 4 horas continuas con 0 clases en franja de almuerzo (13:00–14:00)."
          action={
            <div className="inline-flex rounded-xl border border-slate-200 bg-slate-50 p-1">
              <button
                onClick={() => setVista("tarjetas")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                  vista === "tarjetas" ? "bg-white text-[#1F6AA5] shadow-sm" : "text-slate-600"
                }`}
              >
                <LayoutGrid className="w-3.5 h-3.5" /> Tarjetas
              </button>
              <button
                onClick={() => setVista("tabla")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                  vista === "tabla" ? "bg-white text-[#1F6AA5] shadow-sm" : "text-slate-600"
                }`}
              >
                <List className="w-3.5 h-3.5" /> Tabla
              </button>
            </div>
          }
        />

        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          <div className="md:col-span-5">
            <Select value={programaFiltro} onChange={(e) => setProgramaFiltro(e.target.value)}>
              <option value="">Todos los Programas ({programas.length})</option>
              {programas.map((p) => (
                <option key={p.id_programa} value={p.id_programa}>
                  {p.id_programa} — {p.nombre_programa}
                </option>
              ))}
            </Select>
          </div>
          <div className="md:col-span-7 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <Input
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por código (SIS101), asignatura, docente o día (Lunes)..."
              className="pl-10"
            />
          </div>
        </div>

        <p className="text-xs font-medium text-slate-500">
          Mostrando <b className="text-slate-800">{filtrados.length}</b> grupo(s) ofertados.
        </p>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <div key={n} className="h-32 rounded-2xl bg-slate-100 animate-pulse" />
            ))}
          </div>
        ) : filtrados.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-500">
            No se encontraron grupos con ese criterio de búsqueda.
          </div>
        ) : vista === "tarjetas" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5">
            {filtrados.slice(0, 36).map((g) => (
              <div
                key={g.id_grupo}
                className="p-4 rounded-2xl border border-slate-200 hover:border-[#1F6AA5]/50 hover:shadow-sm transition bg-white flex flex-col justify-between gap-3"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold text-[#1F6AA5] bg-sky-50 px-2 py-0.5 rounded-md">
                      {g.id_grupo}
                    </span>
                    <Badge variant={g.cupos_disponibles > 5 ? "green" : g.cupos_disponibles > 0 ? "amber" : "red"}>
                      {g.cupos_disponibles}/{g.cupos_totales} cupos
                    </Badge>
                  </div>
                  <h3 className="font-bold text-sm text-slate-900 leading-snug">{g.nombre_curso}</h3>
                  <p className="text-xs text-slate-500">{g.nombre_programa}</p>
                </div>

                <div className="pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600">
                  <span className="inline-flex items-center gap-1 font-medium">
                    <Clock className="w-3.5 h-3.5 text-[#0E7490]" />
                    {g.horario_texto}
                  </span>
                  <Badge variant="cyan">{g.creditos} Cr.</Badge>
                </div>
                <p className="text-[11px] text-slate-500 truncate">Docente: {g.docente}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-50 text-slate-600 uppercase text-[11px] font-bold">
                <tr>
                  <th className="px-4 py-3">Grupo</th>
                  <th className="px-4 py-3">Asignatura</th>
                  <th className="px-4 py-3">Programa</th>
                  <th className="px-4 py-3 text-center">Cr.</th>
                  <th className="px-4 py-3">Horario</th>
                  <th className="px-4 py-3">Docente</th>
                  <th className="px-4 py-3 text-center">Cupos</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtrados.slice(0, 80).map((g) => (
                  <tr key={g.id_grupo} className="hover:bg-slate-50/70">
                    <td className="px-4 py-2.5 font-mono font-bold text-[#1F6AA5] whitespace-nowrap">{g.id_grupo}</td>
                    <td className="px-4 py-2.5 font-semibold text-slate-900">{g.nombre_curso}</td>
                    <td className="px-4 py-2.5 text-slate-600">{g.nombre_programa}</td>
                    <td className="px-4 py-2.5 text-center font-bold">{g.creditos}</td>
                    <td className="px-4 py-2.5 whitespace-nowrap text-slate-700">{g.horario_texto}</td>
                    <td className="px-4 py-2.5 text-slate-600">{g.docente}</td>
                    <td className="px-4 py-2.5 text-center">
                      <Badge variant={g.cupos_disponibles > 5 ? "green" : g.cupos_disponibles > 0 ? "amber" : "red"}>
                        {g.cupos_disponibles}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
