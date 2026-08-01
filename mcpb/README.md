# onenote-mcp (MCPB Bundle)

FastMCP 3.1.0+ server for Microsoft OneNote integration

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "onenote-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "onenote_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **onenote-mcp**: FastMCP 3.1.0+ server for Microsoft OneNote integration

## Requirements

- Python 3.12+
- uv
