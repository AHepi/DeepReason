"""The shipped seat pack layouts — today's composition, as configuration.

`seat-pack.conjecturer.legacy-v0` and `seat-pack.critic.legacy-v0` reproduce
what `render_conj_pack` and `render_crit_pack` compose today: the same section
ids, in the same priorities, with the same droppable/compressible flags and
the same `min_tokens` floors. Nothing changes unless someone selects a
different layout, which is the operator's "configurable with defaults" (R11)
made checkable — `tests/test_conj_pack_legacy_golden.py` and
`tests/test_crit_pack_legacy_golden.py` are the check.

The two seats SHARE `dr.frame.crisis`, `dr.frame.slice` and
`dr.evidence.citable`, at different priorities and floors. That sharing is the
point of putting allocation facts in the layout entry rather than in the
plugin: the same section, budgeted differently, is one plugin used twice.
"""

from __future__ import annotations

from deepreason.llm.seat_sections import (
    SeatPackLayoutEntryV1,
    SeatPackLayoutV1,
    SeatShellV1,
    register_seat_pack_layout,
    register_seat_shell,
)

CONJECTURER_SEAT = "conjecturer"
CRITIC_SEAT = "argumentative_critic"

CONJECTURER_LEGACY_LAYOUT_ID = "seat-pack.conjecturer.legacy-v0"
CRITIC_LEGACY_LAYOUT_ID = "seat-pack.critic.legacy-v0"


def _entry(plugin_id, priority, *, droppable=False, compressible=False,
           min_tokens=0, params=None):
    return SeatPackLayoutEntryV1(
        plugin_id=plugin_id,
        priority=priority,
        droppable=droppable,
        compressible=compressible,
        min_tokens=min_tokens,
        params=params or {},
    )


# Order here is CONSTRUCTION order, which is what the renderer walks. The
# allocator re-orders by `(priority, id)` afterwards, so this list's order is
# visible only in the rare tie the ids do not break.
CONJECTURER_LEGACY_LAYOUT = SeatPackLayoutV1(
    layout_id=CONJECTURER_LEGACY_LAYOUT_ID,
    entries=(
        _entry("dr.problem", 1),
        _entry("dr.criteria", 2),
        _entry("dr.open-criticisms", 2),
        _entry("dr.mandatory-interface", 3),
        _entry("dr.active-properties", 4, droppable=True, compressible=True,
               min_tokens=24),
        _entry("dr.school-stance", 5, compressible=True, min_tokens=24),
        _entry("dr.generation-context", 6),
        _entry("dr.scratch-advisory", 7),
        _entry("dr.evidence.frozen", 4, droppable=True, compressible=True,
               min_tokens=64),
        _entry("dr.evidence.citable", 4, droppable=True, compressible=True,
               min_tokens=64),
        _entry("dr.capability-result", 3),
        _entry("dr.frame.crisis", 4),
        _entry("dr.frame.slice", 4, compressible=True, min_tokens=96),
        _entry("dr.neighbourhood", 8, droppable=True, compressible=True,
               min_tokens=32),
        _entry("dr.neighbourhood.live", 12, droppable=True, compressible=True,
               min_tokens=32),
        _entry("dr.history.v1", 8, droppable=True, compressible=True,
               min_tokens=24),
        _entry("dr.crossover", 9, droppable=True, compressible=True,
               min_tokens=24),
        _entry("dr.complement-directive", 10),
        _entry("dr.diversity-specifications", 11),
        _entry("dr.output-contract.conjecturer", 12),
    ),
)

CRITIC_LEGACY_LAYOUT = SeatPackLayoutV1(
    layout_id=CRITIC_LEGACY_LAYOUT_ID,
    entries=(
        _entry("dr.problem-context", 1, compressible=True, min_tokens=64),
        _entry("dr.target-commitments", 2),
        _entry("dr.machine-evaluation-boundary", 3),
        _entry("dr.standing-attacks", 5, droppable=True, compressible=True,
               min_tokens=24),
        _entry("dr.target.support-chain", 4),
        _entry("dr.target.support-content", 6, droppable=True,
               compressible=True, min_tokens=24),
        _entry("dr.frame.crisis", 4),
        _entry("dr.frame.slice", 4, compressible=True, min_tokens=96),
        _entry("dr.target", 4),
        _entry("dr.counterexample-recourse", 6),
        _entry("dr.premise-invitation", 6, droppable=True, compressible=True,
               min_tokens=32),
        # The legend renders only alongside the invitation it serves: one
        # visible while the invitation was dropped would list ids nothing
        # asked the critic to cite.
        _entry("dr.evidence.citable", 6, droppable=True, compressible=True,
               min_tokens=32, params={"requires_invitation": True}),
        _entry("dr.output-contract.critic", 7),
    ),
)


# The two shipped shells reproduce today's two seats exactly. A third pairing
# -- a second conjecturer kind, a second criticism kind -- is a registration
# when the operator says what it is (R22, R23), not a code change.
CONJECTURER_LEGACY_SHELL = SeatShellV1(
    shell_id="seat.conjecturer.legacy-v0",
    seat_id=CONJECTURER_SEAT,
    layout_id=CONJECTURER_LEGACY_LAYOUT_ID,
    form_id="conjecturer.turn.v6",
    role_prompt_template_id="role-prompt.legacy-v0",
)

CRITIC_LEGACY_SHELL = SeatShellV1(
    shell_id="seat.critic.legacy-v0",
    seat_id=CRITIC_SEAT,
    layout_id=CRITIC_LEGACY_LAYOUT_ID,
    form_id="argumentative_critic.compact.v1",
    role_prompt_template_id="role-prompt.legacy-v0",
)


# ---------------------------------------------------------------------------
# The organiser: a third registered pairing (R22's "conjecturers will need to
# be split in two", first instance). It carries a writer's-room record onto
# the run through the attached-evidence road and invents nothing: the same
# seat, a different brief, and the form the managed conjecturer already fills.
#
# THE FORM. The tranche that commissioned this pairing named
# `reasoning.conjecturer.compact.v2` as the existing form to pair with. That
# form does not reach the managed `deepreason reason` path: under a v6
# manifest `rules/conj.py` dispatches `conjecturer.turn.v6`, whose candidate
# on the reasoning workload is the same `ReasoningCandidateProposal` (claim,
# mechanism, counterconditions >= 1, typicality, evidence_refs <= 8) that
# compact.v2 compiles to, and whose counterconditions become commitments on
# admission. So the pairing names `conjecturer.turn.v6` -- the form the seat
# actually fills -- and delivers the property the brief wanted rather than
# the id it named (experiments/2026-09-06-change-writers-room-organiser-
# testing/SPEC.md, A1). No new form; the parse half does not vary.
#
# THE LAYOUT. The legacy conjecturer layout with the sections that push
# INVENTION removed (school stance, crossover, the complement directive, the
# diversity specifications, history) and the two evidence sections made
# exact: the room IS the input, so a budget that compressed or dropped it
# would render a brief that asks the seat to organise content it cannot see.
# Everything else -- open criticisms and their discharge obligation, the
# mandatory interface, the neighbourhood the seat must not re-propose into --
# is the record's, and stays.
#
# THE CRITIC BESIDE IT. `seat.critic.evidence-blind-v1` is the legacy critic
# layout without the premise invitation and the citable legend, for a run
# whose critic must attack the organised candidates on its own terms and
# never read the room (the same tranche, R14). It changes no target binding
# and no form.
# ---------------------------------------------------------------------------

ORGANISER_LAYOUT_ID = "seat-pack.conjecturer.organiser-v1"
ORGANISER_SHELL_ID = "seat.conjecturer.organiser-v1"
ORGANISER_ROLE_PROMPT_ID = "role-prompt.organiser-v1"
CRITIC_EVIDENCE_BLIND_LAYOUT_ID = "seat-pack.critic.evidence-blind-v1"
CRITIC_EVIDENCE_BLIND_SHELL_ID = "seat.critic.evidence-blind-v1"

_ORGANISER_DROPS = frozenset(
    {
        "dr.school-stance",
        "dr.crossover",
        "dr.complement-directive",
        "dr.diversity-specifications",
        "dr.history.v1",
        "dr.output-contract.conjecturer",
    }
)
_ORGANISER_EXACT = frozenset({"dr.evidence.frozen", "dr.evidence.citable"})


def _organiser_entries() -> tuple[SeatPackLayoutEntryV1, ...]:
    entries: list[SeatPackLayoutEntryV1] = []
    for entry in CONJECTURER_LEGACY_LAYOUT.entries:
        if entry.plugin_id in _ORGANISER_DROPS:
            continue
        if entry.plugin_id in _ORGANISER_EXACT:
            entries.append(_entry(entry.plugin_id, 2))
            continue
        entries.append(entry)
    entries.append(_entry("dr.output-contract.organiser", 12))
    return tuple(entries)


ORGANISER_LAYOUT = SeatPackLayoutV1(
    layout_id=ORGANISER_LAYOUT_ID, entries=_organiser_entries()
)

CRITIC_EVIDENCE_BLIND_LAYOUT = SeatPackLayoutV1(
    layout_id=CRITIC_EVIDENCE_BLIND_LAYOUT_ID,
    entries=tuple(
        entry
        for entry in CRITIC_LEGACY_LAYOUT.entries
        if entry.plugin_id not in {"dr.premise-invitation", "dr.evidence.citable"}
    ),
)

ORGANISER_SHELL = SeatShellV1(
    shell_id=ORGANISER_SHELL_ID,
    seat_id=CONJECTURER_SEAT,
    layout_id=ORGANISER_LAYOUT_ID,
    form_id="conjecturer.turn.v6",
    role_prompt_template_id=ORGANISER_ROLE_PROMPT_ID,
)

CRITIC_EVIDENCE_BLIND_SHELL = SeatShellV1(
    shell_id=CRITIC_EVIDENCE_BLIND_SHELL_ID,
    seat_id=CRITIC_SEAT,
    layout_id=CRITIC_EVIDENCE_BLIND_LAYOUT_ID,
    form_id=CRITIC_LEGACY_SHELL.form_id,
    role_prompt_template_id=CRITIC_LEGACY_SHELL.role_prompt_template_id,
)


def register_shipped_layouts() -> None:
    register_seat_pack_layout(
        CONJECTURER_LEGACY_LAYOUT, default_for_seat=CONJECTURER_SEAT
    )
    register_seat_pack_layout(CRITIC_LEGACY_LAYOUT, default_for_seat=CRITIC_SEAT)
    register_seat_shell(CONJECTURER_LEGACY_SHELL, default_for_seat=CONJECTURER_SEAT)
    register_seat_shell(CRITIC_LEGACY_SHELL, default_for_seat=CRITIC_SEAT)
    # Registered, never default: a run selects them through
    # DEEPREASON_SEAT_SHELL, and the goldens above stay byte-identical.
    register_seat_pack_layout(ORGANISER_LAYOUT)
    register_seat_pack_layout(CRITIC_EVIDENCE_BLIND_LAYOUT)
    register_seat_shell(ORGANISER_SHELL)
    register_seat_shell(CRITIC_EVIDENCE_BLIND_SHELL)
