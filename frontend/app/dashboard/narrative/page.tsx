"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { generateNarrative, getNarrative } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function NarrativePage() {
  const { user } = useAuth();
  const router = useRouter();
  const [client, setClient]         = useState<any>(null);
  const [narrative, setNarrative]   = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError]           = useState("");

  useEffect(() => {
    const s = localStorage.getItem("analytiq_client");
    if (s) { const c = JSON.parse(s); setClient(c); fetchNarrative(c); }
  }, []);

  const fetchNarrative = async (c: any) => {
    if (!user) return;
    try { const res = await getNarrative(user.id, c.name); if (res.data.narrative) setNarrative(res.data.narrative); } catch {}
  };

  const handleGenerate = async () => {
    if (!client || !user) return;
    setGenerating(true); setError("");
    try { const res = await generateNarrative(user.id, client.name, client.domain); setNarrative(res.data.narrative); }
    catch (e: any) { setError(e.response?.data?.detail || "Failed. Run insights first."); }
    finally { setGenerating(false); }
  };

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Executive <span className="text-blue-600 italic">Narrative</span></h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">AI-written consultant report · {client?.name}</p>
      </div>
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3 mb-5">{error}</div>}
      {!narrative ? (
        <div className="card text-center py-16">
          <div className="text-3xl text-gray-200 mb-4">◻</div>
          <div className="text-sm font-medium text-gray-600 mb-2">No narrative yet</div>
          <div className="text-xs text-gray-400 mb-8 max-w-sm mx-auto">The AI will write a 4-5 paragraph executive summary in the style of a senior consultant with specific numbers, segment insights, and actionable recommendations.</div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-6 text-xs font-mono text-blue-700 max-w-sm mx-auto">Make sure you have run Insights first.</div>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary">{generating ? "Writing report..." : "Generate Executive Narrative"}</button>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="card">
            <div className="border-b border-gray-100 pb-4 mb-6">
              <div className="text-xs font-mono text-gray-400 uppercase tracking-wider">Executive Summary</div>
              <div className="text-sm font-medium text-gray-900 mt-1">{client?.name} · {client?.domain}</div>
            </div>
            {narrative.split("\n\n").map((para, i) => (<p key={i} className="text-sm text-gray-700 leading-relaxed mb-4">{para}</p>))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => router.push("/dashboard/interactive")} className="btn-primary">Continue to Dashboard →</button>
            <button onClick={() => { setNarrative(null); handleGenerate(); }} disabled={generating} className="btn-secondary">{generating ? "Regenerating..." : "Regenerate"}</button>
          </div>
        </div>
      )}
    </div>
  );
}
