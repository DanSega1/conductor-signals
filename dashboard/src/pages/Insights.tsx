import { useState } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import InsightCard from "../components/InsightCard";
import type { Insight } from "../types";

export default function Insights() {
  const { data, loading, error, refetch } = useApi(() => api.insights(50));
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.generateInsights();
      refetch();
    } catch {
      /* ignore */
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Insights</h1>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {generating ? "Generating..." : "Generate New"}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 text-sm text-red-400">
          Failed to load: {error}
        </div>
      )}

      <div className="transition-opacity duration-500" style={{ opacity: loading ? 0.4 : 1 }}>
        {!loading && (!data || data.length === 0) ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No insights yet</p>
            <p className="text-sm mt-1">Click "Generate New" to analyze your data</p>
          </div>
        ) : (
          <div className="space-y-3">
            {(data ?? []).map((i: Insight) => (
              <InsightCard key={i.id} insight={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
