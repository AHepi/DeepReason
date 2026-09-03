"""The stop report — the harness's own first account of why a run stopped.

A pure reader over one run root (or one home). It answers the question a
diagnosing window asks first, and answers it from the RECORD rather than
from the settings file the window wrote: what actually ran, what the
pre-run check already knew, how the provider behaved, which of four
boxes the stop belongs in, and whether the run can still be continued.

The classification never asserts a defect. It ranks four boxes —
CONFIGURATION, ENVIRONMENT, MODEL, HARNESS — by the typed evidence for
and against each, and says which are ruled out and why. HARNESS is
claimable only when the other three are ruled out with cited evidence,
because "the code is broken" is the conclusion that costs the most to
reach wrongly.

Two constraints this module may not relax:

* It never writes into a root. It reads durable sidecars and the log,
  and constructs no `Harness` of its own; `--verify` delegates to
  `invariants.verify_root`, which opens the root `read_only=True`. A
  writable open repairs, and therefore destroys, the evidence.
* It reads a run-config YAML ONLY when one is passed explicitly, and
  then only to populate the diff between what the operator wrote and
  what compiled. Every other line comes from the record, because a
  report derived from the settings file cannot contradict the settings
  file — which is the whole failure this instrument exists to remove.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "deepreason-stop-report.v1"

BOXES = ("CONFIGURATION", "ENVIRONMENT", "MODEL", "HARNESS")

SUPPORTED = "SUPPORTED"
RULED_OUT = "RULED OUT"
NO_EVIDENCE = "NO EVIDENCE EITHER WAY"

_VERDICT_WEIGHT = {SUPPORTED: 2, NO_EVIDENCE: 1, RULED_OUT: 0}

# A transport wall is a streak, not a single blip: one disconnect is noise
# on any long run, and the P-A1 root's 41 on a single endpoint is the shape
# that actually stopped a run. The threshold sits between them.
DISCONNECT_STREAK = 5

# Qualification failure codes that name the environment rather than the
# model. A pair that failed only these did not fail on capability — the
# distinction Phase-1 PARKED.md P3 had to make by hand ("Not a capability
# failure, not a schema failure").
_ENVIRONMENT_CODE_MARKERS = ("429", "5XX", "TIMEOUT", "TRANSPORT",
                             "DISCONNECT", "UNAVAILABLE", "CIRCUIT")

_REASONING_OMITTED = "omitted → provider default"

# A run that reached its budget and finished did not fail. Attributing a
# box to it manufactures blame the record does not carry (operator law,
# 2026-08-29: "clean stop. with an assurance that continuing is possible").
_CLEAN_STOP_REASONS = ("budget_exhausted", "cycles_exhausted", "goal_reached")


class StopReportError(Exception):
    """A typed refusal: the path is not something this reader can report on."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# Resolution. Deliberately NOT `results.resolve_results_root`: that one
# refuses a home holding no run root, and a configuration error that fails
# qualification never mints one. Three of the six recorded failures this
# report was built against are exactly that case.
# ---------------------------------------------------------------------------

def resolve_report_source(path: Path | str) -> tuple[Path, str]:
    """Resolve to (path, kind).

    Three kinds, because a failure can stop at three different depths and
    the operator needs a report at each:

    * ``root`` — a directory holding ``log.jsonl``: the run reasoned.
    * ``root-no-log`` — a run directory that compiled a manifest and ran
      qualification but never opened a log. A configuration error caught
      by the gate stops here, which is where the operator's own example
      landed; the manifest is present, so section 1 is still answerable.
    * ``home-no-root`` — a home whose qualification is cached but which
      minted no run directory at all.
    """

    base = Path(path).expanduser()
    if (base / "log.jsonl").is_file():
        return base, "root"
    if ((base / "production-contract-qualification.json").is_file()
            or (base / "run-manifest.json").is_file()):
        return base, "root-no-log"
    if not base.is_dir():
        raise StopReportError(
            "STOP_REPORT_PATH_NOT_FOUND",
            f"{base} is not a directory: neither a run root nor a home",
        )

    runs = base / "runs"
    candidates: list[Path] = []
    if runs.is_dir():
        candidates = sorted(
            entry for entry in runs.iterdir()
            if entry.is_dir() and (entry / "log.jsonl").is_file()
        )
    if len(candidates) == 1:
        return candidates[0], "root"
    if candidates:
        listed = "\n".join(f"  {entry}" for entry in candidates)
        raise StopReportError(
            "STOP_REPORT_HOME_AMBIGUOUS",
            f"{base} holds {len(candidates)} run roots; name one:\n{listed}",
        )
    if _home_qualification(base) is not None:
        return base, "home-no-root"
    raise StopReportError(
        "STOP_REPORT_SOURCE_NOT_FOUND",
        f"{base} is neither a run root (no log.jsonl) nor a home holding "
        f"one or a qualification record",
    )


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _home_qualification(home: Path) -> tuple[dict, str] | None:
    """The newest cached qualification in a home, with its subject digest.

    The cache is keyed by subject digest and the digest IS the filename,
    so the caller can say which subject a cached result came from.
    """

    cache = home / "qualification-cache"
    if not cache.is_dir():
        return None
    for entry in sorted(cache.glob("*.json")):
        payload = _read_json(entry)
        if isinstance(payload, dict) and payload.get("pairs") is not None:
            return payload, payload.get("subject_digest") or entry.stem
    return None


def _absent(reason: str) -> dict[str, Any]:
    return {"absent": True, "reason": reason}


# ---------------------------------------------------------------------------
# Section 1 — WHAT ACTUALLY RAN
# ---------------------------------------------------------------------------

def _split_armed_seats(events: list[dict]) -> set[tuple[str, int]]:
    armed = set()
    for event in events:
        llm = event.get("llm") or {}
        for attempt in llm.get("attempt_trace") or []:
            if attempt.get("split_legs"):
                armed.add((llm.get("role") or "", attempt.get("seat") or 0))
    return armed


def _what_actually_ran(manifest: dict | None, events: list[dict]) -> dict[str, Any]:
    if not manifest:
        return _absent("no run-manifest.json: the run never compiled a manifest")

    armed = _split_armed_seats(events)
    seats: list[dict[str, Any]] = []
    for role in sorted(manifest.get("roles") or {}):
        for index, entry in enumerate(manifest["roles"][role] or []):
            reasoning = entry.get("reasoning")
            seats.append({
                "role": role,
                "seat": index,
                "model_id": entry.get("model_id"),
                "model_revision": entry.get("model_revision"),
                "family": entry.get("family"),
                "provider": entry.get("provider"),
                "endpoint_id": entry.get("endpoint_id"),
                "model_profile": manifest.get("model_profile"),
                # An omitted knob is the provider's DEFAULT, never "off".
                "reasoning": _REASONING_OMITTED if reasoning is None else reasoning,
                "max_tokens": entry.get("max_tokens"),
                "timeout_s": entry.get("timeout_s"),
                "output_mechanism": entry.get("output_mechanism"),
                "context_window_tokens": entry.get("context_window_tokens"),
                "split_protocol": ("armed" if (role, index) in armed
                                   else "not observed in this run"),
            })

    notices = list(manifest.get("compile_notices") or [])
    gates: list[dict[str, Any]] = []
    for notice in notices:
        if notice.get("code") != "ENGINE_CONFIG_FIELD_NOT_CARRIED":
            continue
        pointer = notice.get("pointer") or ""
        gates.append({
            "field": pointer.rsplit("/", 1)[-1],
            "pointer": pointer,
            "value": notice.get("value"),
            "resolution": notice.get("resolution"),
            "carried": False,
            "note": "restored at run time from notice",
        })

    engine_config = {}
    raw = manifest.get("engine_config_json")
    if isinstance(raw, str):
        try:
            engine_config = json.loads(raw)
        except ValueError:
            engine_config = {}
    embedder_model = engine_config.get("EMBEDDER_MODEL")

    return {
        "absent": False,
        "seats": seats,
        "gates_restored_from_notice": sorted(gates, key=lambda row: row["pointer"]),
        "compile_notices": notices,
        # Null means the run measured with hashing. Do not guess a model.
        "embedder": "hashing" if embedder_model in (None, "") else embedder_model,
        "engine_profile": manifest.get("engine_profile"),
        "concurrency": manifest.get("concurrency"),
        "source_config_hash": manifest.get("source_config_hash"),
    }


# ---------------------------------------------------------------------------
# Section 2 — PRE-RUN CHECK
# ---------------------------------------------------------------------------

def _qualification_rows(payload: dict) -> list[dict[str, Any]]:
    cases_per_pair = payload.get("representative_cases_per_pair")
    rows = []
    for pair in payload.get("pairs") or []:
        descriptor = pair.get("pair") or {}
        codes: dict[str, int] = {}
        for case in pair.get("cases") or []:
            if case.get("eventual_valid"):
                continue
            code = case.get("failure_code")
            if code:
                codes[code] = codes.get(code, 0) + 1
        rows.append({
            "role": descriptor.get("role"),
            "seat": descriptor.get("seat"),
            "contract_id": descriptor.get("contract_id"),
            "endpoint_id": descriptor.get("endpoint_id"),
            "model_id": descriptor.get("model_id"),
            "cases": len(pair.get("cases") or []) or cases_per_pair,
            "first_pass_valid_count": pair.get("first_pass_valid_count"),
            "eventual_valid_count": pair.get("eventual_valid_count"),
            "repair_count": pair.get("repair_count"),
            "qualified": pair.get("qualified"),
            "failure_codes": dict(sorted(codes.items())),
        })
    return sorted(rows, key=lambda row: (str(row["role"]), row["seat"] or 0,
                                         str(row["contract_id"])))


def _pre_run_check(qualification, digest, cached) -> dict[str, Any]:
    if qualification is None:
        return _absent("no qualification record: neither the root nor the "
                       "home carries one")
    rows = _qualification_rows(qualification)
    summary = qualification.get("summary") or {}
    return {
        "absent": False,
        "cached": cached,
        "subject_digest": digest,
        "representative_cases_per_pair":
            qualification.get("representative_cases_per_pair"),
        "summary": summary,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Section 3 — PROVIDER HEALTH
# ---------------------------------------------------------------------------

def _walk_attempt(attempt: dict):
    yield attempt
    for leg in attempt.get("split_legs") or []:
        yield leg


def _provider_health(events: list[dict]) -> dict[str, Any]:
    per_seat: dict[tuple[str, int, str], dict[str, Any]] = {}
    for event in events:
        llm = event.get("llm") or {}
        role = llm.get("role")
        if role is None:
            continue
        for attempt in llm.get("attempt_trace") or []:
            key = (role, attempt.get("seat") or 0, attempt.get("endpoint_id") or "")
            row = per_seat.setdefault(key, {
                "role": role,
                "seat": attempt.get("seat") or 0,
                "endpoint_id": attempt.get("endpoint_id"),
                "attempts": 0,
                "invalid_attempts": 0,
                "zero_token_returns": 0,
                "truncated_at_cap": 0,
                "truncated_when_invalid": 0,
                "faults_by_kind": {},
                "http_429_messages": [],
                "last_fault": None,
                "validation_paths": {},
            })
            row["attempts"] += 1
            invalid = attempt.get("valid") is False
            if invalid:
                row["invalid_attempts"] += 1
            path = attempt.get("validation_path") or ""
            if path:
                row["validation_paths"][path] = row["validation_paths"].get(path, 0) + 1
            for leg in _walk_attempt(attempt):
                if leg.get("tokens") == 0 or leg.get("usage_unknown"):
                    row["zero_token_returns"] += 1
                if leg.get("natural_stop") is False and leg.get("tokens"):
                    row["truncated_at_cap"] += 1
                    if invalid:
                        row["truncated_when_invalid"] += 1
                for fault in leg.get("transport_diagnostics") or []:
                    text = str(fault)
                    kind = text.split(":", 1)[0]
                    row["faults_by_kind"][kind] = row["faults_by_kind"].get(kind, 0) + 1
                    row["last_fault"] = text
                    if "HTTP-429" in text:
                        message = text.split(":", 2)[-1]
                        if message not in row["http_429_messages"]:
                            row["http_429_messages"].append(message)

    if not per_seat:
        return _absent("no provider calls recorded in log.jsonl")
    rows = []
    for key in sorted(per_seat):
        row = per_seat[key]
        row["faults_by_kind"] = dict(sorted(row["faults_by_kind"].items()))
        row["validation_paths"] = dict(sorted(row["validation_paths"].items()))
        rows.append(row)
    return {"absent": False, "seats": rows}


# ---------------------------------------------------------------------------
# Section 4 — THE STOP, CLASSIFIED
# ---------------------------------------------------------------------------

_EXHAUSTION_MARKERS = (
    "terminally exhausted",
    "insufficient_capability",
    "insufficient capability",
    "smallest authorized contract",
)

_SCHEMA_MARKERS = ("schema", "did not validate", "invalid json", "contract")


def _is_environment_code(code: str) -> bool:
    upper = str(code).upper()
    if "HTTP_5" in upper or "HTTP-5" in upper:
        return True
    return any(marker in upper for marker in _ENVIRONMENT_CODE_MARKERS)


def _implicated(status: dict | None, health: dict, pre_run: dict) -> list[dict]:
    """Seats the stop plausibly touched: those named in the stop message,
    else the seats that actually made provider calls."""

    message = str((status or {}).get("message") or "").lower()
    seats = [] if health.get("absent") else list(health.get("seats") or [])
    named = [row for row in seats if str(row["role"]).lower() in message]
    return named or seats


def _classify(status, manifest, events, health, pre_run, config_diff) -> dict[str, Any]:
    message = str((status or {}).get("message") or "")
    lowered = message.lower()
    boxes: dict[str, dict[str, Any]] = {
        name: {"verdict": NO_EVIDENCE, "supporting": [], "ruling_out": [], "notes": []}
        for name in BOXES
    }

    state = (status or {}).get("state")
    stop_reason = (status or {}).get("stop_reason")
    clean_stop = state == "completed" or (
        state != "failed" and stop_reason in _CLEAN_STOP_REASONS)

    implicated = _implicated(status, health, pre_run)
    implicated_keys = {(row["role"], row["seat"]) for row in implicated}
    rows = [] if pre_run.get("absent") else list(pre_run.get("rows") or [])
    failing_rows = [row for row in rows if row["qualified"] is False]
    if failing_rows:
        implicated_rows = failing_rows
    else:
        implicated_rows = [row for row in rows
                           if (row["role"], row["seat"]) in implicated_keys] or rows

    if clean_stop:
        reason = (f"the run reached a clean terminal (state={state!r}, "
                  f"stop_reason={stop_reason!r}); there is no failure to "
                  f"attribute. Section 5 reports whether it can be continued.")
        for box in boxes.values():
            box["verdict"] = RULED_OUT
            box["ruling_out"].append(reason)
        return {
            "absent": False,
            "clean_stop": True,
            "stop_message": message,
            "ranked": list(BOXES),
            "boxes": boxes,
            "implicated_seats": sorted(
                f"{row['role']}#{row['seat']}" for row in implicated),
        }

    # ---- ENVIRONMENT ------------------------------------------------------
    env = boxes["ENVIRONMENT"]
    http_429 = 0
    disconnects: dict[str, int] = {}
    for row in ([] if health.get("absent") else health.get("seats") or []):
        for kind, count in row["faults_by_kind"].items():
            if kind == "RemoteDisconnected":
                endpoint = row["endpoint_id"] or ""
                disconnects[endpoint] = disconnects.get(endpoint, 0) + count
        http_429 += sum(len(row["http_429_messages"]) and count
                        for kind, count in row["faults_by_kind"].items()
                        if kind == "HTTPError" and row["http_429_messages"])
        for message_text in row["http_429_messages"]:
            env["supporting"].append(
                f"{row['role']}#{row['seat']} on {row['endpoint_id']}: "
                f"HTTP 429 from the provider — \"{message_text.strip()}\"")
    worst_endpoint = max(disconnects.items(), key=lambda kv: kv[1], default=None)
    if worst_endpoint and worst_endpoint[1] >= DISCONNECT_STREAK:
        env["supporting"].append(
            f"transport wall: {worst_endpoint[1]} RemoteDisconnected on "
            f"endpoint {worst_endpoint[0]}")
    qual_env_codes = {}
    for row in rows:
        for code, count in row["failure_codes"].items():
            if _is_environment_code(code):
                qual_env_codes[code] = qual_env_codes.get(code, 0) + count
    for code, count in sorted(qual_env_codes.items()):
        env["supporting"].append(
            f"qualification: {count} case(s) failed with {code}")
    if env["supporting"]:
        env["verdict"] = SUPPORTED
    else:
        env["verdict"] = RULED_OUT
        env["ruling_out"].append(
            "no HTTP 429, no transport-fault streak, and no qualification "
            "case carrying an environment failure code")

    # ---- MODEL ------------------------------------------------------------
    model = boxes["MODEL"]
    config = boxes["CONFIGURATION"]
    vindicated: list[str] = []
    capability_failures: list[str] = []
    for row in implicated_rows:
        cases = row["cases"] or 0
        first = row["first_pass_valid_count"]
        if cases and first == cases:
            vindicated.append(
                f"{row['role']}#{row['seat']} passed qualification "
                f"{first}/{cases} first-pass on {row['contract_id']} "
                f"with {row['repair_count']} repairs")
        elif row["qualified"] is False:
            non_env = {code: count for code, count in row["failure_codes"].items()
                       if not _is_environment_code(code)}
            unexplained = (sum(non_env.values()) > 0) or not row["failure_codes"]
            if unexplained:
                capability_failures.append(
                    f"{row['role']}#{row['seat']} failed qualification on "
                    f"{row['contract_id']}: {first}/{cases} first-pass, "
                    f"eventual {row['eventual_valid_count']}")
            else:
                model["ruling_out"].append(
                    f"{row['role']}#{row['seat']} failed qualification on "
                    f"{row['contract_id']}, but every failing case carries an "
                    f"environment failure code "
                    f"({', '.join(sorted(row['failure_codes']))}) — not a "
                    f"capability failure")
    model["supporting"].extend(capability_failures)

    seat_knobs: dict[tuple[str, int], Any] = {}
    for role in sorted((manifest or {}).get("roles") or {}):
        for index, entry in enumerate((manifest or {})["roles"][role] or []):
            seat_knobs[(role, index)] = entry.get("reasoning")
    for row in implicated_rows:
        if row["qualified"] is not False:
            continue
        key = (row["role"], row["seat"])
        if key not in seat_knobs:
            continue
        knob = seat_knobs[key]
        rendered = _REASONING_OMITTED if knob is None else repr(knob)
        line = (f"{row['role']}#{row['seat']} ran {row['contract_id']} with "
                f"reasoning {rendered} — the knob this seat was configured "
                f"with for this form")
        model["notes"].append(line)
        config["notes"].append(line)

    if any(marker in lowered for marker in _EXHAUSTION_MARKERS):
        model["supporting"].append(
            f"the stop names seat exhaustion: \"{message}\"")
    for row in ([] if health.get("absent") else health.get("seats") or []):
        if (row["role"], row["seat"]) not in implicated_keys:
            continue
        for path, count in row["validation_paths"].items():
            model["supporting"].append(
                f"{row['role']}#{row['seat']}: {count} attempt(s) rejected at "
                f"{path}")
        if row["truncated_when_invalid"]:
            model["supporting"].append(
                f"{row['role']}#{row['seat']}: "
                f"{row['truncated_when_invalid']} rejected completion(s) "
                f"truncated at the cap")
    for note in vindicated:
        model["notes"].append(note)
    if vindicated:
        model["notes"].append(
            "a seat that passed its form at full marks did not lose the "
            "ability between qualification and the run — look to "
            "CONFIGURATION or ENVIRONMENT first")
    if model["supporting"]:
        model["verdict"] = SUPPORTED
    else:
        model["verdict"] = RULED_OUT
        if vindicated:
            model["ruling_out"].extend(vindicated)
        if not model["ruling_out"]:
            model["ruling_out"].append(
                "no qualification failure, no schema rejection and no "
                "truncation recorded against the implicated seats")

    # ---- CONFIGURATION ----------------------------------------------------
    if not (manifest or {}):
        config["notes"].append("no manifest: nothing to compare")
    restored = ([] if (manifest is None) else
                [g for g in (_what_actually_ran(manifest, events).get(
                    "gates_restored_from_notice") or [])])
    for gate in restored:
        line = (f"{gate['field']} = {gate['value']} was NOT carried by the "
                f"compiled manifest; restored at run time from notice "
                f"({gate['pointer']})")
        if gate["field"].lower() in lowered:
            config["supporting"].append(line + " — and the stop names it")
        else:
            config["notes"].append(line)
    if config_diff:
        for line in config_diff:
            config["supporting"].append(f"run-config vs manifest: {line}")
    omitted = []
    if manifest:
        for role in sorted(manifest.get("roles") or {}):
            for index, entry in enumerate(manifest["roles"][role] or []):
                if entry.get("reasoning") is None:
                    omitted.append(f"{role}#{index} ({entry.get('model_id')})")
    if omitted:
        config["notes"].append(
            "reasoning omitted → provider default on: " + ", ".join(omitted)
            + " — an omitted knob is the provider's DEFAULT, not 'off'. "
              "NO PROFILE ENTRY consulted: whether these models need an "
              "explicit value is a model-profile question")
    armed = sorted(f"{role}#{seat}" for role, seat in _split_armed_seats(events))
    if armed:
        config["notes"].append(
            "split protocol armed on: " + ", ".join(armed)
            + " — the split arms on an omitted knob")
    if config["supporting"]:
        config["verdict"] = SUPPORTED
    else:
        config["verdict"] = RULED_OUT
        carried_note = (
            f"{len(restored)} field(s) were restored at run time from "
            f"notices (listed below), but the stop names none of them"
            if restored else
            "no ENGINE_CONFIG_FIELD_NOT_CARRIED notice was recorded")
        config["ruling_out"].append(
            carried_note + "; "
            + ("no run-config was supplied to diff against the manifest, so "
               "a mismatch there cannot be ruled out — re-run with --config "
               "to close that gap"
               if config_diff is None else "the supplied run-config matches "
                                           "the compiled manifest"))

    # ---- HARNESS ----------------------------------------------------------
    harness = boxes["HARNESS"]
    others = [boxes[name] for name in ("CONFIGURATION", "ENVIRONMENT", "MODEL")]
    last_valid = None
    for event in events:
        for attempt in (event.get("llm") or {}).get("attempt_trace") or []:
            last_valid = attempt.get("valid")
    if all(box["verdict"] == RULED_OUT for box in others) and message:
        harness["verdict"] = SUPPORTED
        harness["supporting"].append(f"the stop message: \"{message}\"")
        harness["supporting"].append(
            "CONFIGURATION, ENVIRONMENT and MODEL are each RULED OUT above "
            "with cited evidence")
        if last_valid is True:
            harness["supporting"].append(
                "the last recorded provider call returned a valid response")
    else:
        harness["verdict"] = NO_EVIDENCE
        standing = sorted(name for name in ("CONFIGURATION", "ENVIRONMENT", "MODEL")
                          if boxes[name]["verdict"] != RULED_OUT)
        harness["notes"].append(
            "not claimable: " + ", ".join(standing) + " still holds evidence. "
            "A harness verdict requires the other three to be ruled out.")

    ranked = sorted(
        BOXES,
        key=lambda name: (-_VERDICT_WEIGHT[boxes[name]["verdict"]],
                          -len(boxes[name]["supporting"]), name),
    )
    # R9: a seat vindicated by its own qualification row points at
    # configuration or environment INSTEAD, whatever the model box's own
    # verdict — the operator's recorded case, made structural.
    if vindicated and "MODEL" in ranked:
        ranked.remove("MODEL")
        anchor = max(ranked.index("CONFIGURATION"), ranked.index("ENVIRONMENT"))
        ranked.insert(anchor + 1, "MODEL")

    return {
        "absent": False,
        "stop_message": message,
        "ranked": ranked,
        "boxes": boxes,
        "implicated_seats": sorted(
            f"{row['role']}#{row['seat']}" for row in implicated),
    }


# ---------------------------------------------------------------------------
# Section 5 — CONTINUABILITY
# ---------------------------------------------------------------------------

def _continuability(root: Path | None, status, replay, verify) -> dict[str, Any]:
    if status is None:
        return _absent("no run-status.json: the run never reached a terminal")
    verdict: Any
    if verify and root is not None:
        from deepreason.invariants import verify_root

        result = verify_root(root)
        violations = result.get("violations") or []
        verdict = {"source": "re-derived", "violations": len(violations),
                   "checks": sorted({v.get("check") for v in violations})}
    elif isinstance(replay, dict):
        violations = replay.get("violations") or []
        verdict = {"source": "stored", "violations": len(violations),
                   "checks": sorted({v.get("check") for v in violations
                                     if isinstance(v, dict)})}
    else:
        verdict = _absent("no REPLAY_VALIDATION.json stored in this root")

    refusal = status.get("terminal_lifecycle_refusal")
    state = status.get("state")
    if refusal:
        continuation = "REFUSED"
        reason = f"the record carries {refusal}"
    elif state in ("completed", "failed"):
        continuation = "ACCEPTED"
        reason = "the run is at a terminal and carries no lifecycle refusal"
    else:
        continuation = "UNKNOWN"
        reason = f"the run is in state {state!r}, not at a terminal"

    return {
        "absent": False,
        "state": state,
        "stop_reason": status.get("stop_reason"),
        "message": status.get("message"),
        "terminal_lifecycle_refusal": refusal,
        "cycle": status.get("cycle"),
        "token_spend": status.get("token_spend"),
        "token_limit": status.get("token_limit"),
        "verify_root": verdict,
        "continue": continuation,
        "amend": continuation,
        "continuation_reason": reason,
    }


# ---------------------------------------------------------------------------
# The run-config diff — the ONE place a YAML is read, and only on request.
# ---------------------------------------------------------------------------

def _config_diff(config_path: Path | None, manifest: dict | None) -> list[str] | None:
    if config_path is None or manifest is None:
        return None
    try:
        import yaml

        written = yaml.safe_load(Path(config_path).read_text()) or {}
    except Exception as error:  # noqa: BLE001 - an unreadable config is a finding
        return [f"could not read {config_path}: {error}"]
    engine = {}
    raw = manifest.get("engine_config_json")
    if isinstance(raw, str):
        try:
            engine = json.loads(raw)
        except ValueError:
            engine = {}
    notices = {
        (n.get("pointer") or "").rsplit("/", 1)[-1]: n.get("value")
        for n in manifest.get("compile_notices") or []
        if n.get("code") == "ENGINE_CONFIG_FIELD_NOT_CARRIED"
    }
    lines: list[str] = []
    for key in sorted(k for k in written if isinstance(k, str)):
        wrote = written[key]
        if key in engine:
            if engine[key] != wrote:
                lines.append(f"{key}: you wrote {wrote!r}, the manifest "
                             f"compiled {engine[key]!r}")
        elif key in notices:
            lines.append(f"{key}: you wrote {wrote!r}; NOT carried by the "
                         f"manifest, restored at run time from a notice")
        else:
            lines.append(f"{key}: you wrote {wrote!r}; the compiled manifest "
                         f"does not carry this field at all")
    return lines


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

def stop_report(path: Path | str, *, config_path: Path | str | None = None,
                verify: bool = False) -> dict[str, Any]:
    """Build the typed stop report for the run root or home at ``path``."""

    source, kind = resolve_report_source(path)

    if kind in ("root", "root-no-log"):
        root: Path | None = source
        status = _read_json(source / "run-status.json")
        manifest = _read_json(source / "run-manifest.json")
        replay = _read_json(source / "REPLAY_VALIDATION.json")
        qualification = _read_json(source / "production-contract-qualification.json")
        digest, cached = None, False
        if qualification is None:
            found = _home_qualification(source.parent.parent)
            if found is not None:
                qualification, digest = found
                cached = True
        events = []
        log = source / "log.jsonl"
        if log.is_file():
            for line in log.read_text().splitlines():
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        continue
    else:
        root = None
        status = manifest = replay = None
        events = []
        found = _home_qualification(source)
        qualification, digest = found if found else (None, None)
        cached = True

    ran = _what_actually_ran(manifest, events)
    if kind == "home-no-root":
        ran = _absent("no run root: the run never started, so nothing was "
                      "compiled into a manifest")
    pre_run = _pre_run_check(qualification, digest, cached)
    health = _provider_health(events)
    if kind == "home-no-root":
        health = _absent("no run root: the run never started, so no provider "
                         "call was recorded")
    elif kind == "root-no-log":
        health = _absent("no log.jsonl: the run stopped before its first "
                         "reasoning call, so no provider call was recorded "
                         "in the run. Section 2 carries the provider's "
                         "behaviour during qualification instead")
    diff = _config_diff(Path(config_path) if config_path else None, manifest)
    classification = _classify(status, manifest, events, health, pre_run, diff)
    continuability = _continuability(root, status, replay, verify)
    if kind == "home-no-root":
        continuability = _absent(
            "no run root: the run never started, so there is nothing to "
            "continue or amend")
    elif kind == "root-no-log" and status is None:
        continuability = _absent(
            "no run-status.json: the run stopped before it reached a "
            "terminal, so there is no stopped state to continue from. "
            "Relaunching is the road, not `continue`")

    return {
        "schema": SCHEMA,
        "source": {
            "path": str(source),
            "kind": kind,
            "run_id": (status or {}).get("run_id"),
        },
        "sections": {
            "what_actually_ran": ran,
            "pre_run_check": pre_run,
            "provider_health": health,
            "classification": classification,
            "continuability": continuability,
        },
    }


def _absence_line(section: dict) -> str | None:
    if section.get("absent"):
        return f"_Not available: {section.get('reason')}._"
    return None


def render_stop_report(report: dict[str, Any]) -> str:
    """Render the typed report as Markdown. Carries every section the dict
    carries; adds no fact the dict does not hold."""

    sections = report["sections"]
    source = report["source"]
    out: list[str] = []
    out.append("# Stop report")
    out.append("")
    out.append(f"- source: `{source['path']}` ({source['kind']})")
    out.append(f"- run id: {source['run_id'] or '(none — no run root)'}")
    out.append("")
    out.append("This report is derived from the record alone. It ranks four "
               "boxes by evidence and never asserts a defect.")
    out.append("")

    # 1
    out.append("## 1. WHAT ACTUALLY RAN")
    out.append("")
    ran = sections["what_actually_ran"]
    absent = _absence_line(ran)
    if absent:
        out.append(absent)
    else:
        out.append("| seat | model | profile | reasoning | max_tokens | timeout_s | split |")
        out.append("|---|---|---|---|---|---|---|")
        for seat in ran["seats"]:
            out.append(
                f"| {seat['role']}#{seat['seat']} | {seat['model_id']} "
                f"({seat['endpoint_id']}) | {seat['model_profile']} | "
                f"{seat['reasoning']} | {seat['max_tokens']} | "
                f"{seat['timeout_s']} | {seat['split_protocol']} |")
        out.append("")
        out.append(f"- embedder as compiled: **{ran['embedder']}**")
        out.append("")
        if ran["gates_restored_from_notice"]:
            out.append("Gates NOT carried by the compiled manifest "
                       "(restored at run time from notice):")
            out.append("")
            for gate in ran["gates_restored_from_notice"]:
                out.append(f"- `{gate['pointer']}` = {gate['value']} — "
                           f"restored at run time from notice"
                           + (f"; resolution `{gate['resolution']}`"
                              if gate["resolution"] else ""))
            out.append("")
        if ran["compile_notices"]:
            out.append("Every compile notice, verbatim:")
            out.append("")
            for notice in ran["compile_notices"]:
                out.append(f"- `{notice.get('code')}` {notice.get('message')}")
            out.append("")

    # 2
    out.append("## 2. PRE-RUN CHECK")
    out.append("")
    pre = sections["pre_run_check"]
    absent = _absence_line(pre)
    if absent:
        out.append(absent)
    else:
        if pre["cached"] and pre["subject_digest"]:
            out.append(f"Qualification was CACHED, read from subject digest "
                       f"`{pre['subject_digest']}`.")
            out.append("")
        out.append("| seat | form | first-pass | eventual | repairs | qualified |")
        out.append("|---|---|---|---|---|---|")
        for row in pre["rows"]:
            out.append(
                f"| {row['role']}#{row['seat']} | {row['contract_id']} | "
                f"{row['first_pass_valid_count']}/{row['cases']} | "
                f"{row['eventual_valid_count']} | {row['repair_count']} | "
                f"{row['qualified']} |")
        out.append("")
        for row in pre["rows"]:
            if row["failure_codes"]:
                out.append(f"- {row['role']}#{row['seat']} "
                           f"{row['contract_id']} failure codes: "
                           + ", ".join(f"{code} ×{count}" for code, count
                                       in row["failure_codes"].items()))
        out.append("")

    # 3
    out.append("## 3. PROVIDER HEALTH")
    out.append("")
    health = sections["provider_health"]
    absent = _absence_line(health)
    if absent:
        out.append(absent)
    else:
        out.append("| seat | endpoint | attempts | invalid | zero-token | faults |")
        out.append("|---|---|---|---|---|---|")
        for row in health["seats"]:
            faults = ", ".join(f"{kind} ×{count}" for kind, count
                               in row["faults_by_kind"].items()) or "none"
            out.append(
                f"| {row['role']}#{row['seat']} | {row['endpoint_id']} | "
                f"{row['attempts']} | {row['invalid_attempts']} | "
                f"{row['zero_token_returns']} | {faults} |")
        out.append("")
        for row in health["seats"]:
            for message in row["http_429_messages"]:
                out.append(f"- {row['role']}#{row['seat']} HTTP 429 from the "
                           f"provider: \"{message.strip()}\"")
            if row["last_fault"]:
                out.append(f"- {row['role']}#{row['seat']} last fault: "
                           f"`{row['last_fault']}`")
        out.append("")

    # 4
    out.append("## 4. THE STOP, CLASSIFIED")
    out.append("")
    classification = sections["classification"]
    out.append(f"Stop message: `{classification['stop_message'] or '(none recorded)'}`")
    out.append("")
    out.append("Boxes ranked by evidence:")
    out.append("")
    for position, name in enumerate(classification["ranked"], start=1):
        box = classification["boxes"][name]
        out.append(f"### {position}. {name} — {box['verdict']}")
        out.append("")
        for item in box["supporting"]:
            out.append(f"- evidence FOR: {item}")
        for item in box["ruling_out"]:
            out.append(f"- evidence RULING IT OUT: {item}")
        for item in box["notes"]:
            out.append(f"- note: {item}")
        if not (box["supporting"] or box["ruling_out"] or box["notes"]):
            out.append("- no typed evidence either way in this record")
        out.append("")

    # 5
    out.append("## 5. CONTINUABILITY")
    out.append("")
    cont = sections["continuability"]
    absent = _absence_line(cont)
    if absent:
        out.append(absent)
    else:
        out.append(f"- state: {cont['state']}")
        out.append(f"- stop_reason: {cont['stop_reason']}")
        out.append(f"- terminal_lifecycle_refusal: "
                   f"{cont['terminal_lifecycle_refusal'] or '(none)'}")
        out.append(f"- verify_root: {json.dumps(cont['verify_root'], sort_keys=True)}")
        out.append(f"- continue: **{cont['continue']}** — {cont['continuation_reason']}")
        out.append(f"- amend: **{cont['amend']}** — {cont['continuation_reason']}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"
