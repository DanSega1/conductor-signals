import type { Insight } from "../types";

interface Props {
  insight: Insight;
}

export default function InsightCard({ insight }: Props) {
  const confidencePct = Math.round(insight.confidence * 100);
  const barColor =
    confidencePct >= 80 ? "bg-green-500" : confidencePct >= 50 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-sm truncate">{insight.title}</h3>
          <p className="text-sm text-gray-400 mt-1 line-clamp-3">{insight.description}</p>
        </div>
        <span className="text-xs text-gray-500 shrink-0">
          {new Date(insight.timestamp).toLocaleDateString()}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span className="text-xs text-gray-500">confidence</span>
        <div className="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${barColor}`}
            style={{ width: `${confidencePct}%` }}
          />
        </div>
        <span className="text-xs font-mono text-gray-400">{confidencePct}%</span>
      </div>
    </div>
  );
}
