import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Database,
  GraduationCap,
  RefreshCw,
  Server,
  Shield,
  Sparkles,
  Trash2,
  UserCheck,
  X,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api, DEFAULT_API_URL } from "@/lib/api";
import type { DemoPerfilesResponse } from "@/types/api";
import { Badge, Button, Input } from "@/components/ui/Primitives";

export function DemoDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, demoSwitch, health, apiUrl, updateApiUrl, bumpDataVersion } = useAuth();
  const [perfiles, setPerfiles] = useState<DemoPerfilesResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmVaciar, setConfirmVaciar] = useState("");
  const [customUrl, setCustomUrl] = useState(apiUrl);
  const [tab, setTab] = useState<"roles" | "datos" | "servidor">("roles");

  useEffect(() => {
    if (!open) return;
    setCustomUrl(apiUrl);
    api
      .demoPerfiles()
      .then(setPerfiles)
      .catch(() => setPerfiles(null));
  }, [open, apiUrl]);

  if (!open) return null;

  const handleSwitch = async (perfil: string) => {
    setBusy(true);
    try {
      const u = await demoSwitch(perfil);
      toast.success(`Sesión cambiada a ${u.nombre_completo} (${u.rol})`);
      onClose();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handlePoblar = async () => {
    setBusy(true);
    try {
      // Asegurar sesión admin para ejecutar la semilla
      if (user?.rol !== "Administrador") {
        await demoSwitch("admin");
      }
      const res = await api.demoPoblar();
      toast.success(`Base de datos poblada: ${res.resumen.estudiantes} estudiantes y ${res.resumen.grupos} grupos.`);
      const p = await api.demoPerfiles();
      setPerfiles(p);
      bumpDataVersion();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleVaciar = async () => {
    if (confirmVaciar.trim().toUpperCase() !== "VACIAR") {
      toast.error('Escribe exactamente "VACIAR" para confirmar.');
      return;
    }
    setBusy(true);
    try {
      if (user?.rol !== "Administrador") {
        await demoSwitch("admin");
      }
      await api.demoVaciar("VACIAR");
      setConfirmVaciar("");
      toast.success("Base de datos vaciada en blanco.");
      const p = await api.demoPerfiles();
      setPerfiles(p);
      bumpDataVersion();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleGuardarUrl = async () => {
    setBusy(true);
    try {
      await updateApiUrl(customUrl);
      toast.success("Servidor API actualizado.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/45 backdrop-blur-[2px]">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-slate-200 animate-in slide-in-from-right duration-200">
        {/* Cabecera */}
        <div className="p-5 bg-gradient-to-r from-[#1F6AA5] to-[#154B75] text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-white/15">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base leading-tight">Modo Exposición</h3>
              <p className="text-xs text-sky-100">Simulación rápida para sustentación</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-white/15 transition"
            aria-label="Cerrar panel de demostración"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Pestañas */}
        <div className="grid grid-cols-3 border-b border-slate-200 bg-slate-50 p-1.5 gap-1">
          {[
            { id: "roles", label: "Perfiles", icon: UserCheck },
            { id: "datos", label: "Datos BD", icon: Database },
            { id: "servidor", label: "Servidor", icon: Server },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id as typeof tab)}
              className={`flex items-center justify-center gap-1.5 py-2 text-xs font-bold rounded-lg transition ${
                tab === t.id ? "bg-white text-[#1F6AA5] shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <t.icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          ))}
        </div>

        {/* Contenido */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {tab === "roles" && (
            <>
              <div className="space-y-2.5">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Roles Institucionales (1 clic)</p>
                {perfiles?.cuentas_base.map((c) => (
                  <button
                    key={c.perfil}
                    disabled={busy}
                    onClick={() => handleSwitch(c.perfil)}
                    className="w-full text-left p-3.5 rounded-xl border border-slate-200 hover:border-[#1F6AA5] hover:bg-sky-50/40 transition flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-sky-50 text-[#1F6AA5]">
                        <Shield className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900">{c.etiqueta}</p>
                        <p className="text-xs text-slate-500">{c.detalle}</p>
                      </div>
                    </div>
                    <Badge variant={c.rol === "Administrador" ? "purple" : "cyan"}>{c.rol}</Badge>
                  </button>
                ))}
              </div>

              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Estudiantes Registrados</p>
                  <Badge variant="blue">{perfiles?.estudiantes.length || 0} visibles</Badge>
                </div>
                {!perfiles?.estudiantes.length ? (
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900">
                    La base de datos PostgreSQL está en blanco. Ve a la pestaña <b>Datos BD</b> y pulsa{" "}
                    <b>Poblar 50+ Estudiantes</b> para simular al instante.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {perfiles.estudiantes.map((e) => (
                      <button
                        key={e.perfil}
                        disabled={busy}
                        onClick={() => handleSwitch(e.perfil)}
                        className="w-full text-left p-3 rounded-xl border border-slate-200 hover:border-[#1F6AA5] hover:bg-sky-50/40 transition flex items-center justify-between gap-2"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 shrink-0">
                            <GraduationCap className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-semibold text-slate-900 truncate">{e.etiqueta}</p>
                            <p className="text-xs text-slate-500 truncate">{e.detalle}</p>
                          </div>
                        </div>
                        {user?.usuario === e.perfil && <Badge variant="green">Activo</Badge>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          {tab === "datos" && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl border border-sky-200 bg-sky-50/50 space-y-3">
                <h4 className="text-sm font-bold text-[#154B75]">Cargar Simulación Completa (PostgreSQL)</h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Puebla en menos de 1 segundo <b>5 Facultades, 8 Programas, 120 Asignaturas, 240 Grupos</b> (sin clases
                  de 13:00 a 14:00) y <b>50 estudiantes sintéticos</b> encabezados por Alejandro Campo, Juan Esteban
                  Cardona y Diego Fernando Gómez.
                </p>
                <Button onClick={handlePoblar} disabled={busy} className="w-full">
                  <RefreshCw className={`w-4 h-4 ${busy ? "animate-spin" : ""}`} />
                  Poblar 50+ Estudiantes en PostgreSQL
                </Button>
              </div>

              <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/50 space-y-3">
                <h4 className="text-sm font-bold text-rose-800">Zona Segura: Vaciar Base de Datos</h4>
                <p className="text-xs text-rose-700 leading-relaxed">
                  Deja todas las tablas académicas en blanco (conserva cuentas <code>admin</code> y <code>profe</code>).
                  Para prevenir borrados accidentales, escribe <b>VACIAR</b> abajo:
                </p>
                <Input
                  value={confirmVaciar}
                  onChange={(e) => setConfirmVaciar(e.target.value)}
                  placeholder="Escribe VACIAR para habilitar"
                />
                <Button
                  variant="danger"
                  onClick={handleVaciar}
                  disabled={busy || confirmVaciar.trim().toUpperCase() !== "VACIAR"}
                  className="w-full"
                >
                  <Trash2 className="w-4 h-4" />
                  Confirmar Vaciado Total
                </Button>
              </div>
            </div>
          )}

          {tab === "servidor" && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase text-slate-500">Estado Actual</span>
                  {health?.database === "postgresql_connected" ? (
                    <Badge variant="green">PostgreSQL Conectado</Badge>
                  ) : (
                    <Badge variant="red">Sin Conexión</Badge>
                  )}
                </div>
                <p className="text-xs font-mono text-slate-700 break-all">{apiUrl}</p>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold uppercase text-slate-600">URL del Backend API (Plan B Sustentación)</label>
                <Input
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  placeholder="http://localhost:8000/api/v1"
                />
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCustomUrl("http://localhost:8000/api/v1")}
                  >
                    Docker Local
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCustomUrl(DEFAULT_API_URL)}
                  >
                    Servidor Nube
                  </Button>
                </div>
                <Button onClick={handleGuardarUrl} disabled={busy} className="w-full mt-2">
                  Guardar y Reconectar
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
