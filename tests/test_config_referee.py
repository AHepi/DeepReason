"""The config referee: standard views in, cited verdicts or typed rejections out."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deepreason.canonical import canonical_json
from deepreason.ontology import Rule
from deepreason.ontology.event import Event
from deepreason.referee import (
    CONFIG_REFEREE_RESPONSE_MENU,
    ConfigRefereeError,
    ConfigRefereePolicyV1,
    ConfigRefereeVerdictV1,
    build_config_review_view,
    latest_config_critique,
    parse_config_referee_verdict,
    record_config_critique,
    record_rejected_config_critique,
    validate_config_referee_verdict,
)

NARROW = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "live_research_2026-07-29"
    / "narrow"
    / "runs"
    / "run-7d8723fbe8626c71db880826c244d332"
)


def _event(seq: int, signal: str, *inputs: str, rule: Rule = Rule.MEASURE) -> Event:
    return Event(
        seq=seq,
        ts="2026-07-29T00:00:00Z",
        rule=rule,
        inputs=[signal, *inputs],
    )


class _Blobs(dict):
    def put(self, data: bytes) -> str:
        import hashlib

        ref = hashlib.sha256(data).hexdigest()
        self[ref] = data
        return ref

    def get(self, ref: str) -> bytes:
        return self[ref]


class _Log:
    def __init__(self, events):
        self.events = list(events)

    def read(self):
        return list(self.events)


class _FakeHarness:
    def __init__(self, events, root: Path):
        self.log = _Log(events)
        self.root = root
        self.blobs = _Blobs()
        self.measures = []

    def record_measure(self, *, inputs):
        self.measures.append(tuple(inputs))
        event = _event(
            (self.log.events[-1].seq + 1) if self.log.events else 0,
            inputs[0],
            *inputs[1:],
        )
        self.log.events.append(event)
        return event


def _window_events():
    return [
        _event(0, "cycle", "1", "pi-example"),
        _event(1, "research-allowance:2/3", "waste:1/2", "refusal-streak:0"),
        _event(2, "research-fetch:FETCHED", "docs.python.org", "requests:1/6"),
        _event(3, "evidence-citation:EVIDENCE_REF_UNKNOWN_BLOCK", "sha256:aa", "art-1"),
        _event(4, "unrelated-signal", "ignored"),
        _event(5, "gate:duplicate", "art-2"),
        _event(6, "assembled", "art-3", rule=Rule.MEASURE),
    ]


class _Manifest:
    inquiry_capability_policy = None


def test_policy_binds_authority_only_when_enabled():
    disabled = ConfigRefereePolicyV1()
    assert disabled.enabled is False
    with pytest.raises(ValueError, match="cannot bind authority"):
        ConfigRefereePolicyV1(window_events=64)
    with pytest.raises(ValueError, match="finite positive bounds"):
        ConfigRefereePolicyV1(enabled=True, cadence_cycles=8, window_events=64)
    enabled = ConfigRefereePolicyV1(
        enabled=True, cadence_cycles=8, window_events=512, maximum_view_bytes=65_536
    )
    assert enabled.digest != disabled.digest


def test_view_is_a_content_blind_window_of_registered_signals(tmp_path):
    harness = _FakeHarness(_window_events(), tmp_path)
    (tmp_path / "TOKEN_ACCOUNTING.json").write_text('{"total": 123}', encoding="utf-8")
    (tmp_path / "FINDINGS.md").write_text("# Findings\nBody.", encoding="utf-8")
    view = build_config_review_view(
        harness, _Manifest(), window_events=6, maximum_view_bytes=65_536
    )
    assert view.fence_seq == 6
    assert view.window_first_seq == 1  # seq 0 falls outside the trailing window
    signals = [item.signal for item in view.observations]
    # Registered families only; the unrelated and non-config measures never appear.
    assert signals == [
        "research-allowance:2/3",
        "research-fetch:FETCHED",
        "evidence-citation:EVIDENCE_REF_UNKNOWN_BLOCK",
        "gate:duplicate",
    ]
    assert view.citable_seqs == {1, 2, 3, 5}
    assert view.token_accounting_excerpt == '{"total": 123}'
    assert view.findings_excerpt.startswith("# Findings")
    assert view.dropped_observations == 0


def test_view_truncation_drops_oldest_and_counts_the_drop(tmp_path):
    harness = _FakeHarness(_window_events(), tmp_path)
    small = build_config_review_view(
        harness, _Manifest(), window_events=7, maximum_view_bytes=600
    )
    assert small.dropped_observations > 0
    full = build_config_review_view(
        harness, _Manifest(), window_events=7, maximum_view_bytes=65_536
    )
    kept = [item.seq for item in small.observations]
    # The retained observations are exactly the newest tail of the full set.
    assert kept == [item.seq for item in full.observations][len(full.observations) - len(kept):]
    assert len(canonical_json(small.model_dump(mode="json", by_alias=True))) <= 600


def test_verdict_requires_menu_coherence_and_unique_citations():
    assert set(CONFIG_REFEREE_RESPONSE_MENU) == {
        "no_change",
        "criticism_weighted_cycle",
        "research_allowance_step_tighten",
        "research_allowance_step_widen",
    }
    with pytest.raises(ValueError, match="no_change"):
        ConfigRefereeVerdictV1(
            verdict="config_effective",
            assessment="fine",
            cited_seqs=(1,),
            recommendation="criticism_weighted_cycle",
        )
    with pytest.raises(ValueError, match="no_change"):
        ConfigRefereeVerdictV1(
            verdict="config_mistuned",
            assessment="allowance never tightens",
            cited_seqs=(1,),
            recommendation="no_change",
        )
    with pytest.raises(ValueError, match="unique"):
        ConfigRefereeVerdictV1(
            verdict="config_mistuned",
            assessment="dup",
            cited_seqs=(1, 1),
            recommendation="research_allowance_step_tighten",
        )


def test_uncited_verdict_is_rejected_and_recorded_as_typed_refusal(tmp_path):
    harness = _FakeHarness(_window_events(), tmp_path)
    view = build_config_review_view(
        harness, _Manifest(), window_events=7, maximum_view_bytes=65_536
    )
    verdict = ConfigRefereeVerdictV1(
        verdict="config_mistuned",
        assessment="cites an observation the referee was never shown",
        cited_seqs=(4, 999),
        recommendation="research_allowance_step_tighten",
    )
    with pytest.raises(ConfigRefereeError, match="UNFOUNDED.*\\[4, 999\\]"):
        validate_config_referee_verdict(verdict, view)
    with pytest.raises(ConfigRefereeError):
        record_config_critique(harness, verdict, view)
    assert harness.measures == []  # a rejected verdict never records as advice
    record_rejected_config_critique(
        harness, ConfigRefereeError("CONFIG_REFEREE_VERDICT_UNFOUNDED: [4, 999]"), view
    )
    assert harness.measures[0][0] == "config-critique:REJECTED_UNFOUNDED"
    latest = latest_config_critique(harness)
    assert latest is not None
    assert latest["signal"] == "config-critique:REJECTED_UNFOUNDED"


def test_grounded_critique_records_citations_and_refs(tmp_path):
    harness = _FakeHarness(_window_events(), tmp_path)
    view = build_config_review_view(
        harness, _Manifest(), window_events=7, maximum_view_bytes=65_536
    )
    verdict = ConfigRefereeVerdictV1(
        verdict="config_mistuned",
        assessment=(
            "Every consumed source stays uncited (seq 1 waste:1/2) while "
            "fetches keep landing (seq 2); tighten the allowance step."
        ),
        cited_seqs=(1, 2),
        recommendation="research_allowance_step_tighten",
    )
    record_config_critique(harness, verdict, view)
    inputs = harness.measures[0]
    assert inputs[0] == "config-critique:config_mistuned"
    assert inputs[1] == "recommendation:research_allowance_step_tighten"
    assert inputs[2] == "cited:1,2"
    view_ref = inputs[3].removeprefix("view:")
    verdict_ref = inputs[4].removeprefix("verdict:")
    stored_view = json.loads(harness.blobs.get(view_ref))
    stored_verdict = json.loads(harness.blobs.get(verdict_ref))
    assert stored_view["schema"] == "config-review-view.v1"
    assert stored_verdict["recommendation"] == "research_allowance_step_tighten"
    # The critique itself becomes a citable observation for the next review.
    following = build_config_review_view(
        harness, _Manifest(), window_events=16, maximum_view_bytes=65_536
    )
    assert "config-critique:config_mistuned" in [
        item.signal for item in following.observations
    ]


def test_parse_is_strict_and_typed():
    verdict = parse_config_referee_verdict(
        json.dumps(
            {
                "schema": "config-referee-verdict.v1",
                "verdict": "config_effective",
                "assessment": "signals move with the record",
                "cited_seqs": [1],
                "recommendation": "no_change",
            }
        )
    )
    assert verdict.verdict == "config_effective"
    with pytest.raises(ConfigRefereeError, match="UNPARSEABLE"):
        parse_config_referee_verdict("not json")
    with pytest.raises(ConfigRefereeError, match="INVALID"):
        parse_config_referee_verdict(json.dumps({"verdict": "config_effective"}))


def _referee_manifest():
    from deepreason.capabilities.policy import (
        ConfigRefereePolicyV1 as PolicyRecord,
        InquiryCapabilityPolicyV1,
    )
    from deepreason.run_manifest import compile_run_manifest
    from tests.test_v6_nonconjecture_recovery import (
        STAMP,
        _config,
        _control,
        _criticism_policy,
    )

    config = _config()
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=_criticism_policy(),
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2",
            config_referee=PolicyRecord(
                enabled=True,
                cadence_cycles=4,
                window_events=256,
                maximum_view_bytes=65_536,
            ),
        ),
        run_input_digest="f" * 64,
    )
    return config, manifest


def _referee_provider_prefix(root, manifest, *, raw: bytes):
    from deepreason.harness import Harness
    from deepreason.referee import build_config_review_view
    from deepreason.workflow.models import WorkflowTaskKind
    from deepreason.workflow.transaction import ContextNamespace, VisibleContextItemV1
    from tests.test_v6_nonconjecture_recovery import _provider_prefix

    harness = Harness(root)
    harness.record_measure(inputs=["cycle", "1", "-"])
    harness.record_measure(
        inputs=["evidence-citation:EVIDENCE_REF_UNKNOWN_BLOCK", "sha256:aa", "art-1"]
    )
    policy = manifest.inquiry_capability_policy.config_referee
    view = build_config_review_view(
        harness,
        manifest,
        window_events=policy.window_events,
        maximum_view_bytes=policy.maximum_view_bytes,
    )
    view_ref = harness.blobs.put(
        canonical_json(view.model_dump(mode="json", by_alias=True))
    )
    payload = {
        "schema": "config-referee.semantic-task.v1",
        "critic_school_id": "school-1",
        "view_ref": view_ref,
        "fence_seq": view.fence_seq,
        "caller_trigger_ref": "config-referee-cycle:4",
    }
    item = VisibleContextItemV1(
        namespace=ContextNamespace.SOURCE,
        alias="SRC_001",
        object_ref=view_ref,
        content_sha256=view_ref,
        planned_bytes=64,
    )
    preparation, provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.CRITICISM,
        role="argumentative_critic",
        seat=1,
        contract_id="config-referee.v1",
        payload=payload,
        trigger_prefix="config-referee:",
        raw=raw,
        target_refs=(view_ref,),
        input_refs=(view_ref,),
        items=(item,),
    )
    return preparation, provider, view


def _critique_events(harness):
    return [
        event
        for event in harness.log.read()
        if event.inputs and str(event.inputs[0]).startswith("config-critique:")
    ]


def test_recovered_referee_verdict_records_critique_exactly_once(tmp_path):
    from deepreason.workflow.transaction_service import TokenMeter
    from deepreason.workflow.nonconjecture_recovery import (
        recover_nonconjecture_admission,
    )
    from tests.test_v6_nonconjecture_recovery import _recover

    config, manifest = _referee_manifest()
    root = tmp_path / "referee-grounded"
    raw = json.dumps(
        {
            "verdict": "config_mistuned",
            "assessment": "Citation failures at seq 1 show wasted evidence.",
            "cited_seqs": [1],
            "recommendation": "research_allowance_step_tighten",
        }
    ).encode("utf-8")
    _preparation, provider, view = _referee_provider_prefix(root, manifest, raw=raw)
    assert 1 in view.citable_seqs
    reopened, item, admission = _recover(root, manifest, provider)
    assert admission.outcome == "admitted"
    assert item.terminal.status == "completed"
    critiques = _critique_events(reopened)
    assert len(critiques) == 1
    assert critiques[0].inputs[0] == "config-critique:config_mistuned"
    assert critiques[0].inputs[1] == "recommendation:research_allowance_step_tighten"
    # Recovering again applies no second advice record.
    again = recover_nonconjecture_admission(
        reopened, manifest, TokenMeter(100_000), provider
    )
    assert again.id == admission.id
    assert len(_critique_events(reopened)) == 1


def test_recovered_unfounded_referee_verdict_is_a_typed_rejection(tmp_path):
    from tests.test_v6_nonconjecture_recovery import _recover

    config, manifest = _referee_manifest()
    root = tmp_path / "referee-unfounded"
    raw = json.dumps(
        {
            "verdict": "config_mistuned",
            "assessment": "Cites an observation the referee was never shown.",
            "cited_seqs": [999],
            "recommendation": "criticism_weighted_cycle",
        }
    ).encode("utf-8")
    _preparation, provider, _view = _referee_provider_prefix(root, manifest, raw=raw)
    reopened, item, admission = _recover(root, manifest, provider)
    assert admission.outcome == "admitted"  # semantic admission is not grounding
    critiques = _critique_events(reopened)
    assert len(critiques) == 1
    assert critiques[0].inputs[0] == "config-critique:REJECTED_UNFOUNDED"


def test_recovered_malformed_referee_output_terminalizes_without_advice(tmp_path):
    from tests.test_v6_nonconjecture_recovery import _recover

    config, manifest = _referee_manifest()
    root = tmp_path / "referee-malformed"
    _preparation, provider, _view = _referee_provider_prefix(
        root, manifest, raw=b'{"verdict": "nope"}'
    )
    reopened, item, admission = _recover(root, manifest, provider)
    assert admission.outcome != "admitted"
    assert _critique_events(reopened) == []


def test_budget_denied_referee_terminates_typed_without_second_transition(tmp_path):
    """Live regression (run-e542c3c1): WorkBudgetDenied inside issue must not
    be followed by an abandon transition — the service's typed budget-denied
    termination is the complete durable outcome."""

    from deepreason.harness import Harness
    from deepreason.llm.budget import TokenMeter
    from deepreason.llm.firewall import leases_from_manifest
    from deepreason.referee import run_config_referee
    from deepreason.run_manifest import write_run_manifest
    from deepreason.workflow.transaction import WorkBudgetDenied
    from tests.test_v6_compact_recovery_transition import _bind_classification

    _config_unused, manifest = _referee_manifest()
    root = tmp_path / "referee-budget"
    harness = Harness(root)
    write_run_manifest(manifest, harness.root / "run-manifest.json")
    _bind_classification(harness, manifest)
    harness.record_measure(inputs=["cycle", "1", "-"])

    class _Adapter:
        leases = leases_from_manifest(manifest)
        meter = TokenMeter(10)

        def preview_request(self, role, pack, model, **kwargs):
            return "referee prompt", kwargs["wire_contract"], kwargs["endpoint_lease"], 8_192

    with pytest.raises(WorkBudgetDenied):
        run_config_referee(
            harness,
            _Adapter(),
            manifest,
            trigger_ref="config-referee-cycle:2",
        )
    items = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.contract_id == "config-referee.v1"
    ]
    assert len(items) == 1
    assert items[0].terminal is not None
    assert items[0].terminal.status == "budget_denied"
    assert _critique_events(harness) == []
    # The log stayed well-formed: reopening replays without error.
    reopened = Harness(root)
    assert reopened.workflow_state.transaction_work[items[0].preparation.id].terminal


def test_scheduler_absorbs_budget_denied_referee(monkeypatch):
    from types import SimpleNamespace

    from deepreason.scheduler.scheduler import Scheduler
    from deepreason.workflow.transaction import WorkBudgetDenied

    _config_unused, manifest = _referee_manifest()

    from types import SimpleNamespace as _NS

    def deny(*args, **kwargs):
        raise WorkBudgetDenied(_NS(work_id="sha256:" + "0" * 17))

    monkeypatch.setattr("deepreason.referee.run_config_referee", deny)
    fake = SimpleNamespace(
        run_manifest=manifest,
        adapter=SimpleNamespace(has_role=lambda role: True),
        harness=object(),
        _cycles=4,
        _drop=lambda error: None,
    )
    Scheduler._maybe_config_referee(fake)  # must not raise


def test_scheduler_fires_referee_only_on_the_frozen_cadence(monkeypatch):
    from types import SimpleNamespace

    from deepreason.scheduler.scheduler import Scheduler

    _config_unused, manifest = _referee_manifest()
    calls = []
    monkeypatch.setattr(
        "deepreason.referee.run_config_referee",
        lambda harness, adapter, mani, *, trigger_ref: calls.append(trigger_ref),
    )
    fake = SimpleNamespace(
        run_manifest=manifest,
        adapter=SimpleNamespace(has_role=lambda role: True),
        harness=object(),
        _cycles=8,
        _drop=lambda error: None,
    )
    Scheduler._maybe_config_referee(fake)
    assert calls == ["config-referee-cycle:8"]
    fake._cycles = 7
    Scheduler._maybe_config_referee(fake)
    assert calls == ["config-referee-cycle:8"]  # off-cadence cycle stays silent
    fake._cycles = 0
    Scheduler._maybe_config_referee(fake)
    assert calls == ["config-referee-cycle:8"]  # cycle zero never fires
    fake.adapter = SimpleNamespace(has_role=lambda role: False)
    fake._cycles = 12
    Scheduler._maybe_config_referee(fake)
    assert calls == ["config-referee-cycle:8"]  # no critic role, no dispatch


@pytest.mark.skipif(not NARROW.is_dir(), reason="live narrow evidence root is not present")
def test_view_builds_from_the_live_narrow_record():
    from deepreason.harness import Harness

    harness = Harness(NARROW, read_only=True)
    manifest = harness._load_workflow_manifest()
    view = build_config_review_view(
        harness, manifest, window_events=2_000, maximum_view_bytes=131_072
    )
    signals = [item.signal for item in view.observations]
    # The live narrow record carries citation checks and cycle heartbeats —
    # exactly the waste evidence a referee would cite against the config.
    assert any(item.startswith("evidence-citation:") for item in signals)
    assert "cycle" in signals
    assert view.research_policy_digest is not None
    assert view.research_policy_bounds["maximum_requests"] >= 1
    assert view.citable_seqs
    # Every observation really is inside the content-blind window.
    assert all(
        view.window_first_seq <= item.seq <= view.fence_seq
        for item in view.observations
    )
