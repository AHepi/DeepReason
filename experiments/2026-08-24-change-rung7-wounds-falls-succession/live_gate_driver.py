#!/usr/bin/env python3
"""L-6, staged INSIDE the run so nothing is written past the terminal horizon.

The first attempt staged the fall on the root AFTER `deepreason run` had
terminalized it, and the harness's own `terminal-authority` check refused it:
`TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED`. That is the check working. Writing
to a terminalized root is, in Rung 4's own words, "exercising a state no
operator can reach" -- and L-6 judges `verify_root` clean, so an illegitimate
staging cannot produce a passing gate. Recorded rather than quietly corrected;
the refused root is retired beside this file.

The legitimate shape is the one Rung 4's `_framed_manifest_root` already uses:
file the frame assertion DURING the run, while the epoch is open. This driver
wraps `ops.run_scheduler` -- the same function the CLI calls -- runs the real
live scheduler for its cycles, and then stages the fall on the still-open
harness before returning. Everything the run itself does is untouched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from deepreason import ops                                       # noqa: E402
from deepreason.calculus import operations                       # noqa: E402
from deepreason.calculus.render import (                         # noqa: E402
    render_frame_crisis_context,
    render_frame_slice_context,
)
from deepreason.calculus.standing import (                       # noqa: E402
    consulted,
    fallen_frames,
    framed_problem_ids,
    standing_of,
)
from deepreason.ontology import (                                # noqa: E402
    Commitment,
    Interface,
    Provenance,
    Status,
)
from deepreason.premises import (                                # noqa: E402
    batch_translation_offers,
    open_orphans,
    premise_orphaned,
)
from deepreason.rules.warrants import register_fail_warrant      # noqa: E402

REPORT = HERE / "l6-typed-outcomes.json"
report: dict = {}


def _subject(harness) -> str | None:
    """A model-written accepted artifact, chosen deterministically."""
    addressed = {aid for aid, _pid in harness.state.addr}
    candidates = sorted(
        aid for aid in addressed
        if harness.state.status.get(aid) is Status.ACCEPTED
        and harness.state.artifacts[aid].provenance is not None
        and harness.state.artifacts[aid].provenance.role
        in {"conjecturer", "synthesizer"}
    )
    return candidates[0] if candidates else None


def _stage(harness) -> None:
    """The fall, on the OPEN harness, after the live cycles have run."""
    subject_id = _subject(harness)
    if subject_id is None:
        report["outcome"] = "NO_SUBJECT: the run produced no accepted candidate"
        return
    report["subject"] = subject_id
    report["subject_head"] = (harness.state.artifacts[subject_id].content_ref or "")[:90]

    seed = next(
        (p for p in harness.state.problems.values()
         if p.provenance.trigger.value == "seed"), None
    )
    if seed is None:
        report["outcome"] = "NO_SEED_PROBLEM"
        return
    token = seed.description.split()[0].lower()
    scope = {
        "schema": "declarative-scope.v1",
        "predicate": {"op": "contains",
                      "args": [{"field": "description"}, {"text": token}]},
    }
    report["seed_problem"] = seed.id
    report["scope_token"] = token

    case = harness.create_artifact(
        "reach record (staged, L-6): this subject was cited across the run's "
        "problem lineages",
        interface=Interface(),
        provenance=Provenance(role="import"),
    )
    promotion = operations.ensure_promotion_problem(
        harness, subject_id,
        "promote or refuse this explanation as the frame for the scope",
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject_id, scope=scope,
        reach_case_refs=(case.id,),
        departure_protocol="declare which of its commitments you break with",
    )
    report["assertion"] = assertion.id
    report["promotion_problem"] = promotion.id
    report["consulted_before_the_fall"] = [
        g.assertion_id for g in consulted(harness)
    ]
    carried = list(framed_problem_ids(harness, scope))
    report["carried_count"] = len(carried)
    report["carried_includes_seed"] = seed.id in carried
    report["frame_renders_before_the_fall"] = bool(
        render_frame_slice_context(harness, seed.id)
    )

    # A warrant may only name a REGISTERED commitment. The wound's is
    # OBSERVATION-VALUED -- that is what makes a failure on it a wound rather
    # than an ordinary criticism (§9.6).
    harness.register_commitment(Commitment(
        id="observation:staged-wound@v1", eval="program:json_wf",
        observation_valued=True,
    ))
    harness.register_commitment(Commitment(
        id="argument:staged-fall@v1", eval="program:json_wf",
    ))

    # --- Prop 9.6: a WOUND changes status(b) and leaves standing(b) alone ---
    standing_before = standing_of(harness, subject_id)
    wound = register_fail_warrant(
        harness,
        commitment_id="observation:staged-wound@v1",
        target_id=subject_id,
        nu_content="nu (staged, L-6): the wound on this subject is sound and relevant",
        critic_content="critic (staged, L-6): this explanation mispredicts",
        trace_ref=harness.blobs.put(b'{"verdict": "fail", "staged": "wound"}'),
    )
    report["prop_9_6"] = {
        "subject_status_after_wound": str(harness.state.status.get(subject_id)),
        "assertion_status_after_wound": str(harness.state.status.get(assertion.id)),
        "standing_unchanged": standing_of(harness, subject_id) == standing_before,
        "marks_after_wound": premise_orphaned(harness),
        "frame_still_renders_after_wound": bool(
            render_frame_crisis_context(harness, seed.id)
        ),
        "wound_id": wound.id if wound is not None else None,
    }

    # --- then the FALL: a warranted attack on the ASSERTION ----------------
    fall = register_fail_warrant(
        harness,
        commitment_id="argument:staged-fall@v1",
        target_id=assertion.id,
        nu_content="nu (staged, L-6): the case against this frame assertion is sound",
        critic_content="critic (staged, L-6): this frame overreaches the scope it claims",
        trace_ref=harness.blobs.put(b'{"verdict": "fail", "staged": "fall"}'),
    )
    report["fall_critic"] = fall.id if fall is not None else None
    report["typed_outcomes"] = {
        "assertion_status": str(harness.state.status.get(assertion.id)),
        "fallen_frames": [
            {"assertion": f.assertion_id, "grade": f.grade, "label": f.label.value}
            for f in fallen_frames(harness)
        ],
        "marks": premise_orphaned(harness),
        "open_orphans": open_orphans(harness),
        "batch_offers": [
            {"cause": o["cause"], "grade": o["grade"], "size": o["size"]}
            for o in batch_translation_offers(harness)
        ],
        "standing_after_the_fall": [
            g.assertion_id for g in standing_of(harness, subject_id)
        ],
        "fallen_frame_still_renders": bool(
            render_frame_slice_context(harness, seed.id)
        ),
    }


def main() -> int:
    real = ops.run_scheduler

    def staging_scheduler(harness, config, cycles, token_budget=None, **kw):
        # FINALLY, not after. The scheduler can end by raising -- this config
        # has died `operational_failure` at cycle 2 on every attempt -- and a
        # staging that only ran on the clean path would silently skip the gate
        # on exactly the runs that reached the frontier anyway. The harness is
        # still open here either way, which is the whole reason to stage from
        # inside rather than on the stopped root.
        try:
            return real(harness, config, cycles, token_budget, **kw)
        finally:
            try:
                _stage(harness)
            except Exception as exc:        # noqa: BLE001 - reported, not raised
                report["staging_error"] = f"{type(exc).__name__}: {exc}"
                import traceback
                report["staging_traceback"] = traceback.format_exc()[-1200:]

    ops.run_scheduler = staging_scheduler
    from deepreason.cli.main import main as cli

    root = HERE / "run"
    argv = [
        "--root", str(root), "run",
        "--run-manifest", str(root / "run-manifest.json"),
        "--problem", str(root / "problem.json"),
        "--budget", f"cycles={sys.argv[1] if len(sys.argv) > 1 else 6}",
        "--token-budget", sys.argv[2] if len(sys.argv) > 2 else "150000",
    ]
    try:
        rc = cli(argv)
    except SystemExit as exc:
        rc = exc.code
    report["run_rc"] = rc

    from deepreason.invariants import verify_root
    result = verify_root(root)
    report["verify_root"] = {
        "violations": len(result["violations"]),
        "checks": sorted({v["check"] for v in result["violations"]}),
        "details": [v["detail"][:200] for v in result["violations"]][:5],
    }

    outcomes = report.get("typed_outcomes") or {}
    p96 = report.get("prop_9_6") or {}
    ok = (
        len(outcomes.get("fallen_frames", [])) == 1
        and outcomes["fallen_frames"][0]["grade"] == "fall"
        and bool(outcomes.get("marks"))
        and set(outcomes["marks"].values()) == {"premise-refuted"}
        and p96.get("standing_unchanged") is True
        and not p96.get("marks_after_wound")
        and p96.get("subject_status_after_wound") == "Status.REFUTED"
        and p96.get("assertion_status_after_wound") == "Status.ACCEPTED"
        # L-6's third clause, and it is ABSOLUTE rather than a delta: the
        # first attempt passed a delta test while the record carried a
        # terminal-authority violation its own staging had caused.
        and len(result["violations"]) == 0
    )
    report["outcome"] = "L-6 PASS" if ok else "L-6 FAIL"
    REPORT.write_text(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(report, indent=1, sort_keys=True, default=str))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
