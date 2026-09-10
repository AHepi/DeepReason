"""Stub root: the SAME one-model configuration, reaching the trial the other way.

Everything about the run is the shape `stub_solo_config_path.py` uses -- one
model id in every seat, two judge seats, a defender seat, two schools -- except
that criticism is school-routed and its authority is the manifest's own
`defended_trial` instead of Config's `single_family_trial`.
"""
import json, pathlib, sys

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance, WarrantType
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.scheduler.scheduler import Scheduler
from deepreason.v6_policy import configured_criticism_policy, engaged_control_plane_policy_v3

M = "qwen3.5:397b"


def _fixed(text):
    return lambda prompt: text


CRITIC_PROMPTS = []


def _critic(prompt):
    """Attack every target the pack lists, under the alias the wire enum names.

    The criticism pack names targets by call-local alias and the batch wire
    contract carries them as a closed enum, so the responder reads the aliases
    out of the rendered schema rather than assuming an id.
    """
    import re
    CRITIC_PROMPTS.append(prompt)
    m = re.search(r'"target_alias":\s*\{"enum":\s*\[([^\]]*)\]', prompt)
    aliases = re.findall(r'"([^"]+)"', m.group(1)) if m else []
    return json.dumps({"cases": [
        {"target_alias": a, "attack": True,
         "case": "clause 2 forbids parallel fifths and bar 3 has them"}
        for a in aliases
    ]})


def spec(eid):
    return {"endpoint_id": eid, "endpoint": f"mock://{eid}", "model": M,
            "provider": "fixture", "family": "qwen", "max_tokens": 512,
            "context_window_tokens": 262_144}


CONJ = json.dumps({"candidates": [
    {"content": "a chorale passage with parallel fifths in bar 3", "typicality": 0.5},
]})
CASE = json.dumps({"attack": True, "case": "clause 2 forbids parallel fifths and bar 3 has them"})
DEFENCE = json.dumps({"answer": "the fifths echo the cantus firmus deliberately"})
RULING = json.dumps({"verdict": "fail", "decisive_point": "bar 3 has them"})

root = pathlib.Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=True)

config = Config(
    N_SCHOOLS=2,
    LEGACY_CRITICISM_ENABLED=False,
    ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
    ENGAGED_CRITICISM_AUTHORITY="defended_trial",
    VS_K=1, FLOOR=0, SPEC_INJECTION=False, CONTROLLER=False, FUZZ_N=0,
    RECRIT_STANDING=False, NEAR_DUP_EPS=None, model_profile="standard",
    roles={
        "conjecturer": [spec("r-conj")],
        "argumentative_critic": [spec("r-crit")],
        "defender": [spec("r-def")],
        "judge": [spec("r-j0"), spec("r-j1")],
    },
)
from deepreason.evidence.models import (
    AttachedSourceProvenanceV1, EvidenceDossierV1, RunInputManifestV2, RunInputProblemV2,
)
from deepreason.evidence.state import bind_run_input

PROBLEM_ID = "p-seed"
PROBLEM_TEXT = "Does a chorale passage with parallel fifths in bar 3 violate clause 2?"

from deepreason.evidence.models import (
    AttachedSourceProvenanceV1, EvidenceDossierV1, RunInputManifestV2, RunInputProblemV2,
)
from deepreason.evidence.state import bind_run_input

PROBLEM_ID = "p-seed"
PROBLEM_TEXT = "Does a chorale passage with parallel fifths in bar 3 violate clause 2?"

provenance = AttachedSourceProvenanceV1(
    supplied_by="offline stub", acquisition_method="pre-freeze construction",
)
dossier = EvidenceDossierV1.create(
    problem_ref=PROBLEM_ID, sources=(), total_byte_count=0,
    creation_provenance=provenance,
)
run_input = RunInputManifestV2.create(
    problem=RunInputProblemV2.from_commitments(
        id=PROBLEM_ID, description=PROBLEM_TEXT, criteria=(),
    ),
    evidence_dossier_digest=dossier.dossier_digest,
)
bind_run_input(run_input, dossier, root)

policy = configured_criticism_policy(config, "r-crit")
manifest = compile_run_manifest(
    config, schema_version=6, workload_profile="text", rubric_policy="forbid",
    compiled_at="2026-09-09T00:00:00Z",
    control_plane_policy=engaged_control_plane_policy_v3(),
    criticism_policy=policy, run_input_digest=run_input.run_input_digest,
)
print("criticism authority:", manifest.criticism_policy.authority)
print("compile notices:", [n.code for n in (getattr(manifest, "compile_notices", ()) or ())])

h = Harness(root)
bind_run_manifest(manifest, root)
h.register_problem(Problem(
    id=PROBLEM_ID,
    description=PROBLEM_TEXT,
    provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
))

leases = leases_from_manifest(manifest)
endpoints = {
    "conjecturer": MockEndpoint(_fixed(CONJ), name="mock://r-conj", model=M, max_tokens=512),
    "argumentative_critic": MockEndpoint(_critic, name="mock://r-crit", model=M, max_tokens=512),
    "defender": MockEndpoint(_fixed(DEFENCE), name="mock://r-def", model=M, max_tokens=512),
    "judge": [
        MockEndpoint(_fixed(RULING), name="mock://r-j0", model=M, max_tokens=512),
        MockEndpoint(_fixed(RULING), name="mock://r-j1", model=M, max_tokens=512),
    ],
}
from deepreason.llm.budget import TokenMeter

adapter = LLMAdapter(
    endpoints, h.blobs, retry_max=0, model_profile=manifest.model_profile,
    leases=leases, transaction_authority_required=True,
    meter=TokenMeter(2_000_000),
)
from deepreason.cli.doctor import run_production_contract_doctor
from deepreason.qualification import ProductionContractCaseResultV1

report = run_production_contract_doctor(
    manifest,
    case_executor=lambda _m, _pair, index: ProductionContractCaseResultV1(
        case_id=f"case-{index + 1:03d}", first_pass_valid=True,
        eventual_valid=True, repair_count=0, semantic_admission=True,
    ),
)
h.bind_model_classification(manifest, report)
adapter.bind_v6_authority(h, manifest)
print("is_single_model:", adapter.is_single_model(), "judge seats:", len(adapter.judge_seats()))

Scheduler(h, adapter, config, run_manifest=manifest).run(
    int(sys.argv[2]) if len(sys.argv) > 2 else 3
)

h2 = Harness(root, read_only=True)
warrants = list(h2.warrants.values())
arg = [w for w in warrants if w.type == WarrantType.ARGUMENTATIVE]
print("warrants total:", len(warrants), "argumentative:", len(arg))
print("attack edges:", len(h2.state.att))
for w in arg:
    print("  ARGUMENTATIVE warrant ->", w.target)
from collections import Counter
c = Counter()
for e in h2.log.read():
    if e.inputs and str(e.inputs[0]).startswith(("trial-declined", "trial-blocked", "arg-crit", "foreign-criticism")):
        k = str(e.inputs[0])
        if k == "trial-declined" and len(e.inputs) > 2:
            k += ":" + str(e.inputs[2])
        c[k] += 1
print("trial/crit measures:", dict(c))
if CRITIC_PROMPTS:
    pathlib.Path(sys.argv[1] + "-critic-prompt.txt").write_text(CRITIC_PROMPTS[0])
    print("critic prompt saved; handles seen:", CRITIC_PROMPTS[0][:0] or "(see file)")
