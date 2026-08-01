# Changelog

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
