"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { exportPDF, exportExcel, getStatus } from "@/lib/api";

export default function ExportPage() {
  const { user } = useAuth();
  const router   = useRouter();
  const [client, setClient]       = useState<any>(null);
  const [status, setStatus]       = useState<any>(null);
  const [exporting, setExporting] = useState<"pdf" | "excel" | null>(null);
  const [error, setError]         = useState("");
  const [mounted, setMounted]     = useState(false);

  useEffect(() => {
    setMounted(true);
    const s = localStorage.getItem("analytiq_client");
    if (s) { const c = JSON.parse(s); setClient(c); fetchStatus(c); }
  }, []);

  const fetchStatus = async (c: any) => {
    if (!user) return;
    try { const res = await getStatus(user.id, c.name); setStatus(res.data); } catch {}
  };

  const downloadBlob = (data: any, filename: string, mime: string) => {
    const blob = new Blob([data], { type: mime });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handlePDF = async () => {
    if (!client || !user) return;
    setExporting("pdf"); setError("");
    try {
      const res = await exportPDF(user.id, client.name, client.domain);
      downloadBlob(res.data, `Analytiq_${client.name}_Report.pdf`, "application/pdf");
    } catch (e: any) {
      const detail = e?.response?.data?.detail || e?.message || "Unknown error";
      setError(`PDF export failed: ${detail}`);
    } finally { setExporting(null); }
  };

  const handleExcel = async () => {
    if (!client || !user) return;
    setExporting("excel"); setError("");
    try {
      const res = await exportExcel(user.id, client.name, client.domain);
      downloadBlob(
        res.data,
        `Analytiq_${client.name}_Dashboard.xlsx`,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      );
    } catch (e: any) {
      const detail = e?.response?.data?.detail || e?.message || "Unknown error";
      setError(`Excel export failed: ${detail}`);
    } finally { setExporting(null); }
  };

  if (!mounted) return null;

  const checks = [
    { label: "Data cleaned",        done: status?.has_data },
    { label: "Insights generated",  done: status?.has_insights },
    { label: "ML model trained",    done: status?.has_model },
    { label: "Executive narrative", done: status?.has_narrative },
  ];

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">
          Export <span className="text-blue-600 italic">Report</span>
        </h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">
          Client-ready deliverables · {client?.name}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3 mb-5">
          {error}
        </div>
      )}

      {/* Checklist */}
      <div className="card mb-6">
        <div className="section-title">Analysis checklist</div>
        <div className="space-y-3">
          {checks.map(c => (
            <div key={c.label} className="flex items-center gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs flex-shrink-0
                ${c.done ? "bg-green-100 text-green-600" : "bg-gray-100 text-gray-400"}`}>
                {c.done ? "✓" : "○"}
              </div>
              <div className={`text-sm ${c.done ? "text-gray-900" : "text-gray-400"}`}>{c.label}</div>
              {c.done
                ? <span className="badge-green ml-auto">Complete</span>
                : <span className="badge-gray ml-auto">Pending</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Export buttons */}
      <div className="grid grid-cols-2 gap-5">
        {/* PDF */}
        <div className="card">
          <div className="text-sm font-medium text-gray-900 mb-2">PDF Report</div>
          <div className="text-xs text-gray-400 mb-5 leading-relaxed">
            Professional 8-page PDF with cover page, KPIs, segment analysis, ML model performance,
            at-risk records, AI recommendations, charts, and executive narrative.
          </div>
          <div className="flex items-center gap-2 mb-5">
            <div className="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center text-red-500 text-sm font-mono font-bold">
              PDF
            </div>
            <div className="text-xs text-gray-500">8 pages · Charts included · Executive summary</div>
          </div>
          <button
            onClick={handlePDF}
            disabled={exporting === "pdf" || !status?.has_insights}
            className="btn-primary w-full flex items-center justify-center gap-2">
            {exporting === "pdf" ? (
              <>
                <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
                Generating PDF...
              </>
            ) : "Download PDF Report"}
          </button>
        </div>

        {/* Excel */}
        <div className="card">
          <div className="text-sm font-medium text-gray-900 mb-2">Excel Dashboard</div>
          <div className="text-xs text-gray-400 mb-5 leading-relaxed">
            Professional Excel workbook with 6 formatted sheets — executive summary, KPI dashboard,
            color-coded at-risk records, segment analysis, model performance, and visual charts.
          </div>
          <div className="flex items-center gap-2 mb-5">
            <div className="w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center text-green-600 text-sm font-mono font-bold">
              XLS
            </div>
            <div className="text-xs text-gray-500">6 sheets · Color coded · Risk badges</div>
          </div>
          <button
            onClick={handleExcel}
            disabled={exporting === "excel" || !status?.has_insights}
            className="btn-primary w-full flex items-center justify-center gap-2">
            {exporting === "excel" ? (
              <>
                <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
                Generating Excel...
              </>
            ) : "Download Excel Dashboard"}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="mt-6 pt-6 border-t border-gray-200 flex gap-3">
        <button onClick={() => router.push("/dashboard/interactive")} className="btn-secondary text-xs">
          ← View Dashboard
        </button>
        <button onClick={() => router.push("/dashboard/simulator")} className="btn-secondary text-xs">
          ← What-If Simulator
        </button>
        <button onClick={() => router.push("/workspace")} className="btn-primary text-xs">
          Back to workspace →
        </button>
      </div>
    </div>
  );
}
