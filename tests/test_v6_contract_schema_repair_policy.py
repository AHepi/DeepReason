"""Frozen per-contract schema-repair authority in new v6 manifests."""

import json

import pytest

from deepreason.bridge.repair import GroundingRepairWireV1
from deepreason.bridge.review import GroundingVerdictWireV1
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.llm.wire import DirectWireContract
from deepreason.ontology import Commitment
from deepreason.run_manifest import (
    CompactRecoveryPolicyV1,
    ContractSchemaRepairGrantV1,
    ContractSchemaRepairPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    RunManifestError,
    ScratchAuthoringPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
    load_run_manifest,
    write_run_manifest,
)
from tests.test_run_input_v6_commitments import (
    _bind_v2,
    _context_policy,
    _school_execution,
)


STAMP = "2026-07-20T00:00:00Z"
CORE_CONTRACTS = (
    "batch-critic.v2",
    "conjecturer.atomic-candidate.v1",
    "conjecturer.turn.v6",
    "critic.atomic-target.v1",
)
SCRATCH_CONTRACTS = (
    "scratch.block.compact.v1",
    "scratch.block.minimal.v1",
    "scratch.cluster-guide.compact.v1",
    "scratch.cluster-guide.minimal.v1",
    "scratch.link.compact.v1",
    "scratch.link.minimal.v1",
)
BRIDGE_CONTRACTS = (
    "bridge.composition-batch.v1",
    "bridge.composition.v2",
    "bridge.ledger-batch.v1",
    "bridge.ledger.v3",
)
REVIEW_CONTRACTS = tuple(
    sorted(
        (
            DirectWireContract(GroundingRepairWireV1).contract_id,
            DirectWireContract(GroundingVerdictWireV1).contract_id,
        )
    )
)
NONEXISTENT_REVIEW_CONTRACTS = (
    "grounding-repair.direct.v1",
    "grounding-review.direct.v1",
)


def _route(role: str) -> dict:
    return {
        "endpoint_id": f"{role}-repair-policy",
        "endpoint": f"mock://{role}-repair-policy",
        "model": f"offline-{role}",
        "provider": "mock",
        "family": "offline",
        "max_tokens": 64,
    }


def _scratch_authoring(enabled: bool) -> ScratchAuthoringPolicyV1:
    if not enabled:
        return ScratchAuthoringPolicyV1()
    return ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=2,
        maximum_revisions_per_turn=2,
        maximum_links_per_turn=2,
        maximum_unresolved_questions_per_turn=2,
        maximum_cluster_suggestions_per_turn=2,
        maximum_total_bytes=64 * 1024,
    )


def _control(*, scratch_authoring: bool) -> ControlPlanePolicyV3:
    return ControlPlanePolicyV3(
        school_execution=_school_execution(),
        conjecture_context=_context_policy(),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=_scratch_authoring(scratch_authoring),
    )


def _compile_v6(
    *,
    retry_max: int = 2,
    scratch_authoring: bool = False,
    scratch_enabled: bool = False,
    bridge_mode: str = "legacy_thesis",
    grounding_review: bool = True,
    bridge_schema_repairs: int = 2,
    grounding_repairs: int = 4,
    run_input_digest: str = "a" * 64,
):
    roles = {
        role: _route(role)
        for role in (
            "conjecturer",
            "argumentative_critic",
            "summarizer",
            "synthesizer",
            "thesis",
            "judge",
        )
    }
    config = Config(
        RETRY_MAX=retry_max,
        roles=roles,
        bridge={
            "mode": bridge_mode,
            "grounding_review": grounding_review,
            "max_schema_repair_attempts": bridge_schema_repairs,
            "max_grounding_repair_attempts": grounding_repairs,
        },
        scratchpad={"enabled": scratch_enabled},
    )
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(scratch_authoring=scratch_authoring),
        run_input_digest=run_input_digest,
    )


def _grant_map(manifest) -> dict[str, ContractSchemaRepairGrantV1]:
    policy = manifest.contract_schema_repair_policy
    assert isinstance(policy, ContractSchemaRepairPolicyV1)
    return {grant.contract_id: grant for grant in policy.grants}


def _grant_payload(contract_id: str = "conjecturer.turn.v6", repairs: int = 2):
    return {
        "contract_id": contract_id,
        "maximum_schema_repairs": repairs,
        "maximum_provider_calls": repairs + 1,
        "repair_execution": "fresh_transaction_per_repair",
        "route_scope": "same_route_seat",
        "exhaustion_status": "schema_exhausted",
    }


def _policy_payload(*grants: dict) -> dict:
    return {
        "schema": "contract-schema-repair-policy.v1",
        "grants": list(grants or (_grant_payload(),)),
    }


def test_new_v6_manifest_freezes_typed_core_contract_grants():
    manifest = _compile_v6()
    grants = _grant_map(manifest)

    assert tuple(grants) == CORE_CONTRACTS
    assert manifest.contract_schema_repair_policy is not None
    assert manifest.contract_schema_repair_policy.schema_ == (
        "contract-schema-repair-policy.v1"
    )
    assert all(grant.maximum_schema_repairs == 2 for grant in grants.values())
    assert all(grant.maximum_provider_calls == 3 for grant in grants.values())
    assert all(
        grant.repair_execution == "fresh_transaction_per_repair"
        and grant.route_scope == "same_route_seat"
        and grant.exhaustion_status == "schema_exhausted"
        for grant in grants.values()
    )


@pytest.mark.parametrize(
    ("configured", "expected"),
    ((-7, 0), (0, 0), (1, 1), (2, 2), (9, 2)),
)
def test_shared_retry_ceiling_is_clamped_for_core_and_scratch(configured, expected):
    grants = _grant_map(_compile_v6(retry_max=configured, scratch_authoring=True))

    for contract_id in (*CORE_CONTRACTS, *SCRATCH_CONTRACTS):
        assert grants[contract_id].maximum_schema_repairs == expected
        assert grants[contract_id].maximum_provider_calls == expected + 1


def test_enabled_scratch_authoring_adds_exactly_six_strong_and_minimal_contracts():
    enabled = _grant_map(_compile_v6(scratch_authoring=True))
    disabled = _grant_map(_compile_v6(scratch_authoring=False))

    assert tuple(enabled) == tuple(sorted((*CORE_CONTRACTS, *SCRATCH_CONTRACTS)))
    assert tuple(disabled) == CORE_CONTRACTS


@pytest.mark.parametrize("bridge_schema_repairs", (0, 1, 2))
def test_grounded_bridge_uses_its_schema_repair_ceiling(bridge_schema_repairs):
    grants = _grant_map(
        _compile_v6(
            retry_max=0,
            bridge_mode="grounded_two_stage",
            grounding_review=True,
            bridge_schema_repairs=bridge_schema_repairs,
            grounding_repairs=8,
        )
    )

    assert tuple(grants) == tuple(
        sorted((*CORE_CONTRACTS, *BRIDGE_CONTRACTS, *REVIEW_CONTRACTS))
    )
    for contract_id in (*BRIDGE_CONTRACTS, *REVIEW_CONTRACTS):
        assert grants[contract_id].maximum_schema_repairs == bridge_schema_repairs
        assert grants[contract_id].maximum_provider_calls == bridge_schema_repairs + 1
    assert not set(NONEXISTENT_REVIEW_CONTRACTS).intersection(grants)
    assert grants["conjecturer.turn.v6"].maximum_schema_repairs == 0


def test_grounding_review_controls_only_review_contract_inventory():
    without_review = _grant_map(
        _compile_v6(
            bridge_mode="grounded_two_stage",
            grounding_review=False,
            bridge_schema_repairs=1,
        )
    )
    legacy = _grant_map(_compile_v6(grounding_review=True))

    assert tuple(without_review) == tuple(sorted((*CORE_CONTRACTS, *BRIDGE_CONTRACTS)))
    assert not set(REVIEW_CONTRACTS).intersection(without_review)
    assert not set(NONEXISTENT_REVIEW_CONTRACTS).intersection(without_review)
    assert tuple(legacy) == CORE_CONTRACTS


def test_grants_are_immutable_unique_and_lexicographically_sorted():
    policy = _compile_v6(
        scratch_authoring=True,
        bridge_mode="grounded_two_stage",
        grounding_review=True,
    ).contract_schema_repair_policy
    assert policy is not None
    contract_ids = tuple(grant.contract_id for grant in policy.grants)

    assert contract_ids == tuple(sorted(contract_ids))
    assert len(contract_ids) == len(set(contract_ids))
    with pytest.raises(ValueError):
        policy.grants = ()


@pytest.mark.parametrize(
    "payload",
    (
        {"schema": "contract-schema-repair-policy.v1", "grants": []},
        _policy_payload(_grant_payload("z.v1"), _grant_payload("a.v1")),
        _policy_payload(_grant_payload("a.v1"), _grant_payload("a.v1")),
        _policy_payload(
            {
                **_grant_payload(repairs=2),
                "maximum_provider_calls": 2,
            }
        ),
        _policy_payload(
            {
                **_grant_payload(repairs=2),
                "maximum_schema_repairs": 3,
                "maximum_provider_calls": 4,
            }
        ),
    ),
)
def test_empty_unsorted_duplicate_or_invalid_ceiling_policy_is_rejected(payload):
    with pytest.raises(ValueError):
        ContractSchemaRepairPolicyV1.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "invalid"),
    (
        ("repair_execution", "same_transaction"),
        ("route_scope", "role"),
        ("exhaustion_status", "rejected"),
    ),
)
def test_malformed_fixed_grant_semantics_are_rejected(field, invalid):
    grant = _grant_payload()
    grant[field] = invalid

    with pytest.raises(ValueError):
        ContractSchemaRepairPolicyV1.model_validate(_policy_payload(grant))


def test_unknown_policy_and_grant_fields_are_rejected():
    wrong_schema = _policy_payload()
    wrong_schema["schema"] = "contract-schema-repair-policy.v2"
    policy_unknown = _policy_payload()
    policy_unknown["qualification"] = True
    grant_unknown = _grant_payload()
    grant_unknown["model_may_request"] = True
    coerced_integer = _grant_payload()
    coerced_integer["maximum_schema_repairs"] = "2"

    with pytest.raises(ValueError):
        ContractSchemaRepairPolicyV1.model_validate(wrong_schema)
    with pytest.raises(ValueError):
        ContractSchemaRepairPolicyV1.model_validate(policy_unknown)
    with pytest.raises(ValueError):
        ContractSchemaRepairPolicyV1.model_validate(_policy_payload(grant_unknown))
    with pytest.raises(ValueError):
        ContractSchemaRepairPolicyV1.model_validate(_policy_payload(coerced_integer))


def _pre_v6_manifest(schema_version: int):
    if schema_version <= 3:
        from tests.test_run_manifest import _config

        return compile_run_manifest(
            _config(),
            single_model="gemma4:31b",
            model_profile="standard",
            rubric_policy="forbid",
            compiled_at=STAMP,
            schema_version=schema_version,
            workload_profile="text" if schema_version >= 2 else None,
        )
    if schema_version == 4:
        from tests.test_run_manifest_v4 import (
            _compile_v4,
            _control_policy,
            _historical_config,
        )

        return _compile_v4(_historical_config(), _control_policy())
    from tests.test_run_manifest_v5_inquiry import _compile

    return _compile("b" * 64)


@pytest.mark.parametrize("schema_version", (1, 2, 3, 4, 5))
def test_pre_v6_manifests_omit_and_reject_contract_repair_policy(schema_version):
    manifest = _pre_v6_manifest(schema_version)
    assert manifest.contract_schema_repair_policy is None
    assert "contract_schema_repair_policy" not in manifest.model_dump(mode="json")
    assert b"contract_schema_repair_policy" not in manifest.canonical_bytes()

    payload = json.loads(manifest.canonical_bytes())
    payload["contract_schema_repair_policy"] = _policy_payload()
    with pytest.raises(ValueError):
        RunManifest.model_validate(payload)


def test_historical_v6_without_policy_loads_with_no_inferred_authority(tmp_path):
    current = _compile_v6()
    payload = json.loads(current.canonical_bytes())
    payload.pop("contract_schema_repair_policy")
    payload.pop("route_seat_behavioral_capability_plan")
    path = tmp_path / "historical-v6.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    historical = load_run_manifest(path, verify_hash=False)

    assert historical.contract_schema_repair_policy is None
    assert "contract_schema_repair_policy" not in historical.model_dump(mode="json")
    assert b"contract_schema_repair_policy" not in historical.canonical_bytes()
    assert historical.sha256 != current.sha256


def test_policy_serialization_digest_and_reload_are_exact(tmp_path):
    manifest = _compile_v6(
        retry_max=1,
        scratch_authoring=True,
        bridge_mode="grounded_two_stage",
        grounding_review=True,
        bridge_schema_repairs=2,
    )
    path, digest_path = write_run_manifest(manifest, tmp_path / "manifest.json")

    assert path.read_bytes() == manifest.canonical_bytes()
    assert digest_path.read_text(encoding="utf-8").strip() == manifest.sha256
    assert load_run_manifest(path) == manifest
    serialized = json.loads(path.read_text(encoding="utf-8"))
    assert serialized["contract_schema_repair_policy"] == (
        manifest.contract_schema_repair_policy.model_dump(mode="json", by_alias=True)
    )


def test_policy_presence_changes_identity_and_binding_conflicts(tmp_path):
    run_input = _bind_v2(
        tmp_path,
        Commitment(id="repair-policy-binding", eval="predicate:True"),
    )
    current = _compile_v6(run_input_digest=run_input.run_input_digest)
    historical_payload = json.loads(current.canonical_bytes())
    historical_payload.pop("contract_schema_repair_policy")
    historical_payload.pop("route_seat_behavioral_capability_plan")
    historical = RunManifest.model_validate(historical_payload)

    assert historical.contract_schema_repair_policy is None
    assert historical.canonical_bytes() != current.canonical_bytes()
    assert historical.sha256 != current.sha256
    bind_run_manifest(current, tmp_path)
    with pytest.raises(RunManifestError) as raised:
        bind_run_manifest(historical, tmp_path)
    assert raised.value.code == "RUN_MANIFEST_CONFLICT"


def test_valid_policy_field_change_changes_manifest_identity():
    current = _compile_v6()
    changed_payload = json.loads(current.canonical_bytes())
    first_grant = changed_payload["contract_schema_repair_policy"]["grants"][0]
    first_grant["maximum_schema_repairs"] = 1
    first_grant["maximum_provider_calls"] = 2
    changed_payload.pop("route_seat_behavioral_capability_plan")
    changed = RunManifest.model_validate(changed_payload)

    assert changed.contract_schema_repair_policy != (
        current.contract_schema_repair_policy
    )
    assert changed.canonical_bytes() != current.canonical_bytes()
    assert changed.sha256 != current.sha256


def test_compact_recovery_and_provider_fallback_authority_are_unchanged():
    manifest = _compile_v6()

    assert manifest.compact_recovery_policy == CompactRecoveryPolicyV1()
    assert manifest.provider_fallback is False
