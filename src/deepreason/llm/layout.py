"""The render layout policy — where a rendered prompt puts what it carries.

`docs/RESEARCH_ATTENTION_LAYOUT_2026-08-28.md` lists seven findings as robust
across models. Four of them are layout decisions this tree can act on: put
nothing load-bearing after the question, keep standing instructions under
about forty, carry prior-round material distilled rather than verbatim with
the full text retrievable by reference, and prefer few large blocks to many
small ones. That note is an external document and is NOT evidence in this
record's sense; what makes these four safe to fix in the harness is that the
note itself separates them from the model-specific items in its section (b),
and the operator approved a tranche implementing exactly that list.

Three layers, and they are not interchangeable (the signal-contract pattern
the modularity law generalizes):

**FROZEN** is the change protocol. A layout decision is a POLICY a renderer
READS; no renderer may hold a layout constant of its own, and the
architecture test in `tests/test_render_layout_policy.py` goes red when one
does. Layout touches PRESENTATION, never EVIDENCE: no flag here may change
which artifacts exist, what a commitment means, or what counts as a
refutation -- only where the bytes sit and how much of one artifact is shown.

**VERSIONED** is this registry. Every arrangement the tree can render is a
named, registered policy, so the pre-2026-08-28 arrangement remains reachable
as configuration (`render-layout.legacy-v0`) rather than by reverting code.

**FREE** is the parameter values inside their envelopes, refused typed at
construction when out of range rather than silently clamped.

Why this is an artifact registry and not a `Config` field, which would be the
obvious shape: `run_manifest.py::_source_config_data` dumps every `Config`
field into `engine_config_json`, and `qualification.py` folds that into every
qualification subject digest. A layout knob on `Config` would therefore move
the digest of every qualification bundle in the tree -- or need a companion
pop inside `run_manifest.py`, which is a frozen surface. Selection by id, from
an argument or from the environment, reaches neither.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field

LAYOUT_POLICY_SCHEMA = "render-layout.v1"
DEFAULT_LAYOUT_POLICY_ID = "render-layout.v1"
LEGACY_LAYOUT_POLICY_ID = "render-layout.legacy-v0"
LAYOUT_POLICY_ENV = "DEEPREASON_RENDER_LAYOUT_POLICY"

# The research note's own numbers: a steep decline in adherence from about
# forty simultaneous instructions and a hard floor -- zero perfect responses,
# every model, every format -- at eighty. A ceiling above the floor would be a
# ceiling that cannot bind, so the envelope stops there.
INSTRUCTION_CEILING_FLOOR = 80


class RenderLayoutPolicyError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class RenderLayoutPolicyV1(BaseModel):
    """One arrangement of a rendered prompt, as a versioned artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1, max_length=64)

    question_last: bool = True
    """Restate the question as the final block, so nothing load-bearing
    follows it. The negative is the robust half of 2507.22887: material at the
    end of the user message flipped more than 30% of predictions without
    improving correctness. Which PRE-question slot is best is model-specific
    and is not decided here."""

    instruction_ceiling: int = Field(default=40, ge=1, le=INSTRUCTION_CEILING_FLOOR)
    """The most natural-language standing instructions one rendered prompt may
    carry. Measured, not enforced by truncation: nothing here drops an
    instruction, because dropping one silently is the failure this bound
    exists to make visible."""

    live_verbatim_n: int = Field(default=2, ge=0, le=8)
    """How many live prior-round artifacts render whole, late, labelled live.
    Few by design: the late slot amplifies whatever occupies it, distractors
    included, so it is spent only on material that should dominate."""

    distilled_head_chars: int = Field(default=160, ge=32, le=4096)
    """The width of a distilled carry-forward entry."""

    superseded_summary_n: int = Field(default=0, ge=0, le=8)
    """How many SUPERSEDED artifacts render as one-line distilled summaries.
    Zero is this tree's shipped behaviour and one of the two options the
    research note's own placement table gives for this row ("Middle or
    omit"). Raising it puts refuted lines back in front of the seat whose job
    is to leave them -- an epistemic change, not a layout one -- so it is a
    knob the operator turns, not a default."""

    retrieval_note: bool = True
    """State a carry-forward cap in band and name the route to the full text.
    A silent cut is indistinguishable, from the model's side, from content
    that never existed."""

    merge_head_label_blocks: bool = True
    """Join each head label to the body it labels. The U-shape re-instantiates
    inside every delimiter-bounded interval, so a bare label on its own is a
    block boundary bought for nothing."""


ROBUST_LAYOUT_POLICY = RenderLayoutPolicyV1(policy_id=DEFAULT_LAYOUT_POLICY_ID)

LEGACY_LAYOUT_POLICY = RenderLayoutPolicyV1(
    policy_id=LEGACY_LAYOUT_POLICY_ID,
    question_last=False,
    live_verbatim_n=0,
    superseded_summary_n=0,
    retrieval_note=False,
    merge_head_label_blocks=False,
)
"""The arrangement every committed root was rendered under. Shipped so the old
layout is reachable by configuration; a rollback that needs a code edit is the
thing the modularity law forbids."""

_REGISTRY: dict[str, RenderLayoutPolicyV1] = {
    ROBUST_LAYOUT_POLICY.policy_id: ROBUST_LAYOUT_POLICY,
    LEGACY_LAYOUT_POLICY.policy_id: LEGACY_LAYOUT_POLICY,
}


def register_layout_policy(policy: RenderLayoutPolicyV1) -> RenderLayoutPolicyV1:
    """Add an arrangement. Re-registering the same id with different values is
    refused: a policy id names one arrangement for the life of the process, or
    two renders citing the same id would not mean the same thing."""

    existing = _REGISTRY.get(policy.policy_id)
    if existing is not None and existing != policy:
        raise RenderLayoutPolicyError(
            "RENDER_LAYOUT_POLICY_CONFLICT",
            f"policy id {policy.policy_id!r} is already registered with "
            "different values",
        )
    _REGISTRY[policy.policy_id] = policy
    return policy


def layout_policy_ids() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def resolve_layout_policy(
    policy_id: str | None = None,
) -> RenderLayoutPolicyV1:
    """Explicit argument, then the environment, then the default."""

    requested = policy_id or os.environ.get(LAYOUT_POLICY_ENV) or ""
    requested = requested.strip() or DEFAULT_LAYOUT_POLICY_ID
    policy = _REGISTRY.get(requested)
    if policy is None:
        raise RenderLayoutPolicyError(
            "RENDER_LAYOUT_POLICY_UNKNOWN",
            f"no render layout policy {requested!r}; registered: "
            + ", ".join(layout_policy_ids()),
        )
    return policy
