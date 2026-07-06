import type { ReactNode } from "react";

interface Props {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  loading?: boolean;
}

export default function MetricCard({ label, value, subtitle, icon, loading }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 min-h-[104px]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          {label}
        </span>
        {icon && <span className="text-gray-600">{icon}</span>}
      </div>
      <div className="text-2xl font-bold transition-opacity duration-500" style={{ opacity: loading ? 0.3 : 1 }}>
        {loading ? "—" : value}
      </div>
      <div className="h-4 mt-1">
        {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
      </div>
    </div>
  );
}
