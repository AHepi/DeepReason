import pytest

from deepreason.provider_profile import ProviderProfileV1, write_provider_profile
from deepreason.seat_bindings import (
    GROUP_ALIASES,
    GROUP_ROLES,
    SeatBindingError,
    load_seat_bindings,
    parse_seat_flags,
    resolve_seat_bindings,
    seat_bindings_path,
    write_seat_bindings,
)


def _profile(**updates):
    values = {
        "provider": "openai",
        "endpoint": "https://api.example.com/v1",
        "model_id": "model-a",
        "model_revision": "rev-a",
        "family": "family-a",
        "context_window_tokens": 262144,
        "maximum_completion_tokens": 4096,
        "credential_env": "DEEPREASON_TEST_KEY",
    }
    values.update(updates)
    return ProviderProfileV1.create(**values)


def test_parse_seat_flags_none_or_empty_is_no_bindings():
    assert parse_seat_flags(None) == {}
    assert parse_seat_flags([]) == {}


def test_parse_seat_flags_unknown_group_refuses_typed():
    with pytest.raises(SeatBindingError) as excinfo:
        parse_seat_flags(["nonsense=/tmp/a.yaml"])
    assert excinfo.value.code == "SEAT_BINDING_GROUP_UNKNOWN"


def test_parse_seat_flags_duplicate_group_refuses_typed():
    with pytest.raises(SeatBindingError) as excinfo:
        parse_seat_flags(["coder=/tmp/a.yaml", "coder=/tmp/b.yaml"])
    assert excinfo.value.code == "SEAT_BINDING_GROUP_DUPLICATED"


def test_parse_seat_flags_simulation_alias_parses():
    assert parse_seat_flags(["simulation=/tmp/a.yaml"]) == {
        "simulation": "/tmp/a.yaml"
    }
    assert "simulation" in GROUP_ALIASES
    assert GROUP_ALIASES["simulation"] == "conjecture"
    assert GROUP_ALIASES["simulation"] in GROUP_ROLES


def test_write_and_load_seat_bindings_round_trip(tmp_path):
    target = tmp_path / "seat-bindings.yaml"
    written = write_seat_bindings({"coder": "/profiles/coder.yaml"}, target)
    assert written == target
    assert load_seat_bindings(target) == {"coder": "/profiles/coder.yaml"}


def test_load_seat_bindings_missing_file_is_no_bindings(tmp_path):
    assert load_seat_bindings(tmp_path / "absent.yaml") == {}


def test_resolve_seat_bindings_no_file_is_no_bindings(tmp_path):
    assert resolve_seat_bindings(home=str(tmp_path)) == {}


def test_resolve_seat_bindings_conflict_on_named_simulation_conjecture_pair(
    tmp_path,
):
    """R8/R9: conflicting --seat values for the shared role set (simulation
    aliases conjecture) refuse typed, never last-one-wins."""

    profile_a = tmp_path / "a.yaml"
    profile_b = tmp_path / "b.yaml"
    write_provider_profile(_profile(model_id="model-a"), profile_a)
    write_provider_profile(_profile(model_id="model-b"), profile_b)
    write_seat_bindings(
        {"conjecture": str(profile_a), "simulation": str(profile_b)},
        seat_bindings_path(home=str(tmp_path)),
    )
    with pytest.raises(SeatBindingError) as excinfo:
        resolve_seat_bindings(home=str(tmp_path))
    assert excinfo.value.code == "SEAT_BINDING_ROLE_CONFLICT"
    assert "conjecturer" in str(excinfo.value)


def test_resolve_seat_bindings_conflict_on_discovered_scratch_conjecture_overlap(
    tmp_path,
):
    """A8: the same typed refusal applies to the scratch/conjecture overlap
    (both claim "conjecturer") this tranche's spec discovered, not only the
    operator-named simulation/conjecture pair."""

    profile_a = tmp_path / "a.yaml"
    profile_b = tmp_path / "b.yaml"
    write_provider_profile(_profile(model_id="model-a"), profile_a)
    write_provider_profile(_profile(model_id="model-b"), profile_b)
    write_seat_bindings(
        {"conjecture": str(profile_a), "scratch": str(profile_b)},
        seat_bindings_path(home=str(tmp_path)),
    )
    with pytest.raises(SeatBindingError) as excinfo:
        resolve_seat_bindings(home=str(tmp_path))
    assert excinfo.value.code == "SEAT_BINDING_ROLE_CONFLICT"


def test_resolve_seat_bindings_same_profile_is_not_a_conflict(tmp_path):
    profile_a = tmp_path / "a.yaml"
    write_provider_profile(_profile(model_id="model-a"), profile_a)
    write_seat_bindings(
        {"conjecture": str(profile_a), "simulation": str(profile_a)},
        seat_bindings_path(home=str(tmp_path)),
    )
    resolved = resolve_seat_bindings(home=str(tmp_path))
    assert resolved["conjecturer"].model_id == "model-a"
    assert resolved["variator"].model_id == "model-a"


def test_resolve_seat_bindings_expands_group_to_its_role_set(tmp_path):
    profile_a = tmp_path / "a.yaml"
    write_provider_profile(_profile(model_id="model-a"), profile_a)
    write_seat_bindings(
        {"coder": str(profile_a)}, seat_bindings_path(home=str(tmp_path))
    )
    resolved = resolve_seat_bindings(home=str(tmp_path))
    assert set(resolved) == {"property_designer"}
    assert resolved["property_designer"].model_id == "model-a"
