import { useState } from "react";
import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";
import SidebarToggle from "./SidebarToggle";

const links = [
  { to: "/", label: "Dashboard", icon: "⊞" },
  { to: "/timeline", label: "Timeline", icon: "⊟" },
  { to: "/insights", label: "Insights", icon: "⊡" },
  { to: "/analytics", label: "Analytics", icon: "⊠" },
  { to: "/chat", label: "Chat", icon: "⊡" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950 text-gray-100">
      <aside
        className={`${
          sidebarCollapsed ? "w-14" : "w-60"
        } shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-200`}
      >
        <div className="p-4 border-b border-gray-800 flex items-center gap-2">
          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <h1 className="text-lg font-bold tracking-tight truncate">Observatory</h1>
              <p className="text-xs text-gray-500 mt-0.5 truncate">Conductor Signals</p>
            </div>
          )}
          <SidebarToggle collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed((c) => !c)} />
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-blue-600/20 text-blue-400"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
                } ${sidebarCollapsed ? "justify-center px-0" : ""}`
              }
              title={sidebarCollapsed ? l.label : undefined}
            >
              <span className="w-5 text-center shrink-0">{l.icon}</span>
              {!sidebarCollapsed && <span className="truncate">{l.label}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          {!sidebarCollapsed && <p className="text-xs text-gray-600">v0.1.0</p>}
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
