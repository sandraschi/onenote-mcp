# Tools

## MCP tools (19) + prompt (`onenote_triage`)

| Tool | Purpose |
|------|---------|
| `authenticate` | Sign in with Microsoft (device-code flow). |
| `onenote_save_access_token` | Store a Graph access token manually. |
| `onenote_list_notebooks` | List all accessible notebooks. |
| `onenote_get_notebook` | Details for one notebook. |
| `onenote_list_sections` | Sections of a notebook. |
| `onenote_list_pages` | Pages of a section. |
| `onenote_get_page` | Full HTML content of a page. |
| `onenote_create_page` | Create a page (HTML body) in a notebook. |
| `onenote_append_page` | Append plain text to a page (paragraphs from blank lines). |
| `onenote_search_pages` | Title (`mode="title"`) or FTS body search (`mode="fulltext"`). |
| `onenote_index_start` | Build/refresh the local full-text index (background). |
| `onenote_index_status` | Index build progress and searchable page count. |
| `onenote_get_notebook_toc` | Notebook table of contents (sections + pages). |
| `onenote_recent` | Recently modified pages across notebooks (domain inbox). |
| `onenote_export` | Back up notebooks to Markdown files (background). |
| `onenote_export_status` | Backup progress, file count, output dir. |
| `show_notebooks_card` | Notebooks as an in-chat Prefab card. |
| `onenote_help` | One-line usage for every tool. |
| `shutdown_server` | Graceful server termination. |

All tools are read-only except `onenote_create_page` / `onenote_append_page`
(MUTATING), `onenote_save_access_token` / `authenticate` (MUTATING) and
`shutdown_server` (DESTRUCTIVE). Every tool requires a valid Graph token
unless it is `authenticate` itself.

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
| `POST /api/auth/device`, `GET /api/auth/poll`, `GET /api/auth/status` | Non-blocking device-code auth (fallback). |
| `GET /api/auth/login`, `GET /api/auth/callback` | Browser auth-code sign-in (primary). |
| `GET /api/auth/debug` | Auth diagnostics: client suffix, authority, scopes, token shape/age, JWT claims (no secrets). |
| `GET /api/llm/providers`, `GET /api/llm/models`, `GET /api/llm/onboarding` | LLM registry + onboarding facts. |
| `POST /api/llm/chat` | Backend chat proxy (Ollama + OpenAI-compatible). |
| `GET /api/notebooks` | Notebook list. |
| `GET /api/notebooks/{id}/toc` | Notebook table of contents. |
| `GET /api/pages/{id}` | Page content. |
| `POST /api/pages` | Create page (`notebook_id`, `title`, `content`). |
| `GET /api/search?q=` | Search pages (`mode=title` default, `mode=fulltext` over the local index). |
| `POST /api/index`, `GET /api/index/status` | Build + monitor the FTS5 full-text index. |

## MCP transport

- stdio: default (`python -m onenote_mcp`).
- HTTP streamable: `MCP_TRANSPORT=http` or `--http`; MCP endpoint at `/mcp`
  (e.g. `http://127.0.0.1:10907/mcp`).
