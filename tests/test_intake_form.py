import pytest
from pydantic import ValidationError

from deepreason.intake_form import (
    INTAKE_CYCLES_CEILING_EXCEEDED,
    INTAKE_SEAT_CONFLICT,
    IntakeFormV1,
)
from deepreason.preparation import PUBLIC_MAX_CYCLES


def test_minimal_valid_form_passes():
    form = IntakeFormV1(question="Is P equal to NP?")
    assert form.question == "Is P equal to NP?"
    assert form.shallow is False
    assert form.seats is None


def test_missing_question_fails():
    with pytest.raises(ValidationError) as excinfo:
        IntakeFormV1()
    errors = excinfo.value.errors()
    assert any(e["loc"] == ("question",) and e["type"] == "missing" for e in errors)


def test_seat_conflict_raises_intake_seat_conflict():
    with pytest.raises(ValidationError) as excinfo:
        IntakeFormV1(
            question="Q",
            seats={"conjecture": "profile-a", "simulation": "profile-b"},
        )
    assert INTAKE_SEAT_CONFLICT in str(excinfo.value)


def test_seat_alias_same_profile_is_not_a_conflict():
    form = IntakeFormV1(
        question="Q",
        seats={"conjecture": "profile-a", "simulation": "profile-a"},
    )
    assert form.seats == {"conjecture": "profile-a", "simulation": "profile-a"}


def test_cycles_over_ceiling_raises():
    with pytest.raises(ValidationError) as excinfo:
        IntakeFormV1(question="Q", cycles=PUBLIC_MAX_CYCLES + 1)
    assert INTAKE_CYCLES_CEILING_EXCEEDED in str(excinfo.value)


def test_cycles_at_ceiling_is_fine():
    form = IntakeFormV1(question="Q", cycles=PUBLIC_MAX_CYCLES)
    assert form.cycles == PUBLIC_MAX_CYCLES


def test_token_budget_has_no_ceiling():
    """R1: the former 200k per-run token ceiling is retired; any positive
    token_budget is accepted."""

    formerly_over_ceiling = 200_000 + 1
    form = IntakeFormV1(question="Q", token_budget=formerly_over_ceiling)
    assert form.token_budget == formerly_over_ceiling


def test_token_budget_must_be_positive():
    with pytest.raises(ValidationError):
        IntakeFormV1(question="Q", token_budget=0)


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        IntakeFormV1(question="Q", not_a_real_field=1)


def test_json_schema_has_question_property():
    schema = IntakeFormV1.model_json_schema()
    assert "question" in schema["properties"]
