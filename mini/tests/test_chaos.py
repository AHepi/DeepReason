"""Edge probes — the deterministic slice of the chaos battery: hostile
content, crash injection, degenerate budgets/knobs, and the failure modes
that must stay LOUD (corruption raises; it never silently misreads)."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from minireason import gate
from minireason.call import MockEndpoint
from minireason.checks import compile_checks, evaluate, run_checks
from minireason.log import ObjectStore, SeqError, replay
from minireason.loop import Session, run


def _conj(*contents) -> str:
    return json.dumps({"candidates": [
        {"content": c, "typicality": 0.5} for c in contents]})


# --- hostile content ---------------------------------------------------------

def test_hostile_content_survives_the_full_trip(tmp_path):
    hostile = [
        "",                                     # empty
        "\x00\x01\x02",                         # control bytes
        "é中文 🧪 zálgo \\ \" '",           # unicode soup
        "{" * 5000,                              # pathological nesting prefix
        json.dumps({"claim": "q\nq", "mechanism": "m\tm",
                    "forbidden": [{"case": "newlines everywhere",
                                   "eval": "rubric:std"}]}),
        json.dumps({"claim": "huge", "mechanism": "m",
                    "prose_notes": "pad " * 50_000,
                    "forbidden": [{"case": "c", "eval": "rubric:std"}]}),
        "gate:hash: deadbeef is a refuted artifact",  # measure-format mimicry
    ]
    summary = run([("pi-0", "d")], MockEndpoint([_conj(*hostile)]),
                  budget=10**7, root=tmp_path / "run", vs_k=10, max_cycles=1)
    # Every candidate registered or refuted -- nothing crashed, and the
    # measure-format mimic stayed CONTENT (no phantom gate blocks).
    assert summary["gate_blocks"] == 0
    assert summary["meter_equals_log"]
    root = tmp_path / "run"
    assert replay(root).digest() == replay(root).digest() == Session(root).state.digest()
    deepreason = pytest.importorskip("deepreason.invariants")
    assert deepreason.verify_root(root)["violations"] == []


def test_punctuation_only_contents_share_an_equivalence_class(tmp_path):
    """Documented edge: normalize() maps symbol-only bytes to the empty
    token set, so a refuted symbol-only prior blocks every other
    symbol-only candidate. Acceptable in v0: such content is always
    refuted by skeleton-wf anyway; recorded here so the behavior is a
    choice, not a surprise."""
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    cks = compile_checks("!!!")
    from minireason.log import artifact_id
    aid = artifact_id("inline:!!!", "utf8",
                      {"commitments": [c["id"] for c in cks], "refs": []})
    for c in cks:
        s.register_commitments([c])
    s.register_candidates([(aid, "!!!", cks)], "pi-0", "mechanist", None)
    s.refute(aid, [{"commitment": "skeleton-wf", "eval": "program:skeleton_wf",
                    "verdict": "fail"}])
    ok, reason = gate.check("b" * 64, "???", s.state)
    assert not ok and "to refuted" in reason


def test_predicate_bomb_is_bounded(tmp_path):
    """A hostile forbidden case must not hang the loop. evaluate() bounds
    predicate wall time; the bomb comes back as a failed verdict."""
    script = textwrap.dedent("""
        import sys
        sys.path.insert(0, sys.argv[1])
        from minireason.checks import evaluate
        verdict, detail = evaluate("predicate:10**10**8", "x")
        print(verdict, detail.get("error", "")[:40])
    """)
    proc = subprocess.run(
        [sys.executable, "-c", script, str(Path(__file__).resolve().parents[1])],
        capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.startswith("fail")


def test_bad_eval_syntax_refutes_instead_of_crashing():
    text = json.dumps({"claim": "c", "mechanism": "m",
                       "forbidden": [{"case": "broken",
                                      "eval": "predicate:len(content >"}]})
    failures = run_checks(text, compile_checks(text))
    assert failures and failures[0]["verdict"] == "fail"


def test_predicate_sandbox_blocks_io():
    for expr in ("open('/etc/passwd')", "__import__('os').system('true')",
                 "exec('x=1')", "getattr(json, 'load')"):
        verdict, _ = evaluate(f"predicate:{expr}", "x")
        assert verdict == "fail", expr


# --- degenerate knobs --------------------------------------------------------

def test_budget_zero_stops_before_spending(tmp_path):
    summary = run([("pi-0", "d")], MockEndpoint([_conj("x")]),
                  budget=0, root=tmp_path / "run")
    assert summary["stop"] == "budget"
    assert summary["tokens"]["total"] == 0
    assert summary["meter_equals_log"]


def test_max_cycles_zero(tmp_path):
    summary = run([("pi-0", "d")], MockEndpoint([]), budget=1000,
                  root=tmp_path / "run", max_cycles=0)
    assert summary["stop"] == "max-cycles"
    assert summary["cycles"] == 0


def test_empty_problem_queue(tmp_path):
    summary = run([], MockEndpoint([]), budget=1000, root=tmp_path / "run")
    assert summary["stop"] == "queue-exhausted"
    assert summary["cycles"] == 0


def test_resume_after_stop_continues_the_same_log(tmp_path):
    root = tmp_path / "run"
    run([("pi-0", "d")], MockEndpoint([_conj(json.dumps(
        {"claim": "a", "mechanism": "m",
         "forbidden": [{"case": "c", "eval": "rubric:std"}]}))]),
        budget=10**6, root=root, turnover_k=1, max_cycles=1)
    n1 = len(Session(root).state.events)
    # Second run appends to the same root; seqs stay consecutive.
    run([("pi-1", "d2")], MockEndpoint([_conj(json.dumps(
        {"claim": "b", "mechanism": "m",
         "forbidden": [{"case": "c", "eval": "rubric:std"}]}))]),
        budget=10**6, root=root, turnover_k=1, max_cycles=1)
    state = replay(root)
    assert len(state.events) > n1
    assert set(state.problems) == {"pi-0", "pi-1"}


# --- crash & corruption: loud, never silent ----------------------------------

def test_torn_final_line_recovers_and_reuses_seq(tmp_path):
    root = tmp_path / "run"
    s = Session(root)
    s.spawn_problem("pi-0", "d")
    s.measure(["ok"])
    with open(root / "log.jsonl", "a") as f:
        f.write('{"seq": 2, "rule": "Meas')  # crash mid-append
    with pytest.warns(UserWarning):
        s2 = Session(root)
    assert len(s2.state.events) == 2
    s2.measure(["recovered"])  # seq 2 reused; the torn line was never durable
    assert [e.seq for e in replay(root).events] == [0, 1, 2]


def test_interior_corruption_raises(tmp_path):
    root = tmp_path / "run"
    s = Session(root)
    s.measure(["a"])
    s.measure(["b"])
    lines = (root / "log.jsonl").read_text().splitlines()
    lines[0] = lines[0][: len(lines[0]) // 2]  # corrupt a NON-final line
    (root / "log.jsonl").write_text("\n".join(lines) + "\n")
    with pytest.raises(Exception):
        list(replay(root).events)


def test_missing_object_fails_loudly(tmp_path):
    root = tmp_path / "run"
    s = Session(root)
    s.spawn_problem("pi-0", "d")
    ObjectStore(root / "objects")._path("pi-0").unlink()
    with pytest.raises(KeyError):
        replay(root)


def test_seq_gap_raises(tmp_path):
    root = tmp_path / "run"
    s = Session(root)
    s.measure(["a"])
    s.measure(["b"])
    lines = (root / "log.jsonl").read_text().splitlines()
    (root / "log.jsonl").write_text(lines[1] + "\n")  # drop event 0
    with pytest.raises(SeqError):
        replay(root)


# --- single-writer discipline -------------------------------------------------

def test_concurrent_writers_conflict_loudly(tmp_path):
    """Two Sessions on one root: the stale writer's append must raise
    SeqError, never silently interleave (single-writer by design)."""
    root = tmp_path / "run"
    s1, s2 = Session(root), Session(root)
    s1.measure(["from-s1"])
    with pytest.raises(SeqError):
        s2.measure(["from-s2"])


# --- scoring math under random inputs ----------------------------------------

def test_score_orders_properties_hold_for_all_inputs():
    """raw/adjusted bounded, symmetric under X/Y swap (up to sign), and
    order-disagreement in [0,1] — for every random choice matrix."""
    import random as _random

    from minireason.judge import CRITERIA, score_orders

    rng = _random.Random(7)
    names = [n for n, _ in CRITERIA]
    for _ in range(500):
        c1 = {n: rng.choice(["A", "B", "tie"]) for n in names}
        c2 = {n: rng.choice(["A", "B", "tie"]) for n in names}
        lx, ly = rng.randint(1, 5000), rng.randint(1, 5000)
        row = score_orders(c1, c2, lx, ly)
        assert -1.0 <= row["raw"] <= 1.0
        assert -1.0 <= row["adjusted"] <= 1.0
        assert 0.0 <= row["order_disagreement"] <= 1.0
        # Swap X and Y: the mirrored run's first presentation IS the
        # original second one (same seat behavior), so orders swap whole.
        mirrored = score_orders(c2, c1, ly, lx)
        assert mirrored["raw"] == -row["raw"]
        assert mirrored["adjusted"] == -row["adjusted"]
        assert mirrored["order_disagreement"] == row["order_disagreement"]
