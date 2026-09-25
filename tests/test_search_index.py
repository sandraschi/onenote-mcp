"""Tests for the local FTS5 full-text search index (no network)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from onenote_mcp.search_index import index_count, search_fulltext, strip_html


def test_strip_html_drops_scripts_images_and_tags():
    html = (
        "<html><head><style>.x{color:red}</style></head>"
        "<body><h1>Hello</h1><p>world <b>bold</b></p>"
        "<script>evil()</script>"
        '<img src="data:image/png;base64,AAAA" /></body></html>'
    )
    text = strip_html(html)
    assert "Hello" in text and "bold" in text
    assert "evil" not in text and "AAAA" not in text and "<" not in text


def _seed(tmp_path):

    from onenote_mcp.search_index import _connect

    db = tmp_path / "t.db"
    with _connect(db) as conn:
        conn.execute(
            "INSERT INTO pages_fts VALUES (?,?,?,?,?,?,?)",
            ("p1", "Hiking checklist", "Outdoor", "Trips", "boots tent map", "2024-01-01", 1),
        )
        conn.execute(
            "INSERT INTO pages_fts VALUES (?,?,?,?,?,?,?)",
            ("p2", "Meeting notes", "Work", "Sync", "quarterly roadmap budget", "2024-02-01", 1),
        )
        conn.commit()
    return db


def test_fulltext_and_ranking(tmp_path):
    db = _seed(tmp_path)
    hits = search_fulltext("tent map", db_path=db)
    assert [h.id for h in hits] == ["p1"]
    assert index_count(db) == 2


def test_fulltext_no_match_and_empty_query(tmp_path):
    db = _seed(tmp_path)
    assert search_fulltext("zebra", db_path=db) == []
    assert search_fulltext("   ", db_path=db) == []


def test_fulltext_special_chars_quoted(tmp_path):
    db = _seed(tmp_path)
    # Must not raise on FTS5 operators; treated as literal text (no match).
    assert search_fulltext('tent* OR "1"', db_path=db) == []
