# Changelog

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
