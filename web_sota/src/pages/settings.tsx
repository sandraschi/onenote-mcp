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

interface ProviderInfo {
  detected: boolean;
  port: number;
  models: string[];
}

interface DiscoverPayload {
  ollama_detected?: boolean;
  configured_model?: string;
  providers: Record<string, ProviderInfo>;
}

const PROVIDER_ORDER = ["ollama", "lm_studio", "vllm"];
const PROVIDER_LABELS: Record<string, string> = {
  ollama: "Ollama",
  lm_studio: "LM Studio",
  vllm: "vLLM",
};

function LLMSettings() {
  const [providers, setProviders] = useState<Record<string, ProviderInfo>>({});
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [detecting, setDetecting] = useState(true);
  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/llm/discover`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d: DiscoverPayload) => {
        if (cancelled) return;
        const detected = PROVIDER_ORDER.filter(
          (p) => d.providers?.[p]?.detected,
        );
        if (detected.length === 0) {
          setProviders(d.providers ?? {});
          setSelectedProvider("");
          setSelectedModel("");
          setDetecting(false);
          return;
        }
        const savedP = localStorage.getItem("llm_provider");
        const first = detected.includes(savedP ?? "") ? savedP! : detected[0];
        setProviders(d.providers);
        setSelectedProvider(first);
        const savedM = localStorage.getItem("llm_model") ?? "";
        const models = d.providers[first]?.models ?? [];
        setSelectedModel(models.includes(savedM) ? savedM : (models[0] ?? ""));
        setDetecting(false);
      })
      .catch(() => {
        if (!cancelled) {
          setProviders({});
          setSelectedProvider("");
          setSelectedModel("");
          setDetecting(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);
  const save = (p: string, m: string) => {
    localStorage.setItem("llm_provider", p);
    localStorage.setItem("llm_model", m);
  };
  const models = selectedProvider
    ? (providers[selectedProvider]?.models ?? [])
    : [];
  const detectedProviders = PROVIDER_ORDER.filter(
    (p) => providers[p]?.detected,
  );
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
            setSelectedProvider(p);
            const modelsFor = providers[p]?.models ?? [];
            setSelectedModel(modelsFor[0] ?? "");
            save(p, modelsFor[0] ?? "");
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
            setSelectedModel(e.target.value);
            save(selectedProvider, e.target.value);
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
            <CardDescription className="text-slate-400">
              Connection details for the backend server
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label className="text-slate-300">API Host</Label>
              <Input
                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                defaultValue="http://127.0.0.1:10907"
              />
            </div>
            <Button
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
            >
              Test Connection
            </Button>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Advanced Integration</CardTitle>
            <CardDescription className="text-slate-400">
              Custom connection parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label className="text-slate-300">Timeout (ms)</Label>
              <Input
                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-400"
                defaultValue="5000"
              />
            </div>
            <Button
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
            >
              Save Parameters
            </Button>
          </CardContent>
        </Card>

        <LLMSettings />
      </div>
    </div>
  );
}
