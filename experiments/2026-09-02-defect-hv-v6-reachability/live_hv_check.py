"""One guarded live check: does the v6 transactional `hv` dispatch work against
a real provider, and do both producers reach real verdicts?

WHAT THIS PROVES. The offline tests drive `MockEndpoint`, so they prove the
transaction is opened, settled and recorded correctly — but they cannot prove
that a REAL model's variator output satisfies the `variator.direct.v1` wire
contract through the v6 boundary, nor that `hv` computes a sensible number from
real edits. That is what this asks.

WHAT THIS DOES NOT PROVE. It does not show that a live SCHEDULER reaches
`_lazy_hv` or the `hv-floor` arm on its own — that needs a run deep enough to
produce an ACCEPTED-and-addressed artifact or a connection problem, and is
stochastic. This drives the two producers directly.

WHAT IS STUBBED, stated so the result is not over-read. The production-contract
doctor's per-case executor is stubbed: qualification is a separate battery with
its own cost and is not what this checks. Everything from
`InquiryTransactionService.prepare` to the provider socket is live.

Usage:
    set -a && . experiments/2026-09-02-defect-hv-v6-reachability/env && set +a
    python -u experiments/2026-09-02-defect-hv-v6-reachability/live_hv_check.py

Exit 0 when both producers reached a typed outcome through a live transaction.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
CONFIG = pathlib.Path(__file__).resolve().parent / "run-config-hv-grant.yaml"


QUESTION = "Why do urban heat islands persist after sunset?"


def build_root(root):
    """A real root: dossier, run-input, manifest on disk, in that order.

    The order is forced rather than stylistic. `compile_run_manifest` takes the
    run input's digest, and `bind_run_manifest` refuses a root whose run input
    is not already verified on disk — so the input is built first and the
    manifest compiled against it. Skipping this and binding the manifest in
    memory alone makes `verify_root` return early with an empty controller-v3
    context, which reads as a pairing violation on every transactional call.
    """

    import yaml

    from deepreason.config import Config
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        EvidenceDossierV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )
    from deepreason.preparation import _question_digest
    from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
    from deepreason.v6_policy import engaged_control_plane_policy_v3

    config = Config(**yaml.safe_load(CONFIG.read_text()))
    problem_id = f"question-{_question_digest(QUESTION)[:32]}"
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="live_hv_check.py",
            acquisition_method="no attached evidence",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=QUESTION, criteria=()
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        single_model="glm-5.2",
        concurrency=2,
        compiled_at="2026-09-02T00:00:00+00:00",
        control_plane_policy=engaged_control_plane_policy_v3(),
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    return config, manifest


def variator_grant(manifest) -> list[str]:
    plan = manifest.route_seat_behavioral_capability_plan
    return sorted(
        contract.contract_id
        for entry in (plan.entries if plan else ())
        if entry.role == "variator"
        for contract in entry.contracts
    )


def bind(harness, manifest):
    """Durable model classification, with the doctor's case executor stubbed."""

    from deepreason.cli.doctor import run_production_contract_doctor

    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tests.test_v6_compact_recovery_transition import _admitted_case

    report = run_production_contract_doctor(
        manifest, case_executor=lambda _m, _pair, index: _admitted_case(index)
    )
    harness.bind_model_classification(manifest, report)


def main() -> int:
    if not os.environ.get("OLLAMA_API_KEY"):
        print("OLLAMA_API_KEY is not set; source the tranche's gitignored env file")
        return 2

    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.llm.adapter import build_adapter
    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.embedder import build_embedder
    from deepreason.measures.hv import hv_floor_commitment, hv_spot_check, run_hv_floor
    from deepreason.ontology import Interface, Provenance, Ref, Status
    from deepreason.storage.blobs import BlobStore
    from deepreason.workflow.models import WorkflowTaskKind

    workdir = pathlib.Path(tempfile.mkdtemp(prefix="live-hv-"))
    root = workdir / "run"
    root.mkdir(parents=True)
    config, manifest = build_root(root)
    grant = variator_grant(manifest)
    print(f"manifest schema_version   {manifest.schema_version}")
    print(f"criticism authority       {manifest.criticism_policy.authority}")
    print(f"variator[0] grant         {grant}")
    print(f"variator route            {manifest.roles['variator'][0].endpoint_id} "
          f"/ {manifest.roles['variator'][0].model_id}")
    if not grant:
        print("FAIL: the manifest grants the variator nothing; the gate cannot open")
        return 1

    harness = Harness(root)
    bind(harness, manifest)
    adapter = build_adapter(
        config,
        harness.blobs,
        meter=TokenMeter(400_000),
        run_manifest=manifest,
    )
    adapter.bind_v6_authority(harness, manifest)
    # `_survival` counts an edit as a surviving variant only if it passes the
    # battery AND is judged INEQUIVALENT to the original, so the equivalence
    # surrogate decides half of every verdict. Running on the hashing fallback
    # makes the number untrustworthy; run `deepreason embedder-warmup` first.
    embedder = build_embedder(config.EMBEDDER_MODEL)
    print(f"adapter transactional     {adapter.transaction_authority_required}")
    print(f"embedder                  {type(embedder).__name__} "
          f"({config.EMBEDDER_MODEL})")
    print(f"working root              {harness.root}")
    print()

    outcomes: dict[str, object] = {"embedder": type(embedder).__name__}

    # --- producer 1: hv_spot_check, the ranking estimate --------------------
    spot_target = harness.create_artifact(
        "Urban heat islands persist after sunset because dense construction "
        "materials release stored daytime radiation slowly through the night.",
        provenance=Provenance(role="conjecturer"),
    )
    print("hv_spot_check on a live variator seat ...")
    try:
        value = hv_spot_check(harness, adapter, spot_target.id, int(config.HV_K), embedder)
        measured = [
            event
            for event in harness.log.read()
            if event.state_diff.hv_set.get(spot_target.id) is not None
        ]
        outcomes["hv_spot_check"] = {
            "returned": value,
            "hv_set_events": len(measured),
            "state_hv": harness.state.hv.get(spot_target.id),
            "llm_attached": None if not measured else measured[0].llm is not None,
        }
        print(f"  -> hv={value}  hv_set events={len(measured)}  "
              f"llm attached={None if not measured else measured[0].llm is not None}")
    except Exception as error:  # noqa: BLE001 - the typed failure IS the result
        outcomes["hv_spot_check"] = {"error": f"{type(error).__name__}: {error}"}
        print(f"  -> {type(error).__name__}: {error}")

    # --- producer 2: run_hv_floor, the criterion that can refute ------------
    a = harness.create_artifact("theory A: energy is conserved",
                                provenance=Provenance(role="conjecturer"))
    b = harness.create_artifact("theory B: entropy increases",
                                provenance=Provenance(role="conjecturer"))
    floor = hv_floor_commitment(Config(HV_K=int(config.HV_K), HV_MIN=0.5))
    harness.register_commitment(floor)
    relation = harness.create_artifact(
        "energy conservation bounds entropy production in closed systems",
        interface=Interface(
            commitments=[floor.id],
            refs=[Ref(target=a.id, role="dependence"),
                  Ref(target=b.id, role="dependence")],
        ),
        provenance=Provenance(role="synthesizer"),
    )
    before = dict(harness.state.status)
    print("run_hv_floor on a live variator seat ...")
    try:
        verdict = run_hv_floor(harness, adapter, relation.id, floor, embedder)
        warrants = [w for w in harness.warrants.values() if w.target == relation.id]
        outcomes["run_hv_floor"] = {
            "verdict": verdict,
            "status": str(harness.state.status.get(relation.id)),
            "status_moved": before.get(relation.id) != harness.state.status.get(relation.id),
            "warrants_minted": len(warrants),
            "state_hv": harness.state.hv.get(relation.id),
        }
        print(f"  -> verdict={verdict}  status={harness.state.status.get(relation.id)}  "
              f"warrants={len(warrants)}  hv={harness.state.hv.get(relation.id)}")
        if warrants:
            trace = json.loads(harness.blobs.get(warrants[0].trace_ref))
            outcomes["run_hv_floor"]["s_hat"] = trace.get("s_hat")
            outcomes["run_hv_floor"]["kernel"] = trace.get("kernel")
            print(f"     s_hat={trace.get('s_hat')}  kernel={trace.get('kernel')}  "
                  f"edits sampled={len(trace.get('per_edit') or [])}")
    except Exception as error:  # noqa: BLE001
        outcomes["run_hv_floor"] = {"error": f"{type(error).__name__}: {error}"}
        print(f"  -> {type(error).__name__}: {error}")

    # --- producer 2b: the PASS arm, so both verdicts are shown live ---------
    # Without a real battery every edit survives vacuously, s_hat = 1 and hv = 0,
    # which exercises only the refuting arm. A battery the edits break is what
    # makes the number non-degenerate.
    from deepreason.ontology import Commitment

    harness.register_commitment(
        Commitment(
            id="k-energy",
            eval="predicate:'energy' in content and 'entropy' in content",
        )
    )
    hard = harness.create_artifact(
        "energy conservation bounds entropy production in closed systems",
        interface=Interface(
            commitments=["k-energy", floor.id],
            refs=[Ref(target=a.id, role="dependence"),
                  Ref(target=b.id, role="dependence")],
        ),
        provenance=Provenance(role="synthesizer"),
    )
    print("run_hv_floor with a real battery (the PASS arm) ...")
    try:
        verdict2 = run_hv_floor(harness, adapter, hard.id, floor, embedder)
        outcomes["run_hv_floor_with_battery"] = {
            "verdict": verdict2,
            "status": str(harness.state.status.get(hard.id)),
            "state_hv": harness.state.hv.get(hard.id),
            "warrants_minted": len(
                [w for w in harness.warrants.values() if w.target == hard.id]
            ),
        }
        print(f"  -> verdict={verdict2}  status={harness.state.status.get(hard.id)}  "
              f"hv={harness.state.hv.get(hard.id)}")
    except Exception as error:  # noqa: BLE001
        outcomes["run_hv_floor_with_battery"] = {"error": f"{type(error).__name__}: {error}"}
        print(f"  -> {type(error).__name__}: {error}")

    # --- the transactional record both calls must have written --------------
    work = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.DEFENDED_TRIAL_STEP
    ]
    print()
    print(f"v6 work items (DEFENDED_TRIAL_STEP)  {len(work)}")
    for item in work:
        payload = item.preparation.task_payload_value
        print(f"  contract={item.preparation.contract_id}  "
              f"schema={payload.get('schema')}  step={payload.get('step')}")
    outcomes["work_items"] = [
        {
            "contract_id": item.preparation.contract_id,
            "schema": item.preparation.task_payload_value.get("schema"),
        }
        for item in work
    ]

    from deepreason.invariants import verify_root

    report = verify_root(harness.root)
    violations = report["violations"] if isinstance(report, dict) else report
    print(f"verify_root violations               {len(violations)}")
    outcomes["verify_root_violations"] = len(violations)
    for violation in violations[:5]:
        print(f"  {violation}")

    out = pathlib.Path(__file__).resolve().parent / "live_hv_check.json"
    out.write_text(json.dumps(outcomes, indent=2, default=str) + "\n")
    print(f"\nwrote {out}")

    reached = [
        name for name in ("hv_spot_check", "run_hv_floor")
        if "error" not in outcomes[name]
    ]
    return 0 if len(reached) == 2 and not violations else 1


if __name__ == "__main__":
    sys.exit(main())
