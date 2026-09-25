"""Local full-text search index for OneNote pages (SQLite FTS5).

Microsoft removed server-side full-text OneNote search and collection-wide
page queries fail on section-heavy accounts (Graph 20266), so we index
locally: walk each notebook TOC, fetch page bodies, strip to text, and query
with FTS5 + bm25. Incremental - pages whose modified stamp is unchanged are
skipped. DB lives in gitignored data/.
"""

import logging
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("onenote_mcp.search_index")

from .models import SearchHit

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = PROJECT_ROOT / "data" / "search-index.db"

_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    id UNINDEXED, title, notebook UNINDEXED, section UNINDEXED,
    content, modified UNINDEXED, indexed_at UNINDEXED
);
"""

# Build job state (in-memory; survives nothing, and needn't - rebuildable).
_job: dict[str, Any] = {"state": "idle", "total": 0, "done": 0, "error": ""}


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(_SCHEMA)
    return conn


def strip_html(html: str) -> str:
    """Page HTML -> plain text (drops scripts, styles, images incl. base64)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "img", "object", "embed"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


def _quote_term(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def index_count(db_path: Path | None = None) -> int:
    try:
        with _connect(db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM pages_fts").fetchone()[0]
    except Exception:
        return 0


def search_fulltext(query: str, limit: int = 50, db_path: Path | None = None) -> list["SearchHit"]:
    """BM25-ranked full-text search. Terms ANDed as literal phrases."""
    terms = [_quote_term(t) for t in query.strip().split() if t]
    if not terms:
        return []
    match = " ".join(terms)
    with _connect(db_path) as conn:
        rows = conn.execute(
            """SELECT id, title, notebook, section, modified,
                      snippet(pages_fts, 4, '<b>', '</b>', '...', 24)
               FROM pages_fts WHERE pages_fts MATCH ?
               ORDER BY bm25(pages_fts) LIMIT ?""",
            (match, limit),
        ).fetchall()
    return [
        SearchHit(
            id=r[0],
            title=r[1] or "",
            notebook=r[2] or "",
            section=r[3] or "",
            lastModifiedDateTime=r[4] or "",
            snippet=re.sub(r"<[^>]+>", "", r[5] or ""),
        )
        for r in rows
    ]


async def build_index(
    list_notebooks,
    get_toc,
    get_page_content,
    progress: dict[str, Any] | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """Walk all notebooks, upsert changed pages. Callables injected for tests."""
    prog = progress if progress is not None else _job
    prog.update({"state": "running", "total": 0, "done": 0, "error": ""})
    started = time.time()
    try:
        with _connect(db_path) as conn:
            known = {r[0]: r[1] for r in conn.execute("SELECT id, modified FROM pages_fts")}
            # Count first for progress honesty.
            toc_map: list[tuple[Any, Any, Any]] = []
            for nb in await list_notebooks():
                try:
                    toc, _ = await get_toc(nb.id)
                except Exception as exc:
                    logger.warning("Index skipped notebook %s: %s", nb.id, exc)
                    continue
                for section in toc.sections:
                    for pg in section.pages:
                        toc_map.append((nb, section, pg))
            prog["total"] = len(toc_map)
            for nb, section, pg in toc_map:
                try:
                    html = await get_page_content(pg.id)
                    text = strip_html(html)
                    modified = pg.modified or ""
                    if known.get(pg.id) == modified and text:
                        pass  # unchanged - keep stored row
                    else:
                        conn.execute("DELETE FROM pages_fts WHERE id = ?", (pg.id,))
                        conn.execute(
                            "INSERT INTO pages_fts VALUES (?,?,?,?,?,?,?)",
                            (
                                pg.id,
                                pg.title or "",
                                getattr(nb, "displayName", ""),
                                section.name or "",
                                text,
                                modified,
                                int(time.time()),
                            ),
                        )
                        conn.commit()
                except Exception as exc:
                    logger.warning("Index skipped page %s: %s", pg.id, exc)
                prog["done"] += 1
    except Exception as exc:
        prog.update({"state": "error", "error": str(exc)})
        logger.exception("Index build failed: %s", exc)
        return prog
    prog.update({"state": "done", "elapsed_seconds": round(time.time() - started, 1)})
    return prog


def job_status() -> dict[str, Any]:
    return {**_job, "indexed_pages": index_count()}
