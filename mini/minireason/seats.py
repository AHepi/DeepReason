"""Mini's three seats as shells -- who sees what, and which form each fills.

Implements S5 and S6 (R5, R6, R7, C7, C8) of the mini isolation programme.

A seat is a shell: its input (the brief, a registered LAYOUT) and its output
(the FORM it is asked to fill) define it, and both are configuration
(CLAUDE.md, 2026-09-03). Three layouts and three shells ship here, one per
seat, and every one of them renders through the ONE public road the full
harness's seats share (`deepreason.llm.packs.render_seat_brief`). Nothing in
this module builds a section or names a status.

WHO SEES WHAT, and why the critic's layout is SHORT. R5 is the operator's
"critics see the conjecture artifact, not the proposed commitments"; R6 is
"conjecturers see everything generated so far and so do commitment
artifacts". The blinding is STRUCTURAL, not a filter: the critic layout
REGISTERS NO section that could carry a commitment proposal, so there is no
slot to fill, blank or otherwise. That is the same shape the record already
required of provenance blinding (the amended judge law, 2026-08-28: renderers
OMIT the field entirely, because a present-but-blank slot draws more
attention than a filled one). `mini/tests/test_mini_exposure.py` is the byte
assertion.

Every entry here is MANDATORY -- neither droppable nor compressible -- so the
allocator retains each section in full and can cut nothing silently. What a
seat is shown of a growing pool is the retention rule's decision, declared on
the `mini.everything-so-far` entry and disclosed inside the section
(`minireason.sources`).
"""

from __future__ import annotations

from deepreason.llm.seat_sections import (
    SeatPackLayoutEntryV1,
    SeatPackLayoutV1,
    register_seat_pack_layout,
)
# Importing the sources module registers the mini section plugins the
# layouts below name; a layout is refused at registration if its plugins do
# not resolve, so the order of these two imports is load-bearing.
from minireason import sources as _sources  # noqa: F401

CONJECTURER_SEAT = "mini.conjecturer"
CRITIC_SEAT = "mini.critic"
COMMITMENT_SEAT = "mini.commitment"
MINI_SEATS = (CONJECTURER_SEAT, CRITIC_SEAT, COMMITMENT_SEAT)

CONJECTURER_LAYOUT_ID = "seat-pack.mini.conjecturer.v0"
CRITIC_LAYOUT_ID = "seat-pack.mini.critic.v0"
COMMITMENT_LAYOUT_ID = "seat-pack.mini.commitment.v0"

# The directive is DATA in the layout entry, so a file-declared layout can
# reword a seat with no code. None of the three names a status, a rank or a
# verdict: within mini a criticism overturns nothing (operator, 2026-09-05),
# and the wording says so to the seat that writes one.
CONJECTURER_DIRECTIVE = (
    "You are the conjecture seat. Propose bold, criticizable explanations for "
    "the PROBLEM above, in whatever shape says the interesting part best -- "
    "prose is welcome and no skeleton is required. Return {vs_k} diverse "
    "candidates, each with a typicality estimate in [0,1]. Do not repeat what "
    "has already been generated; differ from it substantively."
)
CRITIC_DIRECTIVE = (
    "You are the critic seat. Mount the strongest specific objections to the "
    "TARGET CONJECTURE above. Each objection names what it is about and states "
    "its case in free prose. You decide nothing: an objection is recorded and "
    "shown, and it overturns nothing."
)
COMMITMENT_DIRECTIVE = (
    "You are the commitment seat. Read the TARGET CONJECTURE and propose the "
    "commitments it should be held to: what would refute it, what it must not "
    "do, what it forbids. Free prose; the only requirement is that each "
    "proposal names the conjecture it is about. A proposal is recorded, never "
    "enforced."
)

# 98 is the highest priority a layout entry may claim; the directive sorts
# last so nothing load-bearing follows the instruction.
_DIRECTIVE_PRIORITY = 98


def _entry(plugin_id: str, priority: int, **params) -> SeatPackLayoutEntryV1:
    return SeatPackLayoutEntryV1(plugin_id=plugin_id, priority=priority, params=params)


CONJECTURER_LAYOUT = SeatPackLayoutV1(
    layout_id=CONJECTURER_LAYOUT_ID,
    entries=(
        _entry("mini.problem", 1),
        _entry("mini.everything-so-far", 2),
        _entry("mini.directive", _DIRECTIVE_PRIORITY, text=CONJECTURER_DIRECTIVE),
    ),
)

# No `mini.everything-so-far` here, and no other section that could carry a
# proposal: the omission IS the blinding (R5).
CRITIC_LAYOUT = SeatPackLayoutV1(
    layout_id=CRITIC_LAYOUT_ID,
    entries=(
        _entry("mini.problem", 1),
        _entry("mini.target-conjecture", 2),
        _entry("mini.directive", _DIRECTIVE_PRIORITY, text=CRITIC_DIRECTIVE),
    ),
)

COMMITMENT_LAYOUT = SeatPackLayoutV1(
    layout_id=COMMITMENT_LAYOUT_ID,
    entries=(
        _entry("mini.problem", 1),
        _entry("mini.everything-so-far", 2),
        _entry("mini.target-conjecture", 3),
        _entry("mini.directive", _DIRECTIVE_PRIORITY, text=COMMITMENT_DIRECTIVE),
    ),
)

MINI_LAYOUTS = {
    CONJECTURER_SEAT: CONJECTURER_LAYOUT,
    CRITIC_SEAT: CRITIC_LAYOUT,
    COMMITMENT_SEAT: COMMITMENT_LAYOUT,
}

for _seat, _layout in MINI_LAYOUTS.items():
    register_seat_pack_layout(_layout, default_for_seat=_seat)


__all__ = [
    "COMMITMENT_LAYOUT",
    "COMMITMENT_LAYOUT_ID",
    "COMMITMENT_SEAT",
    "CONJECTURER_LAYOUT",
    "CONJECTURER_LAYOUT_ID",
    "CONJECTURER_SEAT",
    "CRITIC_LAYOUT",
    "CRITIC_LAYOUT_ID",
    "CRITIC_SEAT",
    "MINI_LAYOUTS",
    "MINI_SEATS",
]
