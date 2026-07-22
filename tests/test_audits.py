"""P5 acceptance (d) (spec §16): planted-flaw battery yields a measured
judge error rate; a paraphrase-flip audit registers a program warrant
against a nu; a self-preference probe logs a measured bias."""

import json

import pytest

from deepreason.config import Config
from deepreason.informal.audits import (
    bias_probes,
    paraphrase_invariance_audit,
    planted_flaw_calibration,
    premise_deletion_audit,
)
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import run_trial
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import JudgeEnsemblePolicyError
from deepreason.ontology import Commitment, Interface, Status
from tests.conftest import art

CASE = "the passage uses parallel fifths in bar 3, violating clause 2"
FAIL = json.dumps({"verdict": "fail", "decisive_point": "parallel fifths in bar 3"})
PASS = json.dumps({"verdict": "pass", "decisive_point": "parallel fifths in bar 3"})
PARAPHRASES = json.dumps(
    {"edits": [{"content": "bar 3 has consecutive fifths, contra clause 2"},
               {"content": "clause 2 is violated by the fifths at bar 3"}]}
)


def _judges(first, second=None):
    return [
        MockEndpoint(
            first,
            name="mock://judge-gemma",
            model="gemma-test",
        ),
        MockEndpoint(
            first if second is None else second,
            name="mock://judge-qwen",
            model="qwen-test",
        ),
    ]


def _refute_by_trial(harness) -> tuple[str, str]:
    """Returns (target_id, nu_id) for a trial-refuted target."""
    register_standard(harness, "std-1", "clause 2: no parallel fifths")
    kappa = Commitment(id="kappa-taste", eval="rubric:std-1")
    harness.register_commitment(kappa)
    target = art(harness, "a chorale passage with parallel fifths in bar 3",
                 interface=Interface(commitments=["kappa-taste"]))
    adapter = LLMAdapter(
        {
            "argumentative_critic": MockEndpoint([json.dumps({"attack": True, "case": CASE})]),
            "defender": MockEndpoint([json.dumps({"answer": "it is an echo effect"})]),
            "judge": [
                MockEndpoint(
                    [FAIL, FAIL, FAIL],
                    name="mock://judge-gemma",
                    model="gemma-test",
                ),
                MockEndpoint(
                    [FAIL, FAIL, FAIL],
                    name="mock://judge-qwen",
                    model="qwen-test",
                ),
            ],
            "variator": MockEndpoint([PARAPHRASES]),
        },
        harness.blobs, retry_max=2,
    )
    run_trial(
        harness, target.id, kappa, adapter, Config(TRIAL_PARAPHRASE_N=2),
        authority="status",
    )
    assert harness.state.status[target.id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    return target.id, warrant.validity_node


def test_paraphrase_flip_audit_attacks_nu_and_reinstates(harness):
    target_id, nu_id = _refute_by_trial(harness)
    # Audit replay: the judge now flips on a paraphrase — the original
    # ruling was easy to vary.
    audit_adapter = LLMAdapter(
        {
            "judge": _judges([PASS, FAIL]),
            "variator": MockEndpoint([PARAPHRASES]),
        },
        harness.blobs, retry_max=2,
    )
    hits = paraphrase_invariance_audit(harness, audit_adapter, Config(TRIAL_PARAPHRASE_N=2))
    assert len(hits) == 1
    # Program warrant landed on the nu; closure fells the rubric warrant;
    # the target reinstates — the full force of the graph (§10.4).
    assert harness.state.status[nu_id] == Status.REFUTED
    assert harness.state.status[target_id] == Status.ACCEPTED
    audit_warrant = next(w for w in harness.warrants.values() if w.target == nu_id)
    assert audit_warrant.commitment == "audit:paraphrase-invariance"


def test_premise_deletion_audit(harness):
    target_id, nu_id = _refute_by_trial(harness)
    # Verdict survives deletion of its own decisive_point => hit.
    audit_adapter = LLMAdapter(
        {"judge": _judges([FAIL])}, harness.blobs, retry_max=2
    )
    hits = premise_deletion_audit(harness, audit_adapter, Config())
    assert len(hits) == 1
    assert harness.state.status[nu_id] == Status.REFUTED


def test_planted_flaw_calibration_measures_error_rate(harness):
    calibration = [
        ("this argument assumes its own conclusion", True),      # circular
        ("winter happens because the gods will it", True),       # vacuous
        ("tides correlate with lunar position, mechanism given", False),
        ("the derivation follows from the axioms stated", False),
    ]
    # Judge errs once: calls the second flaw clean.
    responses = [FAIL, PASS, PASS, PASS]
    adapter = LLMAdapter(
        {"judge": _judges(responses)}, harness.blobs, retry_max=2
    )
    config = Config(JUDGE_ERR_MAX=0.1)
    rate = planted_flaw_calibration(harness, adapter, config, calibration, "no bad reasoning")
    assert rate == 0.25  # measured, ground truth by construction
    measures = [e for e in harness.log.read()
                if any(t.startswith("judge-error-rate:") for t in e.inputs)]
    assert measures
    assert "audit:planted-flaw-error-rate" in harness.state.problems  # > JUDGE_ERR_MAX


def test_bias_probes_log_measured_bias(harness):
    own = "a crisp account of the tides via differential gravity"
    foreign = "an equally crisp account of the tides via differential gravity, restated"
    # Judge always prefers the own-family probe wherever it is presented.
    def prefer_probe(prompt: str) -> str:
        label = "A" if prompt.index(own) < prompt.index(foreign) else "B"
        return json.dumps({"winner": label, "decisive_point": ""})

    adapter = LLMAdapter(
        {"judge": _judges(prefer_probe)}, harness.blobs, retry_max=2
    )
    result = bias_probes(
        harness, adapter, Config(),
        self_preference_pairs=[(own, foreign)],
        verbosity_pairs=[],
    )
    assert result["self_preference"] == 1.0  # systematic — a measured bias
    measures = [e for e in harness.log.read()
                if any(t.startswith("judge-self-preference:") for t in e.inputs)]
    assert measures


def test_warrant_audits_are_noop_without_rubric_warrants(harness):
    """Program/rubric-forbid roots have nothing to audit and therefore do
    not need judge or variator routes merely because the periodic sweep ran."""
    adapter = LLMAdapter({}, harness.blobs, retry_max=2)
    before_events = len(list(harness.log.read()))

    assert paraphrase_invariance_audit(harness, adapter, Config()) == []
    assert premise_deletion_audit(harness, adapter, Config()) == []
    assert len(list(harness.log.read())) == before_events


@pytest.mark.parametrize("audit_path", ["paraphrase", "premise", "calibration", "bias"])
@pytest.mark.parametrize("judge_shape", ["missing", "one-family"])
def test_audit_paths_preflight_ensemble_before_any_spend(
    harness, audit_path, judge_shape
):
    """Every graph-capable audit rejects a missing/single judge before even
    the variator can run, and before any audit event mutates the root."""
    if audit_path in {"paraphrase", "premise"}:
        _refute_by_trial(harness)

    endpoint_calls = []

    def counted(response):
        def complete(_prompt):
            endpoint_calls.append(response)
            return response

        return complete

    endpoints = {
        "variator": MockEndpoint(counted(PARAPHRASES)),
    }
    if judge_shape == "one-family":
        endpoints["judge"] = MockEndpoint(
            counted(FAIL), name="mock://judge-gemma", model="gemma-test"
        )
    adapter = LLMAdapter(endpoints, harness.blobs, retry_max=2)
    before_events = len(list(harness.log.read()))

    with pytest.raises(JudgeEnsemblePolicyError):
        if audit_path == "paraphrase":
            paraphrase_invariance_audit(
                harness, adapter, Config(TRIAL_PARAPHRASE_N=1)
            )
        elif audit_path == "premise":
            premise_deletion_audit(harness, adapter, Config())
        elif audit_path == "calibration":
            planted_flaw_calibration(
                harness, adapter, Config(), [("a planted flaw", True)], "rubric"
            )
        else:
            bias_probes(
                harness,
                adapter,
                Config(),
                self_preference_pairs=[("probe", "control")],
            )

    assert endpoint_calls == []
    assert len(list(harness.log.read())) == before_events


def test_paraphrase_audit_ensemble_split_fails_closed_and_accounts_all_calls(
    harness,
):
    target_id, nu_id = _refute_by_trial(harness)
    meter = TokenMeter()
    adapter = LLMAdapter(
        {
            "judge": _judges([PASS], [FAIL]),
            "variator": MockEndpoint([PARAPHRASES]),
        },
        harness.blobs,
        retry_max=2,
        meter=meter,
    )
    before_seq = len(list(harness.log.read()))

    hits = paraphrase_invariance_audit(
        harness, adapter, Config(TRIAL_PARAPHRASE_N=1)
    )

    assert hits == []
    assert harness.state.status[nu_id] == Status.ACCEPTED
    assert harness.state.status[target_id] == Status.REFUTED
    audit_events = [event for event in harness.log.read() if event.seq >= before_seq]
    logged_calls = [event.llm for event in audit_events if event.llm]
    assert meter.calls == len(logged_calls) == 3  # variator + both judge seats
    assert sum(call.tokens for call in logged_calls) == meter.total
    assert any(
        event.inputs and event.inputs[0] == "audit-blocked:ensemble-split"
        for event in audit_events
    )


def test_premise_deletion_ensemble_split_cannot_attack_nu(harness):
    target_id, nu_id = _refute_by_trial(harness)
    adapter = LLMAdapter(
        {"judge": _judges([FAIL], [PASS])}, harness.blobs, retry_max=2
    )

    assert premise_deletion_audit(harness, adapter, Config()) == []
    assert harness.state.status[nu_id] == Status.ACCEPTED
    assert harness.state.status[target_id] == Status.REFUTED


def test_calibration_split_returns_no_rate_and_spawns_nothing(harness):
    adapter = LLMAdapter(
        {"judge": _judges([FAIL], [PASS])}, harness.blobs, retry_max=2
    )

    rate = planted_flaw_calibration(
        harness,
        adapter,
        Config(JUDGE_ERR_MAX=0.0),
        [("a planted flaw", True)],
        "no bad reasoning",
    )

    assert rate is None
    assert "audit:planted-flaw-error-rate" not in harness.state.problems
    assert not any(
        event.inputs and event.inputs[0].startswith("judge-error-rate:")
        for event in harness.log.read()
    )


def test_bias_split_produces_no_single_seat_measurement(harness):
    a_ruling = json.dumps({"winner": "A", "decisive_point": ""})
    b_ruling = json.dumps({"winner": "B", "decisive_point": ""})
    adapter = LLMAdapter(
        {"judge": _judges([a_ruling], [b_ruling])},
        harness.blobs,
        retry_max=2,
    )

    result = bias_probes(
        harness,
        adapter,
        Config(),
        self_preference_pairs=[("probe", "control")],
    )

    assert result == {"self_preference": None, "verbosity": None}
    assert not any(
        event.inputs and event.inputs[0].startswith("judge-self-preference:")
        for event in harness.log.read()
    )
