"""The attribute boundary for untrusted model-authored code.

Regression (execution-safety tranche 2026-08-27): every sandbox in this
repository rejected attributes beginning with an underscore and nothing else.
`gg.gi_frame.f_back.f_back.f_globals` uses no underscore, so it walked out of
all four to the real `builtins` — a file written outside the scratch directory,
an arbitrary shell command, and a TCP connection to the open internet, each
while the verdict stayed `pass`.  See
`experiments/2026-08-27-change-execution-safety/SAFETY.md` findings E1-E3 and
`proof/containment_probe.py`.

Three obligations, all of them here:
  * the escape is rejected at every call site (the fix),
  * the rejected set is exactly CPython's introspection surface and is CLOSED
    (the fix is not a patch over three attribute names),
  * legitimate model code still runs (REQUEST.md C8, "it doesn't break other
    modules") — a guard that closed the escape by rejecting everything would
    pass the first two and fail the operator.
"""

from __future__ import annotations

import ast
import errno
import hashlib
import inspect
import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

from deepreason import programs
from deepreason.harness import Harness
from deepreason.ontology import Provenance
from deepreason.oracle import exec_oracle_commitment
from deepreason.sandbox_guard import (
    FORBIDDEN_ATTRIBUTE_NAMES,
    FORBIDDEN_ATTRIBUTE_PREFIXES,
    WORKER_GUARD_SOURCE,
    attribute_violation,
    forbidden_attribute,
    forbidden_name,
)
from deepreason.verification import contained as contained_module
from deepreason.verification.contained import (
    CONTAINED_WORKER_SHA256,
    CONTAINED_WORKER_SOURCE_V1,
    ContainedSimulationBackend,
    _apply_containment_limits,
    _containment_limits,
)
from deepreason.verification.simulation import SimulationRequest
from deepreason.workloads.code import SimulationSpec

CONTAINMENT_AVAILABLE = ContainedSimulationBackend.containment_available()
needs_containment = pytest.mark.skipif(
    not CONTAINMENT_AVAILABLE,
    reason="host cannot create an unshared network namespace",
)

# The escape, verbatim from the reproduction that was RED before this fix.
# No attribute in the chain begins with an underscore.
FRAME_WALK = (
    "    box = []\n"
    "    def g():\n"
    "        box.append(gg.gi_frame.f_back.f_back.f_globals)\n"
    "        yield 1\n"
    "    gg = g()\n"
    "    for v in gg:\n"
    "        break\n"
    "    w = box[0]\n"
)


# --- the boundary itself ---------------------------------------------------- #


def test_the_escape_chain_is_rejected_attribute_by_attribute():
    """Each link, not just the whole chain: a fix that caught only `gi_frame`
    would leave `f_globals` reachable from any other frame source."""

    for attribute in ("gi_frame", "f_back", "f_globals", "f_locals", "f_builtins"):
        assert forbidden_attribute(attribute), attribute
    for attribute in ("cr_frame", "ag_frame", "tb_frame", "co_consts", "mro"):
        assert forbidden_attribute(attribute), attribute
    assert forbidden_attribute("__class__") and forbidden_attribute("__globals__")


def test_the_prefix_set_covers_every_public_introspection_attribute():
    """The CLOSURE proof, re-derived from the running interpreter.

    This is the property a hand-maintained denylist cannot have: it walks the
    real attribute list of every object type that can carry scope, and pins the
    residue to a frozen set.  A future CPython that adds an introspection
    attribute under a new prefix turns this RED rather than silently reopening
    the hole.
    """

    def generator():
        yield 1

    async def coroutine():
        return None

    async def async_generator():
        yield 1

    try:
        raise ValueError("sample")
    except ValueError as error:
        traceback_object = error.__traceback__

    running = coroutine()
    generating = async_generator()
    try:
        samples = {
            "generator": generator(),
            "coroutine": running,
            "async_generator": generating,
            "traceback": traceback_object,
            "frame": inspect.currentframe(),
            "code": (lambda: 0).__code__,
            "function": (lambda: 0),
            "method": [].append,
            "type": type,
        }

        # Everything public that survives the boundary, across every
        # scope-bearing type. Frozen: this set is the whole residue.
        residue = {
            name
            for obj in samples.values()
            for name in dir(obj)
            if not name.startswith("_") and not forbidden_attribute(name)
        }
    finally:
        running.close()

    assert residue == {
        # Generator/coroutine/async-generator PROTOCOL methods. They resume or
        # finalise an object you must ALREADY hold, and return only what that
        # object yields — never a frame, code object or namespace.
        "close",
        "send",
        "throw",
        "aclose",
        "asend",
        "athrow",
        # frame.clear() -> None, code.replace() -> a new code object. Both
        # require already holding a frame or code object, and every attribute
        # that YIELDS one is rejected above. They are also the names of
        # ordinary container/string methods (list.clear, str.replace), which is
        # why rejecting them would break legitimate code for no safety gain.
        "clear",
        "replace",
    }, sorted(residue)


def test_no_residual_attribute_is_reachable_as_a_first_step():
    """The other half of closure: the residue is safe only because nothing in
    the sandbox hands model code an object that carries it."""

    import math
    import random

    reachable = (math, random.Random(0), [], {}, set(), "", 0, 0.0, (), True)
    residue = {"send", "throw", "aclose", "asend", "athrow"}
    for obj in reachable:
        assert not (residue & set(dir(obj))), (type(obj).__name__, residue & set(dir(obj)))


def test_names_are_judged_by_the_underscore_rule_only():
    """A local variable named `f_total` reaches nothing; `obj.f_total` is
    indistinguishable from a frame walk at parse time. The asymmetry is
    deliberate, so it is pinned."""

    assert forbidden_name("_hidden") and forbidden_name("__import__")
    assert not forbidden_name("f_total") and not forbidden_name("gi_count")
    assert forbidden_attribute("f_total") and forbidden_attribute("gi_count")


def test_attribute_violation_reports_the_first_offending_access():
    assert attribute_violation(ast.parse("x = 1\n")) is None
    assert "f_globals" in (attribute_violation(ast.parse("y = g.gi_frame.f_globals")) or "")
    assert "forbidden name" in (attribute_violation(ast.parse("z = __import__")) or "")


# --- one definition, four consumers ----------------------------------------- #


def test_the_frozen_worker_carries_the_same_boundary_not_a_copy():
    """The contained worker cannot import this repository — its environment is
    scrubbed and carries no PYTHONPATH — so it gets the rule as generated
    source. Generated, not hand-copied: the two must agree on every input."""

    assert "__DEEPREASON_SANDBOX_GUARD__" not in CONTAINED_WORKER_SOURCE_V1
    assert WORKER_GUARD_SOURCE.rstrip("\n") in CONTAINED_WORKER_SOURCE_V1

    namespace: dict = {}
    exec(compile(WORKER_GUARD_SOURCE, "<worker-guard>", "exec"), namespace)  # noqa: S102
    worker_rule = namespace["forbidden_attribute"]

    assert tuple(namespace["FORBIDDEN_ATTRIBUTE_PREFIXES"]) == FORBIDDEN_ATTRIBUTE_PREFIXES
    assert set(namespace["FORBIDDEN_ATTRIBUTE_NAMES"]) == set(FORBIDDEN_ATTRIBUTE_NAMES)

    probes = [
        "gi_frame", "f_back", "f_globals", "cr_frame", "ag_frame", "tb_frame",
        "co_consts", "func_globals", "im_self", "mro", "__class__",
        "sqrt", "randint", "append", "items", "join", "replace", "clear",
    ]
    for probe in probes:
        assert worker_rule(probe) == forbidden_attribute(probe), probe


def test_worker_identity_moved_and_is_still_self_consistent():
    """A changed worker is a changed runtime identity, visible in every
    execution receipt's fingerprint. That is the design working, and it is why
    the sha is asserted rather than pinned to a literal."""

    assert CONTAINED_WORKER_SHA256 == hashlib.sha256(
        CONTAINED_WORKER_SOURCE_V1.encode("utf-8")
    ).hexdigest()
    ast.parse(CONTAINED_WORKER_SOURCE_V1)


def test_the_brokered_worker_inherits_the_boundary_by_derivation():
    """A fifth call site, found only by running the wider ring.

    `verification/brokered.py` does not carry its own guard: it DERIVES its
    worker from `CONTAINED_WORKER_SOURCE_V1`, so it inherited this fix without
    being touched. That is the property worth pinning — a derivation that
    stopped deriving would silently reopen the hole in a worker nobody thought
    to look at.
    """

    from deepreason.verification.brokered import (
        BROKERED_WORKER_SHA256_V2,
        BROKERED_WORKER_SOURCE_V2,
    )

    assert "FORBIDDEN_ATTRIBUTE_PREFIXES" in BROKERED_WORKER_SOURCE_V2
    assert WORKER_GUARD_SOURCE.rstrip("\n") in BROKERED_WORKER_SOURCE_V2
    assert BROKERED_WORKER_SHA256_V2 != CONTAINED_WORKER_SHA256

    namespace: dict = {}
    exec(compile(BROKERED_WORKER_SOURCE_V2, "<brokered>", "exec"), namespace)  # noqa: S102
    function, error = namespace["load_function"](
        "def simulate(inputs, rng):\n" + FRAME_WALK + "    return {'value': 1}\n",
        "simulate",
        "simulation",
        {},
    )
    assert function is None
    assert "f_globals" in error


def test_every_guard_call_site_consults_the_shared_boundary():
    """The architecture check the modularity law asks for: it goes RED when a
    consumer reimplements the rule locally instead of consuming the interface.
    Four call sites executed model-authored Python with four private copies of
    one rule; that is how one hole became four."""

    import deepreason.oracle
    import deepreason.programs
    import deepreason.verification.simulation

    for module in (
        deepreason.oracle,
        deepreason.programs,
        deepreason.verification.simulation,
    ):
        source = pathlib.Path(module.__file__).read_text()
        assert "from deepreason.sandbox_guard import" in source, module.__name__
        assert 'attr.startswith("_")' not in source, (
            f"{module.__name__} still carries a private copy of the rule"
        )


# --- the escape, driven end to end at each call site ------------------------ #


class _Blobs(dict):
    def put(self, data: bytes) -> str:
        ref = hashlib.sha256(data).hexdigest()
        self[ref] = data
        return ref

    def get(self, ref: str) -> bytes:
        return self[ref]


_CHECKER = "def check(input_item, seed, output):\n    return {'pass': True, 'metrics': {}}\n"


def _contained(source: str, *, toolchain: str = "python@guard-test"):
    blobs = _Blobs()
    inputs = json.dumps(
        [{"parameter_set": "d", "parameters": {"base": 3}, "sealed_inputs": {}}]
    ).encode()
    spec = SimulationSpec(
        entry="simulate",
        seed_set=(7,),
        inputs_ref=blobs.put(inputs),
        observables=("value",),
        checker_ref=blobs.put(_CHECKER.encode()),
        deterministic_step_limit=200_000,
        sample_limit=8,
        toolchain_id=toolchain,
    )
    request = SimulationRequest(
        source_ref=blobs.put(source.encode()), spec=spec, maximum_output_bytes=65_536
    )
    backend = ContainedSimulationBackend(
        toolchain_id=toolchain,
        maximum_wall_ms=15_000,
        maximum_memory_bytes=512 * 1024 * 1024,
    )
    return backend.verify(request, blobs), blobs


@needs_containment
def test_contained_runner_refuses_the_frame_walk(tmp_path):
    """SAFETY.md E1/E2: this wrote a file outside the scratch directory and ran
    a shell command, verdict `pass`, before the fix."""

    marker = tmp_path / "escaped"
    result, _ = _contained(
        "def simulate(inputs, rng):\n"
        + FRAME_WALK
        + "    bi = w['builtins']\n"
        + f"    h = bi.open({str(marker)!r}, 'w')\n"
        + "    h.write('ESCAPED')\n"
        + "    h.close()\n"
        + "    return {'value': 1}\n"
    )
    assert result.verdict == "fail"
    assert "f_globals" in result.trace["error"]
    assert not marker.exists()


def test_code_testing_channel_refuses_the_frame_walk(tmp_path):
    """SAFETY.md E3: this opened a TCP connection to the open internet from
    inside the sandbox, and the exec-oracle commitment returned `pass`."""

    marker = tmp_path / "escaped"
    harness = Harness(tmp_path / "run")
    commitment = exec_oracle_commitment("double", [{"in": [2], "out": 4}])
    harness.register_commitment(commitment)
    hostile = harness.create_artifact(
        "def double(n):\n"
        + FRAME_WALK
        + "    rb = w['__builtins__']\n"
        + f"    rb['open']({str(marker)!r}, 'w').write('ESCAPED')\n"
        + "    return n * 2\n",
        codec="code:python",
        provenance=Provenance(role="conjecturer"),
    )
    verdict, _trace = programs.evaluate(commitment, hostile, harness.blobs)
    assert verdict == programs.FAIL
    assert not marker.exists()


def test_predicate_eval_refuses_the_frame_walk():
    with pytest.raises(programs.UnsafePredicate) as caught:
        programs._validate_predicate("(x for x in [1]).gi_frame.f_globals")
    # ast.walk is breadth-first, so the OUTERMOST access is named first. Either
    # link is a rejection; asserting the specific one pins walk order, not the
    # boundary.
    message = str(caught.value)
    assert "f_globals" in message or "gi_frame" in message


def test_declarative_simulation_worker_refuses_the_frame_walk():
    from deepreason.verification.simulation import _compile

    function, error = _compile(
        "def simulate(inputs, rng):\n" + FRAME_WALK + "    return {'value': 1}\n",
        "simulate",
        "simulation",
    )
    assert function is None
    assert "f_globals" in error


# --- C8: legitimate model code still runs ----------------------------------- #


@needs_containment
def test_ordinary_sandboxed_python_still_runs_and_still_passes():
    """The operator's constraint as a check: math, rng, container methods,
    nested functions, closures and comprehensions all still work.

    NOT exercised because it never worked: `class` statements. The builtin
    whitelist has no `__build_class__`, so a class definition raises
    `NameError` inside this sandbox, and did so identically before this fix
    (verified against the pre-fix tree). That is a pre-existing expressive
    limit of the sandbox, not a cost of the boundary — recorded here so the
    next reader does not attribute it to the fix. Parked at
    `experiments/2026-08-27-change-execution-safety/PARKED.md` P8."""

    result, blobs = _contained(
        "def simulate(inputs, rng):\n"
        "    base = inputs['parameters'].get('base', 2)\n"
        "    tally = {'total': 0}\n"
        "    def add(amount):\n"
        "        tally['total'] = tally['total'] + amount\n"
        "        return tally['total']\n"
        "    for step in [1, 2, 3]:\n"
        "        add(step * base)\n"
        "    squares = [v * v for v in range(4)]\n"
        "    label = ','.join([str(v) for v in squares]).replace('0', 'z')\n"
        "    counts = {}\n"
        "    for v in squares:\n"
        "        counts[v] = counts.get(v, 0) + 1\n"
        "    return {\n"
        "        'value': tally['total'],\n"
        "        'root': math.sqrt(base),\n"
        "        'jitter': rng.randint(0, 0),\n"
        "        'label': label,\n"
        "        'count': len(sorted(counts.items())),\n"
        "    }\n"
    )
    assert result.verdict == "pass", result.trace
    records = json.loads(blobs.get(result.output_ref))
    # Only DECLARED observables are recorded, so `value` is what comes back;
    # the string, dict and comprehension work is proved by the run reaching
    # `pass` at all -- any rejected attribute would have failed it at load.
    assert records[0]["observables"]["value"] == 18


def test_ordinary_code_testing_candidates_still_pass_and_still_fail(tmp_path):
    """Both directions: a road that can only say FAIL is no better than one
    that can only say PASS."""

    harness = Harness(tmp_path / "run")
    commitment = exec_oracle_commitment(
        "solve", [{"in": [2], "out": 4}, {"in": [5], "out": 10}]
    )
    harness.register_commitment(commitment)
    right = harness.create_artifact(
        "def solve(x):\n"
        "    doubled = [v * 2 for v in [x]]\n"
        "    return sorted(doubled)[0]\n",
        codec="code:python",
        provenance=Provenance(role="conjecturer"),
    )
    wrong = harness.create_artifact(
        "def solve(x):\n    return x + 2\n",
        codec="code:python",
        provenance=Provenance(role="conjecturer"),
    )
    assert programs.evaluate(commitment, right, harness.blobs)[0] == programs.PASS
    assert programs.evaluate(commitment, wrong, harness.blobs)[0] == programs.FAIL


def test_ordinary_predicates_still_validate():
    for expression in (
        "len(content) > 120",
        "'x' in content.lower()",
        "any(len(part) > 3 for part in content.split())",
        "content.replace('a', 'b').strip().startswith('z')",
        "json.loads(content).get('k') == 1",
    ):
        programs._validate_predicate(expression)


def test_ordinary_declarative_worker_sources_still_compile():
    from deepreason.verification.simulation import _compile

    function, error = _compile(
        "def simulate(inputs, rng):\n"
        "    return {'value': inputs['parameters']['base'] * 2}\n",
        "simulate",
        "simulation",
    )
    assert error is None and callable(function)


# --- the OS layer, which does not depend on the guard being right ----------- #


def test_the_code_testing_worker_runs_behind_the_network_namespace(monkeypatch):
    """Wiring: the probed prefix really is the head of the worker command.

    Asserted on the ACTUAL argv of a real `run_isolated` call, not on a
    configuration value the module reports about itself — the failure shape
    SAFETY.md G5 records, where a self-reported `"network": False` outlived the
    containment it described.
    """

    import subprocess

    from deepreason import oracle_sandbox
    from deepreason.sandbox_os import network_denial_available, network_denial_prefix

    if not network_denial_available():
        pytest.skip("host cannot create an unshared network namespace")

    seen: list[list[str]] = []
    real_popen = subprocess.Popen

    def recording_popen(command, *args, **kwargs):
        seen.append(list(command))
        return real_popen(command, *args, **kwargs)

    monkeypatch.setattr(oracle_sandbox.subprocess, "Popen", recording_popen)
    oracle_sandbox.run_isolated(
        "run",
        {
            "source": "def double(n):\n    return n * 2\n",
            "entry": "double",
            "tests": [{"in": [2], "out": 4}],
            "step_limit": 10_000,
        },
        step_limit=10_000,
    )

    assert seen, "run_isolated launched no subprocess"
    prefix = list(network_denial_prefix())
    assert seen[0][: len(prefix)] == prefix, seen[0]


# The probe both network differentials run. It reports an OS-level effect --
# the kernel's interface table and the errno a connect returns -- never a value
# any DeepReason module reports about itself.
_NETWORK_PROBE = (
    "import json, socket\n"
    "try:\n"
    "    socket.create_connection(('1.1.1.1', 80), 5).close()\n"
    "    reached, code = True, None\n"
    "except OSError as error:\n"
    "    reached, code = False, error.errno\n"
    "print(json.dumps({'reached': reached, 'errno': code,"
    " 'interfaces': sorted(name for _index, name in socket.if_nameindex())}))\n"
)


def _probe_network(prefix: tuple[str, ...]) -> dict:
    """Run `_NETWORK_PROBE` under `prefix`; `()` is the unprefixed outside arm."""

    return json.loads(
        subprocess.run(  # noqa: S603
            [*prefix, sys.executable, "-c", _NETWORK_PROBE],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout
    )


def _observed_environment(env: dict[str, str] | None) -> list[str]:
    """The variable names a real child SEES; `None` inherits the parent's."""

    return json.loads(
        subprocess.run(  # noqa: S603
            [sys.executable, "-c", "import json, os; print(json.dumps(sorted(os.environ)))"],
            capture_output=True, text=True, timeout=60, check=True, env=env,
        ).stdout
    )


def _assert_prefix_denies_network(prefix: tuple[str, ...], label: str) -> None:
    """Both arms of one network differential, or a skip -- never one arm.

    A one-armed inside check passes vacuously on a host whose only interface is
    already `lo`, which is the shape SAFETY.md G5 records: a test that cannot
    fail for the reason it exists. The outside arm is measured FIRST and the
    whole differential skips when the host has nothing to deny.
    """

    outside = _probe_network(())
    if outside["interfaces"] == ["lo"]:
        pytest.skip(f"{label}: host itself has only loopback, nothing to deny")
    inside = _probe_network(prefix)
    assert inside["interfaces"] == ["lo"], (label, inside, outside)
    assert set(outside["interfaces"]) > {"lo"}, (label, outside)
    assert inside["reached"] is False, (label, inside)
    assert inside["errno"] == errno.ENETUNREACH, (label, inside)


def test_the_network_namespace_actually_denies_network():
    """The differential the committed suite never carried, for the CODE-TESTING
    channel's prefix (`sandbox_os.network_denial_prefix`).

    Inside the probed prefix only the loopback interface exists and a connect
    returns ENETUNREACH; outside it, the same probe sees real interfaces. That
    is what makes property (a) a measurement rather than a claim — and it is
    the property that survived the escape when the language boundary did not.
    """

    from deepreason.sandbox_os import network_denial_available, network_denial_prefix

    if not network_denial_available():
        pytest.skip("host cannot create an unshared network namespace")

    _assert_prefix_denies_network(network_denial_prefix(), "code-testing channel")


def test_the_contained_backend_prefix_actually_denies_network():
    """The same differential for the CONTAINED simulation backend's OWN prefix.

    `verification/contained.py` probes for its prefix separately from
    `sandbox_os` and imports nothing from it, so a differential on one says
    nothing about the other. This one replaces the self-reports
    `resource_limits()["network"] is False` and
    `fingerprint()["network_denial"] == "namespace_unshared"`, both of which are
    dict literals that survive any regression in the launch they describe.
    """

    prefix = ContainedSimulationBackend.containment_prefix()
    if not prefix:
        pytest.skip("host cannot create an unshared network namespace")

    _assert_prefix_denies_network(prefix, "contained simulation backend")


@needs_containment
def test_the_contained_worker_argv_really_carries_the_probed_prefix(monkeypatch):
    """Wiring, on the ACTUAL argv of a real `ContainedSimulationBackend.verify`.

    `fingerprint()["network_denial"]` and `resource_limits()["network_denial"]`
    are literals at `contained.py:502` and `:521`; neither consults
    `containment_prefix()`, and nothing in `src/` reads them back. A launch that
    stopped prepending the prefix would keep reporting `namespace_unshared`.
    This test fails on that launch, because it reads the command that ran.
    """

    seen: list[tuple[list[str], object, dict]] = []
    real_popen = subprocess.Popen

    def recording_popen(command, *args, **kwargs):
        seen.append(
            (list(command), kwargs.get("cwd"), dict(kwargs.get("env") or {}))
        )
        return real_popen(command, *args, **kwargs)

    monkeypatch.setattr(contained_module.subprocess, "Popen", recording_popen)
    result, _ = _contained("def simulate(inputs, rng):\n    return {'value': 1}\n")

    assert result.verdict == "pass", result.trace
    assert seen, "the contained backend launched no subprocess"
    argv, _cwd, _env = seen[0]
    prefix = list(ContainedSimulationBackend.containment_prefix())
    assert prefix, "containment_available() was true but the prefix is empty"
    assert argv[: len(prefix)] == prefix, argv
    assert argv[len(prefix) :] == [sys.executable, "worker.py"], argv


@needs_containment
def test_the_contained_scratch_directory_is_the_cwd_and_does_not_survive(monkeypatch):
    """The honest replacement for `resource_limits()["filesystem"]`.

    That field reads `"ephemeral scratch workdir"`; it is a literal, and the
    prefix carries `--net` only, so no mount namespace stands behind it (see
    this tranche's `proof/filesystem_not_a_jail.out`). What IS true and
    observable is asserted here: the directory is the launch `cwd`, it is what
    `HOME` and `TMPDIR` point the worker at, and it is gone when `verify`
    returns.
    """

    captured: dict[str, str] = {}
    real_mkdtemp = tempfile.mkdtemp

    def observing_mkdtemp(*args, **kwargs):
        captured["scratch"] = real_mkdtemp(*args, **kwargs)
        return captured["scratch"]

    seen: list[tuple[list[str], object, dict]] = []
    real_popen = subprocess.Popen

    def recording_popen(command, *args, **kwargs):
        seen.append(
            (list(command), kwargs.get("cwd"), dict(kwargs.get("env") or {}))
        )
        return real_popen(command, *args, **kwargs)

    monkeypatch.setattr(contained_module.tempfile, "mkdtemp", observing_mkdtemp)
    monkeypatch.setattr(contained_module.subprocess, "Popen", recording_popen)
    result, _ = _contained("def simulate(inputs, rng):\n    return {'value': 1}\n")

    assert result.verdict == "pass", result.trace
    scratch = captured["scratch"]
    _argv, cwd, env = seen[0]
    assert cwd == scratch, (cwd, scratch)
    assert env["HOME"] == scratch, env
    assert env["TMPDIR"] == scratch, env
    assert not pathlib.Path(scratch).exists(), scratch


def test_the_contained_child_really_receives_every_declared_rlimit():
    """Read the limits BACK out of a child, instead of comparing two self-reports.

    `test_containment_limits_cover_every_resource_class` used to assert
    `resource_limits()[k] == _containment_limits(...)[k]` — the same pure
    function on both sides of the equals sign, which holds whether or not a
    single `setrlimit` ever runs. Here a real child is launched through
    `_apply_containment_limits` and reports its own `getrlimit`, and an
    otherwise identical child launched WITHOUT it is the second arm: every one
    of the five limits must differ between them, or the containment is
    measuring the ambient shell rather than doing anything.
    """

    readback = (
        "import json, resource\n"
        "print(json.dumps({k: resource.getrlimit(getattr(resource, 'RLIMIT_' + k))[0]"
        " for k in ('NOFILE', 'NPROC', 'FSIZE', 'AS', 'CPU')}))\n"
    )
    backend = ContainedSimulationBackend(
        toolchain_id="python@guard-test",
        maximum_wall_ms=20_000,
        maximum_memory_bytes=512 * 1024 * 1024,
    )
    reported = backend.resource_limits()
    limits = _containment_limits(
        maximum_wall_ms=20_000, maximum_memory_bytes=512 * 1024 * 1024
    )

    def child(**kwargs) -> dict:
        return json.loads(
            subprocess.run(  # noqa: S603
                [sys.executable, "-c", readback],
                capture_output=True, text=True, timeout=60, check=True, **kwargs,
            ).stdout
        )

    contained_child = child(
        preexec_fn=lambda: _apply_containment_limits(limits)  # noqa: PLW1509
    )
    bare_child = child()

    assert contained_child["NOFILE"] == reported["nofile"], contained_child
    assert contained_child["NPROC"] == reported["nproc"], contained_child
    assert contained_child["FSIZE"] == reported["fsize_bytes"], contained_child
    assert contained_child["AS"] == reported["memory_bytes"], contained_child
    assert contained_child["CPU"] == reported["cpu_seconds"], contained_child
    for key in ("NOFILE", "NPROC", "FSIZE", "AS", "CPU"):
        assert bare_child[key] != contained_child[key], (
            key, bare_child, contained_child
        )


@needs_containment
def test_the_contained_worker_environment_reaches_the_child_scrubbed(monkeypatch):
    """The allowlist is pinned on a REAL child's `os.environ`, not on the dict.

    `test_worker_environment_is_a_fixed_allowlist` asserts what
    `_contained_environment` returns. That is a claim about what the child WILL
    get; this reads what a child actually got, from the `env=` of the real
    launch, and the unprefixed arm shows the same secrets are visible when the
    scrub is not applied.
    """

    monkeypatch.setenv("OLLAMA_API_KEY", "secret-that-must-not-leak")
    monkeypatch.setenv("DEEPREASON_RESEARCH_ALLOWLIST", "example.com")

    seen: list[dict | None] = []
    real_popen = subprocess.Popen

    def recording_popen(command, *args, **kwargs):
        seen.append(kwargs.get("env"))
        return real_popen(command, *args, **kwargs)

    monkeypatch.setattr(contained_module.subprocess, "Popen", recording_popen)
    result, _ = _contained("def simulate(inputs, rng):\n    return {'value': 1}\n")
    assert result.verdict == "pass", result.trace
    assert seen, "the contained backend launched no subprocess"
    # A launch that passes no `env=` inherits the parent's whole environment,
    # and the scrub is then perfect and unused: the allowlist test still passes
    # while the child sees every secret.
    assert seen[0], "the launch passed no environment; the worker inherited ours"

    observed = _observed_environment(dict(seen[0]))
    inherited = _observed_environment(None)
    assert "OLLAMA_API_KEY" in inherited, "the arm that proves the probe can see it"
    assert "OLLAMA_API_KEY" not in observed, observed
    assert not [
        key for key in observed if "DEEPREASON" in key or "KEY" in key
    ], observed


def test_the_code_testing_worker_environment_reaches_the_child_scrubbed(monkeypatch):
    """`oracle_sandbox._worker_environment` had no test anywhere in `tests/`.

    The code-testing channel is ON by default, so its scrub is the one a run is
    most likely to depend on. Same two arms as the contained case.
    """

    from deepreason import oracle_sandbox

    monkeypatch.setenv("OLLAMA_API_KEY", "secret-that-must-not-leak")
    monkeypatch.setenv("DEEPREASON_RESEARCH_ALLOWLIST", "example.com")

    observed = _observed_environment(oracle_sandbox._worker_environment())
    inherited = _observed_environment(None)
    assert "OLLAMA_API_KEY" in inherited, "the arm that proves the probe can see it"
    assert "OLLAMA_API_KEY" not in observed, observed
    assert not [
        key for key in observed if "DEEPREASON" in key or "KEY" in key
    ], observed


def test_worker_resource_limits_fail_closed(monkeypatch):
    """Regression: `_apply_worker_limits` swallowed every setrlimit failure, so
    a host that refused a limit got an UNLIMITED worker and said nothing."""

    from deepreason import oracle_sandbox

    def refuse(_kind, _requested):
        raise OSError("rlimit refused")

    monkeypatch.setattr(oracle_sandbox, "_bounded_limit", refuse, raising=False)

    import resource

    def refusing_setrlimit(*_args, **_kwargs):
        raise OSError("rlimit refused")

    monkeypatch.setattr(resource, "setrlimit", refusing_setrlimit)
    with pytest.raises(OSError):
        oracle_sandbox._apply_worker_limits(2)
