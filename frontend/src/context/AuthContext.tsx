import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getApiBaseUrl, getStoredToken, setApiBaseUrl, setStoredToken } from "@/lib/api";
import type { HealthStatus, UserInfo } from "@/types/api";

interface AuthContextValue {
  user: UserInfo | null;
  loading: boolean;
  health: HealthStatus | null;
  apiUrl: string;
  updateApiUrl: (url: string) => Promise<void>;
  login: (usuario: string, password: string) => Promise<UserInfo>;
  demoSwitch: (perfil: string) => Promise<UserInfo>;
  logout: () => void;
  refreshHealth: () => Promise<void>;
  dataVersion: number;
  bumpDataVersion: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [apiUrl, setApiUrlState] = useState(getApiBaseUrl());
  const [dataVersion, setDataVersion] = useState(0);

  const bumpDataVersion = useCallback(() => setDataVersion((v) => v + 1), []);

  const refreshHealth = useCallback(async () => {
    try {
      const h = await api.health();
      setHealth(h);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      await refreshHealth();
      const token = getStoredToken();
      if (token) {
        try {
          const u = await api.me();
          if (active) setUser(u);
        } catch {
          setStoredToken(null);
          if (active) setUser(null);
        }
      }
      if (active) setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [refreshHealth]);

  const login = useCallback(async (usuario: string, password: string) => {
    const res = await api.login(usuario, password);
    setStoredToken(res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const demoSwitch = useCallback(async (perfil: string) => {
    const res = await api.demoSwitch(perfil);
    setStoredToken(res.access_token);
    setUser(res.user);
    bumpDataVersion();
    return res.user;
  }, [bumpDataVersion]);

  const logout = useCallback(() => {
    setStoredToken(null);
    setUser(null);
  }, []);

  const updateApiUrl = useCallback(
    async (url: string) => {
      setApiBaseUrl(url);
      setApiUrlState(getApiBaseUrl());
      await refreshHealth();
      bumpDataVersion();
    },
    [refreshHealth, bumpDataVersion]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        health,
        apiUrl,
        updateApiUrl,
        login,
        demoSwitch,
        logout,
        refreshHealth,
        dataVersion,
        bumpDataVersion,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
