"""Tests for plain-text -> HTML note conversion (no network)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from onenote_mcp.server import text_to_html


def test_paragraphs_and_breaks():
    assert text_to_html("a\n\nb") == "<p>a</p><p>b</p>"
    assert text_to_html("a\nb") == "<p>a<br/>b</p>"


def test_escapes_html():
    out = text_to_html("<script>x</script> & more")
    assert "<script>" not in out and "&amp;" in out


def test_blank_input():
    assert text_to_html("") == "<p></p>"
    assert text_to_html("   ") == "<p></p>"
