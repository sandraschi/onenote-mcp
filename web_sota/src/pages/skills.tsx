import { BookOpen } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

interface Skill {
  name: string;
  uri: string;
}

export function Skills() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [active, setActive] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await fetch(`${API_BASE}/skills`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = (await r.json()) as { skills?: Skill[] };
      setSkills(d.skills ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Backend unreachable");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const open = async (name: string) => {
    setActive(name);
    setContent("");
    try {
      const r = await fetch(`${API_BASE}/skills/${name}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = (await r.json()) as { content?: string };
      setContent(d.content ?? "");
    } catch (e) {
      setContent(e instanceof Error ? `Failed: ${e.message}` : "Failed");
    }
  };

  return (
    <div className="space-y-6" data-testid="skills-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Skills
          </h2>
          <p className="text-slate-300">
            Agent skill packs served by the backend
          </p>
        </div>
        <Button
          variant="outline"
          onClick={refresh}
          disabled={loading}
          data-testid="skills-retry"
          className="border-slate-800 text-slate-300 hover:bg-slate-800"
        >
          {loading ? "Refreshing..." : "Retry"}
        </Button>
      </div>

      {loading && skills.length === 0 && (
        <p className="text-sm text-slate-300" data-testid="skills-loading">
          Loading skills...
        </p>
      )}
      {error && (
        <p className="text-sm text-red-400" data-testid="skills-error">
          Backend unreachable: {error}
        </p>
      )}
      {!loading && !error && skills.length === 0 && (
        <p className="text-sm text-slate-300" data-testid="skills-empty">
          No skills published by this server.
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {skills.map((s) => (
          <Card
            key={s.name}
            className="border-slate-800 bg-slate-950/50"
            data-testid="skill-card"
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                {s.name}
              </CardTitle>
              <BookOpen className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm text-slate-300 font-mono">{s.uri}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => open(s.name)}
                data-testid="skill-open"
                className="border-slate-800 text-slate-300 hover:bg-slate-800"
              >
                {active === s.name ? "Reload" : "View"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {active && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white font-mono text-sm">
              {active}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre
              className="p-3 bg-slate-900 rounded border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap max-h-96 overflow-y-auto"
              data-testid="skill-content"
            >
              {content || "Loading..."}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
