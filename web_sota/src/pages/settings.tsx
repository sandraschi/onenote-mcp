import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_BASE } from "../lib/api";
import { PROVIDER_ORDER, useLlmStore } from "../store/llm";

const PROVIDER_LABELS: Record<string, string> = {
  ollama: "Ollama",
  lm_studio: "LM Studio",
  vllm: "vLLM",
};

function LLMSettings() {
  const { providers, provider, model, detecting, refresh, select } =
    useLlmStore();
  useEffect(() => {
    refresh();
  }, [refresh]);
  const models = provider ? (providers[provider]?.models ?? []) : [];
  const detectedProviders = PROVIDER_ORDER.filter(
    (p) => providers[p]?.detected,
  );
  const selectedProvider = provider;
  const selectedModel = model;
  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader>
        <CardTitle className="text-white">Local LLM</CardTitle>
        <CardDescription className="text-slate-300">
          Select provider and model for AI features
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2">
          <span
            data-testid="llm-status"
            className={`h-2 w-2 rounded-full ${
              detecting
                ? "animate-pulse bg-slate-500"
                : detectedProviders.length > 0
                  ? "bg-emerald-500"
                  : "bg-red-500"
            }`}
          />
          <span className="text-sm text-slate-300">
            {detecting
              ? "Detecting..."
              : detectedProviders.length > 0
                ? "Local LLM detected"
                : "No local LLM detected - start Ollama or LM Studio"}
          </span>
        </div>
        <select
          data-testid="llm-provider-select"
          className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
          value={selectedProvider}
          disabled={detectedProviders.length === 0}
          onChange={(e) => {
            const p = e.target.value;
            const modelsFor = providers[p]?.models ?? [];
            select(p, modelsFor[0] ?? "");
          }}
        >
          {detectedProviders.length === 0 && (
            <option value="">No local LLM detected</option>
          )}
          {detectedProviders.map((p) => (
            <option key={p} value={p}>
              {PROVIDER_LABELS[p] ?? p} (:{providers[p]?.port ?? 0})
            </option>
          ))}
        </select>
        <select
          data-testid="llm-model-select"
          className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
          value={selectedModel}
          disabled={models.length === 0}
          onChange={(e) => {
            select(selectedProvider, e.target.value);
          }}
        >
          {models.length === 0 && <option value="">No models available</option>}
          {models.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </CardContent>
    </Card>
  );
}

export function Settings() {
  const [probe, setProbe] = useState<string | null>(null);
  const [probing, setProbing] = useState(false);
  const testConnection = async () => {
    setProbing(true);
    setProbe(null);
    try {
      const r = await fetch(`${API_BASE}/status`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = (await r.json()) as { version?: string; tool_count?: number };
      setProbe(
        `Connected - v${d.version ?? "?"} - ${d.tool_count ?? "?"} tools`,
      );
    } catch (e) {
      setProbe(e instanceof Error ? `Failed: ${e.message}` : "Failed");
    } finally {
      setProbing(false);
    }
  };
  return (
    <div className="space-y-6" data-testid="settings-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Configuration
        </h2>
        <p className="text-slate-300">Manage connections and preferences</p>
      </div>

      <div className="grid gap-6">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">
              API Bridge Configuration
            </CardTitle>
            <CardDescription className="text-slate-300">
              Connection details for the backend server
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label className="text-slate-300">API Host</Label>
              <Input
                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-300"
                defaultValue="http://127.0.0.1:10907"
                readOnly
              />
            </div>
            <Button
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
              onClick={testConnection}
              disabled={probing}
              data-testid="settings-test-connection"
            >
              {probing ? "Testing..." : "Test Connection"}
            </Button>
            {probe && (
              <p
                className="text-sm text-slate-300"
                data-testid="settings-probe-result"
              >
                {probe}
              </p>
            )}
          </CardContent>
        </Card>

        <LLMSettings />
      </div>
    </div>
  );
}
