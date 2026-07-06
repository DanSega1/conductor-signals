import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import MetricCard from "../components/MetricCard";
import InsightCard from "../components/InsightCard";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Insight } from "../types";

export default function Dashboard() {
  const health = useApi(() => api.health());
  const obs = useApi(() => api.timeline(10));
  const ins = useApi(() => api.insights(5));

  const sources = obs.data
    ? Object.entries(
        obs.data.reduce<Record<string, number>>((acc, o) => {
          acc[o.source] = (acc[o.source] ?? 0) + 1;
          return acc;
        }, {}),
      ).map(([source, count]) => ({ source, count }))
    : [];

  const hasData = obs.data && obs.data.length > 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Status"
          value={health.data?.status ?? "—"}
          subtitle={health.data ? `v${health.data.version}` : undefined}
          loading={health.loading}
        />
        <MetricCard
          label="Observations"
          value={obs.data?.length ?? 0}
          subtitle="last 10"
          loading={obs.loading}
        />
        <MetricCard
          label="Insights"
          value={ins.data?.length ?? 0}
          subtitle="recent"
          loading={ins.loading}
        />
        <MetricCard
          label="Sources"
          value={sources.length}
          subtitle="active"
          loading={obs.loading}
        />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 min-h-[260px] transition-opacity duration-500" style={{ opacity: obs.loading ? 0.4 : 1 }}>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Observations by Source
        </h2>
        {hasData ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sources}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="source" stroke="#6b7280" fontSize={12} />
              <YAxis stroke="#6b7280" fontSize={12} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#111827",
                  border: "1px solid #1f2937",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                cursor={{ fill: "rgba(59,130,246,0.1)" }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-[200px] text-gray-600 text-sm">
            {obs.loading ? "Loading..." : "No observations yet"}
          </div>
        )}
      </div>

      <div className="transition-opacity duration-500" style={{ opacity: ins.loading ? 0.4 : 1 }}>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Recent Insights
        </h2>
        {ins.data && ins.data.length > 0 ? (
          <div className="space-y-3">
            {ins.data.map((i: Insight) => (
              <InsightCard key={i.id} insight={i} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center text-gray-600 text-sm">
            {ins.loading ? "Loading..." : "No insights yet — click Generate on the Insights page"}
          </div>
        )}
      </div>
    </div>
  );
}
