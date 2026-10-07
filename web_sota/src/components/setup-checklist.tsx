import { CheckCircle2, Circle } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE } from "../lib/api";
import { MsAppRegistration } from "./ms-app-registration";

type ClientRow = { id: string; label: string; status: string };

type Props = {
  /** undefined until the backend status has loaded */
  configured: boolean | undefined;
  signedIn: boolean | undefined;
  /** Ask the parent to re-read backend status (after saving the app registration). */
  onChanged: () => void;
};

/**
 * Under-hero onboarding (ONBOARDING_STANDARD: big red CTA until onboarded). Three steps:
 *  1. register your own Microsoft app (each user must; paste its client ID),
 *  2. sign in to your OneNote with it,
 *  3. connect your AI tools (Claude, Cursor, ...).
 * The app and its backend running does NOT mean Claude/Cursor can use the tools: that is step 3.
 */
export function SetupChecklist({ configured, signedIn, onChanged }: Props) {
  const [clients, setClients] = useState<ClientRow[] | null>(null);
  const guideRef = useRef<HTMLLIElement | null>(null);

  const detect = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}/mcp-clients`);
      if (!r.ok) throw new Error(String(r.status));
      const d = (await r.json()) as { clients?: ClientRow[] };
      setClients(d.clients ?? []);
    } catch {
      setClients(null);
    }
  }, []);

  useEffect(() => {
    detect();
    // A tool installed (or registered) while this page is open: re-check on return.
    window.addEventListener("focus", detect);
    return () => window.removeEventListener("focus", detect);
  }, [detect]);

  if (configured === undefined || signedIn === undefined) return null;

  const found = (clients ?? []).filter((c) => c.status !== "not-found");
  const registered = found.filter((c) => c.status === "present");
  const toolsDone = registered.length > 0;
  const toolsKnown = clients !== null;

  if (configured && signedIn && toolsDone) {
    return (
      <div
        className="rounded-md border border-emerald-700/50 bg-emerald-950/30 px-4 py-2 text-sm text-emerald-200"
        data-testid="onboarding-done"
      >
        All set: your Microsoft app is registered, you are signed in, and{" "}
        {registered.map((c) => c.label).join(", ")} can use OneNote. Restart
        those tools once if they were open when you connected them.
      </div>
    );
  }

  if (configured && signedIn && toolsKnown && found.length === 0) {
    return (
      <div
        className="rounded-md border border-slate-700 bg-slate-900/50 px-4 py-2 text-sm text-slate-200"
        data-testid="onboarding-no-tools"
      >
        Signed in. No supported AI tool (Claude Desktop, Cursor, Antigravity,
        Windsurf, OpenCode, Claude Code) was found on this computer; the app
        works without one. Install one and return here to connect it.
      </div>
    );
  }

  const cta = !configured
    ? { text: "Complete setup: register your Microsoft app", to: "" }
    : !signedIn
      ? { text: "Complete setup: sign in to Microsoft", to: "/notebooks" }
      : { text: "Complete setup: connect your AI tools", to: "/settings" };
  const ctaClass =
    "block w-full rounded-md bg-red-600 px-4 py-3 text-center text-base font-semibold text-white hover:bg-red-500";

  const icon = (done: boolean) =>
    done ? (
      <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
    ) : (
      <Circle className="mt-0.5 h-5 w-5 shrink-0 text-red-300" />
    );

  return (
    <div
      className="space-y-3 rounded-md border border-red-700 bg-red-950/30 p-4"
      data-testid="onboarding-banner"
    >
      {cta.to ? (
        <Link to={cta.to} data-testid="onboarding-cue" className={ctaClass}>
          {cta.text}
        </Link>
      ) : (
        <button
          type="button"
          data-testid="onboarding-cue"
          className={ctaClass}
          onClick={() =>
            guideRef.current?.scrollIntoView({ behavior: "smooth" })
          }
        >
          {cta.text}
        </button>
      )}

      <p className="text-sm text-slate-200">
        This app and its backend are running. That does <strong>not</strong>{" "}
        give Claude, Cursor or other AI tools access to your notes: three
        one-time steps are needed, and AI tools need a restart after step 3.
      </p>

      <ol className="space-y-3">
        <li
          ref={guideRef}
          className="flex items-start gap-3"
          data-testid="step-register"
        >
          {icon(configured)}
          <div className="min-w-0 flex-1 text-sm text-slate-200">
            <span className="font-medium text-white">
              1. Register your own Microsoft app
            </span>{" "}
            {configured ? (
              <span className="text-emerald-300">Done</span>
            ) : (
              <span>
                - free, about 5 minutes. Microsoft requires every user to have
                their own, so OneNote lets you in with your account.
              </span>
            )}
            {!configured && (
              <div className="mt-3 rounded border border-slate-700 bg-slate-950/60 p-3">
                <MsAppRegistration onSaved={onChanged} />
              </div>
            )}
          </div>
        </li>

        <li
          className={`flex items-start gap-3 ${configured ? "" : "opacity-60"}`}
          data-testid="step-signin"
        >
          {icon(signedIn)}
          <div className="text-sm text-slate-200">
            <span className="font-medium text-white">
              2. Sign in to your OneNote
            </span>{" "}
            {signedIn ? (
              <span className="text-emerald-300">Done</span>
            ) : configured ? (
              <>
                - approve access once in your browser.{" "}
                <Link to="/notebooks" className="underline">
                  Sign in
                </Link>
              </>
            ) : (
              <span className="text-slate-300">- after step 1</span>
            )}
          </div>
        </li>

        <li className="flex items-start gap-3" data-testid="step-ai-tools">
          {icon(toolsDone)}
          <div className="text-sm text-slate-200">
            <span className="font-medium text-white">
              3. Connect your AI tools
            </span>{" "}
            {!toolsKnown ? (
              <span className="text-slate-300">checking...</span>
            ) : toolsDone ? (
              <span className="text-emerald-300">
                Done: {registered.map((c) => c.label).join(", ")}
              </span>
            ) : found.length > 0 ? (
              <>
                - found: {found.map((c) => c.label).join(", ")}.{" "}
                <Link to="/settings" className="underline">
                  Connect
                </Link>
              </>
            ) : (
              <span className="text-slate-300">
                - no supported AI tool found on this computer (optional; the app
                works without one). Install one, then return here.
              </span>
            )}
          </div>
        </li>
      </ol>
    </div>
  );
}
