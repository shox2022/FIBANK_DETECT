import { createContext, useContext, useEffect, useMemo, useState } from "react";
import api from "../api";

const AuthContext = createContext(null);

function storedUser() {
  try {
    return JSON.parse(localStorage.getItem("aegis_user"));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("aegis_token"));
  const [user, setUser] = useState(storedUser());
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    let mounted = true;
    async function restore() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const response = await api.get("/api/auth/me");
        if (!mounted) return;
        setUser(response.data);
        localStorage.setItem("aegis_user", JSON.stringify(response.data));
      } catch {
        if (!mounted) return;
        logout();
      } finally {
        if (mounted) setLoading(false);
      }
    }
    restore();
    return () => {
      mounted = false;
    };
  }, [token]);

  async function login(email, password) {
    const response = await api.post("/api/auth/login", { email, password });
    const data = response.data;
    const nextUser = {
      id: data.user_id,
      name: data.name,
      email: data.email,
      role: data.role
    };
    localStorage.setItem("aegis_token", data.access_token);
    localStorage.setItem("aegis_user", JSON.stringify(nextUser));
    setToken(data.access_token);
    setUser(nextUser);
    return nextUser;
  }

  function logout() {
    localStorage.removeItem("aegis_token");
    localStorage.removeItem("aegis_user");
    setToken(null);
    setUser(null);
  }

  const value = useMemo(
    () => ({ token, user, loading, login, logout, isAuthenticated: Boolean(token && user) }),
    [token, user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

