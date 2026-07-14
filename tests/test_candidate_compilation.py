"""Two-phase candidate compilation (bronze postrun repair, RC5): a blocked
proposal must not mutate the epistemic registry. Draft interfaces gate on
overlay commitments; forbidden-case commitments register only after
admission."""

import json

from deepreason.config import Config
from deepreason.informal.skeleton import skeleton_wf_commitment
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.embedder import HashingEmbedder
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    Status,
)
from deepreason.rules.conj import conj
from deepreason.rules.crit import crit_program
from deepreason.rules.guards import anti_relapse
from tests.conftest import art

EMBEDDER = HashingEmbedder()
# Calibrated on this fixture corpus: the paraphrase (three added forbidden
# cases) sits at ~0.36 from the prior, the peasant-revolt stand-in at ~0.66.
EPS = 0.45


def _skeleton(claim: str, mechanism: str, cases: list[str]) -> str:
    return json.dumps(
        {
            "claim": claim,
            "mechanism": mechanism,
            "forbidden": [
                {"case": case, "eval": "rubric:std-collapse"} for case in cases
            ],
        },
        sort_keys=True,
    )


SYSTEMS = _skeleton(
    "the bronze age collapse was a systems-network failure",
    "interdependent palace economies transmitted local shocks through trade "
    "and tribute links until the whole exchange network unravelled",
    ["a polity collapses with no upstream trade disruption"],
)
# A close paraphrase carrying THREE novel forbidden cases: under one-phase
# compilation these mutated the registry even when the proposal was blocked.
PARAPHRASE = _skeleton(
    "the bronze age collapse was a failure of the systems network",
    "interdependent palace economies transmitted local shocks through tribute "
    "and trade links until the exchange network unravelled entirely",
    [
        "a peripheral polity thrives after severing every trade link",
        "shock transmission stops at the first palace boundary",
        "archives show autarkic palace economies before the collapse",
    ],
)
PEASANT = _skeleton(
    "the bronze age collapse was driven by peasant and merchant revolt",
    "rural producers and traders withdrew labour and goods from palace "
    "redistribution, starving elite centres until administration failed",
    [
        "records show stable rural tribute flows during the terminal decades",
        "elite centres persist after total rural withdrawal",
    ],
)


def _seed(harness):
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(
        Commitment(
            id="k-bronze", eval="predicate:'bronze-evidence-marker' in content"
        )
    )
    problem = harness.register_problem(
        Problem(
            id="pi-collapse",
            description="explain the bronze age collapse",
            criteria=["skeleton-wf", "k-bronze"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    prior = art(
        harness,
        SYSTEMS,
        interface=Interface(commitments=["skeleton-wf", "k-bronze"]),
        provenance=Provenance(role="conjecturer"),
    )
    # The prior's domain mirrors what conj compiles for direct text calls.
    anti_relapse.record_domain(
        harness,
        prior.id,
        anti_relapse.relapse_domain(
            prior,
            harness,
            workload_profile="text",
            problem_family=problem.id,
            contract_id="conjecturer.direct.v1",
        ),
    )
    crit_program(harness, prior.id)  # k-bronze fails: marker absent
    assert harness.state.status[prior.id] == Status.REFUTED
    return problem


def _adapter(harness, content: str):
    return LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                [json.dumps({"candidates": [{"content": content, "typicality": 0.4}]})]
            )
        },
        harness.blobs,
        retry_max=2,
    )


def test_blocked_candidate_no_commitment_mutation(harness):
    problem = _seed(harness)
    commitments_before = set(harness.commitments)
    artifacts_before = set(harness.state.artifacts)
    seq_before = harness._next_seq

    admitted = conj(
        harness,
        problem.id,
        _adapter(harness, PARAPHRASE),
        Config(NEAR_DUP_EPS=EPS),
        embedder=EMBEDDER,
        workload_profile="text",
    )

    assert admitted == []
    # Zero commitment registrations: the three novel forbidden cases stayed
    # drafts and never reached the registry.
    assert set(harness.commitments) == commitments_before
    assert set(harness.state.artifacts) == artifacts_before
    new_events = [e for e in harness.log.read() if e.seq >= seq_before]
    assert new_events  # the block itself is on the record
    assert all(event.rule == Rule.MEASURE for event in new_events)
    gate = [e for e in new_events if e.inputs and e.inputs[0].startswith("gate:")]
    assert gate and "battery-equivalent" in gate[0].inputs[0]
    # The gamma call still reached the log exactly once.
    assert sum(event.llm is not None for event in new_events) == 1
    # The block left an operational receipt naming the prior's refuters.
    receipts = [
        json.loads(line)
        for line in (harness.root / "relapse.log.jsonl").read_text().splitlines()
    ]
    block = [r for r in receipts if r.get("type") == "relapse-block"]
    assert block and block[-1]["refuter_ids"]


def test_admitted_candidate_registers_draft_commitments_after_gate(harness):
    problem = _seed(harness)
    commitments_before = set(harness.commitments)

    admitted = conj(
        harness,
        problem.id,
        _adapter(harness, PEASANT),
        Config(NEAR_DUP_EPS=EPS),
        embedder=EMBEDDER,
        workload_profile="text",
    )

    assert len(admitted) == 1
    registered = set(harness.commitments) - commitments_before
    assert len(registered) == 2  # the two novel forbidden cases, post-admission
    assert all(cid.startswith("fc:") for cid in registered)
    assert registered <= set(admitted[0].interface.commitments)
