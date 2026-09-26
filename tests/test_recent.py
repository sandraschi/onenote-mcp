"""Tests for the recent-changes feed filter (no network)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from onenote_mcp.server import select_recent

NOW = 1_700_000_000.0
DAY = 86400


def _iso(ts):
    import datetime

    return datetime.datetime.fromtimestamp(ts, tz=datetime.UTC).isoformat()


def test_recent_filters_and_sorts():
    items = [
        ("a", "Old", "NB", "S", _iso(NOW - 10 * DAY)),
        ("b", "New", "NB", "S", _iso(NOW - 1 * DAY)),
        ("c", "Mid", "NB", "S", _iso(NOW - 3 * DAY)),
    ]
    out = select_recent(items, 7, now=NOW)
    assert [p["id"] for p in out] == ["b", "c"]


def test_recent_window_and_bad_rows():
    items = [
        ("a", "Ancient", "NB", "S", _iso(NOW - 30 * DAY)),
        ("b", "BadDate", "NB", "S", "not-a-date"),
        ("c", "Empty", "NB", "S", ""),
        ("d", "Fresh", "NB", "S", _iso(NOW - 1 * DAY)),
    ]
    out = select_recent(items, 7, now=NOW)
    assert [p["id"] for p in out] == ["d"]
