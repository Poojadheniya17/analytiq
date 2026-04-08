"use client";
// frontend/app/dashboard/ask-ai/page.tsx

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { askQuestion } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const EXAMPLES = [
  "What is the overall churn rate?",
  "Which contract type has the highest churn?",
  "Average monthly charges for churned vs retained customers?",
  "How many customers have tenure greater than 24 months?",
];

interface Result { question: string; sql: string; results: any[]; answer: string; timestamp: string; }

export default function AskAIPage() {
  const { user } = useAuth();
  const router   = useRouter();
  const [client, setClient]     = useState<any>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [history, setHistory]   = useState<Result[]>([]);
  const [activeIdx, setActiveIdx] = useState<number | null>(null);

  useEffect(() => {
    const s = localStorage.getItem("analytiq_client");
    if (s) {
      const c = JSON.parse(s);
      setClient(c);
      const saved = localStorage.getItem(`analytiq_history_${c.name}`);
      if (saved) setHistory(JSON.parse(saved));
    }
  }, []);

  const saveHistory = (newHistory: Result[], clientName: string) => {
    localStorage.setItem(`analytiq_history_${clientName}`, JSON.stringify(newHistory));
  };

  const handleAsk = async () => {
    if (!question.trim() || !client || !user) return;
    setLoading(true); setError("");
    try {
      const res = await askQuestion(user.id, client.name, question);
      const newResult: Result = {
        ...res.data,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      const newHistory = [newResult, ...history.slice(0, 9)];
      setHistory(newHistory);
      setActiveIdx(0);
      saveHistory(newHistory, client.name);
      setQuestion("");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Query failed. Try rephrasing.");
    } finally { setLoading(false); }
  };

  const clearHistory = () => {
    setHistory([]);
    setActiveIdx(null);
    if (client) localStorage.removeItem(`analytiq_history_${client.name}`);
  };

  const active = activeIdx !== null ? history[activeIdx] : null;

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Ask <span className="text-blue-600 italic">AI</span></h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">Plain English → SQL → Answer · {client?.name}</p>
      </div>

      <div className="flex gap-6">
        {/* Left — input + examples */}
        <div className="flex-1 min-w-0 space-y-5">
          {/* Input */}
          <div className="card">
            <label className="label">Your question</label>
            <div className="flex gap-3">
              <input className="input flex-1"
                placeholder="e.g. Which segment has the most at-risk customers?"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !loading && handleAsk()}
              />
              <button onClick={handleAsk} disabled={loading || !question.trim()} className="btn-primary px-6 flex-shrink-0">
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></span>
                    Thinking...
                  </span>
                ) : "Run query"}
              </button>
            </div>
            <div className="mt-3">
              <div className="text-xs text-gray-400 mb-2 font-mono">Examples</div>
              <div className="flex flex-wrap gap-2">
                {EXAMPLES.map(q => (
                  <button key={q} onClick={() => setQuestion(q)}
                    className="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 hover:border-blue-300 hover:bg-blue-50/30 transition-colors">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {error && <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3">{error}</div>}

          {/* Active result */}
          {active && (
            <div className="space-y-4">
              <div className="card">
                <div className="section-title">Generated SQL</div>
                <pre className="bg-gray-900 text-green-400 rounded-lg p-4 text-xs font-mono overflow-x-auto whitespace-pre-wrap">{active.sql}</pre>
              </div>

              {active.results?.length > 0 && (
                <div className="card">
                  <div className="section-title">Query results ({active.results.length} rows)</div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead><tr className="border-b border-gray-100">
                        {Object.keys(active.results[0]).map(k => (
                          <th key={k} className="text-left py-2 px-3 font-mono text-gray-400 font-normal">{k}</th>
                        ))}
                      </tr></thead>
                      <tbody>
                        {active.results.slice(0, 10).map((row, i) => (
                          <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                            {Object.values(row).map((val: any, j) => (
                              <td key={j} className="py-2 px-3 text-gray-600">{String(val)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-xl p-5">
                <div className="text-xs font-mono text-blue-600 uppercase tracking-wider mb-2">AI Answer</div>
                <div className="text-sm text-gray-800 leading-relaxed">{active.answer}</div>
              </div>

              <div className="flex gap-3">
                <button onClick={() => router.push("/dashboard/narrative")} className="btn-primary">Continue to Narrative →</button>
              </div>
            </div>
          )}

          {!active && !loading && history.length === 0 && (
            <div className="card text-center py-12 border-dashed">
              <div className="text-3xl text-gray-200 mb-3">◌</div>
              <div className="text-sm text-gray-400">Ask a question to get started</div>
            </div>
          )}
        </div>

        {/* Right — history */}
        <div className="w-72 flex-shrink-0">
          <div className="flex items-center justify-between mb-3">
            <div className="section-title mb-0">Query history</div>
            {history.length > 0 && (
              <button onClick={clearHistory} className="text-xs text-gray-400 hover:text-red-500 transition-colors">Clear all</button>
            )}
          </div>

          {history.length === 0 ? (
            <div className="card text-center py-8 border-dashed">
              <div className="text-xs text-gray-400">No queries yet</div>
            </div>
          ) : (
            <div className="space-y-2">
              {history.map((h, i) => (
                <button key={i} onClick={() => setActiveIdx(i)}
                  className={`w-full text-left card p-3 hover:border-blue-200 transition-colors cursor-pointer
                    ${activeIdx === i ? "border-blue-300 bg-blue-50/30" : ""}`}>
                  <div className="text-xs font-medium text-gray-800 mb-1 line-clamp-2">{h.question}</div>
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-gray-400 font-mono">{h.timestamp}</div>
                    <div className="text-xs text-blue-500">{h.results?.length || 0} rows</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
