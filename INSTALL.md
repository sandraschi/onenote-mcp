# Installation

## 🧩 As an AI-client extension (no clone needed)

Requires [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv`).

**Claude Desktop (Windows)** - `.mcpb` is a Claude Desktop format. In Windows PowerShell:

```powershell
irm https://github.com/sandraschi/onenote-mcp/releases/latest/download/install.ps1 | iex
```

Then quit Claude Desktop from the tray and relaunch. The script downloads
`onenote-mcp.mcpb`, verifies its SHA256, and registers it with Claude Desktop. Alternatives:
tell Claude *install https://github.com/sandraschi/onenote-mcp/releases/latest/download/onenote-mcp.mcpb*,
or download the `.mcpb` from the release and double-click it. If the extension does not show up
under Settings > Extensions, use the double-click route.

**Cursor / VS Code / any other MCP client** - add to the client's MCP config
(Cursor: `~/.cursor/mcp.json`):

```json
{ "mcpServers": { "onenote": { "command": "uvx",
  "args": ["--from", "git+https://github.com/sandraschi/onenote-mcp", "onenote-mcp"] } } }
```

**Claude Code:** `claude mcp add onenote -- uvx --from git+https://github.com/sandraschi/onenote-mcp onenote-mcp`

First use: sign in with Microsoft once (see [docs/ONBOARDING.md](docs/ONBOARDING.md)).

## 🚀 Quick Start from source (recommended for development)

```powershell
# Install just if you don't have it
winget install Casey.Just    # Windows
# scoop install just          # Windows (alternative)
# brew install just           # macOS
# sudo apt install just       # Debian/Ubuntu
# cargo install just          # Linux (Rust)

git clone https://github.com/sandraschi/onenote-mcp
cd onenote-mcp
just
```

The interactive recipe dashboard opens in your browser. From there:

```powershell
just bootstrap   # install all dependencies
just serve       # start the server
just web         # start the frontend (if applicable)
```

> **Why not `pip install`?** MCP servers bundle webapps, configs, project scaffolding, and tooling that a flat Python package can't deliver. PyPI offers no safety advantage — it doesn't audit packages either. `just` gives you the complete, ready-to-run stack.

---

## 🐌 Traditional Setup

If you prefer not to use `just`:

1. Install [Python 3.13+](https://python.org) and [uv](https://docs.astral.sh/uv/)
2. Clone and enter the repo:
   ```powershell
   git clone https://github.com/sandraschi/onenote-mcp
   cd onenote-mcp
   ```
3. Install dependencies:
   ```powershell
   uv sync --all-extras
   ```
4. Start the server:
   ```powershell
   # stdio mode (for MCP clients like Claude Desktop)
   uv run python -m onenote_mcp.server

   # HTTP mode (for web dashboard)
   uv run uvicorn onenote_mcp.server:http_app --port 10907
   ```
5. Open `http://localhost:10907` or the frontend URL.

---

## ❓ Troubleshooting

| Issue | Fix |
|---|---|
| `just` not found | Install via `winget install Casey.Just`, `scoop install just`, or `brew install just` |
| Port conflict | Run `just kill-all` to clear fleet ports (10700–11000) |
| Dependencies out of sync | `uv sync --all-extras` |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/onenote-mcp/issues) |

---

*See the main [README](README.md) for feature overview and documentation.*
