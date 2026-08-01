# OneNote MCP — Skill

## What this server does

OneNote MCP connects an AI assistant to Microsoft OneNote through the Microsoft
Graph API: browsing notebooks/sections/pages, reading full page content (HTML),
creating pages, and full-text search across the user's notes. 13 tools,
dual transport (stdio + HTTP streamable on 10907).

## Tool categories

| Category | Tools |
|----------|-------|
| Auth | `authenticate`, `onenote_save_access_token` |
| Discovery | `onenote_list_notebooks`, `onenote_get_notebook`, `onenote_list_sections`, `onenote_list_pages`, `onenote_get_notebook_toc` |
| Content | `onenote_get_page`, `onenote_create_page`, `onenote_search_pages` |
| Presentation | `show_notebooks_card` (in-chat Prefab card) |
| System | `onenote_help`, `shutdown_server` |

## Best practices

1. **Authenticate first.** If any tool returns `No access token available`,
   call `authenticate()` (device-code flow) before anything else.
2. **Navigate top-down.** Start with `onenote_list_notebooks()`, then
   `onenote_get_notebook_toc(notebook_id=...)` to see sections + pages in one
   call, then `onenote_get_page(page_id=...)` for content. IDs are opaque
   Graph IDs - always pass them through, never truncate.
3. **Creating pages** takes HTML content:
   `onenote_create_page(notebook_id=..., title="Meeting Notes", content="<h1>...</h1><p>...</p>")`.
4. **Search** (`onenote_search_pages`) is full-text across all notebooks -
   use it when the user describes a note instead of naming a notebook.
5. **Page content is HTML.** Read it as-is; render/sanitize before display
   (the webapp uses DOMPurify).

## Configuration requirements

- Microsoft Graph access: either `GRAPH_ACCESS_TOKEN` in `.env` or the
  device-code flow (recommended; token persisted to `.access-token.txt`).
- Ports: backend 10907 (`/mcp` for MCP, `/api/*` for REST), webapp 10906.
- `MCP_BRIDGE_URLS` optionally proxies remote MCP servers.

## Notes

- Token expiry: Graph tokens rotate; on 401s re-run `authenticate()` or update
  `GRAPH_ACCESS_TOKEN`.
- The MCP surface is reachable only while the backend process runs.
