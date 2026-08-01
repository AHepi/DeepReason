"""Status-neutral jolt actions and matched-state branch manifests.

The pilot's treatment surface is intentionally narrow.  Actions can shape a
conjecturer pack or choose a pre-existing problem for a fixed call index.  They
cannot create artifacts, warrants, graph edges, or status changes.  Branch
freezing copies a quiescent root and proves equality before any continuation;
it does not claim provider outputs are deterministic counterfactual replays.
"""

from __future__ import annotations

import json
import shutil
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.harness import Harness
from deepreason.ontology import Status


ACTION_SIGNAL = "jolt-action"
FALSE_TRIGGER_SIGNAL = "jolt-false-trigger"
BRANCH_MANIFEST_NAME = "jolt-branch-manifest.json"


class JoltError(ValueError):
    """A treatment or matched branch violates the frozen pilot contract."""


class JoltArm(str, Enum):
    J0 = "J0"
    J1 = "J1"
    J2 = "J2"
    J3 = "J3"
    J4 = "J4"
    J5 = "J5"
    J6 = "J6"
    J7 = "J7"


class JoltDiagnosis(str, Enum):
    HARD_ORBIT = "hard_orbit"
    SOFT_EXHAUSTION = "soft_exhaustion"
    HEALTHY = "healthy"


class PublicVerifierFailure(BaseModel):
    """A public failure class, never a withheld test or expected output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=1, max_length=160)
    source_receipt: str = Field(pattern=r"^[0-9a-f]{64}$")
    visibility: Literal["public"] = "public"

    @field_validator("label")
    @classmethod
    def _no_hidden_outcome_content(cls, value: str) -> str:
        lowered = value.casefold()
        forbidden = (
            "hidden test",
            "withheld test",
            "withheld input",
            "expected output",
            "private test",
        )
        if "\n" in value or any(marker in lowered for marker in forbidden):
            raise ValueError("JOLT_VERIFIER_OUTCOME_LEAKAGE")
        return value.strip()


class JoltAction(BaseModel):
    """A process-only action. Extra fields fail, so authority cannot be smuggled in."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_id: Literal["deepreason-jolt-action-v1"] = Field(
        default="deepreason-jolt-action-v1", alias="schema"
    )
    arm: JoltArm
    diagnosis: JoltDiagnosis
    original_problem_id: str = Field(min_length=1)
    prompt_context: str = ""
    suppressed_artifact_ids: tuple[str, ...] = ()
    refuted_target_id: str | None = None
    focus_problem_id: str | None = None
    focus_calls: int = Field(default=0, ge=0, le=5)
    return_after_calls: int = Field(default=0, ge=0, le=5)
    public_failure_receipts: tuple[str, ...] = ()

    @field_validator("suppressed_artifact_ids", "public_failure_receipts")
    @classmethod
    def _deduplicated(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("jolt action references must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _arm_contract(self):
        if self.arm in {JoltArm.J5, JoltArm.J7}:
            raise ValueError("JOLT_ARM_DEFERRED")
        if self.arm == JoltArm.J0 and any(
            (
                self.prompt_context,
                self.suppressed_artifact_ids,
                self.refuted_target_id,
                self.focus_problem_id,
                self.focus_calls,
                self.return_after_calls,
                self.public_failure_receipts,
            )
        ):
            raise ValueError("J0 must be an inert no-intervention action")
        if self.arm == JoltArm.J1 and self.diagnosis not in {
            JoltDiagnosis.HARD_ORBIT,
            JoltDiagnosis.HEALTHY,
        }:
            raise ValueError("J1 is not a soft-exhaustion primary arm")
        if self.arm == JoltArm.J1:
            if self.suppressed_artifact_ids and not self.refuted_target_id:
                raise ValueError("J1 suppression requires its refuted target")
        elif self.refuted_target_id or self.suppressed_artifact_ids:
            raise ValueError("only J1 may suppress a refuted lineage")
        if self.arm == JoltArm.J2:
            if self.diagnosis not in {JoltDiagnosis.HARD_ORBIT, JoltDiagnosis.HEALTHY}:
                raise ValueError("J2 is not a soft-exhaustion primary arm")
            if (
                not self.focus_problem_id
                or self.focus_problem_id == self.original_problem_id
                or self.focus_calls != 2
                or self.return_after_calls != 2
            ):
                raise ValueError("J2 requires a distinct pre-existing problem for calls 1-2")
        elif self.focus_problem_id or self.focus_calls or self.return_after_calls:
            raise ValueError("only J2 may change problem focus")
        if self.arm in {JoltArm.J3, JoltArm.J4} and self.diagnosis not in {
            JoltDiagnosis.SOFT_EXHAUSTION,
            JoltDiagnosis.HEALTHY,
        }:
            raise ValueError(f"{self.arm.value} is not a hard-orbit primary arm")
        if self.arm == JoltArm.J4 and not self.public_failure_receipts:
            raise ValueError("J4 requires a public verifier failure receipt")
        if self.arm != JoltArm.J4 and self.public_failure_receipts:
            raise ValueError("only J4 may carry public failure receipts")
        return self

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json", by_alias=True)))


STANCE_ROTATIONS = {
    "mechanism-first": "counterexample-first",
    "counterexample-first": "mechanism-first",
    "local-repair": "architectural-replacement",
    "architectural-replacement": "local-repair",
    "optimise-current": "different-representation",
    "different-representation": "optimise-current",
    "proof-first": "adversarial-instance-first",
    "adversarial-instance-first": "proof-first",
}

REPRESENTATION_TEMPLATES = {
    "code": "Restate the next proposal as state, invariant, transition, and executable check.",
    "finite": "Restate the next proposal as a finite-domain table, recurrence, or exhaustive predicate.",
    "simulation": "Restate the next proposal as state variables, transition rule, seed, and deterministic score.",
    "formal": "Restate the next proposal as assumptions, obligations, and a machine-checkable witness shape.",
    "browser": "Restate the next proposal as page state, deterministic action sequence, and observable postconditions.",
}

COMPLEMENT_PROMPT = (
    "Avoid the modal continuation of the displayed approaches; propose a "
    "structurally different attempt."
)


def build_jolt_action(
    arm: JoltArm,
    *,
    diagnosis: JoltDiagnosis,
    original_problem_id: str,
    current_stance: str | None = None,
    suppressed_artifact_ids: tuple[str, ...] = (),
    refuted_target_id: str | None = None,
    related_problem_id: str | None = None,
    domain: str | None = None,
    public_failures: tuple[PublicVerifierFailure, ...] = (),
) -> JoltAction:
    """Compile a deterministic action from pre-randomisation public inputs."""
    if arm in {JoltArm.J5, JoltArm.J7}:
        raise JoltError("JOLT_ARM_DEFERRED")
    if arm == JoltArm.J0:
        return JoltAction(
            arm=arm, diagnosis=diagnosis, original_problem_id=original_problem_id
        )
    if arm == JoltArm.J1:
        if current_stance not in STANCE_ROTATIONS:
            raise JoltError("JOLT_STANCE_MAPPING_MISSING")
        rotated = STANCE_ROTATIONS[current_stance]
        return JoltAction(
            arm=arm,
            diagnosis=diagnosis,
            original_problem_id=original_problem_id,
            prompt_context=(
                f"STANCE ROTATION: replace {current_stance} with {rotated} for "
                "this five-call branch. Change the governing search stance, not "
                "the truth or verifier standard."
            ),
            suppressed_artifact_ids=tuple(sorted(suppressed_artifact_ids)),
            refuted_target_id=refuted_target_id,
        )
    if arm == JoltArm.J2:
        if related_problem_id is None:
            raise JoltError("JOLT_RELATED_PROBLEM_REQUIRED")
        return JoltAction(
            arm=arm,
            diagnosis=diagnosis,
            original_problem_id=original_problem_id,
            focus_problem_id=related_problem_id,
            focus_calls=2,
            return_after_calls=2,
        )
    if arm == JoltArm.J3:
        if domain not in REPRESENTATION_TEMPLATES:
            raise JoltError("JOLT_REPRESENTATION_TEMPLATE_MISSING")
        return JoltAction(
            arm=arm,
            diagnosis=diagnosis,
            original_problem_id=original_problem_id,
            prompt_context=(
                "REPRESENTATION RESET: " + REPRESENTATION_TEMPLATES[domain]
                + " Do not add premises or change the verifier."
            ),
        )
    if arm == JoltArm.J4:
        if not public_failures:
            raise JoltError("JOLT_PUBLIC_FAILURE_REQUIRED")
        chosen = min(public_failures, key=lambda item: (item.label, item.source_receipt))
        return JoltAction(
            arm=arm,
            diagnosis=diagnosis,
            original_problem_id=original_problem_id,
            prompt_context=(
                f"VERIFIER-DIRECTED CHALLENGE: the public deterministic failure "
                f"class is '{chosen.label}'. Propose a design based on a different "
                "invariant that changes this named failure mode; do not patch the "
                "current loop or infer hidden tests."
            ),
            public_failure_receipts=(chosen.source_receipt,),
        )
    if arm == JoltArm.J6:
        return JoltAction(
            arm=arm,
            diagnosis=diagnosis,
            original_problem_id=original_problem_id,
            prompt_context=COMPLEMENT_PROMPT,
        )
    raise JoltError(f"JOLT_ARM_UNSUPPORTED:{arm.value}")


def problem_for_post_trigger_call(action: JoltAction, call_index: int) -> str:
    """The fixed five-call focus schedule; no outcome-dependent turnover."""
    if call_index < 0 or call_index >= 5:
        raise JoltError("JOLT_CALL_INDEX_OUT_OF_RANGE")
    if action.arm == JoltArm.J2 and call_index < action.focus_calls:
        assert action.focus_problem_id is not None
        return action.focus_problem_id
    return action.original_problem_id


def suppressible_lineage_exemplars(harness, refuted_target_id: str) -> tuple[str, ...]:
    """Accepted exemplars sharing the refuted target's recorded school."""
    target = harness.state.artifacts.get(refuted_target_id)
    if target is None or harness.state.status.get(refuted_target_id) != Status.REFUTED:
        raise JoltError("JOLT_REFUTED_TARGET_REQUIRED")
    school = target.provenance.school
    if not school:
        return ()
    return tuple(
        sorted(
            artifact_id
            for artifact_id, artifact in harness.state.artifacts.items()
            if artifact.provenance.school == school
            and harness.state.status.get(artifact_id) == Status.ACCEPTED
        )
    )


def validate_action_against_state(harness, action: JoltAction) -> None:
    if action.original_problem_id not in harness.state.problems:
        raise JoltError("JOLT_ORIGINAL_PROBLEM_MISSING")
    if action.focus_problem_id and action.focus_problem_id not in harness.state.problems:
        raise JoltError("JOLT_RELATED_PROBLEM_NOT_PREEXISTING")
    if action.focus_problem_id:
        from deepreason.scheduler.scheduler import problem_family_key

        if problem_family_key(
            harness.state, action.focus_problem_id
        ) != problem_family_key(harness.state, action.original_problem_id):
            raise JoltError("JOLT_RELATED_PROBLEM_FAMILY_MISMATCH")
    refuted_school = None
    if action.refuted_target_id:
        target = harness.state.artifacts.get(action.refuted_target_id)
        if (
            target is None
            or harness.state.status.get(action.refuted_target_id) != Status.REFUTED
        ):
            raise JoltError("JOLT_REFUTED_TARGET_REQUIRED")
        refuted_school = target.provenance.school
    for artifact_id in action.suppressed_artifact_ids:
        artifact = harness.state.artifacts.get(artifact_id)
        if artifact is None or harness.state.status.get(artifact_id) != Status.ACCEPTED:
            raise JoltError("JOLT_SUPPRESSED_EXEMPLAR_NOT_ACCEPTED")
        if not refuted_school or artifact.provenance.school != refuted_school:
            raise JoltError("JOLT_SUPPRESSED_EXEMPLAR_LINEAGE_MISMATCH")


def record_jolt_action(harness, action: JoltAction):
    validate_action_against_state(harness, action)
    payload = json.dumps(
        action.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        separators=(",", ":"),
    )
    return harness.record_measure(inputs=[ACTION_SIGNAL, payload])


def record_false_trigger_sample(
    harness, *, state_digest: str, diagnosis_arm_set: str, sample_seed: str
):
    payload = json.dumps(
        {
            "diagnosis_arm_set": diagnosis_arm_set,
            "sample_seed": sample_seed,
            "state_digest": state_digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return harness.record_measure(inputs=[FALSE_TRIGGER_SIGNAL, payload])


class BranchBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conjecturer_calls: Literal[5] = 5
    prompt_tokens: Literal[25000] = 25000
    completion_tokens: Literal[10000] = 10000


class BranchSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    arm: JoltArm
    branch_id: str = Field(pattern=r"^branch-[0-9]{2}-J[0-7]$")
    branch_seed: str = Field(pattern=r"^[0-9a-f]{64}$")
    execution_order: int = Field(ge=0)
    budget: BranchBudget


class MatchedBranchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_id: Literal["deepreason-matched-jolt-plan-v1"] = Field(
        default="deepreason-matched-jolt-plan-v1", alias="schema"
    )
    experiment_manifest_plan_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_root: str = Field(min_length=1)
    source_state_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_log_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_event_seq: int = Field(ge=0)
    run_manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    route_matrix_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    verifier_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    functional_evaluator_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    embedder_fingerprint: dict[str, str]
    diagnosis: JoltDiagnosis
    trigger_receipt_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    original_problem_id: str = Field(min_length=1)
    related_problem_id: str | None = None
    branch_order_seed: str = Field(min_length=1)
    branches: tuple[BranchSpec, ...]
    exact_counterfactual_replay_claimed: Literal[False] = False

    @field_validator("embedder_fingerprint")
    @classmethod
    def _complete_embedder_fingerprint(cls, value):
        if set(value) != {"model", "version", "sentinel"} or any(
            not value[key] for key in value
        ):
            raise ValueError("JOLT_EXPECTED_EMBEDDER_FINGERPRINT_INVALID")
        return dict(value)

    @model_validator(mode="after")
    def _matched_contract(self):
        arms = [branch.arm for branch in self.branches]
        if len(arms) != len(set(arms)) or JoltArm.J0 not in arms:
            raise ValueError("matched branches require unique arms including J0")
        if len({branch.budget for branch in self.branches}) != 1:
            raise ValueError("JOLT_BUDGET_MISMATCH")
        orders = sorted(branch.execution_order for branch in self.branches)
        if orders != list(range(len(self.branches))):
            raise ValueError("branch execution order must be contiguous")
        return self

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json", by_alias=True)))


def _file_digest(path: Path) -> str:
    return sha256_hex(path.read_bytes()) if path.exists() else sha256_hex(b"")


def _tree_digest(path: Path) -> str:
    if not path.exists():
        return sha256_hex(b"")
    entries = {
        str(item.relative_to(path)): sha256_hex(item.read_bytes())
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }
    return sha256_hex(canonical_json(entries))


def root_state_digest(root: Path | str) -> str:
    """Digest every persisted input that can affect replay or admission."""
    root = Path(root)
    harness = Harness(root, read_only=True)
    process_files = (
        "relapse.log.jsonl",
        "run-manifest.json",
        "run-manifest.sha256",
        "checkpoint.json",
        "run-stop.json",
        "continuations.jsonl",
    )
    payload = {
        "state": harness.state.model_dump(mode="json"),
        "commitments": {
            key: value.model_dump(mode="json")
            for key, value in sorted(harness.commitments.items())
        },
        "warrants": {
            key: value.model_dump(mode="json")
            for key, value in sorted(harness.warrants.items())
        },
        "event_seq": harness._next_seq,
        "log_digest": _file_digest(root / "log.jsonl"),
        "object_tree_digest": _tree_digest(root / "objects"),
        "blob_tree_digest": _tree_digest(root / "blobs"),
        "process_file_digests": {
            name: _file_digest(root / name) for name in process_files
        },
    }
    return sha256_hex(canonical_json(payload))


def _stable_order(arms: tuple[JoltArm, ...], seed: str) -> list[JoltArm]:
    return sorted(
        arms,
        key=lambda arm: sha256_hex(f"{seed}\0{arm.value}".encode("utf-8")),
    )


def plan_matched_branches(
    source_root: Path | str,
    *,
    arms: tuple[JoltArm, ...],
    diagnosis: JoltDiagnosis,
    original_problem_id: str,
    branch_order_seed: str,
    experiment_manifest_plan_digest: str,
    run_manifest_digest: str,
    route_matrix_digest: str,
    verifier_fingerprint: str,
    functional_evaluator_fingerprint: str,
    embedder_fingerprint: dict[str, str],
    trigger_receipt_digest: str,
    related_problem_id: str | None = None,
) -> MatchedBranchPlan:
    """Freeze one source state and deterministically randomise branch order."""
    root = Path(source_root)
    if not root.exists():
        raise JoltError("JOLT_SOURCE_ROOT_MISSING")
    if len(arms) != len(set(arms)) or JoltArm.J0 not in arms:
        raise JoltError("JOLT_NO_J0_CONTROL")
    if diagnosis == JoltDiagnosis.HARD_ORBIT and set(arms) != {
        JoltArm.J0,
        JoltArm.J1,
        JoltArm.J2,
        JoltArm.J6,
    }:
        raise JoltError("JOLT_HARD_ARM_SET_MISMATCH")
    if diagnosis == JoltDiagnosis.SOFT_EXHAUSTION and set(arms) != {
        JoltArm.J0,
        JoltArm.J3,
        JoltArm.J4,
        JoltArm.J6,
    }:
        raise JoltError("JOLT_SOFT_ARM_SET_MISMATCH")
    if JoltArm.J2 in arms and not related_problem_id:
        raise JoltError("JOLT_RELATED_PROBLEM_REQUIRED")
    if original_problem_id not in Harness(root, read_only=True).state.problems:
        raise JoltError("JOLT_ORIGINAL_PROBLEM_MISSING")
    if related_problem_id and related_problem_id not in Harness(root, read_only=True).state.problems:
        raise JoltError("JOLT_RELATED_PROBLEM_NOT_PREEXISTING")
    source_state = Harness(root, read_only=True).state
    if related_problem_id:
        from deepreason.scheduler.scheduler import problem_family_key

        if problem_family_key(source_state, related_problem_id) != problem_family_key(
            source_state, original_problem_id
        ):
            raise JoltError("JOLT_RELATED_PROBLEM_FAMILY_MISMATCH")

    ordered = _stable_order(arms, branch_order_seed)
    budget = BranchBudget()
    branches = tuple(
        BranchSpec(
            arm=arm,
            branch_id=f"branch-{index:02d}-{arm.value}",
            branch_seed=sha256_hex(
                f"{branch_order_seed}\0{arm.value}\0{index}".encode("utf-8")
            ),
            execution_order=index,
            budget=budget,
        )
        for index, arm in enumerate(ordered)
    )
    return MatchedBranchPlan(
        experiment_manifest_plan_digest=experiment_manifest_plan_digest,
        source_root=str(root.resolve()),
        source_state_digest=root_state_digest(root),
        source_log_digest=_file_digest(root / "log.jsonl"),
        source_event_seq=Harness(root, read_only=True)._next_seq,
        run_manifest_digest=run_manifest_digest,
        route_matrix_digest=route_matrix_digest,
        verifier_fingerprint=verifier_fingerprint,
        functional_evaluator_fingerprint=functional_evaluator_fingerprint,
        embedder_fingerprint=dict(embedder_fingerprint),
        diagnosis=diagnosis,
        trigger_receipt_digest=trigger_receipt_digest,
        original_problem_id=original_problem_id,
        related_problem_id=related_problem_id,
        branch_order_seed=branch_order_seed,
        branches=branches,
    )


def materialize_matched_branches(
    plan: MatchedBranchPlan, destination: Path | str
) -> tuple[Path, ...]:
    """Copy the quiescent state once per arm and verify pre-jolt equality."""
    source = Path(plan.source_root)
    if root_state_digest(source) != plan.source_state_digest:
        raise JoltError("JOLT_SOURCE_STATE_ADVANCED")
    if _file_digest(source / "log.jsonl") != plan.source_log_digest:
        raise JoltError("JOLT_SOURCE_LOG_ADVANCED")
    target = Path(destination)
    if target.exists():
        raise JoltError("JOLT_BRANCH_DESTINATION_EXISTS")
    target.mkdir(parents=True)
    created: list[Path] = []
    for branch in sorted(plan.branches, key=lambda item: item.execution_order):
        branch_root = target / branch.branch_id
        shutil.copytree(source, branch_root)
        if root_state_digest(branch_root) != plan.source_state_digest:
            raise JoltError("JOLT_BRANCH_STATE_MISMATCH")
        manifest = {
            "schema": "deepreason-jolt-branch-manifest-v1",
            "plan_digest": plan.digest,
            "source_state_digest": plan.source_state_digest,
            "source_log_digest": plan.source_log_digest,
            "source_event_seq": plan.source_event_seq,
            "run_manifest_digest": plan.run_manifest_digest,
            "route_matrix_digest": plan.route_matrix_digest,
            "verifier_fingerprint": plan.verifier_fingerprint,
            "functional_evaluator_fingerprint": plan.functional_evaluator_fingerprint,
            "embedder_fingerprint": plan.embedder_fingerprint,
            "diagnosis": plan.diagnosis.value,
            "trigger_receipt_digest": plan.trigger_receipt_digest,
            "arm": branch.arm.value,
            "branch_seed": branch.branch_seed,
            "branch_execution_order": branch.execution_order,
            "original_problem_id": plan.original_problem_id,
            "related_problem_id": plan.related_problem_id,
            "budget": branch.budget.model_dump(mode="json"),
            "exact_counterfactual_replay_claimed": False,
        }
        (branch_root / BRANCH_MANIFEST_NAME).write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        created.append(branch_root)
    return tuple(created)


class PilotPreflightReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    preregistration_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    workload_receipt_digests: tuple[str, ...]
    embedder_fingerprint: dict[str, str]
    judge_tokens: Literal[0] = 0
    capture_responses: Literal[False] = False
    controller_present: Literal[False] = False


def _mode_value(value) -> str:
    return str(getattr(value, "value", value))


def preflight_pilot_runtime(
    *,
    manifest,
    config,
    embedder,
    expected_embedder_fingerprint: dict[str, str],
    preregistration_digest: str,
    committed_preregistration_digest: str,
    workload_receipt_digests: tuple[str, ...],
    capture_responses: bool,
    controller_present: bool,
) -> PilotPreflightReceipt:
    """Fail before endpoint construction when the causal or authority fence drifts."""
    if preregistration_digest != committed_preregistration_digest:
        raise JoltError("JOLT_PREREG_NOT_COMMITTED")
    if not re_full_digest(preregistration_digest):
        raise JoltError("JOLT_PREREG_DIGEST_INVALID")
    if not workload_receipt_digests or any(
        not re_full_digest(value) for value in workload_receipt_digests
    ):
        raise JoltError("JOLT_WORKLOAD_RECEIPTS_MISSING")
    if manifest.schema_version != 2 or manifest.workload_profile not in {"code", "formal"}:
        raise JoltError("JOLT_SCHEMA_V2_VERIFIER_WORKLOAD_REQUIRED")
    active_roles = {role for role, routes in manifest.roles.items() if routes}
    if manifest.rubric_policy != "forbid" or active_roles != {"conjecturer"}:
        raise JoltError("JOLT_JUDGE_ROUTE_FORBIDDEN")
    zero_fields = {
        "ARG_CRIT_PER_CYCLE": config.ARG_CRIT_PER_CYCLE,
        "RUBRIC_TRIALS_PER_ARTIFACT": config.RUBRIC_TRIALS_PER_ARTIFACT,
        "ADVISORY_TRIALS_PER_CYCLE": config.ADVISORY_TRIALS_PER_CYCLE,
        "PROP_PROPOSE_PERIOD": config.PROP_PROPOSE_PERIOD,
        "VISION_CRIT_PER_CYCLE": config.VISION_CRIT_PER_CYCLE,
    }
    if any(value != 0 for value in zero_fields.values()):
        raise JoltError("JOLT_ADVISORY_BUDGET_NONZERO")
    authority_fields = (
        config.ARGUMENTATIVE_AUTHORITY,
        config.TEXT_RUBRIC_AUTHORITY,
        config.PAIRWISE_AUTHORITY,
        config.INFRASTRUCTURE_REVIEW_AUTHORITY,
    )
    if any(_mode_value(value) != "observe_only" for value in authority_fields):
        raise JoltError("JOLT_STATUS_AUTHORITY_FORBIDDEN")
    if config.CALIBRATION_RECEIPT is not None:
        raise JoltError("JOLT_CALIBRATION_RECEIPT_FORBIDDEN")
    if config.SPEC_INJECTION:
        raise JoltError("JOLT_SPEC_INJECTION_ACTIVE")
    if config.CONTROLLER or controller_present:
        raise JoltError("JOLT_CONTROLLER_ACTIVE")
    if capture_responses:
        raise JoltError("JOLT_CAPTURE_RESPONSE_ACTIVE")
    if config.RESEARCH_BACKEND is not None:
        raise JoltError("JOLT_RESEARCH_ACTIVE")
    if config.EMBEDDER_FAILURE_POLICY != "error":
        raise JoltError("JOLT_EMBEDDER_FALLBACK_FORBIDDEN")
    from deepreason.views.jolt_signals import require_embedder_fingerprint

    fingerprint = require_embedder_fingerprint(embedder, expected_embedder_fingerprint)
    return PilotPreflightReceipt(
        manifest_digest=manifest.sha256,
        preregistration_digest=preregistration_digest,
        workload_receipt_digests=tuple(workload_receipt_digests),
        embedder_fingerprint=fingerprint,
    )


def re_full_digest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
