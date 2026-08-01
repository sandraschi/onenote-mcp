import DOMPurify from "dompurify";
import {
  BookOpen,
  ChevronRight,
  FileText,
  FolderOpen,
  Loader2,
  NotebookPen,
  Plus,
  Search,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { fetchJson } from "@/lib/api";

type Notebook = {
  id: string;
  displayName: string;
};

type TocPage = { title: string; id: string; created: string; modified: string };
type TocSection = { name: string; pageCount: number; pages: TocPage[] };
type TocData = {
  notebook: string;
  stats: { sections: number; pages: number };
  sections: TocSection[];
};

type PageDetail = {
  id: string;
  title: string;
  createdDateTime: string;
  lastModifiedDateTime: string;
  content?: string;
};

type SearchResult = {
  id: string;
  title: string;
  createdDateTime: string;
  lastModifiedDateTime: string;
};

function fmtDate(iso?: string): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function Notebooks() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedNotebook, setSelectedNotebook] = useState<string | null>(null);
  const [toc, setToc] = useState<TocData | null>(null);
  const [tocLoading, setTocLoading] = useState(false);
  const [selectedPage, setSelectedPage] = useState<PageDetail | null>(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(
    null,
  );
  const [searching, setSearching] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [creating, setCreating] = useState(false);
  const [notice, setNotice] = useState("");

  const loadNotebooks = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchJson<{
        success: boolean;
        notebooks?: Notebook[];
        error?: string;
      }>("/notebooks");
      if (!data.success)
        throw new Error(data.error || "Failed to load notebooks");
      setNotebooks(data.notebooks || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNotebooks();
  }, [loadNotebooks]);

  const loadToc = async (notebookId: string) => {
    setSelectedNotebook(notebookId);
    setToc(null);
    setSelectedPage(null);
    setTocLoading(true);
    setError("");
    try {
      const data = await fetchJson<{
        success: boolean;
        toc?: TocData;
        error?: string;
      }>(`/notebooks/${encodeURIComponent(notebookId)}/toc`);
      if (!data.success) throw new Error(data.error || "Failed to load TOC");
      setToc(data.toc || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setTocLoading(false);
    }
  };

  const openPage = async (pageId: string) => {
    setSelectedPage(null);
    setPageLoading(true);
    setError("");
    try {
      const data = await fetchJson<{
        success: boolean;
        page?: PageDetail;
        error?: string;
      }>(`/pages/${encodeURIComponent(pageId)}`);
      if (!data.success) throw new Error(data.error || "Failed to load page");
      setSelectedPage(data.page || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPageLoading(false);
    }
  };

  const runSearch = async () => {
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    setError("");
    try {
      const data = await fetchJson<{
        success: boolean;
        pages?: SearchResult[];
        error?: string;
      }>(`/search?q=${encodeURIComponent(query.trim())}`);
      if (!data.success) throw new Error(data.error || "Search failed");
      setSearchResults(data.pages || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSearching(false);
    }
  };

  const createPage = async () => {
    if (!selectedNotebook || !newTitle.trim()) return;
    setCreating(true);
    setNotice("");
    try {
      const data = await fetchJson<{
        success: boolean;
        error?: string;
      }>("/pages", {
        method: "POST",
        body: JSON.stringify({
          notebook_id: selectedNotebook,
          title: newTitle.trim(),
          content: newContent,
        }),
      });
      if (!data.success) throw new Error(data.error || "Create failed");
      setShowCreate(false);
      setNewTitle("");
      setNewContent("");
      setNotice(
        `Page created — check the notebook TOC (may take a moment to appear).`,
      );
      loadToc(selectedNotebook);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  };

  const sanitizedHtml = selectedPage?.content
    ? DOMPurify.sanitize(selectedPage.content, {
        USE_PROFILES: { html: true },
      })
    : "";

  return (
    <div className="space-y-6" data-testid="notebooks-page">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            OneNote Notebooks
          </h2>
          <p className="text-slate-400">
            Browse notebooks, sections, and pages via Microsoft Graph
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            {searching ? (
              <Loader2 className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 animate-spin" />
            ) : (
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            )}
            <input
              data-testid="notebook-search"
              className="bg-slate-900 border border-slate-700 rounded-md pl-8 pr-2 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-64"
              placeholder="Search pages..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
            />
          </div>
          <button
            type="button"
            data-testid="notebook-create"
            className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md px-3 py-1.5"
            onClick={() => setShowCreate(true)}
            disabled={!selectedNotebook}
          >
            <Plus className="h-4 w-4" /> New page
          </button>
        </div>
      </div>

      {notice && (
        <p className="text-sm text-emerald-400 bg-emerald-950/30 border border-emerald-900 rounded px-3 py-2">
          {notice}
        </p>
      )}
      {error && (
        <p className="text-sm text-red-400 bg-red-950/30 border border-red-900 rounded px-3 py-2">
          {error}
        </p>
      )}

      {searchResults && (
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800">
            <p className="text-sm text-slate-300">
              {searchResults.length} result
              {searchResults.length !== 1 ? "s" : ""} for "{query}"
            </p>
            <button
              type="button"
              className="text-slate-500 hover:text-slate-300"
              onClick={() => {
                setSearchResults(null);
                setQuery("");
              }}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          {searchResults.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">No matching pages.</p>
          ) : (
            <ul className="divide-y divide-slate-800/60">
              {searchResults.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    className="w-full text-left px-4 py-2.5 hover:bg-slate-900/40 flex items-center justify-between gap-3"
                    onClick={() => openPage(p.id)}
                  >
                    <span className="text-sm text-slate-200 truncate">
                      <FileText className="h-3.5 w-3.5 inline mr-1.5 text-blue-400" />
                      {p.title || "(untitled)"}
                    </span>
                    <span className="text-xs text-slate-500 shrink-0">
                      {fmtDate(p.lastModifiedDateTime)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="grid grid-cols-[280px_1fr] gap-4 min-h-[420px]">
        {/* Notebook + TOC tree */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 overflow-hidden">
          <p className="px-4 py-2 text-xs font-medium text-slate-500 border-b border-slate-800 flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5" /> Notebooks
          </p>
          {loading ? (
            <div className="p-4 flex items-center gap-2 text-slate-500 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading...
            </div>
          ) : notebooks.length === 0 ? (
            <p className="p-4 text-sm text-slate-500">
              No notebooks found. Connect your Microsoft account first.
            </p>
          ) : (
            <ul className="divide-y divide-slate-800/60 max-h-[300px] overflow-y-auto">
              {notebooks.map((nb) => (
                <li key={nb.id}>
                  <button
                    type="button"
                    data-testid={`notebook-${nb.displayName}`}
                    className={`w-full text-left px-4 py-2.5 flex items-center gap-2 text-sm hover:bg-slate-900/40 ${
                      selectedNotebook === nb.id
                        ? "bg-blue-950/30 text-white"
                        : "text-slate-300"
                    }`}
                    onClick={() => loadToc(nb.id)}
                  >
                    <NotebookPen className="h-4 w-4 text-amber-400 shrink-0" />
                    <span className="truncate">{nb.displayName}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {tocLoading && (
            <div className="p-4 flex items-center gap-2 text-slate-500 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading sections...
            </div>
          )}
          {toc && !tocLoading && (
            <div className="max-h-[320px] overflow-y-auto">
              <p className="px-4 py-1.5 text-xs text-slate-500 border-t border-slate-800">
                {toc.stats.sections} sections · {toc.stats.pages} pages
              </p>
              {toc.sections.map((sec) => (
                <div key={sec.name}>
                  <p className="px-4 py-1.5 text-xs font-medium text-slate-400 flex items-center gap-1.5">
                    <FolderOpen className="h-3.5 w-3.5 text-blue-400" />
                    {sec.name}
                    <span className="text-slate-600">({sec.pageCount})</span>
                  </p>
                  {sec.pages.map((pg) => (
                    <button
                      type="button"
                      key={pg.id}
                      data-testid={`page-${pg.title}`}
                      className={`w-full text-left pl-8 pr-3 py-1.5 text-sm flex items-center gap-1.5 hover:bg-slate-900/40 ${
                        selectedPage?.id === pg.id
                          ? "text-blue-300"
                          : "text-slate-300"
                      }`}
                      onClick={() => openPage(pg.id)}
                    >
                      <ChevronRight className="h-3 w-3 text-slate-600 shrink-0" />
                      <span className="truncate">
                        {pg.title || "(untitled)"}
                      </span>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Page viewer */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 overflow-hidden">
          {pageLoading ? (
            <div className="flex items-center justify-center h-64 gap-2 text-slate-500">
              <Loader2 className="h-5 w-5 animate-spin" /> Loading page...
            </div>
          ) : selectedPage ? (
            <div className="h-full flex flex-col">
              <div className="px-4 py-3 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white">
                  {selectedPage.title || "(untitled)"}
                </h3>
                <p className="text-xs text-slate-500">
                  Modified {fmtDate(selectedPage.lastModifiedDateTime)}
                </p>
              </div>
              <div
                data-testid="page-content"
                className="p-4 overflow-y-auto prose-invert onenote-content"
                // biome-ignore lint/security/noDangerouslySetInnerHtml: page HTML is DOMPurify-sanitized
                dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-slate-600 gap-2">
              <FileText className="h-8 w-8" />
              <p className="text-sm">Select a page to view it</p>
            </div>
          )}
        </div>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div
            className="bg-slate-900 border border-slate-700 rounded-lg w-full max-w-lg p-5 space-y-4"
            data-testid="create-page-dialog"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-white font-semibold">New page</h3>
              <button
                type="button"
                className="text-slate-500 hover:text-slate-300"
                onClick={() => setShowCreate(false)}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-2">
              <label className="block text-sm text-slate-300">Title *</label>
              <input
                data-testid="create-title"
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Page title"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm text-slate-300">
                Content (HTML)
              </label>
              <textarea
                data-testid="create-content"
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 h-32 resize-none"
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="<p>Write something...</p>"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="text-sm px-3 py-1.5 rounded border border-slate-700 text-slate-300 hover:bg-slate-800"
                onClick={() => setShowCreate(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                data-testid="create-submit"
                className="text-sm px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
                disabled={creating || !newTitle.trim()}
                onClick={createPage}
              >
                {creating ? "Creating..." : "Create page"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
