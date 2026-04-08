"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface User {
  id:       number;
  username: string;
  email:    string;
}

interface AuthContextType {
  user:    User | null;
  loading: boolean;
  login:   (userData: User) => void;
  logout:  () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user:    null,
  loading: true,
  login:   () => {},
  logout:  async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]       = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // On mount — verify JWT cookie with backend
    // This replaces the insecure localStorage check
    axios.get(`${API}/api/auth/me`, { withCredentials: true })
      .then(res => setUser(res.data.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = (userData: User) => {
    // JWT cookie is set by backend — we just store user data in state
    // No localStorage — no XSS risk
    setUser(userData);
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/api/auth/logout`, {}, { withCredentials: true });
    } catch {}
    setUser(null);
    window.location.href = "/";
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
