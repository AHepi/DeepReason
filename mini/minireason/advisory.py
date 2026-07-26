"""Manifest-bound access to DeepReason's canonical advisory machinery.

MiniReason keeps its reduced scheduler, but scratch objects and grounded final
views are not reduced-engine protocols.  This facade only binds a MiniReason
run to the parent implementation: canonical replay/storage, immutable scratch
objects, deterministic attention, and the two-stage bridge all remain owned by
``deepreason``.

Since the parent moved to the V6-only manifest loader, an advisory-capable
mini root is the phase-1 minimal schema-6 mini manifest (see
``minireason.compat``) with exactly two source policies switched on: the
advisory scratchpad and the ``grounded_two_stage`` bridge.  Everything else —
engine profile, the explicit minimal/disabled control plane, the constant
process-root run input, and the deliberate omission of the transactional-only
v6 authorities — is identical to the default mini manifest, and both are
compiled and validated by the parent compiler so mini never grows a second
manifest dialect.  Legacy pre-v6 advisory roots are never migrated: opening
one fails closed in the parent loader with ``UNSUPPORTED_RUN_MANIFEST_VERSION``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from deepreason.config import Config
from deepreason.evidence import bind_run_input
from deepreason.harness import Harness
from deepreason.llm.firewall import (
    EndpointLease,
    leases_from_manifest,
    route_from_endpoint,
)
from deepreason.llm.profiles import ModelProfile, ProfileSpec, get_profile
from deepreason.run_manifest import (
    MANIFEST_NAME,
    RunManifest,
    compile_run_manifest,
    load_run_manifest,
    persist_run_manifest,
)
from deepreason.scratch.attention import (
    AttentionPackV1,
    AttentionPlanner,
    AttentionRequestV1,
)
from deepreason.scratch.service import ScratchService

from minireason import compat


# The advisory variant of the mini source policy.  Values stay as small as the
# reduced loop honestly needs: bounded four-block packs with no cluster
# guides, keyword/recency retrieval without a semantic embedder, and a
# review-free two-stage bridge with the minimum one-repair schema budget.
_ADVISORY_SCRATCHPAD_SOURCE = {
    "enabled": True,
    "max_blocks_per_pack": 4,
    "max_guides_per_pack": 0,
    "semantic_retrieval": False,
    "coverage_slot_every_n_packs": 8,
}
_ADVISORY_BRIDGE_SOURCE = {
    "mode": "grounded_two_stage",
    "grounding_review": False,
    "max_schema_repair_attempts": 1,
    "max_grounding_repair_attempts": 0,
    "output_section_limit": 4,
}


class MiniAdvisoryError(ValueError):
    """A Mini run is not bound to the shared advisory contract."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _advisory_manifest(
    profile: ProfileSpec,
    lease: EndpointLease,
    run_input_digest: str,
) -> RunManifest:
    """Compile the scratch/bridge-enabled variant of the mini v6 manifest.

    This reuses the exact phase-1 recipe — parent compiler, mini control
    plane, then the transactional-authority strip — and differs from
    ``minireason.compat._new_manifest`` only in the two enabled source
    policies and the two extra bridge roles they require.  The grounded
    two-stage bridge needs frozen ``summarizer`` and ``thesis`` routes; mini
    has exactly one endpoint, so every role is seated on the same route.
    """

    spec = lease.route.endpoint_spec()
    config = Config(
        engine_profile=compat.ENGINE_PROFILE,
        model_profile=profile.name.value,
        scratchpad=_ADVISORY_SCRATCHPAD_SOURCE,
        bridge=_ADVISORY_BRIDGE_SOURCE,
        roles={"conjecturer": spec, "summarizer": spec, "thesis": spec},
    )
    compiled = compile_run_manifest(
        config,
        engine_profile=compat.ENGINE_PROFILE,
        model_profile=profile.name.value,
        rubric_policy="forbid",
        concurrency=profile.default_concurrency,
        schema_version=compat.MINI_MANIFEST_SCHEMA_VERSION,
        workload_profile=compat.MINI_WORKLOAD_PROFILE,
        control_plane_policy=compat._mini_control_plane_policy(),
        run_input_digest=run_input_digest,
    )
    payload = compiled.model_dump(mode="python", by_alias=False)
    for field in compat._TRANSACTIONAL_ONLY_FIELDS:
        payload[field] = None
    return RunManifest.model_validate(payload)


def bind_mini_advisory_root(
    root: Path | str,
    endpoint: object,
    model_profile: str | ModelProfile | ProfileSpec = compat.DEFAULT_MODEL_PROFILE,
) -> RunManifest:
    """Bind (or verify) one advisory-capable v6 mini manifest on a run root.

    New roots receive the constant mini process run input and then the
    compiled schema-6 advisory variant.  Existing v6 roots are verified
    against the requested route and profile exactly like ``bind_mini_root``
    and must already carry the advisory policies; legacy pre-v6 roots fail
    closed in the parent loader with ``UNSUPPORTED_RUN_MANIFEST_VERSION`` and
    are never rewritten.
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
        compat._verify_existing(manifest, profile, lease)
        _require_advisory_policies(manifest)
        return manifest
    run_input, dossier = compat.mini_run_input()
    bind_run_input(run_input, dossier, root_path)
    manifest = _advisory_manifest(profile, lease, run_input.run_input_digest)
    persist_run_manifest(manifest, root_path)
    return manifest


def _require_advisory_policies(manifest: RunManifest) -> None:
    """Reject rebinding an existing root that lacks the advisory policies."""

    scratch = manifest.scratch_policy
    if scratch is None or not scratch.enabled:
        raise MiniAdvisoryError(
            "MINI_ADVISORY_SCRATCH_DISABLED",
            "the bound manifest does not enable scratchpad access",
        )
    bridge = manifest.bridge_policy
    if bridge is None or bridge.mode != "grounded_two_stage":
        raise MiniAdvisoryError(
            "MINI_ADVISORY_BRIDGE_DISABLED",
            "the bound manifest does not enable the grounded two-stage bridge",
        )


@dataclass(frozen=True, slots=True)
class MiniAdvisorySession:
    """Thin MiniReason view over one canonical v6 mini run root.

    The facade deliberately has no object store, event writer, replay loader,
    ontology, validator, routing table, or repair loop of its own.  Callers may
    author scratch records through :attr:`scratch`; every resulting object and
    event is immediately readable by the full :class:`~deepreason.harness.Harness`.
    """

    root: Path
    manifest: RunManifest
    harness: Harness
    _scratch: ScratchService

    @classmethod
    def open(
        cls,
        root: Path | str,
        *,
        read_only: bool = False,
    ) -> "MiniAdvisorySession":
        """Open an already-bound MiniReason v6 run without migrating it.

        Legacy pre-v6 roots fail closed inside ``load_run_manifest`` with the
        parent's ``UNSUPPORTED_RUN_MANIFEST_VERSION``; this facade adds no
        bypass and never rewrites such a root.
        """

        root_path = Path(root)
        if not root_path.is_dir():
            raise MiniAdvisoryError(
                "MINI_ADVISORY_RUN_NOT_FOUND", "run root must already exist"
            )
        manifest = load_run_manifest(root_path / MANIFEST_NAME)
        if manifest.schema_version != compat.MINI_MANIFEST_SCHEMA_VERSION:
            raise MiniAdvisoryError(
                "MINI_ADVISORY_MANIFEST_V6_REQUIRED",
                "scratch and grounded bridge access requires RunManifest v6",
            )
        if manifest.engine_profile != "mini":
            raise MiniAdvisoryError(
                "MINI_ADVISORY_ENGINE_MISMATCH",
                "the bound manifest does not select the mini engine",
            )
        harness = Harness(root_path, read_only=read_only)
        return cls(
            root=root_path,
            manifest=manifest,
            harness=harness,
            _scratch=ScratchService(harness),
        )

    @property
    def scratch(self) -> ScratchService:
        """Return the shared service only when the manifest enables it."""

        policy = self.manifest.scratch_policy
        if policy is None or not policy.enabled:
            raise MiniAdvisoryError(
                "MINI_ADVISORY_SCRATCH_DISABLED",
                "the bound manifest does not enable scratchpad access",
            )
        return self._scratch

    def plan_attention(
        self,
        request: AttentionRequestV1 | dict,
        *,
        pack_count: int | None = None,
    ) -> AttentionPackV1:
        """Plan one bounded pack using the manifest's canonical policy."""

        policy = self.manifest.scratch_policy
        assert policy is not None  # checked by the service property below
        planner = AttentionPlanner(self.scratch, policy.attention_policy())
        return planner.plan(
            AttentionRequestV1.model_validate(request),
            pack_count=pack_count,
        )

    def _require_manifest_adapter(
        self,
        adapter,
        role: str,
        *,
        purpose: str,
    ) -> None:
        """Reject adapters that are not frozen to this exact manifest route."""

        if adapter is None or not callable(getattr(adapter, "has_role", None)):
            raise MiniAdvisoryError(
                "MINI_ADVISORY_ADAPTER_REQUIRED",
                f"{purpose} requires the canonical LLM adapter",
            )
        if not adapter.has_role(role):
            raise MiniAdvisoryError(
                "MINI_ADVISORY_ROLE_UNAVAILABLE",
                f"{purpose} requires manifest role {role!r}",
            )
        expected: tuple[EndpointLease, ...] = leases_from_manifest(self.manifest).get(
            role, ()
        )
        observed = tuple(getattr(adapter, "leases", {}).get(role, ()))
        if not expected or observed != expected:
            raise MiniAdvisoryError(
                "MINI_ADVISORY_ROUTE_MISMATCH",
                f"{purpose} adapter is not frozen to manifest role {role!r}",
            )
        blob_store = getattr(adapter, "blobs", None)
        adapter_blob_root = getattr(blob_store, "root", None)
        if blob_store is not self.harness.blobs and (
            adapter_blob_root is None
            or Path(adapter_blob_root).resolve()
            != self.harness.blobs.root.resolve()
        ):
            raise MiniAdvisoryError(
                "MINI_ADVISORY_BLOB_STORE_MISMATCH",
                f"{purpose} adapter does not use this run's canonical blob store",
            )
        policy = self.manifest.bridge_policy
        assert policy is not None
        if getattr(adapter, "retry_max", None) != policy.max_schema_repair_attempts:
            raise MiniAdvisoryError(
                "MINI_ADVISORY_REPAIR_POLICY_MISMATCH",
                f"{purpose} adapter does not use the manifest repair bound",
            )
        if getattr(adapter, "base_model_profile", None) != self.manifest.model_profile:
            raise MiniAdvisoryError(
                "MINI_ADVISORY_MODEL_PROFILE_MISMATCH",
                f"{purpose} adapter does not use the manifest model profile",
            )

    def build_bridge(
        self,
        problem_id: str,
        target: Literal["thesis", "summary", "answer"],
        *,
        stage_a_adapter,
        composition_adapter=None,
        review_adapter=None,
        repair_adapter=None,
        attention_pack: AttentionPackV1 | None = None,
    ):
        """Build one canonical grounded final view under the bound policy.

        Adapters remain explicit so offline/scripted Mini workloads do not
        trigger route construction or provider access.  Each adapter is still
        required to carry the exact leases, model profile, and repair ceiling
        frozen in the RunManifest.
        """

        policy = self.manifest.bridge_policy
        if self.manifest.workload_profile != "text":
            raise MiniAdvisoryError(
                "MINI_ADVISORY_TEXT_WORKLOAD_REQUIRED",
                "the grounded bridge requires a text workload",
            )
        if policy is None or policy.mode != "grounded_two_stage":
            raise MiniAdvisoryError(
                "MINI_ADVISORY_BRIDGE_DISABLED",
                "the bound manifest does not enable the grounded two-stage bridge",
            )
        if attention_pack is not None:
            scratch_policy = self.manifest.scratch_policy
            if scratch_policy is None or not scratch_policy.enabled:
                raise MiniAdvisoryError(
                    "MINI_ADVISORY_SCRATCH_DISABLED",
                    "an advisory attention pack requires enabled scratch policy",
                )
            attention_pack = AttentionPackV1.model_validate(attention_pack)
            if (
                len(attention_pack.blocks) > scratch_policy.max_blocks_per_pack
                or len(attention_pack.cluster_guides)
                > scratch_policy.max_guides_per_pack
            ):
                raise MiniAdvisoryError(
                    "MINI_ADVISORY_ATTENTION_POLICY_MISMATCH",
                    "the attention pack exceeds the bound manifest limits",
                )
        composer = composition_adapter or stage_a_adapter
        self._require_manifest_adapter(
            stage_a_adapter, policy.ledger_role, purpose="claim-ledger construction"
        )
        self._require_manifest_adapter(
            composer, policy.composer_role, purpose="final composition"
        )
        if policy.grounding_review:
            self._require_manifest_adapter(
                review_adapter, policy.reviewer_role, purpose="grounding review"
            )
            if policy.max_grounding_repair_attempts:
                self._require_manifest_adapter(
                    repair_adapter,
                    policy.grounding_repair_role,
                    purpose="grounding repair",
                )

        return self.harness.build_bridge(
            problem_id,
            target,
            policy.workflow_policy(),
            run_manifest_digest=self.manifest.sha256,
            stage_a_adapter=stage_a_adapter,
            composition_adapter=composer,
            review_adapter=(review_adapter if policy.grounding_review else None),
            repair_adapter=(
                repair_adapter
                if policy.grounding_review
                and policy.max_grounding_repair_attempts
                else None
            ),
            attention_pack=attention_pack,
            maximum_sections=policy.output_section_limit,
            formatting_profile=policy.target_profile,
        )


__all__ = [
    "MiniAdvisoryError",
    "MiniAdvisorySession",
    "bind_mini_advisory_root",
]
