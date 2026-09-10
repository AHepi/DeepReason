"""Build a stub root carrying ONE defended trial, and report both channels.

The smallest artifact that shows the defect: a one-cycle run on the
PRE-EXISTING `ENGAGED_CRITICISM_AUTHORITY=defended_trial` road (none of the
2026-09-09 solo switches), against deterministic mock endpoints. The trial runs
once and writes three `defended_trial_step` transactions -- the defender and
both judge seats.

Prints a typed JSON summary on stdout: `verify_root`'s violation count beside
the report's per-channel counts and the unknown-kind census. Before the fix the
two disagree (0 violations, `valid: false`); after it they agree.

Adapted from `experiments/2026-09-09-fix-solo-criticism-authority/proof/
stub_solo_defended_trial.py`, which is where this shape was first built.
"""
import collections
import json
import pathlib
import sys

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.evidence.models import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
)
from deepreason.evidence.state import bind_run_input
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.scheduler.scheduler import Scheduler
from deepreason.v6_policy import (
    configured_criticism_policy,
    engaged_control_plane_policy_v3,
)

M = "qwen3.5:397b"
PROBLEM_ID = "p-seed"
PROBLEM_TEXT = "Does a chorale passage with parallel fifths in bar 3 violate clause 2?"

CONJ = json.dumps({"candidates": [
    {"content": "a chorale passage with parallel fifths in bar 3", "typicality": 0.5},
]})
DEFENCE = json.dumps({"answer": "the fifths echo the cantus firmus deliberately"})
RULING = json.dumps({"verdict": "fail", "decisive_point": "bar 3 has them"})


def _fixed(text):
    return lambda prompt: text


def _critic(prompt):
    """Attack every target the pack lists, under the alias the wire enum names."""
    import re

    match = re.search(r'"target_alias":\s*\{"enum":\s*\[([^\]]*)\]', prompt)
    aliases = re.findall(r'"([^"]+)"', match.group(1)) if match else []
    return json.dumps({"cases": [
        {"target_alias": alias, "attack": True,
         "case": "clause 2 forbids parallel fifths and bar 3 has them"}
        for alias in aliases
    ]})


def _spec(endpoint_id):
    return {"endpoint_id": endpoint_id, "endpoint": f"mock://{endpoint_id}",
            "model": M, "provider": "fixture", "family": "qwen",
            "max_tokens": 512, "context_window_tokens": 262_144}


def build(root: pathlib.Path, cycles: int = 1):
    root.mkdir(parents=True, exist_ok=True)
    config = Config(
        N_SCHOOLS=2,
        LEGACY_CRITICISM_ENABLED=False,
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ENGAGED_CRITICISM_AUTHORITY="defended_trial",
        VS_K=1, FLOOR=0, SPEC_INJECTION=False, CONTROLLER=False, FUZZ_N=0,
        RECRIT_STANDING=False, NEAR_DUP_EPS=None, model_profile="standard",
        roles={
            "conjecturer": [_spec("r-conj")],
            "argumentative_critic": [_spec("r-crit")],
            "defender": [_spec("r-def")],
            "judge": [_spec("r-j0"), _spec("r-j1")],
        },
    )
    dossier = EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID, sources=(), total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline stub", acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=PROBLEM_ID, description=PROBLEM_TEXT, criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)

    manifest = compile_run_manifest(
        config, schema_version=6, workload_profile="text", rubric_policy="forbid",
        compiled_at="2026-09-10T00:00:00Z",
        control_plane_policy=engaged_control_plane_policy_v3(),
        criticism_policy=configured_criticism_policy(config, "r-crit"),
        run_input_digest=run_input.run_input_digest,
    )
    harness = Harness(root)
    bind_run_manifest(manifest, root)
    harness.register_problem(Problem(
        id=PROBLEM_ID, description=PROBLEM_TEXT,
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(_fixed(CONJ), name="mock://r-conj", model=M, max_tokens=512),
            "argumentative_critic": MockEndpoint(_critic, name="mock://r-crit", model=M, max_tokens=512),
            "defender": MockEndpoint(_fixed(DEFENCE), name="mock://r-def", model=M, max_tokens=512),
            "judge": [
                MockEndpoint(_fixed(RULING), name="mock://r-j0", model=M, max_tokens=512),
                MockEndpoint(_fixed(RULING), name="mock://r-j1", model=M, max_tokens=512),
            ],
        },
        harness.blobs, retry_max=0, model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest), transaction_authority_required=True,
        meter=TokenMeter(2_000_000),
    )
    from deepreason.cli.doctor import run_production_contract_doctor
    from deepreason.qualification import ProductionContractCaseResultV1

    harness.bind_model_classification(manifest, run_production_contract_doctor(
        manifest,
        case_executor=lambda _m, _pair, index: ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}", first_pass_valid=True,
            eventual_valid=True, repair_count=0, semantic_admission=True,
        ),
    ))
    adapter.bind_v6_authority(harness, manifest)
    Scheduler(harness, adapter, config, run_manifest=manifest).run(cycles)
    return root


def report(root: pathlib.Path) -> dict:
    from deepreason.invariants import verify_root
    from deepreason.verification.report import verify_root_report

    replay = verify_root(root)
    rendered = verify_root_report(root)
    kinds = collections.Counter()
    reread = Harness(root, read_only=True)
    for item in reread.workflow_state.transaction_work.values():
        kinds[item.preparation.task_kind.value] += 1
    unknown = collections.Counter()
    for finding in rendered.security:
        if "unknown v6 task kind " in finding.detail:
            unknown[finding.detail.split("unknown v6 task kind ")[1]] += 1
    return {
        "root": str(root),
        "verify_root_violations": len(replay["violations"]),
        "valid": rendered.valid,
        "integrity": len(rendered.integrity),
        "security": len(rendered.security),
        "completion": len(rendered.completion),
        "operational": len(rendered.operational),
        "security_checks": dict(collections.Counter(f.check for f in rendered.security)),
        "unknown_task_kinds": dict(unknown),
        "task_kinds": dict(kinds),
    }


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1])
    build(target, int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    print(json.dumps(report(target), indent=2, sort_keys=True))
