import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  CheckCircle2,
  GraduationCap,
  Lock,
  Monitor,
  Settings2,
  Shield,
  Smartphone,
  Sparkles,
  User,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { api, DEFAULT_API_URL } from "@/lib/api";
import type { DemoPerfilesResponse } from "@/types/api";
import { Badge, Button, Card, Field, Input } from "@/components/ui/Primitives";

export function LoginPage() {
  const { login, demoSwitch, health, apiUrl, updateApiUrl } = useAuth();
  const navigate = useNavigate();

  const [usuario, setUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [perfiles, setPerfiles] = useState<DemoPerfilesResponse | null>(null);
  const [showApiConfig, setShowApiConfig] = useState(false);
  const [customUrl, setCustomUrl] = useState(apiUrl);

  useEffect(() => {
    api
      .demoPerfiles()
      .then(setPerfiles)
      .catch(() => setPerfiles(null));
  }, [apiUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!usuario.trim() || !password.trim()) {
      toast.error("Ingresa tu usuario/ID y contraseña.");
      return;
    }
    setBusy(true);
    try {
      const u = await login(usuario.trim(), password.trim());
      toast.success(`Bienvenido(a), ${u.nombre_completo}`);
      navigate("/");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const handleQuickDemo = async (perfil: string) => {
    setBusy(true);
    try {
      const u = await demoSwitch(perfil);
      toast.success(`Ingreso rápido: ${u.nombre_completo} (${u.rol})`);
      navigate("/");
    } catch (err) {
      toast.error((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-sky-50/40 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 bg-white rounded-3xl shadow-xl border border-slate-200/80 overflow-hidden">
        {/* PANEL IZQUIERDO — IDENTIDAD UCC */}
        <div className="lg:col-span-5 bg-gradient-to-br from-[#1F6AA5] via-[#154B75] to-[#0F3454] text-white p-7 sm:p-9 flex flex-col justify-between gap-8">
          <div className="space-y-6">
            <div className="flex items-center gap-3.5">
              <div className="bg-white p-2 rounded-2xl shadow-md">
                <img src="/logo_ucc.png" alt="Logo UCC" className="w-11 h-11 object-contain" />
              </div>
              <div>
                <p className="font-display font-extrabold text-base leading-tight">
                  Universidad Cooperativa de Colombia
                </p>
                <p className="text-xs text-sky-200 font-medium">Campus Cali · Facultad de Ingeniería</p>
              </div>
            </div>

            <div className="space-y-2.5">
              <h1 className="font-display text-2xl sm:text-3xl font-extrabold leading-tight tracking-tight">
                Portal de Gestión Académica y Matrículas
              </h1>
              <p className="text-sm text-sky-100/90 leading-relaxed">
                Plataforma unificada sobre <b>PostgreSQL</b> con control atómico de cupos, validador matemático de
                horarios sin clases en almuerzo (13:00–14:00), certificados PDF y centro ETL Excel.
              </p>
            </div>

            <div className="space-y-2.5 pt-2">
              {[
                "Misma experiencia en Web, Windows (.exe) y Android (.apk)",
                "Matrícula en 4 pasos (6 a 19 créditos) con horario visual",
                "Seguridad por roles (RBAC) con contraseñas bcrypt y JWT",
              ].map((txt) => (
                <div key={txt} className="flex items-start gap-2.5 text-xs text-sky-100">
                  <CheckCircle2 className="w-4 h-4 text-[#36B5C6] shrink-0 mt-0.5" />
                  <span>{txt}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-3 pt-4 border-t border-white/15">
            <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10">
                <Monitor className="w-3.5 h-3.5 text-[#36B5C6]" /> Web & Windows
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10">
                <Smartphone className="w-3.5 h-3.5 text-[#36B5C6]" /> Android APK
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10">
                <span
                  className={`w-2 h-2 rounded-full ${
                    health?.database === "postgresql_connected" ? "bg-emerald-400" : "bg-rose-400"
                  }`}
                />
                {health?.database === "postgresql_connected" ? "PostgreSQL Activo" : "API Desconectada"}
              </span>
            </div>
            <p className="text-[11px] text-sky-200/80">
              Alejandro Campo · Juan Esteban Cardona · Diego Fernando Gómez
            </p>
          </div>
        </div>

        {/* PANEL DERECHO — FORMULARIO + MODO EXPOSICIÓN */}
        <div className="lg:col-span-7 p-6 sm:p-10 flex flex-col justify-between gap-6">
          <div className="space-y-6">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-xl sm:text-2xl font-extrabold text-slate-900">Iniciar Sesión</h2>
                <p className="text-sm text-slate-500 mt-0.5">
                  Ingresa con tu cuenta institucional o tu ID de estudiante.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowApiConfig((v) => !v)}
                className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:text-[#1F6AA5] hover:border-[#1F6AA5] transition"
                title="Configurar servidor API (Nube / Docker local)"
              >
                <Settings2 className="w-4 h-4" />
              </button>
            </div>

            {showApiConfig && (
              <Card className="p-4 bg-slate-50 space-y-2.5">
                <p className="text-xs font-bold uppercase text-slate-600">URL del Servidor Backend (Plan B)</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <Input
                    value={customUrl}
                    onChange={(e) => setCustomUrl(e.target.value)}
                    placeholder="http://localhost:8000/api/v1"
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={async () => {
                      await updateApiUrl(customUrl);
                      toast.success("URL de servidor actualizada.");
                    }}
                  >
                    Aplicar
                  </Button>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setCustomUrl("http://localhost:8000/api/v1")}
                    className="text-xs font-semibold text-[#1F6AA5] hover:underline"
                  >
                    Usar Docker Local
                  </button>
                  <span className="text-slate-300">·</span>
                  <button
                    type="button"
                    onClick={() => setCustomUrl(DEFAULT_API_URL)}
                    className="text-xs font-semibold text-[#1F6AA5] hover:underline"
                  >
                    Restaurar por defecto
                  </button>
                </div>
              </Card>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Field label="Usuario o ID de Estudiante">
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <Input
                    value={usuario}
                    onChange={(e) => setUsuario(e.target.value)}
                    placeholder="Ej: admin, profe o 1001"
                    className="pl-10"
                    autoComplete="username"
                  />
                </div>
              </Field>

              <Field label="Contraseña">
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Ej: 1234"
                    className="pl-10"
                    autoComplete="current-password"
                  />
                </div>
              </Field>

              <Button type="submit" size="lg" disabled={busy} className="w-full">
                {busy ? "Verificando credenciales..." : "Ingresar al Portal"}
              </Button>
            </form>

            {/* CENTRO DE ACCESO RÁPIDO PARA EXPOSICIÓN */}
            {(perfiles?.demo_mode ?? health?.demo_mode) && (
              <div className="pt-4 border-t border-slate-200/80 space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#154B75]">
                    <Sparkles className="w-3.5 h-3.5" />
                    Acceso Rápido — Modo Exposición
                  </div>
                  <Badge variant="cyan">1 clic</Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => handleQuickDemo("admin")}
                    className="p-3 rounded-xl border border-slate-200 hover:border-[#1F6AA5] hover:bg-sky-50/50 text-left transition"
                  >
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                      <Shield className="w-4 h-4 text-[#3B1C7A]" />
                      Administrador
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">CRUD, ETL y Analítica</p>
                  </button>

                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => handleQuickDemo("profe")}
                    className="p-3 rounded-xl border border-slate-200 hover:border-[#1F6AA5] hover:bg-sky-50/50 text-left transition"
                  >
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                      <User className="w-4 h-4 text-[#0E7490]" />
                      Docente UCC
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">Planillas y Notas</p>
                  </button>

                  <button
                    type="button"
                    disabled={busy || !perfiles?.estudiantes?.length}
                    onClick={() => handleQuickDemo(perfiles?.estudiantes[0]?.perfil || "1001")}
                    className="p-3 rounded-xl border border-slate-200 hover:border-[#1F6AA5] hover:bg-sky-50/50 text-left transition disabled:opacity-50"
                  >
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                      <GraduationCap className="w-4 h-4 text-emerald-700" />
                      Estudiante 1001
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 truncate">
                      {perfiles?.estudiantes?.length ? "Alejandro Campo" : "Poblar BD primero"}
                    </p>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
