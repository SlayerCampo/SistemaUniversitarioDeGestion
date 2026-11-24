import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { MatriculaPage } from "@/pages/MatriculaPage";
import { NotasPage } from "@/pages/NotasPage";
import { DocentePage } from "@/pages/DocentePage";
import { AdminPage } from "@/pages/AdminPage";
import { DescargasPage } from "@/pages/DescargasPage";

function ProtectedRoutes() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <img src="/logo_ucc.png" alt="UCC" className="w-14 h-14 object-contain animate-pulse" />
          <p className="text-sm font-semibold text-slate-600">Cargando Portal Académico UCC...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route element={user ? <AppShell /> : <Navigate to="/login" replace />}>
        <Route path="/" element={<DashboardPage />} />
        <Route
          path="/matricula"
          element={
            user && ["Estudiante", "Administrador"].includes(user.rol) ? (
              <MatriculaPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/notas"
          element={
            user && ["Estudiante", "Administrador"].includes(user.rol) ? (
              <NotasPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/docente"
          element={
            user && ["Profesor", "Administrador"].includes(user.rol) ? (
              <DocentePage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/admin"
          element={user?.rol === "Administrador" ? <AdminPage /> : <Navigate to="/" replace />}
        />
        <Route path="/descargas" element={<DescargasPage />} />
      </Route>
      <Route path="*" element={<Navigate to={user ? "/" : "/login"} replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ProtectedRoutes />
        <Toaster position="top-right" richColors closeButton />
      </BrowserRouter>
    </AuthProvider>
  );
}
