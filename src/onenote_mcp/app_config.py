"""The user's own Microsoft (Entra) app registration: client ID + sign-in audience.

Every user must register their own app (free, ~5 minutes): the borrowed Graph Explorer client ID
yields tokens the OneNote workload rejects. The registration is stored in ``settings.json`` inside
the shared data folder (see ``paths.data_root``), so the desktop app and the stdio process an AI
client launches both use it without anyone editing ``.env``.

Precedence: ``ONENOTE_CLIENT_ID`` / ``ONENOTE_AUTHORITY`` environment variables, then settings.json.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from . import secure_store
from .constants import SCOPES
from .paths import data_root

_GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_BASE = "https://login.microsoftonline.com"
# "Supported account types" of the app registration -> Entra authority.
AUDIENCES = {"consumers": f"{_BASE}/consumers", "common": f"{_BASE}/common", "organizations": f"{_BASE}/organizations"}
DEFAULT_AUDIENCE = "common"
PORTAL_URL = "https://portal.azure.com/"


class NotConfiguredError(RuntimeError):
    """No Microsoft app registration is set up yet."""


def _settings_file():
    return data_root() / "settings.json"


def _load() -> dict[str, Any]:
    try:
        data = json.loads(_settings_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _stored_client_id() -> str:
    raw = str(_load().get("client_id", "")).strip()
    try:
        return secure_store.unprotect_text(raw).strip()
    except (secure_store.UnprotectError, ValueError):
        return ""  # protected for another Windows user/machine: treat as not registered


def client_id() -> str:
    return os.environ.get("ONENOTE_CLIENT_ID", "").strip() or _stored_client_id()


def audience() -> str:
    env = os.environ.get("ONENOTE_AUTHORITY", "").strip()
    if env:
        for name, url in AUDIENCES.items():
            if env.rstrip("/") == url:
                return name
        return "custom"
    stored = str(_load().get("audience", DEFAULT_AUDIENCE))
    return stored if stored in AUDIENCES else DEFAULT_AUDIENCE


def authority() -> str:
    env = os.environ.get("ONENOTE_AUTHORITY", "").strip()
    return env or AUDIENCES[audience()]


def source() -> str:
    if os.environ.get("ONENOTE_CLIENT_ID", "").strip():
        return "env"
    return "settings" if _stored_client_id() else "none"


def is_configured() -> bool:
    return bool(client_id())


def require_client_id() -> str:
    cid = client_id()
    if not cid:
        raise NotConfiguredError(
            "No Microsoft app registration yet. Open the OneNote MCP dashboard and complete step 1 "
            "(register your own free Microsoft app and paste its Application (client) ID)."
        )
    return cid


def save(new_client_id: str, new_audience: str) -> bool:
    """Validate and store the registration. Returns True if the client ID changed."""
    cid = (new_client_id or "").strip()
    if not cid and _stored_client_id():
        cid = _stored_client_id()  # blank = keep the saved ID (e.g. only the account type changes)
    if not _GUID.match(cid):
        raise ValueError("The Application (client) ID is a GUID like 12345678-abcd-1234-abcd-1234567890ab.")
    if new_audience not in AUDIENCES:
        raise ValueError(f"audience must be one of: {', '.join(AUDIENCES)}")
    changed = cid.lower() != client_id().lower()
    path = _settings_file()
    data = _load()
    data.update({"client_id": secure_store.protect_text(cid), "audience": new_audience})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return changed


def public_state(redirect_uri: str) -> dict[str, Any]:
    """Everything the UI needs to guide registration. No secrets (a public client has none)."""
    return {
        "configured": is_configured(),
        # Never returned in full: it is treated as a secret. The hint lets the user recognise which one is saved.
        "client_id_hint": client_id()[-4:],
        "audience": audience(),
        "source": source(),
        "locked_by_env": source() == "env",
        "redirect_uri": redirect_uri,
        "scopes": [s.rsplit("/", 1)[-1] for s in SCOPES],
        "portal_url": PORTAL_URL,
    }
