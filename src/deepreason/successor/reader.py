"""The PRODUCTION DISPATCH SITE: a reader outside `rules/` that walks what
criticism already recorded and routes the questions it finds.

Q3, answered ROAD B (2026-08-30). `DR-SEAM-rules-x-scratch` rule 6 says "Never
widen the criticism side to close the asymmetry. The asymmetry is the design.
Overturning it is an operator's call, not an implementer's." The operator's P9
law of 2026-08-29 IS that call, but it does not say which half survives — so
this road keeps the asymmetry EXACTLY as written. Criticism writes only its own
record; something that is not criticism does the routing.
`src/deepreason/rules/crit.py` takes a ZERO-LINE DIFF, and that is asserted by
`tests/test_successor_dispatch.py`, not claimed here.

The shape is `DR-CON-discharge-channel`'s: that channel is a reader of what
`_observe_case` already records, and so is this one.

WHAT THE RECORD ACTUALLY CARRIES, and the two consequences it forces
-------------------------------------------------------------------
The question is a WIRE field, so the model's own JSON survives as the raw
completion blob (`LLMCall.raw_ref`) whatever else happens. What the raw does
NOT carry is a resolved target: the batch contract addresses targets by
`target_alias` (`SRC_001`, `SRC_002`, ...) and the `AliasTable` that maps them
is call-local, built at dispatch and never recorded. So:

1. **The PROBLEM is resolvable and is what routing needs.** `route` takes a
   problem id, not a target: the law says "linked to the problem it was
   proposed under". Every artifact one criticism call attacks is drawn from one
   problem's candidate set, so ANY target of that call resolves the same
   problem through `state.addr` — no alias needed. This road is therefore
   fully live.
2. **The TARGET is resolvable only when the call criticised exactly one.**
   Minting needs one (`from: [problem, target]`), so a multi-target call whose
   aliases cannot be re-resolved records a typed UNRESOLVED disposition and
   mints nothing. It never guesses, and it never falls silent. Minting is off
   by default, so this bounds a road a run has to switch on.

IDEMPOTENCE IS BY THE RECORD, never by module state. A dispatch receipt names
the call event's seq, so a resumed run re-reads the same log and skips what it
already dispatched. A flag on this module would forget across a resume and
double-route every question in the first half of the run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from deepreason.ontology.event import Rule

# The dispatch family's receipt. Declared once in `signals.py`, never restated
# at an emit site.
DISPATCH_RECEIPT_PREFIX = "successor-dispatch:"

# Written once per criticism call whose proposals have ALL been disposed of.
# It is what lets a later walk skip that call without opening its raw blob
# again: this reader fires every cycle, and re-reading every historical
# completion each time is quadratic I/O over a run. A call that failed
# part-way through gets NO receipt and is retried on the next walk, which is
# the behaviour a partial failure should have.
CALL_FINISHED_RECEIPT = "successor-dispatch-call-done"

# The wire role whose completions may carry the field. Both criticism contracts
# — the compact/atomic single critic and the batch — dispatch under it.
_CRITIC_ROLE = "argumentative_critic"

_SCRUTINY = "scrutiny"


@dataclass(frozen=True)
class RecordedProposal:
    """One successor question the criticism record carries.

    `target_id` is None when the call criticised more than one artifact and the
    call-local alias table is gone — see the module docstring. `problem_id` is
    None only when no target of the call addresses any problem, which is the
    law's own precondition failing rather than a defect here.
    """

    call_seq: int
    index: int
    question: str
    problem_id: str | None
    target_id: str | None


def _questions_in(raw: bytes) -> list[str]:
    """Every filled `successor_question` in one raw completion, in wire order.

    Both contract shapes, and nothing else: a payload that is not JSON, or that
    is JSON of some other shape, yields nothing rather than raising. A reader
    of the record must never be the reason a run stops.
    """
    try:
        payload = json.loads(raw)
    except (ValueError, TypeError):
        return []
    if not isinstance(payload, dict):
        return []
    found: list[str] = []
    cases = payload.get("cases")
    if isinstance(cases, list):
        for case in cases:
            if isinstance(case, dict):
                text = case.get("successor_question")
                if isinstance(text, str) and text.strip():
                    found.append(text.strip())
        return found
    text = payload.get("successor_question")
    if isinstance(text, str) and text.strip():
        found.append(text.strip())
    return found


@dataclass(frozen=True)
class _RecordIndex:
    """Everything this reader needs from the log, built in ONE pass.

    Three separate walks was the first shape and it was wrong for a reason
    that only shows up in a long run: this reader fires after EVERY criticism
    pass, so a per-cycle walk of a growing log is quadratic in the number of
    cycles. One pass, and the calls already disposed of are known before any
    blob is opened.
    """

    scrutiny_by_source: dict[int, set[str]]
    critic_to_targets: dict[str, set[str]]
    dispatched_keys: set[str]
    finished_calls: set[int]


def _index(harness) -> _RecordIndex:
    scrutiny_by_source: dict[int, set[str]] = {}
    critic_to_targets: dict[str, set[str]] = {}
    dispatched_keys: set[str] = set()
    finished_calls: set[int] = set()
    for event in harness.log.read():
        inputs = list(event.inputs)
        if not inputs:
            continue
        if inputs[0] == _SCRUTINY and len(inputs) >= 3:
            # (critic artifact) -> every artifact it criticised. A SET, not a
            # single id: one critic artifact can carry scrutiny of several
            # targets, and collapsing that to the first would turn an
            # unresolvable link into a confident WRONG one, which is the
            # failure this channel must not have.
            critic_to_targets.setdefault(inputs[2], set()).add(inputs[1])
            # The `source:<seq>` suffix `_observe_case` appends when its caller
            # passes one. Present on the transactional batch path and absent
            # otherwise, which is why it is one input among several rather than
            # the resolution.
            if len(inputs) >= 4 and inputs[3].startswith("source:"):
                try:
                    seq = int(inputs[3].split(":", 1)[1])
                except ValueError:
                    continue
                scrutiny_by_source.setdefault(seq, set()).add(inputs[1])
        elif inputs[0] == CALL_FINISHED_RECEIPT and len(inputs) >= 2:
            try:
                finished_calls.add(int(inputs[1]))
            except ValueError:
                continue
        elif inputs[0].startswith(DISPATCH_RECEIPT_PREFIX) and len(inputs) >= 2:
            dispatched_keys.add(inputs[1])
    # The warrant channel, for the reason `discharge.channel` reads both: an
    # `observe_only` criticism mints no warrant and leaves only a scrutiny
    # Measure, so a reader consulting warrants alone would miss the population
    # that was never routed anywhere -- and one consulting only scrutiny would
    # miss every criticism that actually attacked.
    for artifact_id, artifact in harness.state.artifacts.items():
        for warrant_id in artifact.warrants:
            warrant = harness.warrants.get(warrant_id)
            if warrant is not None and getattr(warrant, "target", None):
                critic_to_targets.setdefault(artifact_id, set()).add(warrant.target)
    return _RecordIndex(
        scrutiny_by_source=scrutiny_by_source,
        critic_to_targets=critic_to_targets,
        dispatched_keys=dispatched_keys,
        finished_calls=finished_calls,
    )


def _first_problem(harness, target_id: str) -> str | None:
    """The first problem this target addresses, in `addr` registration order.

    A3's reading of "the problem it was proposed under", and the same
    expression `views/evidence.py` uses. `addr` is rebuilt identically on
    replay, so first-in-order is deterministic rather than incidental.
    """
    for aid, pid in harness.state.addr:
        if aid == target_id:
            return pid
    return None


def _targets_of_call(harness, event, scrutiny_by_source, critic_to_targets) -> set[str]:
    targets = set(scrutiny_by_source.get(event.seq, ()))
    for object_id in event.outputs:
        targets |= critic_to_targets.get(object_id, set())
    return targets


def recorded_proposals(harness) -> tuple[RecordedProposal, ...]:
    """Every successor question on the record, with what could be resolved.

    Read-only over the log, the state and the blob store. Calling it twice
    returns the same tuple; it writes nothing. This is the COMPLETE reading and
    opens every criticism blob, which is what a caller asking "what is on the
    record" wants; `dispatch_recorded_proposals` uses the cheaper incremental
    form below.
    """
    return _proposals(harness, _index(harness), skip_finished=False)


def _proposals(harness, index, *, skip_finished: bool) -> tuple[RecordedProposal, ...]:
    proposals: list[RecordedProposal] = []
    for event in harness.log.read():
        call = event.llm
        if event.rule != Rule.CRIT or call is None or call.role != _CRITIC_ROLE:
            continue
        if not call.raw_ref:
            continue
        if skip_finished and event.seq in index.finished_calls:
            # Disposed of on an earlier walk. Skipping it BEFORE the blob read
            # is the whole point: the check below is what keeps a per-cycle
            # dispatch from re-opening every historical completion.
            continue
        try:
            raw = harness.blobs.get(call.raw_ref)
        except (KeyError, FileNotFoundError, ValueError):
            # A sealed or pruned blob is a fact about the record, not an error
            # to raise at a reader: the questions in it are simply not readable.
            continue
        questions = _questions_in(raw)
        if not questions:
            continue
        targets = _targets_of_call(
            harness, event, index.scrutiny_by_source, index.critic_to_targets
        )
        # One resolvable target is enough for the PROBLEM, because a criticism
        # call's targets are drawn from one problem's candidate set; it is not
        # enough for the TARGET unless it is the only one.
        problem_id = next(
            (p for p in (_first_problem(harness, t) for t in sorted(targets)) if p),
            None,
        )
        target_id = next(iter(targets)) if len(targets) == 1 else None
        for position, question in enumerate(questions):
            proposals.append(
                RecordedProposal(
                    call_seq=event.seq,
                    index=position,
                    question=question,
                    problem_id=problem_id,
                    target_id=target_id,
                )
            )
    return tuple(proposals)


def dispatch_recorded_proposals(harness, config) -> int:
    """Route every successor question the record carries and has not routed.

    The one production caller of `route` and `mint`. Returns how many proposals
    were dispatched by THIS call, which is zero on a second call over an
    unchanged record.

    Never raises on the channel's own account: a destination that cannot accept
    a question discloses through `route`, and an unresolvable link discloses
    here. A run does not fail because an advisory question could not be filed.
    """
    from deepreason.successor.mint import mint
    from deepreason.successor.route import route

    index = _index(harness)
    already = set(index.dispatched_keys)
    dispatched = 0
    finished: set[int] = set()
    for proposal in _proposals(harness, index, skip_finished=True):
        finished.add(proposal.call_seq)
        key = f"{proposal.call_seq}:{proposal.index}"
        if key in already:
            continue
        if proposal.problem_id is None:
            # The law's own condition -- "linked to the problem it was proposed
            # under" -- cannot be met. Recorded, so silence never has to be
            # read as "nothing was proposed".
            harness.record_measure(
                inputs=[f"{DISPATCH_RECEIPT_PREFIX}UNLINKED", key]
            )
            already.add(key)
            continue
        route(
            harness,
            config,
            problem_id=proposal.problem_id,
            question=proposal.question,
        )
        if proposal.target_id is not None:
            mint(
                harness,
                config,
                problem_id=proposal.problem_id,
                target_id=proposal.target_id,
                question=proposal.question,
            )
            harness.record_measure(
                inputs=[f"{DISPATCH_RECEIPT_PREFIX}ROUTED", key, proposal.problem_id]
            )
        else:
            # Routed, but the call criticised several artifacts and the
            # call-local alias table is not on the record, so the minting road
            # has no `from: [problem, target]` to build. Disclosed rather than
            # guessed; minting is off by default, so this bounds a road a run
            # must switch on.
            harness.record_measure(
                inputs=[
                    f"{DISPATCH_RECEIPT_PREFIX}ROUTED_TARGET_UNRESOLVED",
                    key,
                    proposal.problem_id,
                ]
            )
        already.add(key)
        dispatched += 1
    for call_seq in sorted(finished):
        # Written only after every proposal of that call came through the loop
        # without raising. A call that failed part-way gets no receipt and is
        # retried on the next walk.
        harness.record_measure(inputs=[CALL_FINISHED_RECEIPT, str(call_seq)])
    return dispatched
