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
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
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
  const [tocWarnings, setTocWarnings] = useState<string[]>([]);
  const [selectedPage, setSelectedPage] = useState<PageDetail | null>(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const appendToPage = async () => {
    if (!selectedPage || !appendText.trim()) return;
    setAppending(true);
    setError("");
    try {
      const data = await fetchJson<{ success: boolean; error?: string }>(
        `/pages/${encodeURIComponent(selectedPage.id)}/append`,
        {
          method: "PATCH",
          body: JSON.stringify({ content: appendText }),
        },
      );
      if (!data.success) throw new Error(data.error || "Append failed");
      setAppendText("");
      setNotice("Appended - reloading the page.");
      await openPage(selectedPage.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAppending(false);
    }
  };

  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [creating, setCreating] = useState(false);
  const [appendText, setAppendText] = useState("");
  const [appending, setAppending] = useState(false);
  const [notice, setNotice] = useState("");
  const [authOk, setAuthOk] = useState<boolean | null>(null);
  const [authFlow, setAuthFlow] = useState<{
    auth_uri: string;
  } | null>(null);
  const authTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopAuthPolling = () => {
    if (authTimerRef.current) {
      clearInterval(authTimerRef.current);
      authTimerRef.current = null;
    }
  };

  const loadAuthStatus = useCallback(async () => {
    try {
      const data = await fetchJson<{ authenticated: boolean }>("/auth/status");
      setAuthOk(data.authenticated === true);
    } catch {
      setAuthOk(false);
    }
  }, []);

  useEffect(() => {
    loadAuthStatus();
  }, [loadAuthStatus]);

  // Deep link from Search results: /notebooks?page=<id> opens the page.
  useEffect(() => {
    const pageId = params.get("page");
    if (pageId) openPage(pageId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  const startAuth = async () => {
    setError("");
    // Open the tab synchronously in the click gesture: window.open after an
    // await is outside the gesture and popup blockers kill it silently.
    // NOTE: no "noopener" - with it the opener gets a neutered reference and
    // the later location assignment silently fails, stranding about:blank.
    const tab = window.open("about:blank", "_blank");
    try {
      // Browser redirect login (auth-code flow): device-code tokens are
      // rejected by the OneNote workload for personal accounts.
      const data = await fetchJson<{
        success: boolean;
        auth_uri?: string;
        error?: string;
      }>("/auth/login");
      if (!data.success || !data.auth_uri) {
        try {
          tab?.close();
        } catch {
          /* already closed */
        }
        setError(data.error || "Sign-in start failed");
        return;
      }
      setAuthFlow({ auth_uri: data.auth_uri });
      if (tab) {
        tab.location.href = data.auth_uri;
      } else {
        // Popup blocked entirely: continue in this tab. After approval,
        // return here manually - the page loads signed in.
        window.location.href = data.auth_uri;
        return;
      }
      let attempts = 0;
      authTimerRef.current = setInterval(async () => {
        attempts += 1;
        try {
          const st = await fetchJson<{ authenticated: boolean }>(
            "/auth/status",
          );
          if (st.authenticated === true) {
            stopAuthPolling();
            setAuthFlow(null);
            setAuthOk(true);
            setNotice("Connected to your Microsoft account");
            loadNotebooks();
            return;
          }
        } catch {
          /* keep polling */
        }
        if (attempts >= 200) {
          stopAuthPolling();
          setAuthFlow(null);
          setError("Sign-in timed out - try again");
        }
      }, 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

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
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      // A 401 means the stored token is dead even if /auth/status saw a
      // token file - surface the re-auth banner instead of hiding it.
      if (/401|unauthorized/i.test(msg)) setAuthOk(false);
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
    setTocWarnings([]);
    setSelectedPage(null);
    setTocLoading(true);
    setError("");
    try {
      const data = await fetchJson<{
        success: boolean;
        toc?: TocData;
        warnings?: string[];
        error?: string;
      }>(
        `/notebooks/${encodeURIComponent(notebookId)}/toc`,
        undefined,
        120_000,
      );
      if (!data.success) throw new Error(data.error || "Failed to load TOC");
      setToc(data.toc || null);
      setTocWarnings(data.warnings || []);
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

  const goSearch = () => {
    if (!query.trim()) return;
    navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  const createPage = async () => {
    if (!selectedNotebook || !newTitle.trim()) return;
    setCreating(true);
    setNotice("");
    try {
      // Plain text in, semantic HTML out: blank lines = paragraphs.
      const html = newContent
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .split(/\n{2,}/)
        .map((para) => `<p>${para.replace(/\n/g, "<br/>")}</p>`)
        .join("");
      const data = await fetchJson<{
        success: boolean;
        error?: string;
      }>("/pages", {
        method: "POST",
        body: JSON.stringify({
          notebook_id: selectedNotebook,
          title: newTitle.trim(),
          content: html,
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
          <p className="text-slate-300">
            Browse notebooks, sections, and pages via Microsoft Graph
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              data-testid="notebook-search"
              className="bg-slate-900 border border-slate-700 rounded-md pl-8 pr-2 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-64"
              placeholder="Search in pages... (Enter for full page)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && goSearch()}
            />
          </div>
          <button
            type="button"
            data-testid="notebook-create"
            className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md px-3 py-1.5 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-blue-600"
            onClick={() => setShowCreate(true)}
            disabled={!selectedNotebook || !authOk}
            title={
              !authOk
                ? "Sign in with Microsoft first"
                : !selectedNotebook
                  ? "Select a notebook first"
                  : "Create a new page"
            }
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

      {!authOk && (
        <div
          className="rounded-lg border border-amber-800 bg-amber-950/20 p-4 flex items-center justify-between gap-4"
          data-testid="auth-banner"
        >
          <div>
            <p className="text-sm text-amber-300 font-medium">
              You&apos;re not signed in
            </p>
            <p className="text-sm text-slate-300">
              Sign in with your Microsoft account to browse notebooks and pages,
              then click the blue button.
            </p>
          </div>
          {!authFlow ? (
            <button
              type="button"
              data-testid="auth-connect"
              className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md px-3 py-1.5 shrink-0"
              onClick={startAuth}
            >
              Sign in with Microsoft
            </button>
          ) : (
            <div className="text-right shrink-0 space-y-1">
              <p className="text-sm text-slate-300">
                A sign-in tab opened in your browser - approve access there,{" "}
                <a
                  href={authFlow.auth_uri}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-400 underline"
                >
                  or click here to reopen it
                </a>
                .
              </p>
              <p className="text-sm text-slate-400 flex items-center justify-end gap-1.5">
                <Loader2 className="h-3 w-3 animate-spin" /> Waiting for
                sign-in...
              </p>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-[280px_1fr] gap-4 min-h-[420px]">
        {/* Notebook + TOC tree */}
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 overflow-hidden">
          <p className="px-4 py-2 text-xs font-medium text-slate-400 border-b border-slate-800 flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5" /> Notebooks
          </p>
          {loading ? (
            <div className="p-4 flex items-center gap-2 text-slate-400 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading...
            </div>
          ) : notebooks.length === 0 ? (
            <p className="p-4 text-sm text-slate-400">
              No notebooks found. Sign in with your Microsoft account first.
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
            <div className="p-4 flex items-center gap-2 text-slate-400 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading sections...
            </div>
          )}
          {toc && !tocLoading && (
            <div className="max-h-[320px] overflow-y-auto">
              <p className="px-4 py-1.5 text-xs text-slate-400 border-t border-slate-800">
                {toc.stats.sections} sections · {toc.stats.pages} pages
              </p>
              {tocWarnings.length > 0 && (
                <p
                  data-testid="toc-warnings"
                  className="px-4 py-1.5 text-xs text-amber-300 border-t border-slate-800"
                >
                  Partial load: {tocWarnings.join(" ")} — retry to fetch the
                  rest.
                </p>
              )}
              {toc.sections.map((sec) => (
                <div key={sec.name}>
                  <p className="px-4 py-1.5 text-sm font-medium text-slate-300 flex items-center gap-1.5">
                    <FolderOpen className="h-3.5 w-3.5 text-blue-400" />
                    {sec.name}
                    <span className="text-slate-500">({sec.pageCount})</span>
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
                      <ChevronRight className="h-3 w-3 text-slate-500 shrink-0" />
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
            <div className="flex items-center justify-center h-64 gap-2 text-slate-400">
              <Loader2 className="h-5 w-5 animate-spin" /> Loading page...
            </div>
          ) : selectedPage ? (
            <div className="h-full flex flex-col">
              <div className="px-4 py-3 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white">
                  {selectedPage.title || "(untitled)"}
                </h3>
                <p className="text-sm text-slate-400">
                  Modified {fmtDate(selectedPage.lastModifiedDateTime)}
                </p>
              </div>
              <div
                data-testid="page-content"
                className="p-4 overflow-y-auto prose-invert onenote-content"
                dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
              />
              <div className="px-4 py-3 border-t border-slate-800 space-y-2">
                <textarea
                  data-testid="page-append-input"
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 h-20 resize-none"
                  value={appendText}
                  onChange={(e) => setAppendText(e.target.value)}
                  placeholder="Type to append to this note (plain text, blank lines = paragraphs)..."
                />
                <div className="flex justify-end">
                  <button
                    type="button"
                    data-testid="page-append-btn"
                    className="text-sm px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    disabled={appending || !appendText.trim()}
                    onClick={appendToPage}
                  >
                    {appending ? "Appending..." : "Append to note"}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-2">
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
                className="text-slate-400 hover:text-slate-200"
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
                Content (plain text)
              </label>
              <textarea
                data-testid="create-content"
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 h-32 resize-none"
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder={
                  "First paragraph.\n\nSecond paragraph after a blank line."
                }
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
