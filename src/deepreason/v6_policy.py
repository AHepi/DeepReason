"""Repository-owned RunManifest-v6 control presets.

Two presets live here:

* ``conservative`` — the historical closed baseline (no scratch writes, no
  model context requests, no manifest-owned criticism routing).  It is kept
  verbatim so replay, comparison, and older fixtures remain exact.
* ``engaged`` — the public default compiled by run preparation.  The
  advisory scratchpad and bounded conjecture-context requests are ON
  (designed to relieve pressure and prevent models from hallucinating),
  manifest-owned foreign-school semantic criticism is ON in its
  observe-only, single-provider form, and the grounded two-stage bridge is
  ON in its review-free single-route form so completed public runs can
  produce grounded final views.  Every allowance stays finite and modest so
  the preset fits the fixed public 6-cycle/100k-token envelope.
"""

from __future__ import annotations

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    CriticismPolicyV1,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    ScratchAuthoringPolicyV1,
)


POLICY_PRESET_ID = "deepreason.v6.engaged.v1"

# Public text runs seed exactly Config().N_SCHOOLS conditioning-only schools
# (school-0..school-3, see deepreason.capture.schools.init_schools); the
# engaged criticism policy must bind every one of them.
PUBLIC_SCHOOL_COUNT = 4

# The placeholder endpoint id used only inside the preset digest so the
# preset identity stays provider-neutral; real bindings substitute the
# profile's exact endpoint id at manifest compile time.
_PRESET_ENDPOINT_TEMPLATE = "preset-endpoint-template"


def conservative_control_plane_policy_v3() -> ControlPlanePolicyV3:
    """Return the closed baseline: no retries, model context requests, or scratch writes."""

    return ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(),
    )


def conservative_policy_digest() -> str:
    policy = conservative_control_plane_policy_v3()
    return sha256_hex(
        b"deepreason.v6-policy-preset.v1\x00"
        + canonical_json(
            {
                "preset": "deepreason.v6.conservative.v1",
                "control_plane_policy": policy.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
            }
        )
    )


def engaged_control_plane_policy_v3() -> ControlPlanePolicyV3:
    """Return the public default: bounded scratch authoring and context ON.

    Schools stay conditioning-only (routing diversity is a provider-topology
    question, not a public default), workflow retries stay at zero, and the
    wire contracts are the frozen v6 set.  What changes against the
    conservative baseline is finite advisory authority: models may request a
    small bounded scratch context per conjecture work item and may propose a
    small bounded number of advisory scratch records per turn.
    """

    return ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="harness_plus_model_request",
            initial_max_blocks=8,
            initial_max_guides=2,
            max_context_expansion_requests=2,
            max_extra_blocks=8,
            permitted_retrieval_channels=(
                "focus",
                "link",
                "keyword",
                "semantic",
                "recent",
            ),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(
            enabled=True,
            maximum_new_blocks_per_turn=4,
            maximum_revisions_per_turn=4,
            maximum_links_per_turn=4,
            maximum_unresolved_questions_per_turn=4,
            maximum_cluster_suggestions_per_turn=4,
            maximum_total_bytes=128 * 1024,
        ),
    )


def engaged_scratchpad_source() -> dict:
    """Typed-Config source enabling the advisory scratch workspace.

    Only ``enabled`` changes; every pack/channel bound keeps the audited
    ScratchpadConfig defaults, and with no EMBEDDER_MODEL configured the
    semantic channel compiles to the deterministic hashing embedder — no new
    dependencies.
    """

    return {"enabled": True}


def engaged_bridge_source() -> dict:
    """Typed-Config source enabling the grounded two-stage bridge.

    This is the audited review-free shape: Stage A (claim ledger, frozen
    ``summarizer`` route) and Stage B (composition, frozen ``thesis`` route)
    with the minimum one-repair schema budget, no grounding-review stream,
    and a small bounded four-section output.  Public preparation seats every
    canonical role on the single provider endpoint, so both frozen bridge
    roles ride the one public route.
    """

    return {
        "mode": "grounded_two_stage",
        "grounding_review": False,
        "max_schema_repair_attempts": 1,
        "max_grounding_repair_attempts": 0,
        "output_section_limit": 4,
    }


def engaged_criticism_policy(endpoint_id: str) -> CriticismPolicyV1:
    """Bind every seeded public school to the single provider critic seat.

    Public runs have exactly one provider endpoint carrying every frozen
    role seat, so all four conditioning-only schools share the single
    ``argumentative_critic`` seat (``allow_shared=True``).  Coverage of one
    foreign school per accepted school artifact keeps the token cost inside
    the public envelope while guaranteeing that semantic criticism actually
    runs; authority stays observe-only.
    """

    return CriticismPolicyV1(
        minimum_foreign_school_coverage=1,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{index}",
                role="argumentative_critic",
                seat=0,
                endpoint_id=endpoint_id,
            )
            for index in range(PUBLIC_SCHOOL_COUNT)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="observe_only",
        allow_shared=True,
    )


def engaged_policy_digest() -> str:
    """Digest the complete engaged preset in a provider-neutral form."""

    policy = engaged_control_plane_policy_v3()
    criticism_template = engaged_criticism_policy(_PRESET_ENDPOINT_TEMPLATE)
    return sha256_hex(
        b"deepreason.v6-policy-preset.v2\x00"
        + canonical_json(
            {
                "preset": POLICY_PRESET_ID,
                "control_plane_policy": policy.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
                "criticism_policy_template": criticism_template.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
                "scratchpad_source": engaged_scratchpad_source(),
                "bridge_source": engaged_bridge_source(),
            }
        )
    )


__all__ = [
    "POLICY_PRESET_ID",
    "PUBLIC_SCHOOL_COUNT",
    "conservative_control_plane_policy_v3",
    "conservative_policy_digest",
    "engaged_bridge_source",
    "engaged_control_plane_policy_v3",
    "engaged_criticism_policy",
    "engaged_policy_digest",
    "engaged_scratchpad_source",
]
