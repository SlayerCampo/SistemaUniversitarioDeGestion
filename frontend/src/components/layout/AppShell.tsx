import React, { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  BookOpenCheck,
  ClipboardList,
  Download,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Settings,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { isCapacitorApp, isTauriApp } from "@/lib/platform";
import { Badge, Button, cn } from "@/components/ui/Primitives";
import { DemoDrawer } from "@/components/demo/DemoDrawer";

interface NavItem {
  to: string;
  label: string;
  shortLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: string[];
  hideInNative?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Inicio y Oferta", shortLabel: "Inicio", icon: LayoutDashboard },
  { to: "/matricula", label: "Matrícula", shortLabel: "Matrícula", icon: GraduationCap, roles: ["Estudiante", "Administrador"] },
  { to: "/notas", label: "Notas y Boletín", shortLabel: "Notas", icon: BookOpenCheck, roles: ["Estudiante", "Administrador"] },
  { to: "/docente", label: "Panel Docente", shortLabel: "Docente", icon: ClipboardList, roles: ["Profesor", "Administrador"] },
  { to: "/admin", label: "Administración", shortLabel: "Admin", icon: Settings, roles: ["Administrador"] },
  { to: "/descargas", label: "Apps PC / Android", shortLabel: "Apps", icon: Download, hideInNative: true },
];

export function AppShell() {
  const { user, logout, health } = useAuth();
  const [demoOpen, setDemoOpen] = useState(false);
  const location = useLocation();
  const isNative = isTauriApp() || isCapacitorApp();

  const items = NAV_ITEMS.filter((item) => {
    if (item.hideInNative && isNative) return false;
    if (!item.roles) return true;
    return user ? item.roles.includes(user.rol) : false;
  });

  const currentItem = items.find((i) => i.to === location.pathname) || items[0];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col lg:flex-row">
      {/* SIDEBAR ESCRITORIO (PC / TAURI) */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white border-r border-slate-200 z-30">
        <div className="p-5 flex items-center gap-3 border-b border-slate-100">
          <img src="/logo_ucc.png" alt="Logo UCC" className="w-10 h-10 object-contain shrink-0" />
          <div className="min-w-0">
            <p className="font-display font-extrabold text-sm text-[#154B75] leading-tight truncate">
              Universidad Cooperativa
            </p>
            <p className="text-[11px] text-slate-500 font-medium">Sede Cali · Portal v2.0</p>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all",
                  isActive
                    ? "bg-[#1F6AA5] text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )
              }
            >
              <item.icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Tarjeta de usuario */}
        <div className="p-3.5 border-t border-slate-100 bg-slate-50/70 space-y-2.5">
          {user && (
            <div className="p-3 rounded-xl bg-white border border-slate-200/80">
              <div className="flex items-center justify-between gap-2 mb-1">
                <Badge variant={user.rol === "Administrador" ? "purple" : user.rol === "Profesor" ? "cyan" : "green"}>
                  {user.rol}
                </Badge>
                {user.es_demo && <Badge variant="amber">Demo</Badge>}
              </div>
              <p className="text-xs font-bold text-slate-900 truncate">{user.nombre_completo}</p>
              <p className="text-[11px] text-slate-500 truncate">
                ID: {user.usuario} {user.nombre_programa ? `· ${user.nombre_programa}` : ""}
              </p>
            </div>
          )}
          <Button variant="outline" size="sm" onClick={logout} className="w-full text-rose-700 hover:bg-rose-50 hover:border-rose-200">
            <LogOut className="w-3.5 h-3.5" />
            Cerrar Sesión
          </Button>
        </div>
      </aside>

      {/* CONTENEDOR PRINCIPAL */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* TOPBAR LIMPIO */}
        <header className="sticky top-0 z-20 bg-white/90 backdrop-blur-md border-b border-slate-200/80 safe-top">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <img src="/logo_ucc.png" alt="UCC" className="w-8 h-8 object-contain lg:hidden shrink-0" />
              <div className="min-w-0">
                <h1 className="font-display font-bold text-sm sm:text-lg text-slate-900 truncate">
                  {currentItem?.label || "Portal Académico UCC"}
                </h1>
                <p className="text-[11px] text-slate-500 hidden sm:block">
                  Sistema de Gestión Académica · PostgreSQL en tiempo real
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span
                title={health?.database === "postgresql_connected" ? "PostgreSQL conectado" : "Sin conexión al API"}
                className={cn(
                  "hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border",
                  health?.database === "postgresql_connected"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : "bg-rose-50 text-rose-800 border-rose-200"
                )}
              >
                <span
                  className={cn(
                    "w-2 h-2 rounded-full",
                    health?.database === "postgresql_connected" ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
                  )}
                />
                PostgreSQL
              </span>

              {(health?.demo_mode ?? true) && (
                <Button size="sm" variant="outline" onClick={() => setDemoOpen(true)} className="border-sky-200 bg-sky-50/70 text-[#154B75] hover:bg-sky-100">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Modo Demo</span>
                </Button>
              )}

              <button
                onClick={logout}
                className="lg:hidden p-2 rounded-xl text-slate-500 hover:text-rose-700 hover:bg-rose-50 transition"
                aria-label="Cerrar sesión"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </header>

        {/* CONTENIDO DE PÁGINA */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-5 sm:py-7 pb-24 lg:pb-10">
          <Outlet />
        </main>
      </div>

      {/* BARRA INFERIOR FIJA PARA CELULAR / ANDROID APK */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-white/95 backdrop-blur-md border-t border-slate-200 safe-bottom shadow-[0_-4px_16px_rgba(15,23,42,0.06)]">
        <div className="flex items-center justify-around px-1 pt-1.5">
          {items.slice(0, 5).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex flex-col items-center justify-center gap-0.5 py-1 px-2 rounded-xl min-w-[58px] transition-colors",
                  isActive ? "text-[#1F6AA5]" : "text-slate-500 hover:text-slate-800"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <div className={cn("p-1.5 rounded-xl transition", isActive && "bg-sky-50")}>
                    <item.icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-bold leading-none">{item.shortLabel}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      <DemoDrawer open={demoOpen} onClose={() => setDemoOpen(false)} />
    </div>
  );
}
