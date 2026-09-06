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

from typing import Protocol, runtime_checkable

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
from minireason.sources import ARTIFACT_KINDS_BY_ROLE, mini_section_request

CONJECTURER_SEAT = "mini.conjecturer"
CRITIC_SEAT = "mini.critic"
COMMITMENT_SEAT = "mini.commitment"
MINI_SEATS = (CONJECTURER_SEAT, CRITIC_SEAT, COMMITMENT_SEAT)

#: The kinds a mini seat can produce, as ids a flow names as data. The
#: conjecture's is the label the source layer already gives a conjecturer's
#: artifact; the other two are RECORD kinds (`minireason.records`).
CONJECTURE_KIND = ARTIFACT_KINDS_BY_ROLE["conjecturer"]
CRITICISM_KIND = "mini.criticism.v1"
COMMITMENT_PROPOSAL_KIND = "mini.commitment-proposal.v1"

CONJECTURER_LEGACY_LAYOUT_ID = "seat-pack.mini.conjecturer.legacy-v0"
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

# Today's conjecturer prompt as ONE section, so the legacy flow renders
# through the same road. It is bound by the legacy SHELL, never as a seat's
# default: the default layout for `mini.conjecturer` is the relaxed one, and
# the legacy flow names its shell explicitly.
CONJECTURER_LEGACY_LAYOUT = SeatPackLayoutV1(
    layout_id=CONJECTURER_LEGACY_LAYOUT_ID,
    entries=(_entry("mini.legacy.prompt", 1),),
)
register_seat_pack_layout(CONJECTURER_LEGACY_LAYOUT)

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
# The legacy pairing: today's prompt and the STORED form (R-stored). Registered
# beside the relaxed shell, never as the seat's default.
CONJECTURER_LEGACY_SHELL = SeatShellV1(
    shell_id="seat.mini.conjecturer.legacy-v0",
    seat_id=CONJECTURER_SEAT,
    layout_id=CONJECTURER_LEGACY_LAYOUT_ID,
    form_id="mini.conjecturer.legacy-v0",
    role_prompt_template_id="role-prompt.legacy-v0",
)
register_seat_shell(CONJECTURER_LEGACY_SHELL)
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


# The one section whose size the retention rule decides; every other mini
# section is mandatory and reserved first. The floor keeps the notice and the
# newest entry renderable even when the mandatory sections leave almost nothing.
FREE_SECTION_ID = "everything-so-far"
FREE_SECTION_FLOOR_CHARS = 400


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
    brief = allocate_seat_brief(seat_id, token_budget, sections, receipts)
    limit = (supplied or {}).get("brief_limit_chars")
    if limit is None or len(brief) <= int(limit):
        return brief
    # MANDATORY SECTIONS ARE RESERVED; the free section gets the remainder.
    # Every mini layout entry is mandatory, so the allocator cuts nothing and
    # an overrun would reach the call layer's tail clip -- which is where the
    # directive sits. The D8 live root lost 9 of 19 directives that way. So:
    # measure what the other sections took, hand the everything section what
    # is left, and render once more. If no such section is in this layout
    # the overrun is a mandatory one and is left for the loop to disclose.
    free = next((sec for sec in sections if sec.id == FREE_SECTION_ID), None)
    if free is None:
        return brief
    free_text = free.text_ref[len("inline:"):] if free.text_ref.startswith("inline:") else ""
    remainder = int(limit) - (len(brief) - len(free_text))
    share = (supplied or {}).get("brief_budget_chars")
    budget = max(FREE_SECTION_FLOOR_CHARS, min(remainder, share) if share is not None else remainder)
    resupplied = dict(supplied or {})
    resupplied["brief_budget_chars"] = budget
    request = mini_section_request(
        session, problem_id, target_id=target_id, supplied=resupplied
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


# ---------------------------------------------------------------------------
# The controller hook: DECLARED, never implemented, called by nothing.
#
# R7 asks that what each seat is shown be "calibrated on the fly and
# modifiable by the controller"; R8 says "Don't change the controller just
# yet, the controller steps in only when I can see how best to manage input
# output flows in mini properly." So this is the seam and nothing behind it:
# an interface a future controller can implement, a registry it is selected
# from by id, and ONE registered implementation that returns None. The window
# ruling of 2026-09-05 binds the other half: the hook has ZERO callers, and
# `mini/tests/test_mini_calibration_hook.py` asserts that on the AST. A promise
# is not a mechanism; the test is.
# ---------------------------------------------------------------------------


class MiniSeatError(ValueError):
    """A typed refusal from the seat layer: an unknown or duplicate hook."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@runtime_checkable
class MiniCalibrationHookV1(Protocol):
    """Given a seat's layout entries for a cycle, return a reshaped tuple --
    or None to leave them exactly as the layout declared them."""

    hook_id: str
    hook_version: str

    def calibrate(
        self, *, seat_id: str, cycle: int, entries: tuple[SeatPackLayoutEntryV1, ...]
    ) -> tuple[SeatPackLayoutEntryV1, ...] | None: ...


class _NoopCalibrationHook:
    hook_id = "mini.calibration.noop.v1"
    hook_version = "1.0.0"

    def calibrate(self, *, seat_id, cycle, entries):
        return None


DEFAULT_CALIBRATION_HOOK_ID = _NoopCalibrationHook.hook_id
_CALIBRATION_HOOKS: dict[str, MiniCalibrationHookV1] = {}


def register_mini_calibration_hook(hook: MiniCalibrationHookV1) -> MiniCalibrationHookV1:
    """Add a hook. A SECOND registration anywhere under `src/` or
    `mini/minireason/` is a violation of R8, and the architecture test says
    so by name: the operator has not yet said how the controller steps in."""

    if not isinstance(hook, MiniCalibrationHookV1):
        raise MiniSeatError(
            "MINI_CALIBRATION_HOOK_MALFORMED",
            "a calibration hook must carry hook_id, hook_version and calibrate",
        )
    existing = _CALIBRATION_HOOKS.get(hook.hook_id)
    if existing is not None and existing is not hook:
        raise MiniSeatError(
            "MINI_CALIBRATION_HOOK_CONFLICT",
            f"hook id {hook.hook_id!r} is already registered",
        )
    _CALIBRATION_HOOKS[hook.hook_id] = hook
    return hook


def mini_calibration_hook_ids() -> tuple[str, ...]:
    return tuple(sorted(_CALIBRATION_HOOKS))


def resolve_mini_calibration_hook(hook_id: str | None = None) -> MiniCalibrationHookV1:
    requested = DEFAULT_CALIBRATION_HOOK_ID if hook_id is None else hook_id
    hook = _CALIBRATION_HOOKS.get(requested)
    if hook is None:
        raise MiniSeatError(
            "MINI_CALIBRATION_HOOK_UNKNOWN",
            f"no mini calibration hook {requested!r}; registered: "
            + ", ".join(mini_calibration_hook_ids()),
        )
    return hook


register_mini_calibration_hook(_NoopCalibrationHook())


__all__ = [
    "COMMITMENT_PROPOSAL_KIND",
    "CONJECTURE_KIND",
    "CONJECTURER_LEGACY_LAYOUT",
    "CONJECTURER_LEGACY_LAYOUT_ID",
    "CONJECTURER_LEGACY_SHELL",
    "CRITICISM_KIND",
    "DEFAULT_CALIBRATION_HOOK_ID",
    "MiniCalibrationHookV1",
    "MiniSeatError",
    "mini_calibration_hook_ids",
    "resolve_mini_calibration_hook",
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
