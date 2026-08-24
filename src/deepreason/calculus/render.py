"""Frame render semantics (§9.5) -- what a pack shows about the frame it is
posed in, and the three ways a frame leaves standing.

READ-ONLY, and the whole point. Everything here is recomputed from replayed
state on every call and stored nowhere; nothing in this module can write an
event, mint a warrant, or move a label. That is A9 (render acts only through
attention) and Prop 12.5 (standing never adjudicates) at the render layer,
where they are easiest to lose: a renderer is exactly the place where "while
we are here, we may as well also..." turns a readout into an authority.

THE MECHANISM IS NOT THE POSITION. `RESEARCH_FINDINGS_Q1Q10` Q1 measured that
standing instructions decay in context regardless of where they sit, so this
module does not rely on the model honouring what it is shown. Two things carry
the weight instead: the pack section built from `render_frame_slice_context` is
NON-DROPPABLE, so allocation cannot silently remove it; and
`held_frame_obligations` is computed by the harness from the record, so what a
candidate still implicitly holds is a fact about the log rather than a claim in
a reply. Where the slice's ORDER in the pack matters at all, it is a hedge, and
`DR-CON-packs-and-token-economy` records it as one.

NO PROVENANCE, POPULATED OR BLANK. `RESEARCH_JUDGE_BLINDING`'s placebo result
is that a present-but-empty provenance slot draws MORE attention than a filled
one, so nothing here renders an author, school, seat, model, endpoint, role or
origin -- and an absent part of the slice is ABSENT, with no header, no "(none)"
and no "redacted". Absence is the only signal, which is also how
`packs/allocate.py` already treats a dropped section.
"""

from __future__ import annotations

from dataclasses import dataclass

from deepreason.calculus.claims import (
    ClaimDecodeError,
    DepartureDeclarationV1,
    decode,
)
from deepreason.calculus.programs import DEPARTURE_DECLARATION_COMMITMENT
from deepreason.calculus.standing import consulted, frames
from deepreason.ontology import Status
from deepreason.programs import content_text

# How many of a subject's standing attackers render. A cap, and therefore
# DISCLOSED wherever it bites: the slice says "3 of 7 shown" rather than
# showing three and implying that is all there are.
FRAME_SLICE_ATTACKERS_N = 5
# The articulation head's char bound. "Compressed; expandable by view" is the
# calculus's own description -- the expansion is `deepreason standing --json`
# and the MCP `run_standing` tool, both of which carry the full slice.
ARTICULATION_DIGEST_CHARS = 400
_ATTACKER_HEAD_CHARS = 160

# Keyed to the LABEL, per the Formalization §8.2. Three grades, not two: the
# two-exit claim holds only under an extra axiom (`FrameDecisive`) that the
# source never states, and adopting it would buy a tidy theorem by declaring
# the calculus's own `S` label unreachable for frame assertions. `fall` and
# `revocation` are provably disjoint (Theorem 8.1); `contestation` is the one
# the claim assumed away, and it is rounded to NEITHER neighbour.
EXIT_GRADES: dict[Status, str] = {
    Status.REFUTED: "fall",
    Status.SUSPENDED_UNSUPPORTED: "revocation",
    Status.SUSPENDED: "contestation",
}

EXIT_GRADE_MEANINGS: dict[str, str] = {
    "fall": "the frame assertion itself is defeated",
    "revocation": "accreditation lost -- unearned, not wrong",
    "contestation": "unresolved attack; nobody has won",
}


@dataclass(frozen=True)
class FrameSliceV1:
    """One consulted frame, as a pack sees it. DERIVED and never stored, for
    the reason `StandingGrant` is: a stored slice could fall out of step with
    the log that implies it, and then the pack would be showing a frame the
    record no longer holds."""

    assertion_id: str
    subject_id: str
    promotion_problem: str
    digest_head: str
    digest_truncated: bool
    commitment_ids: tuple[str, ...]
    attackers: tuple[tuple[str, str, str], ...]  # (id, status, head)
    attackers_total: int
    departure_protocol: str
    declared_departures: tuple[tuple[str, tuple[str, ...]], ...]


def subject_attackers(harness, subject_id: str) -> tuple[tuple[str, str, str], ...]:
    """The subject's standing attackers, sorted by attacker id.

    Sorted by ID here even though `harness.state.att` ALREADY arrives sorted --
    `Harness._adjudicate` does `self.state.att = sorted(att)` before any reader
    sees it. So this call is redundant against today's harness and is kept
    anyway, deliberately, because the property the slice needs is its OWN and
    must not be borrowed: under the cap, WHICH attackers a pack shows depends
    on the order, and an order that came from anywhere but the ids would make
    that a fact about arrival. Arrival order is origin information, and
    appraisal may not read origin (Ax 4.1).

    A redundant sort is a real cost -- it is a line nothing can break -- so the
    reason it stays is recorded rather than assumed: `att`'s sortedness is an
    incidental serialization decision in a frozen surface this module must not
    depend on, and the test that pins this contract feeds a SHUFFLED `att` to
    prove the sort here is the one doing the work.
    """
    out = []
    for attacker, target in sorted(harness.state.att):
        if target != subject_id:
            continue
        status = harness.state.status.get(attacker)
        artifact = harness.state.artifacts.get(attacker)
        head = ""
        if artifact is not None:
            head = content_text(artifact, harness.blobs)[
                :_ATTACKER_HEAD_CHARS
            ].replace("\n", " ")
        out.append((attacker, status.value if status else "", head))
    return tuple(out)


def articulation_digest(harness, subject_id: str) -> tuple[str, bool, tuple[str, ...]]:
    """The subject's articulation, compressed: `(head, truncated, commitments)`.

    DETERMINISTIC, and deliberately not a summarizer call. A model-written
    digest would need a seat, a seat would change the pair inventory, and the
    inventory is what every qualification subject digest is built over -- one
    convenience would cost a ~14-minute battery rerun per home and put a
    generation seat between the record and what the frame is said to claim.
    The head plus the declared commitment ids is what a departure has to name
    anyway, so it is also the part that has to be exact.
    """
    artifact = harness.state.artifacts.get(subject_id)
    if artifact is None:
        return "", False, ()
    text = " ".join(content_text(artifact, harness.blobs).split())
    truncated = len(text) > ARTICULATION_DIGEST_CHARS
    return (
        text[:ARTICULATION_DIGEST_CHARS],
        truncated,
        tuple(artifact.interface.commitments),
    )


def frame_obligations(harness, subject_id: str) -> tuple[str, ...]:
    """The commitment ids a departure may name -- the subject's own."""
    artifact = harness.state.artifacts.get(subject_id)
    if artifact is None:
        return ()
    return tuple(artifact.interface.commitments)


def declared_departures(
    harness, subject_id: str
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """`((departing artifact id, broken commitment ids), ...)`, by artifact id.

    Recognition is the loose reading: the commitment is present and the body
    decodes. A declaration whose interface the compiler would not have emitted
    is a mis-registered artifact, and REFUSING to render it would hide the
    departure while leaving the conflict -- which is the state the protocol
    exists to abolish. `departure_declaration_wf` is what reports the
    mis-registration, on the record, where a reader can attack it.
    """
    found: dict[str, tuple[str, ...]] = {}
    for aid, artifact in harness.state.artifacts.items():
        if DEPARTURE_DECLARATION_COMMITMENT.id not in artifact.interface.commitments:
            continue
        try:
            body = decode(content_text(artifact, harness.blobs))
        except (ClaimDecodeError, UnicodeDecodeError, KeyError):
            continue
        if not isinstance(body, DepartureDeclarationV1):
            continue
        if body.subject_ref != subject_id:
            continue
        found[body.departing_ref] = tuple(body.broken_ids)
    return tuple(sorted(found.items()))


def held_frame_obligations(
    harness, subject_id: str, artifact_id: str
) -> tuple[str, ...]:
    """What `artifact_id` still implicitly holds of the frame: the subject's
    obligations minus what it declared it breaks with.

    THIS IS THE GATE, and it is the reason the departure protocol is not just
    a sentence in a prompt. Declaring subtracts an id deterministically, from
    the record; the hidden-premise criticism's target is whatever is left, and
    neither side of that subtraction depends on a model honouring an
    instruction. Q1's finding is that an instruction would not have held.
    """
    declared = dict(declared_departures(harness, subject_id)).get(artifact_id, ())
    return tuple(k for k in frame_obligations(harness, subject_id) if k not in declared)


def frame_slices(harness, problem_id: str) -> tuple[FrameSliceV1, ...]:
    """Every consulted frame whose sigma admits this problem, by assertion id.

    Built on `consulted` and `frames` UNCHANGED. Those two are the consult
    path `invariants.py` reads for the `standing-integrity` check, and a
    render that needed them widened would be a render reaching into a frozen
    surface for its own convenience.
    """
    slices = []
    for grant in consulted(harness):
        if not frames(harness, grant.subject_id, problem_id):
            continue
        head, truncated, commitments = articulation_digest(harness, grant.subject_id)
        attackers = subject_attackers(harness, grant.subject_id)
        slices.append(
            FrameSliceV1(
                assertion_id=grant.assertion_id,
                subject_id=grant.subject_id,
                promotion_problem=grant.problem_id,
                digest_head=head,
                digest_truncated=truncated,
                commitment_ids=commitments,
                attackers=attackers[:FRAME_SLICE_ATTACKERS_N],
                attackers_total=len(attackers),
                departure_protocol=grant.departure_protocol,
                declared_departures=declared_departures(harness, grant.subject_id),
            )
        )
    return tuple(sorted(slices, key=lambda s: s.assertion_id))


def _slice_lines(slice_: FrameSliceV1) -> list[str]:
    lines = [
        f"  subject {slice_.subject_id}",
        f"    {slice_.digest_head}"
        + (" […articulation compressed; expand with `deepreason standing --json`]"
           if slice_.digest_truncated else ""),
    ]
    if slice_.commitment_ids:
        lines.append(
            "    its commitments: " + ", ".join(slice_.commitment_ids)
        )
    if slice_.attackers:
        # The cap states itself. A count shown without its total is a silent
        # cap, and a pack that silently caps is a pack whose reader cannot
        # tell a quiet frame from a truncated one.
        shown = (
            f"{len(slice_.attackers)} of {slice_.attackers_total} shown, by id"
            if slice_.attackers_total > len(slice_.attackers)
            else f"all {slice_.attackers_total}"
        )
        lines.append(
            f"    STANDING ATTACKERS ({shown}) — this frame ships its own crisis; "
            "these are open indictments of the coordinate system itself, not of "
            "your candidate:"
        )
        for attacker, status, head in slice_.attackers:
            lines.append(f"      - {attacker} [{status}]: {head}")
    lines.append(
        "    DEPARTURES ARE PERMITTED. To break with this frame, declare which "
        "of its commitment ids you break with, as a list of ids. A declared "
        "departure carries no penalty anywhere — not in rank, not in "
        "admission, not in acceptance. An UNDECLARED conflict with the frame "
        "is criticisable as a silent assumption; a declared one is criticisable "
        "on its merits."
    )
    if slice_.departure_protocol:
        lines.append(f"    departure protocol: {slice_.departure_protocol}")
    if slice_.declared_departures:
        lines.append("    ALREADY DECLARED against this frame:")
        for departing, broken in slice_.declared_departures:
            lines.append(f"      - {departing} breaks {', '.join(broken)}")
    return lines


def render_frame_slice_context(harness, problem_id: str) -> str | None:
    """The model-facing frame slice for one problem, or None when nothing
    frames it.

    None rather than an empty string, and rather than a "no frame" notice:
    a pack section that announced the absence of a frame would be exactly the
    empty provenance-shaped slot `RESEARCH_JUDGE_BLINDING` measured as worse
    than a populated one.
    """
    slices = frame_slices(harness, problem_id)
    if not slices:
        return None
    lines = [
        "FRAME (consulted background for this problem; the coordinate system "
        "it is posed in, not a claim you are required to accept):"
    ]
    for slice_ in slices:
        lines += _slice_lines(slice_)
    return "\n".join(lines)


def exit_grade(status) -> str | None:
    """The grade a frame assertion left standing under, or None if it has not.

    A pure function of the label, which is what makes all three reachable and
    disjoint without a rule of their own: `final_labels` assigns exactly one
    of the four, so no assertion can be in two grades and none can be rounded
    into a neighbour by this function.
    """
    return EXIT_GRADES.get(status)


def frame_exits(harness) -> tuple[dict, ...]:
    """Every frame assertion addressed to a promotion problem that is not
    unrefuted, with its grade, by assertion id.

    Reports the grade an assertion is IN, not the sequence number it left `U`
    at. The Formalization defines an exit as a transition between consecutive
    prefixes; answering "which grade is this frame in now" needs only the
    label, and replaying every prefix on every render would buy a reader
    nothing they could act on. Recorded as a limit in the tranche's SPEC.
    """
    from deepreason.calculus.standing import (
        _promotion_problem_of,
        declared_frame_assertions,
    )

    exits = []
    for assertion_id, body in declared_frame_assertions(harness):
        problem_id = _promotion_problem_of(harness, assertion_id)
        if problem_id is None:
            continue
        status = harness.state.status.get(assertion_id)
        grade = exit_grade(status)
        if grade is None:
            continue
        exits.append(
            {
                "assertion": assertion_id,
                "subject": body.subject_ref,
                "promotion_problem": problem_id,
                "label": status.value,
                "grade": grade,
                "means": EXIT_GRADE_MEANINGS[grade],
            }
        )
    return tuple(sorted(exits, key=lambda e: e["assertion"]))
