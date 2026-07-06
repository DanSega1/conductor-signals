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

export interface LLMSettings {
  provider: string;
  api_key: string;
  model: string;
  base_url: string;
  available_providers: string[];
}

export interface LLMSettingsUpdate {
  provider: string;
  api_key: string;
  model: string;
  base_url: string;
}

export interface AuthStatus {
  providers: Record<string, boolean>;
}

export interface IntegrationFieldDef {
  key: string;
  label: string;
  type: string;
  placeholder: string;
  options: string[] | null;
  required: boolean;
  configured: boolean;
}

export interface IntegrationDef {
  source: string;
  label: string;
  auth_type: string;
  doc_url: string;
  fields: IntegrationFieldDef[];
  oauth_scopes: string;
  connected: boolean;
}

export interface IntegrationsResponse {
  integrations: IntegrationDef[];
}
