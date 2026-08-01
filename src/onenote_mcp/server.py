"""FastMCP server for Microsoft OneNote integration."""

import json
import os
from pathlib import Path
from typing import Any

import httpx
import msal
from fastmcp import FastMCP
from fastmcp.server import create_proxy
from starlette.requests import Request
from starlette.responses import JSONResponse

from .constants import CLIENT_ID, SCOPES, TOKEN_FILE_NAME
from .models import Notebook, Page, Section, TOCData, TOCPage, TOCSection

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


# ---- REST API for the webapp (notebook/section/page browser) ----


def _error_response(exc: Exception) -> JSONResponse:
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
async def saveAccessToken(token: str) -> str:
    """Save an access token for later use.

    Args:
        token: The Microsoft Graph access token to save

    Returns:
        Confirmation message
    """
    try:
        save_access_token(token)
        return "✅ Access token saved successfully"
    except Exception as e:
        return f"❌ Failed to save token: {e!s}"


@app.tool()
async def listNotebooks() -> str:
    """Get a list of all your OneNote notebooks.

    Returns:
        Formatted list of notebooks with IDs and display names
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
async def getNotebook(notebook_id: str) -> str:
    """Get details of a specific notebook.

    Args:
        notebook_id: The ID of the notebook to retrieve

    Returns:
        Detailed notebook information
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
async def listSections(notebook_id: str) -> str:
    """List all sections in a notebook.

    Args:
        notebook_id: The ID of the notebook

    Returns:
        Formatted list of sections in the notebook
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
async def listPages(section_id: str) -> str:
    """List all pages in a section.

    Args:
        section_id: The ID of the section

    Returns:
        Formatted list of pages in the section
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
async def getPage(page_id: str) -> str:
    """Get the complete content of a specific page.

    This tool retrieves the full HTML content of a OneNote page,
    including all text, formatting, and embedded elements.

    Args:
        page_id: The ID of the page to retrieve

    Returns:
        Complete page content as HTML/markdown
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
async def createPage(notebook_id: str, title: str, content: str = "") -> str:
    """Create a new page in a notebook.

    Args:
        notebook_id: The ID of the notebook to create the page in
        title: The title of the new page
        content: Optional HTML content for the page

    Returns:
        Confirmation of page creation
    """
    try:
        result = await create_page(notebook_id, title, content)
        page_id = result.get("id", "unknown")
        return f"✅ Page '{title}' created successfully with ID: `{page_id}`"
    except Exception as e:
        return f"❌ Failed to create page: {e!s}"


@app.tool()
async def searchPages(query: str) -> str:
    """Search for pages across all notebooks.

    Args:
        query: Search query string

    Returns:
        List of matching pages
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
async def getNotebookTOC(notebook_id: str) -> str:
    """Generate a table of contents for a notebook.

    This tool creates a comprehensive overview of all sections and pages
    in a notebook, useful for navigation and understanding structure.

    Args:
        notebook_id: The ID of the notebook

    Returns:
        Formatted table of contents
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


def main():
    """Main entry point with unified transport handling (FastMCP 2.14.4+)."""
    from .transport import run_server

    run_server(app, server_name="onenote-mcp")


if __name__ == "__main__":
    main()
