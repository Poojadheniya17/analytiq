"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { loginUser, signupUser } from "@/lib/api";

export default function LandingPage() {
  const [modal, setModal]         = useState<"login" | "signup" | null>(null);
  const [username, setUsername]   = useState("");
  const [email, setEmail]         = useState("");
  const [password, setPassword]   = useState("");
  const [confirm, setConfirm]     = useState("");
  const [error, setError]         = useState("");
  const [success, setSuccess]     = useState("");
  const [loading, setLoading]     = useState(false);
  const [mounted, setMounted]     = useState(false);
  const { login, user }           = useAuth();
  const router                    = useRouter();

  useEffect(() => {
    setMounted(true);
    if (user) router.push("/workspace");
  }, [user]);

  if (!mounted) return null;

  const openModal = (tab: "login" | "signup") => {
    setModal(tab);
    setError(""); setSuccess("");
    setUsername(""); setPassword("");
    setConfirm(""); setEmail("");
  };

  const closeModal = () => {
    setModal(null);
    setError(""); setSuccess("");
  };

  const handleLogin = async () => {
    if (!username || !password) { setError("Please fill in all fields."); return; }
    setLoading(true); setError("");
    try {
      const res = await loginUser(username, password);
      login(res.data.user);
      router.push("/workspace");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Incorrect username or password.");
    } finally { setLoading(false); }
  };

  const handleSignup = async () => {
    if (!username || !email || !password) { setError("Please fill in all fields."); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }
    if (password.length < 6) { setError("Password must be at least 6 characters."); return; }
    setLoading(true); setError("");
    try {
      await signupUser(username, email, password);
      setSuccess("Account created! Sign in to continue.");
      setModal("login");
      setPassword(""); setConfirm("");
    } catch (e: any) {
      setError(e.response?.data?.detail || "Could not create account.");
    } finally { setLoading(false); }
  };

  const features = [
    { n: "01", title: "AutoML pipeline",          desc: "Problem type auto-detected. Three algorithms compared. Best model selected and saved — no configuration needed." },
    { n: "02", title: "What-If Simulator",         desc: "Move any feature slider and watch the prediction update in real time. Powered by SHAP explainability." },
    { n: "03", title: "Natural language queries",  desc: "Type any question in plain English. AI converts it to SQL, runs it, and explains the result." },
    { n: "04", title: "Professional reports",      desc: "8-page PDF with cover, charts, ML metrics, and AI narrative. Plus a 6-sheet formatted Excel workbook." },
    { n: "05", title: "Interactive dashboard",     desc: "Click any chart segment to filter the entire dashboard. Live KPIs, segments, and scatter plots." },
    { n: "06", title: "Multi-client workspaces",   desc: "Each client has isolated data, models, and reports. Manage a full portfolio from one account." },
  ];

  const steps = [
    { n: "1", title: "Upload any CSV",          desc: "Drag and drop any dataset — churn, fraud, HR, sales, healthcare. The platform adapts to your data automatically." },
    { n: "2", title: "Auto-clean and validate", desc: "Data quality score, missing value handling, type inference — all automatic. Letter grade shows dataset health." },
    { n: "3", title: "Run AutoML",              desc: "Three algorithms compared, best model selected, SHAP explanations generated. Entire pipeline in one click." },
    { n: "4", title: "Explore interactively",   desc: "Filter dashboards, run What-If scenarios, query in plain English. Everything connected and live." },
    { n: "5", title: "Export and deliver",      desc: "Download a professional PDF or Excel dashboard. Client-ready in one click." },
  ];

  return (
    <div className="min-h-screen bg-white">

      {/* ── Navbar ─────────────────────────────────────────── */}
      <nav className="sticky top-0 z-40 bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg width="13" height="13" viewBox="0 0 40 40" fill="none">
                <rect x="4" y="24" width="8" height="12" rx="2" fill="white"/>
                <rect x="16" y="16" width="8" height="20" rx="2" fill="white"/>
                <rect x="28" y="6"  width="8" height="30" rx="2" fill="white"/>
              </svg>
            </div>
            <span className="text-gray-900 font-bold text-[15px] tracking-tight">Analytiq</span>
          </div>

          <div className="hidden md:flex items-center gap-1">
            {["Features", "How it works", "Pricing"].map(l => (
              <button key={l}
                className="text-sm text-gray-500 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors">
                {l}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <button onClick={() => openModal("login")}
              className="text-sm text-gray-600 px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors font-medium">
              Sign in
            </button>
            <button onClick={() => openModal("signup")}
              className="text-sm text-white bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-semibold">
              Get started
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────── */}
      <section className="relative overflow-hidden" style={{ background: "linear-gradient(160deg, #080f1e 0%, #0f1f3d 100%)" }}>
        <div className="absolute inset-0 opacity-[0.035]"
          style={{ backgroundImage: "linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] opacity-[0.15]"
          style={{ background: "radial-gradient(ellipse, #2563eb 0%, transparent 65%)" }} />

        <div className="relative max-w-4xl mx-auto px-6 py-28 text-center">
          <div className="inline-flex items-center gap-2 border border-blue-500/20 bg-blue-600/10 rounded-full px-4 py-1.5 mb-8">
            <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
            <span className="text-[11px] text-blue-300 font-mono tracking-widest uppercase">Built for data analysts</span>
          </div>

          <h1 className="text-5xl md:text-6xl font-bold text-white leading-[1.1] tracking-tight mb-6">
            Raw data.<br />
            <span className="text-blue-400">Client-ready insights.</span>
          </h1>

          <p className="text-lg text-slate-400 leading-relaxed mb-10 max-w-xl mx-auto">
            Upload any CSV, run AutoML, query your data in plain English, and export professional reports — all without writing a single line of code.
          </p>

          <div className="flex items-center justify-center gap-3 mb-14 flex-wrap">
            <button onClick={() => openModal("signup")}
              className="text-sm font-semibold text-white bg-blue-600 px-7 py-3 rounded-lg hover:bg-blue-700 transition-colors">
              Start for free
            </button>
            <button onClick={() => openModal("login")}
              className="text-sm text-slate-400 border border-white/10 px-7 py-3 rounded-lg hover:border-white/20 hover:text-slate-300 transition-colors">
              Sign in to workspace →
            </button>
          </div>

          <div className="inline-flex border border-white/[0.08] rounded-xl overflow-hidden">
            {[
              { v: "Any CSV",       l: "Dataset" },
              { v: "AutoML",        l: "Model selection" },
              { v: "SHAP",          l: "Explainability" },
              { v: "PDF + Excel",   l: "Export" },
            ].map((s, i) => (
              <div key={s.l}
                className={`px-7 py-4 text-center ${i < 3 ? "border-r border-white/[0.08]" : ""}`}>
                <div className="text-white font-semibold text-sm">{s.v}</div>
                <div className="text-slate-600 text-[11px] mt-0.5">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ───────────────────────────────────────── */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <div className="text-[11px] font-mono text-gray-400 tracking-widest uppercase mb-3">Features</div>
            <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Built for serious analysts</h2>
            <p className="text-gray-500 mt-3 max-w-lg mx-auto text-sm leading-relaxed">
              Everything from data ingestion to client delivery — in one platform.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-gray-100 rounded-2xl overflow-hidden border border-gray-100">
            {features.map(f => (
              <div key={f.n} className="bg-white p-7 hover:bg-gray-50 transition-colors">
                <div className="text-[11px] font-bold text-blue-600 tracking-widest mb-4 font-mono">{f.n}</div>
                <div className="text-[15px] font-semibold text-gray-900 mb-2 tracking-tight">{f.title}</div>
                <div className="text-[13px] text-gray-500 leading-relaxed">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────── */}
      <section className="py-20 px-6 bg-gray-50 border-t border-gray-100">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <div className="text-[11px] font-mono text-gray-400 tracking-widest uppercase mb-3">How it works</div>
            <h2 className="text-3xl font-bold text-gray-900 tracking-tight">From upload to report in 5 steps</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <div className="space-y-0">
              {steps.map((s, i) => (
                <div key={s.n} className="flex gap-5 pb-8 relative">
                  {i < steps.length - 1 && (
                    <div className="absolute left-[19px] top-10 bottom-0 w-px bg-gray-200" />
                  )}
                  <div className="w-10 h-10 bg-gray-900 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 relative z-10">
                    {s.n}
                  </div>
                  <div className="pt-2">
                    <div className="text-sm font-semibold text-gray-900 mb-1">{s.title}</div>
                    <div className="text-sm text-gray-500 leading-relaxed">{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Product preview */}
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
              <div className="bg-white px-4 py-3 border-b border-gray-100 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                </div>
                <span className="text-xs text-gray-400 font-mono ml-2">Customer Churn · Analytiq</span>
              </div>
              <div className="p-5">
                <div className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-3">Key performance indicators</div>
                <div className="grid grid-cols-3 gap-2 mb-4">
                  {[
                    { l: "Total records", v: "7,043", c: "text-gray-900" },
                    { l: "Churn rate",    v: "26.5%", c: "text-red-600" },
                    { l: "Model AUC",     v: "0.973", c: "text-blue-600" },
                  ].map(k => (
                    <div key={k.l} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                      <div className="text-[9px] text-gray-400 uppercase tracking-wide mb-1">{k.l}</div>
                      <div className={`text-lg font-bold ${k.c}`}>{k.v}</div>
                    </div>
                  ))}
                </div>
                <div className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mb-2">Churn by contract type</div>
                <div className="space-y-2 mb-4">
                  {[
                    { l: "Month-to-month", v: 88, pct: "42.7%", c: "bg-red-500" },
                    { l: "One year",       v: 23, pct: "11.3%", c: "bg-orange-400" },
                    { l: "Two year",       v: 6,  pct: "2.8%",  c: "bg-green-500" },
                  ].map(b => (
                    <div key={b.l} className="flex items-center gap-2">
                      <span className="text-[10px] text-gray-500 w-28 flex-shrink-0">{b.l}</span>
                      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div className={`h-full ${b.c} rounded-full`} style={{ width: `${b.v}%` }} />
                      </div>
                      <span className="text-[10px] font-semibold text-gray-600 w-8 text-right">{b.pct}</span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 flex-wrap">
                  <span className="text-[9px] bg-blue-50 text-blue-700 px-2 py-1 rounded font-semibold">XGBoost selected</span>
                  <span className="text-[9px] bg-green-50 text-green-700 px-2 py-1 rounded font-semibold">AUC 0.973</span>
                  <span className="text-[9px] bg-purple-50 text-purple-700 px-2 py-1 rounded font-semibold">SHAP active</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────── */}
      <section className="py-16 px-6" style={{ background: "#080f1e" }}>
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white tracking-tight mb-3">Ready to start?</h2>
          <p className="text-slate-500 mb-8 text-sm">Free to use. No credit card required.</p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <button onClick={() => openModal("signup")}
              className="text-sm font-semibold text-white bg-blue-600 px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors">
              Create free account
            </button>
            <button onClick={() => openModal("login")}
              className="text-sm text-slate-500 border border-white/10 px-8 py-3 rounded-lg hover:border-white/20 transition-colors">
              Sign in
            </button>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 py-6 px-6 bg-white">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-600 rounded-md flex items-center justify-center">
              <svg width="11" height="11" viewBox="0 0 40 40" fill="none">
                <rect x="4"  y="24" width="8" height="12" rx="2" fill="white"/>
                <rect x="16" y="16" width="8" height="20" rx="2" fill="white"/>
                <rect x="28" y="6"  width="8" height="30" rx="2" fill="white"/>
              </svg>
            </div>
            <span className="text-gray-600 text-sm font-semibold">Analytiq</span>
          </div>
          <div className="text-xs text-gray-400">AI-powered analytics platform · Built with FastAPI + Next.js</div>
        </div>
      </footer>

      {/* ── Auth Modal ─────────────────────────────────────── */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(8,15,30,0.7)", backdropFilter: "blur(4px)" }}
          onClick={e => e.target === e.currentTarget && closeModal()}>

          <div className="bg-white rounded-2xl w-full max-w-[420px] p-8 relative shadow-2xl">
            <button onClick={closeModal}
              className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors text-lg leading-none">
              ×
            </button>

            <div className="flex items-center gap-2 mb-6">
              <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg width="13" height="13" viewBox="0 0 40 40" fill="none">
                  <rect x="4"  y="24" width="8" height="12" rx="2" fill="white"/>
                  <rect x="16" y="16" width="8" height="20" rx="2" fill="white"/>
                  <rect x="28" y="6"  width="8" height="30" rx="2" fill="white"/>
                </svg>
              </div>
              <span className="text-gray-900 font-bold text-[15px]">Analytiq</span>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-1 tracking-tight">
              {modal === "login" ? "Welcome back" : "Create your account"}
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              {modal === "login" ? "Sign in to your analytics workspace." : "Start analysing your clients data today."}
            </p>

            <div className="flex bg-gray-100 rounded-xl p-1 mb-6">
              {(["login", "signup"] as const).map(t => (
                <button key={t} onClick={() => { setModal(t); setError(""); setSuccess(""); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    modal === t ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
                  {t === "login" ? "Sign in" : "Create account"}
                </button>
              ))}
            </div>

            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 text-xs rounded-xl px-4 py-3 mb-5">
                {success}
              </div>
            )}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl px-4 py-3 mb-5">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1.5 block">Username</label>
                <input className="input" placeholder="Enter your username"
                  value={username} onChange={e => setUsername(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && (modal === "login" ? handleLogin() : handleSignup())} />
              </div>
              {modal === "signup" && (
                <div>
                  <label className="text-xs font-semibold text-gray-700 mb-1.5 block">Email address</label>
                  <input className="input" type="email" placeholder="you@example.com"
                    value={email} onChange={e => setEmail(e.target.value)} />
                </div>
              )}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-gray-700">Password</label>
                  {modal === "login" && (
                    <span className="text-xs text-blue-600 cursor-pointer hover:underline">Forgot password?</span>
                  )}
                </div>
                <input className="input" type="password" placeholder="••••••••"
                  value={password} onChange={e => setPassword(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && modal === "login" && handleLogin()} />
              </div>
              {modal === "signup" && (
                <div>
                  <label className="text-xs font-semibold text-gray-700 mb-1.5 block">Confirm password</label>
                  <input className="input" type="password" placeholder="••••••••"
                    value={confirm} onChange={e => setConfirm(e.target.value)} />
                </div>
              )}
            </div>

            {modal === "login" && (
              <div className="flex items-center gap-2 mt-4">
                <input type="checkbox" id="stay" defaultChecked
                  className="w-3.5 h-3.5 accent-blue-600 cursor-pointer rounded" />
                <label htmlFor="stay" className="text-xs text-gray-500 cursor-pointer select-none">
                  Keep me signed in
                </label>
              </div>
            )}

            <button
              onClick={modal === "login" ? handleLogin : handleSignup}
              disabled={loading}
              className="btn-primary w-full mt-5 h-11 flex items-center justify-center gap-2 text-sm rounded-xl font-semibold">
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Please wait...
                </>
              ) : modal === "login" ? "Sign in to workspace" : "Create account"}
            </button>

            <div className="text-center mt-5 text-xs text-gray-500">
              {modal === "login" ? "New to Analytiq? " : "Already have an account? "}
              <span className="text-blue-600 font-semibold cursor-pointer hover:underline"
                onClick={() => { setModal(modal === "login" ? "signup" : "login"); setError(""); setSuccess(""); }}>
                {modal === "login" ? "Create an account" : "Sign in"}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
