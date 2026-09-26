"""FastMCP server for Microsoft OneNote integration."""

import asyncio
import base64
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
from fastmcp.tools.base import ToolResult
from prefab_ui import PrefabApp
from prefab_ui.components import Heading, Row, Text
from pydantic import Field
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from . import search_index
from .constants import AUTHORITY, CLIENT_ID, SCOPES, TOKEN_FILE_NAME
from .models import Notebook, Page, Section, TOCData, TOCPage, TOCSection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("onenote_mcp")
_SERVER_VERSION = "1.0.4"
_START_TIME = time.monotonic()

# Fire-and-forget shutdown tasks (stored to satisfy RUF006)
_shutdown_tasks: list[asyncio.Task] = []

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
TOKEN_FILE_PATH = PROJECT_ROOT / TOKEN_FILE_NAME

# Global state
_access_token: str | None = None
_graph_client: httpx.AsyncClient | None = None
_TOKEN_SET_AT: float = 0.0
_TOKEN_TTL_SECONDS = 3000.0  # refresh proactively after ~50 min (Graph gives ~60)

# MSAL token cache (access + refresh tokens). Lets the backend silently
# re-authenticate across restarts without another browser round-trip.
_CACHE_PATH = PROJECT_ROOT / ".msal-token-cache.bin"
_token_cache = msal.SerializableTokenCache()
try:
    if _CACHE_PATH.exists():
        _token_cache.deserialize(_CACHE_PATH.read_bytes().decode("utf-8"))
except Exception as exc:
    logger.warning("Ignoring corrupt MSAL cache: %s", exc)


def _save_cache() -> None:
    if _token_cache.has_state_changed:
        try:
            _CACHE_PATH.write_bytes(_token_cache.serialize().encode("utf-8"))
        except Exception as exc:
            logger.warning("Could not persist MSAL cache: %s", exc)


def _msal_app() -> msal.PublicClientApplication:
    return msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=_token_cache)


def try_silent_auth() -> str | None:
    """Use cached refresh token to get an access token without user action."""
    global _access_token
    try:
        app = _msal_app()
        accounts = app.get_accounts()
        if not accounts:
            return None
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            _save_cache()
            save_access_token(result["access_token"])
            logger.info("Silent auth succeeded")
            _log.info("auth", "silent refresh succeeded")
            return result["access_token"]
        _log.warn("auth", f"silent refresh empty: {(result or {}).get('error_description', 'no token')}")
    except Exception as exc:
        logger.warning("Silent auth failed: %s", exc)
        _log.warn("auth", f"silent refresh failed: {exc}")
    return None


def load_access_token() -> str | None:
    """Load access token: memory, silent refresh, file, environment.

    Silent refresh comes BEFORE the file because file tokens expire hourly
    while the MSAL cache (refresh token) survives - otherwise every backend
    restart + one hour means a dead session and a 401 wall.
    """
    global _access_token
    if _access_token and (time.time() - _TOKEN_SET_AT) < _TOKEN_TTL_SECONDS:
        return _access_token
    if _access_token:
        # Hourly expiry: memory token is stale, refresh before using it.
        _access_token = None
        _graph_client = None

    # Refresh cache first (no network when the cached token is still valid)
    try:
        if (silent := try_silent_auth()) is not None:
            return silent
    except Exception as exc:
        logger.warning("Silent auth attempt failed: %s", exc)

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
        logger.warning("Error reading access token file: %s", e)

    # Check environment variable
    if env_token := os.getenv("GRAPH_ACCESS_TOKEN"):
        _access_token = env_token.strip()
        return _access_token

    # Last resort: cached refresh token (survives restarts, no browser needed)
    return try_silent_auth()


def save_access_token(token: str) -> None:
    """Save access token to file."""
    global _access_token, _graph_client, _TOKEN_SET_AT
    _access_token = token
    _TOKEN_SET_AT = time.time()
    # Drop the cached Graph client: it was built with the previous token's
    # Authorization header and would otherwise keep 401ing after re-auth.
    _graph_client = None

    token_data = json.dumps({"token": token}, indent=2)
    TOKEN_FILE_PATH.write_text(token_data)
    logger.info("Access token saved to %s", TOKEN_FILE_PATH)


async def get_graph_client() -> httpx.AsyncClient:
    """Get or create Microsoft Graph API client."""
    global _graph_client
    if _graph_client:
        return _graph_client

    token = load_access_token()
    if not token:
        raise ValueError("No access token available. Please sign in first (Notebooks page, blue button).")

    _graph_client = httpx.AsyncClient(
        base_url="https://graph.microsoft.com/v1.0",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    return _graph_client


async def authenticate_device_code() -> dict[str, Any]:
    """Start device code authentication flow."""
    app = _msal_app()

    # Get device code (offline_access appended: device flow tolerates the
    # reserved scope and it yields a refresh token for silent re-auth)
    flow = app.initiate_device_flow(scopes=[*SCOPES, "offline_access"])
    if "user_code" not in flow:
        raise ValueError(f"Failed to create device flow: {flow.get('error_description', flow.get('error', 'unknown'))}")

    logger.info("To authenticate: %s (code: %s)", flow["verification_uri"], flow["user_code"])

    # Wait for user to complete authentication
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        _save_cache()
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
    """Get complete content of a specific page (metadata + HTML body)."""
    client = await get_graph_client()
    response = await client.get(f"/me/onenote/pages/{page_id}")
    response.raise_for_status()

    page_data = response.json()
    # The metadata endpoint has no body - the HTML lives at .../content.
    content = ""
    try:
        cr = await client.get(f"/me/onenote/pages/{page_id}/content", headers={"Accept": "text/html"})
        cr.raise_for_status()
        content = cr.text
    except Exception as exc:
        logger.warning("Page content fetch failed for %s: %s", page_id, exc)

    return Page(
        id=page_data["id"],
        title=page_data.get("title", f"Page {page_data['id'][:8]}"),
        createdDateTime=page_data["createdDateTime"],
        lastModifiedDateTime=page_data["lastModifiedDateTime"],
        self=page_data["self"],
        contentUrl=page_data["contentUrl"],
        content=content,
    )


def text_to_html(text: str) -> str:
    """Plain text -> semantic HTML (blank lines = paragraphs). Shared by
    create/append so the webapp and MCP tools behave identically."""
    import html as _html

    paras = (text or "").replace("\r\n", "\n").split("\n\n")
    blocks = "".join(f"<p>{_html.escape(p).replace(chr(10), '<br/>')}</p>" for p in paras if p.strip())
    return blocks or "<p></p>"


async def append_page_content(page_id: str, text: str) -> None:
    """Append plain-text paragraphs to the end of a OneNote page body."""
    client = await get_graph_client()
    commands = [{"target": "body", "action": "append", "position": "after", "content": text_to_html(text)}]
    response = await client.patch(f"/me/onenote/pages/{page_id}/content", json=commands)
    response.raise_for_status()


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
    """Search for pages across all notebooks (title match).

    Collection-wide page queries ($search and cross-notebook $filter) are
    refused for accounts with many sections (Graph 20266), so walk each
    notebook's TOC (section-scoped page lists) and match titles client-side.
    """
    needle = query.strip().lower()
    notebooks = await list_notebooks()
    hits: list[Page] = []
    for nb in notebooks:
        try:
            toc, _ = await get_notebook_toc(nb.id)
        except Exception as exc:
            logger.warning("TOC walk skipped notebook %s: %s", nb.id, exc)
            continue
        for section in toc.sections:
            for toc_page in section.pages:
                if needle in (toc_page.title or "").lower():
                    try:
                        hit = await get_page(toc_page.id)
                        hit.notebook = nb.displayName
                        hit.section = section.name
                        hits.append(hit)
                    except Exception as exc:
                        logger.warning("Search skipped page %s: %s", toc_page.id, exc)
    return hits


def select_recent(
    items: list[tuple[str, str, str, str, str]], days: int, now: float | None = None
) -> list[dict[str, str]]:
    """Pure filter: (id, title, notebook, section, modified_iso) -> recent first.

    Malformed/empty timestamps are skipped (never crash the feed on one bad row).
    """
    import datetime as _dt

    cutoff = (now if now is not None else time.time()) - days * 86400
    hits: list[tuple[float, dict[str, str]]] = []
    for pid, title, notebook, section, modified in items:
        try:
            ts = _dt.datetime.fromisoformat((modified or "").replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            continue
        if ts >= cutoff:
            hits.append(
                (ts, {"id": pid, "title": title, "notebook": notebook, "section": section, "modified": modified})
            )
    hits.sort(key=lambda h: h[0], reverse=True)
    return [h[1] for h in hits]


async def recent_pages(days: int = 7, limit: int = 50) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Walk all notebook TOCs, return recently-modified pages + scan stats."""
    days = max(1, min(days, 90))
    items: list[tuple[str, str, str, str, str]] = []
    scanned = {"notebooks": 0, "sections": 0}
    for nb in await list_notebooks():
        try:
            toc, _ = await get_notebook_toc(nb.id)
        except Exception as exc:
            logger.warning("Recent skipped notebook %s: %s", nb.id, exc)
            continue
        scanned["notebooks"] += 1
        for section in toc.sections:
            scanned["sections"] += 1
            for pg in section.pages:
                items.append((pg.id, pg.title, nb.displayName, section.name, pg.modified))
    return select_recent(items, days)[: max(1, min(limit, 200))], scanned


async def get_notebook_toc(notebook_id: str) -> tuple[TOCData, list[str]]:
    """Generate table of contents for a notebook (sections fetched in parallel).

    Returns (toc, warnings): slow/failing sections are skipped with a warning
    instead of failing the whole notebook (one 5s-timeout section must not
    torpedo a big TOC).
    """
    notebook = await get_notebook(notebook_id)
    sections = await list_sections(notebook_id)

    semaphore = asyncio.Semaphore(4)

    async def _section_pages(section: Section) -> TOCSection | None:
        try:
            async with semaphore:
                pages = await list_pages(section.id)
        except Exception as exc:
            logger.warning("TOC skipped slow section %s: %s", section.displayName, exc)
            return None
        return TOCSection(
            name=section.displayName,
            pageCount=len(pages),
            pages=[
                TOCPage(
                    title=page.title,
                    id=page.id,
                    created=page.createdDateTime,
                    modified=page.lastModifiedDateTime,
                )
                for page in pages
            ],
        )

    results = await asyncio.gather(*(_section_pages(s) for s in sections))
    toc_sections = [r for r in results if r is not None]
    total_pages = sum(s.pageCount for s in toc_sections)
    warnings = (
        [f"{len(sections) - len(toc_sections)} section(s) skipped (timed out)"]
        if len(toc_sections) != len(sections)
        else []
    )

    return TOCData(
        notebook=notebook.displayName,
        stats={"sections": len(sections), "pages": total_pages},
        sections=list(toc_sections),
    ), warnings


# Create FastMCP app
app = FastMCP(name="onenote-mcp", instructions="Microsoft OneNote integration via Model Context Protocol")

# Tool annotations (TOOL_DESIGN_STANDARDS.md §9 - dict format, FastMCP 3.x)
_READONLY = {"readonly": True}
_MUTATING = {}


@app.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "server": "onenote-mcp"})


@app.custom_route("/api/v1/health", methods=["GET"])
async def api_v1_health(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "server": "onenote-mcp",
            "version": _SERVER_VERSION,
            "uptime_seconds": int(time.monotonic() - _START_TIME),
            "tool_count": _tool_count(),
        }
    )


# ---- Webapp REST API (fleet SOTA endpoints) ----

# Adjacent fleet webapps, sourced from mcp-central-docs/operations/WEBAPP_PORTS.md.
# Single source of truth for the Apps Hub - the frontend never hardcodes ports.
_FLEET_APPS: tuple[dict[str, Any], ...] = (
    {"name": "teleconference-mcp", "port": 10886, "description": "Webapp frontend"},
    {"name": "myai", "port": 10888, "description": "Webapp frontend"},
    {"name": "obsidian-mcp", "port": 10890, "description": "Web dashboard frontend"},
    {"name": "yahboom-mcp", "port": 10893, "description": "Web dashboard frontend"},
    {"name": "dreame-mcp", "port": 10895, "description": "Web dashboard frontend"},
    {"name": "mywienerlinien", "port": 10896, "description": "Webapp dashboard"},
)

_TAGGED_SKILLS: list[dict[str, str]] = [{"name": "onenote", "uri": "skill://onenote"}]
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
    "onenote_append_page",
    "onenote_search_pages",
    "onenote_index_start",
    "onenote_index_status",
    "onenote_recent",
    "onenote_get_notebook_toc",
    "show_notebooks_card",
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
                "chat": True,
                "skills": True,
            },
            "tools": [t["name"] for t in _list_mcp_tools()],
        }
    )


@app.custom_route("/api/fleet/apps", methods=["GET"])
async def api_fleet_apps(request: Request) -> JSONResponse:
    return JSONResponse({"apps": list(_FLEET_APPS)})


@app.custom_route("/api/skills", methods=["GET"])
async def api_skills(request: Request) -> JSONResponse:
    return JSONResponse({"skills": _TAGGED_SKILLS})


@app.custom_route("/api/skills/{skill_name}", methods=["GET"])
async def api_skill_content(request: Request) -> JSONResponse:
    skill_name = request.path_params["skill_name"]
    skill_path = Path(__file__).parent / "skills" / skill_name / "SKILL.md"
    if skill_path.exists():
        return JSONResponse({"name": skill_name, "content": skill_path.read_text(encoding="utf-8")})
    return JSONResponse({"success": False, "error": "skill not found"}, status_code=404)


# Local LLM providers probed by /api/llm/* (kind: native ollama vs OpenAI-compatible).
_LLM_PROVIDERS: dict[str, dict[str, Any]] = {
    "ollama": {"port": 11434, "kind": "ollama", "models_path": "/api/tags"},
    "lm_studio": {"port": 1234, "kind": "openai", "models_path": "/v1/models"},
    "vllm": {"port": 8000, "kind": "openai", "models_path": "/v1/models"},
}


async def _probe_llm_providers() -> dict[str, dict[str, Any]]:
    """Probe local LLM providers; shared by discover/providers/models/onboarding."""
    providers: dict[str, dict[str, Any]] = {}

    async def _probe(name: str) -> None:
        port = _LLM_PROVIDERS[name]["port"]
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"http://127.0.0.1:{port}{_LLM_PROVIDERS[name]['models_path']}")
                if r.status_code != 200:
                    providers[name] = {"detected": False, "port": port, "models": []}
                    return
                data = r.json()
                if name == "ollama":
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                else:
                    models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
                providers[name] = {"detected": True, "port": port, "models": models}
        except Exception:
            providers[name] = {"detected": False, "port": port, "models": []}

    await asyncio.gather(*(_probe(name) for name in _LLM_PROVIDERS))
    return providers


@app.custom_route("/api/llm/discover", methods=["GET"])
async def api_llm_discover(request: Request) -> JSONResponse:
    providers = await _probe_llm_providers()

    ollama = providers.get("ollama", {})
    configured_model = (ollama.get("models") or [""])[0]
    return JSONResponse(
        {
            "ollama_detected": bool(ollama.get("detected")),
            "configured_model": configured_model,
            "providers": providers,
        }
    )


@app.custom_route("/api/llm/providers", methods=["GET"])
async def api_llm_providers(request: Request) -> JSONResponse:
    """Provider registry: local detected flags + model lists (never key bytes)."""
    providers = await _probe_llm_providers()
    return JSONResponse(
        {
            "providers": [
                {
                    "name": name,
                    "detected": info.get("detected", False),
                    "port": info.get("port"),
                    "models": info.get("models", []),
                }
                for name, info in providers.items()
            ]
        }
    )


@app.custom_route("/api/llm/models", methods=["GET"])
async def api_llm_models(request: Request) -> JSONResponse:
    """Model list for one provider (?provider=ollama); live when reachable."""
    name = request.query_params.get("provider", "ollama")
    if name not in _LLM_PROVIDERS:
        return JSONResponse(
            {"success": False, "error": f"unknown provider '{name}'"},
            status_code=404,
        )
    providers = await _probe_llm_providers()
    info = providers.get(name, {})
    return JSONResponse({"provider": name, "models": info.get("models", [])})


@app.custom_route("/api/llm/onboarding", methods=["GET"])
async def api_llm_onboarding(request: Request) -> JSONResponse:
    """Fresh-install starter facts + recommended path for the under-hero cue."""
    providers = await _probe_llm_providers()
    any_live = any(info.get("detected") for info in providers.values())
    first_model = ""
    for info in providers.values():
        if info.get("detected") and info.get("models"):
            first_model = info["models"][0]
            break
    return JSONResponse(
        {
            "local_llm_available": any_live,
            "recommended_model": first_model,
            "facts": [
                "Chat runs through a backend proxy - keys and provider URLs never leave this server.",
                "Install Ollama (port 11434) or LM Studio (port 1234) for free local chat.",
                "Pick the provider + model on the Settings page; Chat uses it automatically.",
            ],
            "recommended_path": (
                "open Settings, confirm a detected provider, then use Chat"
                if any_live
                else "install Ollama from https://ollama.com, pull a model, then return to Chat"
            ),
        }
    )


@app.custom_route("/api/llm/chat", methods=["POST"])
async def api_llm_chat(request: Request) -> JSONResponse:
    """Backend chat proxy (the ONLY path Chat uses) - keys never leave the server."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    provider = str(body.get("provider") or "ollama")
    model = str(body.get("model") or "")
    messages = body.get("messages") or []
    if provider not in _LLM_PROVIDERS:
        return JSONResponse({"success": False, "error": f"unknown provider '{provider}'"}, status_code=404)
    if not model or not isinstance(messages, list) or not messages:
        return JSONResponse(
            {"success": False, "error": "model (str) and messages (non-empty list) required"},
            status_code=400,
        )
    kind = _LLM_PROVIDERS[provider]["kind"]
    port = _LLM_PROVIDERS[provider]["port"]
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if kind == "ollama":
                r = await client.post(
                    f"http://127.0.0.1:{port}/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                )
            else:  # OpenAI-compatible (LM Studio, vLLM)
                r = await client.post(
                    f"http://127.0.0.1:{port}/v1/chat/completions",
                    json={"model": model, "messages": messages, "stream": False},
                )
        if r.status_code != 200:
            return JSONResponse({"success": False, "error": f"provider HTTP {r.status_code}"}, status_code=502)
        data = r.json()
        if kind == "ollama":
            content = (data.get("message") or {}).get("content", "")
        else:
            choices = data.get("choices") or []
            content = ((choices[0].get("message") if choices else {}) or {}).get("content", "")
        return JSONResponse({"success": True, "content": content})
    except Exception as exc:
        logger.exception("LLM proxy error: %s", exc)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=502)


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
    )  # type: ignore[return-value]


# ---- Webapp auth (non-blocking device-code flow) ----

_auth_flows: dict[str, dict[str, Any]] = {}


def _start_auth_flow() -> dict[str, Any]:
    app = _msal_app()
    flow = app.initiate_device_flow(scopes=[*SCOPES, "offline_access"])
    if "user_code" not in flow:
        raise ValueError(f"Failed to create device flow: {flow.get('error_description', flow.get('error', 'unknown'))}")
    flow_id = flow.get("device_code", "")[-8:]
    _auth_flows[flow_id] = {"flow": flow, "status": "pending", "result": None}
    _log.info("auth", f"device flow started (user_code={flow['user_code']})")

    def _wait():
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            _save_cache()
            save_access_token(result["access_token"])
            account = result.get("id_token_claims", {}).get("preferred_username", "")
            _log.info("auth", f"device flow authorized ({account})")
            _auth_flows[flow_id]["result"] = {
                "success": True,
                "account": account,
            }
            _auth_flows[flow_id]["status"] = "authorized"
        else:
            err = result.get("error_description", "Authentication failed")
            _log.error("auth", f"device flow failed: {err}")
            _auth_flows[flow_id]["result"] = {
                "success": False,
                "error": err,
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


# ---- Browser redirect login (auth-code flow) ----
# Device-code flow yields MSA tokens the OneNote workload rejects (40001);
# the browser redirect flow (same kind Graph Explorer uses) yields working
# tokens. Requires the app registration to allow the localhost redirect
# (portal: Authentication -> Mobile and desktop applications -> http://localhost).

_auth_code_flows: dict[str, dict[str, Any]] = {}

REDIRECT_URI = os.environ.get("ONENOTE_REDIRECT_URI", "http://localhost:10907/api/auth/callback")


@app.custom_route("/api/auth/login", methods=["GET"])
async def api_auth_login(request: Request) -> JSONResponse:
    """Start browser login. Returns auth_uri for the user to open."""
    now = time.time()
    for state in [s for s, e in _auth_code_flows.items() if now - e["started"] > 600]:
        _auth_code_flows.pop(state, None)
    app = _msal_app()
    flow = app.initiate_auth_code_flow(SCOPES, redirect_uri=REDIRECT_URI)
    if "auth_uri" not in flow:
        err = flow.get("error_description", flow.get("error", "unknown"))
        _log.error("auth", f"browser login start failed: {err}")
        return JSONResponse({"success": False, "error": err}, status_code=500)
    _auth_code_flows[flow["state"]] = {"flow": flow, "started": now}
    _log.info("auth", "browser login started")
    return JSONResponse({"success": True, "auth_uri": flow["auth_uri"]})


def _auth_page(title: str, message: str, ok: bool) -> "HTMLResponse":
    import html as _html

    color = "#34d399" if ok else "#f87171"
    body = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{_html.escape(title)}</title></head>
<body style="background:#020617;color:#e2e8f0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="text-align:center"><h2 style="color:{color}">{_html.escape(title)}</h2><p>{_html.escape(message)}</p>
<p style="color:#64748b">You can close this tab and return to the app.</p></div>
<script>try{{if({str(ok).lower()})setTimeout(function(){{window.close()}},3000);}}catch(e){{}}</script>
</body></html>"""
    return HTMLResponse(body, status_code=200 if ok else 400)


@app.custom_route("/api/auth/callback", methods=["GET"])
async def api_auth_callback(request: Request) -> "HTMLResponse":
    """Microsoft redirects here after browser login. Exchanges the code."""
    params = dict(request.query_params)
    if "error" in params:
        _log.error("auth", f"browser login refused: {params.get('error_description', params['error'])}")
        return _auth_page("Sign-in refused", params.get("error_description", params["error"]), ok=False)
    entry = _auth_code_flows.pop(params.get("state", ""), None)
    if not entry:
        _log.error(
            "auth",
            "callback with unknown/expired state - backend likely restarted after login started",
        )
        return _auth_page("Login expired", "No matching login session - start sign-in again.", ok=False)
    app = _msal_app()
    try:
        # Modern MSAL API: flow first, response second. (The legacy
        # acquire_token_by_authorization_code(code, scopes) takes a scope
        # list second - passing the flow dict raises "Invalid parameter type".)
        result = app.acquire_token_by_auth_code_flow(entry["flow"], dict(params))
    except Exception as exc:
        import traceback as _tb

        logger.exception("auth code exchange crashed: %s", exc)
        _log.error("auth", f"code exchange crashed: {exc}\n{_tb.format_exc()[-1500:]}")
        return _auth_page("Sign-in failed", f"Code exchange crashed: {exc}", ok=False)
    if "access_token" in result:
        _save_cache()
        save_access_token(result["access_token"])
        account = result.get("id_token_claims", {}).get("preferred_username", "")
        _log.info("auth", f"browser login authorized ({account})")
        return _auth_page("Signed in", f"Connected as {account or 'your Microsoft account'}.", ok=True)
    err = result.get("error_description", "Authorization failed")
    _log.error("auth", f"browser login failed: {err}")
    return _auth_page("Sign-in failed", err, ok=False)


def _decode_jwt_claims(token: str) -> dict[str, Any] | None:
    """Decode JWT payload WITHOUT signature verification (diagnostics only)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except Exception:
        return None


@app.custom_route("/api/auth/debug", methods=["GET"])
async def api_auth_debug(request: Request) -> JSONResponse:
    """Local-only auth diagnostics. Returns no secrets - safe to paste into
    issues. Shows which client ID is active, token shape/age, and (for JWTs)
    audience, scopes, appid, tenant, account, and expiry."""
    token = load_access_token()
    info: dict[str, Any] = {
        "client_id_suffix": CLIENT_ID[-4:],
        "authority": AUTHORITY,
        "scopes_requested": SCOPES,
        "token_present": bool(token),
        "token_format": None,
        "token_age_seconds": None,
        "token_cache_present": _CACHE_PATH.exists(),
        "graph_client_cached": _graph_client is not None,
    }
    if token:
        info["token_format"] = "jwt" if token.startswith("eyJ") else "opaque"
        try:
            info["token_age_seconds"] = int(time.time() - TOKEN_FILE_PATH.stat().st_mtime)
        except OSError:
            info["token_age_seconds"] = None  # env-provided token, no file
        claims = _decode_jwt_claims(token)
        if claims:
            exp = claims.get("exp")
            now = int(time.time())
            info["jwt"] = {
                "aud": claims.get("aud"),
                "scp": claims.get("scp"),
                "appid": claims.get("appid"),
                "tid": claims.get("tid"),
                "account": claims.get("preferred_username") or claims.get("upn"),
                "expires_in_seconds": (exp - now) if isinstance(exp, int) else None,
            }
    return JSONResponse(info)


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
        toc, warnings = await get_notebook_toc(notebook_id)
        return JSONResponse({"success": True, "toc": toc.model_dump(), "warnings": warnings})
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


@app.custom_route("/api/pages/{page_id}/append", methods=["PATCH"])
async def api_append_page(request: Request) -> JSONResponse:
    page_id = request.path_params["page_id"]
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
    content = str(body.get("content") or "")
    if not content.strip():
        return JSONResponse({"success": False, "error": "content (plain text) required"}, status_code=400)
    try:
        await append_page_content(page_id, content)
        return JSONResponse({"success": True, "page_id": page_id})
    except Exception as exc:
        return _error_response(exc)


@app.custom_route("/api/search", methods=["GET"])
async def api_search_pages(request: Request) -> JSONResponse:
    query = request.query_params.get("q", "")
    mode = request.query_params.get("mode", "title")
    if not query:
        return JSONResponse({"success": False, "error": "q query param required"}, status_code=400)
    try:
        if mode == "fulltext":
            hits = search_index.search_fulltext(query)
            if not hits and search_index.index_count() == 0:
                return JSONResponse(
                    {
                        "success": True,
                        "query": query,
                        "mode": "fulltext",
                        "pages": [],
                        "warning": "Full-text index is empty - build it (POST /api/index) or use mode=title.",
                    }
                )
            return JSONResponse(
                {"success": True, "query": query, "mode": "fulltext", "pages": [h.model_dump() for h in hits]}
            )
        pages = await search_pages(query)
        return JSONResponse(
            {"success": True, "query": query, "mode": "title", "pages": [p.model_dump() for p in pages]}
        )
    except Exception as exc:
        return _error_response(exc)


async def _page_html(page_id: str) -> str:
    return (await get_page(page_id)).content or ""


@app.custom_route("/api/recent", methods=["GET"])
async def api_recent_pages(request: Request) -> JSONResponse:
    try:
        days = int(request.query_params.get("days", "7"))
    except ValueError:
        days = 7
    try:
        limit = int(request.query_params.get("limit", "50"))
    except ValueError:
        limit = 50
    try:
        pages, scanned = await recent_pages(days, limit)
        return JSONResponse({"success": True, "days": days, "pages": pages, "scanned": scanned})
    except Exception as exc:
        return _error_response(exc)


_BACKGROUND_TASKS: set[asyncio.Task] = set()


def _spawn_index_build() -> bool:
    """Start the FTS index build unless one runs. Returns True if started."""
    if search_index.job_status()["state"] == "running":
        return False
    task = asyncio.create_task(
        search_index.build_index(list_notebooks, get_notebook_toc, _page_html),
        name="onenote-fts-index",
    )
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    return True


@app.custom_route("/api/index", methods=["POST"])
async def api_index_start(request: Request) -> JSONResponse:
    """Start (or restart) the full-text index build in the background."""
    if not _spawn_index_build():
        return JSONResponse({"success": True, "status": "already running"})
    return JSONResponse({"success": True, "status": "started"})


@app.custom_route("/api/index/status", methods=["GET"])
async def api_index_status(request: Request) -> JSONResponse:
    return JSONResponse({"success": True, **search_index.job_status()})


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


# MCP Bridge - proxy remote MCP servers via ProxyProvider
MCP_BRIDGE_URLS = os.environ.get("MCP_BRIDGE_URLS", "")
if MCP_BRIDGE_URLS:
    for url in MCP_BRIDGE_URLS.split(","):
        url = url.strip()
        if url:
            app.add_provider(create_proxy(url))


@app.tool(annotations=_MUTATING)
async def authenticate() -> str:
    """Start the Microsoft authentication flow using device code.

    This tool initiates the OAuth 2.0 device code flow for Microsoft Graph API.
    The user will be provided with a URL and code to complete authentication
    in their browser.

    ## Return Format
    Confirmation string: "✅ Authentication successful" or "❌ ..." on failure.

    ## Examples
    authenticate()
    """
    try:
        result = await authenticate_device_code()
        return f"✅ {result['message']}"
    except Exception as e:
        return f"❌ Authentication failed: {e!s}"


@app.tool(annotations=_MUTATING)
async def onenote_save_access_token(
    token: Annotated[str, Field(description="The Microsoft Graph access token to save")],
) -> str:
    """Save a Microsoft Graph access token for later use.

    Persists the token to the local token file so subsequent tools can call the Graph API.

    ## Return Format
    A confirmation string: "✅ Access token saved successfully" or "❌ ..." on failure.

    ## Examples
    onenote_save_access_token(token="eyJhbGciOi...")  # paste a token from az login / Graph explorer
    """
    try:
        save_access_token(token)
        return "✅ Access token saved successfully"
    except Exception as e:
        return f"❌ Failed to save token: {e!s}"


@app.tool(annotations=_READONLY)
async def onenote_list_notebooks() -> str:
    """List all Microsoft OneNote notebooks accessible to the signed-in account.

    ## Return Format
    Markdown string: "📓 Your OneNote Notebooks:" followed by numbered notebooks with ID.

    ## Examples
    onenote_list_notebooks()
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


@app.tool(annotations=_READONLY)
async def onenote_get_notebook(
    notebook_id: Annotated[str, Field(description="The ID of the notebook to retrieve")],
) -> str:
    """Get details of a specific OneNote notebook.

    ## Return Format
    Markdown string with notebook name, ID, sections URL, and section groups URL.

    ## Examples
    onenote_get_notebook(notebook_id="0-ABC123...")
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


@app.tool(annotations=_READONLY)
async def onenote_list_sections(notebook_id: Annotated[str, Field(description="The ID of the notebook")]) -> str:
    """List all sections in a OneNote notebook.

    ## Return Format
    Markdown string: "📂 Sections in notebook:" with numbered sections and their page URLs.

    ## Examples
    onenote_list_sections(notebook_id="0-ABC123...")
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


@app.tool(annotations=_READONLY)
async def onenote_list_pages(section_id: Annotated[str, Field(description="The ID of the section")]) -> str:
    """List all pages in a OneNote section.

    ## Return Format
    Markdown string: "📄 Pages in section:" with numbered pages, created and modified dates.

    ## Examples
    onenote_list_pages(section_id="0-SEC123...")
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


@app.tool(annotations=_READONLY)
async def onenote_get_page(page_id: Annotated[str, Field(description="The ID of the page to retrieve")]) -> str:
    """Get the complete HTML content of a OneNote page.

    Retrieves the full page content including text, formatting, and embedded elements.

    ## Return Format
    Markdown string: "📄 Page Content:" with title, ID, timestamps, and the raw HTML body.

    ## Examples
    onenote_get_page(page_id="0-PG123...")
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


@app.tool(annotations=_MUTATING)
async def onenote_create_page(
    notebook_id: Annotated[str, Field(description="The ID of the notebook to create the page in")],
    title: Annotated[str, Field(description="The title of the new page")],
    content: Annotated[str, Field(description="Optional HTML content for the page")] = "",
) -> str:
    """Create a new page in a OneNote notebook.

    ## Return Format
    Confirmation string: "✅ Page '<title>' created successfully with ID: `<id>`".

    ## Examples
    onenote_create_page(notebook_id="0-ABC123...", title="Meeting Notes", content="<h1>Notes</h1><p>...</p>")
    """
    try:
        result = await create_page(notebook_id, title, content)
        page_id = result.get("id", "unknown")
        return f"✅ Page '{title}' created successfully with ID: `{page_id}`"
    except Exception as e:
        return f"❌ Failed to create page: {e!s}"


@app.tool(annotations=_MUTATING)
async def onenote_append_page(
    page_id: Annotated[str, Field(description="The ID of the page to append to")],
    content: Annotated[str, Field(description="Plain text to append (blank lines = paragraphs)")],
) -> str:
    """Append plain text to the end of a OneNote page.

    ## Return Format
    Confirmation string: "✅ Appended to page `<id>`".

    ## Examples
    onenote_append_page(page_id="0-PG123...", content="Follow-up note\\n\\nSecond paragraph")
    """
    try:
        if not content.strip():
            return "❌ Nothing to append - content is empty."
        await append_page_content(page_id, content)
        return f"✅ Appended to page `{page_id}`"
    except Exception as e:
        return f"❌ Failed to append: {e!s}"


@app.tool(annotations=_READONLY)
async def onenote_search_pages(
    query: Annotated[str, Field(description="Search query string")],
    mode: Annotated[
        str,
        Field(
            description="Search mode: 'title' (always available) or 'fulltext' (needs the index; see onenote_index_start)"
        ),
    ] = "title",
) -> str:
    """Search for pages across all OneNote notebooks.

    Two modes: 'title' matches page titles via TOC walk (always available);
    'fulltext' queries the local FTS index over page bodies (build it first).

    ## Return Format
    Markdown string: "🔍 Search Results for '<query>':" with numbered matching pages.

    ## Examples
    onenote_search_pages(query="quarterly report")
    onenote_search_pages(query="hiking checklist", mode="fulltext")
    """
    try:
        items: list[tuple[str, str, str, str, str]] = []
        if mode == "fulltext":
            for hit in search_index.search_fulltext(query):
                items.append((hit.title, hit.id, hit.notebook, hit.section, hit.snippet))
            if not items and search_index.index_count() == 0:
                return "Full-text index is empty - run onenote_index_start first (or search mode='title')."
        else:
            for page in await search_pages(query):
                items.append((page.title, page.id, page.notebook or "", page.section or "", ""))
        if not items:
            return f"No pages found matching query: '{query}'"

        result = f"🔍 Search Results for '{query}':\n\n"
        for i, (title, pid, notebook, section, snippet) in enumerate(items, 1):
            where = f"{notebook} / {section}".strip(" /")
            result += f"{i}. **{title}**" + (f" ({where})" if where else "") + "\n"
            result += f"   ID: `{pid}`\n"
            if snippet:
                result += f"   …{snippet}…\n"
            result += "\n"

        return result
    except Exception as e:
        return f"❌ Search failed: {e!s}"


@app.tool(annotations=_READONLY)
async def onenote_recent(
    days: Annotated[int, Field(description="Lookback window in days (1-90)")] = 7,
) -> str:
    """List recently modified pages across all notebooks.

    The domain-inbox answer to "what changed": TOC walk, newest first.

    ## Return Format
    Markdown string with dated page entries (title, notebook/section, id).

    ## Examples
    onenote_recent()
    onenote_recent(days=30)
    """
    try:
        pages, scanned = await recent_pages(days)
        if not pages:
            return f"No pages modified in the last {days} days."
        lines = [f"🕘 Recently modified (last {days} days, {scanned['notebooks']} notebooks scanned):\n"]
        for p in pages:
            day = (p["modified"] or "")[:10]
            lines.append(f"- **{p['title']}** ({p['notebook']} / {p['section']}, {day}) `{p['id']}`")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Recent failed: {e!s}"


@app.tool(annotations=_READONLY)
async def onenote_index_start() -> str:
    """Build (or refresh) the local full-text search index.

    Walks all notebooks and indexes page bodies into SQLite FTS5 (skips
    unchanged pages). Runs in the background - check onenote_index_status.

    ## Return Format
    Markdown string confirming started/already-running.

    ## Examples
    onenote_index_start()
    """
    if not _spawn_index_build():
        return "Index build already running - check onenote_index_status."
    return "Index build started in the background - check onenote_index_status for progress."


@app.tool(annotations=_READONLY)
async def onenote_index_status() -> str:
    """Show full-text index build progress and coverage.

    ## Return Format
    Markdown string with state, pages done/total, indexed page count.

    ## Examples
    onenote_index_status()
    """
    st = search_index.job_status()
    return (
        f"Index state: {st['state']} - {st['done']}/{st['total']} processed, "
        f"{st['indexed_pages']} pages searchable." + (f" Error: {st['error']}" if st.get("error") else "")
    )


@app.tool(annotations=_READONLY)
async def onenote_get_notebook_toc(notebook_id: Annotated[str, Field(description="The ID of the notebook")]) -> str:
    """Generate a table of contents for a OneNote notebook.

    Creates a comprehensive overview of all sections and pages, useful for navigation.

    ## Return Format
    Markdown string: "📚 Table of Contents: <notebook>" with stats and per-section page lists.

    ## Examples
    onenote_get_notebook_toc(notebook_id="0-ABC123...")
    """
    try:
        toc, warnings = await get_notebook_toc(notebook_id)

        result = f"""📚 Table of Contents: {toc.notebook}

**Stats:** {toc.stats["sections"]} sections, {toc.stats["pages"]} pages

"""

        for section in toc.sections:
            result += f"## 📂 {section.name} ({section.pageCount} pages)\n\n"

            for page in section.pages:
                created_date = page.created.split("T")[0]  # Just the date part
                result += f"- **{page.title}** _{created_date}_\n"

            result += "\n"

        if warnings:
            result += "\n⚠️ " + " ".join(warnings) + "\n"
        return result
    except Exception as e:
        return f"❌ Failed to generate TOC: {e!s}"


@app.tool(annotations={"destructive": True})
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


@app.tool(annotations=_READONLY)
async def onenote_help() -> str:
    """List the available OneNote MCP tools and when to use each.

    ## Return Format
    Markdown string enumerating the 17 tools with one-line usage notes.

    ## Examples
    onenote_help()
    """
    return """📚 **OneNote MCP tools:**
- `authenticate` - sign in with Microsoft (device-code flow)
- `onenote_save_access_token` - store a Graph token manually
- `onenote_list_notebooks` - all notebooks
- `onenote_get_notebook` - notebook details
- `onenote_list_sections` - sections of a notebook
- `onenote_list_pages` - pages of a section
- `onenote_get_page` - full HTML content of a page
- `onenote_create_page` - add a page with HTML body
- `onenote_append_page` - append plain text to a page
- `onenote_search_pages` - title or full-text search across notebooks
- `onenote_index_start` - build the full-text index (background)
- `onenote_index_status` - index progress and coverage
- `onenote_recent` - recently modified pages (domain inbox)
- `onenote_get_notebook_toc` - sections + pages overview
- `show_notebooks_card` - notebooks as an in-chat Prefab card
- `shutdown_server` - stop the server"""


@app.tool(annotations=_READONLY)
async def show_notebooks_card() -> ToolResult:
    """Show the user's OneNote notebooks as a rich in-chat card.

    ## Return Format
    ToolResult: PrefabApp card with one row per notebook, plus a plain-text
    markdown fallback for hosts that do not render apps.

    ## Examples
    show_notebooks_card()
    """
    try:
        notebooks = await list_notebooks()
    except Exception as e:
        return ToolResult(content=f"❌ Failed to list notebooks: {e!s}")
    if not notebooks:
        return ToolResult(content="No notebooks found")
    lines = "📓 Your OneNote Notebooks:\n\n"
    lines += "\n".join(f"- **{n.displayName}** (`{n.id}`)" for n in notebooks)
    with PrefabApp(title="OneNote Notebooks") as card:
        Heading(f"{len(notebooks)} notebooks")
        for notebook in notebooks:
            Row(children=[Text(notebook.displayName), Text(notebook.id)])
    return ToolResult(content=lines, structured_content=card)


@app.prompt()
def onenote_triage() -> str:
    """Guided triage prompt: find the right notebook, section, or page.

    ## Return Format
    Markdown prompt text steering discovery-first navigation.

    ## Examples
    onenote_triage()
    """
    return (
        "Help the user triage their OneNote request. First decide the intent: "
        "DISCOVER (list notebooks with onenote_list_notebooks, then drill with "
        "onenote_list_sections / onenote_list_pages), RETRIEVE (search with "
        "onenote_search_pages, then read hits with onenote_get_page), MAP "
        "(onenote_get_notebook_toc for a structural overview), or CAPTURE "
        "(onenote_create_page with semantic HTML). Ask one short clarifying "
        "question when the target notebook is ambiguous; otherwise proceed and "
        "show stable IDs at every step so follow-up calls can address items."
    )


@app.resource("skill://onenote")
def onenote_skill() -> str:
    """The onenote-mcp skill - how to use the server effectively."""
    skill_path = Path(__file__).parent / "skills" / "onenote" / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return (
        "OneNote MCP: list notebooks with onenote_list_notebooks(), explore with "
        "onenote_get_notebook_toc(), read pages with onenote_get_page()."
    )


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
