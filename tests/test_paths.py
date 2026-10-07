"""Persistent-state location and sign-in redirect: regressions found in the installed (frozen) app."""

from __future__ import annotations

import sys
from pathlib import Path

from onenote_mcp import paths, server


def test_data_root_override_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("ONENOTE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert paths.data_root() == tmp_path


def test_frozen_app_uses_local_appdata_not_temp(monkeypatch, tmp_path):
    monkeypatch.delenv("ONENOTE_DATA_DIR", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    root = paths.data_root()
    assert root == tmp_path / "com.sandraschi.onenote-mcp"
    assert root.is_dir()


def test_source_checkout_keeps_repo_root(monkeypatch):
    monkeypatch.delenv("ONENOTE_DATA_DIR", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert (paths.data_root() / "pyproject.toml").is_file()


def test_state_files_follow_data_root():
    for module in (server,):
        assert Path(module.TOKEN_FILE_PATH).parent == module.PROJECT_ROOT
    assert server._CACHE_PATH.parent == server.PROJECT_ROOT


def test_redirect_uri_follows_the_backend_port(monkeypatch):
    monkeypatch.delenv("ONENOTE_REDIRECT_URI", raising=False)
    for name in ("PORT", "ONENOTE_PORT", "MCP_PORT"):
        monkeypatch.delenv(name, raising=False)
    assert server._redirect_uri() == "http://localhost:10907/api/auth/callback"
    monkeypatch.setenv("PORT", "11250")  # what the Tauri shell passes
    assert server._redirect_uri() == "http://localhost:11250/api/auth/callback"
    monkeypatch.setenv("ONENOTE_REDIRECT_URI", "http://localhost:1/x")
    assert server._redirect_uri() == "http://localhost:1/x"
