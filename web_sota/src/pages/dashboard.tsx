import { Activity, Cpu, HardDrive, Network, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface StatusPayload {
  status?: string;
  server?: string;
  version?: string;
  uptime_seconds?: number;
  tool_count?: number;
  providers?: { graph?: { authenticated?: boolean } };
}

interface LogStats {
  total?: number;
  max_entries?: number;
}

export function Dashboard() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [logStats, setLogStats] = useState<LogStats | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    let delay = 1000;
    const poll = async () => {
      try {
        const r = await fetch("/api/status");
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const d = await r.json();
        if (!cancelled) {
          setStatus(d);
          setBackendOk(true);
          setError("");
        }
        try {
          const lr = await fetch("/api/logs/stats");
          if (lr.ok && !cancelled) setLogStats(await lr.json());
        } catch {
          /* log stats optional */
        }
        delay = 1000;
      } catch (e) {
        if (!cancelled) {
          setBackendOk(false);
          setError(e instanceof Error ? e.message : "Backend unreachable");
        }
        delay = Math.min(delay * 2, 16000);
      }
      if (!cancelled) {
        setTimeout(poll, delay);
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, []);

  const uptime = status?.uptime_seconds
    ? `${Math.floor(status.uptime_seconds / 60)}m ${status.uptime_seconds % 60}s`
    : "-";

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            OneNote MCP Dashboard
          </h2>
          <p className="text-slate-300">
            Backend status, tool surface, and activity overview
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div
            data-testid="backend-dot"
            className={`h-2.5 w-2.5 rounded-full animate-pulse ${
              backendOk === null
                ? "bg-slate-500"
                : backendOk
                  ? "bg-emerald-500"
                  : "bg-red-500"
            }`}
          />
          <span className="text-sm text-slate-300">
            {backendOk === null
              ? "Connecting..."
              : backendOk
                ? "Connected"
                : "Offline"}
          </span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Service Status
            </CardTitle>
            <Shield className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {backendOk
                ? "Online"
                : backendOk === null
                  ? "Checking"
                  : "Offline"}
            </div>
            <p className="text-sm text-slate-300">
              {error || `v${status?.version ?? "?"}`}
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              MCP Tools
            </CardTitle>
            <Cpu className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div
              className="text-2xl font-bold text-white"
              data-testid="kpi-tools"
            >
              {status?.tool_count ?? "-"}
            </div>
            <p className="text-sm text-slate-300">Registered tool surface</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Uptime
            </CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div
              className="text-2xl font-bold text-white"
              data-testid="kpi-uptime"
            >
              {uptime}
            </div>
            <p className="text-sm text-slate-300">Since last backend start</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Graph Auth
            </CardTitle>
            <Network className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {status?.providers?.graph?.authenticated
                ? "Authenticated"
                : "Not authed"}
            </div>
            <p className="text-sm text-slate-300">Microsoft account status</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Activity Log</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px] font-mono text-xs p-4 overflow-y-auto border border-slate-800 rounded-md bg-slate-900/50 text-slate-300 space-y-1">
              {logStats === null ? (
                <p className="text-slate-400">Loading activity log...</p>
              ) : (
                <p className="text-slate-300">
                  {logStats.total ?? 0} entries logged (ring buffer of{" "}
                  {logStats.max_entries ?? 2000}) - open the Logging page for
                  the full stream.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Quick Start</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center">
                <HardDrive className="h-4 w-4 text-slate-400 mr-2" />
                <div className="ml-2 space-y-1">
                  <p className="text-sm font-medium leading-none text-white">
                    Not authenticated yet?
                  </p>
                  <p className="text-sm text-slate-300">
                    Head to Settings to run the Microsoft device-code login, or
                    use the <code>authenticate</code> MCP tool.
                  </p>
                </div>
              </div>
              <div className="flex items-center">
                <Activity className="h-4 w-4 text-emerald-500 mr-2" />
                <div className="ml-2 space-y-1">
                  <p className="text-sm font-medium leading-none text-white">
                    Browse your notebooks
                  </p>
                  <p className="text-sm text-slate-300">
                    Open the Notebooks page to explore sections, pages, and
                    search across your OneNote content.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
