"""
Example: Using OneNote Text Extractor in an MCP Server

This shows how to integrate the text extractor into any MCP server
that works with OneNote HTML content.
"""

from onenote_text_extractor import extract_readable_text, extract_text_summary


# Example 1: Basic usage with HTML string
def example_basic():
    """Basic example of extracting text from HTML."""
    html_content = """
    <html>
    <head><title>Project Planning</title></head>
    <body>
        <h1>Q1 2025 Roadmap</h1>
        <p>This quarter we'll focus on three main initiatives.</p>
        <h2>Key Objectives</h2>
        <ul>
            <li>Launch new product feature</li>
            <li>Improve user experience</li>
            <li>Scale infrastructure</li>
        </ul>
        <p>Each objective has specific deliverables and timelines.</p>
        <table>
            <tr><th>Objective</th><th>Owner</th><th>Due Date</th></tr>
            <tr><td>Feature Launch</td><td>Alice</td><td>2025-03-31</td></tr>
            <tr><td>UX Improvements</td><td>Bob</td><td>2025-02-28</td></tr>
        </table>
    </body>
    </html>
    """

    readable_text = extract_readable_text(html_content)
    print("=" * 60)
    print("EXAMPLE 1: Basic Text Extraction")
    print("=" * 60)
    print(readable_text)
    print()


# Example 2: Using with MCP tool (pseudo-code)
def example_mcp_integration():
    """Example of how to use in an MCP tool."""
    print("=" * 60)
    print("EXAMPLE 2: MCP Tool Integration Pattern")
    print("=" * 60)
    print("""
# In your MCP server code:

from fastmcp import FastMCP
from onenote_text_extractor import extract_readable_text

mcp = FastMCP("your-mcp-server")

@mcp.tool()
async def get_onenote_page_text(page_id: str) -> str:
    '''Get OneNote page as readable text.

    Args:
        page_id: OneNote page ID

    Returns:
        Readable text extracted from page HTML
    '''
    # 1. Get HTML from OneNote API (your existing code)
    html_content = await your_onenote_api.get_page_content(page_id)

    # 2. Convert to readable text
    readable_text = extract_readable_text(html_content)

    # 3. Return clean text
    return readable_text
    """)
    print()


# Example 3: Summary extraction
def example_summary():
    """Example of extracting a summary."""
    html_content = """
    <html>
    <body>
        <h1>Long Document</h1>
        <p>This is a very long document with lots of content that goes on and on.</p>
        <p>It has multiple paragraphs and sections.</p>
        <p>You might want just a summary of the first part.</p>
    </body>
    </html>
    """

    summary = extract_text_summary(html_content, max_length=100)
    print("=" * 60)
    print("EXAMPLE 3: Text Summary (first 100 chars)")
    print("=" * 60)
    print(summary)
    print()


# Example 4: Handling office-365-mcp HTML
def example_office365_integration():
    """Example showing integration with office-365-mcp."""
    print("=" * 60)
    print("EXAMPLE 4: Integration with office-365-mcp")
    print("=" * 60)
    print("""
# In office-365-mcp (or similar), modify your tool:

@mcp.tool()
async def get_onenote_page(page_id: str, format: str = "text") -> str:
    '''Get OneNote page content.

    Args:
        page_id: OneNote page identifier
        format: "text" for readable text, "html" for raw HTML

    Returns:
        Page content in requested format
    '''
    # Your existing code to get HTML
    html_content = await office365_api.get_onenote_page(page_id)

    # If user wants readable text, extract it
    if format == "text":
        return extract_readable_text(html_content)
    else:
        return html_content  # Return raw HTML if requested
    """)
    print()


if __name__ == "__main__":
    example_basic()
    example_mcp_integration()
    example_summary()
    example_office365_integration()

    print("=" * 60)
    print("To use in your MCP server:")
    print("1. Copy onenote_text_extractor.py to your project")
    print("2. Add beautifulsoup4 and lxml to requirements.txt")
    print("3. Import and use: from onenote_text_extractor import extract_readable_text")
    print("=" * 60)
