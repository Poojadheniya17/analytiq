"use client";
// frontend/app/dashboard/page.tsx — Dashboard Overview

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { getClients, getStatus } from "@/lib/api";

interface Client { id: number; name: string; domain: string; created: string; }
interface ClientStatus { name: string; domain: string; has_data: boolean; has_insights: boolean; has_model: boolean; has_narrative: boolean; metrics?: any; }

export default function DashboardOverview() {
  const { user } = useAuth();
  const router   = useRouter();
  const [clients, setClients]           = useState<Client[]>([]);
  const [statuses, setStatuses]         = useState<ClientStatus[]>([]);
  const [loading, setLoading]           = useState(true);

  useEffect(() => {
    if (user) fetchAll();
  }, [user]);

  const fetchAll = async () => {
    try {
      const res = await getClients(user!.id);
      const cls: Client[] = res.data;
      setClients(cls);
      const statusResults = await Promise.all(
        cls.map(async (c) => {
          try {
            const s = await getStatus(user!.id, c.name);
            return { name: c.name, domain: c.domain, ...s.data };
          } catch {
            return { name: c.name, domain: c.domain, has_data: false, has_insights: false, has_model: false, has_narrative: false };
          }
        })
      );
      setStatuses(statusResults);
    } catch {}
    finally { setLoading(false); }
  };

  const openClient = (client: Client) => {
    localStorage.setItem("analytiq_client", JSON.stringify(client));
    router.push("/dashboard/upload");
  };

  const totalAnalysed  = statuses.filter(s => s.has_insights).length;
  const totalModels    = statuses.filter(s => s.has_model).length;
  const totalNarratives = statuses.filter(s => s.has_narrative).length;

  const steps = [
    { key: "has_data",      label: "Data loaded",    icon: "↗", color: "text-blue-600 bg-blue-50" },
    { key: "has_insights",  label: "Insights ready", icon: "◎", color: "text-green-600 bg-green-50" },
    { key: "has_model",     label: "Model trained",  icon: "⬡", color: "text-purple-600 bg-purple-50" },
    { key: "has_narrative", label: "Narrative done", icon: "◻", color: "text-orange-600 bg-orange-50" },
  ];

  if (loading) return (
    <div className="p-8 flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <div className="text-sm text-gray-400 font-mono">Loading dashboard...</div>
      </div>
    </div>
  );

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">
          Good morning, <span className="text-blue-600">{user?.username}</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1">Here's an overview of all your client workspaces</p>
      </div>

      {/* Top stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total Clients",    value: clients.length,    icon: "◈", color: "border-t-blue-500" },
          { label: "Analysed",         value: totalAnalysed,     icon: "◎", color: "border-t-green-500" },
          { label: "Models Trained",   value: totalModels,       icon: "⬡", color: "border-t-purple-500" },
          { label: "Reports Written",  value: totalNarratives,   icon: "◻", color: "border-t-orange-500" },
        ].map(s => (
          <div key={s.label} className={`card border-t-2 ${s.color}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="label mb-0">{s.label}</div>
              <div className="text-gray-300 font-mono text-lg">{s.icon}</div>
            </div>
            <div className="text-3xl font-semibold text-gray-900">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Client progress cards */}
      {statuses.length === 0 ? (
        <div className="card text-center py-16 border-dashed">
          <div className="text-3xl text-gray-200 mb-4">◈</div>
          <div className="text-sm font-medium text-gray-500 mb-2">No clients yet</div>
          <div className="text-xs text-gray-400 mb-6">Go to your workspace to create your first client</div>
          <button onClick={() => router.push("/workspace")} className="btn-primary">Go to Workspace</button>
        </div>
      ) : (
        <div>
          <div className="section-title">Client pipeline status</div>
          <div className="space-y-3">
            {statuses.map((s, i) => {
              const client = clients.find(c => c.name === s.name);
              const completed = steps.filter(step => (s as any)[step.key]).length;
              const pct = Math.round((completed / steps.length) * 100);

              return (
                <div key={s.name} className="card hover:border-blue-200 transition-colors">
                  <div className="flex items-center gap-4">
                    {/* Avatar */}
                    <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {s.name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2)}
                    </div>

                    {/* Name + domain */}
                    <div className="w-48 flex-shrink-0">
                      <div className="text-sm font-medium text-gray-900">{s.name}</div>
                      <div className="text-xs text-gray-400">{s.domain}</div>
                    </div>

                    {/* Progress steps */}
                    <div className="flex items-center gap-2 flex-1">
                      {steps.map((step) => {
                        const done = (s as any)[step.key];
                        return (
                          <div key={step.key} className="flex items-center gap-1.5">
                            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono transition-colors
                              ${done ? step.color : "text-gray-300 bg-gray-50"}`}>
                              <span>{step.icon}</span>
                              <span>{step.label}</span>
                            </div>
                            {step.key !== "has_narrative" && (
                              <div className={`w-4 h-px ${done ? "bg-gray-300" : "bg-gray-100"}`} />
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Progress bar */}
                    <div className="w-32 flex-shrink-0">
                      <div className="flex items-center justify-between mb-1">
                        <div className="text-xs text-gray-400 font-mono">{pct}% complete</div>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }} />
                      </div>
                    </div>

                    {/* Model metrics if available */}
                    {s.metrics && (
                      <div className="flex gap-3 flex-shrink-0">
                        <div className="text-center">
                          <div className="text-xs text-gray-400 font-mono">AUC</div>
                          <div className="text-sm font-semibold text-gray-900">{s.metrics.auc_roc}</div>
                        </div>
                        <div className="text-center">
                          <div className="text-xs text-gray-400 font-mono">F1</div>
                          <div className="text-sm font-semibold text-gray-900">{s.metrics.f1_score}</div>
                        </div>
                      </div>
                    )}

                    {/* Action button */}
                    <button onClick={() => client && openClient(client)}
                      className="btn-primary text-xs px-4 py-2 flex-shrink-0">
                      {completed === 0 ? "Start →" : completed === 4 ? "View →" : "Continue →"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="mt-8">
        <div className="section-title">Quick actions</div>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "New client workspace", desc: "Start analysing a new client", icon: "+", href: "/workspace" },
            { label: "View API docs",         desc: "Explore the REST API",          icon: "⌘", href: "http://localhost:8000/docs" },
            { label: "Back to workspace",     desc: "Manage all clients",            icon: "◈", href: "/workspace" },
          ].map(a => (
            <button key={a.label} onClick={() => a.href.startsWith("http") ? window.open(a.href) : router.push(a.href)}
              className="card text-left hover:border-blue-200 transition-colors cursor-pointer">
              <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center text-gray-500 font-mono mb-3">{a.icon}</div>
              <div className="text-sm font-medium text-gray-900 mb-1">{a.label}</div>
              <div className="text-xs text-gray-400">{a.desc}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
