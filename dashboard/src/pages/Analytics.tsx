import { useMemo, useState } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Tab = "comparison" | "year-over-year" | "recurring";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function Analytics() {
  const [tab, setTab] = useState<Tab>("comparison");

  const tabs: { key: Tab; label: string }[] = [
    { key: "comparison", label: "Period Comparison" },
    { key: "year-over-year", label: "Year over Year" },
    { key: "recurring", label: "Recurring Patterns" },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Analytics</h1>
      <div className="flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.key
                ? "bg-blue-600/20 text-blue-400"
                : "bg-gray-900 text-gray-400 hover:text-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "comparison" && <PeriodComparison />}
      {tab === "year-over-year" && <YearOverYear />}
      {tab === "recurring" && <RecurringPatterns />}
    </div>
  );
}

type Row = Record<string, unknown>;
type FeaturePickerProps = {
  entity: string;
  onEntity: (v: string) => void;
  feature: string;
  onFeature: (v: string) => void;
};
function FeaturePicker({ entity, onEntity, feature, onFeature }: FeaturePickerProps) {
  return (
    <div className="flex items-center gap-3 mb-4 flex-wrap">
      <label className="text-xs text-gray-500">Entity</label>
      <input
        value={entity}
        onChange={(e) => onEntity(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm w-32 outline-none focus:border-blue-500"
      />
      <label className="text-xs text-gray-500">Feature</label>
      <input
        value={feature}
        onChange={(e) => onFeature(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm w-32 outline-none focus:border-blue-500"
      />
    </div>
  );
}

function PeriodComparison() {
  const [entity, setEntity] = useState("sleep");
  const [feature, setFeature] = useState("duration_h");
  const { data, loading, error } = useApi(() => api.analyticsComparison(entity, 14));

  const chartData = useMemo(() => {
    if (!data) return [];
    const map = new Map<string, Row>();
    for (const row of data) {
      const date = row["date"] as string;
      const period = row["period"] as string;
      const features = row["features"] as Row | undefined;
      const val = features?.[feature] ?? 0;
      const existing = map.get(date) ?? { date };
      existing[period] = val;
      map.set(date, existing);
    }
    return [...map.values()].sort((a, b) => (a.date as string).localeCompare(b.date as string));
  }, [data, feature]);

  if (loading) return <Skeleton />;
  if (error) return <ErrorMsg msg={error} />;
  if (!chartData.length) return <EmptyMsg />;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <FeaturePicker entity={entity} onEntity={setEntity} feature={feature} onFeature={setFeature} />
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", fontSize: "12px" }}
          />
          <Legend />
          <Bar dataKey="current" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Current (last 7d)" />
          <Bar dataKey="previous" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Previous (7-14d ago)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function YearOverYear() {
  const [entity, setEntity] = useState("sleep");
  const [feature, setFeature] = useState("duration_h");
  const { data, loading, error } = useApi(() => api.analyticsYearOverYear(entity, feature));

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.map((row) => ({
      ...row,
      label: `${row["year"]}-${String(row["month"]).padStart(2, "0")}-${String(row["day"]).padStart(2, "0")}`,
      value: Number(row[feature] ?? 0),
    }));
  }, [data, feature]);

  if (loading) return <Skeleton />;
  if (error) return <ErrorMsg msg={error} />;
  if (!chartData.length) return <EmptyMsg />;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <FeaturePicker entity={entity} onEntity={setEntity} feature={feature} onFeature={setFeature} />
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="label" stroke="#6b7280" fontSize={12} />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", fontSize: "12px" }}
          />
          <Legend />
          <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} name={feature} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function RecurringPatterns() {
  const [entity, setEntity] = useState("sleep");
  const [feature, setFeature] = useState("duration_h");
  const { data, loading, error } = useApi(() => api.analyticsRecurring(entity, feature));

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.map((row) => ({
      ...row,
      dow_label: DAYS[row["day_of_week"] as number] ?? row["day_of_week"],
      value: Number(row["avg_value"] ?? 0),
    }));
  }, [data]);

  if (loading) return <Skeleton />;
  if (error) return <ErrorMsg msg={error} />;
  if (!chartData.length) return <EmptyMsg />;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <FeaturePicker entity={entity} onEntity={setEntity} feature={feature} onFeature={setFeature} />
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="dow_label" stroke="#6b7280" fontSize={12} />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip
            contentStyle={{ backgroundColor: "#111827", border: "1px solid #1f2937", borderRadius: "8px", fontSize: "12px" }}
          />
          <Legend />
          <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} name={`Avg ${feature}`} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function Skeleton() {
  return <div className="h-64 bg-gray-900 border border-gray-800 rounded-xl animate-pulse" />;
}

function ErrorMsg({ msg }: { msg: string }) {
  return <p className="text-red-400 text-sm">{msg}</p>;
}

function EmptyMsg() {
  return <p className="text-gray-500 text-sm">No data for this selection</p>;
}
