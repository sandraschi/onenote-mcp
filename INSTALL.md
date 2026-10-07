# Installation

Pick the one that matches how you want to use OneNote MCP.

| I want... | Use |
|---|---|
| A normal Windows app with a window, no AI client needed | [A. Windows app](#a-windows-app) |
| My notes available inside **Claude Desktop** | [B. Claude Desktop add-on](#b-claude-desktop-add-on) |
| My notes in **Cursor, VS Code, Claude Code** or another AI tool | [C. Other AI tools](#c-other-ai-tools-cursor-vs-code-claude-code) |
| To work on the code | [D. For developers](#d-for-developers) |

Whichever you pick, you sign in to your Microsoft account **once** (see [First use](#first-use-sign-in)).

---

## A. Windows app

1. Download the installer: [onenote-mcp-v1.1.0-setup.exe](https://github.com/sandraschi/onenote-mcp/releases/download/v1.1.0/onenote-mcp-v1.1.0-setup.exe)
   (all versions are on the [Releases page](https://github.com/sandraschi/onenote-mcp/releases)).
2. Double-click it and follow the prompts. If Windows warns about an unknown publisher, that is
   the installer not being code-signed; choose *More info*, then *Run anyway*.
3. Start **OneNote MCP** from the Start menu. Nothing else to install: the app brings its own engine.

---

## B. Claude Desktop add-on

Windows only. `.mcpb` add-ons are a Claude Desktop format; other tools use section C.

**Step 1 - install the add-on.** Open **Windows PowerShell** and run:

```powershell
irm https://github.com/sandraschi/onenote-mcp/releases/latest/download/install.ps1 | iex
```

The installer also sets up `uv` for you if it is missing (a small, free helper that runs the
add-on's Python parts, including Python itself). You never use it directly.

**Step 2 - restart Claude Desktop completely.** Right-click its icon in the system tray, choose
*Quit*, then start it again. OneNote MCP now appears under *Settings > Extensions*.

Other ways to do step 1 (these two do **not** install `uv`; run `winget install astral-sh.uv` first):
- Tell Claude: *install https://github.com/sandraschi/onenote-mcp/releases/latest/download/onenote-mcp.mcpb*
- Download `onenote-mcp.mcpb` from the [latest release](https://github.com/sandraschi/onenote-mcp/releases/latest)
  and double-click it.

---

## C. Other AI tools (Cursor, VS Code, Claude Code)

These tools launch the server with `uvx` (part of `uv`, a small free helper that runs Python
programs). Install it once in PowerShell with `winget install astral-sh.uv`, then reopen the
terminal. Then add this to the tool's MCP settings file
(Cursor: `%USERPROFILE%\.cursor\mcp.json`):

```json
{
  "mcpServers": {
    "onenote": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/sandraschi/onenote-mcp", "onenote-mcp"]
    }
  }
}
```

Claude Code, one command instead:

```powershell
claude mcp add onenote -- uvx --from git+https://github.com/sandraschi/onenote-mcp onenote-mcp
```

---

## First use: sign in

OneNote data comes from your Microsoft account, so you sign in once:

- **In Claude / your AI tool:** ask *"Sign in to my OneNote"*. You get a short code and the page
  `https://microsoft.com/devicelogin`; enter the code there.
- **In the Windows app:** *Notebooks* page, **Sign in with Microsoft**.

Personal Microsoft accounts work. The session renews itself, so you stay signed in for about 90 days.
More detail: [docs/ONBOARDING.md](docs/ONBOARDING.md).

---

## D. For developers

```powershell
winget install Casey.Just
git clone https://github.com/sandraschi/onenote-mcp
cd onenote-mcp
just bootstrap   # install all dependencies
just serve       # backend :10907 + webapp :10906
```

Without `just`: install [Python 3.12+](https://python.org) and [uv](https://docs.astral.sh/uv/), then

```powershell
uv sync --all-extras
uv run python -m onenote_mcp           # stdio, for MCP clients
uv run uvicorn onenote_mcp.server:http_app --port 10907   # HTTP, for the web dashboard
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `winget` is not recognised | Update "App Installer" in the Microsoft Store, or install uv from <https://docs.astral.sh/uv/> |
| `uv` is not recognised after installing | Close and reopen PowerShell |
| Extension missing in Claude Desktop | You must *Quit* Claude from the tray, not just close the window; or use the double-click route in B |
| Add-on shows an error on start | Check `uv` is installed (`uv --version`) |
| Port conflict (developers) | `just kill-all` clears fleet ports 10700-11000 |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/onenote-mcp/issues) |

*Feature overview: [README](README.md).*
