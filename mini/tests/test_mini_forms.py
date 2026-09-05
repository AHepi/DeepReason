"""The mini form registry, and the STORED default that must not move.

Implements S2 (R2, R7, R-stored, C1, C9) of the mini isolation programme.

R-stored is the operator's own instruction of 2026-09-05: "For now, the
current default conjecture form needs stored but not deleted." Everything else
in this file is about relaxing what a mini seat may say; this first test is
about the one form that may not change while that happens.
"""

import json
import pathlib

import pytest

_GOLDEN = pathlib.Path(__file__).parent / "goldens" / "mini_stored_conjecturer_form.json"


def test_the_stored_form_is_byte_identical():
    """R-stored: the current default conjecture form is STORED, not deleted.

    The golden is the whole contract as a mini run sees it -- its id, its
    variant, the names of both models, and the complete JSON Schema a seat is
    shown. Comparing the rendered BYTES rather than a field or two is
    deliberate: a form is what the model is asked for, and a change anywhere
    in that schema is a change to the question, however small it looks in a
    diff.
    """
    from deepreason.llm.wire import ReferenceFreeConjecturerWireContract

    contract = ReferenceFreeConjecturerWireContract()
    rendered = (
        json.dumps(
            {
                "contract_id": contract.contract_id,
                "variant": contract.variant,
                "wire_model": contract.wire_model.__name__,
                "canonical_model": contract.canonical_model.__name__,
                "schema": contract.model_json_schema(),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    assert rendered == _GOLDEN.read_text(encoding="utf-8"), (
        "the stored default conjecture form moved; R-stored says it is stored, "
        "not changed. If a new form is wanted, REGISTER ONE BESIDE IT."
    )


# ------------------------------------------------------- the registry (S2)


def test_no_mini_form_bounds_a_string():
    """R2: "mini artifact forms need to not limit prose length at all."

    Checked over EVERY registered form and the whole rendered schema, not over
    the fields this tranche happened to write: a bound added later to a nested
    model would be just as much a limit, and would be just as invisible.
    """
    from minireason.forms import mini_form_ids, resolve_mini_form

    for form_id in mini_form_ids():
        schema = json.dumps(resolve_mini_form(form_id).wire_model.model_json_schema())
        assert "maxLength" not in schema, (form_id, "a mini form bounds a string")
        assert "maxItems" not in schema, (form_id, "a mini form bounds a list")


def test_the_stored_form_is_registered_beside_the_relaxed_one_not_replaced():
    """R-stored, as a registry fact rather than a promise.

    The stored entry holds the SHIPPED contract instance -- not a copy, not a
    re-derivation -- so "stored, not deleted" is a property of an object nobody
    rewrote.
    """
    from deepreason.llm.wire import ReferenceFreeConjecturerWireContract
    from minireason.forms import mini_form_ids, resolve_mini_form

    ids = mini_form_ids()
    assert "mini.conjecturer.legacy-v0" in ids
    assert "mini.conjecturer.relaxed.v1" in ids

    stored = resolve_mini_form("mini.conjecturer.legacy-v0")
    assert isinstance(stored.contract, ReferenceFreeConjecturerWireContract)
    assert stored.contract.contract_id == "conjecturer.compact.reference_free.v1"
    assert stored.contract.model_json_schema() == (
        ReferenceFreeConjecturerWireContract().model_json_schema()
    )

    relaxed = resolve_mini_form("mini.conjecturer.relaxed.v1")
    assert relaxed.contract.contract_id != stored.contract.contract_id


def test_a_free_prose_candidate_is_well_formed_under_the_relaxed_form():
    """R2's second limit: no required skeleton.

    One paragraph of prose, with no claim/mechanism/forbidden structure, is a
    well-formed candidate. Under the stored form it is well-formed too -- the
    skeleton was never in the SCHEMA -- which is why R2 alone changes nothing
    without R3; see test_mini_commitment_policy.py.
    """
    from minireason.forms import resolve_mini_form

    relaxed = resolve_mini_form("mini.conjecturer.relaxed.v1")
    value = relaxed.wire_model.model_validate(
        {"candidates": [{"content": "Rayleigh scattering, but I am guessing."}]}
    )
    assert value.candidates[0].typicality == 0.5, "typicality is optional"

    compiled = relaxed.compile(value)
    assert compiled.candidates[0].content.startswith("Rayleigh")


def test_the_critic_and_commitment_forms_require_only_what_they_must():
    """R4/C9: a commitment proposal's ONLY requirement is naming its
    conjecture. Nothing else is required, and nothing is ranked."""
    import pydantic

    from minireason.forms import resolve_mini_form

    proposals = resolve_mini_form("mini.commitment.relaxed.v1").wire_model
    proposals.model_validate({"proposals": [{"about": "a1", "body": "x"}]})
    with pytest.raises(pydantic.ValidationError):
        proposals.model_validate({"proposals": [{"body": "x"}]})

    for form_id in ("mini.critic.relaxed.v1", "mini.commitment.relaxed.v1"):
        fields = set()
        for model in resolve_mini_form(form_id).wire_model.model_json_schema().get(
            "$defs", {}
        ).values():
            fields |= set(model.get("properties", {}))
        banned = fields & {
            "score",
            "rank",
            "weight",
            "confidence",
            "priority",
            "authority",
            "severity",
        }
        assert not banned, (form_id, banned)


def test_selection_is_argument_then_environment_then_the_declared_default(monkeypatch):
    """Never `Config`, never the manifest: a form knob on `Config` would move
    the digest of every qualification bundle in the tree."""
    from minireason.forms import MiniFormError, select_mini_form

    monkeypatch.delenv("DEEPREASON_MINI_FORM", raising=False)
    chosen = select_mini_form("mini.conjecturer", "mini.conjecturer.relaxed.v1")
    assert chosen.form_id == "mini.conjecturer.relaxed.v1"

    monkeypatch.setenv(
        "DEEPREASON_MINI_FORM", "mini.conjecturer=mini.conjecturer.legacy-v0"
    )
    assert (
        select_mini_form("mini.conjecturer").form_id == "mini.conjecturer.legacy-v0"
    )
    # The argument still wins over the environment.
    assert (
        select_mini_form("mini.conjecturer", "mini.conjecturer.relaxed.v1").form_id
        == "mini.conjecturer.relaxed.v1"
    )
    # A seat the variable does not name falls through to the declared default.
    assert (
        select_mini_form("mini.critic", default="mini.critic.relaxed.v1").form_id
        == "mini.critic.relaxed.v1"
    )

    monkeypatch.setenv("DEEPREASON_MINI_FORM", "this-is-not-an-assignment")
    with pytest.raises(MiniFormError) as caught:
        select_mini_form("mini.conjecturer")
    assert caught.value.code == "MINI_FORM_ASSIGNMENT_MALFORMED"


def test_an_unknown_form_and_a_seat_with_no_default_are_refused_typed(monkeypatch):
    from minireason.forms import MiniFormError, resolve_mini_form, select_mini_form

    monkeypatch.delenv("DEEPREASON_MINI_FORM", raising=False)
    with pytest.raises(MiniFormError) as caught:
        resolve_mini_form("mini.nothing.v9")
    assert caught.value.code == "MINI_FORM_UNKNOWN"

    with pytest.raises(MiniFormError) as caught:
        select_mini_form("mini.conjecturer")
    assert caught.value.code == "MINI_FORM_NO_DEFAULT"


def test_no_configuration_field_and_no_manifest_field_names_a_mini_form():
    """The architecture check behind Road M. `run_manifest.py` dumps every
    `Config` field into `engine_config_json`, and `qualification.py` folds that
    into every qualification subject digest, so a form knob there would move
    the digest of every bundle in the tree."""
    from deepreason.config import Config
    from deepreason.run_manifest import ContractVersionPolicyV3
    from minireason.forms import mini_form_ids

    suspicious = [
        field
        for field in Config.model_fields
        if "MINI_FORM" in field.upper() or "MINIREASON" in field.upper()
    ]
    assert not suspicious, suspicious

    declared = {
        str(value)
        for value in ContractVersionPolicyV3().model_dump().values()
        if isinstance(value, str)
    }
    assert not (declared & set(mini_form_ids())), declared & set(mini_form_ids())


def test_re_registering_one_id_with_different_values_is_refused():
    from minireason.forms import (
        MiniFormError,
        MiniFormV1,
        register_mini_form,
        resolve_mini_form,
    )

    stored = resolve_mini_form("mini.conjecturer.legacy-v0")
    register_mini_form(stored)  # idempotent: the same values re-register fine
    with pytest.raises(MiniFormError) as caught:
        register_mini_form(
            MiniFormV1(
                form_id="mini.conjecturer.legacy-v0",
                form_version="9.9.9",
                contract=stored.contract,
            )
        )
    assert caught.value.code == "MINI_FORM_CONFLICT"
