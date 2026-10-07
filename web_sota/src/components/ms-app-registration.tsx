import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_BASE } from "../lib/api";

type ConfigState = {
  configured: boolean;
  client_id_hint: string;
  audience: string;
  source: string;
  locked_by_env: boolean;
  redirect_uri: string;
  scopes: string[];
  portal_url: string;
};

const AUDIENCE_LABELS: Record<string, string> = {
  consumers:
    "Personal Microsoft accounts only (outlook.com, live.com, hotmail.com)",
  common: "Any organization AND personal accounts (work/school + personal)",
  organizations: "Organization accounts only (work/school)",
};

type Props = {
  /** Called after a successful save so the parent can refresh its status. */
  onSaved?: () => void;
  /** Show the step-by-step portal guide (the dashboard does; Settings only the form). */
  showGuide?: boolean;
};

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = (await res.json().catch(() => ({}))) as T & { message?: string };
  if (!res.ok) throw new Error(body.message || `HTTP ${res.status}`);
  return body;
}

/** Every user registers their own (free) Microsoft app and pastes its client ID here. */
export function MsAppRegistration({ onSaved, showGuide = true }: Props) {
  const [cfg, setCfg] = useState<ConfigState | null>(null);
  const [clientId, setClientId] = useState("");
  const [audience, setAudience] = useState("common");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [reveal, setReveal] = useState(false);

  const load = useCallback(async () => {
    try {
      const d = await call<ConfigState>("/auth/config");
      setCfg(d);
      // The saved ID is a secret and is never sent to the browser: the field stays empty.
      setClientId("");
      setAudience(d.audience === "custom" ? "common" : d.audience);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = async () => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await call("/auth/config", {
        method: "POST",
        body: JSON.stringify({ client_id: clientId.trim(), audience }),
      });
      setMessage(
        "Saved (stored encrypted for your Windows user). Next: sign in with your Microsoft account.",
      );
      setReveal(false);
      await load();
      onSaved?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const copyRedirect = async () => {
    try {
      await navigator.clipboard.writeText("http://localhost");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard may be unavailable; the text is visible */
    }
  };

  if (!cfg) {
    return (
      <p className="text-sm text-slate-300" data-testid="msapp-loading">
        {error || "Loading..."}
      </p>
    );
  }

  return (
    <div className="space-y-4" data-testid="msapp-registration">
      {showGuide && (
        <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-200">
          <li>
            Open the{" "}
            <a
              href={cfg.portal_url}
              target="_blank"
              rel="noreferrer"
              className="underline"
              data-testid="msapp-portal-link"
            >
              Azure portal
            </a>{" "}
            and sign in with any Microsoft account. Go to{" "}
            <strong>Microsoft Entra ID</strong>, then{" "}
            <strong>App registrations</strong>, then{" "}
            <strong>New registration</strong>. It is free.
          </li>
          <li>
            Name it anything (for example <em>OneNote MCP</em>). Under{" "}
            <strong>Supported account types</strong> choose the option that
            matches your OneNote: personal accounts only, or both. Leave the
            redirect URI empty for now and click <strong>Register</strong>.
          </li>
          <li>
            Open <strong>Authentication</strong>, then{" "}
            <strong>Add a platform</strong>, then{" "}
            <strong>Mobile and desktop applications</strong>, and add the
            redirect URI{" "}
            <code className="rounded bg-slate-800 px-1">http://localhost</code>{" "}
            <button
              type="button"
              className="underline"
              onClick={copyRedirect}
              data-testid="msapp-copy-redirect"
            >
              {copied ? "copied" : "copy"}
            </button>
            . Still on that page, set <strong>Allow public client flows</strong>{" "}
            to <strong>Yes</strong> and save.
          </li>
          <li>
            Open <strong>API permissions</strong>, then{" "}
            <strong>Add a permission</strong>, then{" "}
            <strong>Microsoft Graph</strong>, then <strong>Delegated</strong>,
            and add: <strong>{cfg.scopes.join(", ")}</strong>.
          </li>
          <li>
            On the <strong>Overview</strong> page copy the{" "}
            <strong>Application (client) ID</strong> and paste it below.
          </li>
        </ol>
      )}

      <div className="grid gap-2">
        <Label className="text-slate-300" htmlFor="msapp-client-id">
          Application (client) ID
        </Label>
        <div className="flex gap-2">
          <Input
            id="msapp-client-id"
            data-testid="msapp-client-id"
            type={reveal ? "text" : "password"}
            autoComplete="off"
            className="border-slate-800 bg-slate-900 text-slate-100 placeholder:text-slate-300"
            placeholder={
              cfg.configured
                ? `Saved (ends ${cfg.client_id_hint}). Paste a new ID only to replace it`
                : "12345678-abcd-1234-abcd-1234567890ab"
            }
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            disabled={cfg.locked_by_env || busy}
            spellCheck={false}
          />
          <Button
            type="button"
            variant="outline"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            onClick={() => setReveal((v) => !v)}
            data-testid="msapp-reveal"
          >
            {reveal ? "Hide" : "Show"}
          </Button>
        </div>
        <p className="text-sm text-slate-300">
          Treated as a secret: stored encrypted for your Windows user, never
          shown again, never sent anywhere except Microsoft sign-in.
        </p>
      </div>
      <div className="grid gap-2">
        <Label className="text-slate-300" htmlFor="msapp-audience">
          Supported account types (must match what you chose in step 2)
        </Label>
        <select
          id="msapp-audience"
          data-testid="msapp-audience"
          className="h-9 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-200"
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          disabled={cfg.locked_by_env || busy}
        >
          {Object.entries(AUDIENCE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {cfg.locked_by_env ? (
        <p className="text-sm text-amber-300" data-testid="msapp-env-locked">
          The client ID is set by the ONENOTE_CLIENT_ID environment variable on
          this computer; change it there.
        </p>
      ) : (
        <Button
          variant="outline"
          className="border-slate-800 text-slate-300 hover:bg-slate-800"
          onClick={save}
          disabled={busy || (clientId.trim() === "" && !cfg.configured)}
          data-testid="msapp-save"
        >
          {busy ? "Saving..." : cfg.configured ? "Update" : "Save"}
        </Button>
      )}
      {message && (
        <p className="text-sm text-emerald-300" data-testid="msapp-message">
          {message}
        </p>
      )}
      {error && (
        <p className="text-sm text-red-300" data-testid="msapp-error">
          {error}
        </p>
      )}
    </div>
  );
}
