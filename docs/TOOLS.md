# Tools

## MCP tools (26) + prompt (`onenote_triage`)

| Tool | Purpose |
|------|---------|
| `authenticate` | Sign in with Microsoft (device-code flow). |
| `onenote_save_access_token` | Store a Graph access token manually. |
| `onenote_list_notebooks` | List all accessible notebooks. |
| `onenote_get_notebook` | Details for one notebook. |
| `onenote_list_sections` | Sections of a notebook. |
| `onenote_list_pages` | Pages of a section. |
| `onenote_get_page` | Page content as HTML or Markdown (`output_format`) plus OneNote web/app links; `include_ids` for element IDs. |
| `onenote_create_page` | Create a page from HTML or Markdown (`content_format`) in a section (`section_id`) or the notebook's default section. |
| `onenote_append_page` | Append plain text (paragraphs from blank lines) or Markdown to a page. |
| `onenote_update_page` | Edit one element of a page (replace/insert/prepend/append) or retitle it. |
| `onenote_delete_page` | Permanently delete a page (DESTRUCTIVE). |
| `onenote_get_links` | Web and desktop-app links to open a notebook, section or page. |
| `onenote_create_notebook` | Create a notebook. Graph cannot rename or delete it afterwards. |
| `onenote_create_section` | Create a section in a notebook. Graph cannot rename or delete it afterwards. |
| `onenote_create_section_group` | Create a section group in a notebook. |
| `onenote_list_section_groups` | Section groups of a notebook. |
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

Annotations use the real MCP hints (`readOnlyHint`, `destructiveHint`, `openWorldHint`):
read-only tools list/get/search/status; MUTATING (non-destructive writes) are the
create/append/update tools, `onenote_export`, `onenote_index_start`, `authenticate`
and `onenote_save_access_token`; DESTRUCTIVE are `onenote_delete_page` and `shutdown_server`.
Every tool requires a valid Graph token unless it is `authenticate` itself.

**Markdown (verified live 2026-10-06):** `onenote_create_page`, `onenote_append_page` and
`onenote_update_page` accept `content_format="markdown"`; `onenote_get_page` returns
`output_format="markdown"`. Raw HTML inside Markdown input is escaped, never passed through.
`- [ ]` / `- [x]` items become OneNote to-do paragraphs (`data-tag="to-do"`) and read back as
task items. OneNote restyles on save (bold/italic/code become styled spans, which the reader
understands; block quotes become plain paragraphs, so the quote marker does not survive).
Markdown output is a reading view; use HTML plus `include_ids=True` to edit by element.
`onenote_get_links` returns the web link and the `onenote:` desktop-app link for a notebook or
page; sections returned no links on a personal account.

**Graph limits (v1.0, verified live on a personal Microsoft account 2026-10-06):** there is no
endpoint to delete or rename a notebook, section or section group, so this server
deliberately offers none. Pages can be created, edited element-wise (replace/insert/
prepend/append; `delete` is rejected with 20122, so blank an element by replacing it with
an empty paragraph) and deleted. Section copy (`copyToNotebook`) returns
`501 OData Feature not implemented` on personal accounts, so it is not offered; it may work
on work/school accounts (untested). Use `onenote_get_page(include_ids=True)` to get the
element IDs `onenote_update_page` targets. Notebook names: max 128 chars, no `? * \ / : < > | ' "`;
section and group names: max 50 chars, no `? * \ / : < > | & # ' % ~`.

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
