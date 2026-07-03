"""P2 acceptance (spec §16): an easy-to-vary relation draws an hv-floor
warrant, lands refuted (never suspended), reinstates via nu-attack, and
replays byte-for-byte. Lazy HV spot-checks log into state.hv via Measure
events and survive reload."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.measures.hv import hv_floor_commitment, hv_spot_check, run_hv_floor
from deepreason.ontology import Commitment, Interface, Provenance, Ref, Rule, Status
from deepreason.programs import FAIL, PASS
from tests.conftest import art, attack


def _edits(*contents) -> str:
    return json.dumps({"edits": [{"content": c} for c in contents]})


def _variator(harness, responses) -> LLMAdapter:
    return LLMAdapter({"variator": MockEndpoint(responses)}, harness.blobs, retry_max=2)


def _relation(harness, config, text="A and B both involve energy"):
    a = art(harness, "theory A: energy is conserved")
    b = art(harness, "theory B: entropy increases")
    floor = hv_floor_commitment(config)
    harness.register_commitment(floor)
    relation = harness.create_artifact(
        text,
        interface=Interface(
            commitments=[floor.id],
            refs=[Ref(target=a.id, role="dependence"), Ref(target=b.id, role="dependence")],
        ),
        provenance=Provenance(role="synthesizer"),
    )
    return relation, floor


def test_easy_to_vary_relation_refuted_and_reinstated(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    config = Config(HV_K=4, HV_MIN=0.5)
    relation, floor = _relation(harness, config)
    # Every edit is a distinct inequivalent survivor => s_hat=1 => HV=0 < HV_MIN.
    adapter = _variator(
        harness,
        [_edits("both involve heat", "both involve momentum", "both involve fields",
                "both involve chemistry")],
    )
    verdict = run_hv_floor(harness, adapter, relation.id, floor)
    assert verdict == FAIL
    assert harness.state.status[relation.id] == Status.REFUTED  # refuted, never suspended
    # Endpoints stay accepted: the relation fell, not what it relates (§4).
    warrant = next(w for w in harness.warrants.values() if w.target == relation.id)
    assert warrant.commitment == floor.id
    trace = json.loads(harness.blobs.get(warrant.trace_ref))
    assert trace["s_hat"] == 1.0 and trace["k"] == 4

    # Reinstatement = attack nu ("the counted survivors are ~=-equivalent...").
    attack(harness, warrant.validity_node, "s-hat-inflated")
    assert harness.state.status[relation.id] == Status.ACCEPTED

    # Byte-for-byte replay of the whole episode.
    assert Harness(root).state.model_dump_json() == harness.state.model_dump_json()


def test_hard_to_vary_relation_passes(harness):
    config = Config(HV_K=3, HV_MIN=0.5)
    # Give the relation a real battery so edits can fail it.
    harness.register_commitment(
        Commitment(id="k-energy", eval="predicate:'energy' in content and 'entropy' in content")
    )
    a = art(harness, "theory A: energy is conserved")
    b = art(harness, "theory B: entropy increases")
    floor = hv_floor_commitment(config)
    harness.register_commitment(floor)
    relation = harness.create_artifact(
        "energy conservation bounds entropy production in closed systems",
        interface=Interface(
            commitments=["k-energy", floor.id],
            refs=[Ref(target=a.id, role="dependence"), Ref(target=b.id, role="dependence")],
        ),
        provenance=Provenance(role="synthesizer"),
    )
    # Edits break the battery => no inequivalent survivors => HV=1 >= HV_MIN.
    adapter = _variator(
        harness, [_edits("momentum bounds it", "chemistry bounds it", "fields bound it")]
    )
    verdict = run_hv_floor(harness, adapter, relation.id, floor)
    assert verdict == PASS
    assert harness.state.status[relation.id] == Status.ACCEPTED
    assert harness.state.hv[relation.id] == 1.0  # estimate logged via Measure


def test_spot_check_logs_and_survives_reload(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    target = art(harness, "the moon pulls the sea", interface=Interface(commitments=["k-moon"]))
    adapter = _variator(
        harness, [_edits("the moon pushes the sea", "the sun pulls the sea", "the moon pulls the sea!")]
    )
    hv = hv_spot_check(harness, adapter, target.id, k=3)
    # "moon pushes" survives (passes, inequivalent); "sun pulls" fails k-moon;
    # "moon pulls the sea!" normalizes to the original => equivalent.
    assert hv == 1.0 - (1 / 3)
    events = list(harness.log.read())
    assert events[-1].rule == Rule.MEASURE and events[-1].llm is not None
    reopened = Harness(root)
    assert reopened.state.hv[target.id] == hv  # frontier data persists
