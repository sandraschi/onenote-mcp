import { Box, ExternalLink, Grid } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

interface FleetApp {
  name: string;
  port: number;
  description: string;
}

export function Apps() {
  const [apps, setApps] = useState<FleetApp[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/fleet/apps`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => {
        if (!cancelled) setApps(Array.isArray(d.apps) ? d.apps : []);
      })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "unreachable");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6" data-testid="apps-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            App Hub
          </h2>
          <p className="text-slate-300">
            Discover and navigate the fleet ecosystem
          </p>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-400" data-testid="apps-error">
          Fleet discovery unavailable: {error}
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {apps.map((app) => (
          <Card
            key={app.name}
            className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/50 transition-colors group cursor-pointer"
            onClick={() =>
              window.open(`http://localhost:${app.port}`, "_blank")
            }
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                {app.name}
              </CardTitle>
              <Box className="h-4 w-4 text-blue-500 group-hover:scale-110 transition-transform" />
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-300 mb-4">{app.description}</p>
              <div className="flex items-center text-sm text-blue-400 font-medium">
                <span>localhost:{app.port}</span>
                <ExternalLink className="h-3 w-3 ml-1" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-slate-800 bg-slate-950/50 border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-10 text-center">
          <Grid className="h-10 w-10 text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-300">
            {apps.length > 0 ? "Fleet apps loaded" : "Fleet discovery"}
          </h3>
          <p className="text-sm text-slate-400 max-w-sm">
            App list is served by the backend registry endpoint - ports are
            never hardcoded in the frontend.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
