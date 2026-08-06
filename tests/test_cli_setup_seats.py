from deepreason.cli.main import _main
from deepreason.seat_bindings import load_seat_bindings, seat_bindings_path


def _setup_argv(tmp_path, extra=()):
    return [
        "setup",
        "--provider",
        "custom",
        "--endpoint",
        "https://api.example.com/v1",
        "--model",
        "test-model",
        "--context-window-tokens",
        "1000",
        "--maximum-completion-tokens",
        "100",
        "--credential-env",
        "DEEPREASON_TEST_SETUP_KEY",
        *extra,
    ]


def test_setup_with_seat_flag_writes_seat_bindings(tmp_path, monkeypatch):
    """R1: setup accepts per-role-group profile paths."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    bound_path = str(tmp_path / "coder-profile.yaml")
    rc = _main(_setup_argv(tmp_path, extra=["--seat", f"coder={bound_path}"]))
    assert rc == 0
    assert load_seat_bindings(seat_bindings_path()) == {"coder": bound_path}


def test_setup_without_seat_flag_writes_no_seat_bindings(tmp_path, monkeypatch):
    """R3: default (no --seat) writes no seat-bindings file at all."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    rc = _main(_setup_argv(tmp_path))
    assert rc == 0
    assert not seat_bindings_path().exists()
    assert load_seat_bindings(seat_bindings_path()) == {}
