"""P1 acceptance (spec §16): single-problem Conj -> Crit -> Adj loop.

Point at a problem => Pareto frontier of survivors + theory render + a
complete trace; a gamma-call yields VS_K schema-valid candidates;
anti-relapse blocks a re-submitted refuted idea.
"""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.loop import run_problem
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Rule, Status
from deepreason.rules.conj import conj
from deepreason.views.theory import theory


def _vs(*contents, refs=None) -> str:
    return json.dumps(
        {
            "candidates": [
                {"content": c, "typicality": round(0.9 - 0.2 * i, 2), "refs": refs or []}
                for i, c in enumerate(contents)
            ]
        }
    )


NO_ATTACK = json.dumps({"attack": False, "case": ""})


def _setup(harness: Harness) -> None:
    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _adapter(harness, conj_responses, critic_responses=None) -> LLMAdapter:
    endpoints = {"conjecturer": MockEndpoint(conj_responses)}
    if critic_responses is not None:
        endpoints["argumentative_critic"] = MockEndpoint(critic_responses)
    return LLMAdapter(endpoints, harness.blobs, retry_max=2)


def test_gamma_call_yields_vs_k_candidates(harness):
    _setup(harness)
    config = Config(VS_K=3)
    adapter = _adapter(
        harness,
        [_vs("moon pull 1", "moon pull 2", "moon resonance 3")],
    )
    admitted = conj(harness, "pi-tides", adapter, config)
    assert len(admitted) == 3
    for artifact in admitted:
        assert artifact.provenance.role.value == "conjecturer"
        assert artifact.interface.commitments == ["k-moon"]  # criteria instantiated
    event = list(harness.log.read())[-1]
    assert event.rule == Rule.CONJ
    assert event.llm is not None  # gamma-call logged with prompt/raw refs
    assert event.inputs == ["pi-tides"]


def test_born_connected_refs_kept(harness):
    _setup(harness)
    seed = harness.create_artifact("prior accepted fact")
    config = Config(VS_K=2)
    adapter = _adapter(
        harness,
        [
            _vs(
                "the moon explains it",
                refs=[
                    {"target": seed.id, "role": "dependence"},
                    {"target": "not-a-real-id", "role": "dependence"},
                ],
            )
        ],
    )
    (artifact,) = conj(harness, "pi-tides", adapter, config)
    assert [r.target for r in artifact.interface.refs] == [seed.id]  # bogus ref dropped
    assert (artifact.id, seed.id) in harness.state.dep


def test_loop_end_to_end(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    _setup(harness)
    config = Config(VS_K=3)
    adapter = _adapter(
        harness,
        [_vs("the moon pulls the sea", "moon resonance in basins", "the tides are magic")],
        [NO_ATTACK] * 3,
    )
    result = run_problem(harness, "pi-tides", adapter, config, cycles=1)

    # Program criticism refuted the criterion-violating candidate.
    survivors = result["survivors"]
    assert len(survivors) == 2
    contents = {harness.state.artifacts[a].content_ref for a in survivors}
    assert "inline:the tides are magic" not in contents
    assert result["frontier"] == survivors  # degenerate frontier at P1 (§11.7)

    # Theory render + complete trace.
    doc = theory(survivors[0], harness.state, harness.blobs, log=harness.log)
    assert "the moon pulls the sea" in doc or "moon resonance" in doc
    rules = [e.rule for e in harness.log.read()]
    assert Rule.CONJ in rules and Rule.CRIT in rules

    # Replay after a full loop is still byte-for-byte.
    assert Harness(root).state.model_dump_json() == harness.state.model_dump_json()


def test_anti_relapse_blocks_resubmitted_refuted_idea(harness):
    _setup(harness)
    config = Config(VS_K=1)
    adapter = _adapter(harness, [_vs("the tides are magic"), _vs("the tides are magic")])
    result = run_problem(harness, "pi-tides", adapter, config, cycles=2)
    assert result["survivors"] == []
    refuted = [a for a, s in harness.state.status.items() if s == Status.REFUTED]
    assert len(refuted) == 1  # registered once, refuted, never re-registered
    assert any(d.get("gate", "").startswith("hash") for d in result["diagnostics"])


def test_gate_block_is_persisted_to_the_log(harness):
    """Stress-campaign T7 fix: a finished run must be auditable for gate
    blocks — every block leaves a Measure event, not just an in-memory
    diagnostic."""
    _setup(harness)
    config = Config(VS_K=1)
    adapter = _adapter(harness, [_vs("the tides are magic"), _vs("the tides are magic")])
    run_problem(harness, "pi-tides", adapter, config, cycles=2)
    gate_measures = [
        e for e in harness.log.read()
        if e.rule.value == "Measure" and e.inputs and e.inputs[0].startswith("gate:")
    ]
    assert len(gate_measures) == 1
    assert gate_measures[0].inputs[2] == "pi-tides"
    # Replay reproduces the same log, blocks included.
    assert any(
        e.inputs and e.inputs[0].startswith("gate:")
        for e in type(harness)(harness.root).log.read()
    )


def test_argumentative_critic_attack_registers(harness):
    _setup(harness)
    # Direct argumentative refutation is the pre-repair authority (RC1):
    # this regression opts into legacy_direct explicitly.
    config = Config(VS_K=1, ARGUMENTATIVE_AUTHORITY="legacy_direct")
    attack_case = json.dumps(
        {"attack": True, "case": "resonance alone cannot explain diurnal asymmetry"}
    )
    adapter = _adapter(harness, [_vs("the moon resonance moon")], [attack_case])
    result = run_problem(harness, "pi-tides", adapter, config, cycles=1)
    assert result["survivors"] == []  # argumentative attack stands unanswered
    (target,) = [a for a, p in harness.state.addr if p == "pi-tides"]
    assert harness.state.status[target] == Status.REFUTED
