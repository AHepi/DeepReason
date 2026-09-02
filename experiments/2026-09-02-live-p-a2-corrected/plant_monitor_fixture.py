#!/usr/bin/env python3
"""Prove monitor_pa2.py fires BEFORE the launch, on planted faults.

The tranche instruction requires the alert shown firing on a planted fixture
and that output committed. This builds six synthetic roots -- one per alert,
plus a CLEAN CONTROL -- and asserts the monitor's verdict on each.

The control is the half that is easy to skip and is not optional. P-A1's
monitor failed by staying silent through 40 faults; a monitor that shouted on
everything would be just as useless and would look, in a single screenshot,
exactly as healthy. So the fixture asserts BOTH directions: the clean root
must produce NO alert, and each planted root must produce the ONE alert it
was built for.

The object shapes are the real ones (`{"data": {...}}` wrappers, the schema
field names verified against workflow/transaction.py and workflow/criticism.py),
because a fixture written against a guessed shape proves only that the monitor
agrees with the guess.

Usage:  python plant_monitor_fixture.py <workdir>
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from monitor_pa2 import analyse  # noqa: E402


def _write_object(root: pathlib.Path, kind: str, name: str, data: dict) -> None:
    directory = root / "objects" / kind
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{name}.json").write_text(
        json.dumps({"data": data, "id": f"sha256:{name}", "schema": kind}, indent=1)
    )


def _attempt(seq, role, model, endpoint, seat, *, tokens, diagnostics=(),
             usage_unknown=False, attempt=0):
    return {
        "seq": seq,
        "rule": "Conj",
        "llm": {
            "role": role,
            "model": model,
            "attempt_trace": [
                {
                    "attempt": attempt,
                    "endpoint_id": endpoint,
                    "seat": seat,
                    "tokens": tokens,
                    "usage_unknown": usage_unknown,
                    "transport_diagnostics": list(diagnostics),
                    "transport_attempts": len(diagnostics) or 1,
                    "natural_stop": tokens > 0,
                    "valid": tokens > 0,
                    "ms": 1000,
                }
            ],
        },
    }


def _root(base: pathlib.Path, name: str, events: list[dict],
          objects: list[tuple[str, str, dict]]) -> pathlib.Path:
    root = base / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    (root / "log.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in events)
    )
    (root / "progress.jsonl").write_text(
        json.dumps({"state": "running", "phase": "conjecture", "cycle": 3,
                    "tokens": 1000}) + "\n"
    )
    for kind, ident, data in objects:
        _write_object(root, kind, ident, data)
    return root


def _lease(endpoint, role, seat):
    return {"endpoint_id": endpoint, "role": role, "seat": seat,
            "route_sha256": "0" * 64}


def _provider(ident, outcome, endpoint, role, seat):
    record = {
        "id": f"sha256:{ident}",
        "schema": "workflow.provider-attempt.v1",
        "work_id": "sha256:" + "1" * 64,
        "attempt_index": 0,
        "authorization_bundle_ref": "sha256:" + "2" * 64,
        "contract_id": "conjecturer.turn.v6",
        "route_lease": _lease(endpoint, role, seat),
        "prompt_sha256": "3" * 64,
        "outcome": outcome,
    }
    if outcome == "provider_result":
        record.update({"raw_ref": "4" * 64, "usage_status": "exact",
                       "prompt_tokens": 100, "completion_tokens": 200})
    else:
        record.update({"usage_status": "unknown", "diagnostic_ref": "5" * 64})
    return record


GOOD = "ollama-deepseek-v4-pro-0813"
BAD = "ollama-glm-5.3"
RD = "RemoteDisconnected:Remote end closed connection without response"

CASES: dict[str, str] = {}


def build(base: pathlib.Path) -> list[tuple[str, pathlib.Path, str | None]]:
    cases = []

    # 1. CLEAN CONTROL -- the direction that is easy to forget to test.
    cases.append((
        "clean-control",
        _root(base, "clean-control",
              [_attempt(i, "conjecturer", "deepseek-v4-pro:0813", GOOD, 0,
                        tokens=4000) for i in range(1, 5)],
              [(("workflow-provider-attempt-v1"), f"c{i}",
                _provider(f"c{i}", "provider_result", GOOD, "conjecturer", 0))
               for i in range(1, 5)]),
        None,
    ))

    # 2. A single zero-token call.
    cases.append((
        "zero-token",
        _root(base, "zero-token",
              [_attempt(1, "conjecturer", "deepseek-v4-pro:0813", GOOD, 0, tokens=4000),
               _attempt(2, "defender", "glm-5.3", BAD, 0, tokens=0, usage_unknown=True)],
              [("workflow-provider-attempt-v1", "z1",
                _provider("z1", "provider_result", GOOD, "conjecturer", 0)),
               ("workflow-provider-attempt-v1", "z2",
                _provider("z2", "transport_failure", BAD, "defender", 0))]),
        "ZERO-TOKEN CALLS",
    ))

    # 3. A transport diagnostic (P-A1's exact signature).
    cases.append((
        "transport-diagnostic",
        _root(base, "transport-diagnostic",
              [_attempt(1, "conjecturer", "glm-5.3", BAD, 1, tokens=0,
                        usage_unknown=True, diagnostics=[RD] * 4)],
              [("workflow-provider-attempt-v1", "t1",
                _provider("t1", "transport_failure", BAD, "conjecturer", 1))]),
        "TRANSPORT DIAGNOSTICS",
    ))

    # 4. Two CONSECUTIVE failures on one seat, with a healthy seat interleaved
    #    so the streak counter must key on the seat and not on global order.
    cases.append((
        "seat-streak",
        _root(base, "seat-streak",
              [_attempt(1, "conjecturer", "glm-5.3", BAD, 1, tokens=0,
                        usage_unknown=True, diagnostics=[RD]),
               _attempt(2, "conjecturer", "deepseek-v4-pro:0813", GOOD, 0, tokens=5000),
               _attempt(3, "conjecturer", "glm-5.3", BAD, 1, tokens=0,
                        usage_unknown=True, diagnostics=[RD]),
               _attempt(4, "conjecturer", "deepseek-v4-pro:0813", GOOD, 0, tokens=5000)],
              [("workflow-provider-attempt-v1", f"s{i}",
                _provider(f"s{i}", "transport_failure", BAD, "conjecturer", 1))
               for i in (1, 3)]
              + [("workflow-provider-attempt-v1", f"s{i}",
                  _provider(f"s{i}", "provider_result", GOOD, "conjecturer", 0))
                 for i in (2, 4)]),
        "SEAT STREAK",
    ))

    # 5. The contract ladder running out -- the step immediately before the
    #    non-resumable terminal P5 names as its honest risk.
    cases.append((
        "schema-exhausted",
        _root(base, "schema-exhausted",
              [_attempt(1, "conjecturer", "glm-5.3", BAD, 1, tokens=900)],
              [("workflow-provider-attempt-v1", "e1",
                _provider("e1", "provider_result", BAD, "conjecturer", 1)),
               ("workflow-semantic-admission-v1", "e2",
                {"id": "sha256:e2", "schema": "workflow.semantic-admission.v1",
                 "work_id": "sha256:" + "1" * 64, "attempt_index": 0,
                 "provider_attempt_ref": "sha256:e1",
                 "outcome": "schema_exhausted", "diagnostic_refs": ["6" * 64]})]),
        "SCHEMA EXHAUSTED",
    ))

    # 6. The two readings disagreeing -- the failure mode that made P-A1's
    #    monitor quotable while wrong. The log shows a dead attempt; the
    #    objects claim every attempt succeeded.
    cases.append((
        "readings-disagree",
        _root(base, "readings-disagree",
              [_attempt(1, "conjecturer", "glm-5.3", BAD, 1, tokens=0,
                        usage_unknown=True, diagnostics=[RD])],
              [("workflow-provider-attempt-v1", "d1",
                _provider("d1", "provider_result", BAD, "conjecturer", 1))]),
        "READINGS DISAGREE",
    ))
    return cases


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: plant_monitor_fixture.py <workdir>", file=sys.stderr)
        return 2
    base = pathlib.Path(sys.argv[1])
    base.mkdir(parents=True, exist_ok=True)
    failures = []
    for name, root, expect in build(base):
        report = analyse(root)
        alerts = report["alerts"]
        if expect is None:
            ok = not alerts
            verdict = "SILENT (correct)" if ok else f"WRONGLY ALERTED: {alerts}"
        else:
            ok = any(a.startswith(expect) for a in alerts)
            verdict = "FIRED" if ok else f"DID NOT FIRE (got {alerts})"
        print(f"[{'ok  ' if ok else 'FAIL'}] {name:22s} expect="
              f"{expect or '<no alert>':24s} {verdict}")
        for alert in alerts:
            print(f"           -> {alert}")
        if not ok:
            failures.append(name)
    print()
    if failures:
        print(f"FIXTURE FAILED: {len(failures)} cases -- {failures}")
        return 1
    print(f"FIXTURE OK: {len(build(base))} cases, every alert fires and the "
          f"clean control stays silent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
