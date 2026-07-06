import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import type { Observation } from "../types";

export default function Timeline() {
  const { data, loading, error, refetch } = useApi(() => api.timeline(200));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Timeline</h1>
        <button
          onClick={refetch}
          className="px-3 py-1.5 bg-gray-800 rounded-lg text-xs hover:bg-gray-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 text-sm text-red-400">
          Failed to load: {error}
        </div>
      )}

      <div
        className="space-y-2 transition-opacity duration-500"
        style={{ opacity: loading ? 0.4 : 1 }}
      >
        {!loading && (!data || data.length === 0) ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No observations yet</p>
          </div>
        ) : (
          (data ?? []).slice(0, loading ? 10 : undefined).map((o: Observation) => (
            <div
              key={o.id}
              className={`bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-start gap-4 ${
                loading ? "opacity-40" : ""
              }`}
            >
              <div className="text-xs text-gray-500 font-mono w-32 shrink-0 pt-0.5">
                {new Date(o.timestamp).toLocaleString()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-blue-400 bg-blue-400/10 px-2 py-0.5 rounded">
                    {o.source}
                  </span>
                  <span className="text-xs text-gray-500">/</span>
                  <span className="text-sm font-medium">{o.entity}</span>
                </div>
                {Object.keys(o.features).length > 0 && (
                  <pre className="text-xs text-gray-500 mt-1 truncate">
                    {JSON.stringify(o.features)}
                  </pre>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
