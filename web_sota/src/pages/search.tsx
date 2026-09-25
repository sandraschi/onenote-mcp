import { FileText, Loader2, Search, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { fetchJson } from "@/lib/api";

interface SearchHit {
  id: string;
  title: string;
  createdDateTime: string;
  lastModifiedDateTime: string;
  notebook?: string;
  section?: string;
  snippet?: string;
}

interface IndexState {
  state: string;
  total: number;
  done: number;
  indexed_pages: number;
}

const PAGE_SIZE = 25;

function fmtDate(iso?: string) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function SearchPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState(params.get("q") || "");
  const [mode, setMode] = useState<"title" | "fulltext">("title");
  const [results, setResults] = useState<SearchHit[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [notebook, setNotebook] = useState("");
  const [sort, setSort] = useState<"modified" | "created" | "title">(
    "modified",
  );
  const [page, setPage] = useState(0);
  const [index, setIndex] = useState<IndexState | null>(null);

  const runSearch = useCallback(async (q: string, m: "title" | "fulltext") => {
    if (!q.trim()) {
      setResults(null);
      return;
    }
    setSearching(true);
    setError("");
    setNotice("");
    setPage(0);
    try {
      const data = await fetchJson<{
        success: boolean;
        pages?: SearchHit[];
        warning?: string;
        error?: string;
      }>(
        `/search?q=${encodeURIComponent(q.trim())}&mode=${m}`,
        undefined,
        180_000,
      );
      if (!data.success) throw new Error(data.error || "Search failed");
      setResults(data.pages || []);
      if (data.warning) setNotice(data.warning);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    const q = params.get("q") || "";
    setQuery(q);
    if (q.trim()) runSearch(q, "title");
    refreshIndex();
  }, [params, runSearch]);

  const refreshIndex = async () => {
    try {
      const data = await fetchJson<IndexState & { success: boolean }>(
        "/index/status",
      );
      if (data.success) {
        setIndex({
          state: data.state,
          total: data.total,
          done: data.done,
          indexed_pages: data.indexed_pages,
        });
        return data.state;
      }
    } catch {
      /* backend unreachable */
    }
    return "";
  };

  const startBuild = async () => {
    setError("");
    try {
      const data = await fetchJson<{ success: boolean; error?: string }>(
        "/index",
        { method: "POST" },
      );
      if (!data.success) throw new Error(data.error || "Index start failed");
      await refreshIndex();
      const timer = setInterval(async () => {
        const state = await refreshIndex();
        if (state !== "running") clearInterval(timer);
      }, 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const visible = (results || [])
    .filter((p) => !notebook || p.notebook === notebook)
    .sort((a, b) => {
      if (sort === "title") return (a.title || "").localeCompare(b.title || "");
      const key =
        sort === "created" ? "createdDateTime" : "lastModifiedDateTime";
      return new Date(b[key] || 0).getTime() - new Date(a[key] || 0).getTime();
    });
  const pageCount = Math.max(1, Math.ceil(visible.length / PAGE_SIZE));
  const pageItems = visible.slice(
    page * PAGE_SIZE,
    page * PAGE_SIZE + PAGE_SIZE,
  );
  const notebooks = [
    ...new Set((results || []).map((p) => p.notebook).filter(Boolean)),
  ];

  const exportCsv = () => {
    const esc = (v?: string) => `"${(v || "").replace(/"/g, '""')}"`;
    const csv = [
      "title,notebook,section,created,modified",
      ...visible.map((p) =>
        [
          esc(p.title),
          esc(p.notebook),
          esc(p.section),
          esc(p.createdDateTime),
          esc(p.lastModifiedDateTime),
        ].join(","),
      ),
    ].join("\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `onenote-search-${query.trim() || "results"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6" data-testid="search-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Search notes
        </h2>
        <p className="text-slate-300">
          Titles instantly, or build the index once and search inside every
          note.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-64">
          {searching ? (
            <Loader2 className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 animate-spin" />
          ) : (
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          )}
          <input
            data-testid="search-input"
            className="w-full bg-slate-900 border border-slate-700 rounded-md pl-8 pr-2 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="Search in pages..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runSearch(query, mode)}
          />
        </div>
        <select
          data-testid="search-mode"
          aria-label="Search mode"
          title="Title matches page titles; Full text searches note bodies (needs the index)"
          className="h-9 rounded-md border border-slate-700 bg-slate-900 px-2 text-sm text-slate-300"
          value={mode}
          onChange={(e) => setMode(e.target.value as "title" | "fulltext")}
        >
          <option value="title">Title</option>
          <option value="fulltext">Full text</option>
        </select>
        <Button
          data-testid="search-button"
          onClick={() => runSearch(query, mode)}
          disabled={searching || !query.trim()}
        >
          {searching ? "Searching..." : "Search"}
        </Button>
      </div>

      {mode === "fulltext" && (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-2">
          <Button
            data-testid="index-build"
            variant="outline"
            size="sm"
            className="border-slate-800 text-slate-300 hover:bg-slate-800"
            disabled={index?.state === "running"}
            onClick={startBuild}
          >
            {index?.state === "running"
              ? `Indexing ${index.done}/${index.total}...`
              : "Build full-text index"}
          </Button>
          {index && (
            <span data-testid="index-status" className="text-sm text-slate-400">
              {index.state === "running"
                ? `Indexing ${index.done} of ${index.total} pages...`
                : `${index.indexed_pages} pages indexed`}
            </span>
          )}
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400" data-testid="search-error">
          {error}
        </p>
      )}
      {notice && (
        <p className="text-sm text-amber-300" data-testid="search-notice">
          {notice}
        </p>
      )}

      {results && (
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 overflow-hidden">
          <div className="flex flex-wrap items-center gap-2 px-4 py-2 border-b border-slate-800">
            <p className="text-sm text-slate-300 mr-auto">
              {visible.length} result{visible.length !== 1 ? "s" : ""}
              {query && ` for "${query}"`}
            </p>
            <select
              data-testid="search-notebook-filter"
              aria-label="Filter by notebook"
              className="h-8 rounded border border-slate-700 bg-slate-800 px-2 text-sm text-slate-300"
              value={notebook}
              onChange={(e) => {
                setNotebook(e.target.value);
                setPage(0);
              }}
            >
              <option value="">All notebooks</option>
              {notebooks.map((nb) => (
                <option key={nb} value={nb}>
                  {nb}
                </option>
              ))}
            </select>
            <select
              data-testid="search-sort"
              aria-label="Sort results"
              className="h-8 rounded border border-slate-700 bg-slate-800 px-2 text-sm text-slate-300"
              value={sort}
              onChange={(e) => {
                setSort(e.target.value as "modified" | "created" | "title");
                setPage(0);
              }}
            >
              <option value="modified">Recently modified</option>
              <option value="created">Recently created</option>
              <option value="title">Title A-Z</option>
            </select>
            <button
              type="button"
              data-testid="search-export"
              title="Export filtered results as CSV"
              className="h-8 rounded border border-slate-700 px-2 text-sm text-slate-300 hover:bg-slate-800"
              onClick={exportCsv}
            >
              Export
            </button>
            <button
              type="button"
              aria-label="Clear search"
              className="text-slate-400 hover:text-slate-200"
              onClick={() => {
                setResults(null);
                setQuery("");
                setNotebook("");
                setPage(0);
                navigate("/search", { replace: true });
              }}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          {visible.length === 0 ? (
            <p
              className="p-4 text-sm text-slate-400"
              data-testid="search-empty"
            >
              No matching pages.
            </p>
          ) : (
            <>
              <ul className="divide-y divide-slate-800/60">
                {pageItems.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      className="w-full text-left px-4 py-2.5 hover:bg-slate-900/40 flex items-center justify-between gap-3"
                      onClick={() => navigate(`/notebooks?page=${p.id}`)}
                    >
                      <div className="flex-1 min-w-0">
                        <span className="block text-sm text-slate-200 truncate">
                          <FileText className="h-3.5 w-3.5 inline mr-1.5 text-blue-400" />
                          {p.title || "(untitled)"}
                          {p.notebook && (
                            <span className="text-slate-400">
                              {" "}
                              · {p.notebook}
                            </span>
                          )}
                          {p.section && (
                            <span className="text-slate-500">
                              {" "}
                              / {p.section}
                            </span>
                          )}
                        </span>
                        {p.snippet && (
                          <span className="block text-sm text-slate-400 truncate">
                            …{p.snippet}…
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-slate-400 shrink-0">
                        {fmtDate(p.lastModifiedDateTime)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
              {visible.length > PAGE_SIZE && (
                <div className="flex items-center justify-between px-4 py-2 border-t border-slate-800">
                  <button
                    type="button"
                    data-testid="search-prev"
                    className="h-8 rounded border border-slate-700 px-3 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                    disabled={page === 0}
                    onClick={() => setPage((n) => Math.max(0, n - 1))}
                  >
                    Prev
                  </button>
                  <p
                    data-testid="search-page-info"
                    className="text-sm text-slate-400"
                  >
                    Page {page + 1} of {pageCount}
                  </p>
                  <button
                    type="button"
                    data-testid="search-next"
                    className="h-8 rounded border border-slate-700 px-3 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                    disabled={(page + 1) * PAGE_SIZE >= visible.length}
                    onClick={() => setPage((n) => n + 1)}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
