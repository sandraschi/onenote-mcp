# Development

## Layout

```
src/onenote_mcp/       Python package (server, transport, models, activity log)
web_sota/              React + Vite + Tailwind webapp (Vite dev on 10906)
native/                Tauri 2.0 shell + NSIS installer (embedded backend)
scripts/               build/CUA/fleet helpers (fleet.just, cua-smoke.py, ...)
mcpb/                  MCPB bundle staging (manifest, assets/prompts, run_server.py)
docs/                  This documentation set
```

## Daily loop

```powershell
uv sync --group dev         # install deps (or: just bootstrap)
just serve                  # backend in HTTP mode on 10907
# in web_sota/: npm run dev # frontend on 10906 (or: just serve + start.ps1)
```

`start.ps1` clears both ports, launches the backend, polls `/health`, then
starts Vite and opens the browser.

## Gates

| Gate | Command |
|------|---------|
| Python lint | `uv run ruff check src/` |
| Python format | `uv run ruff format src/` |
| Python types | `uv run pyright src/` |
| Tests | `uv run pytest tests/ -q` |
| Web types | `cd web_sota; npx tsc -b` |
| Web lint | `cd web_sota; npx biome ci .` |
| All | `just gates-green` |

CI (.github/workflows/ci.yml) runs ruff, format, pytest, pyright, tsc, biome and
Playwright on `windows-latest`.

## Builds

- MCPB bundle: `just mcpb-pack` (stages `mcpb/src/` fresh from `src/`, packs to `dist/`).
- NSIS installer: `just build-native` (frontend -> PyInstaller -> Tauri -> NSIS).
- Pre-release certification: `just cua-nsis-test` (install -> launch -> health -> uninstall).

## Conventions

- Fleet standards live in `mcp-central-docs/standards/` - read them before
  changing tool surfaces, webapp pages, or the native wrapper.
- Tools: verb-led `onenote_*` snake_case, `Annotated` + `Field` parameters,
  `## Return Format` / `## Examples` docstrings.
- Ports 10906/10907 are registered in `mcp-central-docs/operations/WEBAPP_PORTS.md` - do not drift.
