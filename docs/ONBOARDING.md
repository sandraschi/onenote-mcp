# Onboarding

OneNote MCP talks to your Microsoft account through the Graph API, so the only
real setup step is signing in. Everything else is clone-and-run.

## Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node 20+ (only for the webapp dev server)
- A Microsoft account with OneNote notebooks

## 1. Install

```powershell
git clone https://github.com/sandraschi/onenote-mcp
cd onenote-mcp
just bootstrap        # uv sync + pre-commit + webapp deps
```

## 2. Authenticate (the whole point)

Run the server and trigger the device-code flow - either:

- **MCP client**: call the `authenticate` tool, or
- **Webapp**: open `http://127.0.0.1:10906`, go to **Settings** (or Notebooks)
  and click the sign-in flow, or
- **CLI**: `uv run python -m onenote_mcp.authenticate_device_code` equivalent via the webapp.

You get a URL (`https://microsoft.com/devicelogin`) and a code. Sign in with
your Microsoft account and approve the OneNote/Graph scopes. The access token is
stored in `.access-token.txt` at the repo root.

> The token expires - if tools start failing with 401s, re-run the flow or set a
> fresh `GRAPH_ACCESS_TOKEN` in `.env`.

## 3. Start using it

```powershell
just serve            # backend on 10907
# separate terminal, if you want the dashboard:
cd web_sota && npm run dev   # frontend on 10906
```

Or double-click `start.ps1` for the full stack.

First things to try: `onenote_list_notebooks`, then
`onenote_get_notebook_toc(notebook_id="...")` to explore, and
`onenote_get_page(page_id="...")` to read a note.

## Desktop installer (optional)

Download the NSIS installer from GitHub Releases (`OneNote MCP_x.y.z_x64-setup.exe`).
It embeds the backend; on first launch it copies `.env.example` to
`%LOCALAPPDATA%\com.sandraschi.onenote-mcp\.env` where you can configure a token
if you prefer it over the in-app device-code flow.
