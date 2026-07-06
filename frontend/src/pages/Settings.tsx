import { type FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { useTheme } from "../hooks/useTheme";
import type { IntegrationDef } from "../types";

const PROVIDER_DEFAULTS: Record<string, { model: string; base_url: string }> = {
  openrouter: { model: "gpt-4o-mini", base_url: "https://openrouter.ai/api/v1" },
  openai: { model: "gpt-4o-mini", base_url: "https://api.openai.com/v1" },
  anthropic: { model: "claude-3-haiku-20240307", base_url: "https://api.anthropic.com/v1" },
  ollama: { model: "llama3.2", base_url: "http://localhost:11434/v1" },
};

function IntegrationCard({ integration: def }: { integration: IntegrationDef }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const update = useCallback((key: string, val: string) => {
    setValues((prev) => ({ ...prev, [key]: val }));
  }, []);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateIntegration(def.source, values);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  const authUrl = `/api/auth/${def.source}/login`;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="font-medium">{def.label}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {def.auth_type === "oauth"
              ? def.connected
                ? "Connected"
                : "Not connected"
              : def.fields.some((f) => f.configured)
                ? "Configured"
                : "Not configured"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {def.auth_type === "oauth" ? (
            def.connected ? (
              <span className="text-xs text-green-500">✓ Connected</span>
            ) : (
              <a
                href={authUrl}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm transition-colors"
              >
                Connect
              </a>
            )
          ) : null}
          {def.doc_url && (
            <a
              href={def.doc_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-500 hover:text-gray-300 underline"
            >
              Get credentials
            </a>
          )}
        </div>
      </div>

      {/* API key fields */}
      {def.auth_type !== "oauth" && (
        <form onSubmit={handleSave} className="space-y-3">
          {def.fields.map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-medium mb-1 text-gray-400">{f.label}</label>
              {f.type === "select" && f.options ? (
                <select
                  value={values[f.key] ?? ""}
                  onChange={(e) => update(f.key, e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="">Default</option>
                  {f.options.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
              ) : (
                <input
                  type={f.type === "password" ? "password" : "text"}
                  value={values[f.key] ?? ""}
                  onChange={(e) => update(f.key, e.target.value)}
                  placeholder={f.placeholder || f.label}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
                />
              )}
            </div>
          ))}
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm disabled:opacity-50 transition-colors"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            {saved && <span className="text-sm text-green-500">Saved!</span>}
          </div>
        </form>
      )}

      {/* OAuth fields (client_id, client_secret) */}
      {def.auth_type === "oauth" && !def.connected && (
        <form onSubmit={handleSave} className="space-y-3">
          {def.fields.map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-medium mb-1 text-gray-400">{f.label}</label>
              <input
                type={f.type === "password" ? "password" : "text"}
                value={values[f.key] ?? ""}
                onChange={(e) => update(f.key, e.target.value)}
                placeholder={f.label}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          ))}
          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm disabled:opacity-50 transition-colors"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            {saved && <span className="text-sm text-green-500">Saved!</span>}
          </div>
        </form>
      )}
    </div>
  );
}

export default function Settings() {
  const { theme, toggle } = useTheme();

  const [provider, setProvider] = useState("openrouter");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const [integrations, setIntegrations] = useState<IntegrationDef[]>([]);
  const [authMsg, setAuthMsg] = useState<string | null>(null);

  useEffect(() => {
    api.getLLMSettings().then((s) => {
      setProvider(s.provider);
      setModel(s.model);
      setBaseUrl(s.base_url);
      setAvailableProviders(s.available_providers);
    }).catch(() => {}).finally(() => setLoading(false));

    api.getIntegrations().then((r) => setIntegrations(r.integrations)).catch(() => {});

    const params = new URLSearchParams(window.location.search);
    const authProvider = params.get("auth");
    const authResult = params.get("status");
    if (authProvider && authResult) {
      setAuthMsg(`${authProvider}: ${authResult === "success" ? "Connected successfully!" : authResult}`);
      window.history.replaceState({}, "", "/settings");
      if (authResult === "success") {
        api.getIntegrations().then((r) => setIntegrations(r.integrations)).catch(() => {});
      }
    }
  }, []);

  const handleProviderChange = (p: string) => {
    setProvider(p);
    const defaults = PROVIDER_DEFAULTS[p];
    if (defaults) {
      setModel(defaults.model);
      setBaseUrl(defaults.base_url);
    }
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateLLMSettings({ provider, api_key: apiKey, model, base_url: baseUrl });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 opacity-50 transition-opacity">
        <p className="text-gray-500">Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {authMsg && (
        <div className="mb-4 px-4 py-3 bg-blue-600/20 border border-blue-600/30 rounded-xl text-sm">
          {authMsg}
        </div>
      )}

      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Appearance</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Theme</p>
              <p className="text-sm text-gray-500 mt-0.5">
                Currently: {theme === "dark" ? "Dark" : "Light"}
              </p>
            </div>
            <button
              onClick={toggle}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors"
            >
              {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
            </button>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Integrations</h2>
        <div className="space-y-3">
          {integrations.map((def) => (
            <IntegrationCard key={def.source} integration={def} />
          ))}
        </div>
        {integrations.length === 0 && (
          <p className="text-sm text-gray-500">No integrations available.</p>
        )}
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">AI Provider</h2>
        <form onSubmit={handleSave} className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">Provider</label>
            <select
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
            >
              {availableProviders.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
            />
            <p className="text-xs text-gray-600 mt-1">Leave empty to keep existing key. Not needed for Ollama.</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Model</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="gpt-4o-mini"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Base URL</label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://openrouter.ai/api/v1"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-blue-600 rounded-lg text-sm font-medium hover:bg-blue-500 disabled:opacity-50 transition-colors"
            >
              {saving ? "Saving..." : "Save"}
            </button>
            {saved && <span className="text-sm text-green-500">Saved!</span>}
          </div>
        </form>
      </section>
    </div>
  );
}
