"""Execution oracle — the *acting* evaluator (prototype).

The harness's criticism is normally either a well-formedness program (skeleton-wf,
lineage_ref — internal) or a rubric judge (an LLM marking an LLM's homework —
self-referential). Neither TESTS a conjecture against reality; the run's
`evidence_lambda` sits at None. This module is the seam that closes that gap:
a `program:` commitment whose verdict comes from RUNNING the candidate against
fixed tests. A conjecture that proposes a function is refuted by *executing it
and observing the wrong output* — a warrant from reality, not from argument.
It generalizes what `scripts/cachebench.py` did once by hand (docs/CACHE_DESIGN.md:
a real measurement that refuted a design and lifted λ 0.0 -> 0.67).

Determinism (§0): the candidate runs against FIXED inputs under a DETERMINISTIC
step bound (Python line-event count, never wall-clock), and an AST int-literal
cap forbids C-level range/collection bombs — so every epistemic verdict is a
pure function of content and replays byte-for-byte. The whole operation,
including module loading, runs in a fresh subprocess. OS memory/CPU limits and
a parent watchdog are emergency containment only: if one fires, the API returns
``overrun`` with ``sandbox_abort`` and no fail warrant may be minted.

Security: every candidate/checker/generator/gate is UNTRUSTED model output, so
it is AST-guarded (no imports, no underscore/dunder names or attributes, no
`**`, no huge int
literals, no global/nonlocal) and executed with a locked, whitelist
`__builtins__` — the same escape-family guard programs.py uses for predicates,
extended to a callable. The AST guard is defense in depth; process isolation is
the availability and blast-radius boundary. See tests/test_oracle.py for the
blocked-escape and hostile-top-level cases.
"""

import ast
import builtins as _builtins
import json
import sys
from contextlib import contextmanager

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.commitment import Budget, Commitment
from deepreason.oracle_sandbox import (
    SandboxAborted as OracleSandboxAborted,
)
from deepreason.oracle_sandbox import run_isolated as _run_isolated

PASS, FAIL, OVERRUN = "pass", "fail", "overrun"

EXEC_PROGRAM = "exec_oracle"
PROPERTY_PROGRAM = "property_oracle"
# Every program whose verdict comes from RUNNING the candidate. warrants.
# execution_backed treats a passing verdict from any of these as a warrant
# from reality that mere argument cannot override.
EXEC_PROGRAMS = frozenset({EXEC_PROGRAM, PROPERTY_PROGRAM})
_STEP_LIMIT_DEFAULT = 100_000
_INT_LITERAL_CAP = 1_000_000  # forbid range()/collection bombs the step bound can't see

# Whitelist builtins (mirrors programs._SAFE_NAMES, sufficient for pure functions).
_ALLOWED = (
    "len range min max abs sum sorted enumerate zip map filter list dict set "
    "tuple str int float bool any all reversed round chr ord divmod isinstance"
).split()
_SAFE_BUILTINS = {name: getattr(_builtins, name) for name in _ALLOWED}


class _StepExceeded(Exception):
    """The candidate ran past its deterministic line-event budget."""


@contextmanager
def _step_budget(step_limit: int):
    """Count Python line events, including untrusted module top-level code."""
    steps = [0]

    def _tracer(frame, event, arg):
        if event == "line":
            steps[0] += 1
            if steps[0] > step_limit:
                raise _StepExceeded()
        return _tracer

    previous = sys.gettrace()
    sys.settrace(_tracer)
    try:
        yield steps
    finally:
        sys.settrace(previous)


def _guard(tree: ast.AST) -> None:
    """Reject the untrusted-code escape family (same shape as programs._validate_
    predicate, extended for a def+body): no imports, no underscore names/attrs
    (blocks the .__class__... walk), no ** (int bomb), no global/nonlocal, and
    no integer literal above the cap (blocks range(10**9)-style C-level hangs the
    line-event bound cannot see)."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("imports are not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError(f"underscore attribute .{node.attr}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError(f"underscore name {node.id}")
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValueError("global/nonlocal not allowed")
        if isinstance(node, ast.Pow):
            raise ValueError("** not allowed (int bomb)")
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and abs(
            node.value
        ) > _INT_LITERAL_CAP:
            raise ValueError(f"integer literal exceeds cap {_INT_LITERAL_CAP}")


def _short(value: object, limit: int = 120) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _compile(source: str, entry: str):
    """Guard, exec, and fetch ``entry`` from untrusted source; returns
    (fn, None) or (None, error). Shared by candidate and checker loading."""
    try:
        tree = ast.parse(source)
        _guard(tree)
    except (SyntaxError, ValueError) as e:
        return None, f"unsafe or unparseable: {e}"
    namespace: dict = {"__builtins__": dict(_SAFE_BUILTINS)}
    try:
        exec(compile(tree, "<candidate>", "exec"), namespace)  # noqa: S102 - guarded+sandboxed
    except _StepExceeded:
        return None, "step limit exceeded while loading module"
    except MemoryError:
        raise
    except Exception as e:  # noqa: BLE001 - a bad candidate is a failed verdict, not a crash
        return None, f"did not load: {e}"
    fn = namespace.get(entry)
    if not callable(fn):
        return None, f"entry point {entry!r} is not defined"
    return fn, None


def _sandbox_abort_verdict(error: OracleSandboxAborted) -> tuple[str, dict]:
    return OVERRUN, {
        "error": "oracle sandbox aborted before a deterministic verdict",
        "sandbox_abort": str(error),
    }


def _run_local(
    source: str,
    entry: str,
    tests: list,
    step_limit: int = _STEP_LIMIT_DEFAULT,
):
    """Worker-side exec oracle; all untrusted loading and calls are traced."""
    with _step_budget(step_limit) as steps:
        fn, err = _compile(source, entry)
        if err:
            return FAIL, {"error": f"candidate: {err}"}
        for i, case in enumerate(tests):
            args = case.get("in", [])
            try:
                got = fn(*args)
            except _StepExceeded:
                return FAIL, {
                    "case": i,
                    "error": "step limit exceeded",
                    "step_limit": step_limit,
                }
            except MemoryError:
                raise
            except Exception as e:  # noqa: BLE001 - candidate raised => failed test
                return FAIL, {"case": i, "error": f"raised {type(e).__name__}: {e}"}
            if got != case.get("out"):
                return FAIL, {
                    "case": i,
                    "input": args,
                    "expected": case.get("out"),
                    "got": _short(got),
                }
    return PASS, {"cases_passed": len(tests), "steps": steps[0]}


def run(source: str, entry: str, tests: list, step_limit: int = _STEP_LIMIT_DEFAULT):
    """Execute a candidate in a fresh subprocess against fixed expected outputs."""
    try:
        return _run_isolated(
            "run",
            {"source": source, "entry": entry, "tests": tests, "step_limit": step_limit},
            step_limit=step_limit,
        )
    except OracleSandboxAborted as e:
        return _sandbox_abort_verdict(e)


def run_from_spec(source: str, budget) -> tuple:
    """programs.py entry point: pull the frozen {entry, tests, step_limit} spec
    from the commitment budget and execute ``source`` against it."""
    spec = _load_spec(budget)
    if not spec.get("tests") or not spec.get("entry"):
        return OVERRUN, {"error": "exec-oracle spec missing entry/tests"}
    return run(source, spec["entry"], spec["tests"], int(spec.get("step_limit", _STEP_LIMIT_DEFAULT)))


def exec_oracle_commitment(entry: str, tests: list, step_limit: int = _STEP_LIMIT_DEFAULT) -> Commitment:
    """Build a content-addressed exec-oracle commitment (like hv-floor/lineage-ref):
    the entry point + fixed test cases are frozen into the id, so verdicts are
    replay-stable and retuning the tests only affects future instantiations. A
    conjecture carrying this commitment is refuted by RUNNING it and failing a
    test — criticism grounded in execution."""
    spec = {"entry": entry, "tests": tests, "step_limit": step_limit}
    digest = sha256_hex(canonical_json(spec))[:12]
    return Commitment(
        id=f"exec-oracle@{digest}",
        eval=f"program:{EXEC_PROGRAM}",
        budget=Budget(extra={"spec": json.dumps(spec, sort_keys=True)}),
    )


# ---------------------------------------------------------------------------
# Property oracle: reference-free execution verdicts.
#
# exec_oracle needs expected outputs, which means someone already SOLVED the
# problem — it can only verify re-derivations. The property oracle replaces
# expected outputs with a CHECKER: `def check(inp, out)` decides whether the
# candidate's output satisfies the problem's correctness properties for that
# input. No reference implementation exists anywhere in the loop, so the
# harness can pose problems nobody has answered. The checker (and the optional
# `def valid(inp)` input gate) are untrusted source too and run under the same
# AST guard + whitelist sandbox + step bound as the candidate.
#
# This is also what makes the critic's grounded recourse REAL: a critic can
# propose a NEW input (a counterexample), and because correctness is decided
# by the checker rather than a frozen expected output, the harness can run it
# and mint a demonstrative refutation on the spot (counterexample_commitment).
# ---------------------------------------------------------------------------


def _run_property_local(
    source: str,
    entry: str,
    inputs: list,
    checker: str,
    step_limit: int = _STEP_LIMIT_DEFAULT,
):
    """Run the candidate on each args-list in ``inputs`` and PASS iff
    ``check(args, out)`` is truthy for every one. A candidate exception or
    step overrun fails; a checker exception fails the candidate too (the
    output was un-checkable, e.g. wrong shape). An unusable CHECKER is an
    ``overrun`` — a spec defect, not the candidate's fault (§1)."""
    with _step_budget(step_limit) as steps:
        fn, err = _compile(source, entry)
        if err:
            return FAIL, {"error": f"candidate: {err}"}
        check, cerr = _compile(checker, "check")
        if cerr:
            return OVERRUN, {"error": f"property checker unusable: {cerr}"}
        for i, args in enumerate(inputs):
            try:
                got = fn(*args)
            except _StepExceeded:
                return FAIL, {
                    "case": i,
                    "error": "step limit exceeded",
                    "step_limit": step_limit,
                }
            except MemoryError:
                raise
            except Exception as e:  # noqa: BLE001 - candidate raised => failed case
                return FAIL, {"case": i, "error": f"raised {type(e).__name__}: {e}"}
            try:
                ok = check(args, got)
            except _StepExceeded:
                return FAIL, {
                    "case": i,
                    "error": "step limit exceeded in checker",
                    "step_limit": step_limit,
                }
            except MemoryError:
                raise
            except Exception as e:  # noqa: BLE001 - un-checkable output => failed case
                return FAIL, {
                    "case": i,
                    "error": f"checker raised {type(e).__name__}: {e}",
                    "got": _short(got),
                }
            if not ok:
                return FAIL, {
                    "case": i,
                    "input": args,
                    "got": _short(got),
                    "error": "property violated",
                }
    return PASS, {"cases_passed": len(inputs), "steps": steps[0]}


def run_property(
    source: str,
    entry: str,
    inputs: list,
    checker: str,
    step_limit: int = _STEP_LIMIT_DEFAULT,
):
    """Execute candidate and checker together in one isolated worker."""
    try:
        return _run_isolated(
            "property",
            {
                "source": source,
                "entry": entry,
                "inputs": inputs,
                "checker": checker,
                "step_limit": step_limit,
            },
            step_limit=step_limit,
        )
    except OracleSandboxAborted as e:
        return _sandbox_abort_verdict(e)


def run_property_from_spec(source: str, budget) -> tuple:
    """programs.py entry point for property_oracle commitments."""
    spec = _load_spec(budget)
    if not spec.get("inputs") or not spec.get("entry") or not spec.get("checker"):
        return OVERRUN, {"error": "property-oracle spec missing entry/inputs/checker"}
    return run_property(
        source, spec["entry"], spec["inputs"], spec["checker"],
        int(spec.get("step_limit", _STEP_LIMIT_DEFAULT)),
    )


def _load_spec(budget) -> dict:
    try:
        return json.loads(budget.extra.get("spec", "{}")) if budget and budget.extra else {}
    except (ValueError, AttributeError):
        return {}


def property_oracle_commitment(
    entry: str,
    inputs: list,
    checker: str,
    input_check: str | None = None,
    step_limit: int = _STEP_LIMIT_DEFAULT,
    generator: str | None = None,
    input_contract: str | None = None,
) -> Commitment:
    """Content-addressed property-oracle commitment. ``checker`` is the source
    of ``def check(inp, out)`` (inp = the args list); ``input_check`` is the
    optional source of ``def valid(inp)`` gating which NEW inputs count as
    admissible counterexamples (without it, a critic could 'refute' any
    candidate with garbage the problem never posed). ``generator`` is the
    optional source of ``def gen(k)`` — a PURE function from an index to an
    input — enabling the deterministic fuzz pass (fuzz_property): the harness
    probing the input space itself, no LLM in the loop. ``input_contract`` is
    a human-readable statement of what inputs are admissible; it is rendered
    in packs and echoed in gate rejections so an LLM critic fixated on an
    out-of-scope attack (e.g. cycles when the gate demands DAGs) gets told in
    words, not just a False."""
    spec = {"entry": entry, "inputs": inputs, "checker": checker,
            "input_check": input_check, "step_limit": step_limit}
    if generator:
        spec["generator"] = generator
    if input_contract:
        spec["input_contract"] = input_contract
    digest = sha256_hex(canonical_json(spec))[:12]
    return Commitment(
        id=f"prop-oracle@{digest}",
        eval=f"program:{PROPERTY_PROGRAM}",
        budget=Budget(extra={"spec": json.dumps(spec, sort_keys=True)}),
    )


def _gate_local(source: str, args: list, step_limit: int) -> tuple[str, str]:
    """Worker-side admission gate load and call."""
    with _step_budget(step_limit):
        valid, err = _compile(source, "valid")
        if err:
            return "unusable", err
        try:
            return ("accept", "") if valid(args) else ("reject", "")
        except _StepExceeded:
            return "raised", "StepExceeded"
        except MemoryError:
            raise
        except Exception as e:  # noqa: BLE001 - deterministic gate rejection detail
            return "raised", type(e).__name__


def admit_counterexample(base: Commitment, args) -> tuple[Commitment | None, str]:
    """Admission for the critic's grounded recourse: returns (commitment, "")
    when the proposed counterexample is admissible, else (None, reason). The
    reason is DETERMINISTIC information the gate produced — callers may echo
    it back to the critic (a one-shot caller otherwise never learns why its
    input refuted nothing). The minted commitment is a property oracle whose
    single input is the counterexample, inheriting the BASE spec's
    entry/checker/input_check verbatim; content-addressed, so the same
    proposal replays to the same commitment."""
    if base.eval != f"program:{PROPERTY_PROGRAM}":
        return None, "target commitment is not a property oracle: counterexamples do not apply"
    if not isinstance(args, list):
        return None, "counterexample must be a JSON LIST of positional args for the entry point"
    spec = _load_spec(base.budget)
    if not spec.get("entry") or not spec.get("checker"):
        return None, "base spec is missing entry/checker"
    gate = spec.get("input_check")
    if gate:
        limit = int(spec.get("step_limit", _STEP_LIMIT_DEFAULT))
        contract = spec.get("input_contract")
        contract_note = f" INPUT CONTRACT: {contract}" if contract else ""
        try:
            outcome, detail = _run_isolated(
                "gate",
                {"source": gate, "args": args, "step_limit": limit},
                step_limit=limit,
            )
        except OracleSandboxAborted:
            return None, (
                "admission gate sandbox aborted — admitting nothing (fail closed)."
                + contract_note
            )
        if outcome == "unusable":
            return None, "admission gate unusable — admitting nothing (fail closed)"
        if outcome == "raised":
            return None, (
                f"admission gate raised on this input ({detail}) — rejected."
                + contract_note
            )
        if outcome == "reject":
            return None, (
                "input rejected by the admission gate (def valid(inp) returned "
                "False) — re-read the gate source and satisfy every constraint."
                + contract_note
            )
    return property_oracle_commitment(
        spec["entry"], [args], spec["checker"], gate,
        int(spec.get("step_limit", _STEP_LIMIT_DEFAULT)),
    ), ""


def counterexample_commitment(base: Commitment, args) -> Commitment | None:
    """Admission without the reason (see admit_counterexample)."""
    return admit_counterexample(base, args)[0]


def _fuzz_property_local(
    source: str,
    spec: dict,
    fuzz_n: int,
    generator: str,
    checker: str,
) -> tuple[list | None, dict]:
    """Worker-side deterministic fuzz pass."""
    limit = int(spec.get("step_limit", _STEP_LIMIT_DEFAULT))
    with _step_budget(limit):
        gen, gerr = _compile(generator, "gen")
    if gerr:
        return None, {"fuzzed": 0, "note": f"generator unusable: {gerr}"}
    gate = spec.get("input_check")
    valid = None
    if gate:
        with _step_budget(limit):
            valid, verr = _compile(gate, "valid")
        if verr:
            return None, {
                "fuzzed": 0,
                "note": "gate unusable — fuzzing nothing (fail closed)",
            }

    tried = 0
    for k in range(max(0, fuzz_n)):
        with _step_budget(limit):
            try:
                candidate_input = gen(k)
                if not isinstance(candidate_input, list):
                    continue
                canonical_json(candidate_input)  # IPC/log-safe, JSON-domain inputs only
                if valid is not None and not valid(candidate_input):
                    continue
            except (_StepExceeded, TypeError, ValueError):
                continue
            except MemoryError:
                raise
            except Exception:  # noqa: BLE001 - a bad generated input is skipped
                continue
        tried += 1
        verdict, detail = _run_property_local(
            source, spec["entry"], [candidate_input], checker, limit
        )
        if verdict == FAIL:
            return candidate_input, {"fuzzed": tried, "k": k, **detail}
        if verdict == OVERRUN:
            return None, {
                "fuzzed": tried,
                "note": "property oracle produced no verdict during fuzzing",
                "oracle_overrun": True,
                **detail,
            }
    return None, {"fuzzed": tried, "note": "no violation found"}


def fuzz_property(
    source: str,
    base: Commitment,
    fuzz_n: int,
    generator: str | None = None,
    checker: str | None = None,
) -> tuple[list | None, dict]:
    """The harness's OWN experimenter — deterministic property-based fuzzing
    (QuickCheck inside the criticism loop). Enumerate ``gen(0..fuzz_n-1)`` from
    the spec's generator, keep the gate-valid inputs, RUN the candidate on
    each, and return the first input whose output violates the checker —
    (input, detail), or (None, detail) when everything holds or no generator
    exists. No LLM anywhere: an input an LLM critic cannot construct (probe
    result: two frontier models fixated on out-of-contract cycle attacks for
    15 straight proposals) is often trivially reachable by enumeration.
    Deterministic (§0): gen is a PURE function of the index k — no PRNG, no
    wall-clock — so the search replays byte-for-byte; gen/gate/candidate all
    run untrusted under the same AST guard + sandbox + step bound.

    ``generator`` overrides the spec's own — this is how EXPERIMENTER-proposed
    generators (rules/experiment.py) plug in. Soundness is generator-
    independent by construction: whoever wrote gen, the frozen gate admits
    each input and the checker decides each violation.

    ``checker`` overrides the spec's checker — this is how PROPOSED PROPERTIES
    plug in. Unlike generators, a checker DOES decide verdicts, so an override
    is only as trustworthy as its own adjudication: callers must gate it
    (checker_wf + relevance trial + wipeout guard, rules/experiment.py) and
    mint the violation against a commitment that DECLARES its source artifact,
    so refuting the property collapses its refutations (edges.py closure)."""
    spec = _load_spec(base.budget)
    generator = generator or spec.get("generator")
    if base.eval != f"program:{PROPERTY_PROGRAM}" or not generator:
        return None, {"fuzzed": 0, "note": "no generator in spec"}
    if checker is None:
        checker = spec["checker"]
    limit = int(spec.get("step_limit", _STEP_LIMIT_DEFAULT))
    try:
        return _run_isolated(
            "fuzz",
            {
                "source": source,
                "spec": spec,
                "fuzz_n": fuzz_n,
                "generator": generator,
                "checker": checker,
            },
            step_limit=limit,
            units=max(1, fuzz_n),
        )
    except OracleSandboxAborted as e:
        return None, {
            "fuzzed": 0,
            "note": "fuzz sandbox aborted before a deterministic result",
            "sandbox_abort": str(e),
        }


# ---------------------------------------------------------------------------
# Experimenter-designed generators (rules/experiment.py).
#
# An LLM proposes `def gen(k)` sources; the harness adjudicates them BY THEIR
# FRUITS, mechanically: generator_wf is an ordinary program commitment whose
# verdict is a pure function of the generator source — does it compile under
# the guard, does it YIELD gate-valid inputs, does it reach anything NOVEL
# (an input outside the frozen suite)? No judge, no trial: a generator can
# never create a false refutation (gate + checker stay frozen), so the only
# question a generator ever poses is "is this a productive place to look?" —
# and that is decidable by running it.
# ---------------------------------------------------------------------------

GENERATOR_PROGRAM = "generator_wf"
_GEN_PROBE_N = 64
_GEN_MIN_VALID = 8


def _check_generator_local(
    source: str,
    gate: str | None,
    frozen_inputs: list,
    probe_n: int = _GEN_PROBE_N,
    min_valid: int = _GEN_MIN_VALID,
    step_limit: int = _STEP_LIMIT_DEFAULT,
) -> tuple[str, dict]:
    """Well-formedness of a proposed generator: enumerate gen(0..probe_n-1)
    under the sandbox and PASS iff at least ``min_valid`` outputs are gate-
    valid AND at least one gate-valid output is NOVEL (not among the frozen
    inputs — a generator that only replays the known suite designs no
    experiment). Deterministic pure function of the source."""
    with _step_budget(step_limit):
        gen, gerr = _compile(source, "gen")
    if gerr:
        return FAIL, {"error": f"generator: {gerr}"}
    valid = None
    if gate:
        with _step_budget(step_limit):
            valid, verr = _compile(gate, "valid")
        if verr:
            return OVERRUN, {"error": f"admission gate unusable: {verr}"}

    frozen = {canonical_json(i) for i in frozen_inputs}
    valid_count = 0
    novel = False
    for k in range(max(0, probe_n)):
        with _step_budget(step_limit):
            try:
                candidate_input = gen(k)
                if not isinstance(candidate_input, list):
                    continue
                encoded = canonical_json(candidate_input)
                if valid is not None and not valid(candidate_input):
                    continue
            except (_StepExceeded, TypeError, ValueError):
                continue
            except MemoryError:
                raise
            except Exception:  # noqa: BLE001 - a bad generated input just doesn't count
                continue
        valid_count += 1
        if encoded not in frozen:
            novel = True
    if valid_count < min_valid:
        return FAIL, {"valid": valid_count, "probe_n": probe_n,
                      "error": f"yield too low: {valid_count}/{probe_n} gate-valid "
                               f"(need {min_valid})"}
    if not novel:
        return FAIL, {"valid": valid_count, "probe_n": probe_n,
                      "error": "no novel input: every gate-valid output replays "
                               "the frozen suite"}
    return PASS, {"valid": valid_count, "probe_n": probe_n, "novel": True}


def check_generator(
    source: str,
    gate: str | None,
    frozen_inputs: list,
    probe_n: int = _GEN_PROBE_N,
    min_valid: int = _GEN_MIN_VALID,
    step_limit: int = _STEP_LIMIT_DEFAULT,
) -> tuple[str, dict]:
    """Evaluate a proposed generator wholly inside one isolated worker."""
    try:
        return _run_isolated(
            "generator",
            {
                "source": source,
                "gate": gate,
                "frozen_inputs": frozen_inputs,
                "probe_n": probe_n,
                "min_valid": min_valid,
                "step_limit": step_limit,
            },
            step_limit=step_limit,
            units=max(1, probe_n),
        )
    except OracleSandboxAborted as e:
        return _sandbox_abort_verdict(e)


def check_generator_from_spec(source: str, budget) -> tuple:
    """programs.py entry point for generator_wf commitments."""
    spec = _load_spec(budget)
    if "inputs" not in spec:
        return OVERRUN, {"error": "generator-wf spec missing inputs"}
    return check_generator(
        source,
        spec.get("input_check"),
        spec["inputs"],
        int(spec.get("probe_n", _GEN_PROBE_N)),
        int(spec.get("min_valid", _GEN_MIN_VALID)),
        int(spec.get("step_limit", _STEP_LIMIT_DEFAULT)),
    )


# ---------------------------------------------------------------------------
# Proposed PROPERTIES (rules/experiment.py): conjectured ground truth.
#
# A checker is NOT a generator: it decides verdicts, so a bogus one can refute
# correct code. The defense is layered, and none of it is a judge deciding a
# status by fiat:
#   1. checker_wf (here): mechanical — compiles under the guard, runs bounded,
#      and is NON-VACUOUS (rejects at least one degenerate output on a probe
#      input; a checker that accepts everything can never refute anything but
#      could be used to feign rigor).
#   2. Relevance trial (rules/experiment.py): cross-family judge ensemble on
#      the narrow question "does this follow from the problem statement?" —
#      the §3 sanctioned path for informal claims.
#   3. Wipeout guard at use time: a property every accepted sibling also
#      violates refutes the population, not a candidate — quarantined.
#   4. The structural safety net (edges.py): every violation is minted against
#      a commitment that DECLARES source_artifact = the property; the att
#      closure gives the property's attackers an edge onto each verdict's nu,
#      so refuting the property REINSTATES everything it felled. Nothing an
#      LLM proposes ever becomes unaccountable ground truth.
# ---------------------------------------------------------------------------

CHECKER_PROGRAM = "checker_wf"
# Degenerate outputs no legitimate correctness property should bless for
# every input: the empty list, zero, the empty string, None, and the echoed
# input. Fixed battery => deterministic verdicts.
_VACUITY_BATTERY = ([], 0, "", None, "echo-input")


def _check_checker_local(
    source: str,
    probe_inputs: list,
    step_limit: int = _STEP_LIMIT_DEFAULT,
) -> tuple[str, dict]:
    """Well-formedness of a proposed property checker: compiles under the
    guard, exposes check(inp, out), stays within the step bound on the probe
    battery, and REJECTS (falsy or raise) at least one degenerate output on
    at least one probe input — non-vacuity. Deterministic pure function of
    the source."""
    with _step_budget(step_limit):
        check, err = _compile(source, "check")
    if err:
        return FAIL, {"error": f"checker: {err}"}

    rejected_any = False
    returned_any = False  # returned a bool at least once (didn't just raise)
    for args in probe_inputs[:4]:
        for degenerate in _VACUITY_BATTERY:
            out = args if degenerate == "echo-input" else degenerate
            with _step_budget(step_limit):
                try:
                    if check(args, out):
                        returned_any = True
                    else:
                        rejected_any = True
                        returned_any = True
                except MemoryError:
                    raise
                except Exception:  # noqa: BLE001 - rejection by exception counts
                    rejected_any = True
    if not rejected_any:
        return FAIL, {"error": "vacuous checker: accepts every degenerate output "
                               "on every probe input — it can never refute anything"}
    if not returned_any:
        # An always-raising checker (e.g. truncated code -> unconditional
        # NameError) is broken, not strict: it would 'violate' every candidate
        # ever written. Rejection must be a decision at least once.
        return FAIL, {"error": "broken checker: raised on every battery pair — "
                               "it never actually decides anything"}
    return PASS, {"non_vacuous": True, "probes": len(probe_inputs[:4])}


def check_checker(
    source: str,
    probe_inputs: list,
    step_limit: int = _STEP_LIMIT_DEFAULT,
) -> tuple[str, dict]:
    """Evaluate a proposed checker wholly inside one isolated worker."""
    units = max(1, len(probe_inputs[:4]) * len(_VACUITY_BATTERY))
    try:
        return _run_isolated(
            "checker",
            {
                "source": source,
                "probe_inputs": probe_inputs,
                "step_limit": step_limit,
            },
            step_limit=step_limit,
            units=units,
        )
    except OracleSandboxAborted as e:
        return _sandbox_abort_verdict(e)


def check_checker_from_spec(source: str, budget) -> tuple:
    """programs.py entry point for checker_wf commitments."""
    spec = _load_spec(budget)
    if "inputs" not in spec:
        return OVERRUN, {"error": "checker-wf spec missing inputs"}
    return check_checker(
        source, spec["inputs"], int(spec.get("step_limit", _STEP_LIMIT_DEFAULT))
    )


def checker_wf_commitment(base: Commitment) -> Commitment | None:
    """Content-addressed checker-wf commitment derived from a property oracle:
    freezes the base's probe inputs. A proposed-property artifact carrying
    this commitment is adjudicated mechanically on arrival by crit_program."""
    if base.eval != f"program:{PROPERTY_PROGRAM}":
        return None
    base_spec = _load_spec(base.budget)
    if not base_spec.get("entry"):
        return None
    spec = {
        "for": base.id,
        "inputs": base_spec.get("inputs", [])[:4],
        "step_limit": int(base_spec.get("step_limit", _STEP_LIMIT_DEFAULT)),
    }
    digest = sha256_hex(canonical_json(spec))[:12]
    return Commitment(
        id=f"chk-wf@{digest}",
        eval=f"program:{CHECKER_PROGRAM}",
        budget=Budget(extra={"spec": json.dumps(spec, sort_keys=True)}),
    )


def property_violation_commitment(
    base: Commitment, property_artifact_id: str, property_source: str, args: list
) -> Commitment:
    """Mint the commitment for a proposed-property violation: a property
    oracle whose single input is the violating args and whose CHECKER is the
    property's own source, frozen at mint time (later edits to the property
    artifact cannot rewrite past verdicts — D8-friendly). The property
    artifact id is DECLARED as source_artifact both inside the content-
    addressed spec and as a top-level budget key, which the att closure
    (edges.py) reads: attackers of the property attack every nu hanging on
    this commitment, so refuting the property reinstates its victims."""
    base_spec = _load_spec(base.budget)
    spec = {
        "entry": base_spec.get("entry"),
        "inputs": [args],
        "checker": property_source,
        "input_check": base_spec.get("input_check"),
        "step_limit": int(base_spec.get("step_limit", _STEP_LIMIT_DEFAULT)),
        "source_artifact": property_artifact_id,
    }
    digest = sha256_hex(canonical_json(spec))[:12]
    return Commitment(
        id=f"prop-oracle@{digest}",
        eval=f"program:{PROPERTY_PROGRAM}",
        budget=Budget(extra={
            "spec": json.dumps(spec, sort_keys=True),
            "source_artifact": property_artifact_id,
        }),
    )


def generator_wf_commitment(
    base: Commitment,
    probe_n: int = _GEN_PROBE_N,
    min_valid: int = _GEN_MIN_VALID,
) -> Commitment | None:
    """Content-addressed generator-wf commitment derived from a property
    oracle: freezes the base's gate + frozen inputs (novelty reference) with
    the probe parameters. A generator artifact carrying this commitment is
    adjudicated by crit_program exactly like any candidate — a generator that
    doesn't compile, doesn't yield, or designs no new experiment is REFUTED
    by a demonstrative warrant, mechanically."""
    if base.eval != f"program:{PROPERTY_PROGRAM}":
        return None
    base_spec = _load_spec(base.budget)
    if not base_spec.get("entry"):
        return None
    spec = {
        "for": base.id,
        "inputs": base_spec.get("inputs", []),
        "input_check": base_spec.get("input_check"),
        "probe_n": probe_n,
        "min_valid": min_valid,
        "step_limit": int(base_spec.get("step_limit", _STEP_LIMIT_DEFAULT)),
    }
    digest = sha256_hex(canonical_json(spec))[:12]
    return Commitment(
        id=f"gen-wf@{digest}",
        eval=f"program:{GENERATOR_PROGRAM}",
        budget=Budget(extra={"spec": json.dumps(spec, sort_keys=True)}),
    )


# Worker dispatch deliberately names only internal implementations: public
# wrappers spawn; worker-local functions never do.
_LOCAL_OPERATIONS = {
    "run": _run_local,
    "property": _run_property_local,
    "gate": _gate_local,
    "fuzz": _fuzz_property_local,
    "generator": _check_generator_local,
    "checker": _check_checker_local,
}
