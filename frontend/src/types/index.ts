export interface Observation {
  id: string;
  timestamp: string;
  source: string;
  category: string;
  entity: string;
  features: Record<string, unknown>;
  metadata: Record<string, unknown>;
  version: number;
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  source: string;
  confidence: number;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  response: string;
}

export interface AnalyticsRow {
  [key: string]: unknown;
}
