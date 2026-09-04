"""Leniency that changes no verdict (SPEC S8.4, S11.4, A3).

The operator hedged this clause — "maybe adapting the accepted outputs so they
compile is something worth doing" — so its boundary is the whole of what makes
it safe, and the boundary is checkable rather than argued:

    A normalisation rewrites how a reply is PACKAGED. It never touches a
    VALUE. A strictly-conforming reply and its loosened twin must compile to
    the SAME canonical artifact, byte for byte.

Anything that would change which handle is cited, which commitment is
discharged, whether a candidate abstains, or what is admitted, ranked, immune
or refuted is OUT of scope and a stop — not a judgment call at the point of
use.

The five: N1 a single-element array wrapping the one expected object (already
shipped, with its live justification recorded inline in wire.py); N2 a scalar
where a one-element array is required; N3 a menu index where a handle is
required (already shipped as `_resolve_menu_indices`); N4 an absent optional
field supplied as null or ""; N5 the whole object wrapped in one redundant key.
"""

import json

import pytest

from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.wire import AliasTable, wire_contract_for


@pytest.fixture
def contract():
    return wire_contract_for(
        "conjecturer", ConjecturerOutput, "standard", AliasTable()
    )


def _strict(contract):
    """One reply that needs no normalisation at all."""
    fields = contract.model_json_schema().get("properties", {})
    assert "candidates" in fields, sorted(fields)
    return {
        "candidates": [
            {
                "content": "stored heat release from masonry",
                "typicality": 0.4,
                "refs": [],
            }
        ]
    }


def _canonical(contract, value):
    return json.dumps(
        contract.compile(contract.validate_value(value)).model_dump(mode="json"),
        sort_keys=True,
    )


def _applied(contract, value):
    """Which rules a value triggers.

    Read from `_normalise_shape` rather than from the contract's
    `normalisations_applied` attribute, because that attribute holds the LAST
    call's rules — a test that validated the loose value and then the strict
    one would read the strict call's empty tuple and pass for the wrong
    reason.
    """
    rules: list[str] = []
    contract._normalise_shape(value, rules)
    return rules


# ------------------------------------------------------------------ N1 - N5


def test_identical_n1_a_single_element_array_wrapping_the_object(contract):
    strict = _strict(contract)
    assert _canonical(contract, [strict]) == _canonical(contract, strict)
    assert "N1" in _applied(contract, [strict])


def test_identical_n2_a_scalar_where_a_one_element_array_is_required(contract):
    strict = _strict(contract)
    loose = dict(strict)
    loose["candidates"] = strict["candidates"][0]
    assert _canonical(contract, loose) == _canonical(contract, strict)
    assert "N2" in _applied(contract, loose)


def test_identical_n4_an_absent_optional_field_supplied_as_null():
    """Proven on a contract that HAS an optional top-level field.

    The conjecturer's own turn contract requires everything it declares, so
    testing N4 against it would have SKIPPED — an unproven rule reported as a
    pass. `ArgumentativeCriticOutput` carries four optional fields, and the
    rule is the same rule.
    """
    from deepreason.llm.contracts import ArgumentativeCriticOutput
    from deepreason.llm.wire import DirectWireContract

    critic = DirectWireContract(ArgumentativeCriticOutput)
    schema = critic.model_json_schema()
    optional = sorted(
        set(schema.get("properties", {})) - set(schema.get("required", ()))
    )
    assert optional, "this test needs a contract with an optional field"

    strict = {"attack": False}
    loose = {**strict, optional[0]: None}
    assert _canonical(critic, loose) == _canonical(critic, strict)
    assert "N4" in _applied(critic, loose)


def test_n4_does_not_touch_an_empty_string_and_the_reason_is_a_measurement():
    """NARROWED from SPEC §8.4's "null or empty string", by that section's own
    stop condition.

    `null` is unambiguously "I am not supplying this". An EMPTY STRING is a
    supplied value, and a contract may reject it deliberately:
    `tests/test_cli_production_doctor_v6.py` plants
    `{"finding": "supported", "message": ""}` precisely so the repair protocol
    makes the model try again. The first version of N4 deleted that field and
    turned a REFUSAL into an ACCEPTANCE — three doctor tests went red and said
    so. A3 makes a verdict change a stop rather than a judgment call, so the
    rule was narrowed rather than the tests adjusted.
    """
    from deepreason.llm.contracts import ArgumentativeCriticOutput
    from deepreason.llm.wire import DirectWireContract

    critic = DirectWireContract(ArgumentativeCriticOutput)
    assert _applied(critic, {"attack": False, "case": ""}) == []


def test_identical_n5_the_object_wrapped_in_one_redundant_key(contract):
    strict = _strict(contract)
    assert _canonical(contract, {"conjecturer_turn": strict}) == _canonical(
        contract, strict
    )
    assert "N5" in _applied(contract, {"conjecturer_turn": strict})


def test_identical_n3_a_menu_index_where_a_handle_is_required():
    """N3 already ships as `_resolve_menu_indices`, and its own guarantee is
    the one this whole file generalises: it can only replace an index token
    with a value the menu ALREADY listed. It cannot invent a handle, so it
    cannot change which evidence a candidate cites."""
    from deepreason.llm.reference_menu import MenuBinding, resolve_indices_in

    binding = MenuBinding(citable_block_ids=("EV-001", "EV-002"))
    loose = {"candidates": [{"evidence_refs": [{"block": "[2]"}]}]}
    strict = {"candidates": [{"evidence_refs": [{"block": "EV-002"}]}]}

    resolved = resolve_indices_in(loose, "conjecturer.turn.v6", binding)
    assert resolved == strict, resolved
    # And the decisive property: an index the menu never listed is NOT
    # invented into a handle.
    out_of_range = resolve_indices_in(
        {"candidates": [{"evidence_refs": [{"block": "[9]"}]}]},
        "conjecturer.turn.v6",
        binding,
    )
    assert out_of_range["candidates"][0]["evidence_refs"][0]["block"] == "[9]"


# ------------------------------------------------- the boundary, as a check


def test_a_normalisation_never_touches_a_value(contract):
    """The stop condition, made mechanical. Shape may be rewritten; the
    CONTENT of every leaf must survive unchanged, or the normalisation would
    be changing what the seat said rather than how it packaged it."""

    def leaves(node):
        if isinstance(node, dict):
            for value in node.values():
                yield from leaves(value)
        elif isinstance(node, list):
            for item in node:
                yield from leaves(item)
        else:
            yield node

    strict = _strict(contract)
    for loose in (
        [strict],
        {"conjecturer_turn": strict},
        {**strict, "candidates": strict["candidates"][0]},
    ):
        applied: list[str] = []
        normalised = contract._normalise_shape(loose, applied)
        assert applied, loose
        assert sorted(map(str, leaves(normalised))) == sorted(
            map(str, leaves(strict))
        )


def test_a_reply_needing_no_normalisation_records_none(contract):
    """The negative anchor: if every reply reported a rule, the record could
    not say how much leniency actually bought."""
    contract.validate_value(_strict(contract))
    assert contract.normalisations_applied == ()


def test_a_genuinely_malformed_reply_is_still_refused(contract):
    """Leniency is not permissiveness. A reply that is wrong rather than
    merely loosely packaged must still fail."""
    with pytest.raises(Exception):
        contract.validate_value({"candidates": [{"typicality": "not a number"}]})
    with pytest.raises(Exception):
        contract.validate_value({"candidates": [{}, {}], "route": "elsewhere"})
