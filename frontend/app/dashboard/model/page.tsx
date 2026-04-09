"use client";
// frontend/app/dashboard/model/page.tsx — Phase 1

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { trainModel, getStatus } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const TRAINING_STEPS = [
  "Loading cleaned dataset...",
  "Detecting problem type...",
  "Validating dataset quality...",
  "Preparing features...",
  "Training XGBoost...",
  "Training Random Forest...",
  "Training Linear model...",
  "Comparing model performance...",
  "Selecting best model...",
  "Generating SHAP explanations...",
  "Saving model to disk...",
  "Identifying at-risk records...",
];

const PROBLEM_TYPE_INFO: Record<string, { label: string; color: string; desc: string }> = {
  binary_classification:    { label: "Binary Classification", color: "bg-blue-100 text-blue-700", desc: "Predicting one of two outcomes — yes or no" },
  multiclass_classification:{ label: "Multi-class Classification",color: "bg-purple-100 text-purple-700",desc: "Predicting one of multiple categories" },
  regression:               { label: "Regression",               color: "bg-green-100 text-green-700", desc: "Predicting a continuous numeric value (e.g. revenue)" },
  clustering:               { label: "Clustering",               color: "bg-orange-100 text-orange-700",desc: "Grouping similar records together (unsupervised)" },
  time_series:              { label: "Time Series",              color: "bg-red-100 text-red-700",     desc: "Forecasting values over time" },
};

const METRIC_INFO: Record<string, string> = {
  auc_roc:   "Overall model quality — closer to 1.0 is better",
  precision: "Of predicted positives, how many were correct",
  recall:    "Of actual positives, how many did we find",
  f1_score:  "Balance between precision and recall",
  accuracy:  "Overall prediction accuracy",
  rmse:      "Root mean square error — lower is better",
  mae:       "Mean absolute error — lower is better",
  r2_score:  "How well the model explains variance — closer to 1.0 is better",
  f1_macro:  "F1 score averaged across all classes",
  silhouette_score: "Cluster quality — closer to 1.0 means well-separated clusters",
};

export default function ModelPage() {
  const { user } = useAuth();
  const router   = useRouter();
  const [client, setClient]       = useState<any>(null);
  const [status, setStatus]       = useState<any>(null);
  const [training, setTraining]   = useState(false);
  const [error, setError]         = useState("");
  const [step, setStep]           = useState(0);
  const [stepMsg, setStepMsg]     = useState("");
  const [targetCol, setTargetCol] = useState<string>("");
  const [manualTarget, setManualTarget] = useState(false);
  const [columns, setColumns]     = useState<string[]>([]);

  useEffect(() => {
    const s = localStorage.getItem("analytiq_client");
    if (s) { const c = JSON.parse(s); setClient(c); fetchStatus(c); }
  }, []);

  const fetchStatus = async (c: any) => {
    if (!user) return;
    try {
      const res = await getStatus(user.id, c.name);
      setStatus(res.data);
    } catch {}
  };

  const handleTrain = async () => {
    if (!client || !user) return;
    setTraining(true); setError(""); setStep(0); setStepMsg(TRAINING_STEPS[0]);

    const interval = setInterval(() => {
      setStep(prev => {
        const next = Math.min(prev + 1, TRAINING_STEPS.length - 1);
        setStepMsg(TRAINING_STEPS[next]);
        return next;
      });
    }, 2000);

    try {
      await trainModel(user.id, client.name);
      clearInterval(interval);
      fetchStatus(client);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Training failed. Check your data.");
    } finally { clearInterval(interval); setTraining(false); }
  };

  const getChartUrl = (chart: string) => {
    if (!user || !client) return "";
    const safe = client.name.toLowerCase().replace(/ /g, "_");
    return `${process.env.NEXT_PUBLIC_API_URL}/static/users/${user.id}/${safe}/charts/${chart}`;
  };

  const full    = status?.full_results;
  const metrics = full?.metrics || status?.metrics;
  const pt      = full?.problem_type || status?.metrics?.problem_type;
  const ptInfo  = pt ? PROBLEM_TYPE_INFO[pt] : null;

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">ML <span className="text-blue-600 italic">Model</span></h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">AutoML · {client?.name} · {client?.domain}</p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3 mb-5">{error}</div>}

      {!status?.has_data ? (
        <div className="card text-center py-12 border-dashed">
          <div className="text-sm text-gray-500 mb-3">No data found</div>
          <button onClick={() => router.push("/dashboard/upload")} className="btn-primary">Go to Upload</button>
        </div>

      ) : training ? (
        <div className="card py-16">
          <div className="max-w-sm mx-auto text-center">
            <div className="w-12 h-12 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-5"></div>
            <div className="text-sm font-medium text-gray-700 mb-1">Running AutoML</div>
            <div className="text-xs text-blue-600 font-mono mb-6 h-4">{stepMsg}</div>
            <div className="space-y-2 text-left">
              {TRAINING_STEPS.map((s, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300
                    ${i < step ? "bg-green-500" : i === step ? "bg-blue-500 animate-pulse" : "bg-gray-200"}`}>
                    {i < step && <span className="text-white text-xs">✓</span>}
                  </div>
                  <div className={`text-xs font-mono transition-colors duration-300
                    ${i < step ? "text-green-600" : i === step ? "text-blue-600 font-medium" : "text-gray-300"}`}>
                    {s}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      ) : !status?.has_model ? (
        <div className="space-y-5">
          {/* Problem type preview */}
          {full?.problem_type && ptInfo && (
            <div className="card border-blue-200 bg-blue-50/30">
              <div className="text-xs font-mono text-gray-400 mb-2">Detected problem type</div>
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${ptInfo.color}`}>{ptInfo.label}</span>
                <div className="text-sm text-gray-600">{ptInfo.desc}</div>
              </div>
              <div className="text-xs text-gray-400 mt-2 font-mono">{full?.problem_reason}</div>
            </div>
          )}

          <div className="card text-center py-12">
            <div className="text-3xl text-gray-200 mb-4">⬡</div>
            <div className="text-sm font-medium text-gray-600 mb-2">Ready to train</div>
            <div className="text-xs text-gray-400 mb-6 max-w-sm mx-auto">
              AutoML will run XGBoost, Random Forest, and a linear model — then automatically select the best one based on your data.
            </div>
            <button onClick={handleTrain} className="btn-primary">Run AutoML Training</button>
          </div>
        </div>

      ) : (
        <div className="space-y-6">

          {/* Problem type badge */}
          {ptInfo && (
            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl border border-gray-200">
              <span className={`text-xs px-3 py-1.5 rounded-full font-medium ${ptInfo.color}`}>{ptInfo.label}</span>
              <div>
                <div className="text-sm text-gray-700">{ptInfo.desc}</div>
                <div className="text-xs text-gray-400 font-mono mt-0.5">{full?.problem_reason}</div>
              </div>
              <div className="ml-auto text-right">
                <div className="text-xs text-gray-400 font-mono">Best model</div>
                <div className="text-sm font-semibold text-gray-900">{full?.best_model || status?.metrics?.best_model}</div>
              </div>
            </div>
          )}

          {/* AutoML comparison table */}
          {full?.automl_comparison && Object.keys(full.automl_comparison).length > 0 && (
            <div>
              <div className="section-title">AutoML model comparison</div>
              <div className="card">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-2 text-xs font-mono text-gray-400 font-normal">Model</th>
                      {Object.keys(Object.values(full.automl_comparison)[0] as any).map(k => (
                        <th key={k} className="text-left py-2 text-xs font-mono text-gray-400 font-normal">{k.replace(/_/g," ").toUpperCase()}</th>
                      ))}
                      <th className="text-left py-2 text-xs font-mono text-gray-400 font-normal">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(full.automl_comparison).map(([name, m]: any) => {
                      const isBest = name === full.best_model;
                      return (
                        <tr key={name} className={`border-b border-gray-50 ${isBest ? "bg-blue-50/50" : ""}`}>
                          <td className="py-2.5 font-medium text-gray-900 flex items-center gap-2">
                            {name}
                            {isBest && <span className="text-[10px] bg-blue-600 text-white px-2 py-0.5 rounded-full">Best</span>}
                          </td>
                          {Object.values(m as any).map((v: any, i: number) => (
                            <td key={i} className={`py-2.5 font-mono text-xs ${isBest ? "text-blue-700 font-semibold" : "text-gray-600"}`}>
                              {typeof v === "number" ? v.toFixed(4) : v}
                            </td>
                          ))}
                          <td className="py-2.5">
                            {isBest
                              ? <span className="badge-green">Selected</span>
                              : <span className="badge-gray">Not selected</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Metrics */}
          {metrics && (
            <div>
              <div className="section-title">Best model performance</div>
              <div className="grid grid-cols-4 gap-4">
                {Object.entries(metrics).map(([k, v]: any) => (
                  <div key={k} className="card border-t-2 border-blue-500">
                    <div className="label">{k.replace(/_/g," ").toUpperCase()}</div>
                    <div className="text-2xl font-semibold text-gray-900">{typeof v === "number" ? v.toFixed(4) : v}</div>
                    <div className="text-xs text-gray-400 mt-1 leading-tight">{METRIC_INFO[k] || ""}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SHAP explanation */}
          {full?.shap?.available && (
            <div>
              <div className="section-title">Why the model decides — SHAP explainability</div>
              <div className="card bg-blue-50/30 border-blue-200">
                <div className="text-sm text-gray-700 mb-4">{full.shap.explanation}</div>
                {full.shap.top_features && (
                  <div className="space-y-2">
                    {full.shap.top_features.map((f: any, i: number) => (
                      <div key={i} className="flex items-center gap-3">
                        <div className="text-xs font-mono text-gray-500 w-6 text-right">{i+1}</div>
                        <div className="text-sm font-medium text-gray-900 w-48">{f.feature}</div>
                        <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${(f.shap_importance / full.shap.top_features[0].shap_importance) * 100}%` }} />
                        </div>
                        <div className="text-xs font-mono text-gray-500 w-16 text-right">{f.shap_importance?.toFixed(4)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Charts */}
          {status?.charts?.length > 0 && (
            <div>
              <div className="section-title">Performance charts</div>
              <div className="grid grid-cols-2 gap-4">
                {status.charts.map((chart: string) => (
                  <div key={chart} className="card p-3">
                    <div className="text-xs font-mono text-gray-400 mb-2">{chart.replace(/_/g," ").replace(".png","")}</div>
                    <img src={getChartUrl(chart)} alt={chart} className="w-full rounded-lg"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* At-risk table */}
          {status?.at_risk?.length > 0 && (
            <div>
              <div className="section-title">Top at-risk records</div>
              <div className="card overflow-x-auto">
                <table className="w-full text-xs">
                  <thead><tr className="border-b border-gray-100">
                    {Object.keys(status.at_risk[0]).slice(0, 6).map((k: string) => (
                      <th key={k} className="text-left py-2 px-3 font-mono text-gray-400 font-normal">{k}</th>
                    ))}
                  </tr></thead>
                  <tbody>
                    {status.at_risk.map((row: any, i: number) => (
                      <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                        {Object.values(row).slice(0, 6).map((val: any, j: number) => (
                          <td key={j} className={`py-2 px-3 ${j === 5 ? "font-medium text-red-600" : "text-gray-600"}`}>
                            {String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={() => router.push("/dashboard/forecast")} className="btn-primary">Continue to Forecast →</button>
            <button onClick={handleTrain} disabled={training} className="btn-secondary">Retrain model</button>
          </div>
        </div>
      )}
    </div>
  );
}
