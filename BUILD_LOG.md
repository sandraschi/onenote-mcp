# BUILD_LOG — onenote-mcp

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
