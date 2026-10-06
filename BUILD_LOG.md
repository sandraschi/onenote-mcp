# BUILD_LOG — onenote-mcp

## 2026-10-06 — v1.1.0 NSIS build (PASS after 2 fixes)

Installer: `native/target/release/bundle/nsis/OneNote MCP_1.1.0_x64-setup.exe` (34.16 MiB),
shipped alongside `dist/onenote-mcp-v1.1.0.mcpb` (82 KB).
CUA-NSIS smoke: **12/12 phases passed** (health 200 on the dedicated port, version 1.1.0,
26 tools in diagnostics, WebView bridge OK, uninstall exit 0). Non-fatal: nav "Overview"
expected text not matched by OCR (template drift, same as 1.0.0) and a "404" string seen on
the Logging page (the activity log listing earlier 404 lines; `/api/logs` itself exists).

Pre-build audit (TAURI_PRODUCTION_PITFALLS Phase 1, A-J) found and fixed:

1. **Side-by-side rule (A) violated.** The installed app spawned its backend on the dev port
   10907, so `free_port` could kill the developer's backend. Claimed `onenote-mcp-native`
   ports 11249/11250 via `fleet-gate/claim_ports.py`; operator backend is now 11250 (Rust
   `BACKEND_PORT`, CSP, frontend Tauri base URL, smoke config). `run_server.py` only read
   `ONENOTE_PORT`/`MCP_PORT`, so it now honours `PORT` first (what the shell passes).
2. **Lifecycle (G).** `main.rs` stopped the backend on `Exit` only and never reaped it; now
   `Exit` and `ExitRequested`, with `wait()`.

Failure found by the smoke test (Phase 3, "Backend not reachable"):

3. **The installed app killed itself ~7 s after launch (exit -1, no log line).** `free_port`
   (added 2026-10-02 in a CI commit, never smoke-tested) ran `Stop-Process -Name
   'onenote-mcp-native'` and `taskkill /IM onenote-mcp-native.exe` - the shell's own process
   name - before spawning the backend. It also still did the forbidden blind
   `Get-NetTCPConnection -LocalPort | taskkill` on any PID owning the port (3 places, §15).
   Fix: image-scoped kill of the backend only, other native instances excluded by PID
   (`std::process::id()`), blind port-PID kills removed. Diagnosed by capturing stderr (empty),
   the missing spawn-log lines, and `git log -S` on the offending line.

Other: backend exe verified to contain `markup`, `markdown_it`, `bs4`, `lxml`, `soupsieve`
(`pyi-archive_viewer`); `/api/v1/health` tool_count was a stale hand-kept 19 (now read from
FastMCP, 26). Web dist is a single 451 KB chunk (no code-splitting); it rendered fine here, so
not changed (see pitfalls section 14 #1 if it ever starts exiting -1).

## 2026-08-01 — v1.0.0 NSIS build (assfix session)

### Result: PASS (after fixes)
Installer: `native/target/release/bundle/nsis/OneNote MCP_1.0.0_x64-setup.exe` (29.7 MB)
CUA-NSIS smoke: **ALL PHASES PASSED** (10/11 phases, 2 non-fatal nav OCR misses on
Dashboard/Logging headers — expected-text drift from the CUA template).

### Failures & fixes (in order encountered)

1. **PyInstaller global-tool env break** — `uv run pyinstaller` resolved to a uv tool
   install on Python 3.13 without fastmcp metadata → `PackageNotFoundError: fastmcp`.
   Fix: add `pyinstaller>=6.21.0` to `[dependency-groups] dev` (project venv),
   run `.venv\Scripts\pyinstaller.exe`.

2. **uv add --dev shadowed dev extras** — `uv add --dev pyinstaller` created a
   `[dependency-groups] dev` with only pyinstaller, which CI's group-first detection
   installs INSTEAD of `[project.optional-dependencies] dev` (ruff/mypy/pre-commit).
   Fix: group now carries pyinstaller + ruff + mypy + pre-commit.

3. **Spec non-compliance** — spec used `upx=True`, `noarchive=False`, bogus
   hiddenimports (`onenote_mcp.api/app/main/tools`). Rewrote per fleet standard:
   `strip=False, upx=False, noarchive=True`, trimmed hiddenimports, `copy_metadata`
   now valid (fastapi added to project deps — run_server.py imports it).

4. **Frozen exe 404 on ALL root routes** — `run_server.py` wrapped `_mcp.http_app()`
   in a FastAPI shell mounted at `/mcp`, so custom routes (`/health`, `/api/*`) lived
   at `/mcp/...`. CUA launch check failed with 404 on `/api/v1/health`.
   Fix: serve the CORS-wrapped `http_app` directly (transport already at `/mcp`).
   Verified frozen exe: /health, /api/status, /api/v1/health, /api/v1/diagnostics all 200.

5. **CUA health path mismatch** — CUA config expects `/api/v1/health`; backend only had
   `/health`. Added `/api/v1/health` custom route (aliases the health payload).

6. **Port collision in smoke run** — a dev uvicorn instance held 10907; CUA Phase 1
   kills only operator/backend image names. Killed manually before re-run.

### Gates at build time
- ruff check/format: clean; pytest: 3 passed; tsc -b: clean; biome: 4 infos only
- PyInstaller backend: 27.6 MB (>= 5 MB gate OK)
- Frontend dist CSS: 30.9 kB (Tailwind gate OK)

## 2026-09-24 - frozen exe crashed at startup (jaraco.text)
- Symptom: ModuleNotFoundError: No module named 'jaraco.text' from
  pyi_rth_pkgres.py before app code runs. PyInstaller's pkg_resources
  runtime hook fires but jaraco helpers were never bundled.
- Fix: jaraco.text, jaraco.context, jaraco.functools added to
  hiddenimports in onenote-mcp-backend.spec. Spec syntax verified;
  full frozen rebuild + smoke still pending (next native build).
- Fleet note: 159 other *-backend.spec files share the template gap -
  only bites when pkg_resources lands in the frozen graph. Fixed here
  where it bit; no fleet-wide sweep (batch rule).
