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


def register_shipped_layouts() -> None:
    register_seat_pack_layout(
        CONJECTURER_LEGACY_LAYOUT, default_for_seat=CONJECTURER_SEAT
    )
    register_seat_pack_layout(CRITIC_LEGACY_LAYOUT, default_for_seat=CRITIC_SEAT)
    register_seat_shell(CONJECTURER_LEGACY_SHELL, default_for_seat=CONJECTURER_SEAT)
    register_seat_shell(CRITIC_LEGACY_SHELL, default_for_seat=CRITIC_SEAT)
