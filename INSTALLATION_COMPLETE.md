# OneNote MCP Installation Complete

## Installation Status

✅ **Repository cloned**: `D:\Dev\repos\onenote-mcp`
✅ **Dependencies installed**: Python packages installed successfully
✅ **FastMCP 2.13+**: Using current standard implementation

## Tool Count

**9 tools total** - Well under Cursor's 50-tool limit ✅

1. `authenticate` - Start Microsoft authentication flow
2. `saveAccessToken` - Save access token for later use
3. `listNotebooks` - List all OneNote notebooks
4. `getNotebook` - Get details of a specific notebook
5. `listSections` - List all sections in a notebook
6. `listPages` - List all pages in a section
7. `getPage` - Get complete page content (including HTML formatting)
8. `createPage` - Create a new page with HTML content
9. `searchPages` - Search for pages across notebooks

## Next Steps

### 1. Test the Server

```powershell
cd D:\Dev\repos\onenote-mcp
python -m onenote_mcp.server --help
```

### 2. Configure for Cursor

Add to Cursor's MCP configuration (`.cursor/mcp.json` or Cursor settings):

```json
{
  "mcpServers": {
    "onenote": {
      "command": "python",
      "args": ["-m", "onenote_mcp.server"],
      "env": {}
    }
  }
}
```

### 3. Configure for Claude Desktop

Add to Claude Desktop settings (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "onenote": {
      "command": "python",
      "args": ["-m", "onenote_mcp.server"],
      "env": {}
    }
  }
}
```

### 4. Authenticate

After starting the server, use the `authenticate` tool through your AI assistant:
- The AI will provide a URL and code
- Visit the URL, enter the code
- Sign in with your Microsoft account
- Token will be saved to `.access-token.txt`

## Key Features

✅ **Reads note content** - `getPage` returns complete page content including HTML
✅ **Low tool count** - Only 9 tools (vs 50+ in microsoft-365-mcp)
✅ **Focused functionality** - Purpose-built for OneNote
✅ **Device code auth** - No Azure setup required
✅ **MCP-friendly format** - Content returned in readable format

## Comparison to microsoft-365-mcp

| Feature | danosb/onenote-mcp | microsoft-365-mcp |
|---------|-------------------|-------------------|
| Tool Count | ✅ 9 tools | ❌ 50+ tools |
| Read Note Content | ✅ Yes (HTML + text) | ❌ Limited |
| OneNote Focus | ✅ Yes | ❌ Covers all M365 |
| Cursor Compatible | ✅ Yes | ❌ Exceeds limit |
| Setup Complexity | ✅ Simple | ❌ Complex |

## Usage Examples

Once configured, you can ask your AI assistant:

```
Show me my OneNote notebooks
List all pages in my "Work" notebook
Read the content of my "Meeting Notes" page
Create a new page titled "Project Ideas"
Search for notes about "machine learning"
```

---

**Installation Date**: 2025-12-21
**Status**: Ready to use (FastMCP 2.13+ implementation)

