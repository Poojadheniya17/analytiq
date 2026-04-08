"use client";
// frontend/app/dashboard/forecast/page.tsx

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getForecast } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function ForecastPage() {
  const { user } = useAuth();
  const router   = useRouter();
  const [client, setClient]     = useState<any>(null);
  const [data, setData]         = useState<any>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  useEffect(() => {
    const s = localStorage.getItem("analytiq_client");
    if (s) { const c = JSON.parse(s); setClient(c); fetchForecast(c); }
  }, []);

  const fetchForecast = async (c: any) => {
    if (!user) return;
    setLoading(true); setError("");
    try {
      const res = await getForecast(user.id, c.name);
      setData(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to generate forecast. Run insights first.");
    } finally { setLoading(false); }
  };

  const allPoints = data ? [...(data.trend || []), ...(data.forecast || [])] : [];
  const maxRate   = allPoints.length ? Math.max(...allPoints.map((p: any) => p.churn_rate)) : 100;
  const chartH    = 200;

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Churn <span className="text-blue-600 italic">Forecast</span></h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">3-month projection · {client?.name} · {client?.domain}</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3 mb-5">
          {error}
          <button onClick={() => router.push("/dashboard/insights")} className="underline ml-2">Run insights first</button>
        </div>
      )}

      {loading ? (
        <div className="card text-center py-16">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-sm text-gray-400 font-mono">Calculating forecast...</div>
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="card border-t-2 border-t-blue-500">
              <div className="label">Current Churn Rate</div>
              <div className="text-3xl font-semibold text-gray-900">{data.current_churn_rate}%</div>
              <div className="text-xs text-gray-400 mt-1">Based on historical data</div>
            </div>
            <div className="card border-t-2 border-t-orange-500">
              <div className="label">3-Month Projection</div>
              <div className="text-3xl font-semibold text-gray-900">
                {data.forecast?.[2]?.churn_rate ?? "N/A"}%
              </div>
              <div className="text-xs text-gray-400 mt-1">Projected churn rate</div>
            </div>
            <div className="card border-t-2 border-t-green-500">
              <div className="label">Trend</div>
              <div className="text-3xl font-semibold text-gray-900">
                {data.forecast?.length && data.forecast[2]?.churn_rate > data.current_churn_rate ? "↑" : "↓"}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {data.forecast?.length && data.forecast[2]?.churn_rate > data.current_churn_rate ? "Increasing — action needed" : "Decreasing — good trend"}
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="text-sm font-medium text-gray-900">Churn Rate Over Time</div>
                <div className="text-xs text-gray-400 mt-0.5">Historical trend + 3-month forecast</div>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <div className="flex items-center gap-1.5"><div className="w-3 h-1 bg-blue-500 rounded"></div> Historical</div>
                <div className="flex items-center gap-1.5"><div className="w-3 h-1 bg-orange-400 rounded border-dashed border border-orange-400"></div> Forecast</div>
              </div>
            </div>

            {/* SVG Chart */}
            <div className="relative" style={{ height: `${chartH + 40}px` }}>
              <svg width="100%" height={chartH + 40} viewBox={`0 0 800 ${chartH + 40}`} preserveAspectRatio="none">
                {/* Grid lines */}
                {[0, 25, 50, 75, 100].map(pct => {
                  const y = chartH - (pct / 100) * chartH + 10;
                  return (
                    <g key={pct}>
                      <line x1="40" y1={y} x2="780" y2={y} stroke="#f3f4f6" strokeWidth="1" />
                      <text x="35" y={y + 4} textAnchor="end" fontSize="10" fill="#9ca3af">{pct}%</text>
                    </g>
                  );
                })}

                {/* Historical line */}
                {data.trend?.length > 1 && (() => {
                  const pts = data.trend.map((p: any, i: number) => {
                    const x = 40 + (i / (allPoints.length - 1)) * 740;
                    const y = chartH - (p.churn_rate / Math.max(maxRate, 1)) * (chartH - 20) + 10;
                    return `${x},${y}`;
                  }).join(" ");
                  return (
                    <>
                      <polyline points={pts} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinejoin="round" />
                      {data.trend.map((p: any, i: number) => {
                        const x = 40 + (i / (allPoints.length - 1)) * 740;
                        const y = chartH - (p.churn_rate / Math.max(maxRate, 1)) * (chartH - 20) + 10;
                        return <circle key={i} cx={x} cy={y} r="3" fill="#3b82f6" />;
                      })}
                    </>
                  );
                })()}

                {/* Forecast line */}
                {data.forecast?.length > 0 && (() => {
                  const lastTrend = data.trend?.[data.trend.length - 1];
                  const lastX = 40 + ((data.trend.length - 1) / (allPoints.length - 1)) * 740;
                  const lastY = chartH - (lastTrend?.churn_rate / Math.max(maxRate, 1)) * (chartH - 20) + 10;

                  const forecastPts = [
                    `${lastX},${lastY}`,
                    ...data.forecast.map((p: any, i: number) => {
                      const x = 40 + ((data.trend.length + i) / (allPoints.length - 1)) * 740;
                      const y = chartH - (p.churn_rate / Math.max(maxRate, 1)) * (chartH - 20) + 10;
                      return `${x},${y}`;
                    })
                  ].join(" ");

                  return (
                    <>
                      <polyline points={forecastPts} fill="none" stroke="#f97316" strokeWidth="2.5" strokeDasharray="6,4" strokeLinejoin="round" />
                      {data.forecast.map((p: any, i: number) => {
                        const x = 40 + ((data.trend.length + i) / (allPoints.length - 1)) * 740;
                        const y = chartH - (p.churn_rate / Math.max(maxRate, 1)) * (chartH - 20) + 10;
                        return (
                          <g key={i}>
                            <circle cx={x} cy={y} r="4" fill="white" stroke="#f97316" strokeWidth="2" />
                            <text x={x} y={y - 8} textAnchor="middle" fontSize="9" fill="#f97316" fontFamily="monospace">{p.churn_rate}%</text>
                          </g>
                        );
                      })}
                    </>
                  );
                })()}

                {/* Divider between historical and forecast */}
                {data.trend?.length > 0 && (
                  <line
                    x1={40 + ((data.trend.length - 1) / (allPoints.length - 1)) * 740}
                    y1="10"
                    x2={40 + ((data.trend.length - 1) / (allPoints.length - 1)) * 740}
                    y2={chartH + 10}
                    stroke="#e5e7eb"
                    strokeWidth="1"
                    strokeDasharray="4,3"
                  />
                )}
              </svg>
            </div>

            {/* AI Summary */}
            {data.summary && (
              <div className="mt-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
                <div className="text-xs font-mono text-blue-600 uppercase tracking-wider mb-1">Forecast Summary</div>
                <div className="text-sm text-gray-700">{data.summary}</div>
              </div>
            )}
          </div>

          {/* Data table */}
          <div className="grid grid-cols-2 gap-4">
            <div className="card">
              <div className="section-title">Historical trend</div>
              <div className="space-y-2">
                {data.trend?.slice(-6).map((p: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="text-xs font-mono text-gray-400 w-16">Month {p.month}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(p.churn_rate, 100)}%` }} />
                    </div>
                    <div className="text-xs font-mono text-gray-700 w-12 text-right">{p.churn_rate}%</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <div className="section-title">3-month forecast</div>
              <div className="space-y-2">
                {data.forecast?.map((p: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="text-xs font-mono text-gray-400 w-16">{p.month}</div>
                    <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                      <div className="h-full bg-orange-400 rounded-full" style={{ width: `${Math.min(p.churn_rate, 100)}%` }} />
                    </div>
                    <div className="text-xs font-mono text-orange-600 w-12 text-right font-medium">{p.churn_rate}%</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => router.push("/dashboard/recommendations")} className="btn-primary">Continue to Recommendations →</button>
            <button onClick={() => fetchForecast(client)} className="btn-secondary">Refresh forecast</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
