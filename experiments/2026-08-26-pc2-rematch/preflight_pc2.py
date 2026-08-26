#!/usr/bin/env python3
"""P-C2's own preflight: prove the REMATCH is the rematch it registered.

P-C1's ladder already carries three preflights and this tranche re-runs all
of them unchanged (`preflight_criteria.py`, `mutation_proof.py`,
`preflight_models.py`).  This file adds the four checks that are specific to
P-C2, and every one of them exists because a SILENT version of the failure
it catches has already happened once in this program.

    S1  THE QUESTION HAS NOT DRIFTED.
        P-C2 is a rematch.  A rematch on a different question measures the
        question.  Asserted by digest against PREREG.md §2's frozen value.

    S2  THE CONFIG DIFFERS FROM P-C1's BY EXACTLY ONE FIELD.
        Same reason: any second field makes the comparison a comparison of
        two re-tuned launches.  Asserted by parsing both YAML files, not by
        reading a comment that claims it.

    S3  DEVIATION D1 IS IN FORCE -- THE DISCHARGE CHANNEL WILL ACTUALLY BE
        ON AT RUNTIME.
        This is the one that matters most, and it is the direct descendant
        of P-C1's killed run.  There, an in-run battery was INERT for
        eleven cycles and the record looked exactly like "the model could
        not do it".  Here the analogous silent failure is a discharge
        channel that is configured on, reads on in the YAML, and is OFF in
        the run -- which is the DEFAULT state of this tree (PREREG.md §3
        FINDING F-A).  A P-C2 that ran with the channel off would be a
        second P-C1 wearing P-C2's name, and nothing in the typed record
        would say so.  So the runtime Config is RECONSTRUCTED here exactly
        as `application/text_runs.py` reconstructs it, and the policy is
        asserted ENABLED.

    S4  THE MANIFEST DIFFERENCE FROM P-C1 IS FULLY ACCOUNTED FOR.
        Everything that moved must be a REBUILD tranche landing or a known
        provenance string.  An unexplained field is a stop: it would mean
        something other than the rebuild changed between the two runs, and
        the whole tranche rests on that not being true.

Exit 0 = launch is licensed by this file.  Any other exit = STOP.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
FRONTIER = REPO / "experiments" / "2026-08-25-change-constructive-frontier"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(FRONTIER))

QUESTION_SHA256 = "64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e"
THE_ONE_FIELD = "DISCHARGE_POLICY"

# S4's allowlist.  Each entry names the REBUILD tranche that owns the change,
# so an unexplained field cannot hide behind a vague "expected differences".
ACCOUNTED_MANIFEST_PATHS = {
    "/research/enabled": "REBUILD F3 -- research channel on by default",
    "/research/backend_identity": "REBUILD F3 -- research channel on by default",
    "/research/domain_allowlist": "REBUILD F3 -- the default frozen allowlist an enabled research channel requires",
    "/research/maximum_requests": "REBUILD F3 -- research channel on by default",
    "/research/maximum_sources": "REBUILD F3 -- research channel on by default",
    "/research/maximum_response_bytes": "REBUILD F3 -- research channel on by default",
}
ACCOUNTED_TOP_LEVEL = {
    "inquiry_capability_policy": "carrier of the F3 research rows above",
    "run_input_digest": "the empty dossier's creation_provenance names THIS builder",
}

_failures: list[str] = []
_report: dict = {"schema": "pc2.preflight.v1", "checks": []}


def _check(cid: str, ok: bool, detail) -> None:
    _report["checks"].append({"id": cid, "ok": bool(ok), "detail": detail})
    print(f"[{'OK ' if ok else 'FAIL'}] {cid}: {detail}")
    if not ok:
        _failures.append(cid)


def s1_question() -> None:
    from deepreason.preparation import _question_digest
    from question import QUESTION

    digest = _question_digest(QUESTION)
    _check(
        "S1-question-frozen",
        digest == QUESTION_SHA256,
        f"question_sha256={digest} (PREREG §2 froze {QUESTION_SHA256})",
    )


def s2_config_delta() -> None:
    a = yaml.safe_load((FRONTIER / "run-config.yaml").read_text()) or {}
    b = yaml.safe_load((TRANCHE / "run-config.yaml").read_text()) or {}
    delta = sorted(
        k for k in set(a) | set(b) if a.get(k, "<absent>") != b.get(k, "<absent>")
    )
    _check(
        "S2-one-field-only",
        delta == [THE_ONE_FIELD] and b.get(THE_ONE_FIELD) == "discharge-required.v1",
        f"fields differing from P-C1's config: {delta}; "
        f"{THE_ONE_FIELD}={b.get(THE_ONE_FIELD)!r}",
    )


def s3_channel_live(root: Path) -> None:
    """The check P-C1's killed run bought."""
    from deepreason.discharge import resolve_policy
    from deepreason.run_manifest import config_from_run_manifest, load_run_manifest

    manifest = load_run_manifest(root / "run-manifest.json")
    runtime = config_from_run_manifest(manifest)
    policy = resolve_policy(runtime)
    _check(
        "S3-discharge-channel-live-at-runtime",
        bool(policy.enabled) and policy.handles_n > 0,
        f"runtime DISCHARGE_POLICY={runtime.DISCHARGE_POLICY!r} "
        f"enabled={policy.enabled} reask={policy.reask!r} "
        f"handles_n={policy.handles_n} "
        f"(deviation D1 absent would read 'off' here)",
    )


def s4_manifest_delta(root: Path) -> None:
    from deepreason.run_manifest import load_run_manifest

    a = load_run_manifest(FRONTIER / "run" / "run-manifest.json")
    b = load_run_manifest(root / "run-manifest.json")

    unexplained: list[str] = []

    ca, cb = json.loads(a.engine_config_json), json.loads(b.engine_config_json)
    echo_delta = sorted(
        k for k in set(ca) | set(cb) if ca.get(k, "<absent>") != cb.get(k, "<absent>")
    )
    unexplained += [f"engine_config_json:{k}" for k in echo_delta]

    da, db = json.loads(a.model_dump_json()), json.loads(b.model_dump_json())
    for key in sorted(set(da) | set(db)):
        if key == "engine_config_json" or da.get(key) == db.get(key):
            continue
        if key not in ACCOUNTED_TOP_LEVEL:
            unexplained.append(f"manifest:{key}")

    pa = json.loads(a.inquiry_capability_policy.model_dump_json())
    pb = json.loads(b.inquiry_capability_policy.model_dump_json())
    leaves: list[str] = []

    def walk(x, y, path=""):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                walk(x.get(k), y.get(k), f"{path}/{k}")
        elif x != y:
            leaves.append(path)

    walk(pa, pb)
    unexplained += [
        f"inquiry_capability_policy{p}"
        for p in leaves
        if p not in ACCOUNTED_MANIFEST_PATHS
    ]

    _check(
        "S4-manifest-delta-accounted",
        not unexplained,
        (
            f"accounted: {len(leaves)} policy leaf/leaves "
            f"+ {sorted(ACCOUNTED_TOP_LEVEL)}; unexplained: {unexplained or 'none'}"
        ),
    )
    _report["manifest_delta"] = {
        "pc1_sha256": a.sha256,
        "pc2_sha256": b.sha256,
        "inquiry_policy_leaves": {p: ACCOUNTED_MANIFEST_PATHS.get(p, "UNEXPLAINED") for p in leaves},
        "engine_config_echo_delta": echo_delta,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: preflight_pc2.py <root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])

    s1_question()
    s2_config_delta()
    s3_channel_live(root)
    s4_manifest_delta(root)

    (TRANCHE / "preflight_pc2.json").write_text(
        json.dumps(_report, indent=1, sort_keys=True) + "\n"
    )
    if _failures:
        print(f"\nPREFLIGHT FAILED: {_failures}", file=sys.stderr)
        return 1
    print("\nPREFLIGHT OK: all four P-C2-specific checks hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
