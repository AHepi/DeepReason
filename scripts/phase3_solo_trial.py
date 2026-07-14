#!/usr/bin/env python
"""Phase 3, step 1: the sealed solo design (experiments/
solo_autonomics_design.md, commit caa0194) enters runs/autonomics as an
ORDINARY candidate — same skeleton shape, same criteria, same compiled
forbidden-case commitments, then the same gauntlet the harness's own
candidates face: program criticism, the rubric trial under the full
guard, and an argumentative critic pass. No special treatment in either
direction."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.config import load as load_config  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.informal.skeleton import compile_forbidden_commitments, parse_skeleton  # noqa: E402
from deepreason.informal.trial import run_trial  # noqa: E402
from deepreason.llm.adapter import build_adapter  # noqa: E402
from deepreason.llm.budget import TokenMeter  # noqa: E402
from deepreason.ontology import Interface, Provenance, Status  # noqa: E402
from deepreason.rules.crit import crit_argumentative_batch, crit_program  # noqa: E402

SKELETON = {
    "claim": (
        "A self-calibrating harness is safe iff its controller can only "
        "ever touch the generator's knobs, never the tribunal's — and "
        "every calibration decision is itself an ordinary, attackable, "
        "replayable artifact adjudicated by the court it cannot influence."
    ),
    "mechanism": (
        "(1) Constitutional two-ledger partition fixed at registration: "
        "generator ledger (controller-writable: reasoning depth, caps, "
        "VS_K, batch size, routing, school knobs, focus shares) vs "
        "tribunal ledger (controller-forbidden: criticism floors, trial "
        "paraphrase N, audit period, judge ensemble, gate epsilon — "
        "anything adjudication reads). The controller tunes the "
        "defendant, structurally never the court. (2) Policy-as-artifact: "
        "the controller emits calibration_policy artifacts (knob vector + "
        "log-window evidence + validity node); the scheduler applies the "
        "latest ACCEPTED policy; a standing attack suspends it and "
        "reverts to the last accepted policy (fail-static). Updates are "
        "pure functions of the log prefix — replayable. (3) Signal->knob "
        "table with damping: truncation rate drives caps (x1.5 up, x0.75 "
        "down after 3 clean windows); valid-JSON drives json_mode/retry/"
        "tier escalation one step per window; admission-rate drops "
        "delegate to the existing capture ladder; survivors-per-token "
        "drives reasoning/routing ONLY via epsilon-greedy probe cycles "
        "with a sequential test over N probes (never single-run deltas). "
        "(4) Frozen reference arm: a seq-determined ~10% of cycles run an "
        "immutable reference policy; Goodhart = controlled-arm proxy "
        "metrics improving while reference-normalized deep metrics "
        "(survivor HV, coverage, guard block rate) degrade beyond a "
        "bound — the alarm freezes the controller until an appellate "
        "ruling. (5) Aging liveness queue: priority = age x unsolvedness "
        "guarantees every registered problem and experiment is funded "
        "within K cycles, replacing manual focus locks."
    ),
    "scope": {
        "covers": [
            "completion caps", "reasoning depth", "model routing",
            "VS_K and batch size", "school knobs and focus shares",
            "starvation prevention for problems and experiments",
        ],
        "excludes": [
            "tribunal parameters (deliberately untunable)",
            "provider probe design (separate problem)",
            "anything requiring wall-clock or randomness outside the log",
        ],
    },
    "forbidden": [
        {"case": "A diff shows any tribunal-ledger knob changed by a controller policy artifact.",
         "eval": "rubric:std-autonomics"},
        {"case": "Controlled-arm survivor yield rises over three windows while reference-arm-normalized survivor HV or coverage falls beyond the bound, without the Goodhart alarm firing.",
         "eval": "rubric:std-autonomics"},
        {"case": "A registered problem or pre-registered experiment goes unworked for more than K cycles despite the aging queue.",
         "eval": "rubric:std-autonomics"},
        {"case": "A knob flip-flops more than M times within one window (damping failure).",
         "eval": "rubric:std-autonomics"},
        {"case": "Replay of a run reproduces different policy artifacts than the live run emitted.",
         "eval": "rubric:std-autonomics"},
        {"case": "The controller emits a new policy while its previous policy is under a standing attack.",
         "eval": "rubric:std-autonomics"},
    ],
    "prose_notes": (
        "Sealed solo entry (operating agent), committed blind at caa0194 "
        "before any harness candidate was read. Reuses existing machinery "
        "as actuators (capture ladder, appellate channel, gate); the two "
        "novel commitments are the ledger partition (checkable by diff) "
        "and the frozen reference arm (makes Goodhart a measurable "
        "divergence). Costs ~20% of cycles (reference + probe arms) as "
        "the price of an untunable baseline and noise-proof repolicying."
    ),
}


def main() -> int:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1
    harness = Harness(Path("runs/autonomics"))
    config = load_config(Path("config/deepseek.yaml"))
    meter = TokenMeter(budget=60_000)

    content = json.dumps(SKELETON, sort_keys=True)
    skeleton = parse_skeleton(content)
    assert skeleton is not None, "solo design does not parse as a skeleton"
    commitments = ["skeleton-wf", "kappa-autonomics"]
    commitments += [
        c for c in compile_forbidden_commitments(harness, skeleton) if c not in commitments
    ]
    artifact = harness.create_artifact(
        content,
        interface=Interface(commitments=commitments),
        provenance=Provenance(role="conjecturer"),
        problem_id="pi-autonomics",
    )
    print(f"registered solo design: {artifact.id[:12]} "
          f"[{harness.state.status.get(artifact.id).value}]")

    adapter = build_adapter(config, harness.blobs, meter=meter)

    diagnostics: list = []
    crit_program(harness, artifact.id)
    print(f"after program criticism: {harness.state.status.get(artifact.id).value}")

    kappa = harness.commitments["kappa-autonomics"]
    run_trial(
        harness, artifact.id, kappa, adapter, config, diagnostics,
        authority="legacy_status",
    )
    print(f"after rubric trial: {harness.state.status.get(artifact.id).value}")

    if harness.state.status.get(artifact.id) == Status.ACCEPTED:
        crit_argumentative_batch(harness, [artifact.id], adapter, config)
        print(f"after argumentative critic: {harness.state.status.get(artifact.id).value}")

    for d in diagnostics:
        print("  diag:", json.dumps(d)[:180])
    print("meter:", json.dumps(meter.snapshot(), sort_keys=True))
    print(f"FINAL: {artifact.id[:12]} {harness.state.status.get(artifact.id).value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
