"""Where persistent state lives (sign-in cache, search index, exports).

* ``ONENOTE_DATA_DIR`` always wins.
* Frozen (installed app / bundled exe): ``%LOCALAPPDATA%\\com.sandraschi.onenote-mcp`` - the Tauri
  app-data folder. Never the source-relative path: in a PyInstaller onefile that resolves into the
  temp extraction area (lost on cleanup) and would differ between the app and the exe an AI client
  starts. Sharing this one folder is what lets a client's stdio process reuse the app's sign-in.
* Source checkout: the repository root (unchanged behaviour for development).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "com.sandraschi.onenote-mcp"


def data_root() -> Path:
    override = os.environ.get("ONENOTE_DATA_DIR")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
        path = root / APP_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
    return Path(__file__).resolve().parent.parent.parent
