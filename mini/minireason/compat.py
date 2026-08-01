"""Shared compatibility kernel for MiniReason.

MiniReason keeps its deliberately small scheduler and rule surface.  Model
presentation, wire validation, bounded repair, route freezing, canonical
bytes, and run-manifest persistence come from the parent implementation so a
mini run does not become a second protocol.

Since the parent moved to the V6-only manifest loader, a new mini root binds
a schema-6 RunManifest with ``engine_profile="mini"``.  The manifest carries
the smallest honest v6 authority surface:

* the mandatory ``ControlPlanePolicyV3`` with every optional capability in
  its explicit minimal/disabled form (conditioning-only schools, disabled
  conjecture context, zero workflow retries, disabled scratch authoring);
* the mandatory bound run input, a constant process-root declaration with no
  frozen criteria and an empty evidence dossier — mini's problems arrive per
  ``run()`` call and are registered canonically in the event log;
* the per-seat presentation plan, which mini genuinely honors through its
  profile-driven compact rendering.

The transactional-only v6 authorities (production qualification, terminal
commitments, compact recovery, contract schema-repair grants, behavioral
capability and decomposition plans) are deliberately OMITTED rather than
declared-and-ignored: mini runs through the parent Harness primitive layer,
never through the v6 transaction controller, and an absent v6 authority
field authorizes nothing.

Legacy pre-v6 mini roots are never migrated or mutated: reopening one fails
closed with ``UNSUPPORTED_RUN_MANIFEST_VERSION`` (see ``minireason.log
.replay`` for the read-only legacy replay path).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.firewall import EndpointLease, RouteFirewallError, route_from_endpoint
from deepreason.llm.profiles import ModelProfile, ProfileSpec, get_profile
from deepreason.llm.wire import (
    ReferenceFreeConjecturerWireContract,
    WireContract,
    wire_contract_for,
)
from deepreason.run_manifest import (
    MANIFEST_NAME,
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    SchoolExecutionPolicyV1,
    compile_run_manifest,
    load_run_manifest,
    persist_run_manifest,
)


ENGINE_PROFILE = "mini"
DEFAULT_MODEL_PROFILE = ModelProfile.COMPACT
MINI_MANIFEST_SCHEMA_VERSION = 6
MINI_WORKLOAD_PROFILE = "text"
# The repaired guard runs its battery and semantic stages only with a full
# scope stack (domain, embedder, eps); a missing piece degrades admission to
# exact-hash only. Mini binds the parent HashingEmbedder (Session) and the
# parent's calibrated default radius here so kernel admission stays scoped
# rather than global - the old every-refuted-prior fallback is the exact
# mechanism that embargoed the bronze flat v1 repertoire.
MINI_NEAR_DUP_EPS: float | None = 0.35

# One constant, deterministic process-root run input.  Mini's problems are
# supplied per run() call, registered canonically in the event log, and its
# commitments come from admitted model candidates at runtime, so there is no
# frozen per-problem criterion set to bind — this record says exactly that
# instead of fabricating one.
MINI_RUN_INPUT_PROBLEM_ID = "minireason:process-root"
_MINI_RUN_INPUT_DESCRIPTION = (
    "MiniReason process root. Problems are supplied per run() invocation and "
    "registered canonically in the event log; commitments are compiled from "
    "admitted model candidates at runtime. This root binds no frozen input "
    "criteria and attaches no evidence."
)

# V6 authorities that only the parent's transactional controller can honor.
# Mini runs generate/check/rotate through the Harness primitive layer, so
# these fields stay absent — an omitted v6 authority field authorizes no
# transition, which is the honest declaration for this reduced engine.
_TRANSACTIONAL_ONLY_FIELDS = (
    "compact_recovery_policy",
    "contract_schema_repair_policy",
    "route_seat_behavioral_capability_plan",
    "route_seat_contract_decomposition_plan",
    "production_qualification_policy",
    "terminal_commitment_policy",
)


@dataclass(frozen=True, slots=True)
class CompatibilityKernel:
    """Immutable process bindings used by the mini control loop."""

    profile: ProfileSpec
    lease: EndpointLease
    wire_contract: WireContract[ConjecturerOutput]
    manifest: RunManifest


def mini_run_input() -> tuple[RunInputManifestV2, EvidenceDossierV1]:
    """Build mini's constant process-root run input and empty dossier.

    Deterministic by construction: rebinding the same root always reproduces
    byte-identical records, so a crash between run-input and manifest binding
    is recoverable through the parent's first-writer protocol.
    """

    dossier = EvidenceDossierV1.create(
        problem_ref=MINI_RUN_INPUT_PROBLEM_ID,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="minireason",
            acquisition_method="constant process-root declaration",
            note="MiniReason attaches no evidence; the dossier is empty.",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id=MINI_RUN_INPUT_PROBLEM_ID,
            description=_MINI_RUN_INPUT_DESCRIPTION,
            criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    return run_input, dossier


def _mini_control_plane_policy() -> ControlPlanePolicyV3:
    """The mandatory v6 control plane in its explicit minimal/disabled form."""

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
    )


def _new_manifest(
    profile: ProfileSpec,
    lease: EndpointLease,
    run_input_digest: str,
) -> RunManifest:
    """Compile MiniReason's secret-free schema-6 process manifest.

    The route matrix, presentation plan, source hash, and engine config all
    come from the parent compiler so mini cannot drift into a second
    manifest dialect.  The transactional-only authorities are then removed:
    mini's calls run through the Harness primitive layer, not the v6
    transaction controller, and pretending otherwise would be a lie the
    reduced loop cannot honor.
    """

    config = Config(
        engine_profile=ENGINE_PROFILE,
        model_profile=profile.name.value,
        roles={"conjecturer": lease.route.endpoint_spec()},
    )
    compiled = compile_run_manifest(
        config,
        engine_profile=ENGINE_PROFILE,
        model_profile=profile.name.value,
        rubric_policy="forbid",
        concurrency=profile.default_concurrency,
        schema_version=MINI_MANIFEST_SCHEMA_VERSION,
        workload_profile=MINI_WORKLOAD_PROFILE,
        control_plane_policy=_mini_control_plane_policy(),
        run_input_digest=run_input_digest,
    )
    payload = compiled.model_dump(mode="python", by_alias=False)
    for field in _TRANSACTIONAL_ONLY_FIELDS:
        payload[field] = None
    return RunManifest.model_validate(payload)


def _verify_existing(
    manifest: RunManifest,
    profile: ProfileSpec,
    lease: EndpointLease,
) -> None:
    if manifest.engine_profile != ENGINE_PROFILE:
        raise RouteFirewallError(
            "MINI_ROOT_ENGINE_MISMATCH: refusing to downgrade a non-mini run root"
        )
    if manifest.model_profile != profile.name.value:
        raise RouteFirewallError(
            "MINI_ROOT_PROFILE_MISMATCH: existing root is bound to "
            f"{manifest.model_profile!r}, requested {profile.name.value!r}"
        )
    routes = manifest.roles.get("conjecturer", ())
    if len(routes) != 1 or routes[0] != lease.route:
        raise RouteFirewallError(
            "MINI_ROOT_ROUTE_MISMATCH: existing root is bound to a different endpoint"
        )
    if manifest.rubric_policy != "forbid":
        raise RouteFirewallError(
            "MINI_ROOT_RUBRIC_POLICY_MISMATCH: MiniReason does not run rubric judging"
        )


def bind_mini_root(
    root: Path | str,
    endpoint: object,
    model_profile: str | ModelProfile | ProfileSpec = DEFAULT_MODEL_PROFILE,
) -> RunManifest:
    """Bind (or verify) one immutable v6 mini manifest on a run root.

    New roots receive, in order, the constant process run input and then the
    compiled schema-6 mini manifest — the exact interface later mini phases
    (advisory/scratch) should build on.  Existing v6 roots are verified
    against the requested route and profile; legacy pre-v6 roots fail closed
    in the parent loader with ``UNSUPPORTED_RUN_MANIFEST_VERSION`` and are
    never rewritten.
    """

    profile = get_profile(model_profile)
    lease = EndpointLease(
        role="conjecturer",
        seat=0,
        route=route_from_endpoint(endpoint),
    )
    root_path = Path(root)
    path = root_path / MANIFEST_NAME
    if path.exists():
        manifest = load_run_manifest(path)
        _verify_existing(manifest, profile, lease)
        return manifest
    run_input, dossier = mini_run_input()
    bind_run_input(run_input, dossier, root_path)
    manifest = _new_manifest(profile, lease, run_input.run_input_digest)
    persist_run_manifest(manifest, root_path)
    return manifest


def initialize(
    root: Path | str,
    endpoint: object,
    model_profile: str | ModelProfile | ProfileSpec = DEFAULT_MODEL_PROFILE,
) -> CompatibilityKernel:
    """Freeze MiniReason's route and compact transport before its first call."""

    profile = get_profile(model_profile)
    lease = EndpointLease(
        role="conjecturer",
        seat=0,
        route=route_from_endpoint(endpoint),
    )
    lease.verify(endpoint)
    manifest = bind_mini_root(root, endpoint, profile)
    # Mini does not preserve conjecturer references in its canonical candidate
    # path. Its compact schema therefore omits references entirely instead of
    # exposing raw ids or pretending an empty alias table is a usable contract.
    # Other explicitly selected profiles retain the shared selector.
    contract = (
        ReferenceFreeConjecturerWireContract()
        if profile.name == ModelProfile.COMPACT
        else wire_contract_for("conjecturer", ConjecturerOutput, profile.name)
    )
    return CompatibilityKernel(
        profile=profile,
        lease=lease,
        wire_contract=contract,
        manifest=manifest,
    )
