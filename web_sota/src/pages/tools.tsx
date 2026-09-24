import { Wrench } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

interface Capabilities {
  tools?: string[];
  features?: Record<string, boolean>;
}

export function Tools() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${API_BASE}/capabilities`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setCaps(await r.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backend unreachable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const tools = caps?.tools ?? [];
  const features = Object.entries(caps?.features ?? {}).filter(([, on]) => on);

  return (
    <div className="space-y-6" data-testid="tools-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Tool Inventory
          </h2>
          <p className="text-slate-300">
            Live MCP tool surface served by the backend
          </p>
        </div>
        <Button
          variant="outline"
          onClick={refresh}
          disabled={loading}
          data-testid="tools-retry"
          className="border-slate-800 text-slate-300 hover:bg-slate-800"
        >
          {loading ? "Refreshing..." : "Retry"}
        </Button>
      </div>

      {loading && tools.length === 0 && (
        <p className="text-sm text-slate-300" data-testid="tools-loading">
          Loading live tool inventory...
        </p>
      )}
      {error && (
        <p className="text-sm text-red-400" data-testid="tools-error">
          Backend unreachable: {error}
        </p>
      )}
      {!loading && !error && tools.length === 0 && (
        <p className="text-sm text-slate-300" data-testid="tools-empty">
          No tools reported - is the backend running?
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {tools.map((name) => (
          <Card
            key={name}
            className="border-slate-800 bg-slate-950/50"
            data-testid="tool-card"
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                {name}
              </CardTitle>
              <Wrench className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-300">
                MCP tool - callable from any connected assistant
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {features.length > 0 && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Active Capabilities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {features.map(([name]) => (
                <div
                  key={name}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-800"
                >
                  <span className="text-sm font-medium text-slate-200">
                    {name}
                  </span>
                  <span className="text-sm text-emerald-500 font-mono">
                    READY
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
