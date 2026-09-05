"""The mini FLOW: which seats run, in what order, producing which kinds --
as registered, versioned DATA that the loop walks and never names.

Implements S8 (R9, R10, C1, C8) of the mini isolation programme. R9 is the
operator's "The mini flow also needs to be adjustable in a pluggable way";
R10 is "add new artifact types on the fly if I can see it might help"; C8 is
the modularity law, whose "enforced" clause is `mini/tests/
test_mini_architecture.py`.

A flow is a tuple of STAGES. Each stage names a seat, the shell it renders
through, the kind it produces and the kinds it reads. The SET of artifact
kinds a flow may carry is declared on the flow, and a stage naming a kind
outside it is refused at construction -- the set is data, and the loop
consults it rather than knowing it. Adding a new artifact kind and its seat
is therefore a registration: a form, a layout, a shell, and a stage that
names them, in any module at all, and no source edit under
`mini/minireason/` (`test_mini_flow.py::test_a_new_artifact_kind_is_a_registration`
is the proof, and it registers from a TEST file).

Two flows ship, both switchable, neither permanent (C1). The DEFAULT is
`mini.flow.legacy-v0`, one conjecturer stage under the legacy shell with both
commitment channels ON -- today's loop -- so nothing changes for anyone who
selects nothing (C4). `mini.flow.isolation.v1` is conjecturer -> critic ->
commitment with both channels OFF and the typed warning. Selection is
argument, then `DEEPREASON_MINI_FLOW`, then the default; never `Config`,
never the manifest, for the reason every registry here gives.

A flow is resolved ONCE, before the first call, and is immutable after (A7):
mid-run mutation of the kind set would let two replays of one log disagree.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from minireason.policy import DEFAULT_MINI_COMMITMENT_POLICY, MiniCommitmentPolicyV1
from minireason.seats import (
    COMMITMENT_PROPOSAL_KIND,
    COMMITMENT_SEAT,
    COMMITMENT_SHELL,
    CONJECTURE_KIND,
    CONJECTURER_LEGACY_SHELL,
    CONJECTURER_SEAT,
    CONJECTURER_SHELL,
    CRITIC_SEAT,
    CRITIC_SHELL,
    CRITICISM_KIND,
    DEFAULT_CALIBRATION_HOOK_ID,
)

MINI_FLOW_ENV = "DEEPREASON_MINI_FLOW"
DEFAULT_MINI_FLOW_ID = "mini.flow.legacy-v0"
ISOLATION_FLOW_ID = "mini.flow.isolation.v1"


class MiniFlowError(ValueError):
    """A typed refusal about a flow: an unknown id, a stage naming a kind the
    flow does not declare, a conflicting registration."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class MiniStageV1:
    """One seat's turn in a cycle.

    `per_target` says whether the stage runs once per cycle (a conjecturer)
    or once for each artifact of its `reads_kinds` that THIS cycle produced
    (a critic, a commitment seat). `brief_share` is the fraction of the
    profile's prompt budget the stage's "everything so far" section may
    take when its layout declares no budget of its own -- the FREE
    parameter that keeps a shell-rendered brief inside the call layer's
    clip (PARKED P8), disclosed by the retention rule rather than cut.
    """

    stage_id: str
    seat_id: str
    shell_id: str
    produces_kind: str
    reads_kinds: tuple[str, ...] = ()
    per_target: bool = False
    brief_share: float = 0.6


@dataclass(frozen=True, slots=True)
class MiniFlowV1:
    flow_id: str
    flow_version: str
    stages: tuple[MiniStageV1, ...]
    artifact_kinds: tuple[str, ...]
    commitment_policy: MiniCommitmentPolicyV1 = field(
        default_factory=lambda: DEFAULT_MINI_COMMITMENT_POLICY
    )
    calibration_hook_id: str = DEFAULT_CALIBRATION_HOOK_ID

    def __post_init__(self) -> None:
        if not self.stages:
            raise MiniFlowError("MINI_FLOW_EMPTY", f"flow {self.flow_id!r} declares no stage")
        declared = set(self.artifact_kinds)
        seen: set[str] = set()
        for stage in self.stages:
            if stage.stage_id in seen:
                raise MiniFlowError(
                    "MINI_FLOW_DUPLICATE_STAGE",
                    f"stage id {stage.stage_id!r} appears twice in {self.flow_id!r}",
                )
            seen.add(stage.stage_id)
            for kind in (stage.produces_kind, *stage.reads_kinds):
                if kind not in declared:
                    raise MiniFlowError(
                        "MINI_FLOW_KIND_UNDECLARED",
                        f"stage {stage.stage_id!r} names kind {kind!r}, which flow "
                        f"{self.flow_id!r} does not declare in artifact_kinds",
                    )


_REGISTRY: dict[str, MiniFlowV1] = {}


def register_mini_flow(flow: MiniFlowV1) -> MiniFlowV1:
    existing = _REGISTRY.get(flow.flow_id)
    if existing is not None and existing != flow:
        raise MiniFlowError(
            "MINI_FLOW_CONFLICT",
            f"flow id {flow.flow_id!r} is already registered with different values",
        )
    _REGISTRY[flow.flow_id] = flow
    return flow


def mini_flow_ids() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def resolve_mini_flow(flow_id: str) -> MiniFlowV1:
    flow = _REGISTRY.get(flow_id)
    if flow is None:
        raise MiniFlowError(
            "MINI_FLOW_UNKNOWN",
            f"no mini flow {flow_id!r}; registered: " + ", ".join(mini_flow_ids()),
        )
    return flow


def select_mini_flow(flow: MiniFlowV1 | str | None = None) -> MiniFlowV1:
    """Argument, then `DEEPREASON_MINI_FLOW`, then the legacy default.

    An argument may be the flow itself (a test that registered its own) or
    an id. Resolved per call, so selecting through the environment takes
    effect without a restart; a malformed or unknown id is a typed refusal
    at the point of use, never a silent fallback to the default.
    """

    if isinstance(flow, MiniFlowV1):
        return flow
    requested = flow
    if requested is None:
        raw = (os.environ.get(MINI_FLOW_ENV) or "").strip()
        requested = raw or None
    if requested is None:
        requested = DEFAULT_MINI_FLOW_ID
    return resolve_mini_flow(requested)


register_mini_flow(
    MiniFlowV1(
        flow_id=DEFAULT_MINI_FLOW_ID,
        flow_version="0.1.0",
        stages=(
            MiniStageV1(
                stage_id="conjecture",
                seat_id=CONJECTURER_SEAT,
                shell_id=CONJECTURER_LEGACY_SHELL.shell_id,
                produces_kind=CONJECTURE_KIND,
            ),
        ),
        artifact_kinds=(CONJECTURE_KIND,),
        commitment_policy=DEFAULT_MINI_COMMITMENT_POLICY,
    )
)
register_mini_flow(
    MiniFlowV1(
        flow_id=ISOLATION_FLOW_ID,
        flow_version="1.0.0",
        stages=(
            MiniStageV1(
                stage_id="conjecture",
                seat_id=CONJECTURER_SEAT,
                shell_id=CONJECTURER_SHELL.shell_id,
                produces_kind=CONJECTURE_KIND,
            ),
            MiniStageV1(
                stage_id="criticism",
                seat_id=CRITIC_SEAT,
                shell_id=CRITIC_SHELL.shell_id,
                produces_kind=CRITICISM_KIND,
                reads_kinds=(CONJECTURE_KIND,),
                per_target=True,
            ),
            MiniStageV1(
                stage_id="commitment",
                seat_id=COMMITMENT_SEAT,
                shell_id=COMMITMENT_SHELL.shell_id,
                produces_kind=COMMITMENT_PROPOSAL_KIND,
                reads_kinds=(CONJECTURE_KIND,),
                per_target=True,
            ),
        ),
        artifact_kinds=(CONJECTURE_KIND, CRITICISM_KIND, COMMITMENT_PROPOSAL_KIND),
        commitment_policy=MiniCommitmentPolicyV1(
            mandatory_skeleton_wf=False, model_authored_forbidden=False
        ),
    )
)


__all__ = [
    "DEFAULT_MINI_FLOW_ID",
    "ISOLATION_FLOW_ID",
    "MINI_FLOW_ENV",
    "MiniFlowError",
    "MiniFlowV1",
    "MiniStageV1",
    "mini_flow_ids",
    "register_mini_flow",
    "resolve_mini_flow",
    "select_mini_flow",
]
