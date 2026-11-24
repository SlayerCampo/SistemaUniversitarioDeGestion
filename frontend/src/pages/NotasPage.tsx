import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { Award, BookOpenCheck, CheckCircle2, FileDown, GraduationCap, Lock } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { BoletinResponse, Estudiante } from "@/types/api";
import { Badge, Button, Card, Field, Select, StatCard, StepHeader } from "@/components/ui/Primitives";

export function NotasPage() {
  const { user, dataVersion } = useAuth();
  const [estudiantes, setEstudiantes] = useState<Estudiante[]>([]);
  const [selectedId, setSelectedId] = useState<string>(
    user?.rol === "Estudiante" ? user.documento_asociado : ""
  );
  const [boletin, setBoletin] = useState<BoletinResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.rol === "Estudiante") {
      setSelectedId(user.documento_asociado);
      return;
    }
    if (user?.rol === "Administrador") {
      api
        .estudiantes()
        .then((list) => {
          setEstudiantes(list);
          if (list.length > 0 && !selectedId) setSelectedId(list[0].id_estudiante);
        })
        .catch(() => setEstudiantes([]));
    }
  }, [user, dataVersion]);

  useEffect(() => {
    if (!selectedId) {
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    api
      .boletin(selectedId, "2026-2")
      .then((res) => {
        if (active) setBoletin(res);
      })
      .catch((e) => {
        toast.error((e as Error).message);
        if (active) setBoletin(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selectedId, dataVersion]);

  const handleDescargarPdf = async () => {
    if (!boletin) return;
    try {
      await api.descargarPdfBoletin(boletin.estudiante.id_estudiante, boletin.periodo);
      toast.success("Boletín oficial PDF descargado.");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-5 sm:p-6 space-y-4">
        <StepHeader
          step="BOLETÍN OFICIAL"
          title="Calificaciones por Corte y Promedio Ponderado Semestral (PPS)"
          subtitle="Ponderación oficial: Corte 1 (30%) · Corte 2 (30%) · Corte 3 (40%). Nota mínima aprobatoria: 3.00."
          action={
            boletin && boletin.asignaturas.length > 0 ? (
              <Button onClick={handleDescargarPdf}>
                <FileDown className="w-4 h-4" />
                Descargar Boletín PDF
              </Button>
            ) : null
          }
        />

        {user?.rol === "Administrador" && estudiantes.length > 0 && (
          <div className="max-w-md">
            <Field label="Consultar Estudiante">
              <Select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                {estudiantes.map((e) => (
                  <option key={e.id_estudiante} value={e.id_estudiante}>
                    {e.id_estudiante} — {e.nombre_completo}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        )}

        {boletin && (
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                {user?.rol === "Estudiante" && (
                  <Badge variant="green">
                    <Lock className="w-3 h-3" /> Boletín Personal
                  </Badge>
                )}
                <Badge variant="blue">Periodo {boletin.periodo}</Badge>
              </div>
              <h3 className="font-display font-extrabold text-lg text-slate-900">
                {boletin.estudiante.id_estudiante} — {boletin.estudiante.nombre_completo}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600">
                {boletin.estudiante.id_programa} · {boletin.estudiante.nombre_programa} · Semestre{" "}
                {boletin.estudiante.semestre}
              </p>
            </div>
          </div>
        )}
      </Card>

      {boletin && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <StatCard
              label="Promedio (PPS)"
              value={`${boletin.resumen.pps.toFixed(2)} / 5.0`}
              icon={<Award className="w-5 h-5" />}
              accent={boletin.resumen.pps >= 3 ? "green" : "amber"}
            />
            <StatCard
              label="Materias Activas"
              value={boletin.resumen.materias_activas}
              icon={<BookOpenCheck className="w-5 h-5" />}
              accent="blue"
            />
            <StatCard
              label="Aprobadas"
              value={boletin.resumen.materias_aprobadas}
              icon={<CheckCircle2 className="w-5 h-5" />}
              accent="green"
            />
            <StatCard
              label="Créditos Aprobados"
              value={`${boletin.resumen.creditos_aprobados} / ${boletin.resumen.creditos_inscritos}`}
              icon={<GraduationCap className="w-5 h-5" />}
              accent="cyan"
            />
          </div>

          <div className="space-y-3">
            {boletin.asignaturas.length === 0 ? (
              <Card className="p-8 text-center text-sm text-slate-500">
                No tienes asignaturas activas matriculadas en este periodo.
              </Card>
            ) : (
              boletin.asignaturas.map((a) => (
                <Card key={a.id_matricula} className="p-4 sm:p-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-[#1F6AA5] bg-sky-50 px-2 py-0.5 rounded-md">
                          {a.id_grupo}
                        </span>
                        <Badge variant="cyan">{a.creditos} Cr.</Badge>
                        <Badge
                          variant={
                            a.estado === "Aprobado" ? "green" : a.estado === "Reprobado" ? "red" : "amber"
                          }
                        >
                          {a.estado}
                        </Badge>
                      </div>
                      <h4 className="font-bold text-base text-slate-900 mt-1">{a.nombre_curso}</h4>
                      <p className="text-xs text-slate-500">Docente: {a.docente}</p>
                    </div>

                    <div className="grid grid-cols-4 gap-2 sm:gap-3 text-center">
                      {[
                        { label: "Corte 1", val: a.nota1 },
                        { label: "Corte 2", val: a.nota2 },
                        { label: "Corte 3", val: a.nota3 },
                        { label: "Definitiva", val: a.definitiva, highlight: true },
                      ].map((c) => (
                        <div
                          key={c.label}
                          className={`px-2.5 py-2 rounded-xl border ${
                            c.highlight
                              ? "bg-[#1F6AA5] text-white border-[#1F6AA5]"
                              : "bg-slate-50 text-slate-800 border-slate-200"
                          }`}
                        >
                          <p className={`text-[10px] font-bold uppercase ${c.highlight ? "text-sky-100" : "text-slate-500"}`}>
                            {c.label}
                          </p>
                          <p className="font-mono text-sm sm:text-base font-extrabold mt-0.5">
                            {c.val !== null ? c.val.toFixed(2) : "—"}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        </>
      )}

      {!loading && !boletin && (
        <Card className="p-8 text-center text-sm text-slate-500">
          No hay datos de boletín disponibles. Pobla los datos de simulación desde el botón <b>Modo Demo</b>.
        </Card>
      )}
    </div>
  );
}
