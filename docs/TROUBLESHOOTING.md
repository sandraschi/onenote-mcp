# Troubleshooting

## Authentication issues

| Symptom | Fix |
|---------|-----|
| `No access token available. Please authenticate first.` | Run the `authenticate` tool or Settings page device-code flow. |
| Device flow fails with `error_description` | The flow expired (10 min) or the code was mistyped. Restart the flow. |
| Stale token in `.access-token.txt` | Delete the file and re-authenticate. Tokens rotate; `401` on Graph calls means the stored token expired. |
| `GRAPH_ACCESS_TOKEN` not picked up | Set it in `.env` at repo root and restart the backend (loaded once at process start). |

## Server won't start

- Port 10907 occupied: `Get-NetTCPConnection -LocalPort 10907 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }`, then restart. `start.ps1` does this automatically.
- `pytest` / `uv` errors: run `uv sync --group dev` first.
- Frozen NSIS sidecar crashes: check `%LOCALAPPDATA%\{identifier}\logs\backend-spawn.log` (see `native/src/backend.rs` `log_line`).

## Webapp can't reach the backend

- Dev: Vite proxies `/api` -> 10907. If the proxy is missing, check `web_sota/vite.config.ts`.
- Installed NSIS app: the built frontend calls `http://127.0.0.1:10907` directly (see `web_sota/src/lib/api.ts`). If the backend didn't start, use the dashboard's **Restart Backend** button or check the spawn log.
- CORS: the backend ships the fleet CORS middleware (Tailscale `*.ts.net`, LAN, `tauri://localhost`). Do not loosen it.

## MCP client can't connect

- Claude Desktop / Cursor: point the `mcpServers` entry at `uv run --directory <repo> python -m onenote_mcp` (stdio) or `http://127.0.0.1:10907/mcp` (HTTP streamable) while the backend is running.
- The MCP surface is only reachable while the backend process is up (stdio clients spawn their own process).

## OneNote data issues

- Pages with no title display `Page <id>` - title comes from Graph metadata.
- `get_page` returns raw HTML. Rendering may be imperfect for complex pages; the webapp sanitizes with DOMPurify before rendering.
