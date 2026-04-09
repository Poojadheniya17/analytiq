"use client";
// frontend/app/dashboard/recommendations/page.tsx

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import axios from "axios";

interface Recommendation {
  title:  string;
  action: string;
  impact: string;
  metric: string;
}

export default function RecommendationsPage() {
  const { user } = useAuth();
  const router   = useRouter();
  const [client, setClient]         = useState<any>(null);
  const [recs, setRecs]             = useState<Recommendation[] | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError]           = useState("");

  useEffect(() => {
    const s = localStorage.getItem("analytiq_client");
    if (s) { const c = JSON.parse(s); setClient(c); fetchExisting(c); }
  }, []);

  const fetchExisting = async (c: any) => {
    if (!user) return;
    try {
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/ai/recommendations/${user.id}/${c.name}`);
      if (res.data.recommendations) setRecs(res.data.recommendations);

    } catch {}
  };

  const handleGenerate = async () => {
    if (!client || !user) return;
    setGenerating(true); setError("");
    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/ai/recommendations`, {
        user_id: user.id, client_name: client.name, domain: client.domain
      });
      setRecs(res.data.recommendations);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed. Run insights first.");
    } finally { setGenerating(false); }
  };

  const colors = [
    { border: "border-l-blue-500",   bg: "bg-blue-50",   icon: "bg-blue-100 text-blue-700",   num: "text-blue-600" },
    { border: "border-l-green-500",  bg: "bg-green-50",  icon: "bg-green-100 text-green-700",  num: "text-green-600" },
    { border: "border-l-orange-500", bg: "bg-orange-50", icon: "bg-orange-100 text-orange-700",num: "text-orange-600" },
  ];

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Smart <span className="text-blue-600 italic">Recommendations</span></h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">AI-generated action items · {client?.name} · {client?.domain}</p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3 mb-5">{error}</div>}

      {!recs ? (
        <div className="card text-center py-16">
          <div className="text-3xl text-gray-200 mb-4">◎</div>
          <div className="text-sm font-medium text-gray-600 mb-2">No recommendations yet</div>
          <div className="text-xs text-gray-400 mb-8 max-w-md mx-auto">
            The AI will analyse your insights and generate 3 specific, data-driven recommendations — each with a concrete action and expected business impact.
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-6 text-xs font-mono text-blue-700 max-w-sm mx-auto">
            Requires insights to be generated first
          </div>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary">
            {generating ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></span>
                Generating recommendations...
              </span>
            ) : "Generate Recommendations"}
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-xs font-mono text-blue-700">
            3 data-driven recommendations generated for {client?.name}
          </div>

          {recs.map((rec, i) => (
            <div key={i} className={`card border-l-4 ${colors[i].border}`}>
              <div className="flex items-start gap-4">
                <div className={`w-8 h-8 rounded-lg ${colors[i].icon} flex items-center justify-center text-sm font-bold flex-shrink-0`}>
                  {i + 1}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-gray-900 mb-3">{rec.title}</div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className={`rounded-lg p-3 ${colors[i].bg}`}>
                      <div className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-1">Action</div>
                      <div className="text-xs text-gray-700 leading-relaxed">{rec.action}</div>
                    </div>
                    <div className="rounded-lg p-3 bg-gray-50">
                      <div className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-1">Expected Impact</div>
                      <div className="text-xs text-gray-700 leading-relaxed">{rec.impact}</div>
                    </div>
                    <div className="rounded-lg p-3 bg-gray-50">
                      <div className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-1">Supporting Data</div>
                      <div className={`text-xs font-medium leading-relaxed ${colors[i].num}`}>{rec.metric}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}

          <div className="flex gap-3 pt-2">
             <button onClick={() => router.push("/dashboard/ask-ai")} className="btn-primary">
              Continue to Ask AI →
            </button>
            <button onClick={() => { setRecs(null); handleGenerate(); }} disabled={generating} className="btn-secondary">
              {generating ? "Regenerating..." : "Regenerate"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
 

