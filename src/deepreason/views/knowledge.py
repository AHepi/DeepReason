"""Def 8.1's `knowledge(a)` as a VIEW (Prop 12.6, D-4 answered A).

    knowledge(a)  <=>  unrefuted  and  active  and  reach > 0

A view steers attention and never adjudicates. Nothing here writes, nothing
here is stored, and no label anywhere is computed from it -- which is what makes
saying the word safe at all.

**The word is never printed bare.** D-4's recommendation attached that
discipline to the decision to build this at all, and the reason is a recorded
precedent rather than caution in the abstract: readers of `positions.accepted`
were treating acceptance as ADJUDICATED, and v1.7 §E had to add the
`adjudication-blindness` check after the fact. The same misreading is available
here and costlier -- "knowledge" carries more weight than "accepted" -- so the
definition travels with every row, and the row and its label are produced by one
function so a caller cannot print one without the other.

`active` is read as §12.2's `demarcated` (`crit and load`), which SUPERSEDES §6's
`active = crit and mod` (R54, operator 2026-08-15). Only the `crit` half is
computable without a seat, so every row says WHICH half it rests on rather than
implying both: `declared-only` means the attack surface is nonempty and nothing
has taken the load reading. A reader who wants the stronger claim can see that
they do not have it.
"""

from __future__ import annotations

from deepreason.measures.demarcation import crit
from deepreason.ontology.state import Status

# The label, and the reason it is a constant: a caller that wanted to print
# "knowledge" alone would have to write the bare word itself, in a diff a
# reviewer can see, rather than by dropping an argument.
KNOWLEDGE_LABEL = "knowledge (unrefuted ∧ active ∧ reach > 0)"


def knowledge_view(harness) -> dict:
    """Every artifact the calculus characterizes as knowledge, with the
    definition inline. Recomputed from replayed state on every call.

    Sorted by artifact id so two renders of one root agree byte for byte, which
    is the same discipline `standing_view` keeps and for the same reason.
    """
    rows = []
    for aid in sorted(harness.state.artifacts):
        reach = harness.state.reach.get(aid, 0.0)
        if reach <= 0:
            continue
        if harness.state.status.get(aid) is not Status.ACCEPTED:
            continue
        artifact = harness.state.artifacts[aid]
        if not crit(artifact, harness.commitments):
            # `crit` false settles `demarcated` on its own: an interface that
            # declares nothing forbids nothing, so no sample could rescue it.
            continue
        rows.append(
            {
                "artifact": aid,
                "label": KNOWLEDGE_LABEL,
                "reach": reach,
                # Which half of §12.2 this row actually rests on. Never
                # omitted: a row claiming the full reading it has not taken
                # would be the misreading this module exists to prevent.
                "active_reading": "declared-only",
                "commitments": sorted(artifact.interface.commitments),
            }
        )
    return {"view": "knowledge.v1", "label": KNOWLEDGE_LABEL, "rows": rows}


def render_knowledge(harness) -> list[str]:
    """The view as lines, for a reader. Empty list when nothing qualifies --
    the caller decides how to say "nothing", because "no knowledge" is a
    sentence this module should not put in anyone's mouth."""
    view = knowledge_view(harness)
    if not view["rows"]:
        return []
    lines = [f"{view['label']}:"]
    for row in view["rows"]:
        lines.append(
            f"    {row['artifact']}  reach {row['reach']:.0f}  "
            f"active: {row['active_reading']}"
        )
    return lines
