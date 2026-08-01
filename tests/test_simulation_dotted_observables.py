"""An observable may name a cell of a nested result, and the schema says so.

Regression (jolt run-b4d6dfda0c20676a864a051fbc97bda4): the run died at cycle 0
with `simulation observables must be plain identifiers` at
`/requested_observables`. The model had designed a 3x2x3 measurement grid,
returned it nested — the natural shape for a grid — and named the cells
`animal.baseline.distinct`. The identifier rule appeared in neither the rendered
schema nor the field's description, so the refusal was the first statement of
it, and four repair attempts never converged.

Two claims are pinned here. Dotted names are accepted end to end, and the rule
that governs them is visible in the schema rather than discovered by rejection.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.capabilities.models import (
    OBSERVABLE_NAME_PATTERN,
    SimulationProposalDraftV1,
)
from deepreason.llm.wire import SimulationProposalWireV1
from deepreason.simulation.compiler import (
    DeclarativeSimulationError,
    compile_declarative_numeric,
)
from deepreason.verification.contained import CONTAINED_WORKER_SOURCE_V1
from deepreason.verification.simulation import _resolve_observable


def _worker():
    """The contained worker is a SOURCE STRING executed in a subprocess, so it
    has to be exec'd to be tested at all — importing the module would test
    something that never runs under containment.
    """

    namespace: dict = {}
    exec(compile(CONTAINED_WORKER_SOURCE_V1, "<contained-worker>", "exec"), namespace)
    return namespace


resolve_observable = _worker()["resolve_observable"]

#: Verbatim from the rejected proposal's diagnostic blob,
#: sha256:a91ae25a…, in the jolt run's `blobs/`.
_REJECTED_NAMES = (
    "animal.baseline.distinct",
    "animal.baseline.top_mass",
    "animal.baseline.normalized_entropy",
    "animal.schools.distinct",
    "animal.schools.top_mass",
    "animal.schools.normalized_entropy",
    "animal.temperature_max.distinct",
    "animal.temperature_max.top_mass",
    "animal.temperature_max.normalized_entropy",
    "random_number.baseline.distinct",
    "random_number.baseline.top_mass",
    "random_number.baseline.normalized_entropy",
    "random_number.schools.distinct",
    "random_number.schools.top_mass",
    "random_number.schools.normalized_entropy",
    "random_number.temperature_max.distinct",
    "random_number.temperature_max.top_mass",
    "random_number.temperature_max.normalized_entropy",
)


def _proposal(names):
    return {
        "request_identifier": "jolt-grid",
        "hypothesis": "schools reduce collapse",
        "rival_predictions": ["entropy rises", "entropy is unchanged"],
        "discriminating_purpose": "separate the two",
        "simulation_mode": "sandboxed_python_v1",
        "model_source": "def simulate(inputs, rng):\n    return {}\n",
        "requested_observables": list(names),
        "interpretation_conditions": ["treat a tie as unchanged"],
    }


@pytest.mark.parametrize(
    "model", [SimulationProposalWireV1, SimulationProposalDraftV1]
)
def test_the_eighteen_names_that_killed_the_jolt_run_are_accepted(model):
    """Both models, because a wire that merely advertises a rule the draft
    enforces just moves the rejection one layer later.
    """

    assert model.model_validate(_proposal(_REJECTED_NAMES))


@pytest.mark.parametrize(
    "model", [SimulationProposalWireV1, SimulationProposalDraftV1]
)
@pytest.mark.parametrize(
    "name",
    [
        "bad name",
        ".leading",
        "trailing.",
        "double..dot",
        "9starts_with_digit",
        "a.b.c.d.e.f.g.h.i",  # nine segments; eight is the bound
    ],
)
def test_a_malformed_observable_is_still_refused(model, name):
    with pytest.raises(ValidationError):
        model.model_validate(_proposal([name]))


def test_the_two_sibling_rules_the_same_sweep_missed_are_also_in_the_schema():
    """Found by asking what else on this contract the C8 survey walked past.

    Both are draft-side validators in `capabilities/models.py` whose rules the
    wire model did not restate, which is exactly how the observable pattern
    stayed invisible. `input_aliases` matters most: the jolt question exposes
    sealed simulation inputs, so a mis-cased alias is a live way to lose a run.
    """

    properties = SimulationProposalWireV1.model_json_schema()["properties"]

    assert properties["input_aliases"]["items"]["pattern"] == r"^[A-Z][A-Z0-9_]{0,31}$"
    seed = properties["requested_seed_set"]["items"]
    assert (seed["minimum"], seed["maximum"]) == (-(2**63), 2**63 - 1)

    for model in (SimulationProposalWireV1, SimulationProposalDraftV1):
        with pytest.raises(ValidationError):
            model.model_validate({**_proposal(["ok"]), "input_aliases": ["sim_001"]})
        with pytest.raises(ValidationError):
            model.model_validate({**_proposal(["ok"]), "requested_seed_set": [2**63]})


def test_the_rule_is_in_the_schema_and_not_only_in_the_validator():
    """The whole reason the run died: the rule existed only where it could be
    discovered by being refused.
    """

    rendered = SimulationProposalWireV1.model_json_schema()["properties"][
        "requested_observables"
    ]

    assert rendered["items"]["pattern"] == OBSERVABLE_NAME_PATTERN
    assert "dots" in rendered["description"]


@pytest.mark.parametrize("resolver", [resolve_observable, _resolve_observable])
def test_resolution_is_literal_first_then_traversal(resolver):
    """Literal-first is what makes this widening rather than a behaviour change:
    a program returning a genuinely flat key with a dot in it keeps its value.
    """

    nested = {"animal": {"baseline": {"distinct": 7}}, "a.b": "flat wins"}

    assert resolver(nested, "animal.baseline.distinct") == 7
    assert resolver(nested, "a.b") == "flat wins"
    assert resolver({"plain": 1}, "plain") == 1
    # A traversal that runs out, and one that hits a non-mapping.
    assert resolver(nested, "animal.baseline.missing") is not 7  # noqa: F632
    assert resolver(nested, "animal.baseline.distinct.deeper") is not 7  # noqa: F632


def test_the_two_resolvers_agree_because_a_result_must_not_depend_on_the_runner():
    cases = [
        ({"a": {"b": 1}}, "a.b"),
        ({"a": {"b": 1}}, "a.c"),
        ({"a.b": 2, "a": {"b": 1}}, "a.b"),
        ({"a": 1}, "a.b"),
        ({}, "a"),
    ]
    for output, name in cases:
        first = resolve_observable(output, name)
        second = _resolve_observable(output, name)
        # Both signal absence with a private sentinel, so compare resolvability
        # and then the value only when both resolved.
        first_found = type(first).__name__ != "object"
        second_found = type(second).__name__ != "object"
        assert first_found == second_found, (output, name)
        if first_found:
            assert first == second, (output, name)


def test_the_worker_source_carries_the_resolver_it_will_actually_run():
    """The worker executes as SOURCE in a subprocess, so importing the function
    here proves nothing about the code that runs under containment.
    """

    assert "def resolve_observable(output, name):" in CONTAINED_WORKER_SOURCE_V1
    assert '"observables": resolved' in CONTAINED_WORKER_SOURCE_V1


def test_a_declarative_program_may_declare_dotted_observables():
    """Flat keys that contain dots, which the runtime resolver finds literally."""

    document = (
        '{"schema": "declarative-numeric.v1", "observables": '
        '{"animal.baseline.distinct": {"const": 3}, "plain": {"const": 4}}}'
    )
    compiled = compile_declarative_numeric(
        document, ("animal.baseline.distinct", "plain")
    ).decode()

    assert "'animal.baseline.distinct': 3" in compiled

    namespace: dict = {}
    exec(compile(compiled, "<declarative>", "exec"), namespace)
    produced = namespace["simulate"]({}, None)
    assert resolve_observable(produced, "animal.baseline.distinct") == 3


def test_a_declarative_program_still_refuses_a_malformed_observable():
    document = (
        '{"schema": "declarative-numeric.v1", "observables": {"bad name": 1}}'
    )
    with pytest.raises(DeclarativeSimulationError, match="invalid observable name"):
        compile_declarative_numeric(document, ("bad name",))
