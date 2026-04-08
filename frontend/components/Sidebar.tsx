"use client";

import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

interface Client { id: number; name: string; domain: string; }
interface SidebarProps { activeClient?: Client | null; }

const navItems = [
  { label: "Overview",        icon: "◈", href: "/dashboard" },
  { label: "Upload & Clean",  icon: "↗", href: "/dashboard/upload" },
  { label: "Insights",        icon: "◎", href: "/dashboard/insights" },
  { label: "ML Model",        icon: "⬡", href: "/dashboard/model" },
  { label: "Forecast",        icon: "△", href: "/dashboard/forecast" },
  { label: "Recommendations", icon: "◉", href: "/dashboard/recommendations" },
  { label: "Ask AI",          icon: "◌", href: "/dashboard/ask-ai" },
  { label: "Narrative",       icon: "◻", href: "/dashboard/narrative" },
  { label: "Dashboard",       icon: "▦", href: "/dashboard/interactive", badge: "NEW" },
  { label: "What-If",         icon: "⟳", href: "/dashboard/simulator",   badge: "NEW" },
  { label: "Export",          icon: "↓", href: "/dashboard/export" },
];

export default function Sidebar({ activeClient }: SidebarProps) {
  const router   = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-[220px] bg-white border-r border-gray-200 flex flex-col flex-shrink-0 h-screen sticky top-0">
      <div className="p-5 pb-4 border-b border-gray-100">
        <div className="text-lg font-bold text-gray-900 tracking-tight">Analytiq</div>
        <div className="text-[10px] font-mono text-gray-400 uppercase tracking-widest mt-0.5">AI Analytics Platform</div>
      </div>

      <nav className="flex-1 p-3 overflow-y-auto">
        <div className="text-xs font-mono text-gray-400 uppercase tracking-widest mb-3 mt-3 px-2">Navigation</div>

        <button onClick={() => router.push("/workspace")}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm mb-0.5 transition-colors text-left
            ${pathname === "/workspace" ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"}`}>
          <span className="font-mono text-base w-4 flex-shrink-0">◱</span>
          Workspace
        </button>

        <div className="h-px bg-gray-100 my-2" />

        {navItems.map((item) => {
          const isActive   = pathname === item.href;
          const isDisabled = !activeClient && item.href !== "/dashboard";
          return (
            <button key={item.href}
              onClick={() => !isDisabled && router.push(item.href)}
              disabled={isDisabled}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm mb-0.5 transition-colors text-left
                ${isActive   ? "bg-blue-50 text-blue-700 font-medium" : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"}
                ${isDisabled ? "opacity-30 cursor-not-allowed" : "cursor-pointer"}`}>
              <span className="font-mono text-base w-4 flex-shrink-0">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className="text-[9px] bg-blue-100 text-blue-600 px-1.5 py-0.5 rounded font-mono">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {activeClient && (
        <div className="mx-3 mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-[9px] font-mono text-gray-400 uppercase tracking-wider mb-1">Active client</div>
          <div className="text-sm font-medium text-gray-900 truncate">{activeClient.name}</div>
          <div className="text-xs text-gray-400 truncate">{activeClient.domain}</div>
        </div>
      )}

      <div className="p-3 border-t border-gray-100">
        <div className="text-xs text-gray-500 px-2 mb-2">
          Signed in as <span className="font-medium text-gray-900">{user?.username}</span>
        </div>
        <button onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-red-50 rounded-lg transition-colors">
          <span className="font-mono">→</span> Sign out
        </button>
      </div>
    </aside>
  );
}
