# onenote-mcp — Architecture

Fleet Standard MCP server: FastMCP 3.4 backend (stdio + streamable HTTP),
Vite+React webapp (`web_sota/`, port 10906), Tauri desktop shell (`native/`),
MCPB bundle (`mcpb/`). Ports 10906/10907 registered adjacent, never hardcoded
(fleet config + `API_BASE`).

## Components

| Piece | Location | Role |
|---|---|---|
| MCP + REST backend | `src/onenote_mcp/server.py` | 13 tools, 1 prompt (`onenote_triage`), `skill://onenote` resource, `/api/*` REST via `custom_route` |
| ASGI target | `http_app` in `server.py` | CORS-wrapped `app.http_app()` — the ONLY uvicorn target (raw `app` 500s everything) |
| CLI transports | `src/onenote_mcp/transport.py` | stdio/http/sse for `python -m onenote_mcp` |
| Frozen entry | `run_server.py` + `onenote-mcp-backend.spec` | PyInstaller sidecar for Tauri |
| Webapp | `web_sota/src` (React, Zustand `store/llm.ts`, TanStack Query) | Dashboard, Notebooks, Recent, Search, Tools, Status, Apps, Skills, Chat (backend LLM proxy; pages groundable via `context_ids`), Logging, Help, Settings |
| Desktop shell | `native/` (Rust + `backend.rs`) | Spawns backend exe, relays `backend-status`, health-polls |
| Logging | `src/onenote_mcp/activity_log.py` | In-memory ring (2000), `/api/logs`, kind-filtered (`auth`, `http`, …) |

## Auth chain (read this before touching auth)

OneNote data flows only with a user-delegated Graph token the OneNote
workload accepts. Getting one has four cooperating parts:

1. **App registration (hers, one time).** Multi-tenant + personal
   ("Any Entra ID tenant + personal Microsoft accounts"), delegated
   `Notes.Read.All` + `Notes.ReadWrite.All` + `User.Read`, public-client
   flows ON, `http://localhost` (+ exact callback) under Mobile and desktop.
   See `docs/ONBOARDING.md` for the click path.
2. **Environment.** `ONENOTE_CLIENT_ID` (default: Graph Explorer public
   client), `ONENOTE_AUTHORITY` (`/common` for multi-tenant apps,
   `/consumers` for personal-only ones), `ONENOTE_REDIRECT_URI`
   (`http://localhost:10907/api/auth/callback`). Repo-root `.env` is loaded
   at startup (`constants.py`); `.env.example` documents everything.
3. **Flows (in preference order).**
   - Browser auth-code (primary): `GET /api/auth/login` → user approves in
     a real tab → `GET /api/auth/callback` redeems via
     `acquire_token_by_auth_code_flow` (note: legacy
     `acquire_token_by_authorization_code(code, scopes)` takes a scope list
     second — passing the flow dict raises "Invalid parameter type").
   - Device-code (fallback + `authenticate` MCP tool): `POST
     /api/auth/device` → `GET /api/auth/poll`, or blocking in the tool.
   - Manual: paste a token via `onenote_save_access_token` or
     `GRAPH_ACCESS_TOKEN`.
4. **Token stores (three layers).** `.access-token.txt` (the token; the
   webapp + debug endpoint read it), `.msal-token-cache.bin` (refresh token;
   enables silent re-auth across restarts — both gitignored), in-memory
   `_access_token` + cached httpx client (the client is **reset on every
   save**, otherwise re-auth keeps 401ing on the stale header).

**Scope recipe (load-bearing).** Request fully-qualified BASE scopes
(`https://graph.microsoft.com/Notes.Read|Notes.ReadWrite|User.Read`);
never pass `offline_access`/`openid`/`profile` to
`initiate_auth_code_flow` (MSAL injects them and raises on explicit ones —
this 500'd the login endpoint outright). Device-flow callers append
`offline_access` explicitly. Background: bare `.All` scopes minted tokens
the OneNote workload rejects with 40001 for personal accounts
(`docs/AUTH_INVESTIGATION.md` has the full 2026-09-24 evidence log).

**Consent versioning.** Changing requested scopes re-prompts automatically;
changing portal permissions does NOT — revoke the app at
account.live.com consent management to force a fresh grant.

**Diagnostics.** `GET /api/auth/debug` (client suffix, authority, scopes
requested, token shape/age, JWT aud/scp/exp — no secrets), auth-kind
entries in the activity log + Logging page, MSAL error text surfaced (never
swallowed into "failed").

## Graph quirks encoded in code

- Section-heavy accounts: collection-wide page queries fail (Graph 20266),
  so title search walks each notebook TOC (sections in parallel, 4-at-a-time)
  and title-matches client-side; slow sections are skipped individually with a
  warning count instead of failing the whole load. Full-text body search runs
  on a local SQLite FTS5 index (`src/onenote_mcp/search_index.py`, DB in
  gitignored `data/`, incremental by modified stamp, built via
  `POST /api/index` / `onenote_index_start`). Backups mirror the same walk
  into Markdown (`src/onenote_mcp/export_notes.py`, `data/exports/`).
- `$search` (full-text) is removed server-side for OneNote, so title match
  is the search semantic everywhere (results carry notebook/section).
- Page bodies come from `.../pages/{id}/content` (metadata endpoint has no
  body); the viewer sanitizes (DOMPurify) and anchors absolute layout
  (`.onenote-content` is `position: relative`).
