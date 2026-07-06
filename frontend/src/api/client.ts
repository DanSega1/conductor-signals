const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<import("../types").HealthStatus>("/health"),

  timeline: (limit = 200) =>
    request<import("../types").Observation[]>(`/timeline?limit=${limit}`),

  observations: (opts?: { source?: string; entity?: string; limit?: number; offset?: number }) => {
    const params = new URLSearchParams();
    if (opts?.source) params.set("source", opts.source);
    if (opts?.entity) params.set("entity", opts.entity);
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.offset) params.set("offset", String(opts.offset));
    return request<import("../types").Observation[]>(`/observations?${params}`);
  },

  insights: (limit = 50) =>
    request<import("../types").Insight[]>(`/insights?limit=${limit}`),

  generateInsights: () =>
    request<{ generated: number }>("/insights/generate", { method: "POST" }),

  analyticsRecent: (limit = 50) =>
    request<Record<string, unknown>[]>(`/analytics/recent?limit=${limit}`),

  analyticsComparison: (entity: string, days = 7) =>
    request<Record<string, unknown>[]>(`/analytics/comparison?entity=${encodeURIComponent(entity)}&days=${days}`),

  analyticsYearOverYear: (entity: string, feature: string) =>
    request<Record<string, unknown>[]>(
      `/analytics/year-over-year?entity=${encodeURIComponent(entity)}&feature=${encodeURIComponent(feature)}`,
    ),

  analyticsRecurring: (entity: string, feature: string) =>
    request<Record<string, unknown>[]>(
      `/analytics/recurring?entity=${encodeURIComponent(entity)}&feature=${encodeURIComponent(feature)}`,
    ),

  chat: (message: string) =>
    request<import("../types").ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  getLLMSettings: () =>
    request<import("../types").LLMSettings>("/settings/llm"),

  updateLLMSettings: (body: import("../types").LLMSettingsUpdate) =>
    request<import("../types").LLMSettingsUpdate>("/settings/llm", {
      method: "PUT",
      body: JSON.stringify(body),
    }),
};
