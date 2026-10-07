"""Per-user Microsoft app registration: storage, validation, precedence and the REST routes."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from onenote_mcp import app_config, server

GUID = "12345678-abcd-1234-abcd-1234567890ab"


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("ONENOTE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("ONENOTE_CLIENT_ID", raising=False)
    monkeypatch.delenv("ONENOTE_AUTHORITY", raising=False)
    monkeypatch.setattr(server, "TOKEN_FILE_PATH", tmp_path / ".access-token.txt")
    return tmp_path


def test_unconfigured_by_default_and_require_raises():
    assert not app_config.is_configured()
    assert app_config.source() == "none"
    with pytest.raises(app_config.NotConfiguredError, match="step 1"):
        app_config.require_client_id()


def test_save_persists_in_the_data_folder_and_is_read_back(isolated):
    assert app_config.save(GUID, "consumers") is True
    assert (isolated / "settings.json").is_file()
    assert app_config.client_id() == GUID
    assert app_config.audience() == "consumers"
    assert app_config.authority() == "https://login.microsoftonline.com/consumers"
    assert app_config.source() == "settings"
    assert app_config.save(GUID.upper(), "consumers") is False  # same ID, different case: unchanged


@pytest.mark.parametrize("bad", ["", "not-a-guid", GUID[:-1], f"{GUID} extra", "x" * 36])
def test_save_rejects_non_guid(bad):
    with pytest.raises(ValueError, match="GUID"):
        app_config.save(bad, "common")


def test_save_rejects_unknown_audience():
    with pytest.raises(ValueError, match="audience"):
        app_config.save(GUID, "everyone")


def test_environment_wins_over_settings(monkeypatch):
    app_config.save(GUID, "common")
    monkeypatch.setenv("ONENOTE_CLIENT_ID", "99999999-9999-9999-9999-999999999999")
    monkeypatch.setenv("ONENOTE_AUTHORITY", "https://login.microsoftonline.com/consumers")
    assert app_config.client_id().startswith("99999999")
    assert app_config.source() == "env"
    assert app_config.audience() == "consumers"


def test_public_state_lists_the_scopes_to_grant():
    state = app_config.public_state("http://localhost:1/cb")
    assert state["configured"] is False
    assert state["scopes"] == ["Notes.Read", "Notes.ReadWrite", "User.Read"]
    assert state["redirect_uri"] == "http://localhost:1/cb"


# ---- REST ----


@pytest.fixture
def http():
    return TestClient(server.http_app)


def test_routes_roundtrip(http):
    assert http.get("/api/auth/config").json()["configured"] is False
    assert GUID not in http.get("/api/auth/config").text
    assert http.post("/api/auth/config", json={"client_id": "nope", "audience": "common"}).status_code == 400
    ok = http.post("/api/auth/config", json={"client_id": GUID, "audience": "consumers"})
    assert ok.status_code == 200 and ok.json()["configured"] is True
    assert http.get("/api/status").json()["providers"]["graph"]["configured"] is True


def test_changing_the_client_id_forgets_the_old_token(http, isolated):
    app_config.save(GUID, "common")
    server.TOKEN_FILE_PATH.write_text("old-token")
    res = http.post(
        "/api/auth/config", json={"client_id": "87654321-abcd-1234-abcd-1234567890ab", "audience": "common"}
    )
    assert res.status_code == 200
    assert not server.TOKEN_FILE_PATH.exists()


def test_env_locked_client_id_cannot_be_overwritten(http, monkeypatch):
    monkeypatch.setenv("ONENOTE_CLIENT_ID", GUID)
    res = http.post("/api/auth/config", json={"client_id": GUID, "audience": "common"})
    assert res.status_code == 409


def test_login_without_registration_says_so(http):
    res = http.get("/api/auth/login")
    assert res.status_code == 409
    body = res.json()
    assert body["needs_registration"] is True and "step 1" in body["error"]
