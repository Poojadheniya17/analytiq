"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/Sidebar";
import { getClients, createClient, deleteClient } from "@/lib/api";

const DOMAINS = ["Retail / E-commerce","Telecom","Healthcare","Finance / Fintech","Manufacturing","HR / People Analytics","Real Estate","Other"];
interface Client { id: number; name: string; domain: string; created: string; }
const COLORS = ["bg-blue-100 text-blue-700","bg-green-100 text-green-700","bg-orange-100 text-orange-700","bg-purple-100 text-purple-700","bg-pink-100 text-pink-700"];

export default function WorkspacePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [clients, setClients]     = useState<Client[]>([]);
  const [showForm, setShowForm]   = useState(false);
  const [newName, setNewName]     = useState("");
  const [newDomain, setNewDomain] = useState(DOMAINS[0]);
  const [creating, setCreating]   = useState(false);
  const [error, setError]         = useState("");

  useEffect(() => { if (!loading && !user) router.push("/"); }, [user, loading]);
  useEffect(() => { if (user) fetchClients(); }, [user]);

  // JWT auth returns user.id as number OR user.sub as string — handle both
  const getUserId = (): number => {
    if (!user) return 0;
    if (typeof (user as any).id === "number") return (user as any).id;
    if (typeof (user as any).sub === "string") return parseInt((user as any).sub, 10);
    return 0;
  };

  const fetchClients = async () => {
    const uid = getUserId();
    if (!uid) return;
    try {
      const res = await getClients(uid);
      setClients(res.data);
    } catch {}
  };

  const handleCreate = async () => {
    const uid = getUserId();
    if (!uid) { setError("Not logged in."); return; }
    if (!newName.trim()) { setError("Please enter a client name."); return; }
    setCreating(true); setError("");
    try {
      await createClient(uid, newName.trim(), newDomain);
      setNewName("");
      setNewDomain(DOMAINS[0]);
      setShowForm(false);
      fetchClients();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg || String(d)).join(", "));
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (clientId: number) => {
    const uid = getUserId();
    if (!confirm("Delete this client and all its data?")) return;
    try { await deleteClient(clientId, uid); fetchClients(); } catch {}
  };

  const openClient = (client: Client) => {
    localStorage.setItem("analytiq_client", JSON.stringify(client));
    router.push("/dashboard/upload");
  };

  const getInitials = (name: string) =>
    name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <div className="text-sm text-gray-400">Loading workspace...</div>
      </div>
    </div>
  );

  const username = (user as any)?.username || (user as any)?.sub || "there";

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            Good to see you, <span className="text-blue-600">{username}</span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">Manage your client workspaces</p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: "Total Clients",    value: clients.length },
            { label: "Active Analyses",  value: clients.length },
            { label: "Account",          value: username },
          ].map(s => (
            <div key={s.label} className="card">
              <div className="label">{s.label}</div>
              <div className="text-2xl font-semibold text-gray-900">{s.value}</div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between mb-4">
          <div className="section-title">Your clients</div>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary text-xs px-4 py-2">
            + New client
          </button>
        </div>

        {showForm && (
          <div className="card mb-5 border-blue-200 bg-blue-50/30">
            <div className="text-sm font-medium text-gray-900 mb-4">New client workspace</div>
            {error && (
              <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-3">
                {error}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="label">Client name</label>
                <input className="input" placeholder="e.g. Acme Corp"
                  value={newName} onChange={e => setNewName(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleCreate()} />
              </div>
              <div>
                <label className="label">Industry domain</label>
                <select className="input" value={newDomain} onChange={e => setNewDomain(e.target.value)}>
                  {DOMAINS.map(d => <option key={d}>{d}</option>)}
                </select>
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={handleCreate} disabled={creating} className="btn-primary">
                {creating ? "Creating..." : "Create workspace"}
              </button>
              <button onClick={() => { setShowForm(false); setError(""); }} className="btn-secondary">
                Cancel
              </button>
            </div>
          </div>
        )}

        {clients.length === 0 ? (
          <div className="card text-center py-16 border-dashed">
            <div className="text-3xl mb-3 text-gray-300">◈</div>
            <div className="text-sm font-medium text-gray-500 mb-1">No clients yet</div>
            <div className="text-xs text-gray-400">Create your first client workspace to get started</div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {clients.map((client, i) => (
              <div key={client.id} className="card hover:border-blue-300 transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg ${COLORS[i % COLORS.length]} flex items-center justify-center text-sm font-bold`}>
                      {getInitials(client.name)}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">{client.name}</div>
                      <div className="text-xs text-gray-400">{client.domain}</div>
                    </div>
                  </div>
                  <span className="badge-green">Active</span>
                </div>
                <div className="text-xs text-gray-400 mb-4 font-mono">
                  Created {client.created?.slice(0, 10)}
                </div>
                <div className="flex gap-2 pt-3 border-t border-gray-100">
                  <button onClick={() => openClient(client)} className="btn-primary flex-1 text-xs py-2">
                    Open workspace →
                  </button>
                  <button onClick={() => handleDelete(client.id)} className="btn-danger text-xs py-2 px-3">
                    Delete
                  </button>
                </div>
              </div>
            ))}
            <button onClick={() => setShowForm(true)}
              className="card border-dashed hover:border-blue-300 hover:bg-blue-50/20 transition-colors flex flex-col items-center justify-center gap-2 min-h-[160px] cursor-pointer">
              <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 text-lg">+</div>
              <div className="text-sm text-gray-400 font-medium">New client workspace</div>
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
