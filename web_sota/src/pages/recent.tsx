import { FileText, History, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { fetchJson } from "@/lib/api";

interface RecentHit {
  id: string;
  title: string;
  notebook: string;
  section: string;
  modified: string;
}

function fmtDate(iso?: string) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function Recent() {
  const navigate = useNavigate();
  const [days, setDays] = useState("7");
  const [pages, setPages] = useState<RecentHit[]>([]);
  const [scanned, setScanned] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async (d: string) => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchJson<{
        success: boolean;
        pages?: RecentHit[];
        scanned?: { notebooks?: number; sections?: number };
        error?: string;
      }>(`/recent?days=${d}&limit=100`, undefined, 120_000);
      if (!data.success) throw new Error(data.error || "Failed to load");
      setPages(data.pages || []);
      const s = data.scanned;
      setScanned(
        s ? `${s.notebooks ?? 0} notebooks, ${s.sections ?? 0} sections` : "",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh("7");
  }, [refresh]);

  return (
    <div className="space-y-6" data-testid="recent-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Recent changes
          </h2>
          <p className="text-slate-300">
            What changed in your notes
            {scanned && ` — scanned ${scanned}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            data-testid="recent-days"
            aria-label="Lookback window"
            className="h-9 rounded-md border border-slate-700 bg-slate-900 px-2 text-sm text-slate-300"
            value={days}
            onChange={(e) => {
              setDays(e.target.value);
              refresh(e.target.value);
            }}
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
          </select>
          <Button
            variant="outline"
            onClick={() => refresh(days)}
            disabled={loading}
            data-testid="recent-retry"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
          >
            {loading ? "Loading..." : "Retry"}
          </Button>
        </div>
      </div>

      {loading && pages.length === 0 && (
        <p className="text-sm text-slate-300" data-testid="recent-loading">
          <Loader2 className="h-4 w-4 inline mr-2 animate-spin" />
          Walking notebooks for recent changes...
        </p>
      )}
      {error && (
        <p className="text-sm text-red-400" data-testid="recent-error">
          {error}
        </p>
      )}
      {!loading && !error && pages.length === 0 && (
        <p className="text-sm text-slate-300" data-testid="recent-empty">
          Nothing modified in the last {days} days. Quiet week.
        </p>
      )}

      {pages.length > 0 && (
        <div
          className="rounded-lg border border-slate-800 bg-slate-950/50 overflow-hidden"
          data-testid="recent-list"
        >
          <ul className="divide-y divide-slate-800/60">
            {pages.map((p) => (
              <li key={p.id}>
                <button
                  type="button"
                  className="w-full text-left px-4 py-2.5 hover:bg-slate-900/40 flex items-center justify-between gap-3"
                  onClick={() => navigate(`/notebooks?page=${p.id}`)}
                >
                  <span className="text-sm text-slate-200 truncate">
                    <History className="h-3.5 w-3.5 inline mr-1.5 text-emerald-500" />
                    {p.title || "(untitled)"}
                    <span className="text-slate-400"> · {p.notebook}</span>
                    <span className="text-slate-500"> / {p.section}</span>
                  </span>
                  <span className="text-xs text-slate-400 shrink-0 flex items-center gap-1.5">
                    <FileText className="h-3.5 w-3.5" />
                    {fmtDate(p.modified)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
