"""Signal registry (signals.py): every measure tag the source tree emits must
be documented. The coverage test AST-scans src/deepreason for
record_measure(inputs=[<literal>...]) heads and record_llm_calls(..., <tag>)
literals — a new signal ships with its meaning or CI fails."""

import ast
import pathlib

from deepreason.signals import PREFIXES, SIGNALS, describe, family, is_known

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "deepreason"


def _literal_head(node) -> str | None:
    """The leading string of a constant or f-string (prefix before the first
    interpolation); None for fully dynamic expressions."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        first = node.values[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
    return None


def _emitted_signals() -> set[str]:
    found: set[str] = set()
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if name == "record_measure":
                for kw in node.keywords:
                    if kw.arg == "inputs" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        if kw.value.elts:
                            head = _literal_head(kw.value.elts[0])
                            if head is not None:
                                found.add(head)
            elif name == "record_llm_calls" and len(node.args) >= 2:
                head = _literal_head(node.args[1])
                if head is not None:
                    found.add(head)
    return found


def test_every_emitted_signal_is_registered():
    unregistered = sorted(s for s in _emitted_signals() if not is_known(s))
    assert not unregistered, (
        f"unregistered signals emitted by the source tree: {unregistered} — "
        "document them in src/deepreason/signals.py"
    )


def test_emitted_inventory_is_nontrivial():
    # Guards the scanner itself: if the AST heuristic silently broke, the
    # coverage test above would pass vacuously.
    found = _emitted_signals()
    assert len(found) >= 20
    for expected in ("arg-crit", "vision-crit", "browser-pass", "trial-llm"):
        assert expected in found


def test_describe_exact_prefix_and_unknown():
    assert "execution supremacy" in describe("arg-crit-overridden-by-execution")
    assert "screened out" in describe("trial-blocked:order-swap")
    assert describe("no-such-signal") == "(unregistered signal)"
    assert is_known("intervention:reseed") and not is_known("bogus:tag")


def test_family_groups_prefixes():
    assert family("trial-blocked:order-swap") == "trial-blocked:*"
    assert family("browser-pass") == "browser-pass"
    assert family("weird-unknown") == "weird-unknown"


def test_registry_entries_have_meanings():
    for name, meaning in {**SIGNALS, **PREFIXES}.items():
        assert meaning.strip(), f"empty meaning for {name}"


# ---- the heartbeat: cycles are visible in the log ----

def test_scheduler_heartbeat_segments_the_log(tmp_path):
    import json

    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.ontology import Commitment, Problem, ProblemProvenance, Rule
    from deepreason.scheduler.scheduler import Scheduler

    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(Problem(
        id="pi-root", description="explain the tides", criteria=["k-moon"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    conj = json.dumps({"candidates": [{"content": "moon idea", "typicality": 0.9}]})
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([conj, conj])}, harness.blobs, retry_max=2
    )
    scheduler = Scheduler(harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0))
    scheduler.step()
    scheduler.step()

    beats = [e for e in harness.log.read()
             if e.rule == Rule.MEASURE and e.inputs and e.inputs[0] == "cycle"]
    assert [b.inputs[1] for b in beats] == ["0", "1"]
    assert all(b.inputs[2] == "pi-root" for b in beats)
    # Every event attributes to a cycle: nothing precedes the first heartbeat
    # except the pre-run registrations (commitment/problem seeds).
    first = beats[0].seq
    pre = [e for e in harness.log.read() if e.seq < first]
    assert all(e.rule == Rule.REGISTER for e in pre)


def test_dropped_call_carries_the_reason(tmp_path):
    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.ontology import Rule
    from deepreason.scheduler.scheduler import Scheduler

    harness = Harness(tmp_path / "run")
    adapter = LLMAdapter({"conjecturer": MockEndpoint([])}, harness.blobs, retry_max=0)
    scheduler = Scheduler(harness, adapter, Config(N_SCHOOLS=0))
    scheduler._drop(SchemaRepairError("judge returned prose, not JSON", spend=None))

    drop = [e for e in harness.log.read()
            if e.rule == Rule.MEASURE and e.inputs and e.inputs[0] == "dropped-call"]
    assert len(drop) == 1
    assert "judge returned prose" in drop[0].inputs[1]  # the WHY is in the log
