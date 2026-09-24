import { create } from "zustand";
import { API_BASE } from "@/lib/api";

export interface LlmProviderInfo {
  detected: boolean;
  port: number;
  models: string[];
}

interface LlmState {
  providers: Record<string, LlmProviderInfo>;
  provider: string;
  model: string;
  detecting: boolean;
  error: string;
  refresh: () => Promise<void>;
  select: (provider: string, model: string) => void;
}

const PROVIDER_KEY = "llm_provider";
const MODEL_KEY = "llm_model";

function readLS(key: string): string {
  try {
    return localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

function writeLS(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* storage unavailable */
  }
}

export const PROVIDER_ORDER = ["ollama", "lm_studio", "vllm"];

export const useLlmStore = create<LlmState>()((set) => ({
  providers: {},
  provider: readLS(PROVIDER_KEY),
  model: readLS(MODEL_KEY),
  detecting: true,
  error: "",
  refresh: async () => {
    set({ detecting: true, error: "" });
    try {
      const r = await fetch(`${API_BASE}/llm/discover`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = (await r.json()) as {
        providers?: Record<string, LlmProviderInfo>;
      };
      const providers = d.providers ?? {};
      const detected = PROVIDER_ORDER.filter((p) => providers[p]?.detected);
      set((s) => {
        if (detected.length === 0)
          return { providers, provider: "", model: "", detecting: false };
        const provider = detected.includes(s.provider)
          ? s.provider
          : detected[0];
        const models = providers[provider]?.models ?? [];
        const model = models.includes(s.model) ? s.model : (models[0] ?? "");
        writeLS(PROVIDER_KEY, provider);
        writeLS(MODEL_KEY, model);
        return { providers, provider, model, detecting: false };
      });
    } catch (e) {
      set({
        providers: {},
        provider: "",
        model: "",
        detecting: false,
        error: e instanceof Error ? e.message : "unreachable",
      });
    }
  },
  select: (provider, model) => {
    writeLS(PROVIDER_KEY, provider);
    writeLS(MODEL_KEY, model);
    set({ provider, model });
  },
}));
