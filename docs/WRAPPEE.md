# Wrappee: Microsoft OneNote (via Microsoft Graph)

This server wraps **Microsoft OneNote**, the note-taking app in Microsoft 365
— notebooks, sections, pages with rich HTML content — through the
**Microsoft Graph API** (`/me/onenote/*`). Nothing is automated on-screen:
all reads/writes are Graph HTTPS calls, so it works headless, in the Tauri
desktop shell, and from any MCP client. Your notes live in your Microsoft
account (personal OneDrive for personal accounts); the server never stores
note content, only access tokens (local, gitignored).

## Official links

- Product: <https://www.onenote.com> (also <https://www.microsoft.com/microsoft-365/onenote>)
- Graph OneNote API: <https://learn.microsoft.com/graph/api/resources/onenote-api-overview>
- Error codes: <https://aka.ms/onenote-errors> (archived mirror page)
- App registrations (for your own client ID): <https://aka.ms/AppRegistrations>
- Consent management (revoke app access): <https://account.live.com/consent/Manage>

## Community

- Microsoft Q&A (onenote + graph tags): <https://learn.microsoft.com/answers>
- r/OneNote: <https://www.reddit.com/r/OneNote/>

## Disambiguation

- **OneNote (current)** vs the retired **OneNote for Windows 10 (UWP)** app:
  both read the same cloud notebooks; this server talks to the cloud side.
- **Sticky Notes** sync into OneNote/Outlook but are not OneNote pages.
- This repo is unrelated to `danosb/onenote-mcp` (JS, same ancestor),
  `purpleslurple/onenote-mcp-server` (Python), and PnP's
  `cli-microsoft365-mcp-server` (no page-content reads) — see
  `docs/AUTH_INVESTIGATION.md` for the comparison.
