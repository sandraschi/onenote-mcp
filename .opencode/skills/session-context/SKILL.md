---
name: session-context
description: OneNote session start - recall notebooks and save notes
---

## Session Context (OneNote MCP)

You have access to Microsoft OneNote via Microsoft Graph (12 tools).

**Before starting work:**
1. Find the notebook: `onenote_list_notebooks()`
2. Get structure: `onenote_get_notebook_toc(notebook_id="...")`

**At end of work, save insights:**
- Persist notes: `onenote_create_page(notebook_id=..., title=..., content="<html>")`
- If auth fails, run: `authenticate()`
