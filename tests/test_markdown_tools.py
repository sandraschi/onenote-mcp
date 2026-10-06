"""Markdown input/output and page/notebook links through the MCP tools (mocked Graph)."""

import json

import httpx
import pytest

from onenote_mcp import server

GRAPH = "https://graph.microsoft.com/v1.0"
LINKS = {
    "oneNoteClientUrl": {"href": "onenote:https://d.docs.live.net/abc/Notes.one#Page&section-id={1}"},
    "oneNoteWebUrl": {"href": "https://onedrive.live.com/redir?resid=abc&page=edit"},
}
PAGE = {
    "id": "pg1",
    "title": "T",
    "createdDateTime": "c",
    "lastModifiedDateTime": "m",
    "self": "s",
    "contentUrl": "u",
    "links": LINKS,
}


def _sent(request: httpx.Request):
    return json.loads(request.content)


# ---- writing Markdown ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_page_markdown_renders_headings_and_todos(graph):
    calls, routes = graph
    routes[("POST", "/v1.0/me/onenote/sections/sec1/pages")] = httpx.Response(201, json={"id": "pg1"})
    out = await server.onenote_create_page(
        notebook_id="nb1",
        title="Plan",
        content="# Goals\n- [ ] ship\n- [x] test",
        section_id="sec1",
        content_format="markdown",
    )
    assert "✅" in out
    sent = calls[-1].content.decode()
    assert "<h1>Goals</h1>" in sent
    assert '<p data-tag="to-do">ship</p>' in sent and '<p data-tag="to-do:completed">test</p>' in sent


@pytest.mark.asyncio
async def test_create_page_html_default_is_passed_through_unchanged(graph):
    calls, routes = graph
    routes[("POST", "/v1.0/me/onenote/sections/sec1/pages")] = httpx.Response(201, json={"id": "pg1"})
    await server.onenote_create_page(notebook_id="nb1", title="T", content="# not markdown", section_id="sec1")
    assert "# not markdown" in calls[-1].content.decode() and "<h1>not" not in calls[-1].content.decode()


@pytest.mark.asyncio
async def test_markdown_escapes_raw_html_in_content(graph):
    calls, routes = graph
    routes[("POST", "/v1.0/me/onenote/sections/sec1/pages")] = httpx.Response(201, json={"id": "pg1"})
    await server.onenote_create_page(
        notebook_id="nb1", title="T", content="hi <script>x()</script>", section_id="sec1", content_format="markdown"
    )
    assert "<script>" not in calls[-1].content.decode()


@pytest.mark.asyncio
async def test_append_markdown_vs_text(graph):
    calls, routes = graph
    routes[("PATCH", "/v1.0/me/onenote/pages/pg1/content")] = httpx.Response(204)
    await server.onenote_append_page(page_id="pg1", content="- [ ] call Sam", content_format="markdown")
    assert 'data-tag="to-do"' in _sent(calls[-1])[0]["content"]
    await server.onenote_append_page(page_id="pg1", content="- [ ] call Sam")  # default = plain text
    sent = _sent(calls[-1])[0]["content"]
    assert "data-tag" not in sent and "- [ ] call Sam" in sent


@pytest.mark.asyncio
async def test_update_page_markdown_converts_but_title_stays_plain(graph):
    calls, routes = graph
    routes[("PATCH", "/v1.0/me/onenote/pages/pg1/content")] = httpx.Response(204)
    await server.onenote_update_page(
        page_id="pg1", target="p:{a}{1}", action="replace", content="**Fixed**", content_format="markdown"
    )
    assert "<strong>Fixed</strong>" in _sent(calls[-1])[0]["content"]
    await server.onenote_update_page(
        page_id="pg1", target="title", action="replace", content="Plain *title*", content_format="markdown"
    )
    assert _sent(calls[-1])[0]["content"] == "Plain *title*"


# ---- reading Markdown + links -------------------------------------------------------------------


def _mock_page(routes, html):
    routes[("GET", "/v1.0/me/onenote/pages/pg1")] = httpx.Response(200, json=PAGE)
    routes[("GET", "/v1.0/me/onenote/pages/pg1/content")] = httpx.Response(200, text=html)


@pytest.mark.asyncio
async def test_get_page_markdown_output_and_links(graph):
    _, routes = graph
    _mock_page(
        routes, '<html><head><title>T</title></head><body><h1>H</h1><p data-tag="to-do">buy milk</p></body></html>'
    )
    out = await server.onenote_get_page(page_id="pg1", output_format="markdown")
    assert "# H" in out and "- [ ] buy milk" in out
    assert "<h1>" not in out and "<title>" not in out
    assert "Open in OneNote (web):** https://onedrive.live.com/redir" in out
    assert "Open in OneNote (app):** onenote:https://d.docs.live.net" in out


@pytest.mark.asyncio
async def test_empty_title_from_graph_gets_placeholder(graph):
    # Graph can return title="" for a few seconds after creation (eventual consistency).
    _, routes = graph
    routes[("GET", "/v1.0/me/onenote/pages/pg1")] = httpx.Response(200, json={**PAGE, "title": ""})
    routes[("GET", "/v1.0/me/onenote/pages/pg1/content")] = httpx.Response(200, text="<body><p>x</p></body>")
    assert "**Title:** Page pg1" in await server.onenote_get_page(page_id="pg1")


@pytest.mark.asyncio
async def test_get_page_default_is_raw_html(graph):
    _, routes = graph
    _mock_page(routes, "<body><h1>H</h1></body>")
    assert "<h1>H</h1>" in await server.onenote_get_page(page_id="pg1")


@pytest.mark.asyncio
async def test_include_ids_with_markdown_is_rejected_without_calling_graph(graph):
    calls, _ = graph
    out = await server.onenote_get_page(page_id="pg1", include_ids=True, output_format="markdown")
    assert out.startswith("❌") and "html" in out and calls == []


@pytest.mark.asyncio
async def test_get_links_for_each_kind(graph):
    _calls, routes = graph
    routes[("GET", "/v1.0/me/onenote/pages/pg1")] = httpx.Response(200, json=PAGE)
    routes[("GET", "/v1.0/me/onenote/notebooks/nb1")] = httpx.Response(
        200, json={"id": "nb1", "displayName": "Thesis", "links": LINKS}
    )
    routes[("GET", "/v1.0/me/onenote/sections/sec1")] = httpx.Response(200, json={"id": "sec1", "displayName": "S"})
    page = await server.onenote_get_links(kind="page", item_id="pg1")
    assert "**T**" in page and "https://onedrive.live.com/redir" in page and "onenote:https://" in page
    nb = await server.onenote_get_links(kind="notebook", item_id="nb1")
    assert "**Thesis**" in nb
    assert (await server.onenote_get_links(kind="section", item_id="sec1")).startswith("No links returned")


@pytest.mark.asyncio
async def test_get_links_errors_are_strings(graph):
    out = await server.onenote_get_links(kind="page", item_id="missing")
    assert out.startswith("❌ Failed to get links")
    bad = await server.onenote_get_links(kind="chapter", item_id="x")  # bypasses schema validation
    assert bad.startswith("❌") and "kind must be one of" in bad


@pytest.mark.asyncio
async def test_format_parameters_advertise_enums_in_the_tool_schema():
    tools = {t.name: t for t in await server.app.list_tools()}

    def enum_of(tool, param):
        prop = tools[tool].parameters["properties"][param]
        return set(prop.get("enum") or [v for opt in prop.get("anyOf", []) for v in opt.get("enum", [])])

    assert enum_of("onenote_get_page", "output_format") == {"html", "markdown"}
    assert enum_of("onenote_create_page", "content_format") == {"html", "markdown"}
    assert enum_of("onenote_append_page", "content_format") == {"text", "markdown"}
    assert enum_of("onenote_update_page", "content_format") == {"html", "markdown"}
    assert enum_of("onenote_get_links", "kind") == {"notebook", "section", "page"}
