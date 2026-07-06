import { type FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import { useTheme } from "../hooks/useTheme";

const PROVIDER_DEFAULTS: Record<string, { model: string; base_url: string }> = {
  openrouter: { model: "gpt-4o-mini", base_url: "https://openrouter.ai/api/v1" },
  openai: { model: "gpt-4o-mini", base_url: "https://api.openai.com/v1" },
  anthropic: { model: "claude-3-haiku-20240307", base_url: "https://api.anthropic.com/v1" },
  ollama: { model: "llama3.2", base_url: "http://localhost:11434/v1" },
};

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

  useEffect(() => {
    api.getLLMSettings().then((s) => {
      setProvider(s.provider);
      setModel(s.model);
      setBaseUrl(s.base_url);
      setAvailableProviders(s.available_providers);
    }).catch(() => {}).finally(() => setLoading(false));
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
