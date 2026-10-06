"""Markdown <-> OneNote HTML conversion (pure, no network)."""

from onenote_mcp.markup import html_to_markdown, markdown_to_html

# ---- Markdown -> HTML ----------------------------------------------------------------------------


def test_basic_blocks_render():
    html = markdown_to_html("# Title\n\nHello **bold** and *it* and ~~gone~~ [site](https://x.example)")
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html and "<em>it</em>" in html and "<s>gone</s>" in html
    assert '<a href="https://x.example">site</a>' in html


def test_lists_code_and_tables_render():
    html = markdown_to_html(
        "1. one\n2. two\n\n- a\n- b\n\n```\ncode here\n```\n\n| h1 | h2 |\n| --- | --- |\n| c1 | c2 |"
    )
    assert "<ol>" in html and "<ul>" in html
    assert "<pre><code>code here" in html
    assert "<table>" in html and "<th>h1</th>" in html and "<td>c2</td>" in html


def test_raw_html_is_escaped_not_passed_through():
    html = markdown_to_html("<script>alert(1)</script> <img src=x onerror=alert(1)>")
    assert "<script>" not in html and "<img" not in html
    assert "&lt;script&gt;" in html


def test_task_list_becomes_onenote_todo_paragraphs():
    html = markdown_to_html("- [ ] open item\n- [x] done item with **bold**")
    assert '<p data-tag="to-do">open item</p>' in html
    assert '<p data-tag="to-do:completed">done item with <strong>bold</strong></p>' in html
    assert "<ul>" not in html and "[ ]" not in html


def test_mixed_list_is_split_into_todo_paragraphs_and_a_plain_list():
    # CommonMark merges these into ONE list; task items must still become to-dos.
    html = markdown_to_html("- [ ] task\n- plain item\n- [x] later task")
    assert html.count("data-tag") == 2
    assert '<p data-tag="to-do">task</p>' in html and '<p data-tag="to-do:completed">later task</p>' in html
    assert html.count("<ul>") == 1 and "<li>plain item</li>" in html
    assert "[ ]" not in html and "[x]" not in html


def test_nested_task_items_are_left_as_plain_list():
    html = markdown_to_html("- [ ] parent\n  - [ ] child")
    assert "data-tag" not in html and "<ul>" in html


def test_empty_markdown_gives_empty_paragraph():
    assert markdown_to_html("") == "<p></p>"
    assert markdown_to_html("   \n") == "<p></p>"


# ---- HTML -> Markdown ----------------------------------------------------------------------------

ONENOTE_PAGE = """<html lang="en-US"><head><title>My Page</title><meta name="created" content="x"/></head>
<body data-absolute-enabled="true" style="font-family:Calibri">
<div style="position:absolute;left:48px" data-id="_default">
<h1 id="h1">Heading</h1>
<p id="p1" style="margin-top:0pt">Some <b>bold</b>, <i>italic</i>, <strike>old</strike> and <a href="https://x.example">a link</a>.</p>
<p data-tag="to-do">buy milk</p>
<p data-tag="to-do:completed">call bank</p>
<ul><li>alpha<ul><li>nested</li></ul></li><li>beta</li></ul>
<ol><li>first</li><li>second</li></ol>
<table><tr><td>H1</td><td>H2</td></tr><tr><td>a|b</td><td>d</td></tr></table>
<pre>line1
line2</pre>
<blockquote><p>quoted</p></blockquote>
<script>evil()</script>
</div></body></html>"""


def test_onenote_page_to_markdown():
    md = html_to_markdown(ONENOTE_PAGE)
    assert "My Page" not in md and "evil" not in md  # head/title/script dropped
    assert "# Heading" in md
    assert "Some **bold**, *italic*, ~~old~~ and [a link](https://x.example)." in md
    assert "- [ ] buy milk\n- [x] call bank" in md  # adjacent to-dos stay adjacent
    assert "- alpha\n  - nested\n- beta" in md
    assert "1. first\n2. second" in md
    assert "| H1 | H2 |\n| --- | --- |\n| a\\|b | d |" in md
    assert "```\nline1\nline2\n```" in md
    assert "> quoted" in md


# Body OneNote actually returned for our Markdown (live capture 2026-10-06, personal account):
# styling arrives as <span style=...>, code blocks as consolas paragraphs + U+FFFC, quotes as plain <p>.
LIVE_ONENOTE_BODY = """<html><head><title>Live markdown</title></head><body data-absolute-enabled="true">
<div data-id="_default" style="position:absolute;left:48px;top:120px;width:624px">
<h1 style="font-size:16pt">Live Markdown test</h1>
<p style="margin-top:5.5pt">Intro with <span style="font-weight:bold">bold</span>, <span style="font-style:italic">italic</span>, <span style="text-decoration:line-through">struck</span>, <span style="font-family:consolas">code</span> and <a href="https://example.com">a link</a>.</p>
<p data-tag="to-do" style="margin-top:5.5pt">open task</p>
<p data-tag="to-do:completed" style="margin-top:5.5pt">done task</p>
<ul> <li><p style="margin-top:0pt">plain bullet</p> <ul> <li>nested bullet</li> </ul> </li> </ul>
<br /> <br />
<ol> <li>first</li> <li>second</li> </ol>
<p style="margin-top:5.5pt">a quote</p>
<table style="border:0px"> <tr> <td style="text-align:center"><span style="font-weight:bold">Name</span></td> <td style="text-align:center"><span style="font-weight:bold">Qty</span></td> </tr>
<tr> <td>apple</td> <td>3</td> </tr> </table>
<p style="margin-top:5.5pt"><span style="font-family:consolas">print(&quot;hi&quot;)</span><span style="font-family:consolas">￼</span> <br /> </p>
<p style="margin-top:5.5pt">end</p>
</div></body></html>"""


def test_live_onenote_html_reads_back_with_styles_code_and_tables():
    md = html_to_markdown(LIVE_ONENOTE_BODY)
    assert "Intro with **bold**, *italic*, ~~struck~~, `code` and [a link](https://example.com)." in md
    assert "- [ ] open task\n- [x] done task" in md
    assert "- plain bullet\n  - nested bullet" in md
    assert "1. first\n2. second" in md
    assert "| Name | Qty |\n| --- | --- |\n| apple | 3 |" in md  # header not double-bolded
    assert '```\nprint("hi")\n```' in md  # consolas paragraph -> fenced block
    assert "￼" not in md
    assert "end" in md


def test_multiline_code_paragraph_and_inline_mono():
    html = '<p><span style="font-family:Consolas">a = 1</span><br/><span style="font-family:Consolas">b = 2</span></p>'
    assert html_to_markdown(html) == "```\na = 1\nb = 2\n```\n"
    mixed = '<p>run <span style="font-family:Consolas">ls -l</span> now</p>'
    assert html_to_markdown(mixed) == "run `ls -l` now\n"


def test_emphasis_keeps_edge_spaces_outside_markers():
    assert html_to_markdown("<p>a<b> bold </b>b</p>") == "a **bold** b\n"


def test_inline_special_characters_are_escaped():
    assert "snake\\_case and 2 \\* 3" in html_to_markdown("<p>snake_case and 2 * 3</p>")
    assert "\\<b>x" in html_to_markdown("<p>&lt;b&gt;x</p>")  # literal '<' must not become markup


def test_empty_html():
    assert html_to_markdown("") == ""
    assert html_to_markdown("<html><body></body></html>") == ""


def test_round_trip_is_stable():
    original = "# Plan\n\nIntro with **bold**.\n\n- [ ] one\n- [x] two\n\n- a\n  - b\n\n1. x\n2. y\n"
    # Task list and bullet list are separate here; to-do + normal list must survive a round trip.
    html = markdown_to_html(original)
    assert html.count("data-tag") == 2  # really converted to OneNote to-dos, not left as text
    again = html_to_markdown(html)
    assert "- [ ] one\n- [x] two" in again
    assert "# Plan" in again and "**bold**" in again and "1. x\n2. y" in again
    assert "- a\n  - b" in again
    assert html_to_markdown(markdown_to_html(again)) == again  # idempotent after one pass
