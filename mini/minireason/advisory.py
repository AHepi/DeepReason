"""Manifest-bound access to DeepReason's canonical advisory machinery.

MiniReason keeps its reduced scheduler, but scratch objects and grounded final
views are not reduced-engine protocols.  This facade only binds a MiniReason
run to the parent implementation: canonical replay/storage, immutable scratch
objects, deterministic attention, and the two-stage bridge all remain owned by
``deepreason``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from deepreason.harness import Harness
from deepreason.llm.firewall import EndpointLease, leases_from_manifest
from deepreason.run_manifest import MANIFEST_NAME, RunManifest, load_run_manifest
from deepreason.scratch.attention import (
    AttentionPackV1,
    AttentionPlanner,
    AttentionRequestV1,
)
from deepreason.scratch.service import ScratchService


class MiniAdvisoryError(ValueError):
    """A Mini run is not bound to the shared v3 advisory contract."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class MiniAdvisorySession:
    """Thin MiniReason view over one canonical v3 run root.

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
        """Open an already-bound MiniReason v3 run without migrating it."""

        root_path = Path(root)
        if not root_path.is_dir():
            raise MiniAdvisoryError(
                "MINI_ADVISORY_RUN_NOT_FOUND", "run root must already exist"
            )
        manifest = load_run_manifest(root_path / MANIFEST_NAME)
        if manifest.schema_version != 3:
            raise MiniAdvisoryError(
                "MINI_ADVISORY_MANIFEST_V3_REQUIRED",
                "scratch and grounded bridge access requires RunManifest v3",
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


__all__ = ["MiniAdvisoryError", "MiniAdvisorySession"]
