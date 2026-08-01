# Configuration

OneNote MCP reads configuration from environment variables (`.env` at repo root,
copied from `.env.example`) and the token file written by the device-code flow.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GRAPH_ACCESS_TOKEN` | - | Microsoft Graph bearer token. Optional - the `authenticate` tool / Settings page device-code flow writes a token file instead. |
| `ONENOTE_HOST` | `127.0.0.1` | HTTP bind host. |
| `ONENOTE_PORT` | `10907` | HTTP bind port (also honors `MCP_PORT`). |
| `ONENOTE_LOG_LEVEL` | `info` | uvicorn log level. |
| `MCP_TRANSPORT` | `stdio` | `stdio` / `http` / `sse` (sse deprecated). |
| `MCP_BRIDGE_URLS` | - | Comma-separated remote MCP URLs proxied via `create_proxy`. |

## Ports

- Backend (REST `/api/*` + MCP streamable HTTP `/mcp`): **10907**
- Frontend (Vite dev, proxies `/api` -> 10907): **10906**

## Authentication

Two paths, both targeting Microsoft Graph:

1. **Device-code flow** (recommended): run the `authenticate` MCP tool or the
   Settings page. A URL + code is shown; sign in, and the token is persisted to
   `.access-token.txt` at the repo root.
2. **Manual token**: set `GRAPH_ACCESS_TOKEN` in `.env`, or use the
   `onenote_save_access_token` tool.

The token file is read at startup and cached for the process lifetime. See
`docs/ONBOARDING.md` for the full first-run walkthrough.
