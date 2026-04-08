"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [client, setClient] = useState<any>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/");
    const stored = localStorage.getItem("analytiq_client");
    if (stored) setClient(JSON.parse(stored));
    else if (!loading && user) router.push("/workspace");
  }, [user, loading]);

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400 text-sm">Loading...</div>;

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar activeClient={client} />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
