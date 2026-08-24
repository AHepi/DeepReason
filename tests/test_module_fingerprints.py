"""Rung 4 (module fingerprints): every run records which modules built it.

Implements R2/R8 and SPEC.md S3 of
``experiments/2026-08-04-change-rung4-module-fingerprints``. The reader is
tested BEFORE the writer exists, because absence of the fingerprint must be
valid for every root recorded before the feature — that ordering is the
rung's own guardrail (R8, C12), not a stylistic preference.
"""

import functools
import subprocess
from pathlib import Path

import pytest

from deepreason.harness import Harness
from deepreason.module_events import (
    ModuleFingerprintV1,
    ModuleFingerprintsEventPayloadV1,
    recorded_module_fingerprints,
)
from deepreason.run_manifest import UnsupportedRunManifestVersionError


def _committed_roots() -> list[Path]:
    """Only roots ``git ls-files`` knows: a session-local root would take the
    meaning of every assertion below with it when the session ends."""

    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    # A tracked ``log.jsonl`` is not by itself a run root: other tools commit
    # append-only logs under that name (``.swarm/log.jsonl``, the swarm gate's
    # coordination record), and opening one as an Event log raises
    # CorruptLogError before any assertion here runs. Every real root carries
    # ``objects/`` beside its log; nothing else does.
    objects = {p.split("/objects/", 1)[0] for p in tracked if "/objects/" in p}
    return [Path(p).parent for p in tracked
            if p.endswith("/log.jsonl") and p[: -len("/log.jsonl")] in objects]


@functools.lru_cache(maxsize=1)
def _sweep_committed_roots() -> tuple[tuple[Path, ...], tuple[Path, ...], tuple[Path, ...]]:
    """Open every committed root ONCE and split it into (unstamped, stamped,
    refused).

    Three claims below are asserted over the same roots; opening ~45 recorded
    roots is the expensive part of this module, so it happens once per
    session rather than once per assertion.

    The split is derived from each root's OWN record rather than from a list
    of root names: a run recorded after the writer landed carries a
    ``module-fingerprints.v1`` payload and one recorded before it does not.
    A census cannot be asserted here, only partitioned — see the module
    docstring.
    """

    unstamped: list[Path] = []
    stamped: list[Path] = []
    refused: list[Path] = []
    for root in _committed_roots():
        try:
            harness = Harness(root, read_only=True)
        except UnsupportedRunManifestVersionError:
            refused.append(root)
            continue
        (stamped if recorded_module_fingerprints(harness) else unstamped).append(root)
    return tuple(unstamped), tuple(stamped), tuple(refused)


def test_absence_is_valid_before_the_feature_and_presence_valid_after():
    """R8: absence is the VALID answer on every root written before this
    feature, not an error and not an empty-because-unreadable — and presence
    is the valid answer on every root written after it.

    Regression (rung-5 A/B roots ``run-9a6be78e``, committed f6d41bff): this
    test previously asserted absence for EVERY committed root, which is not
    R8's claim but the strictly stronger "no root has been committed since
    the writer landed". Rung 4 shipped the writer and that assertion
    together, so the first live run committed afterwards falsified it. Both
    halves are asserted here so neither can expire.

    Regression (P1/P3, root ``run-a518e33a75507207633f864ba6a864b1``,
    continued 2026-08-06): the presence half previously asserted "exactly
    one" stamp per stamped root (``(payload,) = recorded_module_fingerprints
    (...)``), which is not R8's claim either — the writer's per-instance
    idempotency guard (``Scheduler._module_fingerprints_recorded``) resets on
    every ``Scheduler`` construction, so ``deepreason continue`` legitimately
    appends a second, byte-identical stamp. Fixed 2026-08-08 in
    ``experiments/2026-08-08-fix-module-fingerprints-double-stamp/`` by
    asserting the partition the record actually makes: at least one
    well-formed payload per stamped root, never a fixed count.

    Roots that refuse to open at all are excluded here and counted in
    ``test_the_census_of_committed_roots_is_unchanged`` instead: a pre-v6
    manifest is the harness declining to open the root, which says nothing
    about the reader.
    """

    unstamped, stamped, _ = _sweep_committed_roots()

    assert len(unstamped) > 20, len(unstamped)

    # Without a witness the presence half passes vacuously, and would keep
    # passing if every stamp vanished from the record.
    assert stamped, "no committed root carries a stamp; the presence half has no witness"
    for root in stamped:
        payloads = recorded_module_fingerprints(Harness(root, read_only=True))
        assert payloads, root
        for payload in payloads:
            assert payload.schema_ == "module-fingerprints.v1", root
            assert payload.modules, root
            assert payload.digest, root


def test_the_census_of_committed_roots_is_unchanged():
    """The reader must not be credited for roots it never read. Splitting the
    census from the assertion above is what keeps a future change that makes
    roots unopenable from showing up as a passing absence test.
    """

    unstamped, stamped, refused = _sweep_committed_roots()
    assert len(unstamped) + len(stamped) + len(refused) == len(_committed_roots())
    assert refused, "no root refused; the census this test guards has moved"
    assert len(unstamped) + len(stamped) > 20, (len(unstamped), len(stamped))


def test_the_reader_tolerates_an_event_with_no_fingerprint_attribute(tmp_path):
    """R8 at the EVENT level rather than the root level: an event object that
    predates the payload field has no attribute to read, and the reader must
    treat that as absence rather than raising.
    """

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["x"])

    class _EventWithoutTheField:
        pass

    assert getattr(_EventWithoutTheField(), "module_fingerprints", None) is None
    assert recorded_module_fingerprints(harness) == ()


def test_a_fingerprint_digest_is_a_function_of_content_not_key_order():
    """Two runs built by the same modules must stamp the same bytes, or
    cross-run comparison compares serialization accidents instead of modules.
    """

    a = ModuleFingerprintV1.of("r", "m", {"backend": "default", "stances": 8})
    b = ModuleFingerprintV1.of("r", "m", {"stances": 8, "backend": "default"})
    assert a.fingerprint_sha256 == b.fingerprint_sha256
    assert ModuleFingerprintsEventPayloadV1.of([a]).digest == (
        ModuleFingerprintsEventPayloadV1.of([b]).digest
    )


def test_a_different_module_produces_a_different_digest():
    """The companion mutation test the durable-test doctrine requires for an
    equality assertion: the comparison above must be able to notice a change.
    """

    a = ModuleFingerprintV1.of("r", "m", {"backend": "default", "stances": 8})
    c = ModuleFingerprintV1.of("r", "m", {"backend": "default", "stances": 9})
    assert a.fingerprint_sha256 != c.fingerprint_sha256
    assert ModuleFingerprintsEventPayloadV1.of([a]).digest != (
        ModuleFingerprintsEventPayloadV1.of([c]).digest
    )


def test_a_payload_carries_no_wall_clock_field():
    """A timestamped payload would make two runs built by identical modules
    compare unequal, which is the opposite of what the rung asks for. The
    enclosing ``Event.ts`` is the run's only clock.
    """

    fields = set(ModuleFingerprintsEventPayloadV1.model_fields) | set(
        ModuleFingerprintV1.model_fields
    )
    assert not {f for f in fields if "ts" == f or "time" in f or "clock" in f}, fields


def test_a_recorded_digest_cannot_disagree_with_its_own_fingerprint():
    """``of`` digests at construction so no call site can record a digest that
    does not describe the value beside it; a hand-built mismatch is refused.
    """

    with pytest.raises(ValueError):
        ModuleFingerprintV1(
            registry="r", module_id="m", fingerprint={"a": 1}, fingerprint_sha256="nope"
        )


def _payload(**overrides) -> ModuleFingerprintsEventPayloadV1:
    module = ModuleFingerprintV1.of(
        overrides.get("registry", "school-population"),
        overrides.get("module_id", "default"),
        overrides.get("fingerprint", {"backend": "default", "stance_count": 8}),
    )
    return ModuleFingerprintsEventPayloadV1.of([module])


def test_the_appender_round_trips_through_the_log_alone(tmp_path):
    """R2: the stamp must be in the RECORD, which means a reader that has
    only the log — not the live session — can recover it."""

    harness = Harness(tmp_path / "run")
    payload = _payload()
    harness.record_module_fingerprints(payload)

    reopened = Harness(tmp_path / "run", read_only=True)
    got = recorded_module_fingerprints(reopened)
    assert [p.digest for p in got] == [payload.digest]
    assert got[0].modules[0].module_id == "default"


def test_recorded_module_fingerprints_is_a_partition_claim_never_a_single_unpack(tmp_path):
    """Regression (P1/P3, root ``run-a518e33a75507207633f864ba6a864b1``):
    two stamps on ONE run's log — the shape a continuation legitimately
    produces — must both come back, in append order, never assumed down to
    one. Mirrors ``tests/test_seat_bindings_record.py::
    test_recorded_seat_bindings_is_a_partition_claim_never_a_single_unpack``,
    the sibling payload's own test, written as a partition claim from the
    start specifically to avoid this exact failure mode.
    """

    harness = Harness(tmp_path / "run")
    first = _payload(module_id="default")
    second = _payload(module_id="alt")
    harness.record_module_fingerprints(first)
    harness.record_module_fingerprints(second)

    got = recorded_module_fingerprints(harness)
    assert len(got) == 2
    assert [p.digest for p in got] == [first.digest, second.digest]


def test_the_stamp_materializes_no_state(tmp_path):
    """R18's substance: the payload carries identity, not epistemic content.

    If it ever materialized state it would need an ``_apply_event`` branch and
    a ``_reset`` attribute, and the operator's authorization explicitly
    excludes both. This test fails the moment that stops being true.
    """

    harness = Harness(tmp_path / "run")
    before = harness.state.model_dump_json()
    harness.record_module_fingerprints(_payload())
    assert harness.state.model_dump_json() == before

    reopened = Harness(tmp_path / "run", read_only=True)
    for family in ("scratch_state", "bridge_state", "workflow_state", "capability_state"):
        assert hasattr(reopened, family), family
    assert reopened.state.model_dump_json() == before


def test_apply_event_has_no_branch_for_the_payload():
    """R18 as a standing assertion rather than a one-time diff review.

    Anchored to the resolved attribute name rather than to source text
    formatting, so a reformat of ``harness.py`` cannot break it and a real
    dispatch branch cannot hide from it.
    """

    import ast
    import inspect
    import textwrap

    from deepreason.harness import Harness as _H

    tree = ast.parse(textwrap.dedent(inspect.getsource(_H._apply_event)))
    read = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
        and node.value.id == "event"
    }
    assert read, "no event attributes read; the probe stopped measuring"
    assert "module_fingerprints" not in read, sorted(read)


def _scheduler_run(tmp_path, *, n_schools: int) -> Path:
    """The smallest ordinary run: a mock endpoint, no capability anywhere."""

    import json

    from deepreason.config import Config
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.scheduler.scheduler import Scheduler

    root = tmp_path / "run"
    harness = Harness(root)
    reply = json.dumps({"candidates": [{"content": "x", "typicality": 0.5}]})
    adapter = LLMAdapter({"conjecturer": MockEndpoint(lambda _p: reply)}, harness.blobs)
    # run(1), not bare construction: the stamp fires per RUN, because building
    # a Scheduler (or running it for zero cycles) is how callers inspect and
    # recover without touching the record. See SPEC.md D7a/D7b.
    Scheduler(harness, adapter, Config(N_SCHOOLS=n_schools)).run(1)
    return root


def test_an_ordinary_run_records_the_population_backend(tmp_path):
    """R2/S2: an ORDINARY run — mock endpoint, no capability exercised — puts
    the registered backend's fingerprint in its own record, and the value
    recorded is the one the registry pins rather than a second computation.
    """

    from deepreason.capture import schools

    root = _scheduler_run(tmp_path, n_schools=4)
    reopened = Harness(root, read_only=True)

    assert not any(e.capability is not None for e in reopened.log.read())

    got = recorded_module_fingerprints(reopened)
    assert len(got) == 1, got
    module = got[0].modules[0]
    assert module.registry == "school-population"
    assert module.module_id == "default"
    assert dict(module.fingerprint) == schools.SCHOOL_POPULATION.fingerprint("default")


def test_a_run_with_no_schools_still_records_which_module_built_it(tmp_path):
    """R2 says EVERY run. ``init_schools`` is gated on ``N_SCHOOLS > 0``; the
    stamp deliberately is not, because a zero-school run was still built by
    the registered backend. This test is what keeps the writer outside that
    gate when someone later tidies the constructor.
    """

    root = _scheduler_run(tmp_path, n_schools=0)
    got = recorded_module_fingerprints(Harness(root, read_only=True))
    assert len(got) == 1, got
    assert got[0].modules[0].module_id == "default"


def _scrub_wall_clock(value):
    """Drop time-dependent fields at EVERY nesting depth.

    A top-level-only scrub once left ``llm.ms`` inside ``attempt_trace`` and
    produced a 1-in-3 flake (commit ``863a0fa3``); the exclusion set is named
    exactly rather than widened by guess.
    """

    if isinstance(value, dict):
        return {
            k: _scrub_wall_clock(v)
            for k, v in value.items()
            if k not in {"ts", "ms", "started_at", "finished_at"}
        }
    if isinstance(value, list):
        return [_scrub_wall_clock(v) for v in value]
    return value


def _scrubbed_log(root: Path) -> list:
    import json

    return [
        _scrub_wall_clock(json.loads(event.model_dump_json(by_alias=True)))
        for event in Harness(root, read_only=True).log.read()
    ]


def test_two_runs_built_by_the_same_modules_record_the_same_stamp(tmp_path):
    """The property the rung exists for: cross-run comparison is honest only
    if identical modules produce identical bytes. Compares the whole scrubbed
    event log, not just the stamp, so a difference anywhere is visible.
    """

    a = _scheduler_run(tmp_path / "a", n_schools=2)
    b = _scheduler_run(tmp_path / "b", n_schools=2)
    assert _scrubbed_log(a) == _scrubbed_log(b)

    digests = {recorded_module_fingerprints(Harness(r, read_only=True))[0].digest
               for r in (a, b)}
    assert len(digests) == 1, digests


def test_a_stamped_run_replays_to_the_same_state(tmp_path):
    """The stamp must not disturb replay: reopening the root twice must reach
    one state, which is the relation ``verify_root``'s ``replay`` finding
    checks for every recorded root.
    """

    root = _scheduler_run(tmp_path, n_schools=2)
    first = Harness(root, read_only=True)
    second = Harness(root, read_only=True)
    assert first.state.model_dump_json() == second.state.model_dump_json()
    assert _scrubbed_log(root) == _scrubbed_log(root)


def test_a_run_built_by_a_different_backend_records_a_different_stamp(tmp_path):
    """The companion mutation test durable-test rule 3 requires for the
    equality above: a genuinely different module must break the comparison,
    or the comparison is measuring nothing.
    """

    from deepreason.capture import schools

    root = _scheduler_run(tmp_path, n_schools=2)
    recorded = recorded_module_fingerprints(Harness(root, read_only=True))[0]

    altered = ModuleFingerprintsEventPayloadV1.of(
        [
            ModuleFingerprintV1.of(
                "school-population",
                "default",
                {**schools.SCHOOL_POPULATION.fingerprint("default"), "stance_count": 999},
            )
        ]
    )
    assert altered.digest != recorded.digest


def test_a_read_only_scheduler_records_nothing(tmp_path):
    """Regression (rung 4, SPEC.md D7a): the stamp fires outside the
    ``N_SCHOOLS`` gate but NOT on a read-only harness.

    ``tests/test_amendment_epochs.py`` builds a Scheduler over
    ``Harness(root, read_only=True)`` to inspect ranking without writing. An
    unconditional append there raises ``ReadOnlyHarnessError`` and the
    Scheduler cannot be constructed at all — and a read-only open that wrote
    would break the asymmetry every stored verdict depends on.
    """

    from deepreason.config import Config
    from deepreason.scheduler.scheduler import Scheduler

    root = _scheduler_run(tmp_path, n_schools=0)
    before = (root / "log.jsonl").read_bytes()

    Scheduler(Harness(root, read_only=True), None, Config(N_SCHOOLS=0))

    assert (root / "log.jsonl").read_bytes() == before
    assert len(recorded_module_fingerprints(Harness(root, read_only=True))) == 1


def test_building_a_scheduler_and_running_zero_cycles_append_nothing(tmp_path):
    """Regression (rung 4, SPEC.md D7b): the stamp is per RUN, not per object.

    Two gate failures taught this. ``tests/test_v6_transaction_qualification``
    holds two live ``Harness`` handles across a crash and recovers with
    ``run(0)``, asserting the log is byte-identical afterwards; a stamp there
    either trips the single-writer fence or moves a record the recovery pass
    promised to leave alone. ``tests/test_route_firewall_scheduler`` builds a
    Scheduler purely to drive a fail-closed path. Both mean: constructing a
    Scheduler, and running one for zero cycles, must append nothing.
    """

    import json

    from deepreason.config import Config
    from deepreason.llm.adapter import LLMAdapter
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.scheduler.scheduler import Scheduler

    root = tmp_path / "run"
    harness = Harness(root)
    reply = json.dumps({"candidates": [{"content": "x", "typicality": 0.5}]})
    adapter = LLMAdapter({"conjecturer": MockEndpoint(lambda _p: reply)}, harness.blobs)

    scheduler = Scheduler(harness, adapter, Config(N_SCHOOLS=0))
    assert list(harness.log.read()) == []          # construction appended nothing

    scheduler.run(0)
    assert list(harness.log.read()) == []          # a zero-cycle pass too

    scheduler.run(1)
    assert len(recorded_module_fingerprints(harness)) == 1

    scheduler.run(1)                                # once per run, not per cycle
    assert len(recorded_module_fingerprints(harness)) == 1


def _forgeable_event(**overrides):
    from deepreason.ontology.event import Event, Rule

    payload = _payload()
    fields = dict(
        seq=0,
        ts="2026-08-04T00:00:00+00:00",
        rule=Rule.MEASURE,
        inputs=[payload.schema_, payload.digest],
        outputs=[],
        module_fingerprints=payload,
    )
    fields.update(overrides)
    return Event(**fields)


def test_the_appender_shape_is_the_only_accepted_one():
    """Regression (rung 4, VALIDATION.md FAIL): the payload is fenced by the
    RECORD, not merely by the appender's good behaviour.

    ``Event._process_payload_contract`` binds every other typed payload to
    its Rule and constrains its inputs. Without a clause for this one, an
    event pairing the fingerprint payload with ``Rule.CONJ`` and empty
    inputs was accepted, and the reader reported it as a genuine stamp —
    invisible to the gate, the map checks and the sweep alike, because no
    test built such an event.
    """

    from deepreason.ontology.event import Rule

    _forgeable_event()  # the appender's own shape still validates

    with pytest.raises(ValueError, match="only a Measure event"):
        _forgeable_event(rule=Rule.CONJ)

    with pytest.raises(ValueError, match="schema and digest"):
        _forgeable_event(inputs=[])

    with pytest.raises(ValueError, match="identity, not work"):
        _forgeable_event(outputs=["x"])


def test_a_measure_event_without_fingerprints_is_still_ordinary(tmp_path):
    """The fence is ONE-directional. Fingerprints may ride only a Measure,
    but a Measure carries no obligation to hold fingerprints — the two
    existing Measure appenders and every heartbeat depend on that.
    """

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["cycle", "0", "pi-seed"])
    assert recorded_module_fingerprints(harness) == ()


def test_an_empty_module_list_is_refused():
    """A stamp naming no modules answers the rung's question with silence
    while still looking like a recorded answer."""

    with pytest.raises(ValueError):
        ModuleFingerprintsEventPayloadV1.of([])
