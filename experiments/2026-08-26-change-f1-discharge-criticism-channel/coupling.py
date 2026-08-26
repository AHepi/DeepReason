#!/usr/bin/env python3
"""R9 — does the discharge channel actually CARRY criticism? Channel on vs off.

W2 measured that criticism on this tree did no causal work, and named the
reason in one line: **nothing that makes the next candidate was ever shown it**
(0 of 196 LLM attacks exposed to a later conjecture dispatch,
`experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md` §3a). F1's claim is
that the channel closes that gap. This instrument tests the claim the only way
an offline run can.

WHAT IT MEASURES, stated before the number so the number cannot be over-read.
It builds two roots that differ in exactly one respect — `Config.DISCHARGE_POLICY`
— and drives each with a RESPONSIVE WRITER: a stub that answers whatever
criticism its pack actually shows it, and that can do nothing about criticism it
is not shown. So the measurement is:

    with the channel ON,  a responsive writer couples above placebo;
    with the channel OFF, it cannot, because the criticism never reaches it.

That is a property of the PLUMBING, and it is falsifiable: if the render or the
record reader were broken, the on-arm would look like the off-arm.

WHAT IT DOES NOT MEASURE: whether a real provider model responds. That needs the
live four-arm A/B parked as P2, and `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md`
Q1 forbids assuming it — a pack's own claim to have honoured a standing
instruction is the least reliable artifact in the trajectory. RESULTS.md says so.

THE RATE IS W2's, NOT A NEW ONE. R1_mechanical, reproduced from `q5.py` lines
175–217: for a warrant-bearing criticism, the criticized respect is THE
COMMITMENT THE TARGET FAILED, and the next candidate is COUPLED iff it PASSES
that same commitment, re-evaluated by `deepreason.programs.evaluate` on the next
candidate's own bytes. Every rate carries its PLACEBO — the same evaluation run
on the candidate BEFORE the criticism, which cannot have been influenced by it —
and only `coupling - placebo` is evidence. W2's residue item 1 rules
R2_prose-quote inadmissible as a rate, so it is not computed here.

Usage, from the repository root:

    python experiments/2026-08-26-change-f1-discharge-criticism-channel/coupling.py \
        coupling.json
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from deepreason import programs                                    # noqa: E402
from deepreason.config import Config                               # noqa: E402
from deepreason.discharge import (                                 # noqa: E402
    render_open_criticism_context,
    resolve_policy,
)
from deepreason.harness import Harness                             # noqa: E402
from deepreason.llm.packs import render_conj_pack                  # noqa: E402
from deepreason.ontology import (                                  # noqa: E402
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
)
from deepreason.rules.warrants import register_fail_warrant        # noqa: E402

# SIX INDEPENDENT RESPECTS, not one, and the reason is the PLACEBO rather than
# statistical comfort. With a single respect the run has exactly ONE criticism
# -- once the writer answers it nothing fails again -- and that criticism has no
# candidate before it that is not its own target, so W2's placebo is UNDEFINED
# and the only admissible column cannot be computed. Six independent respects
# give every criticism after the first a real predecessor, and because the
# respects are independent, a candidate answering respect j does not
# accidentally satisfy respect i. It is also the shape W2 measured: criticisms
# interleaved through a run, each about something different.
#
# No space after `predicate:` -- `evaluate` partitions on the colon and hands
# the remainder to `ast.parse`, which reads a leading space as an indent and
# fails the verdict for a reason that has nothing to do with the candidate.
RESPECTS = (
    "the solar forcing that sets the spring-neap range",
    "the shallow-water overtides in this harbour",
    "the inverse-barometer response to pressure",
    "the annual cycle in the mean sea level",
    "the wind setup along the estuary axis",
    "the datum the predicted heights are referred to",
)
DESCRIPTION = "state the tide table for this harbour, respect {i}"

MODAL = "candidate {tag}: the tide here is the moon's differential pull, and nothing else"
RESPONSIVE = "candidate {tag}: the tide here is the moon's pull together with {span}"

OPEN_CRITICISM_HEADER = "OPEN CRITICISMS ON THIS PROBLEM"
CITED_SPAN = "CITED SPAN: "


def responsive_writer(pack: str, tag: str) -> str:
    """A writer that answers what it is SHOWN, and nothing it is not.

    It reads ONLY the pack's open-criticism section, and inside it only the
    CITED SPAN the render carries. Two reasons, both about not measuring the
    wrong thing:

    - The criteria section renders each commitment's `eval` string, so a writer
      scanning the raw pack for the discriminating phrase would find it whether
      or not the channel delivered anything, and the on/off comparison would be
      measuring the criteria renderer instead of the channel.
    - Reading the CITED SPAN rather than the whole claim exercises the same
      machinery a real writer would use, span extraction included, so a break
      there surfaces as a failure to couple rather than passing unseen.
    """
    if OPEN_CRITICISM_HEADER not in pack:
        return MODAL.format(tag=tag)
    section = pack.split(OPEN_CRITICISM_HEADER, 1)[1].split("\n## ", 1)[0]
    if CITED_SPAN not in section:
        return MODAL.format(tag=tag)
    span = section.split(CITED_SPAN, 1)[1].splitlines()[0].strip()
    if not span or span == "(none quoted)":
        return MODAL.format(tag=tag)
    return RESPONSIVE.format(tag=tag, span=span)


def _commitment(index: int) -> Commitment:
    return Commitment(
        id=f"k:accounts-for-respect-{index}",
        eval=f"predicate:{RESPECTS[index]!r} in content",
    )


def drive(root: pathlib.Path, *, channel_on: bool) -> dict:
    """One offline run. Identical either way except for the policy.

    Two passes per respect, CONSECUTIVELY: the first candidate is written with
    nothing to answer and is criticized mechanically; the second is written
    from a pack that -- with the channel on -- carries that criticism.

    Consecutive, not interleaved, and the first draft of this instrument got it
    wrong. W2's `next_candidate` is ROOT-WIDE: it takes the next candidate in
    log order, whoever posed it. Interleaving the respects therefore made every
    criticism's "next candidate" belong to a DIFFERENT problem, which fails the
    criticized commitment for a reason that has nothing to do with the
    criticism, and the on-arm measured 0.0 while the channel was working
    perfectly. Working one respect at a time is also what a real seat does, and
    it is why W2's instrument is sound on real roots.

    The respects still differ from each other, which is what keeps the PLACEBO
    honest: the candidate before criticism i answers respect i-1, so it does
    not accidentally satisfy respect i.
    """
    harness = Harness(root)
    policy = resolve_policy(
        Config(DISCHARGE_POLICY="discharge-required.v1" if channel_on else "off")
    )
    problems = []
    for index, _ in enumerate(RESPECTS):
        commitment = _commitment(index)
        harness.register_commitment(commitment)
        problems.append((
            harness.register_problem(
                Problem(
                    id=f"p-tides-{index}",
                    description=DESCRIPTION.format(i=index),
                    criteria=[commitment.id],
                    provenance=ProblemProvenance.model_validate(
                        {"trigger": "seed", "from": []}
                    ),
                )
            ),
            commitment,
        ))

    events = []
    for index, (problem, commitment) in enumerate(problems):
        for turn in ("a", "b"):
            pack = render_conj_pack(
                problem,
                harness.state,
                harness.commitments,
                harness.blobs,
                vs_k=1,
                token_budget=4000,
                open_criticism_context=render_open_criticism_context(
                    harness, problem.id, policy
                ),
            )
            artifact = harness.create_artifact(
                responsive_writer(pack, f"{index}{turn}"),
                problem_id=problem.id,
                provenance=Provenance(role="conjecturer"),
                interface=Interface(commitments=[commitment.id], refs=[]),
            )
            events.append({"kind": "candidate", "seq": harness._next_seq - 1,
                           "artifact": artifact.id, "commitment": commitment.id})

            verdict, _ = programs.evaluate(commitment, artifact, harness.blobs)
            if str(verdict).split(".")[-1].lower() == "pass":
                continue
            critic = register_fail_warrant(
                harness,
                commitment_id=commitment.id,
                target_id=artifact.id,
                nu_content=f"nu: {artifact.id} does not account for respect {index}",
                critic_content=(
                    "critic: this candidate accounts for the lunar pull alone. "
                    f'It omits "{RESPECTS[index]}", so it cannot give the '
                    "heights the problem asks for."
                ),
                trace_ref="inline:offline-coupling-instrument",
            )
            if critic is not None:
                events.append({"kind": "criticism", "seq": harness._next_seq - 1,
                               "artifact": critic.id, "target": artifact.id,
                               "commitment": commitment.id})
    return {"harness": harness, "events": events}


def r1_mechanical(run: dict) -> dict:
    """W2's R1, reproduced from `q5.py` lines 175-217 on this root's own events.

    W2's committed `census.py`/`q5.py` were tried first and cannot run here;
    the reason is recorded in the emitted JSON rather than hidden, and this
    function reproduces the operationalization those lines define rather than
    inventing a new one.
    """
    harness = run["harness"]
    state = harness.state
    candidates = [e for e in run["events"] if e["kind"] == "candidate"]
    seqs = [c["seq"] for c in candidates]

    def neighbour(after_seq: int, *, forward: bool, exclude: str) -> str | None:
        ordered = candidates if forward else list(reversed(candidates))
        for row in ordered:
            if row["artifact"] == exclude:
                continue
            if forward and row["seq"] > after_seq:
                return row["artifact"]
            if not forward and row["seq"] < after_seq:
                return row["artifact"]
        return None

    def passes(artifact_id: str | None, commitment_id: str) -> bool | None:
        """`q5.py`'s exactness, respect by respect.

        The commitment is the CRITICISM's OWN -- the one its target failed --
        never a single global one, so "changed in the criticized respect" stays
        the thing W2 defined even with six respects in flight at once.
        """
        if artifact_id is None:
            return None
        verdict, _ = programs.evaluate(
            harness.commitments[commitment_id], state.artifacts[artifact_id], harness.blobs
        )
        return str(verdict).split(".")[-1].lower() == "pass"

    rows = []
    for criticism in [e for e in run["events"] if e["kind"] == "criticism"]:
        nxt = neighbour(criticism["seq"], forward=True, exclude=criticism["target"])
        pre = neighbour(criticism["seq"], forward=False, exclude=criticism["target"])
        commitment_id = criticism["commitment"]
        coupled = passes(nxt, commitment_id)
        placebo = passes(pre, commitment_id)
        rows.append({
            "seq": criticism["seq"],
            "target": criticism["target"],
            "commitment": criticism["commitment"],
            "next": nxt,
            "placebo": pre,
            "verdict": (
                "no-next-candidate" if nxt is None
                else "coupled" if coupled else "neglected"
            ),
            "placebo_passes": placebo,
        })

    measurable = [r for r in rows if r["verdict"] in ("coupled", "neglected")]
    with_placebo = [r for r in rows if r["placebo_passes"] is not None]
    coupling = (
        sum(1 for r in measurable if r["verdict"] == "coupled") / len(measurable)
        if measurable else None
    )
    placebo = (
        sum(1 for r in with_placebo if r["placebo_passes"]) / len(with_placebo)
        if with_placebo else None
    )
    return {
        "n_criticisms": len(rows),
        "n_measurable": len(measurable),
        "coupling": coupling,
        "placebo": placebo,
        "coupling_minus_placebo": (
            None if coupling is None or placebo is None else round(coupling - placebo, 4)
        ),
        "neglect": (
            None if coupling is None else round(1.0 - coupling, 4)
        ),
        "candidate_seqs": seqs,
        "rows": rows,
    }


W2 = REPO / "experiments/2026-08-26-run-anatomy-w2-criticism"


def w2_rates(root: pathlib.Path, scratch: pathlib.Path) -> dict:
    """W2's OWN committed instruments, unmodified, over this root.

    SPEC S9 allowed a fallback if they could not run on a stub root. They can,
    so they are the HEADLINE and the reproduction below is a cross-check rather
    than the measurement. That matters: a rate computed by the instrument that
    produced the finding is not open to the objection that the new tranche
    scored its own homework.
    """
    import subprocess

    census = scratch / f"{root.name}-census.json"
    rates = scratch / f"{root.name}-q5.json"
    for argv in (
        [str(W2 / "census.py"), str(root), str(census)],
        [str(W2 / "q5.py"), str(root), str(census), str(rates)],
    ):
        result = subprocess.run(
            [sys.executable, *argv], capture_output=True, text=True, cwd=str(REPO)
        )
        if result.returncode != 0:
            return {
                "ran": False,
                "failed_at": pathlib.Path(argv[0]).name,
                "stderr_tail": (result.stderr or "").strip().splitlines()[-4:],
            }
    payload = json.loads(rates.read_text())
    return {
        "ran": True,
        "instrument": "experiments/2026-08-26-run-anatomy-w2-criticism/{census,q5}.py, unmodified",
        "R1_mechanical": payload.get("R1_mechanical"),
        # Recorded, not hidden: W2's channel census reads
        # `workflow-context-exposure-v2` records, which only the v6 workflow
        # path writes. An offline stub root has none, so this reports ZERO
        # exposure even in the arm where the criticism demonstrably reached the
        # writer. The exposure census is INAPPLICABLE here; the coupling rate is
        # not, because it is computed from candidates and commitments alone.
        "exposure_census_inapplicable": payload.get("exposure"),
    }


def main() -> int:
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "coupling.json")
    workspace = pathlib.Path(tempfile.mkdtemp(prefix="f1-coupling-"))
    try:
        report = {
            "instrument": "F1 coupling, channel on vs off",
            "operationalization": (
                "W2 R1_mechanical, reproduced from "
                "experiments/2026-08-26-run-anatomy-w2-criticism/q5.py lines 175-217: "
                "coupled iff the next candidate PASSES the commitment the criticized "
                "one failed, re-evaluated by deepreason.programs.evaluate on the next "
                "candidate's own bytes; every rate carries the same evaluation on the "
                "candidate BEFORE the criticism as its placebo."
            ),
            "claim": (
                "This measures whether the CHANNEL DELIVERS -- a responsive writer "
                "couples above placebo iff the criticism reaches it. It does NOT "
                "measure whether a live provider model responds; that is PARKED as P2."
            ),
            "respects": list(RESPECTS),
        }
        for arm, channel_on in (("on", True), ("off", False)):
            run = drive(workspace / arm, channel_on=channel_on)
            report[arm] = {
                "w2": w2_rates(workspace / arm, workspace),
                "reproduction": r1_mechanical(run),
            }
        # The two must agree. They are independent implementations of one
        # definition, so a disagreement is a finding about an INSTRUMENT and
        # would have to be resolved before either number could be quoted.
        report["cross_check"] = {}
        for arm in ("on", "off"):
            w2 = (report[arm]["w2"].get("R1_mechanical") or {})
            mine = report[arm]["reproduction"]
            report["cross_check"][arm] = {
                "w2_coupling_minus_placebo": w2.get("CouplingRate_minus_Placebo"),
                "reproduction_coupling_minus_placebo": mine["coupling_minus_placebo"],
                "agree": w2.get("CouplingRate_minus_Placebo") == mine["coupling_minus_placebo"],
            }
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        for arm in ("on", "off"):
            w2 = (report[arm]["w2"].get("R1_mechanical") or {})
            check = report["cross_check"][arm]
            print(
                f"{arm:>3}: [W2 instrument] n={w2.get('denominator_measurable')}  "
                f"coupling={w2.get('CouplingRate')}  placebo={w2.get('PlaceboRate')}  "
                f"coupling-placebo={w2.get('CouplingRate_minus_Placebo')}  "
                f"neglect={w2.get('NeglectRate')}   "
                f"[reproduction agrees: {check['agree']}]"
            )
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
