"""The novice web app is a contained loopback shim over the closed MCP surface."""

from __future__ import annotations

import base64
import json
import threading
import urllib.request
from pathlib import Path

import pytest

from deepreason import webapp


@pytest.fixture
def server():
    calls = []

    def scripted_tool(name, arguments):
        calls.append((name, dict(arguments)))
        if name == "get_readiness":
            return json.dumps({"ready": False, "guidance": "run deepreason setup"})
        if name == "start_run":
            attachments = arguments.get("attachments") or []
            observed = [Path(path).read_bytes() for path in attachments]
            return json.dumps(
                {
                    "run_id": "run-web-1",
                    "state": "accepted",
                    "evidence": (
                        {
                            "evidence_dossier_digest": "e" * 64,
                            "sources_admitted": len(observed),
                            "refusals": [],
                            "observed_bytes": [
                                body.decode("utf-8") for body in observed
                            ],
                        }
                        if attachments
                        else None
                    ),
                }
            )
        if name == "run_status":
            return json.dumps({"state": "stopped", "events": []})
        if name == "run_result":
            return json.dumps({"resolution": "answered", "answer": "42"})
        if name == "cancel_run":
            return json.dumps({"state": "cancelling"})
        raise ValueError(f"unexpected tool: {name}")

    instance = webapp.create_server("127.0.0.1", 0, tool=scripted_tool)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield instance, calls
    finally:
        instance.shutdown()
        instance.server_close()


def _request(instance, path, *, token=None, body=None, host=None):
    url = instance.url.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data)
    if token is not None:
        request.add_header("X-DeepReason-Token", token)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    if host is not None:
        request.add_header("Host", host)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def test_page_carries_the_token_and_api_requires_it(server):
    instance, _calls = server
    status, page = _request(instance, "/")
    assert status == 200
    assert instance.api_token in page.decode("utf-8")

    status, body = _request(instance, "/api/readiness")
    assert status == 403 and json.loads(body)["ok"] is False

    status, body = _request(instance, "/api/readiness", token=instance.api_token)
    payload = json.loads(body)
    assert status == 200 and payload["ok"] is True
    assert payload["data"]["guidance"] == "run deepreason setup"


def test_nonlocal_host_header_is_rejected(server):
    instance, _calls = server
    status, body = _request(
        instance,
        "/api/readiness",
        token=instance.api_token,
        host="evil.example.com",
    )
    assert status == 403
    assert "non-local" in json.loads(body)["error"]


def test_ask_stages_uploads_and_cleans_the_staging_copy(server):
    instance, calls = server
    status, body = _request(
        instance,
        "/api/ask",
        token=instance.api_token,
        body={
            "question": "What does the study say?",
            "attachments": [
                {
                    "name": "../..//study one.md",
                    "content_base64": base64.b64encode(
                        b"# Study\n\nWidgets have parts.\n"
                    ).decode("ascii"),
                }
            ],
        },
    )
    payload = json.loads(body)
    assert status == 200 and payload["ok"] is True
    assert payload["data"]["run_id"] == "run-web-1"
    evidence = payload["data"]["evidence"]
    assert evidence["sources_admitted"] == 1
    assert "Widgets have parts." in evidence["observed_bytes"][0]

    (name, arguments) = next(call for call in calls if call[0] == "start_run")
    staged = Path(arguments["attachments"][0])
    # Path traversal in the client-supplied name never leaves staging, and
    # the staging copy is deleted once admission has the bytes.
    assert ".." not in staged.name and " " not in staged.name
    assert not staged.exists()


def test_run_lifecycle_routes_pass_through_the_closed_surface(server):
    instance, calls = server
    token = instance.api_token
    status, body = _request(
        instance, "/api/status?run_id=run-web-1&since_seq=3", token=token
    )
    assert json.loads(body)["data"]["state"] == "stopped"
    status, body = _request(instance, "/api/result?run_id=run-web-1", token=token)
    assert json.loads(body)["data"]["answer"] == "42"
    status, body = _request(
        instance, "/api/cancel", token=token, body={"run_id": "run-web-1"}
    )
    assert json.loads(body)["data"]["state"] == "cancelling"
    assert [name for name, _ in calls] == [
        "run_status",
        "run_result",
        "cancel_run",
    ]
    assert calls[0][1] == {"run_id": "run-web-1", "since_seq": 3}


def test_malformed_requests_are_typed_errors_not_crashes(server):
    instance, _calls = server
    token = instance.api_token
    status, body = _request(instance, "/api/ask", token=token, body={"question": "  "})
    assert status == 400 and "question" in json.loads(body)["error"]
    status, body = _request(
        instance,
        "/api/ask",
        token=token,
        body={"question": "q", "attachments": [{"name": "x"}]},
    )
    assert status == 400
    status, body = _request(instance, "/api/nowhere", token=token)
    assert status == 404


def test_server_refuses_to_bind_beyond_loopback():
    with pytest.raises(ValueError, match="WEBAPP_LOCAL_ONLY"):
        webapp.create_server("0.0.0.0", 0)


def test_setup_options_are_listed_without_secrets(server):
    instance, _calls = server
    status, body = _request(
        instance, "/api/setup/options", token=instance.api_token
    )
    payload = json.loads(body)
    assert status == 200 and payload["ok"] is True
    providers = {item["id"]: item for item in payload["data"]["providers"]}
    assert "deepseek" in providers and "custom" in providers
    assert providers["custom"]["needs_endpoint"] is True
    assert providers["deepseek"]["needs_endpoint"] is False
    assert "key" in providers["deepseek"]["key_hint"].lower()
    # The options are choices only: no environment names, no stored values.
    assert "API_KEY" not in body.decode("utf-8")


def test_in_page_setup_stores_profile_and_key_without_echoing(
    server, tmp_path, monkeypatch
):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "dot"))
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    instance, _calls = server
    secret = "sk-test-never-echoed-1234"
    status, body = _request(
        instance,
        "/api/setup",
        token=instance.api_token,
        body={"provider": "deepseek", "api_key": secret},
    )
    payload = json.loads(body)
    assert status == 200 and payload["ok"] is True
    assert secret not in body.decode("utf-8")

    from deepreason.provider_profile import (
        credential_present,
        resolve_provider_profile,
    )

    profile = resolve_provider_profile(None).profile
    assert profile.provider == "deepseek"
    assert profile.context_window_tokens > profile.maximum_completion_tokens
    assert credential_present(profile)

    # A custom provider without its endpoint is a typed error, not a prompt.
    status, body = _request(
        instance,
        "/api/setup",
        token=instance.api_token,
        body={"provider": "custom", "api_key": secret},
    )
    payload = json.loads(body)
    assert payload["ok"] is False and "SETUP_ENDPOINT_REQUIRED" in payload["error"]


def test_qualification_endpoints_drive_the_single_flight_runner(server):
    instance, _calls = server

    class ScriptedRunner:
        def __init__(self):
            self.started = 0

        def start(self):
            self.started += 1
            return {"state": "running", "completed": 0, "total": 280}

        def status(self):
            return {"state": "running", "completed": 40, "total": 280}

    instance.qualification = ScriptedRunner()
    status, body = _request(
        instance, "/api/qualify", token=instance.api_token, body={}
    )
    assert json.loads(body)["data"]["state"] == "running"
    status, body = _request(
        instance, "/api/qualify/status", token=instance.api_token
    )
    assert json.loads(body)["data"]["completed"] == 40
    assert instance.qualification.started == 1


def test_apply_setup_is_typed_and_never_half_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "dot"))
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    from deepreason.easy import apply_setup
    from deepreason.provider_profile import setup_provider_profile_path

    with pytest.raises(ValueError, match="SETUP_KEY_REQUIRED"):
        apply_setup(provider="deepseek")
    # A refused setup writes nothing: no profile without a usable key.
    assert not setup_provider_profile_path().exists()

    path = apply_setup(provider="deepseek", api_key="sk-x")
    assert path.exists()
