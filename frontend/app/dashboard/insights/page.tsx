"use client";
// frontend/app/dashboard/insights/page.tsx

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { runInsights, getStatus } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const LOADING_STEPS = [
  "Reading your dataset...",
  "Detecting target column...",
  "Calculating KPIs...",
  "Running segment analysis...",
  "Detecting anomalies...",
  "Generating charts...",
  "Saving insights...",
];

export default function InsightsPage() {
  const { user }  = useAuth();
  const router    = useRouter();
  const [client, setClient]       = useState<any>(null);
  const [status, setStatus]       = useState<any>(null);
  const [running, setRunning]     = useState(false);
  const [error, setError]         = useState("");
  const [step, setStep]           = useState(0);
  const [stepMsg, setStepMsg]     = useState("");

  useEffect(() => {
    const s = localStorage.getItem("analytiq_client");
    if (s) { const c = JSON.parse(s); setClient(c); fetchStatus(c); }
  }, []);

  const fetchStatus = async (c: any) => {
    if (!user) return;
    try { const res = await getStatus(user.id, c.name); setStatus(res.data); } catch {}
  };

  const handleRun = async () => {
    if (!client || !user) return;
    setRunning(true); setError(""); setStep(0);
    const interval = setInterval(() => {
      setStep(prev => {
        const next = prev < LOADING_STEPS.length - 1 ? prev + 1 : prev;
        setStepMsg(LOADING_STEPS[next]);
        return next;
      });
    }, 800);
    try {
      setStepMsg(LOADING_STEPS[0]);
      await runInsights(user.id, client.name);
      clearInterval(interval);
      fetchStatus(client);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to generate insights.");
    } finally { clearInterval(interval); setRunning(false); }
  };

  const getChartUrl = (chart: string) => {
  if (!user || !client) return "";
  const safe = client.name.toLowerCase().replace(/ /g, "_");
  return `${process.env.NEXT_PUBLIC_API_URL}/static/users/${user.id}/${safe}/charts/${chart}`;
};

  const ins = status?.insights;

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Business <span className="text-blue-600 italic">Insights</span></h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">Auto-generated analysis · {client?.name} · {client?.domain}</p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3 mb-5">{error}</div>}

      {!status?.has_data ? (
        <div className="card text-center py-12 border-dashed">
          <div className="text-sm text-gray-500 mb-3">No data found for this client</div>
          <button onClick={() => router.push("/dashboard/upload")} className="btn-primary">Go to Upload</button>
        </div>
      ) : !status?.has_insights && !running ? (
        <div className="card text-center py-16">
          <div className="text-3xl text-gray-200 mb-4">◎</div>
          <div className="text-sm font-medium text-gray-600 mb-2">Ready to analyse</div>
          <div className="text-xs text-gray-400 mb-6 max-w-sm mx-auto">Auto-generates KPIs, segment breakdowns, anomaly detection, and visual charts</div>
          <button onClick={handleRun} className="btn-primary">Generate Insights</button>
        </div>
      ) : running ? (
        <div className="card text-center py-16">
          <div className="w-10 h-10 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-5"></div>
          <div className="text-sm font-medium text-gray-700 mb-2">Analysing your data</div>
          <div className="text-xs text-blue-600 font-mono mb-6">{stepMsg}</div>
          <div className="flex justify-center gap-1.5 mb-2">
            {LOADING_STEPS.map((_, i) => (
              <div key={i} className={`h-1 w-8 rounded-full transition-colors duration-300 ${i <= step ? "bg-blue-500" : "bg-gray-200"}`} />
            ))}
          </div>
          <div className="text-xs text-gray-400 font-mono">{step + 1} of {LOADING_STEPS.length} steps</div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* KPIs */}
          <div>
            <div className="section-title">Key performance indicators</div>
            <div className="grid grid-cols-4 gap-4">
              {ins && Object.entries(ins.kpis).slice(0, 8).map(([k, v]: any) => (
                <div key={k} className="card">
                  <div className="label truncate">{k.replace(/_/g, " ")}</div>
                  <div className="text-xl font-semibold text-gray-900">{typeof v === "number" ? v.toLocaleString() : v}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Charts */}
          {status?.charts?.length > 0 && (
            <div>
              <div className="section-title">Visual insights</div>
              <div className="grid grid-cols-2 gap-4">
                {status.charts.map((chart: string) => (
                  <div key={chart} className="card p-3">
                    <div className="text-xs font-mono text-gray-400 mb-2">{chart.replace(/_/g, " ").replace(".png", "")}</div>
                    <img
                      src={getChartUrl(chart)}
                      alt={chart}
                      className="w-full rounded-lg"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Segments */}
          {ins?.segment_insights?.length > 0 && (
            <div>
              <div className="section-title">Segment breakdown</div>
              <div className="grid grid-cols-2 gap-4">
                {ins.segment_insights.slice(0, 4).map((seg: any) => (
                  <div key={seg.segment} className="card">
                    <div className="text-xs font-mono text-gray-400 uppercase tracking-wide mb-3">{seg.segment.replace(/_/g, " ")}</div>
                    <div className="text-xs text-gray-500 mb-3">
                      Highest risk: <span className="font-medium text-gray-900">{seg.highest_churn_value}</span>
                      {" "}at <span className="text-red-600 font-medium">{seg["highest_churn_rate_%"]}%</span>
                    </div>
                    <div className="space-y-2">
                      {seg.full_breakdown?.slice(0, 5).map((item: any, i: number) => (
                        <div key={i} className="flex items-center gap-2">
                          <div className="text-xs text-gray-500 w-28 truncate">{String(item[seg.segment])}</div>
                          <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                            <div className="h-full rounded-full bg-blue-500 transition-all duration-700"
                              style={{ width: `${Math.min(item["churn_rate_%"], 100)}%` }} />
                          </div>
                          <div className="text-xs font-mono text-gray-600 w-10 text-right">{item["churn_rate_%"]}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Anomalies */}
          {ins?.anomalies?.length > 0 && (
            <div>
              <div className="section-title">Anomaly detection</div>
              <div className="card">
                <table className="w-full text-xs">
                  <thead><tr className="border-b border-gray-100">
                    <th className="text-left py-2 font-mono text-gray-400 font-normal">Column</th>
                    <th className="text-left py-2 font-mono text-gray-400 font-normal">Outliers</th>
                    <th className="text-left py-2 font-mono text-gray-400 font-normal">Percentage</th>
                  </tr></thead>
                  <tbody>
                    {ins.anomalies.map((a: any) => (
                      <tr key={a.column} className="border-b border-gray-50">
                        <td className="py-2 font-mono text-gray-700">{a.column}</td>
                        <td className="py-2 text-gray-600">{a.outlier_count}</td>
                        <td className="py-2"><span className="badge-yellow">{a["outlier_%"]}%</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button onClick={() => router.push("/dashboard/model")} className="btn-primary">Continue to ML Model →</button>
            <button onClick={handleRun} disabled={running} className="btn-secondary">Regenerate</button>
          </div>
        </div>
      )}
    </div>
  );
}
