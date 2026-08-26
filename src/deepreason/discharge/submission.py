"""The submission boundary: screen a turn, record what it discharged.

Two functions, and the shape of both is fixed by one line of the operator's
request: a submission with undischarged handles "is returned ONCE with the open
list (a typed re-ask, not a repair grant), then accepted WITH a typed
undischarged disclosure -- disclose, never die".

So there is NO verdict that refuses. The screen decides between asking again
and accepting-with-a-record, and nothing else. A gate here would be the
all-configurations law broken at exactly the boundary it names.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from deepreason.ontology.artifact import Interface, Provenance, Ref, RefRole
from deepreason.discharge.channel import open_criticisms
from deepreason.discharge.policy import declaration

# A rebuttal enters the graph as an ordinary artifact. Its refs are MENTIONS,
# and that is the whole guarantee that a discharge cannot move a label:
# `build_att` lifts attackers through EVIDENCE refs, never through mentions, so
# there is no edge for one to travel. `calculus/operations.py::
# file_departure_declaration` earned the same guarantee the same way.
_REBUTTAL_ROLE = "critic"


class SubmissionScreening(BaseModel):
    """What the screen decided, and what the caller must record.

    `verdict` is `"reask"` or `"accept"`. There is deliberately no third value:
    the vocabulary itself is the promise that no candidate is refused.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    verdict: str
    open_handles: tuple[str, ...] = ()
    undischarged: tuple[str, ...] = ()


def _answers(discharge, legal: frozenset[str]):
    """The declaration this discharge satisfies, or None.

    "Satisfies" is doing work, and ONE definition of it serves both the screen
    and the recorder -- two copies of this rule would be two chances for the
    thing a run discloses and the thing it records to disagree.

    A discharge counts only when it names a handle the pack listed AND carries
    the content its kind declares it requires. The two conditions close the
    same hole from opposite sides: without the first the channel is satisfiable
    by inventing a string, and without the second by a bare label -- the
    acknowledgment shape Q5 measured as actively harmful. An undeclared kind
    raises rather than returning None: the registry is the authority on what a
    kind IS, and silently ignoring an unknown one would hide a wire/registry
    drift the model is already acting on.
    """
    kind = declaration(discharge.kind)
    if discharge.handle not in legal:
        return None
    if any(not (getattr(discharge, field, None) or "").strip() for field in kind.requires):
        return None
    return kind


def screen_submission(harness, problem_id: str, output, policy, *, reask_index: int = 0):
    """Decide whether this submission is re-asked once, or accepted as it is.

    Never a refusal, and never a repair grant: a re-ask re-dispatches the same
    turn with the open list rendered, consuming no repair budget and touching
    no repair contract. The distinction matters because repair exists to fix a
    reply the SCHEMA rejected, and this reply is schema-valid -- treating the
    two alike would spend a budget meant for transport faults on an epistemic
    one.
    """
    open_now = open_criticisms(harness, problem_id, policy)
    if not open_now:
        return SubmissionScreening(verdict="accept")
    legal = frozenset(criticism.handle for criticism in open_now)

    answered = {
        discharge.handle
        for candidate in getattr(output, "candidates", ()) or ()
        for discharge in getattr(candidate, "discharges", ()) or ()
        if _answers(discharge, legal) is not None
    }
    outstanding = tuple(sorted(legal - answered))

    if outstanding and policy.reask == "once" and reask_index == 0:
        return SubmissionScreening(
            verdict="reask",
            open_handles=outstanding,
        )
    return SubmissionScreening(
        verdict="accept",
        open_handles=tuple(sorted(legal)),
        undischarged=outstanding if policy.disclose_undischarged else (),
    )


def record_discharges(harness, problem_id: str, candidate_ref: str, discharges, policy):
    """Persist what a candidate discharged, and return any artifacts registered.

    One Measure per discharge -- attention/diagnostic, never a status, the same
    vehicle gate decisions and evidence-citation checks already use. Reading
    the record back is what makes persistence survive a resume; in-memory
    bookkeeping would forget.

    A REBUTTED discharge ALSO registers its note as an ordinary artifact, which
    is R6 in full: "a REBUTTED discharge is just a criticism artifact entering
    the ordinary graph". Nothing protects it, so a critic attacks it exactly as
    they would attack anything else. No check runs here on whether the rebuttal
    is EARNED -- refusing one would make this path a judge of the criticism it
    answers, and a rebuttal a critic disputes is a criticism they mount, not an
    authoring error (`file_departure_declaration` declines the same
    temptation for the same reason).
    """
    open_now = open_criticisms(harness, problem_id, policy)
    legal = frozenset(criticism.handle for criticism in open_now)
    registered = []
    for discharge in discharges or ():
        kind = _answers(discharge, legal)
        if kind is None:
            continue
        harness.record_measure(
            inputs=[f"discharge:{kind.name}", discharge.handle, candidate_ref, problem_id]
        )
        if not kind.attackable:
            continue
        artifact = harness.create_artifact(
            discharge.note,
            problem_id=problem_id,
            provenance=Provenance(role=_REBUTTAL_ROLE),
            interface=Interface(
                refs=[
                    Ref(target=discharge.handle, role=RefRole.MENTION),
                    Ref(target=candidate_ref, role=RefRole.MENTION),
                ]
            ),
        )
        registered.append(artifact.id)
    return tuple(registered)
