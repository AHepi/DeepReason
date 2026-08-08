"""Form 2 (offline unit reproduction): a minimal synthetic root holding
ONE already-admitted-and-terminalized criticism ATOMIC CHILD work item,
built through the harness's own real decomposition seams (no live
provider) -- the write-time replay validator
(``_validate_preparation_decomposition_authority``) refuses an atomic
child preparation with no matching ``activate_contract_decomposition``
transition, so that machinery is not optional scaffolding here, only
``complete_contract_decomposition`` is skipped (the crash needs no
completion record -- confirmed by DIAGNOSIS.md's read of the sweep/
dispatch code, which never inspects one).

Mirrors the shape rules/crit.py's own execute_atomic_transition uses
to build an atomic child's task payload (schema
"contract-decomposition-child.v1", contract_id
"critic.atomic-target.v1", trigger prefix "decomposition-child:"),
reusing tests/test_v6_nonconjecture_recovery.py's own
_manifest/_config/_lease/_provider_prefix helpers per dr-reproduce's
"do not invent new scaffolding when a helper exists" rule.

Run: python3 experiments/2026-08-08-fix-l1-continue-resumable-crash/repro_synthetic_atomic_child.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))

from deepreason.canonical import canonical_json
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.llm.wire import AliasTable, AtomicCriticWireContractV1
from deepreason.ontology import Provenance
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.nonconjecture_recovery import NonConjectureRecoveryAuthorityError
from deepreason.workflow.transaction_service import InquiryTransactionService

from test_v6_nonconjecture_recovery import _config, _lease, _manifest, _provider_prefix


def main() -> int:
    tmp_root = Path(tempfile.mkdtemp()) / "synthetic-atomic-child"
    config, manifest = _manifest()
    harness = Harness(tmp_root)

    target = harness.create_artifact(
        "one school-owned target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    # 1. A schema-exhausted BATCH source item, the precondition
    #    activate_contract_decomposition itself enforces.
    source_payload = {
        "schema": "criticism.semantic-task.v1",
        "critic_school_id": "school-1",
        "target_ids": [target.id],
        "assignment_refs": [],
        "coverage_attempt_index": 0,
        "phase": "qualification",
        "caller_trigger_ref": None,
    }
    source_preparation, source_provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.CRITICISM,
        role="argumentative_critic",
        seat=1,
        contract_id="batch-critic.v2",
        payload=source_payload,
        trigger_prefix="criticism:",
        raw=b"not valid json",
        target_refs=(target.id,),
    )
    reopened = Harness(tmp_root)
    transaction = InquiryTransactionService(reopened, manifest, TokenMeter(100_000))
    source_admission = transaction.record_semantic_admission(
        source_provider, outcome="schema_exhausted"
    )
    transaction.terminate(
        work_id=source_provider.work_id,
        attempt_index=source_provider.attempt_index,
        status="schema_exhausted",
        reason_code="recovered_criticism_schema_exhausted",
        usage_status="exact",
        prompt_tokens=source_provider.prompt_tokens,
        completion_tokens=source_provider.completion_tokens,
        provider_attempt=source_provider,
        admission=source_admission,
    )

    # 2. The real decomposition-activation seam -- not optional, the
    #    harness's own write-time validator requires this transition
    #    to exist before it will accept an atomic child preparation.
    reopened = Harness(tmp_root)
    pack_text = "one bounded atomic critic pack"
    transition = reopened.activate_contract_decomposition(
        manifest,
        source_preparation.id,
        child_contexts=((target.id, pack_text),),
    )
    assert transition.atomic_contract_id == "critic.atomic-target.v1", transition

    # 3. The atomic child itself -- schema "contract-decomposition-
    #    child.v1", exactly rules/crit.py's execute_atomic_transition
    #    shape (crit.py:555-566) -- admitted and terminalized, i.e.
    #    ALREADY fully resolved. Nothing about it is "pending".
    child_payload = {
        "schema": "contract-decomposition-child.v1",
        "decomposition_transition_ref": transition.id,
        "source_work_id": transition.source_work_id,
        "source_contract_id": transition.source_contract_id,
        "atomic_contract_id": transition.atomic_contract_id,
        "child_partition": transition.child_partition,
        "child_index": 0,
        "child_count": 1,
        "child_key": target.id,
        "critic_school_id": "school-1",
    }
    raw_output = b'{"target_alias":"SRC_001","attack":false,"claim":"a recovered atomic child"}'
    child_preparation, child_provider = _provider_prefix(
        reopened,
        manifest,
        task_kind=WorkflowTaskKind.CRITICISM,
        role="argumentative_critic",
        seat=1,
        contract_id=transition.atomic_contract_id,
        payload=child_payload,
        trigger_prefix="decomposition-child:",
        raw=raw_output,
        target_refs=(target.id,),
        input_refs=(
            transition.source_work_id,
            transition.id,
            transition.child_context_refs[0],
            target.id,
        ),
    )
    reopened = Harness(tmp_root)
    contract = AtomicCriticWireContractV1(
        AliasTable({"SRC_001": target.id}), expected_target=target.id
    )
    output = contract.parse_compile(raw_output.decode("utf-8"))
    admitted_ref = reopened.blobs.put(
        canonical_json(output.model_dump(mode="json", exclude_none=True))
    )
    transaction = InquiryTransactionService(reopened, manifest, TokenMeter(100_000))
    child_admission = transaction.record_semantic_admission(
        child_provider, outcome="admitted", admitted_refs=(admitted_ref,)
    )
    transaction.terminate(
        work_id=child_provider.work_id,
        attempt_index=child_provider.attempt_index,
        status="completed",
        reason_code="atomic_critic_output_admitted",
        usage_status="exact",
        prompt_tokens=child_provider.prompt_tokens,
        completion_tokens=child_provider.completion_tokens,
        provider_attempt=child_provider,
        admission=child_admission,
    )

    reopened = Harness(tmp_root)
    item = reopened.workflow_state.transaction_work[child_preparation.id]
    assert item.terminal is not None and item.terminal.status == "completed", (
        "setup invariant: the atomic child must ALREADY be fully "
        "terminalized before recovery runs -- proving the crash needs "
        "no pending work at all, only an admitted criticism atomic child"
    )

    def forbidden(prompt: str) -> str:
        raise AssertionError("recovery redispatched a durable result -- should never fire")

    route = manifest.roles["argumentative_critic"][1]
    adapter = LLMAdapter(
        {"argumentative_critic": [MockEndpoint(forbidden, name=route.base_url, model=route.model_id)]},
        reopened.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )

    try:
        Scheduler(reopened, adapter, config, workload_profile="text", run_manifest=manifest).run(0)
        print("NO CRASH -- recovery completed cleanly (unexpected before the fix)")
        return 1
    except NonConjectureRecoveryAuthorityError as error:
        print(f"CRASHED as predicted: {type(error).__name__}: {error}")
        assert str(error) == "unknown critic task", error
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
