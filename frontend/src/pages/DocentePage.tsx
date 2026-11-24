import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { Save, Users } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { Grupo, PlanillaGrupoResponse, Programa } from "@/types/api";
import { Badge, Button, Card, Field, Input, Select, StepHeader } from "@/components/ui/Primitives";

interface EditableRow {
  id_matricula: string;
  id_estudiante: string;
  nombre_completo: string;
  nota1: number;
  nota2: number;
  nota3: number;
}

function calcDef(n1: number, n2: number, n3: number): number {
  return Math.round((n1 * 0.3 + n2 * 0.3 + n3 * 0.4) * 100) / 100;
}

export function DocentePage() {
  const { dataVersion, bumpDataVersion } = useAuth();
  const [programas, setProgramas] = useState<Programa[]>([]);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [progFiltro, setProgFiltro] = useState("");
  const [grupoId, setGrupoId] = useState("");
  const [planilla, setPlanilla] = useState<PlanillaGrupoResponse | null>(null);
  const [rows, setRows] = useState<EditableRow[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([api.programas(), api.grupos()])
      .then(([p, g]) => {
        setProgramas(p);
        setGrupos(g);
        if (g.length > 0 && !grupoId) setGrupoId(g[0].id_grupo);
      })
      .catch((e) => toast.error((e as Error).message));
  }, [dataVersion]);

  const gruposFiltrados = progFiltro ? grupos.filter((g) => g.id_programa === progFiltro) : grupos;

  useEffect(() => {
    if (gruposFiltrados.length > 0 && !gruposFiltrados.some((g) => g.id_grupo === grupoId)) {
      setGrupoId(gruposFiltrados[0].id_grupo);
    }
  }, [progFiltro, grupos]);

  useEffect(() => {
    if (!grupoId) return;
    api
      .planillaGrupo(grupoId)
      .then((res) => {
        setPlanilla(res);
        setRows(
          res.estudiantes.map((e) => ({
            id_matricula: e.id_matricula,
            id_estudiante: e.id_estudiante,
            nombre_completo: e.nombre_completo,
            nota1: e.nota1,
            nota2: e.nota2,
            nota3: e.nota3,
          }))
        );
      })
      .catch((e) => {
        toast.error((e as Error).message);
        setPlanilla(null);
      });
  }, [grupoId, dataVersion]);

  const updateRow = (idMat: string, field: "nota1" | "nota2" | "nota3", raw: string) => {
    const val = Math.max(0, Math.min(5, parseFloat(raw) || 0));
    setRows((prev) => prev.map((r) => (r.id_matricula === idMat ? { ...r, [field]: val } : r)));
  };

  const handleGuardar = async () => {
    if (rows.length === 0) return;
    setSaving(true);
    try {
      const res = await api.guardarCalificaciones(
        rows.map((r) => ({
          id_matricula: r.id_matricula,
          nota1: r.nota1,
          nota2: r.nota2,
          nota3: r.nota3,
        }))
      );
      toast.success(res.mensaje);
      bumpDataVersion();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-5 sm:p-6 space-y-4">
        <StepHeader
          step="PASO 1"
          title="Seleccionar Programa Académico y Grupo a Calificar"
          subtitle="Edita Corte 1 (30%), Corte 2 (30%) y Corte 3 (40%) sin duplicar registros en PostgreSQL."
        />

        <div className="grid grid-cols-1 md:grid-cols-12 gap-3.5">
          <div className="md:col-span-5">
            <Field label="Filtrar por Programa">
              <Select value={progFiltro} onChange={(e) => setProgFiltro(e.target.value)}>
                <option value="">Todos los Programas</option>
                {programas.map((p) => (
                  <option key={p.id_programa} value={p.id_programa}>
                    {p.id_programa} — {p.nombre_programa}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          <div className="md:col-span-7">
            <Field label="Grupo / Asignatura">
              <Select value={grupoId} onChange={(e) => setGrupoId(e.target.value)}>
                {gruposFiltrados.map((g) => (
                  <option key={g.id_grupo} value={g.id_grupo}>
                    {g.id_grupo} — {g.nombre_curso} ({g.horario_texto})
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        </div>
      </Card>

      {planilla && (
        <Card className="p-5 sm:p-6 space-y-4">
          <StepHeader
            step="PASO 2"
            title={`Planilla de Calificaciones — ${planilla.id_grupo} (${planilla.nombre_curso})`}
            subtitle={`Docente: ${planilla.docente} · ${rows.length} estudiante(s) matriculados activamente.`}
            action={
              rows.length > 0 ? (
                <Button onClick={handleGuardar} disabled={saving} variant="success">
                  <Save className="w-4 h-4" />
                  {saving ? "Guardando..." : "Guardar Calificaciones"}
                </Button>
              ) : null
            }
          />

          {rows.length === 0 ? (
            <div className="py-10 text-center text-sm text-slate-500 flex flex-col items-center gap-2">
              <Users className="w-7 h-7 text-slate-400" />
              No hay estudiantes matriculados en este grupo todavía.
            </div>
          ) : (
            <>
              {/* VISTA TABLA PARA COMPUTADOR */}
              <div className="hidden md:block overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-sm text-left">
                  <thead className="bg-slate-50 text-[11px] uppercase font-bold text-slate-600">
                    <tr>
                      <th className="px-4 py-3">ID</th>
                      <th className="px-4 py-3">Estudiante</th>
                      <th className="px-3 py-3 w-28 text-center">Corte 1 (30%)</th>
                      <th className="px-3 py-3 w-28 text-center">Corte 2 (30%)</th>
                      <th className="px-3 py-3 w-28 text-center">Corte 3 (40%)</th>
                      <th className="px-4 py-3 text-center">Definitiva</th>
                      <th className="px-4 py-3 text-center">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {rows.map((r) => {
                      const def = calcDef(r.nota1, r.nota2, r.nota3);
                      const apr = def >= 3.0;
                      return (
                        <tr key={r.id_matricula} className="hover:bg-slate-50/70">
                          <td className="px-4 py-2.5 font-mono text-xs font-bold text-[#1F6AA5]">{r.id_estudiante}</td>
                          <td className="px-4 py-2.5 font-semibold text-slate-900">{r.nombre_completo}</td>
                          {(["nota1", "nota2", "nota3"] as const).map((campo) => (
                            <td key={campo} className="px-2 py-2">
                              <Input
                                type="number"
                                step="0.1"
                                min={0}
                                max={5}
                                value={r[campo]}
                                onChange={(e) => updateRow(r.id_matricula, campo, e.target.value)}
                                className="text-center font-mono h-9"
                              />
                            </td>
                          ))}
                          <td className="px-4 py-2.5 text-center font-mono font-extrabold text-slate-900">
                            {def.toFixed(2)}
                          </td>
                          <td className="px-4 py-2.5 text-center">
                            <Badge variant={apr ? "green" : "red"}>{apr ? "Aprobado" : "Reprobado"}</Badge>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* VISTA TARJETAS TÁCTILES PARA CELULAR / ANDROID APK */}
              <div className="md:hidden space-y-3">
                {rows.map((r) => {
                  const def = calcDef(r.nota1, r.nota2, r.nota3);
                  const apr = def >= 3.0;
                  return (
                    <div key={r.id_matricula} className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3">
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="font-mono text-xs font-bold text-[#1F6AA5]">{r.id_estudiante}</p>
                          <p className="font-bold text-sm text-slate-900">{r.nombre_completo}</p>
                        </div>
                        <Badge variant={apr ? "green" : "red"}>Def: {def.toFixed(2)}</Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { k: "nota1" as const, lbl: "C1 (30%)" },
                          { k: "nota2" as const, lbl: "C2 (30%)" },
                          { k: "nota3" as const, lbl: "C3 (40%)" },
                        ].map((c) => (
                          <div key={c.k}>
                            <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">{c.lbl}</label>
                            <Input
                              type="number"
                              step="0.1"
                              min={0}
                              max={5}
                              value={r[c.k]}
                              onChange={(e) => updateRow(r.id_matricula, c.k, e.target.value)}
                              className="text-center font-mono h-9"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </Card>
      )}
    </div>
  );
}
