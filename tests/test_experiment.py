"""Experiment design (rules/experiment.py): the system designs its own
experiments. Proposed generators are adjudicated BY THEIR FRUITS (generator_wf:
compile / yield / novelty — deterministic, no judge), and accepted ones are
enumerated by crit_fuzz. Soundness is generator-independent: the frozen gate
admits every input, the frozen checker decides every violation."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
    WarrantType,
)
from deepreason.oracle import (
    check_generator,
    generator_wf_commitment,
    property_oracle_commitment,
)
from deepreason.rules.crit import crit_fuzz
from deepreason.rules.experiment import accepted_generators, propose_generators
from deepreason.scheduler.scheduler import Scheduler

CHECKER = (
    "def check(inp, out):\n"
    "    xs = inp[0]\n"
    "    return isinstance(out, list) and sorted(xs) == out\n"
)
GATE = (
    "def valid(inp):\n"
    "    if not isinstance(inp, list) or len(inp) != 1:\n"
    "        return False\n"
    "    xs = inp[0]\n"
    "    if not isinstance(xs, list) or len(xs) > 20:\n"
    "        return False\n"
    "    for x in xs:\n"
    "        if not isinstance(x, int):\n"
    "            return False\n"
    "    return True\n"
)
FROZEN = [[[3, 1, 2]]]
GOOD_GEN = (
    "def gen(k):\n"
    "    n = 1 + k % 4\n"
    "    xs = []\n"
    "    j = k\n"
    "    for i in range(n):\n"
    "        xs.append((j * 7 + i * 3) % 10)\n"
    "        j = j // 2 + 1\n"
    "    return [xs]\n"
)
LOW_YIELD_GEN = "def gen(k):\n    return [['not', 'ints']]\n"       # gate rejects all
CONSTANT_GEN = "def gen(k):\n    return [[3, 1, 2]]\n"              # replays frozen suite
# Passes the frozen input (len 3) but wrong on short lists.
SNEAKY = (
    "def solve(xs):\n"
    "    if len(xs) > 2:\n"
    "        return sorted(xs)\n"
    "    return xs\n"
)


def _base():
    # NO spec generator, NO input contract: the system must design its own.
    return property_oracle_commitment("solve", FROZEN, CHECKER, GATE)


# ---- generator_wf: adjudication by fruits, mechanically ----

def test_check_generator_passes_a_productive_generator():
    verdict, detail = check_generator(GOOD_GEN, GATE, FROZEN)
    assert verdict == "pass" and detail["novel"] is True


def test_check_generator_fails_noncompiling_and_low_yield_and_constant():
    v1, d1 = check_generator("import os", GATE, FROZEN)
    assert v1 == "fail" and "generator" in d1["error"]
    v2, d2 = check_generator(LOW_YIELD_GEN, GATE, FROZEN)
    assert v2 == "fail" and "yield too low" in d2["error"]
    v3, d3 = check_generator(CONSTANT_GEN, GATE, FROZEN)
    assert v3 == "fail" and "no novel input" in d3["error"]


def test_generator_wf_commitment_is_derived_and_content_addressed():
    base = _base()
    wf = generator_wf_commitment(base)
    assert wf is not None and wf.id.startswith("gen-wf@")
    assert wf.id == generator_wf_commitment(base).id
    from deepreason.oracle import exec_oracle_commitment

    assert generator_wf_commitment(exec_oracle_commitment("f", [])) is None


# ---- propose_generators: register, adjudicate on arrival ----

def _experimenter(harness, *gen_lists):
    return LLMAdapter(
        {"conjecturer": MockEndpoint(
            [json.dumps({"generators": gens}) for gens in gen_lists]
        )},
        harness.blobs,
        retry_max=2,
    )


def test_propose_registers_and_mechanically_adjudicates(harness):
    base = _base()
    harness.register_commitment(base)
    adapter = _experimenter(harness, [GOOD_GEN, LOW_YIELD_GEN, CONSTANT_GEN])
    survivors = propose_generators(harness, base, adapter, Config())
    assert len(survivors) == 1  # only the productive design survived
    accepted = accepted_generators(harness, base.id)
    assert [src for _, src in accepted] == [GOOD_GEN]
    # The rejects are REFUTED artifacts (not deleted — D8), by demonstrative
    # generator_wf warrants: mechanical adjudication, no judge anywhere.
    statuses = [
        harness.state.status[a.id]
        for a in harness.state.artifacts.values()
        if a.codec == "code:python-gen"
    ]
    assert statuses.count(Status.REFUTED) == 2
    gen_warrants = [
        w for w in harness.warrants.values() if w.commitment and
        w.commitment.startswith("gen-wf@")
    ]
    assert len(gen_warrants) == 2
    assert all(w.type == WarrantType.DEMONSTRATIVE for w in gen_warrants)


# ---- the payoff: a self-designed experiment kills the Goodhart trap ----

def test_fuzz_kills_trap_with_a_proposed_generator(harness):
    base = _base()
    harness.register_commitment(base)
    trap = harness.create_artifact(
        SNEAKY, codec="code:python",
        interface=Interface(commitments=[base.id]),
        provenance=Provenance(role="conjecturer"),
    )
    # Spec has no generator: fuzz alone is blind.
    assert crit_fuzz(harness, trap.id, Config()) is None
    assert harness.state.status[trap.id] == Status.ACCEPTED
    # The experimenter designs the probe; fuzz now sees with it.
    propose_generators(harness, base, _experimenter(harness, [GOOD_GEN]), Config())
    critic = crit_fuzz(harness, trap.id, Config())
    assert critic is not None
    assert harness.state.status[trap.id] == Status.REFUTED
    w = next(w for w in harness.warrants.values() if w.target == trap.id)
    assert w.type == WarrantType.DEMONSTRATIVE
    # Credit flows in the graph: the nu MENTIONS the generator that designed
    # the killing experiment.
    gen_id = accepted_generators(harness, base.id)[0][0]
    nu = harness.state.artifacts[w.validity_node]
    assert any(r.target == gen_id for r in nu.interface.refs)


def test_experiment_pack_shows_the_survivors_code(harness):
    from deepreason.llm.packs import render_experiment_pack
    from deepreason.rules.experiment import _survivor_heads

    base = _base()
    harness.register_commitment(base)
    trap = harness.create_artifact(
        SNEAKY, codec="code:python",
        interface=Interface(commitments=[base.id]),
        provenance=Provenance(role="conjecturer"),
    )
    heads = _survivor_heads(harness, base.id)
    assert len(heads) == 1 and "if len(xs) > 2:" in heads[0]
    pack = render_experiment_pack(base, [], token_budget=4000, targets=heads)
    assert "STANDING SURVIVORS" in pack
    assert "if len(xs) > 2:" in pack  # the experimenter reads the code it probes
    assert trap.id[:12] in pack


def test_refuted_generators_are_never_used(harness):
    base = _base()
    harness.register_commitment(base)
    propose_generators(harness, base, _experimenter(harness, [LOW_YIELD_GEN]), Config())
    assert accepted_generators(harness, base.id) == []


# ---- scheduler: the loop designs, adjudicates, and kills on its own ----

def test_scheduler_designs_its_own_experiment_and_kills_the_trap(tmp_path):
    harness = Harness(tmp_path / "run")
    base = _base()
    harness.register_commitment(base)
    harness.register_problem(
        Problem(
            id="pi-sort",
            description="return the input list sorted ascending",
            criteria=[base.id],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    trap = harness.create_artifact(
        SNEAKY, codec="code:python",
        interface=Interface(commitments=[base.id]),
        provenance=Provenance(role="conjecturer"),
    )
    conj = json.dumps({"candidates": [
        {"content": "def solve(xs):\n    return sorted(xs)", "typicality": 0.9},
    ]})
    gens = json.dumps({"generators": [GOOD_GEN]})
    adapter = LLMAdapter(
        {
            # step 1: conj, then the experimenter design call; step 2: conj.
            "conjecturer": MockEndpoint([conj, gens, conj]),
            "argumentative_critic": MockEndpoint(
                lambda prompt: json.dumps({"cases": [
                    {"target": line.split()[1], "attack": False, "case": ""}
                    for line in prompt.splitlines() if line.startswith("TARGET ")
                ]}) if "TARGETS" in prompt else json.dumps({"attack": False, "case": ""})
            ),
        },
        harness.blobs,
        retry_max=2,
    )
    config = Config(VS_K=1, N_SCHOOLS=0, CRIT_BATCH_K=4, ARG_CRIT_PER_CYCLE=4,
                    GEN_PROPOSE_PERIOD=1, GEN_MAX=1)
    scheduler = Scheduler(harness, adapter, config)
    scheduler.step()  # trap fuzz-passes (no generator yet); experimenter designs
    assert accepted_generators(harness, base.id)  # the design was accepted
    scheduler.step()  # fuzz-clean cache was cleared: the trap is re-probed
    assert harness.state.status[trap.id] == Status.REFUTED
    w = next(w for w in harness.warrants.values() if w.target == trap.id)
    assert w.type == WarrantType.DEMONSTRATIVE  # killed by its own experiment


def test_fuzz_sweep_is_not_rationed_behind_llm_slots(tmp_path):
    """Deterministic criticism runs even when every ARG_CRIT_PER_CYCLE slot
    is taken by fresh admits — fuzz costs sandbox steps, not tokens, so the
    trap must die via _fuzz_sweep with ZERO leftover critic capacity."""
    harness = Harness(tmp_path / "run")
    base = _base()
    harness.register_commitment(base)
    harness.register_problem(
        Problem(
            id="pi-sort",
            description="return the input list sorted ascending",
            criteria=[base.id],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    trap = harness.create_artifact(
        SNEAKY, codec="code:python",
        interface=Interface(commitments=[base.id]),
        provenance=Provenance(role="conjecturer"),
    )
    good = json.dumps({"candidates": [
        {"content": "def solve(xs):\n    return sorted(xs)", "typicality": 0.9},
    ]})
    gens = json.dumps({"generators": [GOOD_GEN]})
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint([good, gens, good]),
            "argumentative_critic": MockEndpoint(
                lambda prompt: json.dumps({"attack": False, "case": ""})
            ),
        },
        harness.blobs,
        retry_max=2,
    )
    # ARG_CRIT_PER_CYCLE=1 and one fresh accepted admit per cycle: the
    # standing arg-crit sweep NEVER gets a slot.
    config = Config(VS_K=1, N_SCHOOLS=0, ARG_CRIT_PER_CYCLE=1,
                    GEN_PROPOSE_PERIOD=1, GEN_MAX=1)
    scheduler = Scheduler(harness, adapter, config)
    scheduler.step()
    scheduler.step()
    assert harness.state.status[trap.id] == Status.REFUTED
