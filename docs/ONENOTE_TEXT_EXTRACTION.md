# OneNote HTML to Readable Text Extraction

## Overview

OneNote's API returns HTML content that is difficult for AI models to parse. This utility converts that HTML into clean, readable text that Claude/Cursor/Sandra can easily understand.

## Quick Start

### Installation

```bash
pip install beautifulsoup4 lxml
```

### Basic Usage

```python
from onenote_text_extractor import extract_readable_text

# Get HTML from OneNote API (however you're getting it)
onenote_html = get_onenote_page_content()  # Your function

# Convert to readable text
readable_text = extract_readable_text(onenote_html)

# Now use readable_text with Claude/Cursor
print(readable_text)
```

## Integration with MCP Servers

### Example: Adding to office-365-mcp (or any MCP server)

```python
from fastmcp import FastMCP
from onenote_text_extractor import extract_readable_text

mcp = FastMCP("office-365-mcp")


@mcp.tool()
async def get_onenote_page_text(page_id: str) -> str:
    """Get OneNote page content as readable text.

    Retrieves a OneNote page and converts the HTML content
    into clean, readable text that AI models can easily parse.

    Args:
        page_id: The ID of the OneNote page to retrieve

    Returns:
        Clean, readable text extracted from the page HTML

    Examples:
        # Get readable text from a page
        text = await get_onenote_page_text("page-123")
    """
    # Your existing code to get HTML from OneNote
    html_content = await your_onenote_api_call(page_id)

    # Convert HTML to readable text
    readable_text = extract_readable_text(html_content)

    return readable_text
```

### Example: Enhancing existing tool

If you already have a tool that returns HTML:

```python
@mcp.tool()
async def get_onenote_page(page_id: str, format: str = "html") -> str:
    """Get OneNote page content.

    Args:
        page_id: The ID of the OneNote page
        format: Output format - "html" or "text" (default: "html")

    Returns:
        Page content in requested format
    """
    html_content = await your_onenote_api_call(page_id)

    if format == "text":
        return extract_readable_text(html_content)
    else:
        return html_content
```

## What It Does

The extractor:

1. **Removes scripts and styles** - Cleans out non-content elements
2. **Preserves structure** - Maintains headings, paragraphs, lists, tables
3. **Formats headings** - Adds underline separators for visual clarity
4. **Numbered lists** - Converts list items to numbered format
5. **Table formatting** - Converts tables to pipe-separated text
6. **Fallback handling** - If structure parsing fails, extracts all body text

## Example Output

**Input HTML:**
```html
<html>
<body>
    <h1>Meeting Notes</h1>
    <p>Discussion about project timeline.</p>
    <ul>
        <li>Task 1: Complete by Friday</li>
        <li>Task 2: Review with team</li>
    </ul>
</body>
</html>
```

**Output Text:**
```
Meeting Notes
-------------

Discussion about project timeline.

1. Task 1: Complete by Friday
2. Task 2: Review with team
```

## Functions

### `extract_readable_text(html: str) -> str`

Main function to extract readable text from OneNote HTML.

**Parameters:**
- `html` (str): Raw HTML content from OneNote API

**Returns:**
- `str`: Clean, readable text with preserved structure

### `extract_text_summary(html: str, max_length: int = 300) -> str`

Extract a text summary (first N characters) from OneNote HTML.

**Parameters:**
- `html` (str): Raw HTML content from OneNote API
- `max_length` (int): Maximum length of summary (default: 300)

**Returns:**
- `str`: Text summary truncated to max_length

## Copying to Other Projects

To use this in another MCP server:

1. **Copy the file:**
   ```bash
   cp onenote-mcp/onenote_text_extractor.py your-mcp-server/src/your_package/utils/
   ```

2. **Add dependency:**
   ```bash
   # In your requirements.txt
   beautifulsoup4>=4.12.0
   lxml>=4.9.0
   ```

3. **Import and use:**
   ```python
   from your_package.utils.onenote_text_extractor import extract_readable_text
   ```

## Testing

Run the module directly to test:

```bash
python onenote_text_extractor.py
```

This will run the example with sample HTML and show the output.

## Notes

- Uses BeautifulSoup4 for HTML parsing (more reliable than regex)
- Handles OneNote's specific HTML structure
- Preserves document hierarchy and formatting
- Gracefully handles malformed HTML
- Returns error message if extraction fails
