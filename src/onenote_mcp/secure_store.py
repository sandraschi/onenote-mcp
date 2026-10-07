"""Protect secrets at rest with Windows DPAPI (current-user scope).

The blob can only be decrypted by the same Windows user on the same machine: a copied folder, a
backup, or another account reads gibberish. Applied to the sign-in cache (it holds a refresh token),
the access-token file and the stored Microsoft client ID.

* ``unprotect`` accepts legacy plaintext (no marker), so existing files migrate on their next write.
* Non-Windows: no-op passthrough (the project targets Windows; this keeps tests/dev portable).
"""

from __future__ import annotations

import base64
import sys

MARKER = b"DPAPI1:"


class UnprotectError(ValueError):
    """The blob is protected but cannot be decrypted here (other user/machine, or corrupt)."""


def _crypt(data: bytes, *, encrypt: bool) -> bytes:
    import ctypes
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32 = ctypes.windll.crypt32  # type: ignore[attr-defined]
    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    buf = ctypes.create_string_buffer(data, len(data))
    src = Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    out = Blob()
    fn = crypt32.CryptProtectData if encrypt else crypt32.CryptUnprotectData
    ui_forbidden = 0x1
    ok = fn(ctypes.byref(src), None, None, None, None, ui_forbidden, ctypes.byref(out))
    if not ok:
        raise UnprotectError("DPAPI call failed (different Windows user or machine?)")
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        kernel32.LocalFree(out.pbData)


def protect(data: bytes) -> bytes:
    if sys.platform != "win32":
        return data
    return MARKER + _crypt(data, encrypt=True)


def unprotect(blob: bytes) -> bytes:
    if not blob.startswith(MARKER):
        return blob  # legacy plaintext
    if sys.platform != "win32":
        raise UnprotectError("DPAPI-protected data cannot be read on this platform")
    return _crypt(blob[len(MARKER) :], encrypt=False)


def protect_text(text: str) -> str:
    """Protected value as an ASCII string, for JSON (``dpapi:<base64>``). Plain text off Windows."""
    if sys.platform != "win32":
        return text
    return "dpapi:" + base64.b64encode(_crypt(text.encode("utf-8"), encrypt=True)).decode("ascii")


def unprotect_text(value: str) -> str:
    if not value.startswith("dpapi:"):
        return value  # legacy plaintext
    return _crypt(base64.b64decode(value[6:]), encrypt=False).decode("utf-8")
