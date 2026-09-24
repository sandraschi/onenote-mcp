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

### If OneNote calls fail with 40001 (own app registration)

The built-in device flow borrows the public Graph Explorer client ID. Its tokens
are accepted by directory endpoints (`/me`) but the OneNote workload rejects
them with `40001 Unauthorized`. The fix is a free 5-minute app registration:

1. Go to [portal.azure.com](https://portal.azure.com) → **Microsoft Entra ID** →
   **App registrations** → **New registration**.
2. Name: `onenote-mcp-local`. Supported account types:
   **Personal Microsoft accounts only** (or multi-tenant if you also use a work account).
3. No redirect URI needed (device-code flow uses no redirect).
4. Copy the **Application (client) ID** from the overview page.
5. **API permissions** → Add → **Microsoft Graph** → **Delegated**:
   `Notes.Read.All`, `Notes.ReadWrite.All`, `User.Read`.
6. **Authentication** → Advanced settings → **Allow public client flows** → **Yes**
   (required — without this the device flow fails with `unauthorized_client`).
7. Set `ONENOTE_CLIENT_ID=<your id>` in `.env` at the repo root, delete
   `.access-token.txt`, restart the backend, and run the device flow again.
8. If your app is **Personal Microsoft accounts only**, also set
   `ONENOTE_AUTHORITY=https://login.microsoftonline.com/consumers` in `.env`
   (the default `/common` endpoint rejects personal-only apps with
   `AADSTS9002346` at flow initiation).

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
