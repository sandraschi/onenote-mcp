# OneNote MCP Server

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

A Model Context Protocol (MCP) server implementation that enables AI language models like Claude and other LLMs to interact with Microsoft OneNote.

> This project is based on [azure-onenote-mcp-server](https://github.com/ZubeidHendricks/azure-onenote-mcp-server) by Zubeid Hendricks, with modifications to simplify authentication and improve usability.

## Quick Start

```powershell
git clone https://github.com/sandraschi/onenote-mcp
cd onenote-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

## What Does This Do?

This server allows AI assistants to:
- Access your OneNote notebooks, sections, and pages
- Create new pages in your notebooks
- Search through your notes
- Read complete note content, including HTML formatting and text
- Analyze and summarize your notes directly

All of this happens directly through the AI interface without you having to switch contexts.

## Using with AI Assistants

### Setup for Cursor

1. Clone this repository and follow the installation steps below
2. Install the Python package: `uv pip install -e .`
3. Register the server in Cursor:
   - Open Cursor preferences (Cmd+, on Mac or Ctrl+, on Windows)
   - Go to the "MCP" tab
   - Add a new MCP server with these settings:
     - Name: `onenote`
     - Command: `python`
     - Args: `["-m", "onenote_mcp.server"]`

   Here's the complete JSON configuration example:
   ```json
   {
     "mcpServers": {
       "onenote": {
         "command": "python",
         "args": ["-m", "onenote_mcp.server"],
         "env": {}
       }
     }
   }
   ```

4. Restart Cursor
5. In Cursor, you can now interact with your OneNote data using natural language:

```
Can you show me my OneNote notebooks?
Create a new page in my first notebook with a summary of this conversation
Find notes related to "project planning" in my OneNote
```

The first time you ask about OneNote, the AI will guide you through the authentication process.

### Setup for Claude Desktop (or other MCP-compatible assistants)

1. Clone this repository and follow the installation steps below
2. Install the Python package: `uv pip install -e .`
3. In the Claude Desktop settings, add the OneNote MCP server:
   - Name: `onenote`
   - Command: `python`
   - Args: `["-m", "onenote_mcp.server"]`

   JSON configuration example:
   ```json
   {
     "mcpServers": {
       "onenote": {
         "command": "python",
         "args": ["-m", "onenote_mcp.server"],
         "env": {}
       }
     }
   }
   ```

4. You can now ask Claude to interact with your OneNote data

## Features

- Authentication with Microsoft OneNote using device code flow (no Azure setup needed)
- List all notebooks, sections, and pages
- Create new pages with HTML content
- Read complete page content, including HTML formatting
- Extract text content for AI analysis and summaries
- Summarize content of all pages in a single operation
- Read full content of all pages in a readable format
- Search across your notes

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx onenote-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "onenote-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/onenote-mcp", "run", "onenote-mcp"]
  }
}
```
### Prerequisites

- Python 3.10 or higher (install from [python.org](https://python.org/))
- pip (Python package installer)
- An active Microsoft account with access to OneNote
- Git (install from [git-scm.com](https://git-scm.com/))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/onenote-mcp.git
cd onenote-mcp
```

### Step 2: Install Project Dependencies

```bash
npm install
```

This will automatically install the MCP TypeScript SDK from npm (`@modelcontextprotocol/sdk`).

### Step 3: Install the Python Package

```bash
uv pip install -e .
```

### Step 4: Start the MCP Server

```bash
python -m onenote_mcp.server
```

This will start the MCP server, and you'll see a message:
```
Server started successfully.
Use the "authenticate" tool to start the authentication flow,
or use "onenote_save_access_token" if you already have a token.
```

### Step 4: Authenticate Through Your AI Assistant

Once the server is running, you can authenticate directly through your AI assistant:

1. In Cursor, Anthropic's Claude Desktop, or any MCP-compatible assistant, ask to authenticate with OneNote:
   ```
   Can you authenticate with my OneNote account?
   ```

2. The AI will trigger the authentication flow and provide you with:
   - A URL (typically microsoft.com/devicelogin)
   - A code to enter

3. Go to the URL, enter the code, and sign in with your Microsoft account

4. After successful authentication, you can start using OneNote with your AI assistant

## Available MCP Tools

Once authenticated, the following tools are available for AI assistants to use:

| Tool Name | Description |
|-----------|-------------|
| `authenticate` | Start the Microsoft authentication flow |
| `onenote_list_notebooks` | Get a list of all your OneNote notebooks |
| `onenote_get_notebook` | Get details of a specific notebook |
| `onenote_list_sections` | List all sections in a notebook |
| `onenote_list_pages` | List all pages in a section |
| `onenote_get_page` | Get the complete content of a specific page, including HTML formatting |
| `onenote_create_page` | Create a new page with HTML content |
| `onenote_search_pages` | Search for pages across your notebooks |
| `onenote_get_notebookTOC` | Generate a Table of Contents for a notebook (all sections & pages) |

## Example Interactions

Here are some examples of how you can interact with the OneNote MCP through your AI assistant:

```
User: Can you show me my OneNote notebooks?
AI: (uses onenote_list_notebooks) I found 3 notebooks: "Work", "Personal", and "Projects"

User: What sections are in my Projects notebook?
AI: (uses onenote_list_sections) Your Projects notebook has the following sections: "Active Projects", "Ideas", and "Completed"

User: Create a new page in Projects with today's date as the title
AI: (uses onenote_create_page) I've created a new page titled "2025-04-12" in your Projects notebook

User: Find all my notes about machine learning
AI: (uses onenote_search_pages) I found 5 pages with content related to machine learning...

User: Can you read and summarize my notes on the "Project Requirements" page?
AI: (uses onenote_get_page) Based on your "Project Requirements" page, here's a summary: The project requires Python 3.8+, integration with AWS services, and completion by Q3. Key deliverables include a web dashboard, API, and documentation...

User: Extract all the action items from my "Team Meeting" notes
AI: (uses onenote_get_page) Here are all the action items from your "Team Meeting" notes:
1. John to complete API documentation by Friday
2. Sarah to schedule design review meeting
3. Team to finalize Q3 roadmap by end of month

User: Summarize content of all my OneNote pages
AI: (runs get-all-page-contents.js) Here's a summary of all your pages:
- Questions: Contains strategic business questions about competitor analysis
- 2025-04-12: Discussion about monetization strategy for bank transfers
- Role Specification: Details about the Chief Payments Officer position
...

User: I want to read through all my OneNote pages so I can ask questions about them
AI: (runs read-all-pages.js) I've retrieved the full content of all your pages in a readable format. Now you can ask me specific questions about any of the content.

User: Generate a table of contents for my Projects notebook
AI: (uses onenote_get_notebookTOC) Here's the TOC for your Projects notebook:

# Projects
> 3 sections, 12 pages

## Active Projects (5 pages)
- **Q1 Planning** *(11/15/2025)*
- **API Design** *(11/20/2025)*
- **Budget Review** *(11/25/2025)*
...

User: Show me a TOC of all my notebooks
AI: (uses onenote_list_notebooks, then onenote_get_notebookTOC for each) Here are all your notebooks with their structure...
```

## Advanced: Direct Script Usage

For testing or development purposes, you can also use the Python module directly:

```bash
# Install the package
uv pip install -e .

# Start the MCP server
python -m onenote_mcp.server

# Or run individual functions (for testing)
python -c "from onenote_mcp.server import authenticate_device_code; print('Authenticating...')"
```

## Troubleshooting

### Authentication Issues

- If authentication fails, make sure you're using a modern browser without tracking prevention
- Try clearing browser cookies and cache
- If you get "expired_token" errors, restart the authentication process

### Server Won't Start

- Verify Python is installed (version 3.10+): `python --version`
- Make sure all dependencies are installed: `uv pip install -e .`
- Check that FastMCP is properly installed: `python -c "import fastmcp; print(FastMCP 3.1.0__version__)"`

### AI Can't Connect to the Server

- Ensure the MCP server is running (`npm start`)
- Check your AI assistant's settings to make sure it's configured to use MCP
- For Cursor, make sure it's the latest version that supports MCP

## Security Notes

- Authentication tokens are stored locally in `.access-token.txt`
- Tokens grant access to your OneNote data, so keep them secure
- Tokens expire after some time, requiring re-authentication
- No Azure setup or API keys are required

## Credits

This project builds upon the [azure-onenote-mcp-server](https://github.com/ZubeidHendricks/azure-onenote-mcp-server) by Zubeid Hendricks, with a focus on simplifying the authentication process and improving the user experience with AI assistants.


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.

## License

This project is licensed under the MIT License - see the LICENSE file for details
