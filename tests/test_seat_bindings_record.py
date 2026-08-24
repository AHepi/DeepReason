"""Rung S5 (seats in the typed record): every run records which
provider/model sat in which role group.

Implements R2/R4/R5/R6 and SPEC.md Items S2-S7 of
``experiments/2026-08-07-change-seats-in-record-s5``. The reader is
tested BEFORE the writer exists, because absence of the stamp must be
valid for every root recorded before the feature -- that ordering is the
rung's own guardrail (R4, C4), mirroring rung 4's own guardrail.

Regression discipline carried forward from rung 4 (C5's trap in
``DR-SEAM-harness-x-verification``: "a census check expires; a
partition check does not" -- ``tests/test_module_fingerprints.py``
asserted NO committed root carried a stamp, which was true only until
the first run recorded after that rung's writer landed): no assertion
below claims a permanent census over committed roots. The absence claim
below is scoped to what the reader itself promises -- it does not raise
and tolerates an event with no attribute -- never to "no root has ever
been stamped", which this rung's own future live runs will falsify.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from deepreason.application.models import RunBudgetIntentV1
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.preparation import (
    RunPreparationRequestV1,
    RunPreparationService,
    build_preparation_manifest,
)
from deepreason.provider_profile import ProviderProfileV1, write_provider_profile
from deepreason.run_manifest import UnsupportedRunManifestVersionError
from deepreason.scheduler.scheduler import Scheduler
from deepreason.seat_bindings import seat_bindings_path, write_seat_bindings
from deepreason.seat_events import (
    SeatBindingsEventPayloadV1,
    SeatBindingV1,
    recorded_seat_bindings,
    seat_bindings_for_run,
)


def _profile(**updates):
    values = {
        "provider": "openai",
        "endpoint": "https://api.example.com/v1",
        "model_id": "model-default",
        "family": "family-a",
        "context_window_tokens": 262144,
        "maximum_completion_tokens": 4096,
        "credential_env": "DEEPREASON_TEST_KEY",
    }
    values.update(updates)
    return ProviderProfileV1.create(**values)


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


def test_recorded_seat_bindings_is_absent_on_a_fresh_harness(tmp_path):
    """SPEC.md Item S2's own accept criterion: a fresh run with no
    seat-bindings event reads as absent, not as an error."""

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["x"])
    assert recorded_seat_bindings(harness) == ()


def test_the_reader_tolerates_every_currently_committed_root():
    """The reader must never raise on a root it can open, whatever that
    root's own history is. Unlike a claim about WHICH roots carry a
    stamp (a census, C5's trap), "the reader does not crash" cannot ever
    be falsified by a future run stamping one -- it stays true forever,
    which is what makes it safe to assert here permanently.
    """

    roots = _committed_roots()
    opened = 0
    refused = 0
    for root in roots:
        try:
            harness = Harness(root, read_only=True)
        except UnsupportedRunManifestVersionError:
            refused += 1
            continue
        assert isinstance(recorded_seat_bindings(harness), tuple), root
        opened += 1
    assert opened + refused == len(roots)
    assert opened > 20, opened  # today's floor; not an upper bound


def test_the_reader_tolerates_an_event_with_no_seat_bindings_attribute(tmp_path):
    """R4 at the EVENT level rather than the root level: an event object
    that predates the payload field has no attribute to read, and the
    reader must treat that as absence rather than raising.
    """

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["x"])

    class _EventWithoutTheField:
        pass

    assert getattr(_EventWithoutTheField(), "seat_bindings", None) is None
    assert recorded_seat_bindings(harness) == ()


def test_the_reader_extracts_a_stamp_the_event_already_carries():
    """The reader's own contract -- read whatever ``event.seat_bindings``
    holds -- does not depend on ``Event.seat_bindings`` existing as a
    declared model field yet (step 7). A bare object exercises the
    reader in isolation from the payload-field step that comes later.
    """

    binding = SeatBindingV1.of(
        "coder",
        type("Profile", (), {"provider": "generic", "model_id": "m", "profile_digest": "d"})(),
    )
    payload = SeatBindingsEventPayloadV1.of([binding])

    class _EventWithTheField:
        seat_bindings = payload

    harness_log = [_EventWithTheField()]

    class _FakeLog:
        def read(self):
            return harness_log

    class _FakeHarness:
        log = _FakeLog()

    assert recorded_seat_bindings(_FakeHarness()) == (payload,)


def test_seat_bindings_for_run_projects_default_when_no_binding_exists(tmp_path):
    """SPEC.md Item S3's own accept criterion: a manifest with no seat
    bindings (every role shares one uniform route -- Rung S1's own
    census) projects exactly one synthesized "default" entry naming the
    manifest's own provider/model_id, with no stored event required.
    """

    profile = _profile()
    manifest = build_preparation_manifest(
        profile,
        question="Why is the sky blue?",
        compiled_at=datetime(2026, 8, 7, tzinfo=timezone.utc).isoformat(),
    )
    harness = Harness(tmp_path / "run")

    projected = seat_bindings_for_run(harness, manifest)

    assert len(projected) == 1
    assert projected[0].group == "default"
    assert projected[0].provider == profile.provider
    assert projected[0].model_id == profile.model_id
    assert recorded_seat_bindings(harness) == ()


def _seat_payload(**overrides) -> SeatBindingsEventPayloadV1:
    binding = SeatBindingV1.of(
        overrides.get("group", "coder"), _profile(model_id="model-bound")
    )
    return SeatBindingsEventPayloadV1.of([binding])


def _forgeable_event(**overrides):
    from deepreason.ontology.event import Event, Rule

    payload = _seat_payload()
    fields = dict(
        seq=0,
        ts="2026-08-07T00:00:00+00:00",
        rule=Rule.MEASURE,
        inputs=[payload.schema_, payload.digest],
        outputs=[],
        seat_bindings=payload,
    )
    fields.update(overrides)
    return Event(**fields)


def test_the_seat_bindings_contract_fence_is_the_only_accepted_shape():
    """SPEC.md Item S4: the payload is fenced by the RECORD, not merely
    by the appender's good behaviour, mirroring
    ``module_fingerprints``'s own already-tested fence exactly.
    """

    from deepreason.ontology.event import Rule

    _forgeable_event()  # the appender's own shape still validates

    with pytest.raises(ValueError, match="only a Measure event"):
        _forgeable_event(rule=Rule.CONJ)

    with pytest.raises(ValueError, match="schema and digest"):
        _forgeable_event(inputs=[])

    with pytest.raises(ValueError, match="identity, not work"):
        _forgeable_event(outputs=["x"])


def test_a_measure_event_without_seat_bindings_is_still_ordinary(tmp_path):
    """The fence is ONE-directional: seat bindings may ride only a
    Measure event, but a Measure carries no obligation to hold one."""

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["cycle", "0", "pi-seed"])
    assert recorded_seat_bindings(harness) == ()


def test_the_appender_round_trips_through_the_log_alone(tmp_path):
    """R2: the stamp must be in the RECORD, which means a reader that has
    only the log -- not the live session -- can recover it."""

    harness = Harness(tmp_path / "run")
    payload = _seat_payload()
    harness.record_seat_bindings(payload)

    reopened = Harness(tmp_path / "run", read_only=True)
    got = recorded_seat_bindings(reopened)
    assert [p.digest for p in got] == [payload.digest]
    assert got[0].bindings[0].group == "coder"


def test_recorded_seat_bindings_is_a_partition_claim_never_a_single_unpack(tmp_path):
    """Q5/A5: two stamps on ONE run's log -- the shape a continuation
    could legitimately produce -- must both come back, in append order,
    never assumed down to one.

    Regression discipline (P1/P3, this program's own recorded pre-
    existing defect in ``tests/test_module_fingerprints.py``): that
    reader's own test used ``(payload,) = recorded_module_fingerprints(
    ...)``, which broke the moment a continued root carried two stamps.
    This rung's own reader test is written as a partition claim from the
    start, so it manufactures no new instance of that failure mode.
    """

    harness = Harness(tmp_path / "run")
    first = _seat_payload(group="coder")
    second = _seat_payload(group="scratch")
    harness.record_seat_bindings(first)
    harness.record_seat_bindings(second)

    got = recorded_seat_bindings(harness)
    assert len(got) == 2
    assert [p.digest for p in got] == [first.digest, second.digest]


def _qualified_report(manifest):
    return run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}",
            first_pass_valid=True,
            eventual_valid=True,
            repair_count=0,
            semantic_admission=True,
        ),
    )


def _prepared_root(tmp_path, *, seat_bindings=None) -> Path:
    """A `prepare()`d root -- the smallest ordinary preparation, matching
    Rung S4's own `MockEndpoint`/fake-manifest pattern. `seat_bindings`,
    when given, is `{group: ProviderProfileV1}` to bind before preparing.
    """

    profile = _profile()
    profile_path = write_provider_profile(profile, tmp_path / "profile.yaml")
    environ = {
        "DEEPREASON_TEST_KEY": "not-a-real-secret",
        "DEEPREASON_HOME": str(tmp_path / "seats-home"),
    }
    if seat_bindings:
        write_seat_bindings(
            {group: str(write_provider_profile(p, tmp_path / f"{group}.yaml"))
             for group, p in seat_bindings.items()},
            seat_bindings_path(environ=environ),
        )
    service = RunPreparationService(
        runs_dir=tmp_path / "runs",
        qualification_cache_dir=tmp_path / "qualification-cache",
        environ=environ,
        qualification_executor=_qualified_report,
    )
    request = RunPreparationRequestV1(
        question="Why is the sky blue?",
        budget=RunBudgetIntentV1(cycles=1, token_budget=2000),
        profile_path=str(profile_path),
    )
    prepared = service.prepare(request)
    return Path(prepared.root)


def _run_one_cycle(root: Path) -> None:
    """The smallest ordinary run over an already-prepared root: a mock
    endpoint, no capability anywhere, mirroring
    ``tests/test_module_fingerprints.py``'s own ``_scheduler_run``."""

    harness = Harness(root)
    reply = json.dumps({"candidates": [{"content": "x", "typicality": 0.5}]})
    adapter = LLMAdapter({"conjecturer": MockEndpoint(lambda _p: reply)}, harness.blobs)
    Scheduler(harness, adapter, Config(N_SCHOOLS=0)).run(1)


def test_a_two_profile_home_stamps_both_bound_groups_in_one_run(tmp_path):
    """SPEC.md Item S7's own accept criterion (R13): a two-profile home's
    run shows the stamp naming both bindings -- exactly one
    ``seat-bindings.v1`` event, one entry per bound group."""

    bound_coder = _profile(model_id="model-coder")
    bound_scratch = _profile(model_id="model-scratch")
    root = _prepared_root(
        tmp_path, seat_bindings={"coder": bound_coder, "scratch": bound_scratch}
    )

    _run_one_cycle(root)

    got = recorded_seat_bindings(Harness(root, read_only=True))
    assert len(got) == 1, got
    assert {b.group for b in got[0].bindings} == {"coder", "scratch"}


def test_a_default_home_stamps_nothing_and_projects_the_single_seat(tmp_path):
    """SPEC.md Item S7's own accept criterion (R14): a default home's run
    shows the single-seat stamp -- no stored event, and
    ``seat_bindings_for_run`` projects exactly one "default" entry."""

    root = _prepared_root(tmp_path)

    _run_one_cycle(root)

    harness = Harness(root, read_only=True)
    assert recorded_seat_bindings(harness) == ()

    from deepreason.run_manifest import load_run_manifest

    manifest = load_run_manifest(root / "run-manifest.json")
    projected = seat_bindings_for_run(harness, manifest)
    assert len(projected) == 1
    assert projected[0].group == "default"
