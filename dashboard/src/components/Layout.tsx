import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";

const links = [
  { to: "/", label: "Dashboard", icon: "⊞" },
  { to: "/timeline", label: "Timeline", icon: "⊟" },
  { to: "/insights", label: "Insights", icon: "⊡" },
  { to: "/analytics", label: "Analytics", icon: "⊠" },
  { to: "/chat", label: "Chat", icon: "⊡" },
];

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-60 shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold tracking-tight">Observatory</h1>
          <p className="text-xs text-gray-500 mt-0.5">Conductor Signals</p>
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
                }`
              }
            >
              <span className="w-5 text-center">{l.icon}</span>
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <p className="text-xs text-gray-600">v0.1.0</p>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
