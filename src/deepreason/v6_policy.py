"""Repository-owned RunManifest-v6 control presets.

Two presets live here:

* ``conservative`` — the historical closed baseline (no scratch writes, no
  model context requests, no manifest-owned criticism routing).  It is kept
  verbatim so replay, comparison, and older fixtures remain exact.
* ``engaged`` — the public default compiled by run preparation.  The
  advisory scratchpad and bounded conjecture-context requests are ON
  (designed to relieve pressure and prevent models from hallucinating),
  manifest-owned foreign-school semantic criticism is ON in its
  observe-only, single-provider form, the grounded two-stage bridge is
  ON in its review-free single-route form so completed public runs can
  produce grounded final views, and the deterministic local simulation
  capability is ON in its declarative-numeric-only form with one frozen
  local no-network toolchain.  Every allowance stays finite and modest so
  the preset fits the fixed public 6-cycle/100k-token envelope.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.capabilities.policy import (
    AttachedEvidencePolicyV1,
    ConfigRefereePolicyV1,
    InquiryCapabilityPolicyV1,
    ResearchCapabilityPolicyV1,
    SimulationCapabilityPolicyV1,
)
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    CriticismPolicyV1,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    ScratchAuthoringPolicyV1,
    ToolchainEntry,
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

    Stage A (claim ledger, frozen ``summarizer`` route) and Stage B
    (composition, frozen ``thesis`` route) with the minimum one-repair schema
    budget and a small bounded four-section output.  Public preparation seats
    every canonical role on the single provider endpoint, so every frozen
    bridge role rides the one public route.

    ``grounding_review`` is the only source of behavioral authority for the
    ``reviewer_role`` seat: ``_route_seat_behavioral_contract_assignments``
    grants that seat a contract in no other branch, so with review off the
    seat qualifies ``inactive_no_authorized_contract`` and every phase that
    needs it defers ``transaction-contract-unavailable``.
    """

    return {
        "mode": "grounded_two_stage",
        "grounding_review": True,
        "max_schema_repair_attempts": 1,
        "max_grounding_repair_attempts": 0,
        "output_section_limit": 4,
    }


def engaged_criticism_policy(
    endpoint_id: str, *, authority: str = "observe_only"
) -> CriticismPolicyV1:
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
        authority=authority,
        allow_shared=True,
    )


# One fixed public identity for the single frozen local simulation
# toolchain.  The identity string is machine-neutral (it participates in the
# preset digest); the executable binding it names is derived per machine at
# manifest compile time by ``engaged_local_simulation_toolchain``.
PUBLIC_SIMULATION_TOOLCHAIN_ID = "python@deepreason-public-local.v1"

# The operator-opted contained runner freezes its own toolchain identity so a
# contained manifest can never be mistaken for a local-declarative one.
PUBLIC_CONTAINED_TOOLCHAIN_ID = "python@deepreason-public-contained.v1"


def _contained_runner_opted(environ=None) -> bool:
    env = os.environ if environ is None else environ
    runner = str(env.get("DEEPREASON_SIMULATION_RUNNER", "")).strip().lower()
    if runner in {"", "declarative"}:
        return False
    if runner != "contained":
        raise ValueError(
            "DEEPREASON_SIMULATION_RUNNER must be 'declarative' or 'contained'"
        )
    return True


def engaged_simulation_policy(environ=None) -> SimulationCapabilityPolicyV1:
    """Return the public simulation authority, declarative-numeric by default.

    Default (``DEEPREASON_SIMULATION_RUNNER`` unset or ``declarative``): only
    the trusted declarative-numeric compiler path is reachable — the runner
    profile is ``simulation.declarative.v1`` and the controller refuses
    ``sandboxed_python_v1`` proposals outright, so no model-authored Python
    ever reaches the local subprocess backend.  The returned policy is
    byte-identical to the historical preset, so existing qualification
    subjects are untouched.

    Operator-opted (``DEEPREASON_SIMULATION_RUNNER=contained``): the runner
    profile becomes ``simulation.container.v1`` and model-authored
    ``sandboxed_python_v1`` programs run inside the contained subprocess
    runner (scratch workdir, scrubbed environment, hard rlimits, unshared
    network namespace, fail-closed refusal when containment is unavailable).
    The changed policy changes the manifest — a different qualification
    subject, exactly like a changed research allowlist.
    """

    if _contained_runner_opted(environ):
        return SimulationCapabilityPolicyV1(
            enabled=True,
            backend_identity="simulation-python-contained",
            runner_profile="simulation.container.v1",
            python_toolchain_identity=PUBLIC_CONTAINED_TOOLCHAIN_ID,
            maximum_simulation_requests=2,
            maximum_simulation_executions=2,
            maximum_proposals_per_turn=1,
            # Model-authored Python earns a larger code bound than the
            # declarative DSL but the same modest request/sample envelope.
            maximum_generated_code_bytes=65_536,
            maximum_input_bytes=16_384,
            maximum_output_bytes=65_536,
            maximum_wall_ms=20_000,
            maximum_memory_bytes=512 * 1024 * 1024,
            maximum_steps=2_000_000,
            maximum_samples=64,
            deterministic_seed_policy="fixed_manifest",
            fixed_seed_set=(7,),
            maximum_follow_up_reasoning_turns=2,
            input_catalog=(),
        )
    return SimulationCapabilityPolicyV1(
        enabled=True,
        runner_profile="simulation.declarative.v1",
        python_toolchain_identity=PUBLIC_SIMULATION_TOOLCHAIN_ID,
        maximum_simulation_requests=2,
        maximum_simulation_executions=2,
        maximum_proposals_per_turn=1,
        maximum_generated_code_bytes=16_384,
        maximum_input_bytes=16_384,
        maximum_output_bytes=16_384,
        maximum_wall_ms=10_000,
        maximum_memory_bytes=256 * 1024 * 1024,
        maximum_steps=50_000,
        maximum_samples=32,
        deterministic_seed_policy="fixed_manifest",
        fixed_seed_set=(7,),
        maximum_follow_up_reasoning_turns=2,
        # Public preparation is question-only: there is no sealed input
        # catalog, so proposals parameterize their declarative programs
        # through bounded parameter definitions alone.
        input_catalog=(),
    )


def engaged_research_policy(environ=None) -> ResearchCapabilityPolicyV1:
    """Return the operator-opted contained research authority, default OFF.

    Research stays disabled — byte-identical to the historical preset, so
    every existing qualification subject is untouched — unless the operator
    names an explicit frozen domain allowlist via
    ``DEEPREASON_RESEARCH_ALLOWLIST`` (comma-separated bare lowercase
    hosts). The allowlist is part of the compiled manifest, hence part of
    the qualification behavior subject: a different list is a different
    subject and requalifies. Bounds stay modest: the budget is denominated
    in dispatched requests, and a per-response byte ceiling is containment.
    """

    env = os.environ if environ is None else environ
    raw = str(env.get("DEEPREASON_RESEARCH_ALLOWLIST", "")).strip()
    if not raw:
        return ResearchCapabilityPolicyV1()
    domains = tuple(
        dict.fromkeys(
            domain.strip().lower()
            for domain in raw.split(",")
            if domain.strip()
        )
    )
    return ResearchCapabilityPolicyV1(
        enabled=True,
        backend_identity="web.contained.v1",
        maximum_requests=int(env.get("DEEPREASON_RESEARCH_MAX_REQUESTS", "6")),
        maximum_sources=int(env.get("DEEPREASON_RESEARCH_MAX_SOURCES", "3")),
        domain_allowlist=domains,
        maximum_response_bytes=4 * 1024 * 1024,
    )


def engaged_config_referee_policy(environ=None) -> ConfigRefereePolicyV1 | None:
    """Return the operator-opted config-referee authority, default OFF.

    ``DEEPREASON_CONFIG_REFEREE`` names the review cadence in scheduler
    cycles (a positive integer). Unset keeps the policy absent — existing
    manifests stay byte-identical. An enabled referee is part of the
    compiled manifest, hence a distinct qualification subject, exactly like
    a research allowlist or the contained simulation runner.
    """

    env = os.environ if environ is None else environ
    raw = str(env.get("DEEPREASON_CONFIG_REFEREE", "")).strip()
    if not raw:
        return None
    cadence = int(raw)
    return ConfigRefereePolicyV1(
        enabled=True,
        cadence_cycles=cadence,
        window_events=1_024,
        maximum_view_bytes=128 * 1024,
    )


def engaged_attached_evidence_policy(
    *, attached: bool = False
) -> AttachedEvidencePolicyV1:
    """Return the attached-evidence authority for this preparation.

    Question-only runs keep the historical disabled policy byte-identical.
    Attaching an admitted dossier is the operator's explicit opt-in gesture,
    and it freezes one fixed finite packing/citation envelope — the same
    subject-changing discipline as the research allowlist and the contained
    simulation runner: a different authority is a different qualification
    subject.
    """

    if not attached:
        return AttachedEvidencePolicyV1()
    return AttachedEvidencePolicyV1(
        enabled=True,
        maximum_sources=16,
        maximum_total_bytes=8 * 1024 * 1024,
        maximum_excerpt_bytes_per_source=262_144,
        maximum_sources_per_pack=8,
    )


def engaged_inquiry_capability_policy(
    environ=None, *, attached_evidence: bool = False
) -> InquiryCapabilityPolicyV1:
    """Return the engaged topology: simulation ON, research operator-opted."""

    return InquiryCapabilityPolicyV1(
        capability_profile="inquiry-capabilities.v2",
        attached_evidence=engaged_attached_evidence_policy(
            attached=attached_evidence
        ),
        simulation=engaged_simulation_policy(environ),
        research=engaged_research_policy(environ),
        config_referee=engaged_config_referee_policy(environ),
    )


def engaged_local_simulation_toolchain() -> ToolchainEntry:
    """Freeze the current interpreter as the one public local toolchain.

    The wheel runs on end-user interpreters, so the executable path and the
    version fingerprint are derived here — at manifest compile time on the
    machine that will execute the run — never hardcoded.  A changed
    interpreter path or version changes the manifest behavior subject, which
    fails closed into requalification instead of silently running simulations
    on an unqualified toolchain.
    """

    version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    return ToolchainEntry(
        id=PUBLIC_SIMULATION_TOOLCHAIN_ID,
        runner="local",
        executable=str(Path(sys.executable).resolve()),
        version_output_sha256=sha256_hex(version.encode("utf-8")),
        network=False,
    )


def engaged_contained_simulation_toolchain() -> ToolchainEntry:
    """Freeze the current interpreter as the contained-runner toolchain.

    The pinned executable is whichever interpreter runs DeepReason — when the
    operator launches from a virtual environment, that venv's interpreter is
    the frozen reproducibility identity.  The containment guarantees live in
    the contained runner (scratch workdir, scrubbed environment, rlimits,
    unshared network namespace), never in the venv itself.
    """

    version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    return ToolchainEntry(
        id=PUBLIC_CONTAINED_TOOLCHAIN_ID,
        runner="container",
        executable=str(Path(sys.executable).resolve()),
        version_output_sha256=sha256_hex(version.encode("utf-8")),
        network=False,
    )


def engaged_simulation_toolchain(environ=None) -> ToolchainEntry:
    """Return the one frozen toolchain matching the engaged simulation policy."""

    if _contained_runner_opted(environ):
        return engaged_contained_simulation_toolchain()
    return engaged_local_simulation_toolchain()


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
                # Machine-neutral by construction: the policy names the fixed
                # toolchain identity string; the per-machine executable pin
                # lives only in the compiled manifest.
                "simulation_policy": engaged_simulation_policy().model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
            }
        )
    )


__all__ = [
    "POLICY_PRESET_ID",
    "PUBLIC_CONTAINED_TOOLCHAIN_ID",
    "PUBLIC_SCHOOL_COUNT",
    "PUBLIC_SIMULATION_TOOLCHAIN_ID",
    "conservative_control_plane_policy_v3",
    "conservative_policy_digest",
    "engaged_attached_evidence_policy",
    "engaged_bridge_source",
    "engaged_config_referee_policy",
    "engaged_control_plane_policy_v3",
    "engaged_criticism_policy",
    "engaged_inquiry_capability_policy",
    "engaged_contained_simulation_toolchain",
    "engaged_local_simulation_toolchain",
    "engaged_policy_digest",
    "engaged_scratchpad_source",
    "engaged_simulation_policy",
    "engaged_simulation_toolchain",
]
