from deepreason.cli.main import (
    JUDGE_SEATS_EVIDENCE_SUMMARY,
    _main,
    build_parser,
)
from deepreason.seat_bindings import (
    criticism_seat_bindings_path,
    load_seat_bindings,
    school_seat_bindings_path,
    seat_bindings_path,
)


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


def test_setup_with_school_seat_flag_writes_school_seat_bindings(tmp_path, monkeypatch):
    """S2d/R5, Amendment 11/R27: setup accepts a per-school profile path,
    persisted separately from the role-group --seat bindings file."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    bound_path = str(tmp_path / "school-1-profile.yaml")
    rc = _main(_setup_argv(tmp_path, extra=["--school-seat", f"school-1={bound_path}"]))
    assert rc == 0
    assert load_seat_bindings(school_seat_bindings_path()) == {"school-1": bound_path}
    assert not seat_bindings_path().exists()


def test_setup_without_school_seat_flag_writes_no_school_seat_bindings(tmp_path, monkeypatch):
    """Default (no --school-seat) writes no school-seat-bindings file at all."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    rc = _main(_setup_argv(tmp_path))
    assert rc == 0
    assert not school_seat_bindings_path().exists()
    assert load_seat_bindings(school_seat_bindings_path()) == {}


def test_setup_with_criticism_seat_flag_writes_criticism_seat_bindings(tmp_path, monkeypatch):
    """Step 44b (S2d/R27): setup accepts a per-school criticism-side profile
    path, persisted separately from BOTH the role-group --seat file and the
    conjecture-side --school-seat file -- the two school-seat levers never
    share a persistence file, matching their independence."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    bound_path = str(tmp_path / "school-2-critic-profile.yaml")
    rc = _main(
        _setup_argv(tmp_path, extra=["--criticism-seat", f"school-2={bound_path}"])
    )
    assert rc == 0
    assert load_seat_bindings(criticism_seat_bindings_path()) == {"school-2": bound_path}
    assert not school_seat_bindings_path().exists()
    assert not seat_bindings_path().exists()


def test_setup_without_criticism_seat_flag_writes_no_criticism_seat_bindings(
    tmp_path, monkeypatch
):
    """Default (no --criticism-seat) writes no criticism-seat-bindings file."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    rc = _main(_setup_argv(tmp_path))
    assert rc == 0
    assert not criticism_seat_bindings_path().exists()
    assert load_seat_bindings(criticism_seat_bindings_path()) == {}


def test_judge_seats_flag_surfaces_evidence_warning(tmp_path, monkeypatch, capsys):
    """Part D (S2b, R2, judge-suspicion law): --judge-seats prints the
    judge-audit evidence-review findings (sensitivity, false-conviction
    rates, the unmeasured self-preference/verbosity gap) before the
    operator can act on the opt-in -- a static disclosure of already-
    committed evidence, surfaced at setup time, not new research."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    rc = _main(_setup_argv(tmp_path, extra=["--judge-seats"]))
    assert rc == 0
    out = capsys.readouterr().out
    assert "11.9%" in out
    assert "47.5%" in out
    assert "Self-preference" in out
    assert JUDGE_SEATS_EVIDENCE_SUMMARY in out


def test_judge_seats_flag_help_text_also_surfaces_the_evidence():
    """The flag's --help text alone (no invocation) already discloses the
    same evidence, for an operator who only reads `deepreason setup -h`."""

    parser = build_parser()
    setup_help = parser._subparsers._group_actions[0].choices["setup"].format_help()
    # argparse word-wraps help text, so a hyphenated phrase can split across
    # lines ("Self-\npreference"); collapse all whitespace including the
    # wrap-hyphen boundary before asserting.
    normalized = " ".join(setup_help.split()).replace("- ", "-")
    assert "11.9%" in normalized
    assert "Self-preference" in normalized


def test_setup_without_judge_seats_flag_prints_no_evidence(tmp_path, monkeypatch, capsys):
    """Default (no --judge-seats): the disclosure is not forced on every
    setup run, only on the ones opting into judges."""

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path))
    monkeypatch.setenv("DEEPREASON_TEST_SETUP_KEY", "already-set")
    rc = _main(_setup_argv(tmp_path))
    assert rc == 0
    out = capsys.readouterr().out
    assert "11.9%" not in out
