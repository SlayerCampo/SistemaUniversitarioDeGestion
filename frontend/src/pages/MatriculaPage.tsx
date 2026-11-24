import React, { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  FileDown,
  Lock,
  Plus,
  ShoppingCart,
  Trash2,
  UtensilsCrossed,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import type { Estudiante, Grupo, ResumenMatricula } from "@/types/api";
import { Badge, Button, Card, Field, Select, StepHeader } from "@/components/ui/Primitives";

const DIAS = [
  { num: 1, nombre: "Lunes", corto: "Lun" },
  { num: 2, nombre: "Martes", corto: "Mar" },
  { num: 3, nombre: "Miércoles", corto: "Mié" },
  { num: 4, nombre: "Jueves", corto: "Jue" },
  { num: 5, nombre: "Viernes", corto: "Vie" },
];

export function MatriculaPage() {
  const { user, dataVersion, bumpDataVersion } = useAuth();
  const [estudiantes, setEstudiantes] = useState<Estudiante[]>([]);
  const [selectedEstId, setSelectedEstId] = useState<string>(
    user?.rol === "Estudiante" ? user.documento_asociado : ""
  );
  const [resumen, setResumen] = useState<ResumenMatricula | null>(null);
  const [asigSeleccionada, setAsigSeleccionada] = useState("");
  const [grupoSeleccionado, setGrupoSeleccionado] = useState("");
  const [carrito, setCarrito] = useState<Grupo[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  // Cargar lista de estudiantes solo si es Administrador
  useEffect(() => {
    if (user?.rol === "Estudiante") {
      setSelectedEstId(user.documento_asociado);
      return;
    }
    if (user?.rol === "Administrador") {
      api
        .estudiantes()
        .then((list) => {
          setEstudiantes(list);
          if (list.length > 0 && !selectedEstId) {
            setSelectedEstId(list[0].id_estudiante);
          }
        })
        .catch(() => setEstudiantes([]));
    }
  }, [user, dataVersion]);

  const cargarResumen = useCallback(async () => {
    if (!selectedEstId) {
      setResumen(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const r = await api.resumenMatricula(selectedEstId, "2026-2");
      setResumen(r);
      setCarrito([]);
      if (r.oferta_disponible.length > 0) {
        setAsigSeleccionada(r.oferta_disponible[0].id_asignatura);
        setGrupoSeleccionado(r.oferta_disponible[0].grupos[0]?.id_grupo || "");
      } else {
        setAsigSeleccionada("");
        setGrupoSeleccionado("");
      }
    } catch (e) {
      toast.error((e as Error).message);
      setResumen(null);
    } finally {
      setLoading(false);
    }
  }, [selectedEstId]);

  useEffect(() => {
    cargarResumen();
  }, [cargarResumen, dataVersion]);

  // Oferta disponible excluyendo las asignaturas ya puestas en el carrito
  const ofertaDisponible = useMemo(() => {
    if (!resumen) return [];
    const enCarrito = new Set(carrito.map((g) => g.id_asignatura));
    return resumen.oferta_disponible.filter((a) => !enCarrito.has(a.id_asignatura));
  }, [resumen, carrito]);

  useEffect(() => {
    if (ofertaDisponible.length === 0) {
      setAsigSeleccionada("");
      setGrupoSeleccionado("");
      return;
    }
    const existe = ofertaDisponible.find((a) => a.id_asignatura === asigSeleccionada);
    const actual = existe || ofertaDisponible[0];
    if (!existe) setAsigSeleccionada(actual.id_asignatura);
    if (!actual.grupos.some((g) => g.id_grupo === grupoSeleccionado)) {
      setGrupoSeleccionado(actual.grupos[0]?.id_grupo || "");
    }
  }, [ofertaDisponible, asigSeleccionada, grupoSeleccionado]);

  const asignaturaObj = ofertaDisponible.find((a) => a.id_asignatura === asigSeleccionada);
  const grupoObj = asignaturaObj?.grupos.find((g) => g.id_grupo === grupoSeleccionado);

  const credInscritos = resumen?.creditos_inscritos ?? 0;
  const credCarrito = carrito.reduce((acc, g) => acc + g.creditos, 0);
  const credTotales = credInscritos + credCarrito;
  const minCred = resumen?.reglas.creditos_minimos ?? 6;
  const maxCred = resumen?.reglas.creditos_maximos ?? 19;
  const porcentaje = Math.min(100, Math.round((credTotales / maxCred) * 100));

  const handleAgregarCarrito = async () => {
    if (!grupoObj || !resumen) return;
    setBusy(true);
    try {
      const nuevosIds = [...carrito.map((g) => g.id_grupo), grupoObj.id_grupo];
      const val = await api.validarCarrito(resumen.estudiante.id_estudiante, resumen.periodo, nuevosIds);
      if (!val.valido) {
        toast.error(val.errores.join(" "));
        return;
      }
      setCarrito((prev) => [...prev, grupoObj]);
      toast.success(`Agregada al carrito: ${grupoObj.nombre_curso}`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleConfirmar = async () => {
    if (!resumen || carrito.length === 0) return;
    setBusy(true);
    try {
      const res = await api.confirmarMatricula(
        resumen.estudiante.id_estudiante,
        resumen.periodo,
        carrito.map((g) => g.id_grupo)
      );
      toast.success(res.mensaje);
      bumpDataVersion();
      await cargarResumen();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleRetirar = async (idMatricula: string, nombre: string) => {
    setBusy(true);
    try {
      const res = await api.retirarMatricula(idMatricula);
      toast.success(res.mensaje || `Asignatura '${nombre}' retirada.`);
      bumpDataVersion();
      await cargarResumen();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleDescargarPdf = async () => {
    if (!resumen) return;
    try {
      await api.descargarPdfMatricula(resumen.estudiante.id_estudiante, resumen.periodo);
      toast.success("Recibo de matrícula PDF generado.");
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  // Bloques para el horario semanal visual (inscritas + carrito)
  const bloquesHorario = useMemo(() => {
    const lista: {
      dia: number;
      inicio: number;
      fin: number;
      codigo: string;
      nombre: string;
      tipo: "inscrita" | "carrito";
    }[] = [];
    for (const ins of resumen?.inscritas || []) {
      for (const h of ins.horarios) {
        lista.push({
          dia: h.dia_semana,
          inicio: h.hora_inicio,
          fin: h.hora_fin,
          codigo: ins.id_grupo,
          nombre: ins.nombre_curso,
          tipo: "inscrita",
        });
      }
    }
    for (const car of carrito) {
      for (const h of car.horarios) {
        lista.push({
          dia: h.dia_semana,
          inicio: h.hora_inicio,
          fin: h.hora_fin,
          codigo: car.id_grupo,
          nombre: car.nombre_curso,
          tipo: "carrito",
        });
      }
    }
    return lista;
  }, [resumen, carrito]);

  if (!loading && !resumen) {
    return (
      <Card className="p-8 text-center space-y-2">
        <p className="font-bold text-slate-900">No hay estudiantes disponibles para matricular</p>
        <p className="text-sm text-slate-500">
          Abre el botón <b>Modo Demo</b> arriba a la derecha y pulsa <b>Poblar 50+ Estudiantes</b> para comenzar.
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* PASO 1: IDENTIFICACIÓN Y CARGA DE CRÉDITOS */}
      <Card className="p-5 sm:p-6 space-y-4">
        <StepHeader
          step="PASO 1"
          title="Estudiante en Sesión y Carga de Créditos"
          subtitle="Rango reglamentario: mínimo 6 créditos y máximo 19 créditos por semestre."
          action={
            resumen && resumen.inscritas.length > 0 ? (
              <Button size="sm" variant="outline" onClick={handleDescargarPdf}>
                <FileDown className="w-4 h-4 text-[#1F6AA5]" />
                Recibo PDF
              </Button>
            ) : null
          }
        />

        {user?.rol === "Administrador" && estudiantes.length > 0 && (
          <div className="max-w-md">
            <Field label="Seleccionar Estudiante (Vista Administrativa)">
              <Select value={selectedEstId} onChange={(e) => setSelectedEstId(e.target.value)}>
                {estudiantes.map((e) => (
                  <option key={e.id_estudiante} value={e.id_estudiante}>
                    {e.id_estudiante} — {e.nombre_completo} ({e.nombre_programa})
                  </option>
                ))}
              </Select>
            </Field>
          </div>
        )}

        {resumen && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center p-4 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="lg:col-span-7 space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                {user?.rol === "Estudiante" && (
                  <Badge variant="green">
                    <Lock className="w-3 h-3" /> Sesión Privada
                  </Badge>
                )}
                <Badge variant="blue">Periodo {resumen.periodo}</Badge>
                <Badge variant="cyan">Semestre {resumen.estudiante.semestre}</Badge>
              </div>
              <h3 className="font-display font-extrabold text-lg text-slate-900">
                {resumen.estudiante.id_estudiante} — {resumen.estudiante.nombre_completo}
              </h3>
              <p className="text-xs sm:text-sm text-slate-600">
                Programa: <b className="text-[#154B75]">{resumen.estudiante.id_programa} · {resumen.estudiante.nombre_programa}</b>
              </p>
            </div>

            <div className="lg:col-span-5 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-slate-600">
                  Inscritos: {credInscritos} · Carrito: {credCarrito}
                </span>
                <span className={credTotales >= minCred && credTotales <= maxCred ? "text-emerald-700" : "text-amber-700"}>
                  {credTotales} / {maxCred} Créditos
                </span>
              </div>
              <div className="h-3 rounded-full bg-slate-200 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    credTotales >= minCred && credTotales <= maxCred ? "bg-emerald-600" : "bg-amber-500"
                  }`}
                  style={{ width: `${porcentaje}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500">
                {credTotales < minCred
                  ? `Te faltan al menos ${minCred - credTotales} créditos para alcanzar el mínimo.`
                  : "Carga académica dentro del rango oficial permitido."}
              </p>
            </div>
          </div>
        )}
      </Card>

      {/* LAYOUT PRINCIPAL: SELECCIÓN + CARRITO */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7 space-y-6">
          {/* PASO 2: ASIGNATURAS YA MATRICULADAS */}
          <Card className="p-5 sm:p-6 space-y-4">
            <StepHeader
              step="PASO 2"
              title={`Asignaturas Ya Matriculadas (${resumen?.inscritas.length ?? 0})`}
              subtitle="Al retirar una asignatura se devuelve automáticamente +1 cupo al grupo en PostgreSQL."
            />

            {!resumen?.inscritas.length ? (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-600">
                Aún no tienes asignaturas inscritas en este periodo. Empieza seleccionando en el Paso 3.
              </div>
            ) : (
              <div className="space-y-2.5">
                {resumen.inscritas.map((ins) => (
                  <div
                    key={ins.id_matricula}
                    className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/35 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded-md">
                          {ins.id_grupo}
                        </span>
                        <Badge variant="green">{ins.creditos} Cr.</Badge>
                      </div>
                      <p className="font-bold text-sm text-slate-900">{ins.nombre_curso}</p>
                      <p className="text-xs text-slate-600">
                        {ins.docente} · <b>{ins.horario_texto}</b>
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busy}
                      onClick={() => handleRetirar(ins.id_matricula, ins.nombre_curso)}
                      className="text-rose-700 border-rose-200 hover:bg-rose-50 shrink-0"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      Retirar
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* PASO 3: SELECCIONAR ASIGNATURA DEL PROGRAMA Y GRUPO */}
          <Card className="p-5 sm:p-6 space-y-4">
            <StepHeader
              step="PASO 3"
              title="Elegir Nueva Asignatura de tu Plan de Estudios"
              subtitle={`Solo se muestran asignaturas propias de ${resumen?.estudiante.nombre_programa || "tu programa"}.`}
            />

            {ofertaDisponible.length === 0 ? (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-sm text-emerald-900 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                Ya tienes inscritas o en carrito todas las asignaturas disponibles para tu programa.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <Field label="3.A — Asignatura del Programa">
                    <Select value={asigSeleccionada} onChange={(e) => setAsigSeleccionada(e.target.value)}>
                      {ofertaDisponible.map((a) => (
                        <option key={a.id_asignatura} value={a.id_asignatura}>
                          {a.id_asignatura} — {a.nombre_curso} ({a.creditos} Cr.)
                        </option>
                      ))}
                    </Select>
                  </Field>

                  <Field label="3.B — Grupo y Horario Ofertado">
                    <Select value={grupoSeleccionado} onChange={(e) => setGrupoSeleccionado(e.target.value)}>
                      {asignaturaObj?.grupos.map((g) => (
                        <option key={g.id_grupo} value={g.id_grupo}>
                          {g.id_grupo} · {g.horario_texto} ({g.cupos_disponibles} cupos)
                        </option>
                      ))}
                    </Select>
                  </Field>
                </div>

                {grupoObj && (
                  <div className="p-4 rounded-xl bg-sky-50/50 border border-sky-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-[#154B75]">{grupoObj.id_grupo}</span>
                        <Badge variant="cyan">{grupoObj.creditos} Créditos ({grupoObj.creditos}h)</Badge>
                        <Badge variant={grupoObj.cupos_disponibles > 0 ? "green" : "red"}>
                          {grupoObj.cupos_disponibles} cupos libres
                        </Badge>
                      </div>
                      <p className="text-sm font-bold text-slate-900">{grupoObj.nombre_curso}</p>
                      <p className="text-xs text-slate-600 flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-[#1F6AA5]" />
                        {grupoObj.horario_texto} · {grupoObj.docente}
                      </p>
                    </div>

                    <Button onClick={handleAgregarCarrito} disabled={busy || grupoObj.cupos_disponibles <= 0} className="shrink-0">
                      <Plus className="w-4 h-4" />
                      Agregar al Carrito
                    </Button>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>

        {/* PASO 4: CARRITO STICKY DE CONFIRMACIÓN */}
        <div className="lg:col-span-5 lg:sticky lg:top-20 space-y-6">
          <Card className="p-5 sm:p-6 space-y-4">
            <StepHeader
              step="PASO 4"
              title={`Carrito por Confirmar (${carrito.length})`}
              subtitle="Valida cupos atómicamente y registra tu matrícula oficial en PostgreSQL."
            />

            {carrito.length === 0 ? (
              <div className="py-8 text-center space-y-2 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                <ShoppingCart className="w-7 h-7 text-slate-400 mx-auto" />
                <p className="text-sm font-semibold text-slate-600">El carrito está vacío</p>
                <p className="text-xs text-slate-500">Elige una asignatura en el Paso 3 y agrégala aquí.</p>
              </div>
            ) : (
              <>
                <div className="space-y-2.5">
                  {carrito.map((item) => (
                    <div
                      key={item.id_grupo}
                      className="p-3.5 rounded-xl border border-amber-200 bg-amber-50/40 flex items-center justify-between gap-3"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-xs font-bold text-amber-900">{item.id_grupo}</span>
                          <Badge variant="amber">{item.creditos} Cr.</Badge>
                        </div>
                        <p className="text-sm font-bold text-slate-900 truncate">{item.nombre_curso}</p>
                        <p className="text-xs text-slate-600">{item.horario_texto}</p>
                      </div>
                      <button
                        onClick={() => setCarrito((prev) => prev.filter((x) => x.id_grupo !== item.id_grupo))}
                        className="p-2 rounded-lg text-rose-600 hover:bg-rose-50 transition shrink-0"
                        title="Quitar del carrito"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>

                {credTotales < minCred && (
                  <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                    <span>
                      Completa mínimo <b>{minCred} créditos</b> en total para confirmar (actual: {credTotales}).
                    </span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2.5 pt-2">
                  <Button variant="outline" onClick={() => setCarrito([])} disabled={busy}>
                    Vaciar Carrito
                  </Button>
                  <Button
                    variant="success"
                    onClick={handleConfirmar}
                    disabled={busy || credTotales < minCred || credTotales > maxCred}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Confirmar Matrícula
                  </Button>
                </div>
              </>
            )}
          </Card>
        </div>
      </div>

      {/* VISUALIZADOR DE HORARIO SEMANAL CON FRANJA DE ALMUERZO */}
      <Card className="p-5 sm:p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <Calendar className="w-5 h-5 text-[#1F6AA5]" />
            <div>
              <h3 className="font-display font-bold text-base text-slate-900">Horario Semanal Consolidado</h3>
              <p className="text-xs text-slate-500">Vista de asignaturas inscritas (azul) y preseleccionadas (ámbar).</p>
            </div>
          </div>
          <Badge variant="cyan">
            <UtensilsCrossed className="w-3.5 h-3.5" /> Almuerzo libre: 13:00 – 14:00
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {DIAS.map((dia) => {
            const delDia = bloquesHorario
              .filter((b) => b.dia === dia.num)
              .sort((a, b) => a.inicio - b.inicio);
            return (
              <div key={dia.num} className="rounded-xl border border-slate-200 bg-slate-50/70 p-3 space-y-2">
                <p className="text-xs font-extrabold uppercase tracking-wider text-[#154B75] pb-1.5 border-b border-slate-200">
                  {dia.nombre}
                </p>
                {delDia.length === 0 ? (
                  <p className="text-xs text-slate-400 italic py-2">Sin clases</p>
                ) : (
                  delDia.map((b, idx) => (
                    <div
                      key={`${b.codigo}-${idx}`}
                      className={`p-2.5 rounded-lg border text-xs space-y-0.5 ${
                        b.tipo === "inscrita"
                          ? "bg-sky-50 border-sky-200 text-slate-900"
                          : "bg-amber-50 border-amber-300 border-dashed text-amber-950"
                      }`}
                    >
                      <p className="font-mono font-bold text-[11px]">
                        {String(b.inicio).padStart(2, "0")}:00 – {String(b.fin).padStart(2, "0")}:00
                      </p>
                      <p className="font-bold leading-snug">{b.nombre}</p>
                      <p className="text-[10px] opacity-75">{b.codigo}</p>
                    </div>
                  ))
                )}
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
