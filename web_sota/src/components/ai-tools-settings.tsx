import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { API_BASE } from "../lib/api";

type ClientRow = {
  id: string;
  label: string;
  status: string;
  detail: string;
};

type StatusResponse = {
  success: boolean;
  message?: string;
  command?: string;
  clients?: ClientRow[];
};

type ChangeResponse = {
  success: boolean;
  message?: string;
  results?: ClientRow[];
};

const STATUS_TEXT: Record<string, { text: string; tone: string }> = {
  present: { text: "Registered", tone: "text-emerald-300" },
  absent: { text: "Not registered", tone: "text-slate-300" },
  "not-found": { text: "Not installed", tone: "text-slate-300" },
  skipped: { text: "Config can't be edited safely", tone: "text-amber-300" },
};

async function call<T>(
  path: string,
  init?: RequestInit,
  timeoutMs = 120_000,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      signal: controller.signal,
    });
    const body = (await res.json().catch(() => ({}))) as T & {
      message?: string;
    };
    if (!res.ok) throw new Error(body.message || `HTTP ${res.status}`);
    return body;
  } finally {
    clearTimeout(timer);
  }
}

/** Register this server in the user's AI tools (Claude Desktop, Cursor, ...). */
export function AiToolsSettings() {
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await call<StatusResponse>(
        "/mcp-clients",
        undefined,
        90_000,
      );
      const rows = data.clients ?? [];
      setClients(rows);
      // Default: tick every detected tool that is not registered yet.
      setSelected(
        new Set(rows.filter((r) => r.status === "absent").map((r) => r.id)),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const apply = async (action: "register" | "unregister") => {
    const ids = [...selected];
    if (ids.length === 0) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const res = await call<ChangeResponse>(`/mcp-clients/${action}`, {
        method: "POST",
        body: JSON.stringify({ clients: ids }),
      });
      const summary = (res.results ?? [])
        .map((r) => `${r.label}: ${r.status}`)
        .join(", ");
      setMessage(`${summary}. ${res.message ?? ""}`.trim());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const detected = clients.filter((c) => c.status !== "not-found");
  const selectable = (c: ClientRow) =>
    c.status === "absent" || c.status === "present";
  const canRegister = [...selected].some((id) =>
    clients.find((c) => c.id === id && c.status === "absent"),
  );
  const canRemove = [...selected].some((id) =>
    clients.find((c) => c.id === id && c.status === "present"),
  );

  return (
    <Card
      className="border-slate-800 bg-slate-950/50"
      data-testid="ai-tools-card"
    >
      <CardHeader>
        <CardTitle className="text-white">AI tools</CardTitle>
        <CardDescription className="text-slate-300">
          Add OneNote MCP to Claude Desktop, Cursor, Antigravity, Windsurf,
          OpenCode and Claude Code so they can read and write your notes.
          Backups of each config file are made first and nothing else in them is
          changed.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading ? (
          <p className="text-sm text-slate-300" data-testid="ai-tools-loading">
            Looking for installed AI tools...
          </p>
        ) : detected.length === 0 && !error ? (
          <p className="text-sm text-slate-300" data-testid="ai-tools-empty">
            No supported AI tool found on this computer. Install one, then press
            Re-detect.
          </p>
        ) : (
          <ul className="space-y-2">
            {clients.map((c) => {
              const st = STATUS_TEXT[c.status] ?? {
                text: c.status,
                tone: "text-slate-300",
              };
              const installed = c.status !== "not-found";
              return (
                <li
                  key={c.id}
                  data-testid={`ai-tool-row-${c.id}`}
                  className={`flex items-start gap-3 rounded border border-slate-800 px-3 py-2 ${
                    installed ? "" : "opacity-60"
                  }`}
                >
                  <input
                    type="checkbox"
                    className="mt-1 h-4 w-4 accent-emerald-500"
                    data-testid={`ai-tool-check-${c.id}`}
                    checked={selected.has(c.id)}
                    disabled={!selectable(c) || busy}
                    onChange={() => toggle(c.id)}
                    aria-label={`Select ${c.label}`}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-x-3">
                      <span className="text-sm font-medium text-slate-100">
                        {c.label}
                      </span>
                      <span
                        className={`text-sm ${st.tone}`}
                        data-testid={`ai-tool-status-${c.id}`}
                      >
                        {st.text}
                      </span>
                    </div>
                    {c.status === "skipped" && (
                      <p className="break-words text-sm text-slate-300">
                        {c.detail}
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            onClick={() => apply("register")}
            disabled={busy || loading || !canRegister}
            data-testid="ai-tools-register"
          >
            {busy ? "Working..." : "Register selected"}
          </Button>
          <Button
            variant="outline"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            onClick={() => apply("unregister")}
            disabled={busy || loading || !canRemove}
            data-testid="ai-tools-remove"
          >
            Remove selected
          </Button>
          <Button
            variant="outline"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            onClick={load}
            disabled={busy || loading}
            data-testid="ai-tools-refresh"
          >
            Re-detect
          </Button>
        </div>

        {message && (
          <p
            className="text-sm text-emerald-300"
            data-testid="ai-tools-message"
          >
            {message}
          </p>
        )}
        {error && (
          <p className="text-sm text-red-300" data-testid="ai-tools-error">
            {error}{" "}
            <button
              type="button"
              className="underline"
              onClick={load}
              data-testid="ai-tools-retry"
            >
              Retry
            </button>
          </p>
        )}
      </CardContent>
    </Card>
  );
}
