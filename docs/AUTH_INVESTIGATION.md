# OneNote auth investigation — 2026-09-24 ("the 401 odyssey")

Goal: get `onenote-mcp` to list/read Sandra's OneNote notebooks (hotmail MSA)
through Microsoft Graph. Status at end of day: **sign-in mechanics all work,
OneNote/OneDrive workloads reject every custom-app token (40001). Account
proven healthy via Graph Explorer.** See "Next steps" for the ranked plan.

## Proven facts (evidence, not theories)

1. The Microsoft account is correct and healthy: `GET /me` returns
   `sandraschipal@hotmail.com`, id `449f68aad06f2da5`, which matches the
   OneDrive `resid=449F68AAD06F2DA5` where her notebooks are visible in the
   browser. Identity is consistent everywhere.
2. Graph Explorer (Microsoft first-party, browser auth-code flow, Notes
   consent via Modify permissions) returns **200 + notebooks** for the same
   account. The account, the notebooks, and the API surface all work.
3. Every token minted by OUR app is **opaque** (`Ew…`, never a JWT) in all
   tested combinations (2 client IDs × 2 authorities × 2 flows, see timeline).
4. Our tokens are accepted by directory/Exchange workloads and rejected by
   SharePoint-backed workloads:

   | Endpoint | Our token | Explorer token |
   |---|---|---|
   | `GET /me` | 200 | 200 |
   | `/me/calendars`, `/me/messages` | 403 (correct: scope not granted) | n/a |
   | `/me/drive/root` | 401 `unauthenticated` / "Must be authenticated to use '/drive' syntax" | n/a |
   | `/me/onenote/notebooks` (v1.0) | 401 code `40001` "not a valid authentication token" | **200** |
   | `/me/onenote/notebooks` (beta) | 401 `40001` | n/a |
   | `onenote.com/api/v1.0/me/notes/notebooks` | 401 `C40001` (same) | n/a |

   The calendars/messages 403s prove the token audience IS graph — this is
   not an audience bug. It is a workload-acceptance bug: SharePoint-backed
   providers won't honor our tokens.
5. Sample request IDs (for a Microsoft support case):
   `d1dedfd3-af14-4978-8661-4de7456514c0` (14:xx),
   `886f094d-66b9-463e-b228-9deb2fb5ea2e` (14:13),
   `0e3f53a5-a351-4bcb-b228-9deb2fb5ea2e` (18:35),
   Explorer-side `2f1a9b90-0c6d-4beb-8a8e-edef2d541674` (14:22, same 40001
   pre-consent).

## What we tried (all verified, in order)

1. **Expired-token re-auth** (device flow, built-in Graph Explorer client ID).
   Flow completed, `/me` 200, OneNote 40001. Killed theory: "just expired".
2. **Own app registration** (`onenote-mcp-local`,
   `b70aba9c-…-38c4b8048c3d`, personal-accounts-only, Notes.Read.All +
   Notes.ReadWrite.All + User.Read, public-client-flows on). Same 40001.
   Killed theory: "borrowed client ID".
3. **Authority `/common` → `/consumers`** (AADSTS9002346 demanded it for a
   personal-only app). Flow worked, same 40001. Killed theory: "wrong endpoint".
4. **Device flow → browser auth-code flow** (new `/api/auth/login` +
   `/api/auth/callback`, localhost redirect registered). Approval completes,
   "Connected", same 40001, still opaque. Killed theory: "device flow issue".
5. **Multi-tenant flip** (personal-only → Any Entra ID + personal, authority
   back to `/common`). Approval completes, token STILL opaque, same 40001.
   Killed theory: "authority determines token class".
6. **Stale-consent purge** (revoked app at account.live.com, re-approved with
   the Notes permissions visibly on screen). Same 40001. Weakened (not fully
   killed): "consent lacked Notes scopes" — the screens showed them, but the
   token is opaque so granted scopes are unverifiable from outside.
7. **office-365-mcp (PnP) as replacement**: evaluated, see below. Verdict:
   cannot replace (no page-content extraction to this day).

## What worked (the day wasn't all loss)

- Launcher failure fixed (`UvicornTarget :app` → `:http_app`); full assfix
  run: score 0 → 86/100 SOTA, 9 commits pushed, MCPB bundle builds.
- Backend LLM proxy, live Status/Tools pages, Skills page, Zustand store,
  ruff T20 + S110/S112 enforcement, Tauri `/api` base fix, Logging prefix fix.
- Auth diagnosability built for exactly this fight: `GET /api/auth/debug`
  (client suffix, authority, token shape/age, JWT aud/scp/exp — no secrets),
  auth events in the activity log, real MSAL error text surfaced in UI
  (this is how we got AADSTS9002346/70002 verbatim instead of guessing).
- Two latent auth bugs fixed: cached Graph client surviving re-auth (would
  have 401'd forever after any re-login), MSAL deprecated-API crash
  ("Invalid parameter type") in the callback.
- Sign-in UX rewritten to one vocabulary ("Sign in"), New-page button
  disabled pre-auth, dimmed styling.

## Ranked plan to 100%

1. **Portal permission reset (5 min, her):** in the app registration, REMOVE
   the three API permissions, save, RE-ADD them, save. This bumps the consent
   version server-side. Then revoke `onenote-mcp-local` at
   account.live.com consent management, re-run Sign in, approve. If the new
   token is a JWT or OneNote 200s — done, root cause was a stuck grant.
2. **Microsoft support case (her or me with her login):** with the request IDs
   above + "first-party token works, third-party token 40001s on OneNote for
   an MSA". This smells like a platform restriction/bug, not app config.
3. **PnP cli-microsoft365-mcp-server as complement, not replacement:** it
   auths via CLI-for-M365's own Entra app (first-party class, likely works),
   but its OneNote surface is only `notebook add/list` + `page list` — NO
   page content. It cannot do the core job (reading notes). Optionally adopt
   for mail/calendar while keeping onenote-mcp for notes.
4. **Do NOT chase:** new MSA, new tenant, paid Azure, scope-format tweaks
   (`Notes.Read` vs `.All`), beta endpoints — all tested or irrelevant.

## Appendix: competition (GitHub research 2026-09-24, 46 OneNote-MCP repos)

| Repo | Stars | Auth | Reads page content? | Verdict |
|---|---|---|---|---|
| `danosb/onenote-mcp` (JS, our README ancestor) | 125 | Borrowed Graph Explorer client ID + device flow, `Notes.Read.All` — the exact setup that 40001s for us | Yes (HTML + text extract) | Same trap, no advantage; stale (Apr 2025) |
| `OfficeMCP/OfficeMCP` (Python) | 119 | None (drives desktop Office apps via automation) | Via app UI, not Graph | Bypasses Entra entirely IF OneNote app installed; brittle COM route, Graph-independent fallback |
| `purpleslurple/onenote-mcp-server` (Python, FastMCP) | 52 | Own app, MULTI-TENANT, base scopes `Notes.Read/Notes.ReadWrite` (not `.All`), device flow, token cache | Yes | Closest working recipe; base-scopes + multi-tenant is an untested combo for us |
| `ZubeidHendricks/azure-onenote-mcp-server` (TS, our upstream) | 26 | Own app | Partial | Stale (May 2025) |
| `pnp/cli-microsoft365-mcp-server` (TS, PnP community) | 133 | CLI-for-M365 Entra app | **No** — only `notebook add/list`, `page list` | Cannot replace; complement at most |
| `ask-marcel/ask-marcel-office-cli` (TS, 204 cmds) | 9 | **No registration: Playwright-captured first-party Teams token** | **Yes, as markdown** (`get-onenote-page-as-markdown` + raw HTML variant) | **Best immediate option**: works around our whole auth disaster by design |
| `eshlon/onenotemcp`, `rajvirtual/MCP-Servers`, `jisujit/onenote-mcp-server` | 5–14 | Various Graph | Mixed | Too small/stale to matter |

Net: nobody beats our feature set (13 tools + webapp + Tauri + MCPB); the
auth wall hits everyone using custom-app tokens the same way. ask-marcel is
the pragmatic unblock, not a replacement.

## Appendix: environment that works
- Backend: `ONENOTE_CLIENT_ID=b70aba9c-…` (or unset for default),
  `ONENOTE_AUTHORITY=https://login.microsoftonline.com/common`
  (multi-tenant app) — debug endpoint confirms live values.
- App registration needs: Notes.Read.All + Notes.ReadWrite.All + User.Read
  (delegated), public-client-flows ON, `http://localhost` (+ exact callback
  as backup) under Mobile and desktop applications.
- Known-good reference: Graph Explorer + Notes.Read.All consent → 200.
