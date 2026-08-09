"""R2's live-run test: a REAL provider call (glm-5.2 via Ollama Cloud,
not a MockEndpoint) dispatching a conjecture turn under
conjecturer.turn.v7 (D2 rev 2 dual-mode), against the P-CEPP-1 fix just
landed (S1-S4). Builds a real, inspectable root under this tranche's
own directory -- not tmp_path -- so the evidence survives the process.

Per SPEC.md Assumption A3: the bar is a v7-labeled request reaching the
real endpoint and a real response being admitted under the v7 contract,
end to end, through the real HTTP path -- not a guaranteed
candidate_checker emission (that is model-choice-dependent and, per
CLAUDE.md's own capability-channel stochasticity doctrine, inconclusive
from one live attempt either way; the offline regression suite, S1-S4,
already proves the mechanism itself works). Uses the SAME classification
bypass the S2/S4 regression tests use and document
(_bind_classification_bypassing_doctor's own docstring:
cli/doctor.py is explicitly out of this tranche's Option C scope).
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import sys

REPO = pathlib.Path("/home/user/DeepReason")
TRANCHE = REPO / "experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring"
sys.path.insert(0, str(REPO / "src"))

from deepreason.canonical import canonical_json  # noqa: E402
from deepreason.config import Config  # noqa: E402
from deepreason.evidence import (  # noqa: E402
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.llm.budget import TokenMeter  # noqa: E402
from deepreason.llm.firewall import leases_from_manifest  # noqa: E402
from deepreason.ontology import Commitment, Problem, ProblemProvenance  # noqa: E402
from deepreason.run_manifest import (  # noqa: E402
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    RunManifestError,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler  # noqa: E402
from deepreason.workflow.transaction import (  # noqa: E402
    RouteSeatModelClassificationPlanV1,
    RouteSeatModelClassificationV1,
)
from deepreason.llm.adapter import _endpoint_from_spec  # noqa: E402
from deepreason.bridge.retry import WorkflowRetryPolicyV1  # noqa: E402


STAMP = "2026-08-09T00:00:00Z"
PROBLEM_ID = "pi-live-v7"
PROBLEM_TEXT = (
    "A store sells widgets in packs of 6 for $9. A customer buys "
    "exactly 4 packs. State the total number of widgets and the "
    "total cost in dollars, and briefly justify the arithmetic."
)


def _bind_run_input(root: pathlib.Path, commitment: Commitment) -> str:
    """Bind one canonical v2 run input and return its digest -- required
    before compile_run_manifest/bind_run_manifest for a v5+ manifest
    (same pattern as tests/test_conjecturer_turn_v4.py::_v6_run_input)."""
    dossier = EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="live-run fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=PROBLEM_ID,
            description=PROBLEM_TEXT,
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return run_input.run_input_digest


def _bind_classification_bypassing_doctor(harness: Harness, manifest: RunManifest) -> None:
    """Same technique as tests/test_v6_transaction_qualification.py's
    _bind_classification_bypassing_doctor -- see that function's own
    docstring for why this is a legitimate bypass of cli/doctor.py, not
    a weakened check."""
    if harness.workflow_state.route_seat_model_classification is not None:
        return
    from types import SimpleNamespace

    behavioral_plan = manifest.route_seat_behavioral_capability_plan
    entries = []
    for grant in behavioral_plan.entries:
        grant_digest = hashlib.sha256(
            b"deepreason.route-seat-behavioral-grant.v1\x00"
            + canonical_json(grant.model_dump(mode="json", by_alias=True, exclude_none=True))
        ).hexdigest()
        contracts = tuple(item.contract_id for item in grant.contracts)
        evidence_pair_ids = tuple(
            sorted(
                "sha256:"
                + hashlib.sha256(
                    f"p-cepp-1-live-run\x00{grant.role}\x00{grant.seat}\x00{contract_id}".encode()
                ).hexdigest()
                for contract_id in contracts
            )
        )
        entries.append(
            RouteSeatModelClassificationV1(
                role=grant.role,
                seat=grant.seat,
                endpoint_id=grant.endpoint_id,
                route_sha256=grant.route_sha256,
                behavioral_grant_sha256=grant_digest,
                selected_class=(
                    "inactive_no_authorized_contract" if not contracts else "qualified_exact_behavior"
                ),
                authorized_contract_ids=contracts,
                evidence_pair_ids=evidence_pair_ids,
            )
        )
    plan = RouteSeatModelClassificationPlanV1.create(
        manifest_digest=manifest.sha256,
        qualification_evidence_sha256="0" * 64,
        entries=tuple(entries),
    )
    report = SimpleNamespace(route_seat_model_classification=plan)
    harness.bind_model_classification(manifest, report)


def build_manifest(key_env: str, run_input_digest: str) -> RunManifest:
    route = {
        "endpoint_id": "conjecturer-live-v7",
        "endpoint": "https://ollama.com/v1",
        "model": "glm-5.2",
        "provider": "ollama",
        "family": "ollama:glm",
        "reasoning": "none",
        "temperature": 0.0,
        "max_tokens": 8192,
        "timeout_s": 90,
        "json_mode": True,
        "api_key_env": key_env,
    }
    config = Config(RETRY_MAX=0, roles={"conjecturer": [route]})
    control = ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only", bindings=(), allow_shared=True,
            require_distinct_models=False, require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled", initial_max_blocks=0, initial_max_guides=0,
            max_context_expansion_requests=0, max_extra_blocks=0,
            permitted_retrieval_channels=(), coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(
            conjecturer_turn_contract="conjecturer.turn.v7"
        ),
    )
    manifest = compile_run_manifest(
        config, schema_version=6, workload_profile="text", rubric_policy="forbid",
        compiled_at=STAMP, control_plane_policy=control, run_input_digest=run_input_digest,
    )
    return manifest, config


def main():
    key_env = sys.argv[1] if len(sys.argv) > 1 else "OLLAMA_API_KEY_AARON"
    if not os.environ.get(key_env):
        print(f"FATAL: {key_env} not set in environment")
        sys.exit(1)

    root = TRANCHE / "live_run_v7"
    if root.exists():
        print(f"FATAL: {root} already exists -- retire it first (git mv), never overwrite")
        sys.exit(1)

    seed_commitment = Commitment(id="k-live-v7", eval="predicate:len(content) > 0")
    run_input_digest = _bind_run_input(root, seed_commitment)
    manifest, config = build_manifest(key_env, run_input_digest)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    commitment = harness.register_commitment(seed_commitment)
    harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description=PROBLEM_TEXT,
            criteria=[commitment.id],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )

    route = manifest.roles["conjecturer"][0]
    endpoint = _endpoint_from_spec(route.endpoint_spec())
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification_bypassing_doctor(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)

    print(f"LIVE RUN starting: root={root} model=glm-5.2 contract=conjecturer.turn.v7 key={key_env}")
    try:
        Scheduler(harness, adapter, config, workload_profile="text", run_manifest=manifest).run(1)
    except Exception as exc:  # noqa: BLE001 - typed outcome either way, report and move on
        print(f"LIVE RUN raised: {type(exc).__name__}: {exc}")

    work_items = list(harness.workflow_state.transaction_work.values())
    print(f"transaction_work count: {len(work_items)}")
    for w in work_items:
        print(f"  work {w.preparation.id}: contract_id={w.preparation.contract_id} "
              f"terminal={w.terminal.status if w.terminal else None}")

    calls = [e.llm for e in harness.log.read() if e.llm is not None and e.llm.role == "conjecturer"]
    print(f"conjecturer LLM calls logged: {len(calls)}")
    for c in calls:
        print(f"  call: attempts={c.attempts} attempt_trace_contracts="
              f"{[a.contract_id for a in c.attempt_trace]} tokens={c.tokens}")

    accepted = [aid for aid, status in harness.state.status.items() if status.value == "accepted"]
    print(f"accepted artifacts: {len(accepted)}")
    for aid in accepted:
        art = harness.state.artifacts[aid]
        from deepreason.programs import content_text
        text = content_text(art, harness.blobs)
        interface_commitments = list(art.interface.commitments)
        print(f"  artifact {aid[:16]}: commitments={interface_commitments}")
        print(f"    content: {text[:300]!r}")

    result = verify_root(root)
    print(f"verify_root violations: {result['violations']}")
    print(f"LIVE RUN COMPLETE: root={root}")


if __name__ == "__main__":
    main()
