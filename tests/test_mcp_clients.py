"""AI-client registration: argv building, error handling and the REST routes (no real PowerShell)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from onenote_mcp import mcp_clients, server


def _fake_run(calls: list[list[str]], status_for=lambda client: "registered"):
    def run(cmd, **kwargs):
        calls.append(cmd)
        clients = [cmd[cmd.index("-Clients") + 1]] if "-Clients" in cmd else list(mcp_clients.CLIENT_IDS)
        rows = [{"id": c, "label": c, "status": status_for(c), "detail": ""} for c in clients]
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(rows), stderr="")

    return run


@pytest.fixture
def script(monkeypatch, tmp_path):
    path = tmp_path / "install-mcp-clients.ps1"
    path.write_text("# stub")
    monkeypatch.setattr(mcp_clients, "script_path", lambda: path)
    return path


def test_source_checkout_finds_the_vendored_script():
    assert mcp_clients.script_path() is not None, "native/resources/install-mcp-clients.ps1 must be vendored"


def test_register_runs_the_script_once_per_client_with_stdio_env(script, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(mcp_clients.subprocess, "run", _fake_run(calls))
    rows = mcp_clients.register(["cursor", "opencode"])
    assert [r["id"] for r in rows] == ["cursor", "opencode"]
    assert len(calls) == 2
    for argv, client in zip(calls, ["cursor", "opencode"], strict=True):
        assert argv[argv.index("-Clients") + 1] == client
        assert argv[argv.index("-Name") + 1] == "onenote-mcp"
        assert "-Json" in argv
        assert argv[argv.index("-EnvPairs") + 1] == "MCP_TRANSPORT=stdio"
        assert argv[argv.index("-Command") + 1] == mcp_clients.launch_command()


def test_unregister_and_status_use_uninstall_and_list(script, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(mcp_clients.subprocess, "run", _fake_run(calls, lambda c: "present"))
    mcp_clients.unregister(["cursor"])
    assert "-Uninstall" in calls[0]
    calls.clear()
    data = mcp_clients.status()
    assert len(calls) == 1 and "-List" in calls[0] and "-Clients" not in calls[0]  # one process for all clients
    assert [r["id"] for r in data["clients"]] == list(mcp_clients.CLIENT_IDS)


def test_unknown_client_is_rejected_before_running_anything(script, monkeypatch):
    monkeypatch.setattr(mcp_clients.subprocess, "run", lambda *a, **k: pytest.fail("must not run"))
    with pytest.raises(ValueError, match="unknown client"):
        mcp_clients.register(["cursor", "notepad; calc"])


def test_missing_script_and_bad_output_raise_clients_error(monkeypatch, tmp_path):
    monkeypatch.setattr(mcp_clients, "script_path", lambda: None)
    with pytest.raises(mcp_clients.ClientsError, match="not found"):
        mcp_clients.status()
    stub = tmp_path / "s.ps1"
    stub.write_text("#")
    monkeypatch.setattr(mcp_clients, "script_path", lambda: stub)
    monkeypatch.setattr(
        mcp_clients.subprocess, "run", lambda cmd, **k: subprocess.CompletedProcess(cmd, 1, stdout="boom", stderr="")
    )
    with pytest.raises(mcp_clients.ClientsError, match="no JSON"):
        mcp_clients.status()


def test_launch_command_in_a_source_checkout_is_the_console_script():
    assert Path(mcp_clients.launch_command()).name == "onenote-mcp.exe"


# ---- REST routes ----


@pytest.fixture
def http():
    return TestClient(server.http_app)


def test_route_status_ok_and_503(http, monkeypatch):
    monkeypatch.setattr(mcp_clients, "status", lambda: {"command": "x", "server": "onenote-mcp", "clients": []})
    res = http.get("/api/mcp-clients")
    assert res.status_code == 200 and res.json()["success"] is True

    def boom():
        raise mcp_clients.ClientsError("no script")

    monkeypatch.setattr(mcp_clients, "status", boom)
    res = http.get("/api/mcp-clients")
    assert res.status_code == 503 and res.json()["success"] is False


def test_route_register_validates_body(http, monkeypatch):
    monkeypatch.setattr(mcp_clients, "register", lambda clients=None: [{"id": "cursor", "status": "registered"}])
    ok = http.post("/api/mcp-clients/register", json={"clients": ["cursor"]})
    assert ok.status_code == 200 and ok.json()["results"][0]["status"] == "registered"
    assert http.post("/api/mcp-clients/register", json={"clients": "cursor"}).status_code == 400
    assert http.post("/api/mcp-clients/register", json={"clients": [1]}).status_code == 400


def test_route_unknown_client_is_400(http):
    res = http.post("/api/mcp-clients/unregister", json={"clients": ["../../evil"]})
    assert res.status_code == 400 and "unknown client" in res.json()["message"]
