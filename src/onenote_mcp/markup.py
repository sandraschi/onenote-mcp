"""Markdown <-> OneNote page HTML (pure functions, no network).

Agents write Markdown; OneNote pages are HTML. ``markdown_to_html`` renders Markdown with raw
HTML disabled (so untrusted text cannot inject markup) and maps GFM task lists to OneNote
to-do paragraphs (``<p data-tag="to-do">``). ``html_to_markdown`` is the reverse for reading.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag
from markdown_it import MarkdownIt
from markdown_it.token import Token

_TASK = re.compile(r"^\[([ xX])\]\s+")
_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
_BLOCKS = {"p", "div", "ul", "ol", "li", "pre", "blockquote", "table", "hr", "body", "section", *_HEADINGS}


# ---------------------------------------------------------------- Markdown -> HTML


def _task_state(item_tokens: list[Token]) -> str | None:
    """'to-do' / 'to-do:completed' if the first inline of a list item starts with [ ] / [x]."""
    inline = next((t for t in item_tokens if t.type == "inline"), None)
    if inline is None:
        return None
    match = _TASK.match(inline.content)
    if not match:
        return None
    return "to-do" if match.group(1) == " " else "to-do:completed"


def _convert_task_lists(md: MarkdownIt, tokens: list[Token]) -> list[Token]:
    """Rewrite flat `[ ]`/`[x]` list items into OneNote to-do paragraphs (nested lists are left alone)."""
    out: list[Token] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type != "bullet_list_open":
            out.append(tok)
            i += 1
            continue
        j = i + 1
        while not (tokens[j].type == "bullet_list_close" and tokens[j].level == tok.level):
            j += 1
        body = tokens[i + 1 : j]
        items: list[list[Token]] = []
        for t in body:
            if t.type == "list_item_open" and t.level == tok.level + 1:
                items.append([])
            if items:
                items[-1].append(t)
        # An item that holds a nested list stays a plain item (a to-do paragraph cannot contain a list).
        states = [
            None if any(t.type in ("bullet_list_open", "ordered_list_open") for t in item) else _task_state(item)
            for item in items
        ]
        if not any(states):  # no convertible task item: render the list as-is
            out.extend(tokens[i : j + 1])
            i = j + 1
            continue
        # Flat list with at least one task item: CommonMark merges adjacent same-marker lists, so
        # split into runs - task runs become to-do paragraphs, plain runs stay a bullet list.
        k = 0
        while k < len(items):
            is_task = states[k] is not None
            run_end = k
            while run_end < len(items) and (states[run_end] is not None) == is_task:
                run_end += 1
            if is_task:
                for item, state in zip(items[k:run_end], states[k:run_end], strict=True):
                    inline = next(t for t in item if t.type == "inline")
                    inline.content = _TASK.sub("", inline.content, count=1)
                    inline.children = md.parseInline(inline.content)[0].children  # re-tokenise without marker
                    out.append(Token("html_block", "", 0, content=f'<p data-tag="{state}">'))
                    out.append(inline)
                    out.append(Token("html_block", "", 0, content="</p>\n"))
            else:
                out.append(Token("bullet_list_open", "ul", 1, level=tok.level, block=True, markup=tok.markup))
                for item in items[k:run_end]:
                    out.extend(item)
                out.append(Token("bullet_list_close", "ul", -1, level=tok.level, block=True, markup=tok.markup))
            k = run_end
        i = j + 1
    return out


def markdown_to_html(text: str) -> str:
    """Render Markdown to OneNote-ready HTML. Raw HTML in the input is escaped, not passed through."""
    md = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    tokens = _convert_task_lists(md, md.parse(text or ""))
    html = md.renderer.render(tokens, md.options, {})
    return html.strip() or "<p></p>"


# ---------------------------------------------------------------- HTML -> Markdown


_OBJ_CHAR = "￼"  # OneNote appends U+FFFC (object replacement) after code blocks


def _escape(text: str) -> str:
    return re.sub(r"([\\*_`<])", r"\\\1", text)


def _wrap(inner: str, marker: str) -> str:
    """Wrap `inner` in an emphasis marker, keeping edge spaces outside it (Markdown requires that)."""
    core = inner.strip()
    if not core:
        return inner
    lead, trail = inner[: len(inner) - len(inner.lstrip())], inner[len(inner.rstrip()) :]
    return f"{lead}{marker}{core}{marker}{trail}"


def _is_mono(node: Tag) -> bool:
    style = (node.get("style") or "").lower().replace(" ", "")
    return "font-family:consolas" in style or "font-family:courier" in style or "font-family:monospace" in style


def _styled(node: Tag, inner: str) -> str:
    """OneNote rewrites <b>/<i>/<s>/<code> into <span style=...>; read the styles back."""
    style = (node.get("style") or "").lower().replace(" ", "")
    if _is_mono(node):
        code = node.get_text().replace(_OBJ_CHAR, "")
        return f"`{code}`" if code.strip() else ""
    for needle, marker in (
        ("font-weight:bold", "**"),
        ("font-style:italic", "*"),
        ("text-decoration:line-through", "~~"),
    ):
        if needle in style:
            inner = _wrap(inner, marker)
    return inner


def _inline(node: Tag | NavigableString) -> str:
    if isinstance(node, NavigableString):
        return _escape(re.sub(r"\s+", " ", str(node).replace(_OBJ_CHAR, "")))
    inner = "".join(_inline(c) for c in node.children)
    name = node.name
    if name == "span":
        return _styled(node, inner)
    if name in ("b", "strong"):
        return _wrap(inner, "**")
    if name in ("i", "em"):
        return _wrap(inner, "*")
    if name in ("s", "strike", "del"):
        return _wrap(inner, "~~")
    if name == "code":
        return f"`{node.get_text()}`"
    if name == "a":
        href = node.get("href", "")
        return f"[{inner.strip()}]({href})" if href and inner.strip() else inner
    if name == "img":
        return f"![{node.get('alt', '')}]({node.get('src', '')})"
    if name == "br":
        return "  \n"
    return inner


def _list(node: Tag, depth: int) -> str:
    ordered = node.name == "ol"
    lines: list[str] = []
    n = 0
    for li in node.find_all("li", recursive=False):
        n += 1
        marker = f"{n}." if ordered else "-"
        pad = "  " * depth
        text = "".join(_inline(c) for c in li.children if not (isinstance(c, Tag) and c.name in ("ul", "ol")))
        lines.append(f"{pad}{marker} {text.strip()}")
        for sub in li.find_all(["ul", "ol"], recursive=False):
            lines.append(_list(sub, depth + 1))
    return "\n".join(lines)


def _table(node: Tag) -> str:
    rows = [
        [re.sub(r"\s+", " ", _inline(c)).strip().replace("|", "\\|") for c in tr.find_all(["th", "td"])]
        for tr in node.find_all("tr")
    ]
    rows = [r for r in rows if r]
    if not rows:
        return ""
    rows[0] = [re.sub(r"^\*\*(.+)\*\*$", r"\1", cell) for cell in rows[0]]  # OneNote bolds header cells itself
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def _code_paragraph(p: Tag) -> str:
    """Text of a paragraph that is entirely monospace (how OneNote stores a code block), else ''."""
    texts = [s for s in p.find_all(string=True) if s.replace(_OBJ_CHAR, "").strip()]
    if not texts or not all(
        any(_is_mono(a) for a in s.parents if isinstance(a, Tag) and a.name == "span") for s in texts
    ):
        return ""
    parts: list[str] = []
    for d in p.descendants:
        if isinstance(d, Tag) and d.name == "br":
            parts.append("\n")
        elif isinstance(d, NavigableString):
            parts.append(str(d).replace(_OBJ_CHAR, ""))
    return "".join(parts).strip("\n").rstrip()


def _blocks(node: Tag) -> list[tuple[str, str]]:
    """(kind, markdown) blocks of a container; kind 'todo' lets adjacent to-dos stay on adjacent lines."""
    out: list[tuple[str, str]] = []
    run: list[str] = []

    def flush() -> None:
        text = "".join(run).strip()
        if text:
            out.append(("p", text))
        run.clear()

    for child in node.children:
        if isinstance(child, NavigableString) or child.name not in _BLOCKS:
            run.append(_inline(child))
            continue
        flush()
        name = child.name
        if name in _HEADINGS:
            text = "".join(_inline(c) for c in child.children).strip()
            if text:
                out.append(("h", f"{'#' * _HEADINGS[name]} {text}"))
        elif name == "p":
            text = "".join(_inline(c) for c in child.children).strip()
            tag = str(child.get("data-tag", ""))
            if code := _code_paragraph(child):
                out.append(("code", f"```\n{code}\n```"))
            elif tag.startswith("to-do"):
                out.append(("todo", f"- [{'x' if 'completed' in tag else ' '}] {text}"))
            elif text:
                out.append(("p", text))
        elif name in ("ul", "ol"):
            out.append(("list", _list(child, 0)))
        elif name == "pre":
            out.append(("code", f"```\n{child.get_text().strip(chr(10))}\n```"))
        elif name == "blockquote":
            inner = "\n\n".join(t for _, t in _blocks(child))
            out.append(("q", "\n".join(f"> {line}" for line in inner.splitlines())))
        elif name == "table":
            if table := _table(child):
                out.append(("table", table))
        elif name == "hr":
            out.append(("hr", "---"))
        else:  # div / section / body / stray li: just a container
            out.extend(_blocks(child))
    flush()
    return out


def html_to_markdown(html: str) -> str:
    """OneNote page HTML -> Markdown (headings, lists, tables, code, links, to-do tags)."""
    soup = BeautifulSoup(html or "", "lxml")
    for junk in soup(["script", "style", "head", "title"]):
        junk.decompose()
    blocks = _blocks(soup.body or soup)
    parts: list[str] = []
    for i, (kind, text) in enumerate(blocks):
        if i:
            parts.append("\n" if kind == "todo" and blocks[i - 1][0] == "todo" else "\n\n")
        parts.append(text)
    result = "".join(parts).strip()
    return result + "\n" if result else ""
