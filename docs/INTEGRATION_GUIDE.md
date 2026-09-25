# Integration Guide: OneNote Text Extractor

## Quick Integration Steps

### Step 1: Copy the Utility

Copy `onenote_text_extractor.py` to your MCP server project:

```bash
# From onenote-mcp directory
cp onenote_text_extractor.py /path/to/your-mcp-server/src/your_package/utils/
```

### Step 2: Add Dependencies

Add to your `requirements.txt`:

```txt
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

Install:

```bash
pip install -r requirements.txt
```

### Step 3: Import and Use

In your MCP server code:

```python
from your_package.utils.onenote_text_extractor import extract_readable_text
```

## Integration Patterns

### Pattern 1: New Tool for Readable Text

Add a new tool that returns readable text:

```python
@mcp.tool()
async def get_onenote_page_text(page_id: str) -> str:
    """Get OneNote page as readable text.

    Args:
        page_id: OneNote page ID

    Returns:
        Clean, readable text extracted from page HTML
    """
    # Get HTML from your OneNote API
    html_content = await your_onenote_api.get_page(page_id)

    # Convert to readable text
    return extract_readable_text(html_content)
```

### Pattern 2: Enhance Existing Tool

Modify existing tool to support both HTML and text:

```python
@mcp.tool()
async def get_onenote_page(page_id: str, format: str = "text") -> str:
    """Get OneNote page content.

    Args:
        page_id: OneNote page identifier
        format: Output format - "text" (readable) or "html" (raw)

    Returns:
        Page content in requested format
    """
    html_content = await your_onenote_api.get_page(page_id)

    if format == "text":
        return extract_readable_text(html_content)
    else:
        return html_content
```

### Pattern 3: Always Return Text

If you always want readable text, modify your existing tool:

```python
@mcp.tool()
async def get_onenote_page(page_id: str) -> str:
    """Get OneNote page content as readable text.

    Args:
        page_id: OneNote page identifier

    Returns:
        Clean, readable text from the page
    """
    # Get HTML
    html_content = await your_onenote_api.get_page(page_id)

    # Always convert to readable text
    return extract_readable_text(html_content)
```

## For office-365-mcp Specifically

If you're using office-365-mcp, here's a concrete example:

```python
# In your office-365-mcp tool file
from fastmcp import FastMCP
from office365_mcp.utils.onenote_text_extractor import extract_readable_text

mcp = FastMCP("office-365-mcp")


@mcp.tool()
async def get_onenote_page(page_id: str) -> str:
    """Get OneNote page content as readable text.

    The office-365-mcp returns HTML that's hard to parse.
    This tool converts it to clean, readable text.

    Args:
        page_id: OneNote page ID or title

    Returns:
        Clean, readable text extracted from page HTML
    """
    # Your existing office-365-mcp code to get HTML
    html_content = await office365_client.get_onenote_page_content(page_id)

    # Convert the idiosyncratic HTML to readable text
    readable_text = extract_readable_text(html_content)

    return readable_text
```

## Testing

Test the integration:

```python
# Test script
from onenote_text_extractor import extract_readable_text

# Sample OneNote HTML (idiosyncratic format)
test_html = """
<html>
<body>
    <div data-id="onenote-content">
        <p>Some content here</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </div>
</body>
</html>
"""

result = extract_readable_text(test_html)
print(result)
# Should output clean, readable text
```

## Benefits

✅ **Clean Output**: Removes OneNote's HTML quirks
✅ **Preserves Structure**: Maintains headings, lists, tables
✅ **AI-Friendly**: Easy for Claude/Cursor/Sandra to parse
✅ **Reusable**: Works with any OneNote HTML source
✅ **Simple**: Just one function call

## Troubleshooting

**Import Error:**
```bash
pip install beautifulsoup4 lxml
```

**Empty Output:**
- Check that HTML is valid
- Try the fallback: `extract_readable_text(html)` should still return body text

**Formatting Issues:**
- The extractor preserves structure but may need tweaking for specific HTML patterns
- Modify `extract_readable_text()` if needed for your specific use case
