"""Local web app for novice users: one page, one question, optional files.

This is deliberately a thin shim over the same closed MCP tool surface
(`deepreason.mcp_server.call_tool`), so the web app can do nothing the
validated facade cannot: no provider selection, no path authority beyond
the user's own uploads, no policy fields. Everything is standard library
— serving a page to a novice must not require installing a web stack.

Containment: the server binds to loopback only, rejects requests whose
Host header is not local (DNS-rebinding defence), and requires a
per-process token on every API call (cross-site request defence). The
page itself carries the token, so only pages served by this process can
drive the API.
"""

from __future__ import annotations

import base64
import hmac
import json
import re
import secrets
import shutil
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from deepreason.mcp_server import call_tool

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8710
MAX_BODY_BYTES = 96 * 1024 * 1024  # bounded transport; admission enforces its own budgets
MAX_UPLOAD_FILES = 16
_LOCAL_HOSTS = ("127.0.0.1", "localhost", "[::1]")
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")
_TOKEN_HEADER = "X-DeepReason-Token"


class WebAppError(ValueError):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(message)


def _sanitized_name(raw: str, index: int) -> str:
    base = _SAFE_NAME.sub("_", Path(str(raw)).name).lstrip(".")
    return f"{index:02}-{base}" if base else f"{index:02}-upload"


def _decoded_uploads(entries, staging: Path) -> list[str]:
    if not isinstance(entries, list):
        raise WebAppError(400, "attachments must be a list")
    if len(entries) > MAX_UPLOAD_FILES:
        raise WebAppError(400, f"at most {MAX_UPLOAD_FILES} files per question")
    paths: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not isinstance(
            entry.get("content_base64"), str
        ):
            raise WebAppError(400, "each attachment needs name and content_base64")
        try:
            data = base64.b64decode(entry["content_base64"], validate=True)
        except (ValueError, TypeError) as error:
            raise WebAppError(400, "attachment content is not valid base64") from error
        target = staging / _sanitized_name(entry.get("name", ""), index)
        target.write_bytes(data)
        paths.append(str(target))
    return paths


class _Handler(BaseHTTPRequestHandler):
    server_version = "DeepReasonWeb/0.1"
    protocol_version = "HTTP/1.1"

    # --- plumbing -----------------------------------------------------

    def log_message(self, format, *args):  # noqa: A002 - stdlib signature
        pass  # a novice-facing local app should not spam the terminal

    def _respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict) -> None:
        self._respond(
            status,
            json.dumps(payload, sort_keys=True).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _reject_nonlocal_host(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if host not in _LOCAL_HOSTS:
            self._json(403, {"ok": False, "error": "non-local Host rejected"})
            return True
        return False

    def _authorized(self) -> bool:
        supplied = self.headers.get(_TOKEN_HEADER, "")
        if hmac.compare_digest(supplied, self.server.api_token):
            return True
        self._json(403, {"ok": False, "error": "missing or invalid API token"})
        return False

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            raise WebAppError(400, "request body is required")
        if length > MAX_BODY_BYTES:
            raise WebAppError(413, "request body exceeds the fixed bound")
        try:
            body = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError) as error:
            raise WebAppError(400, "request body must be JSON") from error
        if not isinstance(body, dict):
            raise WebAppError(400, "request body must be a JSON object")
        return body

    def _tool(self, name: str, arguments: dict) -> None:
        try:
            self._json(200, {"ok": True, "data": json.loads(self.server.tool(name, arguments))})
        except Exception as error:  # noqa: BLE001 - single-user local surface
            # Local single-user surface: the full typed message (admission
            # refusal codes, readiness codes) is the most helpful response.
            self._json(200, {"ok": False, "error": str(error)})

    # --- routes -------------------------------------------------------

    def do_GET(self):  # noqa: N802 - stdlib signature
        if self._reject_nonlocal_host():
            return
        path, _, query = self.path.partition("?")
        if path == "/":
            page = PAGE_HTML.replace("__DEEPREASON_TOKEN__", self.server.api_token)
            self._respond(200, page.encode("utf-8"), "text/html; charset=utf-8")
            return
        if not path.startswith("/api/"):
            self._json(404, {"ok": False, "error": "not found"})
            return
        if not self._authorized():
            return
        params = {}
        for pair in query.split("&"):
            key, _, value = pair.partition("=")
            if key:
                params[key] = value
        if path == "/api/readiness":
            self._tool("get_readiness", {})
            return
        if path == "/api/setup/options":
            from deepreason.easy import setup_options

            self._json(200, {"ok": True, "data": {"providers": setup_options()}})
            return
        if path == "/api/qualify/status":
            self._json(
                200, {"ok": True, "data": self.server.qualification.status()}
            )
            return
        if path == "/api/status":
            arguments = {"run_id": params.get("run_id", "")}
            if params.get("since_seq"):
                arguments["since_seq"] = int(params["since_seq"])
            self._tool("run_status", arguments)
            return
        if path == "/api/result":
            self._tool("run_result", {"run_id": params.get("run_id", "")})
            return
        self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):  # noqa: N802 - stdlib signature
        if self._reject_nonlocal_host():
            return
        if not self._authorized():
            return
        try:
            if self.path == "/api/qualify":
                # An explicit start with an empty body: qualification spends
                # provider quota, so it never begins as a side effect.
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                self._json(
                    200,
                    {"ok": True, "data": self.server.qualification.start()},
                )
                return
            body = self._read_json_body()
            if self.path == "/api/setup":
                self._setup(body)
                return
            if self.path == "/api/ask":
                self._ask(body)
                return
            if self.path == "/api/cancel":
                self._tool("cancel_run", {"run_id": str(body.get("run_id", ""))})
                return
            if self.path == "/api/continue":
                self._tool(
                    "continue_run",
                    {
                        "run_id": str(body.get("run_id", "")),
                        "budget": body.get("budget") or {},
                    },
                )
                return
            self._json(404, {"ok": False, "error": "not found"})
        except WebAppError as error:
            self._json(error.status, {"ok": False, "error": str(error)})

    def _setup(self, body: dict) -> None:
        """Configure the AI service from the local page — never through MCP.

        The key transits one loopback request guarded by the page token,
        lands in the same user-only credential store the terminal wizard
        uses, and is never echoed back in any response.
        """

        from deepreason.easy import apply_setup, load_credentials

        provider = body.get("provider")
        if not isinstance(provider, str) or not provider.strip():
            raise WebAppError(400, "choose an AI service")

        def bounded_int(name):
            value = body.get(name)
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise WebAppError(400, f"{name} must be a positive whole number")
            return value

        try:
            apply_setup(
                provider=provider.strip(),
                api_key=(
                    body["api_key"]
                    if isinstance(body.get("api_key"), str)
                    else None
                ),
                endpoint=(
                    body["endpoint"].strip()
                    if isinstance(body.get("endpoint"), str)
                    else None
                ),
                model=(
                    body["model"].strip()
                    if isinstance(body.get("model"), str)
                    else None
                ),
                context_window_tokens=bounded_int("context_window_tokens"),
                maximum_completion_tokens=bounded_int(
                    "maximum_completion_tokens"
                ),
            )
        except ValueError as error:
            self._json(200, {"ok": False, "error": str(error)})
            return
        # Make the stored key visible to this already-running process so the
        # first question does not require a restart.
        load_credentials()
        self._json(200, {"ok": True, "data": {"configured": True}})

    def _ask(self, body: dict) -> None:
        question = body.get("question")
        if not isinstance(question, str) or not question.strip():
            raise WebAppError(400, "a question is required")
        arguments: dict = {"question": question}
        if isinstance(body.get("budget"), dict) and body["budget"]:
            arguments["budget"] = body["budget"]
        if body.get("allow_partial"):
            arguments["allow_partial"] = True
        uploads = body.get("attachments") or []
        staging: Path | None = None
        try:
            if uploads:
                staging = Path(
                    tempfile.mkdtemp(prefix="deepreason-web-uploads-")
                )
                arguments["attachments"] = _decoded_uploads(uploads, staging)
            outcome = {"ok": True, "data": json.loads(self.server.tool("start_run", arguments))}
        except WebAppError:
            raise
        except Exception as error:  # noqa: BLE001 - single-user local surface
            outcome = {"ok": False, "error": str(error)}
        finally:
            if staging is not None:
                # Admission stored every accepted source's exact bytes in the
                # managed store; the transport staging copy is disposable —
                # removed before responding so no orphan outlives the request.
                shutil.rmtree(staging, ignore_errors=True)
        self._json(200, outcome)


class QualificationRunner:
    """One background qualification at a time, with bounded live progress.

    Qualification spends provider calls, so the page must start it with an
    explicit click, watch real progress, and land on the same durable tier
    record the CLI produces — this runner wraps the exact CLI ladder.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._status: dict = {"state": "idle", "completed": 0, "total": 0}

    def status(self) -> dict:
        with self._lock:
            return dict(self._status)

    def _update(self, **fields) -> None:
        with self._lock:
            self._status.update(fields)

    def start(self) -> dict:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return dict(self._status)
            self._status = {"state": "running", "completed": 0, "total": 0}
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return dict(self._status)

    def _run(self) -> None:
        try:
            from deepreason.cli.doctor import run_production_contract_doctor
            from deepreason.preparation import qualification_subject_manifest
            from deepreason.provider_profile import (
                credential_present,
                provider_state_dir,
                resolve_provider_profile,
            )
            from deepreason.qualification import (
                QualificationError,
                load_completed_qualification,
                qualification_subject_digest,
                resolve_completed_qualification,
                shallow_tier_record_from_cases,
                write_qualification_tier,
            )
            from deepreason.shallow_fitness import run_shallow_fitness_battery

            profile = resolve_provider_profile(None).profile
            if not credential_present(profile):
                raise QualificationError(
                    "PROVIDER_CREDENTIAL_MISSING",
                    "configured provider credential is absent",
                )
            manifest = qualification_subject_manifest(profile)
            cache_dir = provider_state_dir() / "qualification-cache"
            subject = qualification_subject_digest(manifest, profile)
            try:
                load_completed_qualification(cache_dir, subject)
                self._update(state="passed", tier="full", reused=True)
                return
            except QualificationError as error:
                if error.code != "QUALIFICATION_NOT_CONFIGURED":
                    raise

            def executor(manifest_value):
                return run_production_contract_doctor(
                    manifest_value,
                    progress_callback=lambda completed, total: self._update(
                        completed=completed, total=total
                    ),
                )

            try:
                resolve_completed_qualification(
                    manifest, profile, cache_dir=cache_dir, executor=executor
                )
                self._update(state="passed", tier="full", reused=False)
            except ValueError as full_error:
                if not str(full_error).startswith(
                    (
                        "QUALIFICATION_EXECUTION_FAILED",
                        "QUALIFICATION_EXECUTION_INVALID",
                        "DOCTOR_",
                    )
                ):
                    raise
                self._update(phase="shallow_fitness")
                cases = run_shallow_fitness_battery(profile)
                record = shallow_tier_record_from_cases(
                    cases, subject_digest=subject, profile=profile
                )
                write_qualification_tier(record, cache_dir)
                if record.tier == "shallow":
                    self._update(state="passed", tier="shallow", reused=False)
                else:
                    self._update(
                        state="failed",
                        tier=record.tier,
                        error=str(full_error)[:500],
                    )
        except Exception as error:  # noqa: BLE001 - surfaced to the local page
            self._update(state="failed", error=str(error)[:500])


class DeepReasonWebServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, host: str, port: int, *, tool=call_tool):
        super().__init__((host, port), _Handler)
        self.api_token = secrets.token_urlsafe(32)
        self.tool = tool
        self.qualification = QualificationRunner()

    @property
    def url(self) -> str:
        return f"http://{self.server_address[0]}:{self.server_address[1]}/"


def create_server(
    host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, *, tool=call_tool
) -> DeepReasonWebServer:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("WEBAPP_LOCAL_ONLY: the novice web app serves loopback only")
    return DeepReasonWebServer(host, port, tool=tool)


def serve(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    *,
    open_browser: bool = True,
) -> int:
    from deepreason.easy import load_credentials

    load_credentials()  # keys stored by `deepreason setup` reach web runs too
    server = create_server(host, port)
    print(f"DeepReason is running at {server.url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        import webbrowser

        threading.Timer(0.4, webbrowser.open, args=(server.url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DeepReason</title>
<style>
:root {
  color-scheme: light dark;
  --bg: #f6f7f9; --panel: #ffffff; --ink: #1c2733; --muted: #5b6b7b;
  --line: #dde3ea; --accent: #245ecb; --good: #1c7c46; --warn: #a05a00;
  --bad: #b3372e;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #10161d; --panel: #19212b; --ink: #e8edf2; --muted: #9aa8b6;
          --line: #2a3541; --accent: #6ea0ff; --good: #4fc07f; --warn: #e0a04a;
          --bad: #e06a5e; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 16px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 46rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
h1 { font-size: 1.6rem; margin: 0 0 0.25rem; }
.tagline { color: var(--muted); margin: 0 0 1.5rem; }
.card { background: var(--panel); border: 1px solid var(--line);
        border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; }
.banner { display: none; border-left: 4px solid var(--warn); }
.banner.ready { border-left-color: var(--good); }
.banner p { margin: 0.25rem 0 0; }
textarea { width: 100%; min-height: 5.5rem; resize: vertical; padding: 0.7rem;
           border: 1px solid var(--line); border-radius: 8px; font: inherit;
           background: var(--bg); color: var(--ink); }
.filerow { margin: 0.75rem 0; }
.filelist { list-style: none; margin: 0.5rem 0 0; padding: 0; color: var(--muted);
            font-size: 0.9rem; }
button { font: inherit; border: 0; border-radius: 8px; padding: 0.6rem 1.3rem;
         cursor: pointer; }
#ask { background: var(--accent); color: #fff; font-weight: 600; }
#ask:disabled { opacity: 0.5; cursor: default; }
#cancel { background: transparent; color: var(--bad); border: 1px solid var(--bad);
          display: none; margin-left: 0.5rem; }
details { margin-top: 0.75rem; color: var(--muted); }
details input { width: 7rem; margin-right: 1rem; font: inherit; padding: 0.25rem;
                border: 1px solid var(--line); border-radius: 6px;
                background: var(--bg); color: var(--ink); }
#progress { display: none; }
#events { font-family: ui-monospace, monospace; font-size: 0.82rem;
          white-space: pre-wrap; max-height: 14rem; overflow-y: auto;
          color: var(--muted); margin: 0.5rem 0 0; }
#result { display: none; }
#answer { white-space: pre-wrap; }
.status-line { color: var(--muted); font-size: 0.9rem; }
.err { color: var(--bad); }
summary { cursor: pointer; }
pre.raw { overflow-x: auto; font-size: 0.78rem; background: var(--bg);
          padding: 0.75rem; border-radius: 8px; }
.spin { display: inline-block; width: 0.9rem; height: 0.9rem; vertical-align: -2px;
        border: 2px solid var(--muted); border-top-color: transparent;
        border-radius: 50%; animation: r 0.8s linear infinite; }
@keyframes r { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<main>
  <h1>DeepReason</h1>
  <p class="tagline">Ask a question. Attach documents if you have them.
     DeepReason reasons carefully and tells you how sure it is.</p>

  <div id="banner" class="card banner">
    <strong id="banner-title"></strong>
    <p id="banner-text"></p>
  </div>

  <div id="setup" class="card" style="display:none">
    <h2>Connect an AI service</h2>
    <p class="status-line">DeepReason uses an AI service you have an account
       with. Pick yours, paste its API key, and you're done — the key is
       stored on this computer only, readable only by your user account.</p>
    <div id="provider-list"></div>
    <div id="custom-fields" style="display:none">
      <p><input id="setup-endpoint" type="text" size="40"
         placeholder="Service URL, e.g. https://api.example.com/v1"></p>
      <p><input id="setup-model" type="text" size="40"
         placeholder="Model name, e.g. my-model-v2"></p>
      <p>
        <label>Context window <input id="setup-context" type="number"
          min="1" placeholder="32768"></label>
        <label>Max completion <input id="setup-completion" type="number"
          min="1" placeholder="4096"></label>
      </p>
    </div>
    <p><span id="key-hint" class="status-line"></span></p>
    <p><input id="setup-key" type="password" size="40"
       placeholder="Paste your API key"></p>
    <p><button id="setup-save">Save</button></p>
    <p id="setup-error" class="err"></p>
  </div>

  <div id="qualify" class="card" style="display:none">
    <h2>One-time model check</h2>
    <p class="status-line">Before full reasoning, DeepReason verifies your
       model can do this work reliably. The check runs a few hundred small
       test calls against your AI service (it uses some of your quota) and
       is remembered afterwards.</p>
    <p>
      <button id="qualify-start">Run the check</button>
      <span id="qualify-progress" class="status-line"></span>
    </p>
    <p id="qualify-error" class="err"></p>
  </div>

  <div class="card">
    <textarea id="question" placeholder="What would you like to understand?"></textarea>
    <div class="filerow">
      <input type="file" id="files" multiple>
      <ul id="filelist" class="filelist"></ul>
    </div>
    <details>
      <summary>Advanced</summary>
      <p>
        <label>Cycles <input id="cycles" type="number" min="1"></label>
        <label>Token budget <input id="tokens" type="number" min="1"></label>
        <label><input id="allow-partial" type="checkbox"> allow partial admission</label>
      </p>
    </details>
    <p>
      <button id="ask">Ask</button>
      <button id="cancel">Stop</button>
    </p>
    <p id="ask-error" class="err"></p>
  </div>

  <div id="progress" class="card">
    <span class="spin"></span> <span id="progress-label">Reasoning…</span>
    <div id="events"></div>
  </div>

  <div id="result" class="card">
    <h2 id="result-title"></h2>
    <p id="evidence-line" class="status-line"></p>
    <div id="answer"></div>
    <details><summary>Full record</summary><pre id="raw" class="raw"></pre></details>
  </div>
</main>
<script>
"use strict";
const TOKEN = "__DEEPREASON_TOKEN__";
const $ = (id) => document.getElementById(id);
let runId = null, sinceSeq = -1, pollTimer = null, evidence = null;

async function api(path, options) {
  const opts = options || {};
  opts.headers = Object.assign({"X-DeepReason-Token": TOKEN}, opts.headers || {});
  const response = await fetch(path, opts);
  return response.json();
}

let setupOptionsLoaded = false;

async function refreshReadiness() {
  const banner = $("banner");
  try {
    const reply = await api("/api/readiness");
    if (!reply.ok) throw new Error(reply.error);
    const r = reply.data;
    const state = r.qualification_state || "";
    const needsSetup = ["profile_missing", "profile_invalid",
                        "credential_missing"].includes(state);
    const needsQualify = ["unqualified", "ready_shallow"].includes(state);
    banner.style.display = "block";
    banner.classList.toggle("ready", !!r.ready);
    $("banner-title").textContent = r.ready
      ? "Ready" : needsSetup ? "Let's get set up"
      : needsQualify ? "Almost there" : "One-time setup needed";
    $("banner-text").textContent = r.ready
      ? "" : needsSetup
      ? "Two quick steps: connect your AI service, then run a one-time check."
      : (r.guidance || r.next_action || "");
    $("setup").style.display = needsSetup ? "block" : "none";
    $("qualify").style.display = needsQualify ? "block" : "none";
    $("ask").disabled = !r.ready;
    if (needsSetup && !setupOptionsLoaded) await loadSetupOptions();
  } catch (e) {
    banner.style.display = "block";
    $("banner-title").textContent = "Cannot reach DeepReason";
    $("banner-text").textContent = String(e);
  }
}

let providerOptions = [];

async function loadSetupOptions() {
  const reply = await api("/api/setup/options");
  if (!reply.ok) return;
  providerOptions = reply.data.providers;
  setupOptionsLoaded = true;
  const list = $("provider-list");
  list.innerHTML = "";
  for (const option of providerOptions) {
    const label = document.createElement("label");
    label.style.display = "block";
    const radio = document.createElement("input");
    radio.type = "radio"; radio.name = "provider"; radio.value = option.id;
    radio.addEventListener("change", () => selectProvider(option));
    label.appendChild(radio);
    label.appendChild(document.createTextNode(" " + option.label));
    list.appendChild(label);
  }
}

function selectProvider(option) {
  $("custom-fields").style.display = option.needs_endpoint ? "block" : "none";
  $("key-hint").textContent = "Your API key comes from: " + option.key_hint;
}

$("setup-save").addEventListener("click", async () => {
  $("setup-error").textContent = "";
  const chosen = document.querySelector('input[name="provider"]:checked');
  if (!chosen) { $("setup-error").textContent = "Pick an AI service first."; return; }
  const body = {provider: chosen.value, api_key: $("setup-key").value};
  const option = providerOptions.find((item) => item.id === chosen.value);
  if (option && option.needs_endpoint) {
    body.endpoint = $("setup-endpoint").value;
    body.model = $("setup-model").value;
    if ($("setup-context").value)
      body.context_window_tokens = Number($("setup-context").value);
    if ($("setup-completion").value)
      body.maximum_completion_tokens = Number($("setup-completion").value);
  }
  $("setup-save").disabled = true;
  try {
    const reply = await api("/api/setup", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    if (!reply.ok) throw new Error(reply.error);
    $("setup-key").value = "";
    await refreshReadiness();
  } catch (e) {
    $("setup-error").textContent = String(e.message || e);
  } finally {
    $("setup-save").disabled = false;
  }
});

let qualifyTimer = null;

$("qualify-start").addEventListener("click", async () => {
  $("qualify-error").textContent = "";
  $("qualify-start").disabled = true;
  const reply = await api("/api/qualify", {method: "POST"});
  if (!reply.ok) {
    $("qualify-error").textContent = reply.error;
    $("qualify-start").disabled = false;
    return;
  }
  qualifyTimer = setInterval(pollQualification, 2000);
});

async function pollQualification() {
  const reply = await api("/api/qualify/status");
  if (!reply.ok) return;
  const status = reply.data;
  if (status.state === "running") {
    $("qualify-progress").textContent = status.phase === "shallow_fitness"
      ? "full check did not pass; trying the reduced check…"
      : status.total
      ? "checking… " + status.completed + " of " + status.total + " test calls"
      : "starting…";
    return;
  }
  clearInterval(qualifyTimer); qualifyTimer = null;
  $("qualify-start").disabled = false;
  if (status.state === "passed") {
    $("qualify-progress").textContent = status.tier === "full"
      ? "Passed — you're ready to ask questions."
      : "Passed the reduced check only; answers use the reduced engine.";
    await refreshReadiness();
  } else {
    $("qualify-progress").textContent = "";
    $("qualify-error").textContent = status.error ||
      "The check did not complete. You can run it again.";
  }
}

$("files").addEventListener("change", () => {
  const list = $("filelist");
  list.innerHTML = "";
  for (const f of $("files").files) {
    const li = document.createElement("li");
    li.textContent = f.name + " (" + Math.ceil(f.size / 1024) + " KB)";
    list.appendChild(li);
  }
});

function readFile(f) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("could not read " + f.name));
    reader.onload = () => resolve({
      name: f.name,
      content_base64: String(reader.result).split(",", 2)[1] || "",
    });
    reader.readAsDataURL(f);
  });
}

$("ask").addEventListener("click", async () => {
  $("ask-error").textContent = "";
  const question = $("question").value.trim();
  if (!question) { $("ask-error").textContent = "Type a question first."; return; }
  const body = {question};
  const budget = {};
  if ($("cycles").value) budget.cycles = Number($("cycles").value);
  if ($("tokens").value) budget.token_budget = Number($("tokens").value);
  if (Object.keys(budget).length) body.budget = budget;
  if ($("allow-partial").checked) body.allow_partial = true;
  try {
    if ($("files").files.length) {
      body.attachments = await Promise.all(Array.from($("files").files, readFile));
    }
    $("ask").disabled = true;
    $("result").style.display = "none";
    $("events").textContent = "";
    $("progress").style.display = "block";
    $("progress-label").textContent = "Starting…";
    const reply = await api("/api/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body),
    });
    if (!reply.ok) throw new Error(reply.error);
    runId = reply.data.run_id;
    sinceSeq = -1;
    evidence = reply.data.evidence || null;
    if (evidence) {
      appendEvent("evidence admitted: " + evidence.sources_admitted +
        " source(s), dossier " + evidence.evidence_dossier_digest.slice(0, 12) + "…");
      for (const refusal of evidence.refusals || []) {
        appendEvent("refused: " + JSON.stringify(refusal));
      }
    }
    $("cancel").style.display = "inline-block";
    $("progress-label").textContent = "Reasoning…";
    pollTimer = setInterval(poll, 2500);
  } catch (e) {
    $("ask-error").textContent = String(e.message || e);
    $("progress").style.display = "none";
    $("ask").disabled = false;
  }
});

$("cancel").addEventListener("click", async () => {
  if (!runId) return;
  await api("/api/cancel", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({run_id: runId}),
  });
  appendEvent("stop requested; finishing the current cycle…");
});

function appendEvent(line) {
  const box = $("events");
  box.textContent += (box.textContent ? "\\n" : "") + line;
  box.scrollTop = box.scrollHeight;
}

async function poll() {
  try {
    const reply = await api("/api/status?run_id=" + encodeURIComponent(runId) +
      "&since_seq=" + sinceSeq);
    if (!reply.ok) throw new Error(reply.error);
    const status = reply.data;
    for (const event of status.events || []) {
      if (typeof event.seq === "number") sinceSeq = Math.max(sinceSeq, event.seq);
      appendEvent(event.message || event.activity || JSON.stringify(event));
    }
    const state = String(status.state || status.lifecycle || "");
    if (["running", "accepted", "queued", "starting"].includes(state)) return;
    clearInterval(pollTimer); pollTimer = null;
    await showResult();
  } catch (e) {
    appendEvent("status check failed: " + String(e.message || e));
  }
}

async function showResult() {
  $("progress").style.display = "none";
  $("cancel").style.display = "none";
  $("ask").disabled = false;
  const reply = await api("/api/result?run_id=" + encodeURIComponent(runId));
  $("result").style.display = "block";
  if (!reply.ok) {
    $("result-title").textContent = "No result yet";
    $("answer").textContent = reply.error;
    $("raw").textContent = "";
    return;
  }
  const data = reply.data;
  const answer = data.answer || data.composed_answer || data.prose ||
    data.summary || data.thesis || "";
  const resolution = data.resolution || data.state || data.status || "finished";
  $("result-title").textContent = "Outcome: " + resolution;
  $("evidence-line").textContent = evidence
    ? "Grounded in " + evidence.sources_admitted + " attached source(s)." : "";
  $("answer").textContent = answer || (
    "The full reasoning record is below. This run ended in state \\"" +
    resolution + "\\".");
  $("raw").textContent = JSON.stringify(data, null, 2);
}

refreshReadiness();
setInterval(refreshReadiness, 30000);
</script>
</body>
</html>
"""


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="deepreason-web")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    return serve(args.host, args.port, open_browser=not args.no_browser)


__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DeepReasonWebServer",
    "create_server",
    "main",
    "serve",
]
