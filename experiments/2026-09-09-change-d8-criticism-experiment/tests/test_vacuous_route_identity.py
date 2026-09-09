"""ARM V's contentless objections reach the next candidate by the SAME route.

Implements SPEC S4's second accept / R9. ARM V exists to isolate the CONTENT of
criticism: if it differed from ARM C in the ROUTE its objections travel, then
`C vs V` would measure the route and the arm would answer a question nobody
asked.

The proof is STRUCTURAL rather than statistical, because the mechanism allows it
to be. `discharge/channel.py::_open_with_total` reads the scrutiny Measures and
the attack edges, takes the criticism artifact's TEXT, and carries no field
naming who wrote it — its own comment says so: "Which channel a criticism
arrived through is deliberately NOT carried forward: the writer answers the
criticism, and a field naming its provenance would be a number-shaped invitation
to treat the two as differently weighty." So a bank objection and a model's
objection are the same object to this channel, and these tests hold it to that.

Fixture shape borrowed from `tests/test_discharge_channel.py`: the `observe_only`
criticism — a critic-role artifact plus a `["scrutiny", target, critic]` Measure
and no warrant — which is the population W2 measured as unrouted and the one
both arms actually produce.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

from deepreason.config import Config
from deepreason.discharge import (OpenCriticism, open_criticisms,
                                  render_open_criticism_context, resolve_policy)
from deepreason.harness import Harness
from deepreason.ontology import (Interface, Problem, ProblemProvenance,
                                 Provenance)

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import make_vacuous_bank  # noqa: E402

ON = "discharge-required.v1"

# A real ARM C-shaped objection: it names its target's subject matter.
MODEL_OBJECTION = ("critic: the candidate treats corroboration as a guide to "
                   "future reliability, which is the induction it rejects")


@pytest.fixture
def policy():
    return resolve_policy(Config(DISCHARGE_POLICY=ON))


def _seed(harness):
    return harness.register_problem(Problem(
        id="p-d8", description="state whether the preference is defensible",
        criteria=[],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))


def _candidate(harness, problem):
    return harness.create_artifact(
        "candidate: corroboration is a report on past tests only",
        problem_id=problem.id, provenance=Provenance(role="conjecturer"),
        interface=Interface(refs=[]))


def _scrutiny(harness, target, text):
    """The `observe_only` record shape: a critic artifact, a scrutiny Measure,
    NO warrant. Built exactly as `tests/test_discharge_channel.py` builds it —
    the role on the record is `critic`, the ontology's own value, not the
    ROUTE name `argumentative_critic` that names a seat in the configuration.
    Getting that wrong is how a fixture can look right and pin nothing."""
    critic = harness.create_artifact(text, provenance=Provenance(role="critic"))
    harness.record_measure(inputs=["scrutiny", target.id, critic.id])
    return critic


def _channel(tmp_path, name, objection, policy):
    harness = Harness(tmp_path / name)
    problem = _seed(harness)
    target = _candidate(harness, problem)
    critic = _scrutiny(harness, target, objection)
    return (harness, problem, target, critic,
            open_criticisms(harness, problem.id, policy),
            render_open_criticism_context(harness, problem.id, policy))


def _bank_objection():
    bank = make_vacuous_bank.build(median=600, iqr=(400, 900), count=12,
                                   seed=20260909)
    return bank["entries"][0]["text"]


def test_a_bank_objection_is_open_exactly_as_a_model_objection_is(tmp_path, policy):
    """The load-bearing test: same population, same count, same target."""
    _h, _p, target_c, _c, arm_c, _r = _channel(tmp_path, "armC", MODEL_OBJECTION, policy)
    _h2, _p2, target_v, _c2, arm_v, _r2 = _channel(tmp_path, "armV", _bank_objection(), policy)

    assert len(arm_c) == 1 and len(arm_v) == 1, (arm_c, arm_v)
    assert arm_c[0].target == target_c.id
    assert arm_v[0].target == target_v.id
    # The handle IS the critic artifact id, so it differs by content-addressing.
    # Everything ABOUT the route is the same shape.
    assert arm_c[0].span is None and arm_v[0].span is None


def test_the_channel_carries_no_field_that_could_tell_the_two_apart(tmp_path, policy):
    """A provenance field is what would let a downstream reader weigh a bank
    objection differently, and there is none to read."""
    fields = set(OpenCriticism.model_fields)
    assert fields == {"handle", "claim", "span", "target"}, sorted(fields)
    for forbidden in ("author", "provenance", "source", "role", "model",
                      "endpoint", "family", "seat"):
        assert forbidden not in fields, forbidden


def test_both_render_into_the_same_section_with_the_same_shape(tmp_path, policy):
    """Same section text scaffold, differing only where the objection's own
    words go."""
    _h, _p, _t, _c, _o, render_c = _channel(tmp_path, "armC2", MODEL_OBJECTION, policy)
    _h2, _p2, _t2, _c2, _o2, render_v = _channel(tmp_path, "armV2", _bank_objection(), policy)
    assert render_c is not None and render_v is not None
    # The scaffold is every line that is not the claim body.
    def scaffold(text: str) -> list[str]:
        return [line for line in text.splitlines()
                if not line.strip().startswith(("-", "•")) and "critic" not in line.lower()]
    assert scaffold(render_c)[:1] == scaffold(render_v)[:1], (
        scaffold(render_c)[:1], scaffold(render_v)[:1])


def test_a_bank_objection_renders_a_NON_EMPTY_section(tmp_path, policy):
    """The failure this guards is silent: a channel that rendered None for a
    bank objection would make ARM V a no-criticism arm while its configuration
    said otherwise, and nothing in the record would say so."""
    _h, _p, _t, _c, opened, render = _channel(tmp_path, "armV3", _bank_objection(), policy)
    assert opened, "a bank objection is not OPEN — ARM V would carry no criticism"
    assert render and render.strip(), "a bank objection renders nothing"
    assert len(render) > 100, len(render)


def test_the_bank_objection_really_is_the_vacuous_one(tmp_path, policy):
    """Guards against this file quietly testing a model objection twice, which
    would make every test above pass while proving nothing about the bank."""
    text = _bank_objection()
    for word in ("corroboration", "induction", "reliability", "Popper"):
        assert word.lower() not in text.lower(), (word, text[:120])
