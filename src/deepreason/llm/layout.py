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
import re

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

    distil_carry_forward: bool = True
    """Carry a prior-round artifact as its CLAIM rather than as the first N
    characters of its serialized envelope. Distillation here is STRUCTURAL and
    deterministic -- the claim field is read, not summarized by a model -- so
    it costs no call and cannot hallucinate. A prefix clip cuts through the
    middle of an envelope and is the shape the research note argues against
    twice over: verbose half-baked prior text causes rehashing, and a
    one-sentence claim summary matched or beat full context on 3-4 of 4
    models at roughly eight times less context."""

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
    distil_carry_forward=False,
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


# ---------------------------------------------------------------------------
# The unit the instruction ceiling is measured in.
#
# A ceiling without a counting rule is not a bound, so the rule lives here,
# beside the number, and one definition serves both the gate
# (`tests/test_render_layout_rules.py`) and the census instrument in
# `experiments/2026-08-28-change-render-layout-robust/tools/prompt_census.py`.
#
# A STANDING INSTRUCTION is one normative clause addressed to the model in the
# NATURAL-LANGUAGE part of a rendered prompt: a sentence or semicolon-clause
# that is imperative or carries a deontic marker.
#
# TWO EXCLUSIONS, disclosed rather than assumed, because the number means
# nothing without them:
#
# 1. The JSON Schema. It is the largest text in most prompts and carries up to
#    154 machine-checkable constraints, and the harness VALIDATES it and
#    repairs violations through the contract-repair protocol. Its clauses do
#    not compete for the adherence budget the research note measured; prose
#    clauses, which nothing checks, do. Counted in, the conjecturer reads 163
#    rather than 28 -- past the note's own hard floor -- and that number would
#    be measuring the wrong thing.
# 2. Data lines: artifact bodies, `predicate:`/`program:` commitment schemas,
#    alias listings. They are what the model reasons ABOUT, not what it is
#    told to do.

_DEONTIC = re.compile(
    r"\b(must|never|only|always|should|shall|may not|cannot|do not|don't|"
    r"required|require|forbidden|invalid|rejected|refuted|ensure|avoid)\b",
    re.IGNORECASE,
)
_IMPERATIVE = re.compile(
    r"^(return|respond|propose|give|judge|answer|write|mount|assess|state|"
    r"choose|include|carry|apply|classify|concede|explore|complete|vary|"
    r"reconcile|produce|argue|tie|set|use|read|list|report|treat|copy|"
    r"submit|address|explain|name|cite|quote|repair|do|never|always)\b",
    re.IGNORECASE,
)
_DATA_LINE = re.compile(
    r"^\s*(\{|\[|- [0-9a-f]{12,}|- SRC_\d+|- [A-Za-z0-9_.@-]+: (predicate|program):"
    r"|\"|PROBLEM [0-9a-z-]+$|TARGET [0-9a-f]{12,}|spec \d+:)"
)


def model_facing_prose(prompt: str) -> str:
    """The part of a rendered prompt the instruction ceiling is about."""

    kept = []
    for line in prompt.splitlines():
        stripped = line.strip()
        if not stripped or _DATA_LINE.match(line):
            continue
        if len(stripped) > 400 and stripped.count('"') > 20:
            continue  # an inlined record rendered on one line
        kept.append(line)
    return "\n".join(kept)


def count_standing_instructions(prompt: str) -> int:
    """How many normative clauses one rendered prompt asks the model to hold."""

    total = 0
    for chunk in re.split(r"(?<=[.!?;:])\s+|\n", model_facing_prose(prompt)):
        clause = chunk.strip(" -\t")
        if len(clause) < 12:
            continue
        if _IMPERATIVE.match(clause) or _DEONTIC.search(clause):
            total += 1
    return total
