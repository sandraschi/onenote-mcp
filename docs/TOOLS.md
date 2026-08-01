# Tools

## MCP tools (12)

| Tool | Purpose |
|------|---------|
| `authenticate` | Start Microsoft device-code login flow. |
| `onenote_save_access_token` | Store a Graph access token manually. |
| `onenote_list_notebooks` | List all accessible notebooks. |
| `onenote_get_notebook` | Details for one notebook. |
| `onenote_list_sections` | Sections of a notebook. |
| `onenote_list_pages` | Pages of a section. |
| `onenote_get_page` | Full HTML content of a page. |
| `onenote_create_page` | Create a page (HTML body) in a notebook. |
| `onenote_search_pages` | Full-text search across notebooks. |
| `onenote_get_notebook_toc` | Notebook table of contents (sections + pages). |
| `onenote_help` | One-line usage for every tool. |
| `shutdown_server` | Graceful server termination. |

All tools are read-only except `onenote_create_page` (MUTATING),
`onenote_save_access_token` / `authenticate` (MUTATING) and `shutdown_server`
(DESTRUCTIVE). Every tool requires a valid Graph token unless it is
`authenticate` itself.

## REST API (backend 10907)

| Endpoint | Purpose |
|----------|---------|
| `GET /health`, `GET /api/v1/health` | Liveness + version/uptime/tool count. |
| `GET /api/status` | Status incl. Graph auth state. |
| `GET /api/capabilities` | Feature flags + tool list. |
| `GET /api/skills` | Registered skills (serves `skill://onenote`). |
| `GET /api/llm/discover` | Local LLM probe (Ollama 11434, LM Studio 1234, vLLM 8000). |
| `GET /api/v1/diagnostics` | Tool list + system info (CUA smoke test). |
| `POST /api/shutdown` | Graceful shutdown. |
| `GET /api/logs`, `DELETE /api/logs`, `GET /api/logs/stats`, `GET /api/logs/export` | Ring-buffer activity log. |
| `POST /api/auth/device`, `GET /api/auth/poll`, `GET /api/auth/status` | Non-blocking device-code auth. |
| `GET /api/notebooks` | Notebook list. |
| `GET /api/notebooks/{id}/toc` | Notebook table of contents. |
| `GET /api/pages/{id}` | Page content. |
| `POST /api/pages` | Create page (`notebook_id`, `title`, `content`). |
| `GET /api/search?q=` | Search pages. |

## MCP transport

- stdio: default (`python -m onenote_mcp`).
- HTTP streamable: `MCP_TRANSPORT=http` or `--http`; MCP endpoint at `/mcp`
  (e.g. `http://127.0.0.1:10907/mcp`).
