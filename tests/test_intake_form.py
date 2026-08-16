import pytest
from pydantic import ValidationError

from deepreason.intake_form import (
    INTAKE_CYCLES_CEILING_EXCEEDED,
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


def test_seat_conflict_now_validates_unchanged():
    """All-configs-allowed (2026-08-12): a conflicting seats mapping used to
    refuse (INTAKE_SEAT_CONFLICT); the form itself has no consumer that
    resolves a canonical winner (grep-confirmed, see intake_form.py's
    docstring on the validator), so it now validates and the mapping passes
    through exactly as given -- unresolved, not silently repaired."""
    form = IntakeFormV1(
        question="Q",
        seats={"conjecture": "profile-a", "simulation": "profile-b"},
    )
    assert form.seats == {"conjecture": "profile-a", "simulation": "profile-b"}


def test_seat_alias_same_profile_is_not_a_conflict():
    form = IntakeFormV1(
        question="Q",
        seats={"conjecture": "profile-a", "simulation": "profile-a"},
    )
    assert form.seats == {"conjecture": "profile-a", "simulation": "profile-a"}


def test_cycles_over_ceiling_clamps():
    """All-configs-allowed completion (2026-08-16): asking for more cycles
    than the engine accepts is a configuration, not a shape error, so it
    resolves deterministically to the ceiling instead of refusing. The form
    carries no manifest and so no notice sink -- the clamped value IS the
    disclosure, and `error_catalog.py`'s entry for
    INTAKE_CYCLES_CEILING_EXCEEDED describes the clamp."""

    form = IntakeFormV1(question="Q", cycles=PUBLIC_MAX_CYCLES + 1)
    assert form.cycles == PUBLIC_MAX_CYCLES
    assert IntakeFormV1(question="Q", cycles=1).cycles == 1
    assert IntakeFormV1(question="Q").cycles is None


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


def test_cli_validate_intake_exits_zero_on_a_valid_file(tmp_path, capsys):
    from deepreason.cli.main import main

    intake_path = tmp_path / "intake.json"
    intake_path.write_text('{"question": "Is P equal to NP?"}')
    assert main(["validate-intake", str(intake_path)]) == 0
    assert "OK" in capsys.readouterr().out


def test_cli_validate_intake_accepts_a_resolved_semantic_input(tmp_path, capsys):
    """All-configs-allowed, both halves.

    2026-08-12 (R6) made a typed `CODE:` violation advisory: reported, exit 0.
    The 2026-08-16 completion went one step further for the cycles ceiling --
    it resolves by CLAMPING inside the model, so it never becomes a violation
    at all. Exit 0, and nothing to report.

    Consequence recorded so nobody reads the empty stderr as a regression:
    with `INTAKE_SEAT_CONFLICT` and `INTAKE_CYCLES_CEILING_EXCEEDED` both
    resolving in-model, `IntakeFormV1` has no remaining semantic violation an
    input can construct, so `_cmd_validate_intake`'s advisory branch is
    currently unreachable. The branch stays: it is the contract every future
    semantic check inherits. The shape-error half is pinned by the next test.
    """
    from deepreason.cli.main import main

    over_ceiling = tmp_path / "intake-cycles.json"
    over_ceiling.write_text(
        f'{{"question": "Q", "cycles": {PUBLIC_MAX_CYCLES + 1}}}'
    )
    assert main(["validate-intake", str(over_ceiling)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "OK" in captured.out


def test_cli_validate_intake_still_exits_nonzero_for_a_shape_error(tmp_path, capsys):
    """A missing required field is a parse/shape error (a non-input, not a
    configuration, per R2) -- still refused, not made advisory."""
    from deepreason.cli.main import main

    intake_path = tmp_path / "intake.json"
    intake_path.write_text("{}")
    assert main(["validate-intake", str(intake_path)]) == 1
    assert "required" in capsys.readouterr().err


def test_cli_validate_intake_still_exits_nonzero_for_an_unparseable_file(tmp_path, capsys):
    from deepreason.cli.main import main

    intake_path = tmp_path / "intake.json"
    intake_path.write_text("[]")
    assert main(["validate-intake", str(intake_path)]) == 1
    assert "INTAKE_FILE_NOT_AN_OBJECT" in capsys.readouterr().err
