# onenote-mcp — Agent Guide

FastMCP 3.4 server for Microsoft OneNote via the Microsoft Graph API.

## Quick Ref

- Backend: `uv run python -m onenote_mcp` (stdio default; `--http` for streamable HTTP)
- Backend port (HTTP/uvicorn): 10907 — ASGI target `onenote_mcp.server:http_app`
- Webapp: `cd web_sota && npm run dev` (port 10906)
- Tests: `uv run pytest tests/ -q`
- Lint: `just lint` / `just fix` (ruff + biome)

## Standards

- MCP tools are verb-led snake_case `onenote_*` with SOTA docstrings
  (`## Return Format`, `## Examples`, `Annotated[T, Field(...)]` — no `Args:` blocks)
- REST endpoints via `@app.custom_route` on the FastMCP app
- Never pass the raw FastMCP object to uvicorn — always `http_app`/`app.http_app()`
- CORS per `mcp-central-docs/standards/CORS_STANDARD.md` (tauri://localhost + Tailscale regex)

## Key Files

| File | Purpose |
|------|---------|
| `src/onenote_mcp/server.py` | FastMCP app, tools, REST routes, `http_app` export |
| `src/onenote_mcp/transport.py` | stdio/http/sse runner (uvicorn.Server on http_app) |
| `src/onenote_mcp/activity_log.py` | Ring-buffer log for the Logging page |
| `src/onenote_mcp/models.py` | Pydantic v2 models (Notebook, Page, Section, TOC) |
| `run_server.py` | PyInstaller entry (FastAPI shell + CORS + `/mcp` mount) |
| `web_sota/` | Vite React webapp (dashboard, notebooks, chat, logging) |
| `native/` | Tauri 2 wrapper (NSIS installer, embedded backend) |
| `fleet-start.config.ps1` | Fleet launcher config (ports + uvicorn target) |

## Session Context

You have access to OneNote notebooks via Microsoft Graph (12 tools).
Before starting work on notes: `onenote_list_notebooks()` to find the notebook,
then `onenote_get_notebook_toc()` for structure.
At end of work: `onenote_create_page()` to persist notes; `onenote_save_access_token()`
if auth is missing.
