# Changelog

## [Unreleased]

### Assfix 2026-09-25 (66 -> ~85, SOTA)
- `data/` + `*.sqlite3` + `.coverage` gitignored (index DB must never commit).
- Session-context tool counts 13 -> 15 (second drift in 2 days).
- README mirror re-synced (mcp-central-docs project page).
- Deferred (documented): Inbox page, output_schema, dialogic retype;
  ghaudit stale, thin coverage, no shortcuts.

### Added
- Append-to-note: `onenote_append_page` tool + `PATCH /api/pages/{id}/append`
  (plain text in, Graph PATCH commands) + viewer append box with reload.
  16 tools total.
- Local full-text search: SQLite FTS5 index over page bodies
  (`src/onenote_mcp/search_index.py`, incremental, stopword-safe quoting),
  `onenote_index_start|status` tools, `POST /api/index` +
  `GET /api/index/status`, `mode=fulltext` on search (tool + REST + UI with
  snippet rows, index button + progress). 15 tools total.
- Browser auth-code sign-in (`GET /api/auth/login` + `/api/auth/callback`,
  Notebooks blue button) - device-flow tokens are rejected by the OneNote
  workload for personal accounts; the browser flow yields working tokens.
- `GET /api/auth/debug` (client suffix, authority, scopes, token shape/age,
  JWT claims - no secrets) + auth events in the activity log + real MSAL
  error text surfaced in UI.
- `GET /api/llm/providers|models|onboarding`, `POST /api/llm/chat` proxy;
  Skills page; `onenote_triage` prompt; Zustand `store/llm.ts`.
- `docs/ARCHITECTURE.md` (components, auth chain, scope recipe, Graph
  quirks); `docs/AUTH_INVESTIGATION.md` (401-odyssey record + resolution).

### Changed (auth - the winning recipe)
- Scopes: fully-qualified base form
  (`https://graph.microsoft.com/Notes.Read|Notes.ReadWrite|User.Read`) -
  bare `.All` scopes minted OneNote-rejected tokens for personal accounts.
- Multi-tenant personal-capable app + `/common` authority (personal-only +
  `/consumers` also minted rejects); `ONENOTE_CLIENT_ID`/`ONENOTE_AUTHORITY`/
  `ONENOTE_REDIRECT_URI` env (repo-root `.env` loaded at startup).
- Silent-refresh-first load order + MSAL cache (`.msal-token-cache.bin`,
  gitignored): hourly expiry and backend restarts self-heal, no clicks.
- Sign-in vocabulary unified ("Sign in" everywhere); New-page button
  disabled + dimmed until signed in.

### Fixed
- Launcher `UvicornTarget :app` regression (500s) - restored `:http_app`.
- Cached Graph client surviving re-auth (eternal 401s); MSAL deprecated-API
  crash in callback ("Invalid parameter type"); reserved-scope 500 in
  `/api/auth/login` (MSAL injects `offline_access` itself).
- `get_page` stuffed metadata JSON into content - now fetches `.../content`.
- Search: TOC-walk title match (collection queries refused with 20266 on
  section-heavy accounts); results carry notebook/section; UI has notebook
  filter, sort, 25/page pagination, CSV export.
- Big-notebook timeouts: parallel section fetch (4-at-a-time), 30s Graph
  client timeout, partial TOC with warning count, longer UI budgets.
- Page viewer anchors absolute OneNote layout (was escaping left).
- New-page dialog takes plain text (paragraphs from blank lines).
- Status/Tools un-mocked (live endpoints); Tauri `/api` base; Logging
  double-prefix; Chat via backend proxy; dead Settings buttons wired/removed.
- Frozen exe `jaraco.text` startup crash (spec hiddenimports + BUILD_LOG).

### Docs
- `docs/AUTH_INVESTIGATION.md`: full 2026-09-24 401-odyssey record (evidence,
  killed theories, request IDs, ranked plan, PnP verdict) + resolution.

## [1.0.3] - 2026-09-24 (assfix)

### Fixed
- Launcher failure: worktree `fleet-start.config.ps1` had regressed
  `UvicornTarget` to the raw FastMCP `server:app` (every route 500'd);
  restored to `server:http_app`, `WebRoot` made relative. Verified
  backend+frontend 200 via the real `web_sota/start.ps1` path.
- Tauri desktop app called all APIs at the wrong base (`...:10907/status`
  instead of `.../api/status`); `API_BASE` now appends `/api` under Tauri.
- Logging page used a double `/api/api/logs*` prefix (404 in dev and Tauri).
- Status/Tools pages showed hardcoded mock data (ACTIVE/12/45MB, fictional
  `onenote_sync`); both now render live `/api/status` + `/api/capabilities`.
- Chat called Ollama directly from the browser; now goes through the backend
  proxy. Settings dead buttons (Test Connection, Save Parameters) wired/removed.
- Wrong callable names in `onenote_help` + tool examples (`save_access_token`,
  `list_notebooks`, ...); corrected to the real `onenote_*` names.
- CUA smoke config pointed at non-existent `/api/v1/system/info`; now
  `/api/status`, with real `nav_routes` for the sidebar walk.

### Added
- Backend LLM surface: `POST /api/llm/chat` proxy (Ollama + OpenAI-compatible
  LM Studio/vLLM), `GET /api/llm/providers`, `/api/llm/models`,
  `/api/llm/onboarding`. Chat + Settings share a Zustand `store/llm.ts`.
- Skills page (`/skills`) backed by `/api/skills`; sidebar + App routes.
- `@app.prompt()` `onenote_triage` guided-triage prompt.
- `renovate.json`, `.agents/skills/` session-context skill.

### Changed
- Ruff: `T20` enforced, `S110`/`S112` un-ignored (with scoped per-file-ignores
  for CLI/demo/test/CUA scripts); `ruff check .` + format now fully green.
- Justfile lone `Set-Location` lines joined (Windows per-line shell pitfall).
- Root `start.ps1` collapsed to a thin delegate of `web_sota/start.ps1`.

## [1.0.1] - 2026-08-01 (assfix follow-up)

### Fixed
- Settings page LLM section called non-existent `/api/llm/providers` and fell back
  to a hardcoded `llama3.2:3b` mock; rewired to the real `/api/llm/discover` with a
  graceful "no local LLM detected" state and no fake model data.
- Hardcoded/hallucinated ports in the frontend: `settings.tsx` (`107xx` placeholder),
  `help.tsx` (10894/10895), `apps.tsx` (static catalog with wrong ports). Apps Hub now
  fetches the backend `/api/fleet/apps` registry endpoint.
- Tauri NSIS production bug: `lib/api.ts` + `dashboard.tsx` used relative `/api`, which
  works under the Vite proxy but fails in the built WebView. API_BASE now resolves to
  `http://127.0.0.1:10907` inside Tauri.
- pyright gate: `Response` return in `/api/logs/export` (typed ignore with code);
  pyright added to dev deps and as a blocking CI step.
- `print()` in non-test code converted to `logger` calls; phantom `fastapi` dependency
  removed (FastMCP custom routes are Starlette-based).
- justfile mojibake box-drawing comments replaced with ASCII; README badges refreshed
  (Python 3.12+, FastMCP 3.4).

### Added
- `docs/`: CONFIGURATION, DEVELOPMENT, TOOLS, TROUBLESHOOTING, ONBOARDING.
- Tool annotations (`READ_ONLY`/`MUTATING`/DESTRUCTIVE) on all 13 tools.
- `show_notebooks_card` — Prefab UI in-chat card (13th tool).
- `skills/onenote/SKILL.md` + `skill://onenote` MCP resource + `GET /api/skills/{name}`.
- Chat page is now skill-first: loads the skill content on mount and composes it with
  the personality prompt.
- `/api/llm/discover` probes LM Studio (:1234) and vLLM (:8000) in addition to Ollama,
  returning per-provider model lists.
- Dashboard listens for the Tauri `backend-status` event and adds a Restart Backend
  button when the backend is offline.
- `backend.rs`: multi-layer port kill (Stop-Process -> taskkill -> UAC -> 240s poll)
  and a TCP health-check loop that emits `backend-status`.
- `data-testid` on settings/status/tools/help/apps/logging pages; contrast fixes
  (`text-slate-400/500` -> `slate-300`, `text-xs` -> `text-sm`).

## [1.0.0] - 2026-08-01

### Fixed
- ASGI crash (`TypeError: 'FastMCP' object is not callable`): uvicorn target now
  `onenote_mcp.server:http_app` (CORS-wrapped `app.http_app()`), fixed in
  `fleet-start.config.ps1`, `transport.py` (uvicorn.Server instead of `run_http_async`),
  and `run_server.py` (CORS on the FastAPI shell).
- Critical packaging leak: `tauri.conf.json` + `native/build.ps1` bundled the real `.env`;
  now bundle `.env.example` template only.
- Tracked junk removed from git: `*.pyc` and `*.bak` dross (41 files untracked), patterns
  added to `.gitignore`.

### Added
- REST surface: `/api/status`, `/api/capabilities`, `/api/v1/diagnostics`, `/api/skills`,
  `/api/llm/discover`, `/api/shutdown`.
- MCP tools: `onenote_help`, `shutdown_server`; all tools renamed to verb-led `onenote_*`
  snake_case with SOTA docstrings (`## Return Format`, `## Examples`, `Annotated`+`Field`).
- `.env.example`, `llms.txt`, `llms-full.txt`, `CLAUDE.md`, session-context injection
  (`.claude-plugin`, `.cursorrules` update, `.windsurfrules`, Copilot instructions,
  OpenCode skill).
- Webapp: real backend-backed dashboard (live KPIs, backoff polling, `data-testid`),
  `useZoom` hook (Ctrl+Scroll zoom + Ctrl+0 reset, `tauri-zoom` persistence),
  `@tauri-apps/api` dependency.
- justfile: `serve`, `test`, `fmt`, `e2e`, `build-native`, `gates-green` recipes.
- Coverage threshold in pytest config; Playwright e2e scaffold.

### Changed
- `glama.json` refreshed (FastMCP 3.4+, HTTP+stdio transport, 12 tools).
- `start.ps1` clears zombie ports and polls backend readiness.

## [0.x] - 2026-07

- Webapp notebooks browser, activity log API, non-blocking device-code auth UI (2026-07-31)
- Inline CI (Windows, Node 22) replacing reusable workflow (2026-07-31)
