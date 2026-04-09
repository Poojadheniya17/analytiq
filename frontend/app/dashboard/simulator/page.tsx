"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function safe(val: any): string {
  if (val === null || val === undefined || typeof val === "object") return "";
  return String(val);
}

export default function SimulatorPage() {
  const { user } = useAuth();
  const router   = useRouter();

  const [client, setClient]         = useState<any>(null);
  const [config, setConfig]         = useState<any>(null);
  const [values, setValues]         = useState<Record<string, any>>({});
  const [result, setResult]         = useState<any>(null);
  const [loading, setLoading]       = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [error, setError]           = useState("");
  const [mounted, setMounted]       = useState(false);
  const [showAll, setShowAll]       = useState(false);

  useEffect(() => {
    setMounted(true);
    const s = localStorage.getItem("analytiq_client");
    if (s) {
      const c = JSON.parse(s);
      setClient(c);
      loadConfig(c);
    } else {
      setLoading(false);
    }
  }, []);

  async function loadConfig(c: any) {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      const res = await axios.post(`${API}/api/simulator/config`, {
        user_id: user.id, client_name: c.name
      });
      setConfig(res.data);
      // Pre-populate with sample at-risk record
      const defaults: Record<string, any> = {};
      for (const feat of res.data.features) {
        if (res.data.sample_record[feat.name] !== undefined) {
          defaults[feat.name] = res.data.sample_record[feat.name];
        } else {
          defaults[feat.name] = feat.default;
        }
      }
      setValues(defaults);
      // Auto-predict with sample record
      predictWithValues(defaults, c);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not load simulator. Train a model first.");
    } finally {
      setLoading(false);
    }
  }

  async function predictWithValues(vals: Record<string, any>, c?: any) {
    const cl = c || client;
    if (!cl || !user) return;
    setPredicting(true);
    try {
      const res = await axios.post(`${API}/api/simulator/predict`, {
        user_id:     user.id,
        client_name: cl.name,
        features:    vals,
      });
      setResult(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Prediction failed.");
    } finally {
      setPredicting(false);
    }
  }

  function handleChange(name: string, value: any) {
    const newValues = { ...values, [name]: value };
    setValues(newValues);
    predictWithValues(newValues);
  }

  function resetToSample() {
    if (!config) return;
    const defaults: Record<string, any> = {};
    for (const feat of config.features) {
      if (config.sample_record[feat.name] !== undefined) {
        defaults[feat.name] = config.sample_record[feat.name];
      } else {
        defaults[feat.name] = feat.default;
      }
    }
    setValues(defaults);
    predictWithValues(defaults);
  }

  function resetToMeans() {
    if (!config) return;
    const defaults: Record<string, any> = {};
    for (const feat of config.features) {
      defaults[feat.name] = feat.default;
    }
    setValues(defaults);
    predictWithValues(defaults);
  }

  if (!mounted) return null;

  if (loading) return (
    <div className="p-8 flex items-center justify-center min-h-96">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <div className="text-sm text-gray-400 font-mono">Loading simulator...</div>
      </div>
    </div>
  );

  if (error) return (
    <div className="p-8">
      <div className="card text-center py-16 border-dashed">
        <div className="text-3xl text-gray-200 mb-4">◌</div>
        <div className="text-sm font-medium text-gray-600 mb-2">{error}</div>
        <div className="space-y-2">
          <button onClick={() => router.push("/dashboard/narrative")} className="btn-primary w-full">
            Generate Narrative →
          </button>
          <button onClick={() => router.push("/dashboard/export")} className="btn-secondary w-full">
            Go to Export →
          </button>
        </div>
      </div>
    </div>
  );

  if (!config) return null;

  const topFeatures     = config.features.filter((f: any) => f.is_top);
  const otherFeatures   = config.features.filter((f: any) => !f.is_top);
  const visibleFeatures = showAll ? config.features : (topFeatures.length > 0 ? topFeatures : config.features.slice(0, 6));

  const riskPct   = result?.risk_probability ?? 0;
  const riskColor = result?.risk_color === "red" ? "#EF4444" : result?.risk_color === "orange" ? "#F97316" : "#10B981";
  const riskBg    = result?.risk_color === "red" ? "bg-red-50 border-red-200" : result?.risk_color === "orange" ? "bg-orange-50 border-orange-200" : "bg-green-50 border-green-200";
  const riskText  = result?.risk_color === "red" ? "text-red-700" : result?.risk_color === "orange" ? "text-orange-700" : "text-green-700";

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">
          What-If <span className="text-blue-600 italic">Simulator</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">
          Adjust any feature and see how the prediction changes in real time · {safe(client?.name)}
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6">

        {/* Left — Feature controls */}
        <div className="col-span-2 space-y-4">

          {/* Top bar */}
          <div className="flex items-center justify-between">
            <div className="text-xs font-mono text-gray-400 uppercase tracking-wider">
              {topFeatures.length > 0 ? "Top features by SHAP importance" : "Feature controls"}
            </div>
            <div className="flex gap-2">
              <button onClick={resetToSample}
                className="text-xs text-blue-600 border border-blue-200 px-3 py-1.5 rounded-lg hover:bg-blue-50 transition-colors">
                Load at-risk sample
              </button>
              <button onClick={resetToMeans}
                className="text-xs text-gray-500 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
                Reset to averages
              </button>
            </div>
          </div>

          {/* Feature inputs */}
          <div className="card space-y-5">
            {visibleFeatures.map((feat: any) => (
              <div key={feat.name}>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-900">
                    {safe(feat.label)}
                    {feat.is_top && (
                      <span className="ml-2 text-xs bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-mono">
                        Top driver
                      </span>
                    )}
                  </label>
                  <span className="text-xs font-mono text-gray-500">
                    {feat.type === "numeric"
                      ? Number(values[feat.name] ?? feat.default).toFixed(feat.max > 100 ? 0 : 2)
                      : safe(values[feat.name] ?? feat.default)}
                  </span>
                </div>

                {feat.type === "categorical" ? (
                  <div className="flex flex-wrap gap-2">
                    {feat.options.map((opt: string) => (
                      <button key={opt}
                        onClick={() => handleChange(feat.name, opt)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors
                          ${safe(values[feat.name]) === opt
                            ? "bg-blue-600 text-white border-blue-600"
                            : "bg-white text-gray-600 border-gray-200 hover:border-blue-300 hover:bg-blue-50"}`}>
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-1">
                    <input
                      type="range"
                      min={feat.min}
                      max={feat.max}
                      step={(feat.max - feat.min) / 100}
                      value={Number(values[feat.name] ?? feat.default)}
                      onChange={e => handleChange(feat.name, parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-blue-600"
                    />
                    <div className="flex justify-between text-xs text-gray-400 font-mono">
                      <span>{feat.max > 100 ? Math.round(feat.min) : feat.min}</span>
                      <span className="text-blue-600 font-medium">
                        {feat.max > 100 ? Math.round(values[feat.name] ?? feat.default) : Number(values[feat.name] ?? feat.default).toFixed(1)}
                      </span>
                      <span>{feat.max > 100 ? Math.round(feat.max) : feat.max}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {otherFeatures.length > 0 && !showAll && (
              <button onClick={() => setShowAll(true)}
                className="w-full text-xs text-gray-400 hover:text-blue-600 py-2 border border-dashed border-gray-200 rounded-lg transition-colors">
                + Show {otherFeatures.length} more features
              </button>
            )}
            {showAll && otherFeatures.length > 0 && (
              <button onClick={() => setShowAll(false)}
                className="w-full text-xs text-gray-400 hover:text-blue-600 py-2 border border-dashed border-gray-200 rounded-lg transition-colors">
                − Show fewer features
              </button>
            )}
          </div>
        </div>

        {/* Right — Prediction result */}
        <div className="space-y-4">

          {/* Risk meter */}
          <div className="card text-center">
            <div className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-4">
              {safe(config.target_col).replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())} Probability
            </div>

            {/* Circular gauge */}
            <div className="relative w-36 h-36 mx-auto mb-4">
              <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#F3F4F6" strokeWidth="12" />
                <circle cx="60" cy="60" r="50" fill="none"
                  stroke={riskColor} strokeWidth="12"
                  strokeDasharray={`${(riskPct / 100) * 314} 314`}
                  strokeLinecap="round"
                  style={{ transition: "stroke-dasharray 0.5s ease" }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-3xl font-bold text-gray-900" style={{ color: riskColor }}>
                  {predicting ? "..." : `${riskPct.toFixed(1)}%`}
                </div>
                <div className="text-xs text-gray-400 font-mono mt-1">probability</div>
              </div>
            </div>

            {result && (
              <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border ${riskBg} ${riskText}`}>
                <div className="w-2 h-2 rounded-full" style={{ background: riskColor }} />
                {safe(result.risk_label)}
              </div>
            )}
          </div>

          {/* Risk bar */}
          <div className="card">
            <div className="text-xs font-mono text-gray-400 mb-3">Risk scale</div>
            <div className="h-3 rounded-full overflow-hidden bg-gray-100 mb-2">
              <div className="h-full rounded-full transition-all duration-500"
                style={{ width: `${riskPct}%`, background: riskColor }} />
            </div>
            <div className="flex justify-between text-xs text-gray-400 font-mono">
              <span>0% Low</span>
              <span>50%</span>
              <span>100% High</span>
            </div>
          </div>

          {/* Recommendation */}
          {result?.recommendation && (
            <div className={`card border ${riskBg}`}>
              <div className={`text-xs font-mono uppercase tracking-wider mb-2 ${riskText}`}>
                Recommendation
              </div>
              <div className="text-sm text-gray-700 leading-relaxed">
                {safe(result.recommendation)}
              </div>
            </div>
          )}

          {/* How to use tip */}
          <div className="card bg-gray-50 border-gray-200">
            <div className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-2">How to use</div>
            <div className="text-xs text-gray-500 leading-relaxed space-y-1.5">
              <div>→ Adjust sliders or click buttons on the left</div>
              <div>→ Prediction updates instantly in real time</div>
              <div>→ Use "Load at-risk sample" to start with a high-risk customer</div>
              <div>→ Find the combination that reduces risk below 20%</div>
            </div>
          </div>

          <button onClick={() => router.push("/dashboard/export")} className="btn-primary w-full">
            Export Report →
          </button>
        </div>
      </div>
    </div>
  );
}
