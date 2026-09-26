"""Markdown backup/export for OneNote notebooks (no network in helpers).

Walks notebooks via injected callables, converts page HTML to Markdown,
writes ``data/exports/<stamp>/Notebook/Section/Title.md`` plus an index.
Tracks progress in an in-memory job dict (same pattern as search_index).
"""

import logging
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

logger = logging.getLogger("onenote_mcp.export_notes")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORT_ROOT = PROJECT_ROOT / "data" / "exports"

_job: dict[str, Any] = {
    "state": "idle",
    "total": 0,
    "done": 0,
    "error": "",
    "output_dir": "",
    "files": 0,
}


class _MdConverter(HTMLParser):
    """Tiny HTML->Markdown: headings, paragraphs, breaks, lists, bold,
    italic, links. Drops scripts/styles/images to text/alt."""

    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self._skip = 0
        self._li_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip += 1
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("\n" + "#" * int(tag[1]) + " ")
        elif tag == "p":
            self.out.append("\n")
        elif tag == "br":
            self.out.append("\n")
        elif tag == "li":
            self.out.append("\n" + "  " * max(0, self._li_depth - 1) + "- ")
        elif tag in ("ul", "ol"):
            self._li_depth += 1
        elif tag in ("b", "strong"):
            self.out.append("**")
        elif tag in ("i", "em"):
            self.out.append("*")
        elif tag == "a":
            href = dict(attrs).get("href", "")
            self.out.append("[" if href else "")
            self._link = href
        elif tag == "img":
            alt = dict(attrs).get("alt", "")
            if alt:
                self.out.append(f"![{alt}]()")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        elif tag in ("ul", "ol"):
            self._li_depth = max(0, self._li_depth - 1)
        elif tag in ("b", "strong"):
            self.out.append("**")
        elif tag in ("i", "em"):
            self.out.append("*")
        elif tag == "a" and getattr(self, "_link", ""):
            self.out.append(f"]({self._link})")
            self._link = ""
        elif tag in ("p", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.out.append(data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def html_to_markdown(html: str) -> str:
    """Page HTML -> readable Markdown (front matter added by exporter)."""
    conv = _MdConverter()
    conv.feed(html or "")
    text = "".join(conv.out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text + "\n" if text else ""


def safe_name(name: str) -> str:
    """Windows-safe filename stem (dedup handled by caller via counter)."""
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name or "untitled").strip().rstrip(".")
    return clean[:80] or "untitled"


async def build_export(
    list_notebooks,
    get_toc,
    list_pages,
    get_page,
    notebook_id: str = "",
    progress: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Export notebooks to Markdown files. Returns the job dict."""
    prog = progress if progress is not None else _job
    stamp = time.strftime("%Y%m%d-%H%M%S")
    outdir = (root or EXPORT_ROOT) / stamp
    prog.update({"state": "running", "total": 0, "done": 0, "error": "", "output_dir": str(outdir), "files": 0})
    started = time.time()
    try:
        notebooks = await list_notebooks()
        if notebook_id:
            notebooks = [nb for nb in notebooks if nb.id == notebook_id]
        # Count pages first for honest progress.
        toc_map: list[tuple[Any, Any]] = []
        for nb in notebooks:
            try:
                toc, _ = await get_toc(nb.id)
            except Exception as exc:
                logger.warning("Export skipped notebook %s: %s", nb.id, exc)
                continue
            for section in toc.sections:
                toc_map.append((nb, section))
        total_pages = sum(getattr(s, "pageCount", 0) for _, s in toc_map)
        prog["total"] = total_pages
        outdir.mkdir(parents=True, exist_ok=True)
        index_lines = [f"# OneNote export {stamp}", ""]
        for nb, section in toc_map:
            nb_dir = outdir / safe_name(nb.displayName) / safe_name(section.name)
            nb_dir.mkdir(parents=True, exist_ok=True)
            try:
                pages = await list_pages(section.id)
            except Exception as exc:
                logger.warning("Export skipped section %s: %s", section.name, exc)
                continue
            seen: dict[str, int] = {}
            for pg in pages:
                try:
                    page = await get_page(pg.id)
                    body = html_to_markdown(page.content or "")
                    stem = safe_name(page.title)
                    seen[stem] = seen.get(stem, 0) + 1
                    if seen[stem] > 1:
                        stem = f"{stem} ({seen[stem]})"
                    front = (
                        f"---\ntitle: {page.title}\nnotebook: {nb.displayName}\n"
                        f"section: {section.name}\nmodified: {page.lastModifiedDateTime}\n---\n\n"
                    )
                    (nb_dir / f"{stem}.md").write_text(front + body, encoding="utf-8")
                    prog["files"] += 1
                    rel = (nb_dir.relative_to(outdir) / f"{stem}.md").as_posix()
                    index_lines.append(f"- [{page.title}]({rel})")
                except Exception as exc:
                    logger.warning("Export skipped page %s: %s", pg.id, exc)
                prog["done"] += 1
        (outdir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    except Exception as exc:
        prog.update({"state": "error", "error": str(exc)})
        logger.exception("Export failed: %s", exc)
        return prog
    prog.update({"state": "done", "elapsed_seconds": round(time.time() - started, 1)})
    return prog


def job_status() -> dict[str, Any]:
    return dict(_job)
