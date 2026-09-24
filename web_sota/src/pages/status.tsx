import { Cloud, FileText, HardDrive, Shield } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

interface StatusPayload {
  status?: string;
  version?: string;
  uptime_seconds?: number;
  tool_count?: number;
  providers?: { graph?: { authenticated?: boolean } };
}

export function Status() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${API_BASE}/status`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setStatus(await r.json());
      try {
        const ar = await fetch(`${API_BASE}/auth/status`);
        if (ar.ok) {
          const ad = (await ar.json()) as { authenticated?: boolean };
          setAuthed(ad.authenticated ?? null);
        }
      } catch {
        /* auth state optional */
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backend unreachable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const uptime =
    status?.uptime_seconds != null
      ? `${Math.floor(status.uptime_seconds / 3600)}h ${Math.floor(
          (status.uptime_seconds % 3600) / 60,
        )}m`
      : "-";

  return (
    <div className="space-y-6" data-testid="status-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Microsoft Graph Status
          </h2>
          <p className="text-slate-300">
            Live API health and synchronization telemetry
          </p>
        </div>
        <Button
          variant="outline"
          onClick={refresh}
          disabled={loading}
          data-testid="status-retry"
          className="border-slate-800 text-slate-300 hover:bg-slate-800"
        >
          {loading ? "Refreshing..." : "Retry"}
        </Button>
      </div>

      {loading && !status && (
        <p className="text-sm text-slate-300" data-testid="status-loading">
          Loading live status...
        </p>
      )}
      {error && (
        <p className="text-sm text-red-400" data-testid="status-error">
          Backend unreachable: {error}
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Auth Session
            </CardTitle>
            <Shield className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div
              className="text-2xl font-bold text-white"
              data-testid="status-auth"
            >
              {authed === null ? "-" : authed ? "ACTIVE" : "SIGNED OUT"}
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Backend
            </CardTitle>
            <Cloud className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div
              className="text-2xl font-bold text-white"
              data-testid="status-backend"
            >
              {status ? `v${status.version ?? "?"}` : "-"}
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              MCP Tools
            </CardTitle>
            <FileText className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div
              className="text-2xl font-bold text-white"
              data-testid="status-tools"
            >
              {status?.tool_count ?? "-"}
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">
              Uptime
            </CardTitle>
            <HardDrive className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div
              className="text-2xl font-bold text-white"
              data-testid="status-uptime"
            >
              {uptime}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
