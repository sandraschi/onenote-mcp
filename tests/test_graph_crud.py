"""Notebook/section/page CRUD against a mocked Microsoft Graph (no network, no live OneNote)."""

import json

import httpx
import pytest

from onenote_mcp import server

GRAPH = "https://graph.microsoft.com/v1.0"
NB = {
    "id": "nb1",
    "displayName": "Thesis",
    "self": f"{GRAPH}/me/onenote/notebooks/nb1",
    "sectionsUrl": f"{GRAPH}/me/onenote/notebooks/nb1/sections",
    "sectionGroupsUrl": f"{GRAPH}/me/onenote/notebooks/nb1/sectionGroups",
}
SEC = {"id": "sec1", "displayName": "Notes", "pagesUrl": f"{GRAPH}/me/onenote/sections/sec1/pages", "self": "s"}


@pytest.fixture
def graph(monkeypatch):
    """Route server.get_graph_client() to a MockTransport; collect every request made."""
    calls: list[httpx.Request] = []
    routes: dict[tuple[str, str], httpx.Response | callable] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        route = routes.get((request.method, request.url.path))
        if route is None:
            return httpx.Response(404, json={"error": {"message": f"no mock for {request.method} {request.url.path}"}})
        return route(request) if callable(route) else route

    client = httpx.AsyncClient(base_url=GRAPH, transport=httpx.MockTransport(handler))

    async def fake_client():
        return client

    monkeypatch.setattr(server, "get_graph_client", fake_client)
    return calls, routes


def _body(request: httpx.Request):
    return json.loads(request.content)


# ---- name validation -------------------------------------------------------------------------


def test_validate_name_rules():
    ok = server.validate_name("  Thesis  ", "Notebook", 128, server._NOTEBOOK_NAME_FORBIDDEN)
    assert ok == "Thesis"
    with pytest.raises(ValueError, match="empty"):
        server.validate_name("   ", "Notebook", 128, server._NOTEBOOK_NAME_FORBIDDEN)
    with pytest.raises(ValueError, match="at most 50"):
        server.validate_name("x" * 51, "Section", 50, server._SECTION_NAME_FORBIDDEN)
    with pytest.raises(ValueError, match="/"):
        server.validate_name("a/b", "Notebook", 128, server._NOTEBOOK_NAME_FORBIDDEN)


def test_ampersand_allowed_in_notebook_but_not_section():
    assert server.validate_name("R&D", "Notebook", 128, server._NOTEBOOK_NAME_FORBIDDEN) == "R&D"
    with pytest.raises(ValueError, match="&"):
        server.validate_name("R&D", "Section", 50, server._SECTION_NAME_FORBIDDEN)


# ---- create notebook / section / section group -------------------------------------------------


@pytest.mark.asyncio
async def test_create_notebook_posts_display_name(graph):
    calls, routes = graph
    routes[("POST", "/v1.0/me/onenote/notebooks")] = httpx.Response(201, json=NB)
    out = await server.onenote_create_notebook(name=" Thesis ")
    assert "✅" in out and "nb1" in out
    assert _body(calls[0]) == {"displayName": "Thesis"}


@pytest.mark.asyncio
async def test_create_notebook_bad_name_never_calls_graph(graph):
    calls, _ = graph
    out = await server.onenote_create_notebook(name="bad:name")
    assert out.startswith("❌ Failed to create notebook")
    assert calls == []


@pytest.mark.asyncio
async def test_create_section_and_group_paths(graph):
    calls, routes = graph
    routes[("POST", "/v1.0/me/onenote/notebooks/nb1/sections")] = httpx.Response(201, json=SEC)
    routes[("POST", "/v1.0/me/onenote/notebooks/nb1/sectionGroups")] = httpx.Response(
        201, json={"id": "sg1", "displayName": "Archive"}
    )
    assert "sec1" in await server.onenote_create_section(notebook_id="nb1", name="Notes")
    assert "sg1" in await server.onenote_create_section_group(notebook_id="nb1", name="Archive")
    assert [c.url.path for c in calls] == [
        "/v1.0/me/onenote/notebooks/nb1/sections",
        "/v1.0/me/onenote/notebooks/nb1/sectionGroups",
    ]


@pytest.mark.asyncio
async def test_graph_error_is_returned_as_string(graph):
    _, routes = graph
    routes[("POST", "/v1.0/me/onenote/notebooks/nb1/sections")] = httpx.Response(409, json={"error": "dup"})
    out = await server.onenote_create_section(notebook_id="nb1", name="Notes")
    assert out.startswith("❌ Failed to create section")


# ---- pagination --------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_pages_follows_next_link(graph):
    calls, routes = graph

    def page(i):
        return {
            "id": f"p{i}",
            "title": f"T{i}",
            "createdDateTime": "c",
            "lastModifiedDateTime": "m",
            "self": "s",
            "contentUrl": "u",
        }

    routes[("GET", "/v1.0/me/onenote/sections/sec1/pages")] = httpx.Response(
        200, json={"value": [page(1), page(2)], "@odata.nextLink": f"{GRAPH}/me/onenote/sections/sec1/pages2"}
    )
    routes[("GET", "/v1.0/me/onenote/sections/sec1/pages2")] = httpx.Response(200, json={"value": [page(3)]})
    pages = await server.list_pages("sec1")
    assert [p.id for p in pages] == ["p1", "p2", "p3"]
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_get_all_respects_cap(graph):
    _, routes = graph
    routes[("GET", "/v1.0/x")] = httpx.Response(200, json={"value": [{"id": i} for i in range(10)]})
    assert len(await server._get_all("/x", cap=4)) == 4


# ---- create_page (endpoint fix) ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_page_resolves_default_section_and_escapes_title(graph):
    calls, routes = graph
    routes[("GET", "/v1.0/me/onenote/notebooks/nb1/sections")] = httpx.Response(
        200, json={"value": [{"id": "first"}, {"id": "dflt", "isDefault": True}]}
    )
    routes[("POST", "/v1.0/me/onenote/sections/dflt/pages")] = httpx.Response(201, json={"id": "pg1"})
    out = await server.onenote_create_page(notebook_id="nb1", title="<b>x</b> & y", content="<p>hi</p>")
    assert "pg1" in out
    post = calls[-1]
    assert post.url.path == "/v1.0/me/onenote/sections/dflt/pages"
    assert "<title>&lt;b&gt;x&lt;/b&gt; &amp; y</title>" in post.content.decode()
    assert not any("/notebooks/nb1/pages" in str(c.url) for c in calls)


@pytest.mark.asyncio
async def test_create_page_explicit_section_skips_lookup(graph):
    calls, routes = graph
    routes[("POST", "/v1.0/me/onenote/sections/sec9/pages")] = httpx.Response(201, json={"id": "pg2"})
    await server.onenote_create_page(notebook_id="nb1", title="T", section_id="sec9")
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_create_page_empty_notebook_gives_actionable_error(graph):
    _, routes = graph
    routes[("GET", "/v1.0/me/onenote/notebooks/nb1/sections")] = httpx.Response(200, json={"value": []})
    out = await server.onenote_create_page(notebook_id="nb1", title="T")
    assert "onenote_create_section" in out


# ---- update / delete page ----------------------------------------------------------------------


def test_build_patch_command_validation():
    assert server.build_patch_command("body", "append", "<p>x</p>", None) == {
        "target": "body",
        "action": "append",
        "content": "<p>x</p>",
    }
    assert server.build_patch_command("#p1", "delete", "ignored", None) == {"target": "#p1", "action": "delete"}
    with pytest.raises(ValueError, match="action"):
        server.build_patch_command("body", "explode", "x", None)
    with pytest.raises(ValueError, match="content is required"):
        server.build_patch_command("body", "replace", "  ", None)
    with pytest.raises(ValueError, match="position"):
        server.build_patch_command("#p1", "insert", "x", "sideways")
    with pytest.raises(ValueError, match="target"):
        server.build_patch_command(" ", "append", "x", None)


@pytest.mark.asyncio
async def test_update_page_sends_single_command_array(graph):
    calls, routes = graph
    routes[("PATCH", "/v1.0/me/onenote/pages/pg1/content")] = httpx.Response(204)
    out = await server.onenote_update_page(
        page_id="pg1", target="#p1", action="insert", content="<p>new</p>", position="before"
    )
    assert "✅" in out
    assert _body(calls[0]) == [{"target": "#p1", "action": "insert", "content": "<p>new</p>", "position": "before"}]


@pytest.mark.asyncio
async def test_delete_page_success_and_not_found(graph):
    calls, routes = graph
    routes[("DELETE", "/v1.0/me/onenote/pages/pg1")] = httpx.Response(204)
    assert "deleted" in await server.onenote_delete_page(page_id="pg1")
    assert calls[0].method == "DELETE"
    out = await server.onenote_delete_page(page_id="gone")
    assert out.startswith("❌ Failed to delete page")


# ---- copy section ------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_copy_section_returns_operation_and_polls(graph):
    calls, routes = graph
    op = f"{GRAPH}/me/onenote/operations/copy-1"
    routes[("POST", "/v1.0/me/onenote/sections/sec1/copyToNotebook")] = httpx.Response(
        202, headers={"Operation-Location": op}
    )
    routes[("GET", "/v1.0/me/onenote/operations/copy-1")] = httpx.Response(
        200, json={"status": "completed", "resourceId": "newsec"}
    )
    out = await server.onenote_copy_section(section_id="sec1", destination_notebook_id="nb2", rename_as="Copy")
    assert op in out
    assert _body(calls[0]) == {"id": "nb2", "renameAs": "Copy"}
    status = await server.onenote_copy_status(operation_url=op)
    assert "completed" in status and "newsec" in status


@pytest.mark.asyncio
async def test_copy_status_rejects_foreign_url(graph):
    calls, _ = graph
    out = await server.onenote_copy_status(operation_url="https://evil.example/steal")
    assert out.startswith("❌") and calls == []


def test_version_sources_agree():
    import tomllib
    from pathlib import Path

    import onenote_mcp

    pyproject = tomllib.loads((Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8"))
    assert onenote_mcp.__version__ == server._SERVER_VERSION == pyproject["project"]["version"]
    assert server.app.version == server._SERVER_VERSION  # what MCP initialize reports


# ---- tool surface + annotations (the Glama complaint) ------------------------------------------

NEW_TOOLS = {
    "onenote_create_notebook",
    "onenote_create_section",
    "onenote_create_section_group",
    "onenote_list_section_groups",
    "onenote_update_page",
    "onenote_delete_page",
    "onenote_copy_section",
    "onenote_copy_status",
}


@pytest.mark.asyncio
async def test_crud_tools_registered_and_annotations_are_real_mcp_hints():
    tools = {t.name: t for t in await server.app.list_tools()}
    assert NEW_TOOLS <= set(tools)
    for name, tool in tools.items():
        assert tool.annotations is not None and tool.annotations.readOnlyHint is not None, (
            f"{name} advertises no readOnlyHint"
        )
    assert tools["onenote_delete_page"].annotations.destructiveHint is True
    assert tools["onenote_list_notebooks"].annotations.readOnlyHint is True
    assert tools["onenote_create_notebook"].annotations.destructiveHint is False
    assert tools["onenote_create_notebook"].annotations.readOnlyHint is False
