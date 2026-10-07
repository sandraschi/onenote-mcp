"""Register / unregister this server in the user's AI clients (Claude Desktop, Cursor, ...).

All real work is done by the fleet script ``install-mcp-clients.ps1`` (the same one the installer
runs), so there is one implementation and one set of tests. This module only locates the script,
decides which command to register, runs it per client and parses its ``-Json`` output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SERVER_NAME = "onenote-mcp"
CLIENT_IDS = ("claude-desktop", "cursor", "antigravity", "windsurf", "opencode", "claude-code")
_SCRIPT = "install-mcp-clients.ps1"
_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
_TIMEOUT_S = 60


class ClientsError(RuntimeError):
    """The registration script is unavailable or returned something unusable."""


def script_path() -> Path | None:
    """The bundled script: next to the frozen exe, or native/resources in a source checkout."""
    if getattr(sys, "frozen", False):
        candidate = Path(sys.executable).parent / _SCRIPT
    else:
        candidate = Path(__file__).resolve().parents[2] / "native" / "resources" / _SCRIPT
    return candidate if candidate.is_file() else None


def launch_command() -> str:
    """What an AI client should run to start this server over stdio.

    Frozen: the backend exe itself. Source checkout: the ``onenote-mcp`` console script of the venv.
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(sys.executable).parent / "onenote-mcp.exe")


def _run(client: str | None, extra: list[str]) -> list[dict]:
    """One script invocation; ``client=None`` lets the script handle every client in a single process."""
    script = script_path()
    if script is None:
        raise ClientsError("install-mcp-clients.ps1 not found next to the application")
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-Name",
        SERVER_NAME,
        *(["-Clients", client] if client else []),
        "-Json",
        *extra,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_TIMEOUT_S, creationflags=_NO_WINDOW, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ClientsError(f"could not run the registration script: {exc}") from exc
    text = (proc.stdout or "").strip().removeprefix("﻿")
    try:
        rows = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ClientsError(f"registration script returned no JSON ({(proc.stderr or text)[:300]})") from exc
    if isinstance(rows, dict):
        rows = [rows]
    return rows


def _run_for(client: str, extra: list[str]) -> dict:
    for row in _run(client, extra):
        if row.get("id") == client:
            return row
    return {"id": client, "label": client, "status": "not-found", "detail": ""}


def _validate(clients: list[str] | None) -> list[str]:
    chosen: list[str] = list(clients) if clients else list(CLIENT_IDS)
    unknown = [c for c in chosen if c not in CLIENT_IDS]
    if unknown:
        raise ValueError(f"unknown client id(s): {', '.join(unknown)}")
    return chosen


def status() -> dict:
    """Detected clients and whether this server is registered in each."""
    by_id = {r.get("id"): r for r in _run(None, ["-List"])}
    rows = [by_id.get(c) or {"id": c, "label": c, "status": "not-found", "detail": ""} for c in CLIENT_IDS]
    return {"command": launch_command(), "server": SERVER_NAME, "clients": rows}


def register(clients: list[str] | None = None) -> list[dict]:
    chosen = _validate(clients)
    command = launch_command()
    return [_run_for(c, ["-Command", command, "-EnvPairs", "MCP_TRANSPORT=stdio"]) for c in chosen]


def unregister(clients: list[str] | None = None) -> list[dict]:
    chosen = _validate(clients)
    return [_run_for(c, ["-Uninstall"]) for c in chosen]
