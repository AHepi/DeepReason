#!/usr/bin/env python3
"""P-A2 live monitor: read OUTCOMES, not dispatches.

WHY THIS FILE IS NOT P-A1's monitor.sh. That monitor classified a failed
provider attempt as::

    t.get("error") or t.get("failure") or t.get("status") == "error"

and the attempt trace carries NONE of those three keys. P-A1's run took 39
`RemoteDisconnected` faults plus one `HTTPError` -- 66% of its wall clock --
and the monitor printed `provider calls FAILED: none` throughout
(MONITOR_REVIEW.md MR-B). A monitor that cannot see the signature it was
built for is worse than no monitor, because its silence reads as health.

So this one reads the TYPED vocabulary the harness actually writes, and it
reads it from two independent places that must agree:

  OBJECTS (authoritative outcome, no ordering)
    objects/workflow-provider-attempt-v1/*.json  outcome:
        provider_result | transport_failure
        usage_status:   exact | unknown
    objects/criticism-attempt-v1/*.json          outcome:
        completed | schema_failure | transport_failure | budget_denied
    objects/workflow-semantic-admission-v1/*.json outcome:
        admitted | rejected | schema_exhausted | unrepairable

  LOG (ordering and per-attempt detail, no independent outcome)
    log.jsonl -> llm.attempt_trace[] rows carrying tokens, usage_unknown,
        transport_diagnostics, transport_attempts, natural_stop, valid

Both are reported. WHERE THEY DISAGREE THAT IS ITSELF THE FINDING, and the
monitor says so rather than picking a winner -- P-A1's whole failure was an
instrument quietly reporting one number as if it were the other.

Field paths verified against the schemas rather than guessed:
`ProviderAttemptV1` (workflow/transaction.py:366) and `CriticismAttemptV1`
(workflow/criticism.py:157). Stored objects wrap the record under a "data"
key, which is the second thing P-A1's reader would have got wrong.

Usage:  python monitor_pa2.py <root> [--json]
Exit:   0 = no alert, 1 = at least one ALERT fired, 2 = usage error.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

# A seat is (endpoint_id, role, seat_index): the signal contract keys on SEAT
# INSTANCE, not role, because one model may sit in several structurally
# different seats and only one of them may be dying.
FAILED_PROVIDER = "transport_failure"


def _objects(root: pathlib.Path, kind: str) -> list[dict]:
    directory = root / "objects" / kind
    if not directory.is_dir():
        return []
    rows = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        # Stored objects wrap the record; a reader that skips this sees every
        # `outcome` as None and reports a clean run.
        rows.append(payload.get("data", payload))
    return rows


def _attempt_rows(root: pathlib.Path) -> list[dict]:
    """Every attempt_trace row, in log order, with its seat and call attached."""
    log = root / "log.jsonl"
    if not log.exists():
        return []
    rows = []
    with log.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            llm = event.get("llm")
            if not llm:
                continue
            for attempt in llm.get("attempt_trace") or ():
                rows.append(
                    {
                        "seq": event.get("seq"),
                        "role": llm.get("role"),
                        "model": llm.get("model"),
                        "endpoint_id": attempt.get("endpoint_id"),
                        "seat": attempt.get("seat"),
                        "attempt": attempt.get("attempt"),
                        "tokens": attempt.get("tokens"),
                        "usage_unknown": bool(attempt.get("usage_unknown")),
                        "diagnostics": tuple(attempt.get("transport_diagnostics") or ()),
                        "transport_attempts": attempt.get("transport_attempts"),
                        "natural_stop": attempt.get("natural_stop"),
                        "valid": attempt.get("valid"),
                        "ms": attempt.get("ms"),
                    }
                )
    return rows


def _is_failed(row: dict) -> bool:
    """No usable output came back.

    This is the LOG-side stand-in for the object's typed `transport_failure`,
    and it is deliberately the union of the three signatures P-A1's record
    carried together: a dropped connection, an unknown usage, and a zero
    token count. Any one of them alone is enough to call the attempt dead.
    """
    return bool(row["diagnostics"]) or not row["tokens"] or row["usage_unknown"]


def analyse(root: pathlib.Path) -> dict:
    provider = _objects(root, "workflow-provider-attempt-v1")
    criticism = _objects(root, "criticism-attempt-v1")
    admission = _objects(root, "workflow-semantic-admission-v1")
    rows = _attempt_rows(root)

    provider_outcomes = collections.Counter(r.get("outcome") for r in provider)
    criticism_outcomes = collections.Counter(r.get("outcome") for r in criticism)
    admission_outcomes = collections.Counter(r.get("outcome") for r in admission)
    usage = collections.Counter(r.get("usage_status") for r in provider)

    transport_by_seat = collections.Counter()
    for record in provider:
        if record.get("outcome") != FAILED_PROVIDER:
            continue
        lease = record.get("route_lease") or {}
        transport_by_seat[
            (lease.get("endpoint_id"), lease.get("role"), lease.get("seat"))
        ] += 1

    zero_token = [r for r in rows if not r["tokens"]]
    with_diagnostics = [r for r in rows if r["diagnostics"]]
    diagnostic_kinds = collections.Counter(
        (r["model"], d.split(":")[0]) for r in with_diagnostics for d in r["diagnostics"]
    )

    # Consecutive failures PER SEAT, in log order. A seat that fails twice in a
    # row is the F4 death signature forming: P-A1's glm-5.3 conjecturer seat
    # exhausted its contract ladder AFTER a ten-call transport streak, and the
    # run was not resumable afterwards.
    streaks: dict[tuple, int] = collections.defaultdict(int)
    worst: dict[tuple, int] = collections.defaultdict(int)
    for row in sorted(rows, key=lambda r: (r["seq"] or 0, r["attempt"] or 0)):
        key = (row["endpoint_id"], row["role"], row["seat"])
        if _is_failed(row):
            streaks[key] += 1
            worst[key] = max(worst[key], streaks[key])
        else:
            streaks[key] = 0
    consecutive = {k: v for k, v in worst.items() if v >= 2}

    alerts: list[str] = []
    if zero_token:
        alerts.append(
            f"ZERO-TOKEN CALLS: {len(zero_token)} of {len(rows)} provider attempts "
            f"returned no tokens at all "
            f"-- {sorted({(r['model'], r['role']) for r in zero_token})}"
        )
    if with_diagnostics:
        alerts.append(
            f"TRANSPORT DIAGNOSTICS: {len(with_diagnostics)} attempts carry "
            f"{sum(len(r['diagnostics']) for r in with_diagnostics)} diagnostics "
            f"-- {dict(diagnostic_kinds)}"
        )
    for key, count in sorted(consecutive.items(), key=lambda kv: -kv[1]):
        alerts.append(
            f"SEAT STREAK: {key[1]} seat {key[2]} on {key[0]} failed {count} "
            f"CONSECUTIVE attempts -- this is the F4 seat-exhaustion signature "
            f"forming; that terminal is not resumable"
        )
    if provider_outcomes.get(FAILED_PROVIDER):
        alerts.append(
            f"TYPED PROVIDER FAILURES: {provider_outcomes[FAILED_PROVIDER]} "
            f"workflow-provider-attempt-v1 objects say transport_failure "
            f"-- by seat {dict(transport_by_seat)}"
        )
    if criticism_outcomes.get("transport_failure"):
        alerts.append(
            f"TYPED CRITICISM FAILURES: "
            f"{criticism_outcomes['transport_failure']} criticism-attempt-v1 "
            f"objects say transport_failure (each retains coverage debt)"
        )
    if admission_outcomes.get("schema_exhausted"):
        alerts.append(
            f"SCHEMA EXHAUSTED: {admission_outcomes['schema_exhausted']} semantic "
            f"admissions ran the contract ladder out -- the step immediately "
            f"before V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY (P5's honest risk)"
        )

    # The two readings must agree. They are independent counts of the same
    # fact, so a divergence means one of them is wrong and neither may be
    # quoted alone.
    log_failures = len([r for r in rows if _is_failed(r)])
    object_failures = provider_outcomes.get(FAILED_PROVIDER, 0)
    reconciled = log_failures == object_failures
    if not reconciled and (rows or provider):
        alerts.append(
            f"READINGS DISAGREE: log attempt_trace says {log_failures} dead "
            f"attempts, typed objects say {object_failures}. One of these two "
            f"instruments is wrong -- do not quote either alone"
        )

    progress = root / "progress.jsonl"
    state = {}
    if progress.exists():
        lines = [l for l in progress.read_text().splitlines() if l.strip()]
        if lines:
            try:
                state = json.loads(lines[-1])
            except json.JSONDecodeError:
                state = {}

    return {
        "state": {
            k: state.get(k)
            for k in ("state", "phase", "cycle", "accepted", "refuted",
                      "stop_reason", "tokens")
        },
        "provider_attempts": dict(provider_outcomes),
        "provider_usage_status": dict(usage),
        "criticism_attempts": dict(criticism_outcomes),
        "semantic_admissions": dict(admission_outcomes),
        "attempt_rows": len(rows),
        "zero_token_attempts": len(zero_token),
        "attempts_with_diagnostics": len(with_diagnostics),
        "diagnostic_kinds": {f"{m}/{d}": n for (m, d), n in diagnostic_kinds.items()},
        "transport_failures_by_seat": {
            f"{e}/{r}/{s}": n for (e, r, s), n in transport_by_seat.items()
        },
        "consecutive_failures_by_seat": {
            f"{e}/{r}/{s}": n for (e, r, s), n in consecutive.items()
        },
        "readings_reconciled": reconciled,
        "log_side_failures": log_failures,
        "object_side_failures": object_failures,
        "alerts": alerts,
    }


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 2
    root = pathlib.Path(argv[0])
    as_json = "--json" in argv[1:]
    if not root.exists():
        print(f"root {root} does not exist yet")
        return 0
    report = analyse(root)
    if as_json:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        s = report["state"]
        print(
            f"state={s.get('state')} phase={s.get('phase')} cycle={s.get('cycle')} "
            f"accepted={s.get('accepted')} refuted={s.get('refuted')} "
            f"stop={s.get('stop_reason')} tokens={s.get('tokens')}"
        )
        print(f"  provider attempts (typed) : {report['provider_attempts'] or 'none yet'}")
        print(f"  usage_status              : {report['provider_usage_status'] or 'none yet'}")
        print(f"  criticism attempts (typed): {report['criticism_attempts'] or 'none yet'}")
        print(f"  semantic admissions       : {report['semantic_admissions'] or 'none yet'}")
        print(
            f"  attempt_trace rows        : {report['attempt_rows']} "
            f"({report['zero_token_attempts']} zero-token, "
            f"{report['attempts_with_diagnostics']} with diagnostics)"
        )
        print(f"  diagnostics by model      : {report['diagnostic_kinds'] or 'none'}")
        print(
            f"  reconciled                : {report['readings_reconciled']} "
            f"(log {report['log_side_failures']} vs objects "
            f"{report['object_side_failures']})"
        )
        for alert in report["alerts"]:
            print(f"  *** ALERT: {alert} ***")
        if not report["alerts"]:
            print("  no alert")
    return 1 if report["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
