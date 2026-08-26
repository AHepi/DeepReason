"""Reading the record for open criticisms, and rendering them.

Two functions and a record, and the interesting decisions are all in the
first one. `DR-CON-discharge-channel` carries the reasoning; the constraints
that the code cannot show are stated here.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

from deepreason.ontology.state import Status
from deepreason.programs import content_text

# A criticism's own quoted span, when it has one. Critics quote their target
# verbatim about three times in four (W2 §COMMITMENT ATTACKS: 72% and 76% of
# quoted spans are verbatim in the target), so this finds a span often enough
# to be worth showing and reports none rather than guessing when it does not.
_QUOTED = re.compile(r'"([^"]{12,})"')

_SCRUTINY = "scrutiny"


class OpenCriticism(BaseModel):
    """One criticism the writer has not yet answered.

    `handle` is the critic artifact's id. Stable by content addressing, unique
    by construction, re-derivable on replay, and needing no handle map -- which
    keeps the recorded key-sort trap (handle maps reload B1, B10, B2; compare
    by index, never by `.values()`) out of this channel entirely. A short
    ordinal would renumber whenever a lower-sorting criticism arrived, and the
    failure would be silent because both renders look equally well-formed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    handle: str
    claim: str
    span: str | None
    target: str


def _addressed(state, problem_id: str) -> set[str]:
    return {aid for aid, pid in state.addr if pid == problem_id}


def _scrutiny_pairs(harness) -> list[tuple[str, str]]:
    """(target, critic) for every `observe_only` criticism on the record.

    THIS IS THE HALF THAT MATTERS. `observe_only` is the authority mode that
    cannot mint a warrant, so these criticisms produce no attack edge at all --
    a reader that consulted `state.att` alone would see none of them. W2
    measured that exact population as the one never routed anywhere: 0 of 196
    LLM attacks exposed to a later conjecture dispatch. Dropping this function
    would leave the channel carrying only the criticism that was already
    acting, which is the defect rather than the fix.
    """
    pairs = []
    for event in harness.log.read():
        inputs = list(event.inputs)
        if len(inputs) >= 3 and inputs[0] == _SCRUTINY:
            pairs.append((inputs[1], inputs[2]))
    return pairs


def discharged_handles(harness, problem_id: str) -> frozenset[str]:
    """Every handle some candidate has discharged on this problem.

    Read from the discharge Measures rather than from any in-memory bookkeeping:
    the record is the only admissible evidence, and a channel whose persistence
    depended on process state would forget across a resume.
    """
    handles = set()
    for event in harness.log.read():
        inputs = list(event.inputs)
        if len(inputs) >= 4 and inputs[0].startswith("discharge:") and inputs[3] == problem_id:
            handles.add(inputs[1])
    return frozenset(handles)


def open_criticisms(harness, problem_id: str, policy) -> tuple[OpenCriticism, ...]:
    """Every criticism on this problem the writer has not answered, capped.

    The public reading. `_open_with_total` is the same walk plus the uncapped
    count, which only the renderer needs -- it has to say "N of M shown" where
    the cap bites, and a caller that got the total back would be tempted to
    treat it as a rate. There is no rate here: a count of open criticisms is
    exactly the kind of number that would cross the law line the moment
    anything ranked on it.
    """
    return _open_with_total(harness, problem_id, policy)[0]


def _open_with_total(harness, problem_id: str, policy) -> tuple[tuple[OpenCriticism, ...], int]:
    """The walk, and how many there were before the cap.

    BOTH channels, and the order is not negotiable: scrutiny Measures AND
    attack edges. A criticism leaves the population when it is discharged, or
    when the criticism artifact is itself REFUTED -- a defeated attack was made
    and lost, so rendering it under a cap would displace a live one and the
    list would understate itself in the case where it matters most.

    Capped at `policy.handles_n` in a stable order, so what the writer sees is
    the same across renders and across replay.
    """
    if not policy.enabled or not policy.handles_n:
        return (), 0
    state = harness.state
    addressed = _addressed(state, problem_id)
    spent = discharged_handles(harness, problem_id)

    # Both channels into one map, scrutiny first. Which channel a criticism
    # arrived through is deliberately NOT carried forward: the writer answers
    # the criticism, and a field naming its provenance would be a number-shaped
    # invitation to treat the two as differently weighty.
    found: dict[str, str] = {}
    for target, critic in _scrutiny_pairs(harness):
        if target in addressed:
            found.setdefault(critic, target)
    for attacker, target in state.att:
        if target in addressed:
            found.setdefault(attacker, target)

    rows = []
    for handle in sorted(found):
        if handle in spent or handle not in state.artifacts:
            continue
        if state.status.get(handle) is Status.REFUTED:
            continue
        text = content_text(state.artifacts[handle], harness.blobs)
        quoted = _QUOTED.search(text)
        rows.append(
            OpenCriticism(
                handle=handle,
                claim=text[: policy.claim_head_chars].replace("\n", " ").strip(),
                span=quoted.group(1)[: policy.span_head_chars] if quoted else None,
                target=found[handle],
            )
        )
    return tuple(rows[: policy.handles_n]), len(rows)


def render_open_criticism_context(harness, problem_id: str, policy) -> str | None:
    """The open criticisms, or None when there are none.

    None rather than an empty string, and rather than a "no open criticisms"
    notice: a section announcing the absence would be the empty
    provenance-shaped slot `RESEARCH_JUDGE_BLINDING` measured as worse than a
    populated one, and the same rule Rung 6's frame slice already obeys.

    Rendered EXACT -- the caller makes the section non-droppable and
    non-compressible -- which is affordable only because every dimension is
    capped by the policy: how many handles, and how much of each claim and each
    span. Where a cap bites it is STATED IN BAND, because a model cannot
    inspect a Python object and an undisclosed cap reads as completeness.
    """
    shown, total = _open_with_total(harness, problem_id, policy)
    if not shown:
        return None
    header = "OPEN CRITICISMS ON THIS PROBLEM"
    if total > len(shown):
        header += f" ({len(shown)} of {total} shown, by handle)"
    lines = [
        header
        + " -- these are part of what your candidate must answer, not advice.",
        "Every candidate you submit must DISCHARGE each handle below, one of:",
    ]
    from deepreason.discharge.policy import declaration

    for kind in policy.kind_names():
        lines.append(f"  - {declaration(kind).directive_line}")
    for criticism in shown:
        lines.append(f"  [{criticism.handle}] against {criticism.target}")
        lines.append(f"      CLAIM: {criticism.claim}")
        lines.append(
            f"      CITED SPAN: {criticism.span}"
            if criticism.span
            else "      CITED SPAN: (none quoted)"
        )
    return "\n".join(lines)
