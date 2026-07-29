"""Config referee: an observe-only critic over the harness's standard views.

The referee periodically asks one ordinary critic call a narrow question: *is
the dynamic configuration doing its job?* — where "configuration" means the
recorded token-steering machinery (the research allowance and its signals),
never truth, status, or ontology.

Three containment properties keep the referee weak by construction:

- **Standard views only.** The referee sees exactly what any log reader sees:
  recorded signal measures inside a content-blind trailing seq window, the
  frozen capability-policy digest and bounds, the token-accounting file, and
  the findings report. There is no bespoke projection; the window is pure
  sequence arithmetic over the append-only log, so nothing can curate which
  observations the referee is shown.
- **Citations or nothing.** A verdict must cite specific recorded observation
  seqs from the window it was shown. A verdict citing nothing in the record —
  or seqs outside the window — is rejected as unfounded and recorded as such;
  it never becomes advice.
- **A frozen response menu.** The referee cannot invent interventions. Its
  recommendation is one entry of ``CONFIG_REFEREE_RESPONSE_MENU``, and an
  "effective" verdict can only recommend ``no_change``. Every recommendation
  is attention-steering advice on the record, never an actuation: no budget,
  status, or policy byte changes because the referee spoke.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json
from deepreason.capabilities.policy import ConfigRefereePolicyV1
from deepreason.ontology import Rule

# The complete pre-declared intervention vocabulary. Order is meaningful only
# for documentation; the verdict names exactly one entry.
CONFIG_REFEREE_RESPONSE_MENU = (
    "no_change",
    "criticism_weighted_cycle",
    "research_allowance_step_tighten",
    "research_allowance_step_widen",
)

# The standard signal families a config review may observe: the config's own
# working-allowance record, the fetch attempts it governs, the citation checks
# that define waste, cycle/run heartbeats for pacing, admission-gate pressure,
# and any previous critiques (so the referee can see whether earlier advice
# corresponded to a change in the signals).
_OBSERVATION_SIGNALS = frozenset({"cycle", "run-resume", "run-stop"})
_OBSERVATION_PREFIXES = (
    "research-allowance:",
    "research-fetch:",
    "evidence-citation:",
    "gate:",
    "config-critique:",
)

_INPUT_CLIP_CHARS = 200
_MAX_OBSERVATION_INPUTS = 8
_EXCERPT_SHARE = 4  # token accounting and findings each get 1/4 of the byte bound


class ConfigRefereeError(ValueError):
    """A config-referee record fell outside its frozen authority."""


class _FrozenModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )


class ConfigObservationV1(_FrozenModel):
    """One recorded signal measure, exactly as the log holds it (clipped)."""

    seq: int = Field(ge=0)
    signal: str = Field(min_length=1, max_length=256)
    inputs: tuple[str, ...] = Field(default=(), max_length=_MAX_OBSERVATION_INPUTS)


class ConfigReviewViewV1(_FrozenModel):
    """The complete referee-visible material, all from standard views."""

    schema_: Literal["config-review-view.v1"] = Field(
        "config-review-view.v1", alias="schema"
    )
    fence_seq: int = Field(ge=0)
    window_first_seq: int = Field(ge=0)
    window_events: int = Field(ge=1)
    research_policy_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    research_policy_bounds: dict[str, int] = Field(default_factory=dict)
    observations: tuple[ConfigObservationV1, ...] = ()
    dropped_observations: int = Field(default=0, ge=0)
    token_accounting_excerpt: str = Field(default="", max_length=262_144)
    findings_excerpt: str = Field(default="", max_length=262_144)

    @model_validator(mode="after")
    def _window_shape(self):
        if self.window_first_seq > self.fence_seq:
            raise ValueError("config review window begins after its fence")
        for observation in self.observations:
            if not self.window_first_seq <= observation.seq <= self.fence_seq:
                raise ValueError("config review observation escapes its seq window")
        return self

    @property
    def citable_seqs(self) -> frozenset[int]:
        return frozenset(item.seq for item in self.observations)


def _read_clipped(path: Path, limit: int) -> str:
    try:
        if not path.is_file():
            return ""
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def build_config_review_view(
    harness,
    manifest,
    *,
    window_events: int,
    maximum_view_bytes: int,
) -> ConfigReviewViewV1:
    """Assemble the deterministic review material from standard views only.

    The window is content-blind: the trailing ``window_events`` sequence
    numbers of the append-only log, full stop. Within it, the included
    observations are every measure carrying a registered config-relevant
    signal — never a hand-picked subset. When the byte bound forces
    truncation, the OLDEST observations drop first and the drop count is
    part of the view, so a truncated review is visibly truncated.
    """

    if window_events < 1:
        raise ConfigRefereeError("CONFIG_REFEREE_WINDOW_REQUIRED")
    if maximum_view_bytes < 1:
        raise ConfigRefereeError("CONFIG_REFEREE_VIEW_BYTES_REQUIRED")
    events = list(harness.log.read())
    fence_seq = events[-1].seq if events else 0
    window_first_seq = max(0, fence_seq - window_events + 1)
    observations: list[ConfigObservationV1] = []
    for event in events:
        if event.seq < window_first_seq or event.seq > fence_seq:
            continue
        if event.rule != Rule.MEASURE or not event.inputs:
            continue
        signal = str(event.inputs[0])
        if signal not in _OBSERVATION_SIGNALS and not signal.startswith(
            _OBSERVATION_PREFIXES
        ):
            continue
        observations.append(
            ConfigObservationV1(
                seq=event.seq,
                signal=signal[:256],
                inputs=tuple(
                    str(value)[:_INPUT_CLIP_CHARS]
                    for value in event.inputs[1 : _MAX_OBSERVATION_INPUTS + 1]
                ),
            )
        )

    capabilities = getattr(manifest, "inquiry_capability_policy", None)
    research = getattr(capabilities, "research", None)
    research_digest = research.digest if research is not None else None
    research_bounds = (
        {
            "maximum_requests": research.maximum_requests,
            "maximum_sources": research.maximum_sources,
            "maximum_response_bytes": research.maximum_response_bytes,
        }
        if research is not None and research.enabled
        else {}
    )

    excerpt_limit = max(1, maximum_view_bytes // _EXCERPT_SHARE)
    root = Path(harness.root)
    token_accounting = _read_clipped(root / "TOKEN_ACCOUNTING.json", excerpt_limit)
    findings = _read_clipped(root / "FINDINGS.md", excerpt_limit)

    dropped = 0
    while True:
        view = ConfigReviewViewV1(
            fence_seq=fence_seq,
            window_first_seq=window_first_seq,
            window_events=window_events,
            research_policy_digest=research_digest,
            research_policy_bounds=research_bounds,
            observations=tuple(observations),
            dropped_observations=dropped,
            token_accounting_excerpt=token_accounting,
            findings_excerpt=findings,
        )
        size = len(canonical_json(view.model_dump(mode="json", by_alias=True)))
        if size <= maximum_view_bytes or not observations:
            return view
        observations.pop(0)
        dropped += 1


class ConfigRefereeVerdictV1(_FrozenModel):
    """One typed critique of the configuration, grounded or rejected."""

    schema_: Literal["config-referee-verdict.v1"] = Field(
        "config-referee-verdict.v1", alias="schema"
    )
    verdict: Literal["config_effective", "config_mistuned"]
    assessment: str = Field(min_length=1, max_length=4_096)
    cited_seqs: tuple[int, ...] = Field(min_length=1, max_length=32)
    recommendation: Literal[
        "no_change",
        "criticism_weighted_cycle",
        "research_allowance_step_tighten",
        "research_allowance_step_widen",
    ]

    @field_validator("cited_seqs")
    @classmethod
    def _unique_citations(cls, value):
        if len(value) != len(set(value)) or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in value
        ):
            raise ValueError("cited seqs must be unique non-negative integers")
        return tuple(value)

    @model_validator(mode="after")
    def _menu_coherence(self):
        if (self.verdict == "config_effective") != (
            self.recommendation == "no_change"
        ):
            raise ValueError(
                "an effective config recommends no_change and a mistuned "
                "config recommends one menu intervention"
            )
        return self


def validate_config_referee_verdict(
    verdict: ConfigRefereeVerdictV1, view: ConfigReviewViewV1
) -> None:
    """Fail closed unless every citation names a recorded observation shown."""

    citable = view.citable_seqs
    unfounded = sorted(seq for seq in verdict.cited_seqs if seq not in citable)
    if unfounded:
        raise ConfigRefereeError(
            "CONFIG_REFEREE_VERDICT_UNFOUNDED: cited seqs "
            f"{unfounded} are not recorded observations in the review window"
        )


def record_config_critique(
    harness,
    verdict: ConfigRefereeVerdictV1,
    view: ConfigReviewViewV1,
):
    """Durably record one grounded critique; advice on the record, never actuation."""

    validate_config_referee_verdict(verdict, view)
    view_ref = harness.blobs.put(
        canonical_json(view.model_dump(mode="json", by_alias=True))
    )
    verdict_ref = harness.blobs.put(
        canonical_json(verdict.model_dump(mode="json", by_alias=True))
    )
    cited = ",".join(str(seq) for seq in verdict.cited_seqs)[:_INPUT_CLIP_CHARS]
    return harness.record_measure(
        inputs=[
            f"config-critique:{verdict.verdict}",
            f"recommendation:{verdict.recommendation}",
            f"cited:{cited}",
            f"view:{view_ref}",
            f"verdict:{verdict_ref}",
        ]
    )


def record_rejected_config_critique(
    harness,
    error: ConfigRefereeError,
    view: ConfigReviewViewV1,
):
    """Record an unfounded or malformed critique as a typed refusal.

    A referee output that fails citation validation is not silently retried
    into existence: the rejection itself is the durable outcome, so a
    misbehaving referee is visible in the same log it failed to cite.
    """

    view_ref = harness.blobs.put(
        canonical_json(view.model_dump(mode="json", by_alias=True))
    )
    return harness.record_measure(
        inputs=[
            "config-critique:REJECTED_UNFOUNDED",
            str(error)[:_INPUT_CLIP_CHARS],
            f"view:{view_ref}",
        ]
    )


def latest_config_critique(harness) -> dict | None:
    """Return the most recent recorded critique (or rejection) as plain data."""

    latest: dict | None = None
    for event in list(harness.log.read()):
        if event.rule != Rule.MEASURE or not event.inputs:
            continue
        signal = str(event.inputs[0])
        if not signal.startswith("config-critique:"):
            continue
        latest = {
            "seq": event.seq,
            "signal": signal,
            "inputs": tuple(str(value) for value in event.inputs[1:]),
        }
    return latest


CONFIG_REFEREE_CONTRACT_V1 = "config-referee.v1"


def _wire_contract_class():
    """Build the wire contract lazily so referee stays importable standalone."""

    from pydantic import Field as WireField
    from deepreason.llm.wire import StrictWireModel, WireContract

    class ConfigRefereeWireV1(StrictWireModel):
        verdict: Literal["config_effective", "config_mistuned"]
        assessment: str = WireField(min_length=1, max_length=4_096)
        cited_seqs: list[int] = WireField(min_length=1, max_length=32)
        recommendation: Literal[
            "no_change",
            "criticism_weighted_cycle",
            "research_allowance_step_tighten",
            "research_allowance_step_widen",
        ]

    class ConfigRefereeWireContractV1(WireContract[ConfigRefereeVerdictV1]):
        """One review, one verdict; targets and evidence are the shown view."""

        def __init__(self, aliases=None) -> None:
            super().__init__(
                CONFIG_REFEREE_CONTRACT_V1,
                ConfigRefereeWireV1,
                ConfigRefereeVerdictV1,
                aliases=aliases,
            )

        def compile(self, wire) -> ConfigRefereeVerdictV1:
            return ConfigRefereeVerdictV1(
                verdict=wire.verdict,
                assessment=wire.assessment,
                cited_seqs=tuple(wire.cited_seqs),
                recommendation=wire.recommendation,
            )

    return ConfigRefereeWireContractV1


def config_referee_wire_contract(aliases=None):
    return _wire_contract_class()(aliases)


def render_config_review_pack(view: ConfigReviewViewV1) -> str:
    """Deterministic review pack: the complete view, nothing else."""

    payload = canonical_json(view.model_dump(mode="json", by_alias=True)).decode(
        "utf-8"
    )
    return (
        "config-review SRC_001\n"
        "Review whether the harness's dynamic token-steering configuration is "
        "doing its job: does the working research allowance tighten when "
        "consumed sources go uncited, widen when evidence converts, and does "
        "criticism keep pace with rivalry growth? Judge only the recorded "
        "observations below. Every claim in your assessment must cite the seq "
        "numbers of specific observations shown here; a verdict citing "
        "anything else is rejected. If the configuration is effective, say so "
        "and recommend no_change. If it is mistuned, recommend exactly one "
        "menu intervention.\n\n"
        f"{payload}\n"
    )


def run_config_referee(
    harness,
    adapter,
    manifest,
    *,
    trigger_ref: str,
) -> ConfigRefereeVerdictV1 | None:
    """Execute one transactional config review under frozen manifest authority.

    Returns the grounded verdict, or ``None`` when the review was skipped
    (disabled policy, an existing transaction for this trigger) or its
    output was rejected as unfounded — in which case the rejection is
    already on the record.
    """

    from deepreason.llm.firewall import (
        resolve_school_role_lease,
        route_fingerprint,
        select_lease,
    )
    from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
    from deepreason.workflow.transaction import (
        ContextNamespace,
        VisibleContextItemV1,
    )
    from deepreason.workflow.transaction_service import InquiryTransactionService

    capabilities = getattr(manifest, "inquiry_capability_policy", None)
    policy = getattr(capabilities, "config_referee", None)
    if policy is None or not policy.enabled:
        return None
    if manifest.schema_version != 6:
        raise ConfigRefereeError("CONFIG_REFEREE_V6_REQUIRED")
    meter = getattr(adapter, "meter", None)
    if meter is None:
        raise ConfigRefereeError("CONFIG_REFEREE_METER_REQUIRED")

    criticism = manifest.criticism_policy
    if criticism is not None:
        critic_school_id = min(
            binding.school_id
            for binding in criticism.bindings
            if binding.role == "argumentative_critic"
        )
        endpoint_lease = resolve_school_role_lease(
            manifest,
            adapter.leases,
            school_id=critic_school_id,
            role="argumentative_critic",
        )
    else:
        critic_school_id = None
        endpoint_lease = select_lease(adapter.leases, "argumentative_critic", 0)
    route_ref = RouteLeaseRefV1(
        role="argumentative_critic",
        seat=endpoint_lease.seat,
        endpoint_id=endpoint_lease.route.endpoint_id,
        route_sha256=route_fingerprint(endpoint_lease.route),
    )

    view = build_config_review_view(
        harness,
        manifest,
        window_events=policy.window_events,
        maximum_view_bytes=policy.maximum_view_bytes,
    )
    view_bytes = canonical_json(view.model_dump(mode="json", by_alias=True))
    view_ref = harness.blobs.put(view_bytes)
    payload = {
        "schema": "config-referee.semantic-task.v1",
        "critic_school_id": critic_school_id,
        "view_ref": view_ref,
        "fence_seq": view.fence_seq,
        "caller_trigger_ref": trigger_ref,
    }
    matches = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.contract_id == CONFIG_REFEREE_CONTRACT_V1
        and item.preparation.task_payload_value == payload
        and item.preparation.route_lease == route_ref
    ]
    if matches:
        # This exact review already has durable work; recovery owns any
        # incomplete remainder and a completed one already spoke.
        return None

    service = InquiryTransactionService(harness, manifest, meter)
    from deepreason.llm.wire import AliasTable

    aliases = AliasTable({"SRC_001": view_ref})
    contract = config_referee_wire_contract(aliases)
    fence = max(0, harness._next_seq - 1)
    preparation_trigger = (
        "config-referee:" + hashlib.sha256(canonical_json(payload)).hexdigest()
    )
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CRITICISM,
        attempt_index=0,
        route_lease=route_ref,
        contract_id=CONFIG_REFEREE_CONTRACT_V1,
        trigger_ref=preparation_trigger,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        target_refs=(view_ref,),
        input_refs=(view_ref,),
        task_payload_value=payload,
    )
    authorized = None

    def abandon(*, issued: bool, reason_code: str) -> None:
        if authorized is not None and authorized.reservation.is_open:
            authorized.release()
        service.terminate(
            work_id=preparation.id,
            attempt_index=preparation.attempt_index,
            status="abandoned",
            reason_code=reason_code,
            usage_status=("unknown" if issued else "exact"),
            prompt_tokens=(None if issued else 0),
            completion_tokens=(None if issued else 0),
        )

    try:
        pack = render_config_review_pack(view)
        rendered_bytes = len(pack.encode("utf-8"))
        plan = service.context_plan(
            preparation,
            plan_kind="dossier",
            items=(
                VisibleContextItemV1(
                    namespace=ContextNamespace.SOURCE,
                    alias="SRC_001",
                    object_ref=view_ref,
                    content_sha256=view_ref,
                    planned_bytes=rendered_bytes,
                ),
            ),
            maximum_bytes=rendered_bytes,
            rendered_bytes=rendered_bytes,
        )
        prompt, preview_contract, preview_lease, maximum_tokens = (
            adapter.preview_request(
                "argumentative_critic",
                pack,
                ConfigRefereeVerdictV1,
                endpoint_index=endpoint_lease.seat,
                template_role="config_referee",
                wire_contract=contract,
                aliases=aliases,
                endpoint_lease=endpoint_lease,
            )
        )
        if preview_contract is not contract or preview_lease != endpoint_lease:
            raise ValueError("config referee preview changed frozen call authority")
        authorized = service.issue(
            preparation,
            plans=(plan,),
            prompt=prompt,
            max_tokens=maximum_tokens,
        )
    except Exception:
        abandon(issued=False, reason_code="config_referee_preissue_failure")
        raise

    provider = None
    try:
        output, llm_call = adapter.call(
            "argumentative_critic",
            pack,
            ConfigRefereeVerdictV1,
            endpoint_index=endpoint_lease.seat,
            template_role="config_referee",
            wire_contract=contract,
            aliases=aliases,
            endpoint_lease=endpoint_lease,
            school_id=critic_school_id,
            dispatch_authorization=authorized,
        )
    except Exception as error:
        from deepreason.llm.adapter import EndpointError, SchemaRepairError

        if isinstance(error, EndpointError):
            spend = getattr(error, "spend", None)
            if spend is None:
                abandon(issued=True, reason_code="config_referee_transport_unknown")
            else:
                diagnostic_ref = (
                    spend.attempt_trace[-1].diagnostic_ref
                    if spend.attempt_trace
                    else harness.blobs.put(str(error).encode("utf-8"))
                )
                provider = service.record_provider_attempt(
                    authorized,
                    call=spend,
                    outcome="transport_failure",
                    usage_status="unknown",
                    diagnostic_ref=diagnostic_ref,
                )
                service.terminate(
                    work_id=preparation.id,
                    attempt_index=preparation.attempt_index,
                    status="transport_failed",
                    reason_code="config_referee_transport_failure",
                    usage_status="unknown",
                    provider_attempt=provider,
                )
                error.spend = None
            error.transaction_terminalized = True
            raise
        if isinstance(error, SchemaRepairError):
            repaired = service.repair_schema_failure(
                adapter=adapter,
                authorized=authorized,
                error=error,
                role="argumentative_critic",
                pack=pack,
                output_model=ConfigRefereeVerdictV1,
                wire_contract=contract,
                endpoint_index=endpoint_lease.seat,
                template_role="config_referee",
                endpoint_lease=endpoint_lease,
                school_id=critic_school_id,
                reason_prefix="config_referee",
            )
            output = repaired.output
            llm_call = repaired.llm_call
            preparation = repaired.preparation
            authorized = repaired.authorized
            provider = repaired.provider_attempt
        else:
            abandon(issued=True, reason_code="config_referee_authority_failure")
            raise

    if provider is None:
        provider = service.record_provider_attempt(
            authorized,
            call=llm_call,
            outcome="provider_result",
            usage_status="exact",
        )
    verdict = ConfigRefereeVerdictV1.model_validate(
        output.model_dump(mode="python", by_alias=True)
    )
    admitted_ref = harness.blobs.put(
        canonical_json(verdict.model_dump(mode="json", by_alias=True))
    )
    admission = service.record_semantic_admission(
        provider,
        outcome="admitted",
        admitted_refs=(admitted_ref,),
    )
    service.terminate(
        work_id=preparation.id,
        attempt_index=preparation.attempt_index,
        status="completed",
        reason_code="config_referee_output_admitted",
        usage_status="exact",
        prompt_tokens=llm_call.prompt_tokens,
        completion_tokens=llm_call.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    try:
        record_config_critique(harness, verdict, view)
    except ConfigRefereeError as error:
        record_rejected_config_critique(harness, error, view)
        return None
    return verdict


def parse_config_referee_verdict(payload: str | bytes) -> ConfigRefereeVerdictV1:
    """Strictly parse one referee response; anything nonconforming fails typed."""

    try:
        value = json.loads(payload)
    except (TypeError, json.JSONDecodeError) as error:
        raise ConfigRefereeError(
            f"CONFIG_REFEREE_VERDICT_UNPARSEABLE: {type(error).__name__}"
        ) from error
    try:
        return ConfigRefereeVerdictV1.model_validate(value)
    except ValueError as error:
        raise ConfigRefereeError(
            f"CONFIG_REFEREE_VERDICT_INVALID: {error}"
        ) from error


__all__ = [
    "CONFIG_REFEREE_CONTRACT_V1",
    "CONFIG_REFEREE_RESPONSE_MENU",
    "ConfigObservationV1",
    "ConfigRefereeError",
    "ConfigRefereePolicyV1",
    "ConfigRefereeVerdictV1",
    "ConfigReviewViewV1",
    "build_config_review_view",
    "config_referee_wire_contract",
    "latest_config_critique",
    "render_config_review_pack",
    "run_config_referee",
    "parse_config_referee_verdict",
    "record_config_critique",
    "record_rejected_config_critique",
    "validate_config_referee_verdict",
]
