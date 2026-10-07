"""Secrets at rest: DPAPI protection of the client ID, sign-in cache and access token."""

from __future__ import annotations

import json
import sys

import pytest

from onenote_mcp import app_config, secure_store, server

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="DPAPI is Windows-only")
GUID = "12345678-abcd-1234-abcd-1234567890ab"


@windows_only
def test_roundtrip_hides_the_plaintext():
    blob = secure_store.protect(b"refresh-token-123")
    assert blob.startswith(secure_store.MARKER)
    assert b"refresh-token-123" not in blob
    assert secure_store.unprotect(blob) == b"refresh-token-123"


@windows_only
def test_text_roundtrip_and_marker():
    value = secure_store.protect_text(GUID)
    assert value.startswith("dpapi:") and GUID not in value
    assert secure_store.unprotect_text(value) == GUID


def test_legacy_plaintext_still_reads_so_old_files_migrate():
    assert secure_store.unprotect(b"plain bytes") == b"plain bytes"
    assert secure_store.unprotect_text(GUID) == GUID


@windows_only
def test_corrupt_protected_blob_raises():
    with pytest.raises(secure_store.UnprotectError):
        secure_store.unprotect(secure_store.MARKER + b"not a real dpapi blob")


@pytest.fixture
def data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("ONENOTE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("ONENOTE_CLIENT_ID", raising=False)
    monkeypatch.delenv("ONENOTE_AUTHORITY", raising=False)
    return tmp_path


@windows_only
def test_client_id_is_not_stored_in_plaintext(data_dir):
    app_config.save(GUID, "consumers")
    raw = (data_dir / "settings.json").read_text(encoding="utf-8")
    assert GUID not in raw and "dpapi:" in raw
    assert app_config.client_id() == GUID


def test_client_id_is_never_returned_in_full(data_dir):
    app_config.save(GUID, "common")
    state = app_config.public_state("http://localhost:1/cb")
    assert "client_id" not in state
    assert state["client_id_hint"] == GUID[-4:]
    assert GUID not in json.dumps(state)


def test_blank_id_keeps_the_saved_one_when_only_the_account_type_changes(data_dir):
    app_config.save(GUID, "common")
    assert app_config.save("", "consumers") is False
    assert app_config.client_id() == GUID and app_config.audience() == "consumers"


def test_blank_id_without_a_saved_one_is_rejected(data_dir):
    with pytest.raises(ValueError, match="GUID"):
        app_config.save("", "common")


@windows_only
def test_unreadable_protected_id_counts_as_not_registered(data_dir):
    (data_dir / "settings.json").write_text(json.dumps({"client_id": "dpapi:AAAA", "audience": "common"}))
    assert app_config.client_id() == "" and not app_config.is_configured()


@windows_only
def test_access_token_file_is_protected_and_readable(data_dir, monkeypatch):
    monkeypatch.setattr(server, "TOKEN_FILE_PATH", data_dir / ".access-token.txt")
    server.save_access_token("super-secret-access-token")
    raw = server.TOKEN_FILE_PATH.read_bytes()
    assert b"super-secret-access-token" not in raw
    assert json.loads(secure_store.unprotect(raw))["token"] == "super-secret-access-token"
