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

function LLMSettings() {
  const [providers, setProviders] = useState<
    Record<string, { name: string }[]>
  >({});
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [, setStatus] = useState<"loading" | "ready" | "error">("loading");
  useEffect(() => {
    fetch(API_BASE + "/api/llm/providers")
      .then((r) => r.json())
      .then((d) => {
        setProviders(d);
        const savedP = localStorage.getItem("llm_provider") || "ollama";
        const savedM = localStorage.getItem("llm_model") || "";
        setSelectedProvider(savedP);
        const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
        setSelectedModel(
          savedM && models.some((m: { name: string }) => m.name === savedM)
            ? savedM
            : models[0]?.name || "",
        );
        setStatus(models.length > 0 ? "ready" : "error");
      })
      .catch(() => {
        setProviders({ ollama: [{ name: "llama3.2:3b" }] });
        setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
        setStatus("ready");
      });
  }, []);
  const save = (p: string, m: string) => {
    localStorage.setItem("llm_provider", p);
    localStorage.setItem("llm_model", m);
  };
  const models =
    providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader>
        <CardTitle className="text-white">Local LLM</CardTitle>
        <CardDescription className="text-slate-400">
          Select provider and model for AI features
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <select
          className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
          value={selectedProvider}
          onChange={(e) => {
            setSelectedProvider(e.target.value);
            save(e.target.value, "");
          }}
        >
          <option value="ollama">Ollama</option>
          <option value="lm_studio">LM Studio</option>
        </select>
        <select
          className="h-9 w-full rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
          value={selectedModel}
          onChange={(e) => {
            setSelectedModel(e.target.value);
            save(selectedProvider, e.target.value);
          }}
        >
          {models.map((m) => (
            <option key={m.name} value={m.name}>
              {m.name}
            </option>
          ))}
        </select>
      </CardContent>
    </Card>
  );
}

export function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Configuration
        </h2>
        <p className="text-slate-400">Manage connections and preferences</p>
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
                defaultValue="http://localhost:107xx"
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
