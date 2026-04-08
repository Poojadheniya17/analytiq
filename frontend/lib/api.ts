import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL:         API_URL,
  withCredentials: true,   // sends JWT cookie on every request
});

// ── Auth ──────────────────────────────────────────────────────
export const loginUser  = (username: string, password: string) =>
  api.post("/api/auth/login",  { username, password });

export const signupUser = (username: string, email: string, password: string) =>
  api.post("/api/auth/signup", { username, email, password });

export const logoutUser = () =>
  api.post("/api/auth/logout");

export const getMe = () =>
  api.get("/api/auth/me");

// ── Clients ───────────────────────────────────────────────────
export const getClients   = (userId: number) =>
  api.get(`/api/clients/${userId}`);

export const createClient = (userId: number, name: string, domain: string) =>
  api.post("/api/clients/", { user_id: userId, name, domain });

export const deleteClient = (clientId: number, userId: number) =>
  api.delete(`/api/clients/${clientId}?user_id=${userId}`);

// ── Analysis ──────────────────────────────────────────────────
export const uploadFile = (userId: number, clientName: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.post(`/api/clients/${userId}/${clientName}/upload`, form);
};

export const cleanData   = (userId: number, clientName: string) =>
  api.post("/api/analysis/clean",    { user_id: userId, client_name: clientName });

export const runInsights = (userId: number, clientName: string) =>
  api.post("/api/analysis/insights", { user_id: userId, client_name: clientName });

export const trainModel  = (userId: number, clientName: string) =>
  api.post("/api/analysis/train",    { user_id: userId, client_name: clientName });

export const getStatus   = (userId: number, clientName: string) =>
  api.get(`/api/analysis/status/${userId}/${clientName}`);

export const getDataQuality = (userId: number, clientName: string) =>
  api.get(`/api/clients/${userId}/${clientName}/quality`);

// ── AI ────────────────────────────────────────────────────────
export const askQuestion       = (userId: number, clientName: string, question: string) =>
  api.post("/api/ai/query",     { user_id: userId, client_name: clientName, question });

export const generateNarrative = (userId: number, clientName: string, domain: string) =>
  api.post("/api/ai/narrative", { user_id: userId, client_name: clientName, domain });

export const getNarrative      = (userId: number, clientName: string) =>
  api.get(`/api/ai/narrative/${userId}/${clientName}`);

// ── Export ────────────────────────────────────────────────────
export const exportPDF   = (userId: number, clientName: string, domain: string) =>
  api.post("/api/export/pdf",   { user_id: userId, client_name: clientName, domain }, { responseType: "blob" });

export const exportExcel = (userId: number, clientName: string, domain: string) =>
  api.post("/api/export/excel", { user_id: userId, client_name: clientName, domain }, { responseType: "blob" });

// ── Forecast ──────────────────────────────────────────────────
export const getForecast = (userId: number, clientName: string) =>
  api.post("/api/forecast/churn", { user_id: userId, client_name: clientName });

// ── Dashboard ─────────────────────────────────────────────────
export const getDashboardConfig  = (userId: number, clientName: string) =>
  api.post("/api/dashboard/config",   { user_id: userId, client_name: clientName });

export const getDashboardData    = (userId: number, clientName: string) =>
  api.post("/api/dashboard/data",     { user_id: userId, client_name: clientName });

export const getFilteredData     = (userId: number, clientName: string, filters: Record<string, string>) =>
  api.post("/api/dashboard/filtered", { user_id: userId, client_name: clientName, filters });

// ── Simulator ─────────────────────────────────────────────────
export const getSimulatorConfig = (userId: number, clientName: string) =>
  api.post("/api/simulator/config",  { user_id: userId, client_name: clientName });

export const simulatorPredict   = (userId: number, clientName: string, features: Record<string, any>) =>
  api.post("/api/simulator/predict", { user_id: userId, client_name: clientName, features });

export default api;
