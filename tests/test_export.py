"""Tests for the Markdown backup/export helpers (no network)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from onenote_mcp.export_notes import build_export, html_to_markdown, job_status, safe_name
from onenote_mcp.models import TOCSection


def test_html_to_markdown_basics():
    md = html_to_markdown("<h1>T</h1><p>Hello <b>bold</b> and <i>it</i></p><ul><li>a</li><li>b</li></ul>")
    assert "# T" in md
    assert "**bold**" in md and "*it*" in md
    assert "- a" in md and "- b" in md


def test_html_to_markdown_drops_scripts_and_escapes():
    md = html_to_markdown("<script>evil()</script><p>5 < 6 & 7</p>")
    assert "evil" not in md
    assert "&lt;" in md and "&amp;" in md


def test_safe_name_windows():
    assert safe_name('a<b>:"/\\|?*c') == "abc"
    assert safe_name("  ...  ") == "untitled"


class _NB:
    def __init__(self, id, displayName):
        self.id = id
        self.displayName = displayName


class _Sec:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.pageCount = 2


class _TP:
    def __init__(self, id, title):
        self.id = id
        self.title = title


class _TOC:
    def __init__(self, sections):
        self.sections = sections


class _Page:
    def __init__(self, pid, title):
        self.id = pid
        self.title = title
        self.lastModifiedDateTime = "2024-01-01T00:00:00Z"
        self.content = "<h1>Hi</h1><p>body text</p>"


async def _fake_list_notebooks():
    return [_NB("nb1", "My NB"), _NB("nb2", "Other:NB")]  # colon tests safe_name


async def _fake_get_toc(nbid):
    if nbid == "nb1":
        sec = _Sec("s1", "Sec/A")  # slash tests safe_name
        sec.pages = [_TP("p1", "Hello"), _TP("p2", "Hello")]  # dup title tests (2)
        return _TOC([sec]), []
    return _TOC([]), []


async def _fake_list_pages(sid):
    return [_TP("p1", "Hello"), _TP("p2", "Hello")] if sid == "s1" else []


async def _fake_get_page(pid):
    return _Page(pid, "Hello")


def test_build_export_writes_tree_and_index(tmp_path):
    prog: dict = {}
    out = asyncio.run(
        build_export(
            _fake_list_notebooks, _fake_get_toc, _fake_list_pages, _fake_get_page, progress=prog, root=tmp_path
        )
    )
    assert out["state"] == "done"
    assert out["files"] == 2
    base = sorted((tmp_path).rglob("*.md"))
    names = [p.name for p in base]
    assert "Hello.md" in names and "Hello (2).md" in names and "index.md" in names
    # NB "Other:NB" -> colon stripped, section "Sec/A" -> slash stripped
    hello = sorted((tmp_path).rglob("Hello.md"))[0]
    body = hello.read_text(encoding="utf-8")
    assert hello.parent.name == "SecA" and hello.parent.parent.name == "My NB"
    assert body.startswith("---\ntitle: Hello") and "# Hi" in body
    assert job_status()["state"] in ("idle", "done")


def test_toc_section_carries_id_for_export():
    # Regression: export walks section.id - a missing id silently skips everything.
    sec = TOCSection(id="s-1", name="S", pageCount=0, pages=[])
    assert sec.id == "s-1"


def test_build_export_notebook_filter(tmp_path):
    prog: dict = {}
    out = asyncio.run(
        build_export(
            _fake_list_notebooks,
            _fake_get_toc,
            _fake_list_pages,
            _fake_get_page,
            notebook_id="nb2",
            progress=prog,
            root=tmp_path,
        )
    )
    assert out["state"] == "done" and out["files"] == 0
