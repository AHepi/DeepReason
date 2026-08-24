"""Succession -- ordinary discrimination, with the ONE proper render exception.

§9.7: "Rival frame assertions over overlapping scope trigger the ordinary
>=2-survivors discrimination spawn, resolved comparatively... One render
exception is proper to succession: the succession pack suppresses the
incumbent's frame slice and renders both articulation digests, so the trial of
a frame is framed by neither party."

NOTHING IS SPAWNED HERE. The rivalry reaches the frontier through
`rules/spawn.py`'s existing discrimination branch, unchanged and unaware of
frames: two accepted candidates on one problem is two accepted candidates on
one problem, whatever they claim. What this module adds is what the pack SHOWS
once that problem is selected, and what the trial RECORDS about how it judged.

The failure being mitigated has a name: INCUMBENT-JUDGE BIAS -- a succession
posed inside the incumbent's vocabulary is adjudicated by the defendant. The
mitigation is SYMMETRIC EXPOSURE, and the calculus says plainly what it is not:
"a view from nowhere is not on offer."

READ-ONLY in the sense `render.py` is: nothing here writes a label, an edge or
a warrant. The trial RECORD is registered by `record_succession_trial`, which
is the one function in this module that touches the log at all, and what it
registers is an ordinary attackable artifact carrying no problem_id.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from deepreason.calculus.render import (
    FRAME_SLICE_ATTACKERS_N,
    articulation_digest,
    subject_attackers,
)
from deepreason.calculus.standing import frame_assertion_body
from deepreason.ontology import Provenance, SpawnTrigger

SUCCESSION_TRIAL_SCHEMA = "succession-trial.v1"

# Q2c's answer, and the record carries it so a reader never has to infer it.
# FIXED rather than randomized: §12.1's determinism requirement admits exactly
# two roads -- seed the kernel or log the draw -- and Q2's own measurement is
# that criterion order SHIFTS a criterion's mean, not that randomizing removes
# the shift. Fixing it makes the shift constant and named.
SUCCESSION_CRITERION_ORDER = "fixed"

# Typed outcomes. `no-verdict` is the one Q2b requires and is NEVER a tiebreak:
# when the two orders disagree the rivalry stays unresolved and routes onward,
# the way the harness already treats no-consensus.
NO_VERDICT = "no-verdict"
NEITHER = "neither"
ORDER_DISAGREEMENT = "order-disagreement"


@dataclass(frozen=True)
class SuccessionTrial:
    """One succession trial, as the pack and the record see it. DERIVED."""

    problem_id: str
    promotion_problem: str
    rival_ids: tuple[str, ...]
    subject_ids: tuple[str, ...]
    criteria: tuple[str, ...]


def succession_trial_of(harness, problem_id: str) -> SuccessionTrial | None:
    """The trial this problem IS, or None.

    Three conditions, and each one is a fact about the record rather than a
    declaration: the problem is a DISCRIMINATION problem, the problem it
    discriminates for is a PROMOTION problem, and at least two of its rivals
    are recognised frame assertions. Recognition is STRICT -- an artifact whose
    interface the controller's compiler would not have emitted is not a frame
    claim, so a discrimination between two things that merely mention frames is
    an ordinary discrimination and gets the ordinary pack.
    """
    problem = harness.state.problems.get(problem_id)
    if problem is None or problem.provenance.trigger is not SpawnTrigger.DISCRIMINATION:
        return None
    sources = list(problem.provenance.from_)
    if not sources:
        return None
    parent = harness.state.problems.get(sources[0])
    if parent is None or parent.provenance.trigger is not SpawnTrigger.PROMOTION:
        return None
    rivals, subjects = [], []
    for aid in sources[1:]:
        artifact = harness.state.artifacts.get(aid)
        if artifact is None:
            continue
        body = frame_assertion_body(harness, artifact)
        if body is None:
            continue
        rivals.append(aid)
        subjects.append(body.subject_ref)
    if len(rivals) < 2:
        return None
    return SuccessionTrial(
        problem_id=problem_id,
        promotion_problem=parent.id,
        rival_ids=tuple(rivals),
        subject_ids=tuple(subjects),
        # Q2c: the criteria the trial judges on, in the FIXED order, taken
        # from the PROMOTION problem -- the discrimination problem carries
        # none of its own, and a trial that showed an empty criteria block
        # while recording "criterion order: fixed" would be claiming a
        # discipline it did not have.
        criteria=tuple(sorted(parent.criteria)),
    )


def is_succession_trial(harness, problem_id: str) -> bool:
    """Whether the ONE render exception applies to this problem."""
    return succession_trial_of(harness, problem_id) is not None


# --- the render exception ----------------------------------------------------


def _candidate_block(harness, label: str, subject_id: str) -> list[str]:
    """One candidate's half of the pack. IDENTICAL in shape for both, because
    symmetric exposure is the whole mitigation: a difference in how the two are
    presented would reintroduce the bias the suppression removes."""
    head, truncated, commitments = articulation_digest(harness, subject_id)
    lines = [f"  {label}: subject {subject_id}", f"    {head}"]
    if truncated:
        lines[-1] += (
            " […articulation compressed; expand with `deepreason standing --json`]"
        )
    if commitments:
        lines.append("    its commitments: " + ", ".join(commitments))
    attackers = subject_attackers(harness, subject_id)
    shown = attackers[:FRAME_SLICE_ATTACKERS_N]
    if shown:
        # ANOMALY CONSERVATION, rendered on BOTH sides or on neither: what
        # broke each candidate is what the successor must predict. The cap
        # states itself, for `render.py`'s own reason -- a count shown without
        # its total is a silent cap.
        count = (
            f"{len(shown)} of {len(attackers)} shown, by id"
            if len(attackers) > len(shown)
            else f"all {len(attackers)}"
        )
        lines.append(f"    ITS WOUNDS ({count}):")
        for attacker, status, head_text in shown:
            lines.append(f"      - {attacker} [{status}]: {head_text}")
    return lines


def render_succession_context(harness, problem_id: str) -> str | None:
    """The succession pack, or None when this problem is not a succession trial.

    NO PROVENANCE, POPULATED OR BLANK, and no incumbency label: the two
    candidates are ordered by SUBJECT ID, which is a fact about content rather
    than about who arrived first. Ordering them by incumbency would be
    provenance entering appraisal (Ax 4.1), and a "(incumbent)" marker would be
    the empty provenance-shaped slot `RESEARCH_JUDGE_BLINDING` measured as
    worse than a populated one.
    """
    trial = succession_trial_of(harness, problem_id)
    if trial is None:
        return None
    lines = [
        "SUCCESSION TRIAL. Neither candidate frames this problem: the frame "
        "slice is SUPPRESSED here, deliberately, so the trial of a frame is "
        "framed by neither party. What follows is both candidates' own "
        "articulation, presented identically. This is symmetric exposure, not "
        "a view from nowhere:"
    ]
    for label, subject_id in zip(
        ("CANDIDATE A", "CANDIDATE B"), sorted(set(trial.subject_ids))
    ):
        lines += _candidate_block(harness, label, subject_id)
    if trial.criteria:
        lines.append(
            "  CRITERIA, in a fixed order that is recorded with the verdict:"
        )
        lines += [f"    - {cid}" for cid in trial.criteria]
    return "\n".join(lines)


# --- the trial record (Q2a-Q2d) ----------------------------------------------


def program_road(harness, trial: SuccessionTrial) -> list[dict]:
    """Each rival pair judged in BOTH presentation orders, by program.

    Q2a asks the trial to judge both orders. For a PROGRAM road that is a
    demonstration rather than a precaution: the verdict is order-invariant by
    construction, and running it both ways is what turns "it cannot flip" from
    an assertion into a recorded fact. A road that skipped the second order
    because it knew the answer would be claiming the invariance it never
    exhibited.

    By the time a succession trial exists, both rivals have already PASSED the
    promotion criteria -- a candidate that fails `accounts-for` is refuted by
    `promotion_criteria_sweep` and is not a surviving rival, so the
    discrimination never spawns. The program therefore discriminates only where
    the record already separates the two, and otherwise answers `neither` with
    its reason and routes onward. That is D-6 answer A working as specified:
    program where a program can adjudicate, and a VISIBLE fallback where it
    cannot.
    """
    evaluations = []
    rivals = sorted(trial.rival_ids)
    for i, first in enumerate(rivals):
        for second in rivals[i + 1:]:
            orders = [
                _program_order(harness, "ab", first, second),
                _program_order(harness, "ba", second, first),
            ]
            tops = {o["top"] for o in orders}
            flipped = len(tops) > 1
            evaluations.append(
                {
                    "pair": [first, second],
                    "road": "program",
                    "orders": orders,
                    "flipped": flipped,
                    "outcome": (
                        NO_VERDICT if flipped
                        else (orders[0]["top"] or NEITHER)
                    ),
                    "no_verdict_reason": ORDER_DISAGREEMENT if flipped else None,
                }
            )
    return evaluations


def _program_order(harness, order: str, first: str, second: str) -> dict:
    """One presentation order, judged on what the record already holds.

    The only thing that can separate two SURVIVING rivals by program is a
    difference in what the record says each one succeeded: a candidate that
    declares wounds of the incumbent it accounts for has done work the other
    has not. Where both declare the same, the program says so and stops --
    `neither` is an answer, and it is the honest one.
    """
    claims = {}
    for aid in (first, second):
        artifact = harness.state.artifacts.get(aid)
        body = frame_assertion_body(harness, artifact) if artifact else None
        claims[aid] = frozenset(body.succeeded_wound_refs) if body else frozenset()
    a, b = claims[first], claims[second]
    if a > b:
        return {"order": order, "top": first, "reason": "accounts-for-strictly-more"}
    if b > a:
        return {"order": order, "top": second, "reason": "accounts-for-strictly-more"}
    return {
        "order": order,
        "top": None,
        "reason": (
            "both-account-for-the-same-wounds" if a
            else "neither-declares-a-succession"
        ),
    }


def pairwise_observer(evaluations: list, pair: tuple[str, str]):
    """A callback for `informal.trial.pairwise_discriminate`'s `observer`.

    The RUBRIC road's contribution, and the reason `informal/trial.py` needs to
    learn nothing about frames: it hands back the two rulings it already made
    and this function turns them into the same evaluation shape the program
    road produces. Q2b is the branch that matters -- when the two orders
    disagree the outcome is typed `no-verdict`, never a tiebreak, and no ruling
    is picked from either order.
    """

    def observe(ruling1, ruling2, outcome):
        first, second = pair
        top1 = None if ruling1.winner == "neither" else (
            first if ruling1.winner == "A" else second
        )
        # Under the swap the candidates change places, so "A" names `second`.
        top2 = None
        if ruling2 is not None and ruling2.winner != "neither":
            top2 = second if ruling2.winner == "A" else first
        flipped = ruling2 is not None and top1 != top2
        evaluations.append(
            {
                "pair": [first, second],
                "road": "rubric",
                "orders": [
                    {"order": "ab", "top": top1, "reason": outcome},
                    {"order": "ba", "top": top2,
                     "reason": outcome if ruling2 is not None else "not-run"},
                ],
                "flipped": flipped,
                "outcome": NO_VERDICT if flipped else (top1 or NEITHER),
                "no_verdict_reason": ORDER_DISAGREEMENT if flipped else None,
            }
        )

    return observe


def trial_record(
    trial: SuccessionTrial, evaluations: list, rubric_coverage=(0, 0)
) -> dict:
    """The body Q2a-Q2d require, as a plain dict.

    `flip_rate` is a FIELD and not a derivation a reader has to ask for (Q2d):
    "a succession trial that never reports its flip rate is claiming a
    precision it does not have." A trial with no evaluations reports `0.0`
    beside `evaluated: 0`, so an empty rate can never be misread as a clean
    one.
    """
    flips = sum(1 for e in evaluations if e["flipped"])
    evaluated = len(evaluations)
    outcomes = {e["outcome"] for e in evaluations}
    if NO_VERDICT in outcomes:
        overall = NO_VERDICT
    elif outcomes - {NEITHER}:
        overall = sorted(outcomes - {NEITHER})[0]
    else:
        overall = NEITHER
    return {
        "schema": SUCCESSION_TRIAL_SCHEMA,
        "problem": trial.problem_id,
        "promotion_problem": trial.promotion_problem,
        "rivals": sorted(trial.rival_ids),
        "criterion_order": SUCCESSION_CRITERION_ORDER,
        "criteria": list(trial.criteria),
        "evaluations": evaluations,
        "flips": flips,
        "evaluated": evaluated,
        "flip_rate": (flips / evaluated) if evaluated else 0.0,
        # NO SILENT CAPS. The rubric road costs two provider calls per pair, so
        # a caller may bound it -- and a bound nobody can see reads as full
        # coverage. Both numbers, always, so a reader can tell a trial that
        # judged everything from one that judged the first pair.
        "rubric_pairs_judged": rubric_coverage[0],
        "rubric_pairs_available": rubric_coverage[1],
        "outcome": overall,
    }


def rubric_presentation(harness, trial: SuccessionTrial, first: str, second: str):
    """What a judge is shown for one rival pair: the two ARTICULATION DIGESTS.

    Q2a's own words are "both orders of the two articulation digests", and the
    reason is §9.7's: the succession pack renders the two accounts of the
    world, not the two frame assertions' JSON. A judge handed the assertions
    would be comparing paperwork.
    """
    from deepreason.informal.trial import PairwisePresentation

    subjects = {}
    for aid in (first, second):
        artifact = harness.state.artifacts.get(aid)
        body = frame_assertion_body(harness, artifact) if artifact else None
        subjects[aid] = body.subject_ref if body else aid
    head_a, _, _ = articulation_digest(harness, subjects[first])
    head_b, _, _ = articulation_digest(harness, subjects[second])
    return PairwisePresentation(
        a_text=head_a, b_text=head_b, criteria=tuple(trial.criteria)
    )


def _pairs(rivals) -> list[tuple[str, str]]:
    ordered = sorted(rivals)
    return [
        (ordered[i], second)
        for i in range(len(ordered))
        for second in ordered[i + 1:]
    ]


def run_succession_trial(
    harness, problem, adapter, config, *, authority, diagnostics=None,
    rubric_rivals=None,
):
    """Both roads, then the record. Returns the trial artifact, or None.

    The PROGRAM road always runs and needs no seat: succession is not locked
    out of a solo run (the operator's standing law, and D-6 answer A). The
    RUBRIC road runs only when a `judge` seat exists, and it runs through
    `pairwise_discriminate` UNCHANGED, so its referential-integrity,
    order-swap and execution-supremacy screens all still apply -- D-6's "a
    rubric ruling is admitted only through the existing trial guard".

    `rubric_rivals` bounds what the rubric road judges, because each pair
    costs two provider calls and a trial over n rivals has n(n-1)/2 of them.
    The bound is DISCLOSED in the record rather than applied quietly: a
    coverage a reader cannot see reads as full coverage. The program road is
    free and always covers every pair.
    """
    trial = succession_trial_of(harness, problem.id)
    if trial is None:
        return None
    evaluations = program_road(harness, trial)
    available = _pairs(trial.rival_ids)
    judged = 0
    if adapter is not None and adapter.has_role("judge"):
        wanted = (
            available if rubric_rivals is None
            else [pair for pair in available if set(pair) <= set(rubric_rivals)]
        )
        from deepreason.informal.trial import pairwise_discriminate

        for first, second in wanted:
            pairwise_discriminate(
                harness, problem, first, second, adapter, config, diagnostics,
                authority=authority,
                presentation=rubric_presentation(harness, trial, first, second),
                observer=pairwise_observer(evaluations, (first, second)),
            )
            judged += 1
    return record_succession_trial(
        harness, problem.id, evaluations=evaluations,
        rubric_coverage=(judged, len(available)),
    )


def record_succession_trial(
    harness, problem_id: str, *, evaluations=None, rubric_coverage=None
):
    """Register the trial record, or None when this is not a succession trial.

    Registered with NO `problem_id`, for `file_premise`'s own recorded reason:
    an artifact ADDRESSING the discrimination problem would enter `addr` and
    become a RIVAL in the rivalry it is a diagnostic of. It is otherwise an
    ordinary artifact, so "your trial was mis-conducted" has somewhere to land
    (P6) -- a diagnostic nobody can attack is a diagnostic nobody can correct.

    Content-addressed, so re-recording an unchanged trial registers nothing.
    """
    trial = succession_trial_of(harness, problem_id)
    if trial is None:
        return None
    evaluations = (
        list(evaluations) if evaluations is not None
        else program_road(harness, trial)
    )
    body = trial_record(
        trial, evaluations,
        rubric_coverage=(
            rubric_coverage if rubric_coverage is not None
            else (0, len(_pairs(trial.rival_ids)))
        ),
    )
    artifact = harness.create_artifact(
        json.dumps(body, sort_keys=True),
        codec="json",
        provenance=Provenance(role="critic"),
    )
    harness.record_measure(
        inputs=[
            "succession.trial-flip-rate.v1",
            problem_id,
            artifact.id,
            f"{body['flip_rate']:.4f}",
            body["outcome"],
        ]
    )
    return artifact
