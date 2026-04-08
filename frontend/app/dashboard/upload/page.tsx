"use client";
// frontend/app/dashboard/upload/page.tsx

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { uploadFile, cleanData } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import axios from "axios";

export default function UploadPage() {
  const { user } = useAuth();
  const router   = useRef<any>(useRouter());
  const fileRef  = useRef<HTMLInputElement>(null);
  const [client, setClient]       = useState<any>(null);
  const [preview, setPreview]     = useState<any>(null);
  const [cleaned, setCleaned]     = useState<any>(null);
  const [quality, setQuality]     = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [cleaning, setCleaning]   = useState(false);
  const [loadingQuality, setLoadingQuality] = useState(false);
  const [error, setError]         = useState("");
  const [dragOver, setDragOver]   = useState(false);

  useEffect(() => {
    const s = localStorage.getItem("analytiq_client");
    if (s) setClient(JSON.parse(s));
  }, []);

  const fetchQuality = async (clientName: string) => {
    if (!user) return;
    setLoadingQuality(true);
    try {
      const res = await axios.get(`http://localhost:8000/api/clients/${user.id}/${clientName}/quality`);
      setQuality(res.data);
    } catch {}
    finally { setLoadingQuality(false); }
  };

  const handleFile = async (file: File) => {
    if (!file || !client || !user) return;
    setUploading(true); setError(""); setPreview(null); setQuality(null);
    try {
      const res = await uploadFile(user.id, client.name, file);
      setPreview(res.data);
      fetchQuality(client.name);
    } catch { setError("Upload failed. Please try again."); }
    finally { setUploading(false); }
  };

  const handleClean = async () => {
    if (!client || !user) return;
    setCleaning(true); setError("");
    try {
      const res = await cleanData(user.id, client.name);
      setCleaned(res.data);
    } catch (e: any) { setError(e.response?.data?.detail || "Cleaning failed."); }
    finally { setCleaning(false); }
  };

  const gradeColor = (grade: string) => {
    if (grade === "A") return { bg: "bg-green-50",  border: "border-green-200", text: "text-green-700", ring: "bg-green-500" };
    if (grade === "B") return { bg: "bg-blue-50",   border: "border-blue-200",  text: "text-blue-700",  ring: "bg-blue-500" };
    if (grade === "C") return { bg: "bg-yellow-50", border: "border-yellow-200",text: "text-yellow-700",ring: "bg-yellow-500" };
    return                   { bg: "bg-red-50",     border: "border-red-200",   text: "text-red-700",   ring: "bg-red-500" };
  };

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Upload & <span className="text-blue-600 italic">Clean</span></h1>
        <p className="text-sm text-gray-400 mt-1 font-mono">Client · {client?.name} · {client?.domain}</p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-xs font-mono rounded-lg px-4 py-3 mb-5">{error}</div>}

      {!preview && (
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f); }}
          onClick={() => fileRef.current?.click()}
          className={`card border-2 border-dashed cursor-pointer flex flex-col items-center justify-center py-16 transition-colors
            ${dragOver ? "border-blue-400 bg-blue-50" : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"}`}>
          <div className="text-4xl text-gray-300 mb-4">↑</div>
          <div className="text-sm font-medium text-gray-600 mb-1">Drop your CSV file here</div>
          <div className="text-xs text-gray-400">Works with any domain or industry · Max 200MB</div>
          {uploading && (
            <div className="mt-4 flex items-center gap-2 text-xs text-blue-600 font-mono">
              <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              Uploading...
            </div>
          )}
          <input ref={fileRef} type="file" accept=".csv" className="hidden"
            onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
        </div>
      )}

      {preview && !cleaned && (
        <div className="space-y-5">
          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Rows",           value: preview.rows?.toLocaleString() },
              { label: "Columns",        value: preview.columns },
              { label: "Missing Values", value: preview.missing_values },
              { label: "Duplicates",     value: preview.duplicates },
            ].map(s => (
              <div key={s.label} className="card">
                <div className="label">{s.label}</div>
                <div className="text-2xl font-semibold text-gray-900">{s.value}</div>
              </div>
            ))}
          </div>

          {/* Data Quality Score */}
          {loadingQuality ? (
            <div className="card flex items-center gap-3">
              <div className="w-4 h-4 border border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <div className="text-sm text-gray-400 font-mono">Calculating data quality score...</div>
            </div>
          ) : quality && (() => {
            const g = gradeColor(quality.grade);
            return (
              <div className={`card border ${g.border} ${g.bg}`}>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="text-sm font-medium text-gray-900 mb-1">Data Quality Score</div>
                    <div className="text-xs text-gray-500">Automated audit of your dataset</div>
                  </div>
                  <div className="text-right">
                    <div className={`text-4xl font-bold ${g.text}`}>{quality.score}</div>
                    <div className={`text-xs font-mono ${g.text}`}>Grade {quality.grade} / 100</div>
                  </div>
                </div>

                {/* Score bar */}
                <div className="h-2 bg-white rounded-full overflow-hidden mb-5 border border-gray-200">
                  <div className={`h-full rounded-full transition-all duration-1000 ${g.ring}`}
                    style={{ width: `${quality.score}%` }} />
                </div>

                {/* Checks */}
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(quality.checks).map(([key, check]: any) => (
                    <div key={key} className="flex items-start gap-2.5 bg-white rounded-lg p-3 border border-gray-100">
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5
                        ${check.passed ? "bg-green-100 text-green-600" : "bg-red-100 text-red-500"}`}>
                        <span className="text-xs">{check.passed ? "✓" : "!"}</span>
                      </div>
                      <div>
                        <div className="text-xs font-medium text-gray-700 capitalize">{key.replace(/_/g, " ")}</div>
                        <div className={`text-xs mt-0.5 ${check.passed ? "text-green-600" : "text-red-500"}`}>
                          {check.message}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Recommendations */}
                {quality.recommendations?.filter(Boolean).length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-2">Recommendations</div>
                    <div className="space-y-1.5">
                      {quality.recommendations.filter(Boolean).map((rec: string, i: number) => (
                        <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                          <span className="text-orange-500">→</span> {rec}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Preview table */}
          <div className="card">
            <div className="section-title mb-3">Raw data preview</div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100">
                    {preview.column_names?.slice(0, 8).map((col: string) => (
                      <th key={col} className="text-left py-2 px-3 font-mono text-gray-400 font-normal">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.preview?.map((row: any, i: number) => (
                    <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                      {preview.column_names?.slice(0, 8).map((col: string) => (
                        <td key={col} className="py-2 px-3 text-gray-600 truncate max-w-[120px]">{String(row[col] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={handleClean} disabled={cleaning} className="btn-primary">
              {cleaning ? (
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></span>
                  Cleaning...
                </span>
              ) : "Run Cleaning Pipeline"}
            </button>
            <button onClick={() => { setPreview(null); setQuality(null); }} className="btn-secondary">
              Upload different file
            </button>
          </div>
        </div>
      )}

      {cleaned && (
        <div className="space-y-5">
          <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-lg px-4 py-3">
            Data cleaned successfully — {cleaned.rows?.toLocaleString()} rows · {cleaned.columns} columns
          </div>
          <div className="flex gap-3">
            <button onClick={() => router.current.push("/dashboard/insights")} className="btn-primary">
              Continue to Insights →
            </button>
            <button onClick={() => { setPreview(null); setCleaned(null); setQuality(null); }} className="btn-secondary">
              Upload new file
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
