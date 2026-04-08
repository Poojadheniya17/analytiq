"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend
} from "recharts";

const API = "http://localhost:8000";

function safe(val: any): string {
  if (val === null || val === undefined) return "—";
  if (typeof val === "object") return "—";
  return String(val);
}

function fmt(key: string, val: any): string {
  if (val === null || val === undefined || typeof val === "object") return "—";
  const n = Number(val);
  if (isNaN(n)) return String(val);
  if (key.includes("rate") || key.includes("%")) return n.toFixed(2) + "%";
  if (key.includes("avg")) return n.toFixed(2);
  return n.toLocaleString();
}

export default function InteractiveDashboardPage() {
  const { user } = useAuth();
  const router   = useRouter();

  const [client, setClient]           = useState<any>(null);
  const [config, setConfig]           = useState<any>(null);
  const [data, setData]               = useState<any>(null);
  const [filters, setFilters]         = useState<Record<string, string>>({});
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState("");
  const [activeChart, setActiveChart] = useState(0);
  const [activeBar, setActiveBar]     = useState<string | null>(null);
  const [mounted, setMounted]         = useState(false);

  useEffect(() => {
    setMounted(true);
    const s = localStorage.getItem("analytiq_client");
    if (s) {
      const c = JSON.parse(s);
      setClient(c);
      loadDashboard(c);
    } else {
      setLoading(false);
    }
  }, []);

  async function loadDashboard(c: any) {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      const [cfgRes, dataRes] = await Promise.all([
        axios.post(`${API}/api/dashboard/config`, { user_id: user.id, client_name: c.name }),
        axios.post(`${API}/api/dashboard/data`,   { user_id: user.id, client_name: c.name }),
      ]);
      setConfig(cfgRes.data);
      setData(dataRes.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not load dashboard. Run insights first.");
    } finally {
      setLoading(false);
    }
  }

  async function applyFilters(newFilters: Record<string, string>) {
    if (!client || !user) return;
    try {
      const res = await axios.post(`${API}/api/dashboard/filtered`, {
        user_id:     user.id,
        client_name: client.name,
        filters:     newFilters,
      });
      setData(res.data);
    } catch {}
  }

  function handleFilterChange(col: string, value: string) {
    const f = { ...filters };
    if (value === "All") delete f[col];
    else f[col] = value;
    setFilters(f);
    applyFilters(f);
  }

  function handleBarClick(barData: any, col: string) {
    if (!barData?.activeLabel) return;
    const value = String(barData.activeLabel);
    if (activeBar === value) {
      setActiveBar(null);
      const f = { ...filters };
      delete f[col];
      setFilters(f);
      applyFilters(f);
    } else {
      setActiveBar(value);
      const f = { ...filters, [col]: value };
      setFilters(f);
      applyFilters(f);
    }
  }

  function clearFilters() {
    setFilters({});
    setActiveBar(null);
    if (client && user) {
      axios.post(`${API}/api/dashboard/data`, { user_id: user.id, client_name: client.name })
        .then(r => setData(r.data))
        .catch(() => {});
    }
  }

  if (!mounted) return null;

  if (loading) return (
    <div className="p-8 flex items-center justify-center min-h-96">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <div className="text-sm text-gray-400 font-mono">Building interactive dashboard...</div>
      </div>
    </div>
  );

  if (error) return (
    <div className="p-8">
      <div className="card text-center py-16 border-dashed">
        <div className="text-3xl text-gray-200 mb-4">▦</div>
        <div className="text-sm font-medium text-gray-600 mb-2">{error}</div>
        <button onClick={() => router.push("/dashboard/insights")} className="btn-primary mt-4">
          Go to Insights first
        </button>
      </div>
    </div>
  );

  if (!data) return null;

  const hasFilters  = Object.keys(filters).length > 0;
  const targetCol   = safe(data.target_col);
  const targetLabel = targetCol.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase());
  const kpis        = data.kpis || {};
  const barCharts   = Array.isArray(data.bar_charts) ? data.bar_charts : [];
  const lineChart   = Array.isArray(data.line_chart) ? data.line_chart : [];
  const totalPos    = typeof kpis.total_positive === "number" ? kpis.total_positive : 0;
  const totalNeg    = typeof kpis.total_negative === "number" ? kpis.total_negative : 0;
  const kpiKeys     = Object.keys(kpis).slice(0, 4);

  const borderColors = [
    "border-t-blue-500",
    "border-t-red-500",
    "border-t-orange-500",
    "border-t-green-500",
  ];

  return (
    <div className="p-6 space-y-5">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Interactive <span className="text-blue-600 italic">Dashboard</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1 font-mono">
            {safe(client?.name)} · {safe(client?.domain)} · {Number(data.filtered_rows || 0).toLocaleString()} records
            {hasFilters && <span className="text-blue-600 ml-2">(filtered)</span>}
          </p>
        </div>
        {hasFilters && (
          <button onClick={clearFilters}
            className="text-xs text-red-500 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors">
            ✕ Clear filters
          </button>
        )}
      </div>

      {/* Filters */}
      {config?.filter_cols?.length > 0 && (
        <div className="card">
          <div className="section-title mb-3">Filters · click any bar in the chart to filter automatically</div>
          <div className="flex flex-wrap gap-4">
            {config.filter_cols.map((fc: any) => (
              <div key={safe(fc.column)}>
                <label className="text-xs text-gray-400 font-mono block mb-1">
                  {safe(fc.column).replace(/_/g, " ")}
                </label>
                <select
                  value={filters[fc.column] || "All"}
                  onChange={e => handleFilterChange(safe(fc.column), e.target.value)}
                  className="input h-8 text-xs px-2 w-40">
                  <option value="All">All</option>
                  {(fc.values || []).map((v: any) => (
                    <option key={safe(v)} value={safe(v)}>{safe(v)}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          {hasFilters && (
            <div className="mt-3 flex flex-wrap gap-2">
              {Object.entries(filters).map(([col, val]) => (
                <span key={col}
                  className="inline-flex items-center gap-1.5 text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-full">
                  {col.replace(/_/g, " ")}: <strong>{val}</strong>
                  <button onClick={() => handleFilterChange(col, "All")}
                    className="ml-1 text-blue-400 hover:text-blue-700">✕</button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        {kpiKeys.map((key, i) => (
          <div key={key} className={`card border-t-2 ${borderColors[i] || "border-t-gray-300"}`}>
            <div className="label truncate">{key.replace(/_/g, " ").replace(/%/g, "")}</div>
            <div className="text-2xl font-semibold text-gray-900">{fmt(key, kpis[key])}</div>
            {hasFilters && <div className="text-xs text-blue-500 font-mono mt-1">filtered</div>}
          </div>
        ))}
      </div>

      {/* Bar Charts */}
      {barCharts.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-medium text-gray-900">{targetLabel} Rate by Segment</div>
              <div className="text-xs text-gray-400 mt-0.5">Click any bar to filter the entire dashboard</div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {barCharts.map((chart: any, i: number) => (
                <button key={i}
                  onClick={() => { setActiveChart(i); setActiveBar(null); }}
                  className={`text-xs px-3 py-1.5 rounded-lg font-mono transition-colors
                    ${activeChart === i ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-500 hover:bg-gray-200"}`}>
                  {safe(chart.column).replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>

          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={barCharts[activeChart]?.data || []}
              onClick={(d) => handleBarClick(d, safe(barCharts[activeChart]?.column))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#6B7280" }} />
              <YAxis tick={{ fontSize: 11, fill: "#6B7280" }} unit="%" />
              <Tooltip
                formatter={(value: any) => [Number(value).toFixed(2) + "%", targetLabel + " Rate"]}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E5E7EB" }}
              />
              <Bar dataKey="target_rate" radius={[4, 4, 0, 0]}>
                {(barCharts[activeChart]?.data || []).map((entry: any, idx: number) => (
                  <Cell
                    key={idx}
                    fill={activeBar === entry.name ? "#EF4444" : "#2563EB"}
                    opacity={activeBar && activeBar !== entry.name ? 0.4 : 1}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {activeBar && (
            <div className="mt-2 text-center text-xs text-blue-600 font-mono">
              Filtered: {safe(barCharts[activeChart]?.column).replace(/_/g, " ")} = {activeBar} · click bar again to clear
            </div>
          )}
        </div>
      )}

      {/* Line Chart + Pie Chart */}
      <div className="grid grid-cols-2 gap-5">

        {lineChart.length > 0 && lineChart[0]?.data?.length > 0 && (
          <div className="card">
            <div className="text-sm font-medium text-gray-900 mb-1">
              {targetLabel} Rate Trend
            </div>
            <div className="text-xs text-gray-400 mb-4">
              Across {safe(lineChart[0].column).replace(/_/g, " ")}
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={lineChart[0].data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="avg_value" tick={{ fontSize: 10, fill: "#6B7280" }}
                  tickFormatter={(v) => typeof v === "number" ? v.toFixed(0) : String(v)} />
                <YAxis tick={{ fontSize: 10, fill: "#6B7280" }} unit="%" />
                <Tooltip
                  formatter={(v: any) => [Number(v).toFixed(2) + "%", targetLabel + " Rate"]}
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #E5E7EB" }}
                />
                <Line type="monotone" dataKey="target_rate"
                  stroke="#2563EB" strokeWidth={2.5}
                  dot={{ r: 4, fill: "#2563EB" }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="card">
          <div className="text-sm font-medium text-gray-900 mb-4">Positive vs Negative Split</div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={[
                  { name: "Negative", value: totalNeg },
                  { name: "Positive", value: totalPos },
                ]}
                cx="50%" cy="50%"
                innerRadius={50} outerRadius={75}
                dataKey="value" paddingAngle={3}>
                <Cell fill="#10B981" />
                <Cell fill="#EF4444" />
              </Pie>
              <Tooltip formatter={(v: any) => Number(v).toLocaleString()} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2 border-t border-gray-100 pt-4">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Total records</span>
              <span className="font-medium text-gray-900">{Number(data.filtered_rows || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">{targetLabel} rate</span>
              <span className="font-medium text-red-600">{fmt("target_rate_%", kpis["target_rate_%"])}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Active filters</span>
              <span className="font-medium text-blue-600">{Object.keys(filters).length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <button onClick={() => router.push("/dashboard/simulator")} className="btn-primary">
          What-If Simulator →
        </button>
        <button onClick={clearFilters} disabled={!hasFilters} className="btn-secondary">
          Reset all filters
        </button>
      </div>

    </div>
  );
}
