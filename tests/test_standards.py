"""P5 acceptance (e)+(f) (spec §16): refuting a standard collapses its
verdicts and reinstates targets (closure, replayed); a user ruling enters
the next judge pack's precedent slice and is itself attacked/reinstated.
Plus holdout/Reveal (§10.5)."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal import appellate, holdout
from deepreason.informal.standards import precedent_slice, register_standard, resolve_standard
from deepreason.informal.trial import run_trial
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Interface, Provenance, Status
from deepreason.research.backends import covered, pending
from deepreason.rules.spawn import scan_spawns
from tests.conftest import art, attack

CASE = "the passage uses parallel fifths in bar 3, violating clause 2"
FAIL = json.dumps({"verdict": "fail", "decisive_point": "parallel fifths in bar 3"})
PARAPHRASES = json.dumps(
    {"edits": [{"content": "bar 3: consecutive fifths, contra clause 2"},
               {"content": "the fifths at bar 3 breach clause 2"}]}
)


def _trial_adapter(harness, judge_responses):
    return LLMAdapter(
        {
            "argumentative_critic": MockEndpoint([json.dumps({"attack": True, "case": CASE})]),
            "defender": MockEndpoint([json.dumps({"answer": "it is an echo effect"})]),
            "judge": MockEndpoint(judge_responses),
            "variator": MockEndpoint([PARAPHRASES]),
        },
        harness.blobs, retry_max=2,
    )


def test_standard_refutation_collapses_and_reinstates_replayed(tmp_path):
    """Parallel fifths, end to end: the productive attack lands on the
    standard, and everything under it falls — computed, not curated."""
    root = tmp_path / "run"
    harness = Harness(root)
    standard = register_standard(harness, "std-1", "clause 2: no parallel fifths")
    kappa = Commitment(id="kappa-taste", eval="rubric:std-1")
    harness.register_commitment(kappa)
    target = art(harness, "a chorale passage with parallel fifths in bar 3",
                 interface=Interface(commitments=["kappa-taste"]))
    run_trial(harness, target.id, kappa, _trial_adapter(harness, [FAIL] * 3),
              Config(TRIAL_PARAPHRASE_N=2))
    assert harness.state.status[target.id] == Status.REFUTED

    attack(harness, standard.id, "fifths-are-fine-now")  # the Beethoven move
    status = harness.state.status
    assert status[standard.id] == Status.REFUTED
    assert status[target.id] == Status.ACCEPTED  # reinstated via closure
    assert Harness(root).state.model_dump_json() == harness.state.model_dump_json()


def test_user_ruling_enters_precedent_slice_and_is_revisable(harness):
    """Acceptance (f): authority is pack ordering, never status privilege."""
    standard = register_standard(harness, "std-1", "clause 2: no parallel fifths")
    # An ordinary (non-user) precedent first.
    harness.create_artifact(
        json.dumps({"precedent": {"case": "old-case", "holding": "fifths in echo passages are tolerable"}}),
        codec="json",
        interface=Interface(refs=[{"target": standard.id, "role": "mention"}]),
        provenance=Provenance(role="critic"),
    )
    ruling = appellate.rule(harness, "case-42", "fifths that outline the tonic triad violate clause 2",
                            "std-1")
    slice_ = precedent_slice(harness, standard.id, k=3)
    assert slice_[0]["id"] == ruling.id and slice_[0]["user"]  # user rulings first

    # The ruling reaches the judge's prompt on the next trial.
    kappa = Commitment(id="kappa-taste", eval="rubric:std-1")
    harness.register_commitment(kappa)
    target = art(harness, "a chorale passage with parallel fifths in bar 3",
                 interface=Interface(commitments=["kappa-taste"]))
    adapter = _trial_adapter(harness, [FAIL] * 3)
    run_trial(harness, target.id, kappa, adapter, Config(TRIAL_PARAPHRASE_N=2))
    judge_prompt = harness.blobs.get(
        next(e.llm.prompt_ref for e in harness.log.read() if e.llm and e.llm.role == "judge")
    ).decode()
    assert "fifths that outline the tonic triad" in judge_prompt

    # N1: the ruling is an ordinary artifact — attacked, it leaves the slice;
    # attack the attacker and it returns.
    critic, _ = attack(harness, ruling.id, "ruling-overbroad")
    assert all(p["id"] != ruling.id for p in precedent_slice(harness, standard.id, 3))
    attack(harness, critic.id, "objection-fails")
    assert precedent_slice(harness, standard.id, 3)[0]["id"] == ruling.id


def test_docket_is_disagreement_ranked_and_capped(harness):
    register_standard(harness, "std-1", "clause 2")
    for _ in range(3):
        harness.record_measure(inputs=["trial-blocked:ensemble-split", "case-x"])
    harness.record_measure(inputs=["trial-blocked:paraphrase-flip", "case-y"])
    entries = appellate.docket(harness, Config(USER_RULINGS_BUDGET=1))
    assert len(entries) == 1  # capped: the user is the scarce resource
    assert entries[0]["case"] == "case-x"  # most-confused first


def test_holdout_sealed_then_revealed(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.register_commitment(
        Commitment(id="k-obs", eval="predicate:True", observation_valued=True)
    )
    candidate = harness.create_artifact(
        "the moon pulls the sea",
        interface=Interface(commitments=["k-obs"]),
        provenance=Provenance(role="conjecturer"),
    )
    rid = f"research:k-obs:{candidate.id[:12]}"
    scan_spawns(harness, Config(FLOOR=0))
    assert rid in harness.state.problems

    sealed = holdout.seal(harness, b"novel tide measurements, 2026", problem_id=rid)
    assert holdout.is_sealed(harness, sealed)
    assert not covered(harness, rid)   # sealed does not count as covering
    assert pending(harness, rid)       # ...but no premature research Spawn
    scan_spawns(harness, Config(FLOOR=0))
    research_problems = [p for p in harness.state.problems if p.startswith("research:")]
    assert research_problems == [rid]  # scheduled-pending, not re-spawned

    holdout.reveal(harness, sealed.id)
    assert not holdout.is_sealed(harness, sealed)
    assert covered(harness, rid)
    assert harness.blobs.get(sealed.content_ref) == b"novel tide measurements, 2026"
    # The Reveal event replays: a reopened harness can read the bytes too.
    reopened = Harness(root)
    assert reopened.blobs.get(sealed.content_ref) == b"novel tide measurements, 2026"
    assert reopened.state.model_dump_json() == harness.state.model_dump_json()


def test_resolve_standard_latest_wins(harness):
    first = register_standard(harness, "std-9", "v1 rubric")
    second = register_standard(harness, "std-9", "v2 rubric: revised")
    assert first.id != second.id
    assert resolve_standard(harness, "std-9").id == second.id  # succession
