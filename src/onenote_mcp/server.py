"""FastMCP server for Microsoft OneNote integration."""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Annotated, Any

import httpx
import msal
from fastmcp import FastMCP
from fastmcp.server import create_proxy
from pydantic import Field
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .constants import CLIENT_ID, SCOPES, TOKEN_FILE_NAME
from .models import Notebook, Page, Section, TOCData, TOCPage, TOCSection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("onenote_mcp")
_SERVER_VERSION = "1.0.0"
_START_TIME = time.monotonic()

# Fire-and-forget shutdown tasks (stored to satisfy RUF006)
_shutdown_tasks: list[asyncio.Task] = []

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOKEN_FILE_PATH = PROJECT_ROOT / TOKEN_FILE_NAME

# Global state
_access_token: str | None = None
_graph_client: httpx.AsyncClient | None = None


def load_access_token() -> str | None:
    """Load access token from file or environment variable."""
    global _access_token
    if _access_token:
        return _access_token

    # Try to read from file
    try:
        if TOKEN_FILE_PATH.exists():
            token_data = TOKEN_FILE_PATH.read_text().strip()
            try:
                # Try parsing as JSON first (new format)
                parsed_token = json.loads(token_data)
                _access_token = parsed_token.get("token")
            except json.JSONDecodeError:
                # Fall back to raw token (old format)
                _access_token = token_data
            return _access_token
    except Exception as e:
        print(f"Error reading access token file: {e}")

    # Check environment variable
    if env_token := os.getenv("GRAPH_ACCESS_TOKEN"):
        _access_token = env_token.strip()
        return _access_token

    return None


def save_access_token(token: str) -> None:
    """Save access token to file."""
    global _access_token
    _access_token = token

    token_data = json.dumps({"token": token}, indent=2)
    TOKEN_FILE_PATH.write_text(token_data)
    print(f"Access token saved to {TOKEN_FILE_PATH}")


async def get_graph_client() -> httpx.AsyncClient:
    """Get or create Microsoft Graph API client."""
    global _graph_client
    if _graph_client:
        return _graph_client

    token = load_access_token()
    if not token:
        raise ValueError("No access token available. Please authenticate first.")

    _graph_client = httpx.AsyncClient(
        base_url="https://graph.microsoft.com/v1.0", headers={"Authorization": f"Bearer {token}"}
    )
    return _graph_client


async def authenticate_device_code() -> dict[str, Any]:
    """Start device code authentication flow."""
    app = msal.PublicClientApplication(CLIENT_ID, authority="https://login.microsoftonline.com/common")

    # Get device code
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError("Failed to create device flow")

    print("To authenticate, please:")
    print(f"1. Go to: {flow['verification_uri']}")
    print(f"2. Enter the code: {flow['user_code']}")
    print("3. Sign in with your Microsoft account")

    # Wait for user to complete authentication
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        save_access_token(result["access_token"])
        return {"success": True, "message": "Authentication successful"}
    else:
        error = result.get("error_description", "Authentication failed")
        raise ValueError(f"Authentication failed: {error}")


async def list_notebooks() -> list[Notebook]:
    """List all OneNote notebooks."""
    client = await get_graph_client()
    response = await client.get("/me/onenote/notebooks")
    response.raise_for_status()

    data = response.json()
    return [Notebook(**notebook) for notebook in data.get("value", [])]


async def get_notebook(notebook_id: str) -> Notebook:
    """Get details of a specific notebook."""
    client = await get_graph_client()
    response = await client.get(f"/me/onenote/notebooks/{notebook_id}")
    response.raise_for_status()

    return Notebook(**response.json())


async def list_sections(notebook_id: str) -> list[Section]:
    """List all sections in a notebook."""
    client = await get_graph_client()
    response = await client.get(f"/me/onenote/notebooks/{notebook_id}/sections")
    response.raise_for_status()

    data = response.json()
    return [Section(**section) for section in data.get("value", [])]


async def list_pages(section_id: str) -> list[Page]:
    """List all pages in a section."""
    client = await get_graph_client()
    response = await client.get(f"/me/onenote/sections/{section_id}/pages")
    response.raise_for_status()

    data = response.json()
    pages = []
    for page_data in data.get("value", []):
        # Extract title from content or use ID as fallback
        title = page_data.get("title", f"Page {page_data['id'][:8]}")
        pages.append(Page(**{**page_data, "title": title}))

    return pages


async def get_page(page_id: str) -> Page:
    """Get complete content of a specific page."""
    client = await get_graph_client()
    response = await client.get(f"/me/onenote/pages/{page_id}")
    response.raise_for_status()

    page_data = response.json()
    content = response.text  # Get HTML content

    return Page(
        id=page_data["id"],
        title=page_data.get("title", f"Page {page_data['id'][:8]}"),
        createdDateTime=page_data["createdDateTime"],
        lastModifiedDateTime=page_data["lastModifiedDateTime"],
        self=page_data["self"],
        contentUrl=page_data["contentUrl"],
        content=content,
    )


async def create_page(notebook_id: str, title: str, content: str) -> dict[str, Any]:
    """Create a new page with HTML content."""
    client = await get_graph_client()

    # Basic HTML structure
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
    </head>
    <body>
        <h1>{title}</h1>
        {content}
    </body>
    </html>
    """

    response = await client.post(
        f"/me/onenote/notebooks/{notebook_id}/pages",
        content=html_content,
        headers={"Content-Type": "text/html"},
    )
    response.raise_for_status()

    return response.json()


async def search_pages(query: str) -> list[Page]:
    """Search for pages across all notebooks."""
    client = await get_graph_client()
    response = await client.get(f"/me/onenote/pages?search={query}")
    response.raise_for_status()

    data = response.json()
    pages = []
    for page_data in data.get("value", []):
        title = page_data.get("title", f"Page {page_data['id'][:8]}")
        pages.append(Page(**{**page_data, "title": title}))

    return pages


async def get_notebook_toc(notebook_id: str) -> TOCData:
    """Generate table of contents for a notebook."""
    notebook = await get_notebook(notebook_id)
    sections = await list_sections(notebook_id)

    toc_sections = []
    total_pages = 0

    for section in sections:
        pages = await list_pages(section.id)
        total_pages += len(pages)

        toc_pages = [
            TOCPage(
                title=page.title,
                id=page.id,
                created=page.createdDateTime,
                modified=page.lastModifiedDateTime,
            )
            for page in pages
        ]

        toc_sections.append(TOCSection(name=section.displayName, pageCount=len(pages), pages=toc_pages))

    return TOCData(
        notebook=notebook.displayName,
        stats={"sections": len(sections), "pages": total_pages},
        sections=toc_sections,
    )


# Create FastMCP app
app = FastMCP(name="onenote-mcp", instructions="Microsoft OneNote integration via Model Context Protocol")


@app.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "server": "onenote-mcp"})


# ---- Webapp REST API (fleet SOTA endpoints) ----

_TAGGED_SKILLS: list[dict[str, str]] = []
_HELP_TOOLS: list[dict[str, str]] = []


_TOOL_REGISTRY: tuple[str, ...] = (
    "authenticate",
    "onenote_save_access_token",
    "onenote_list_notebooks",
    "onenote_get_notebook",
    "onenote_list_sections",
    "onenote_list_pages",
    "onenote_get_page",
    "onenote_create_page",
    "onenote_search_pages",
    "onenote_get_notebook_toc",
    "onenote_help",
    "shutdown_server",
)


def _list_mcp_tools() -> list[dict[str, str]]:
    """Return registered MCP tools as name/description dicts."""
    try:
        return [{"name": name, "description": ""} for name in _TOOL_REGISTRY]
    except Exception:
        return [{"name": name, "description": ""} for name in _TOOL_REGISTRY]


def _tool_count() -> int:
    return len(_list_mcp_tools())


@app.custom_route("/api/status", methods=["GET"])
async def api_status(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "server": "onenote-mcp",
            "version": _SERVER_VERSION,
            "uptime_seconds": int(time.monotonic() - _START_TIME),
            "tool_count": _tool_count(),
            "providers": {"graph": {"authenticated": bool(load_access_token())}},
        }
    )


@app.custom_route("/api/capabilities", methods=["GET"])
async def api_capabilities(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "server": "onenote-mcp",
            "version": _SERVER_VERSION,
            "features": {
                "notebooks": True,
                "sections": True,
                "pages": True,
                "search": True,
                "toc": True,
                "auth": True,
                "chat": False,
                "skills": False,
            },
            "tools": [t["name"] for t in _list_mcp_tools()],
        }
    )


@app.custom_route("/api/skills", methods=["GET"])
async def api_skills(request: Request) -> JSONResponse:
    return JSONResponse({"skills": _TAGGED_SKILLS})


@app.custom_route("/api/llm/discover", methods=["GET"])
async def api_llm_discover(request: Request) -> JSONResponse:
    ollama_detected = False
    configured_model = ""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://127.0.0.1:11434/api/tags")
            if r.status_code == 200:
                ollama_detected = True
                models = r.json().get("models", [])
                if models:
                    configured_model = models[0].get("name", "")
    except Exception:
        pass
    return JSONResponse(
        {
            "ollama_detected": ollama_detected,
            "configured_model": configured_model,
            "providers": {"ollama": {"detected": ollama_detected, "port": 11434}},
        }
    )


@app.custom_route("/api/v1/diagnostics", methods=["GET"])
async def api_diagnostics(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "server": "onenote-mcp",
            "version": _SERVER_VERSION,
            "uptime_seconds": int(time.monotonic() - _START_TIME),
            "tool_count": _tool_count(),
            "tools": [{"name": t["name"]} for t in _list_mcp_tools()],
            "system": {"windows": sys.platform == "win32"},
            "errors": [],
        }
    )


@app.custom_route("/api/shutdown", methods=["POST"])
async def api_shutdown(request: Request) -> JSONResponse:
    """Graceful shutdown - agent-requested termination."""
    logger.warning("Shutdown requested via /api/shutdown")

    async def _terminate():
        await asyncio.sleep(0.5)
        os._exit(0)

    _shutdown_tasks.append(asyncio.create_task(_terminate()))
    return JSONResponse({"success": True, "message": "Server shutting down..."})


# ---- Webapp activity log (ring buffer) ----

from .activity_log import ActivityLog

_log = ActivityLog()


@app.custom_route("/api/logs", methods=["GET"])
async def api_get_logs(request: Request) -> JSONResponse:
    qp = request.query_params
    try:
        limit = int(qp.get("limit", 50))
        offset = int(qp.get("offset", 0))
    except (TypeError, ValueError):
        limit, offset = 50, 0
    return JSONResponse(
        _log.query(
            limit=limit,
            offset=offset,
            level=qp.get("level"),
            kind=qp.get("kind"),
            search=qp.get("search"),
            sort=qp.get("sort", "desc"),
            after_id=qp.get("after_id"),
        )
    )


@app.custom_route("/api/logs", methods=["DELETE"])
async def api_clear_logs(request: Request) -> JSONResponse:
    _log.clear()
    return JSONResponse({"success": True, "message": "Logs cleared."})


@app.custom_route("/api/logs/stats", methods=["GET"])
async def api_logs_stats(request: Request) -> JSONResponse:
    return JSONResponse(_log.stats())


@app.custom_route("/api/logs/export", methods=["GET"])
async def api_logs_export(request: Request) -> JSONResponse:
    qp = request.query_params
    content = _log.export(
        format=qp.get("format", "json"),
        level=qp.get("level"),
        kind=qp.get("kind"),
        search=qp.get("search"),
    )
    from starlette.responses import Response

    media = "text/csv" if qp.get("format") == "csv" else "application/json"
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="logs.{qp.get("format", "json")}"'},
    )


# ---- Webapp auth (non-blocking device-code flow) ----

_auth_flows: dict[str, dict[str, Any]] = {}


def _start_auth_flow() -> dict[str, Any]:
    import msal

    app = msal.PublicClientApplication(CLIENT_ID, authority="https://login.microsoftonline.com/common")
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise ValueError("Failed to create device flow")
    flow_id = flow.get("device_code", "")[-8:]
    _auth_flows[flow_id] = {"flow": flow, "status": "pending", "result": None}

    def _wait():
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            save_access_token(result["access_token"])
            _auth_flows[flow_id]["result"] = {
                "success": True,
                "account": result.get("id_token_claims", {}).get("preferred_username", ""),
            }
            _auth_flows[flow_id]["status"] = "authorized"
        else:
            _auth_flows[flow_id]["result"] = {
                "success": False,
                "error": result.get("error_description", "Authentication failed"),
            }
            _auth_flows[flow_id]["status"] = "error"

    import threading

    threading.Thread(target=_wait, daemon=True).start()
    return {
        "flow_id": flow_id,
        "user_code": flow["user_code"],
        "verification_uri": flow.get("verification_uri", "https://microsoft.com/devicelogin"),
        "expires_in": flow.get("expires_in", 900),
        "interval": flow.get("interval", 5),
    }


@app.custom_route("/api/auth/device", methods=["POST"])
async def api_auth_device(request: Request) -> JSONResponse:
    try:
        return JSONResponse({"success": True, **(_start_auth_flow())})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.custom_route("/api/auth/poll", methods=["GET"])
async def api_auth_poll(request: Request) -> JSONResponse:
    flow_id = request.query_params.get("flow_id", "")
    state = _auth_flows.get(flow_id)
    if not state:
        return JSONResponse({"success": False, "status": "error", "error": "unknown flow"}, status_code=404)
    if state["status"] == "pending":
        return JSONResponse({"success": True, "status": "pending"})
    return JSONResponse(
        {"success": state["result"].get("success", False), "status": state["status"], **state["result"]}
    )


@app.custom_route("/api/auth/status", methods=["GET"])
async def api_auth_status(request: Request) -> JSONResponse:
    token = load_access_token()
    return JSONResponse({"authenticated": bool(token)})


# ---- REST API for the webapp (notebook/section/page browser) ----


def _error_response(exc: Exception) -> JSONResponse:
    logger.exception("API error: %s", exc)
    return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@app.custom_route("/api/notebooks", methods=["GET"])
async def api_list_notebooks(request: Request) -> JSONResponse:
    try:
        notebooks = await list_notebooks()
        return JSONResponse({"success": True, "notebooks": [n.model_dump() for n in notebooks]})
    except Exception as exc:
        return _error_response(exc)


@app.custom_route("/api/notebooks/{notebook_id}/toc", methods=["GET"])
async def api_notebook_toc(request: Request) -> JSONResponse:
    notebook_id = request.path_params["notebook_id"]
    try:
        toc = await get_notebook_toc(notebook_id)
        return JSONResponse({"success": True, "toc": toc.model_dump()})
    except Exception as exc:
        return _error_response(exc)


@app.custom_route("/api/pages/{page_id}", methods=["GET"])
async def api_get_page(request: Request) -> JSONResponse:
    page_id = request.path_params["page_id"]
    try:
        page = await get_page(page_id)
        return JSONResponse({"success": True, "page": page.model_dump()})
    except Exception as exc:
        return _error_response(exc)


@app.custom_route("/api/search", methods=["GET"])
async def api_search_pages(request: Request) -> JSONResponse:
    query = request.query_params.get("q", "")
    if not query:
        return JSONResponse({"success": False, "error": "q query param required"}, status_code=400)
    try:
        pages = await search_pages(query)
        return JSONResponse({"success": True, "query": query, "pages": [p.model_dump() for p in pages]})
    except Exception as exc:
        return _error_response(exc)


@app.custom_route("/api/pages", methods=["POST"])
async def api_create_page(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    notebook_id = body.get("notebook_id", "")
    title = body.get("title", "")
    content = body.get("content", "")
    if not notebook_id or not title:
        return JSONResponse({"success": False, "error": "notebook_id and title are required"}, status_code=400)
    try:
        result = await create_page(notebook_id, title, content)
        return JSONResponse({"success": True, "page": result})
    except Exception as exc:
        return _error_response(exc)


# MCP Bridge — proxy remote MCP servers via ProxyProvider
MCP_BRIDGE_URLS = os.environ.get("MCP_BRIDGE_URLS", "")
if MCP_BRIDGE_URLS:
    for url in MCP_BRIDGE_URLS.split(","):
        url = url.strip()
        if url:
            app.add_provider(create_proxy(url))


@app.tool()
async def authenticate() -> str:
    """Start the Microsoft authentication flow using device code.

    This tool initiates the OAuth 2.0 device code flow for Microsoft Graph API.
    The user will be provided with a URL and code to complete authentication
    in their browser.

    Returns:
        Success message or error details
    """
    try:
        result = await authenticate_device_code()
        return f"✅ {result['message']}"
    except Exception as e:
        return f"❌ Authentication failed: {e!s}"


@app.tool()
async def onenote_save_access_token(
    token: Annotated[str, Field(description="The Microsoft Graph access token to save")],
) -> str:
    """Save a Microsoft Graph access token for later use.

    Persists the token to the local token file so subsequent tools can call the Graph API.

    ## Return Format
    A confirmation string: "✅ Access token saved successfully" or "❌ ..." on failure.

    ## Examples
    save_access_token(token="eyJhbGciOi...")  # paste a token from az login / Graph explorer
    """
    try:
        save_access_token(token)
        return "✅ Access token saved successfully"
    except Exception as e:
        return f"❌ Failed to save token: {e!s}"


@app.tool()
async def onenote_list_notebooks() -> str:
    """List all Microsoft OneNote notebooks accessible to the signed-in account.

    ## Return Format
    Markdown string: "📓 Your OneNote Notebooks:" followed by numbered notebooks with ID.

    ## Examples
    list_notebooks()
    """
    try:
        notebooks = await list_notebooks()
        if not notebooks:
            return "No notebooks found"

        result = "📓 Your OneNote Notebooks:\n\n"
        for i, notebook in enumerate(notebooks, 1):
            result += f"{i}. **{notebook.displayName}**\n"
            result += f"   ID: `{notebook.id}`\n\n"

        return result
    except Exception as e:
        return f"❌ Failed to list notebooks: {e!s}"


@app.tool()
async def onenote_get_notebook(
    notebook_id: Annotated[str, Field(description="The ID of the notebook to retrieve")],
) -> str:
    """Get details of a specific OneNote notebook.

    ## Return Format
    Markdown string with notebook name, ID, sections URL, and section groups URL.

    ## Examples
    get_notebook(notebook_id="0-ABC123...")
    """
    try:
        notebook = await get_notebook(notebook_id)
        return f"""📓 Notebook Details:

**Name:** {notebook.displayName}
**ID:** `{notebook.id}`
**Sections URL:** {notebook.sectionsUrl}
**Section Groups URL:** {notebook.sectionGroupsUrl}
"""
    except Exception as e:
        return f"❌ Failed to get notebook: {e!s}"


@app.tool()
async def onenote_list_sections(notebook_id: Annotated[str, Field(description="The ID of the notebook")]) -> str:
    """List all sections in a OneNote notebook.

    ## Return Format
    Markdown string: "📂 Sections in notebook:" with numbered sections and their page URLs.

    ## Examples
    list_sections(notebook_id="0-ABC123...")
    """
    try:
        sections = await list_sections(notebook_id)
        if not sections:
            return "No sections found in this notebook"

        result = "📂 Sections in notebook:\n\n"
        for i, section in enumerate(sections, 1):
            result += f"{i}. **{section.displayName}**\n"
            result += f"   ID: `{section.id}`\n"
            result += f"   Pages URL: {section.pagesUrl}\n\n"

        return result
    except Exception as e:
        return f"❌ Failed to list sections: {e!s}"


@app.tool()
async def onenote_list_pages(section_id: Annotated[str, Field(description="The ID of the section")]) -> str:
    """List all pages in a OneNote section.

    ## Return Format
    Markdown string: "📄 Pages in section:" with numbered pages, created and modified dates.

    ## Examples
    list_pages(section_id="0-SEC123...")
    """
    try:
        pages = await list_pages(section_id)
        if not pages:
            return "No pages found in this section"

        result = "📄 Pages in section:\n\n"
        for i, page in enumerate(pages, 1):
            result += f"{i}. **{page.title}**\n"
            result += f"   ID: `{page.id}`\n"
            result += f"   Created: {page.createdDateTime}\n"
            result += f"   Modified: {page.lastModifiedDateTime}\n\n"

        return result
    except Exception as e:
        return f"❌ Failed to list pages: {e!s}"


@app.tool()
async def onenote_get_page(page_id: Annotated[str, Field(description="The ID of the page to retrieve")]) -> str:
    """Get the complete HTML content of a OneNote page.

    Retrieves the full page content including text, formatting, and embedded elements.

    ## Return Format
    Markdown string: "📄 Page Content:" with title, ID, timestamps, and the raw HTML body.

    ## Examples
    get_page(page_id="0-PG123...")
    """
    try:
        page = await get_page(page_id)
        if page.content:
            # For now, return the HTML content
            # TODO: Convert HTML to markdown for better readability
            return f"""📄 Page Content:

**Title:** {page.title}
**ID:** {page.id}
**Created:** {page.createdDateTime}
**Modified:** {page.lastModifiedDateTime}

---

{page.content}
"""
        else:
            return f"""📄 Page Info:

**Title:** {page.title}
**ID:** {page.id}
**Created:** {page.createdDateTime}
**Modified:** {page.lastModifiedDateTime}

*(Content not available)*
"""
    except Exception as e:
        return f"❌ Failed to get page content: {e!s}"


@app.tool()
async def onenote_create_page(
    notebook_id: Annotated[str, Field(description="The ID of the notebook to create the page in")],
    title: Annotated[str, Field(description="The title of the new page")],
    content: Annotated[str, Field(description="Optional HTML content for the page")] = "",
) -> str:
    """Create a new page in a OneNote notebook.

    ## Return Format
    Confirmation string: "✅ Page '<title>' created successfully with ID: `<id>`".

    ## Examples
    create_page(notebook_id="0-ABC123...", title="Meeting Notes", content="<h1>Notes</h1><p>...</p>")
    """
    try:
        result = await create_page(notebook_id, title, content)
        page_id = result.get("id", "unknown")
        return f"✅ Page '{title}' created successfully with ID: `{page_id}`"
    except Exception as e:
        return f"❌ Failed to create page: {e!s}"


@app.tool()
async def onenote_search_pages(query: Annotated[str, Field(description="Search query string")]) -> str:
    """Search for pages across all OneNote notebooks.

    ## Return Format
    Markdown string: "🔍 Search Results for '<query>':" with numbered matching pages.

    ## Examples
    search_pages(query="quarterly report")
    """
    try:
        pages = await search_pages(query)
        if not pages:
            return f"No pages found matching query: '{query}'"

        result = f"🔍 Search Results for '{query}':\n\n"
        for i, page in enumerate(pages, 1):
            result += f"{i}. **{page.title}**\n"
            result += f"   ID: `{page.id}`\n"
            result += f"   Created: {page.createdDateTime}\n"
            result += f"   Modified: {page.lastModifiedDateTime}\n\n"

        return result
    except Exception as e:
        return f"❌ Search failed: {e!s}"


@app.tool()
async def onenote_get_notebook_toc(notebook_id: Annotated[str, Field(description="The ID of the notebook")]) -> str:
    """Generate a table of contents for a OneNote notebook.

    Creates a comprehensive overview of all sections and pages, useful for navigation.

    ## Return Format
    Markdown string: "📚 Table of Contents: <notebook>" with stats and per-section page lists.

    ## Examples
    get_notebook_toc(notebook_id="0-ABC123...")
    """
    try:
        toc = await get_notebook_toc(notebook_id)

        result = f"""📚 Table of Contents: {toc.notebook}

**Stats:** {toc.stats["sections"]} sections, {toc.stats["pages"]} pages

"""

        for section in toc.sections:
            result += f"## 📂 {section.name} ({section.pageCount} pages)\n\n"

            for page in section.pages:
                created_date = page.created.split("T")[0]  # Just the date part
                result += f"- **{page.title}** _{created_date}_\n"

            result += "\n"

        return result
    except Exception as e:
        return f"❌ Failed to generate TOC: {e!s}"


@app.tool()
async def shutdown_server() -> str:
    """Shut down the onenote-mcp server gracefully.

    Use when the user or an agent explicitly asks to stop the server process.

    ## Return Format
    Confirmation string: "✅ Server shutting down...".

    ## Examples
    shutdown_server()
    """
    logger.warning("Shutdown requested via MCP tool")

    async def _terminate():
        await asyncio.sleep(0.5)
        os._exit(0)

    _shutdown_tasks.append(asyncio.create_task(_terminate()))
    return "✅ Server shutting down..."


@app.tool()
async def onenote_help() -> str:
    """List the available OneNote MCP tools and when to use each.

    ## Return Format
    Markdown string enumerating the 11 tools with one-line usage notes.

    ## Examples
    onenote_help()
    """
    return """📚 **OneNote MCP tools:**
- `authenticate` - start Microsoft device-code login
- `save_access_token` - store a Graph token manually
- `list_notebooks` - all notebooks
- `get_notebook` - notebook details
- `list_sections` - sections of a notebook
- `list_pages` - pages of a section
- `get_page` - full HTML content of a page
- `create_page` - add a page with HTML body
- `search_pages` - full-text search across notebooks
- `get_notebook_toc` - sections + pages overview
- `shutdown_server` - stop the server"""


# ASGI app for uvicorn (fleet standard: serve mcp.http_app(), never the raw FastMCP object)
http_app = CORSMiddleware(
    app.http_app(),
    allow_origins=[
        "http://localhost:10906",
        "http://127.0.0.1:10906",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def main():
    """Main entry point with unified transport handling (FastMCP 2.14.4+)."""
    from .transport import run_server

    run_server(app, server_name="onenote-mcp")


if __name__ == "__main__":
    main()
