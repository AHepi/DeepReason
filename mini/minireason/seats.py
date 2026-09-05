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

from deepreason.llm.packs import allocate_seat_brief, render_seat_brief
from deepreason.llm.seat_sections import (
    SeatPackLayoutEntryV1,
    SeatPackLayoutV1,
    SeatShellV1,
    register_seat_pack_layout,
    register_seat_shell,
    resolve_seat_shell,
)
from minireason.forms import MiniCommitmentProposals, MiniFormV1, select_mini_form
from minireason.records import record_mini_output
# Importing the sources module registers the mini section plugins the
# layouts below name; a layout is refused at registration if its plugins do
# not resolve, so the order of these two imports is load-bearing.
from minireason.sources import mini_section_request

CONJECTURER_SEAT = "mini.conjecturer"
CRITIC_SEAT = "mini.critic"
COMMITMENT_SEAT = "mini.commitment"
MINI_SEATS = (CONJECTURER_SEAT, CRITIC_SEAT, COMMITMENT_SEAT)

#: The kind the commitment seat writes. A registered id, so a flow can name
#: it as data (T5) and a reader can find it in any root.
COMMITMENT_PROPOSAL_KIND = "mini.commitment-proposal.v1"

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


# The three shells: a seat kind IS this pairing of a layout and a form. Mini's
# call layer builds its own directive around the form's schema, so the
# role-prompt template named here is the shipped one and is not read by mini.
def _shell(seat: str, layout_id: str, form_id: str) -> SeatShellV1:
    return SeatShellV1(
        shell_id=f"seat.{seat}.v0",
        seat_id=seat,
        layout_id=layout_id,
        form_id=form_id,
        role_prompt_template_id="role-prompt.legacy-v0",
    )


CONJECTURER_SHELL = _shell(CONJECTURER_SEAT, CONJECTURER_LAYOUT_ID, "mini.conjecturer.relaxed.v1")
CRITIC_SHELL = _shell(CRITIC_SEAT, CRITIC_LAYOUT_ID, "mini.critic.relaxed.v1")
COMMITMENT_SHELL = _shell(COMMITMENT_SEAT, COMMITMENT_LAYOUT_ID, "mini.commitment.relaxed.v1")
MINI_SHELLS = {
    CONJECTURER_SEAT: CONJECTURER_SHELL,
    CRITIC_SEAT: CRITIC_SHELL,
    COMMITMENT_SEAT: COMMITMENT_SHELL,
}

for _seat, _seat_shell in MINI_SHELLS.items():
    register_seat_shell(_seat_shell, default_for_seat=_seat)


def form_for_seat(
    seat_id: str, form_id: str | None = None, *, shell_id: str | None = None
) -> MiniFormV1:
    """The FORM a mini seat fills, resolved THROUGH its shell.

    `SeatShellV1.form_id` had no consumer anywhere before this (PARKED P3):
    the shell paired a layout with a form declaratively while every dispatch
    site still chose its form inline. Here the shell's `form_id` is the
    declared default, so binding another shell in a seat's place changes what
    the seat is asked for as well as what it is shown -- the two halves of
    "a seat is a shell". An explicit argument, then `DEEPREASON_MINI_FORM`,
    still win, as `select_mini_form` orders them.
    """

    shell = resolve_seat_shell(seat_id, shell_id)
    return select_mini_form(seat_id, form_id, default=shell.form_id)


def render_mini_brief(
    session,
    seat_id: str,
    problem_id: str,
    *,
    target_id: str | None = None,
    token_budget: int = 4096,
    shell_id: str | None = None,
    layout_id: str | None = None,
    supplied=None,
    receipts=None,
) -> str:
    """One seat's brief, from a live mini session, through the public road.

    Shell -> layout -> request -> walk -> allocation, and nothing else: no
    section is built here and no private name of `packs` is reached. Every
    mini layout entry is mandatory, so the budget bounds nothing the layout
    carries; what a seat is shown of a growing pool is the retention rule's
    decision, disclosed inside the section. `receipts`, when passed, receives
    the typed record of what actually rendered.
    """

    shell = resolve_seat_shell(seat_id, shell_id)
    layout = layout_id or shell.layout_id
    request = mini_section_request(
        session, problem_id, target_id=target_id, supplied=supplied
    )
    sections, receipts = render_seat_brief(seat_id, layout, request, receipts)
    return allocate_seat_brief(seat_id, token_budget, sections, receipts)


def record_commitment_proposals(session, proposals: MiniCommitmentProposals, *,
                                spend=None) -> list:
    """The commitment seat's ONE act: write what it proposed into the record.

    Each proposal's only requirement is that it names the conjecture it is
    about (S4, in the operator's words: "does not force a strict format").
    The body is free prose, unbounded, unranked. A proposal naming nothing in
    this run is dropped with a typed event, never written dangling. Nothing
    here registers a Commitment, touches a status, or admits, ranks, immunises
    or refutes anything: the proposal is RECORDED, and the road from a
    free-prose proposal to an evaluable commitment is not built (Q-A, E3 not
    built). `spend` lands exactly once, on the first event written.
    """

    events = []
    for proposal in proposals.proposals:
        event = record_mini_output(
            session,
            COMMITMENT_PROPOSAL_KIND,
            about=proposal.about,
            body=proposal.body,
            spend=spend if not events else None,
        )
        events.append(event)
    return events


__all__ = [
    "COMMITMENT_PROPOSAL_KIND",
    "COMMITMENT_SHELL",
    "CONJECTURER_SHELL",
    "CRITIC_SHELL",
    "MINI_SHELLS",
    "form_for_seat",
    "record_commitment_proposals",
    "render_mini_brief",
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
