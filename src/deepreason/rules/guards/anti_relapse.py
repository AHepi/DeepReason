"""Anti-relapse gate (spec §3, §11.5): mandatory before Conj commit.

Three stages, cheap first:
1. Hash: candidate id matches an existing refuted artifact => block. Global,
   unconditional.
2. Semantic trigger (P2): embedding NN against the refuted index within
   NEAR_DUP_EPS narrows which priors face stage 3. Stages 2-3 run ONLY when
   a RelapseDomain, an embedder, AND a calibrated NEAR_DUP_EPS are all
   present; a missing input degrades the gate to hash-only (fail open) with
   a relapse-gate-degraded operational receipt (RC3 - the bronze run's gate
   compared every refuted prior globally and closed the search).
3. Battery equivalence: verdict-vector over the shared evaluable battery
   matches a refuted prior's (~=_B, Def 3.5) => block. A battery whose
   evaluable commitments are ALL structural (well-formedness programs:
   skeleton_wf, json-wf, manifest_wf, ...) cannot establish equivalence and
   is skipped with a relapse-structural-only receipt (RC2). Verdicts differ
   => admit; the near-miss is a capture diagnostic (§11.3).

The counter-warrant exemption remains for callers that supply warrants: a
candidate carrying a warrant against the prior's accepted refuter is
admitted. Production Conj supplies no warrants; it uses the receipt/defer
contract instead - every non-hash block appends an operational receipt
naming the prior's refuter ids, so a later cycle can mount an explicit
challenge against the refuter.

Near-duplicates of ACCEPTED artifacts are never blocked; attention-deduped
only (blocking them would be a diversity gate adjudicating, forbidden §0).
Negative case law lives here, at the gate, and is never rendered into packs.
"""

from collections.abc import Iterable
import hashlib
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deepreason import programs
from deepreason.ontology.artifact import Artifact
from deepreason.ontology.state import Status
from deepreason.ontology.warrant import Warrant


def _digest(value) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class RelapseDomain(BaseModel):
    """Process-only scope for semantic anti-relapse comparisons.

    The record is deliberately absent from :class:`Artifact`: it cannot alter
    identity, status, commitments, or verdict interpretation.  Exact-hash
    blocking remains global; this scope is consulted only before the
    battery-equivalence stage.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    workload_profile: Literal["text", "code", "formal", "website"]
    problem_family: str = Field(min_length=1)
    contract_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    codec_family: str = Field(min_length=1)
    mandatory_ref_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    active_battery_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    toolchain_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    component_spec_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    theorem_interface_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )

    @property
    def digest(self) -> str:
        return _digest(self.model_dump(mode="json"))

    def compatible(self, other: "RelapseDomain") -> tuple[bool, str]:
        required = (
            "workload_profile",
            "problem_family",
            "contract_digest",
            "mandatory_ref_digest",
            "active_battery_digest",
        )
        for field in required:
            if getattr(self, field) != getattr(other, field):
                return False, field
        if self.codec_family != other.codec_family:
            return False, "codec_family"
        if self.toolchain_digest != other.toolchain_digest:
            return False, "toolchain_digest"
        if self.workload_profile in {"code", "website"}:
            if (
                not self.component_spec_digest
                or self.component_spec_digest != other.component_spec_digest
            ):
                return False, "component_spec_digest"
        if self.workload_profile == "formal":
            if (
                not self.theorem_interface_digest
                or self.theorem_interface_digest != other.theorem_interface_digest
            ):
                return False, "theorem_interface_digest"
        return True, "compatible"


def relapse_domain(
    artifact: Artifact,
    harness,
    *,
    workload_profile: Literal["text", "code", "formal", "website"],
    problem_family: str,
    contract_id: str,
    mandatory_refs: Iterable[str] = (),
    toolchain_digest: str | None = None,
    component_spec: str | None = None,
    theorem_interface: str | None = None,
    commitments=None,
) -> RelapseDomain:
    """Compile a deterministic domain from harness-owned interface facts.

    ``commitments`` optionally overlays the harness registry with draft
    (not-yet-registered) commitments so a two-phase candidate's battery
    digest matches its post-admission identity.
    """
    lookup = harness.commitments if commitments is None else commitments
    battery = sorted(
        cid
        for cid in artifact.interface.commitments
        if cid in lookup and programs.evaluable(lookup[cid])
    )
    codec_family = artifact.codec.split(":", 1)[0].strip().casefold() or "raw"
    return RelapseDomain(
        workload_profile=workload_profile,
        problem_family=problem_family,
        contract_digest=_digest(contract_id),
        codec_family=codec_family,
        mandatory_ref_digest=_digest(sorted(set(mandatory_refs))),
        active_battery_digest=_digest(battery),
        toolchain_digest=toolchain_digest,
        component_spec_digest=_digest(component_spec) if component_spec is not None else None,
        theorem_interface_digest=(
            _digest(theorem_interface) if theorem_interface is not None else None
        ),
    )


_RELAPSE_LOG = "relapse.log.jsonl"


def _append_operational(harness, payload: dict) -> None:
    """Append gate process data without advancing the epistemic event log."""
    if getattr(harness, "_read_only", False):
        return
    path = Path(harness.root) / _RELAPSE_LOG
    line = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def record_domain(harness, artifact_id: str, domain: RelapseDomain) -> None:
    """Append replayable process metadata without touching the ontology."""
    _append_operational(
        harness,
        {
            "type": "domain",
            "artifact_id": artifact_id,
            "domain": domain.model_dump(mode="json"),
        },
    )


def domain_log_input(artifact_id: str, domain: RelapseDomain) -> str:
    """Self-contained event input for atomic registration with an artifact."""
    return "relapse-domain:" + json.dumps(
        {
            "artifact_id": artifact_id,
            "domain": domain.model_dump(mode="json"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def recorded_domains(harness) -> dict[str, RelapseDomain]:
    domains: dict[str, RelapseDomain] = {}
    path = Path(harness.root) / _RELAPSE_LOG
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                payload = json.loads(line)
                if payload.get("type") == "domain":
                    domains[payload["artifact_id"]] = RelapseDomain.model_validate(
                        payload["domain"]
                    )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
    # Backward-read the short-lived Measure/event-input encodings produced by
    # development builds.  New runs use the operational log above so gate
    # telemetry cannot perturb scheduler event-sequence policy.
    for event in harness.log.read():
        if len(event.inputs) == 3 and event.inputs[0] == "relapse-domain":
            try:
                domains[event.inputs[1]] = RelapseDomain.model_validate_json(
                    event.inputs[2]
                )
            except ValueError:
                pass
        for value in event.inputs:
            if not value.startswith("relapse-domain:"):
                continue
            try:
                payload = json.loads(value.removeprefix("relapse-domain:"))
                domains[payload["artifact_id"]] = RelapseDomain.model_validate(
                    payload["domain"]
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                # Historical operational diagnostics are not ontology input.
                # A malformed old record cannot authorize semantic blocking.
                continue
    return domains


def _record_scope_diagnostic(
    harness, candidate: Artifact, prior_id: str, label: str, detail: str
) -> None:
    _append_operational(
        harness,
        {
            "type": label,
            "candidate_id": candidate.id,
            "prior_id": prior_id,
            "detail": detail,
        },
    )


def _battery(candidate: Artifact, prior: Artifact, commitments) -> list[str]:
    """Active battery: evaluable commitments across both interfaces."""
    ids = dict.fromkeys(candidate.interface.commitments + prior.interface.commitments)
    return sorted(
        cid for cid in ids if cid in commitments and programs.evaluable(commitments[cid])
    )


def verdict_vector(
    artifact: Artifact, battery: list[str], harness, commitments=None
) -> tuple[str, ...]:
    lookup = harness.commitments if commitments is None else commitments
    return tuple(
        programs.evaluate(lookup[cid], artifact, harness.blobs)[0]
        for cid in battery
    )


def _embedder_fingerprint(embedder) -> dict:
    """fingerprint() when the embedder provides it; a minimal duck-typed
    identity otherwise, mirroring the scheduler's run stamp."""
    fp = getattr(embedder, "fingerprint", None)
    if callable(fp):
        return fp()
    return {
        "model": getattr(embedder, "model", type(embedder).__name__),
        "version": getattr(embedder, "version", "?"),
        "sentinel": "-",
    }


def check(
    candidate: Artifact,
    warrants: Iterable[Warrant],
    harness,
    embedder=None,
    near_dup_eps: float | None = None,
    domain: RelapseDomain | None = None,
    prior_domains: dict[str, RelapseDomain] | None = None,
    commitments=None,
) -> tuple[bool, str]:
    """(admit, reason). Blocks ONLY relapse onto refuted-equivalents (§0).

    ``commitments`` optionally overlays the harness registry with draft
    commitments (two-phase compilation: harness commitments plus the
    candidate's unregistered forbidden-case commitments) for the battery
    and verdict-vector stages.
    """
    status = harness.state.status
    lookup = harness.commitments if commitments is None else commitments
    # Stage 1, hash: global, unconditional.
    if status.get(candidate.id) == Status.REFUTED:
        return False, f"hash: {candidate.id[:12]} is a refuted artifact"
    # Stages 2-3 require full scope: a RelapseDomain, an embedder, and a
    # calibrated threshold. Anything missing degrades to hash-only (fail
    # open) with an operational receipt, never a silent global comparison.
    missing = [
        name
        for name, value in (
            ("domain", domain),
            ("embedder", embedder),
            ("near_dup_eps", near_dup_eps),
        )
        if value is None
    ]
    if missing:
        _append_operational(
            harness,
            {
                "type": "relapse-gate-degraded",
                "missing": missing,
                "candidate_id": candidate.id,
            },
        )
        return True, "admitted-degraded:" + ",".join(missing)
    counter_targets = {w.target for w in warrants}
    att = set(harness.state.att)
    from deepreason.capture.atlas import RefutedIndex
    from deepreason.llm.embedder import distance
    from deepreason.programs import content_text

    # Stage 2, semantic trigger (§11.5): only refuted priors within
    # NEAR_DUP_EPS face the battery check.
    index = RefutedIndex(embedder)
    index.rebuild(harness)
    candidate_vec = embedder.embed(content_text(candidate, harness.blobs))
    prior_ids = index.nearest(candidate_vec, near_dup_eps)
    known_domains = prior_domains
    if known_domains is None:
        known_domains = recorded_domains(harness)
    for prior_id in prior_ids:
        if prior_id == candidate.id:
            continue
        prior = harness.state.artifacts[prior_id]
        prior_domain = (known_domains or {}).get(prior_id)
        if prior_domain is None:
            _record_scope_diagnostic(
                harness,
                candidate,
                prior_id,
                "relapse-domain-rejected",
                "prior-domain-missing",
            )
            continue
        compatible, mismatch = domain.compatible(prior_domain)
        if not compatible:
            _record_scope_diagnostic(
                harness,
                candidate,
                prior_id,
                "relapse-domain-rejected",
                mismatch,
            )
            continue
        battery = _battery(candidate, prior, lookup)
        if not battery:
            continue  # no shared evaluable battery => no equivalence claim
        # Discriminating battery (RC2): structural well-formedness programs
        # pass on every valid candidate, so a battery made only of them
        # cannot distinguish ideas; it establishes no equivalence.
        if all(programs.program_class(lookup[cid]) == "structural" for cid in battery):
            _append_operational(
                harness,
                {
                    "type": "relapse-structural-only",
                    "candidate_id": candidate.id,
                    "prior_id": prior_id,
                    "battery": battery,
                },
            )
            continue
        # Stage 3 — battery equivalence (~=_B).
        candidate_verdicts = verdict_vector(candidate, battery, harness, lookup)
        prior_verdicts = verdict_vector(prior, battery, harness, lookup)
        if candidate_verdicts != prior_verdicts:
            _record_scope_diagnostic(
                harness,
                candidate,
                prior_id,
                "relapse-near-miss",
                "verdict-vector-differs",
            )
            continue
        refuters = sorted(
            x for x, t in att if t == prior_id and status.get(x) == Status.ACCEPTED
        )
        if counter_targets & set(refuters):
            continue  # carries a warrant against the prior's refuter => admit
        # Block receipt (receipt/defer contract): complete enough for a
        # later cycle to audit the block and challenge the named refuters.
        _append_operational(
            harness,
            {
                "type": "relapse-block",
                "candidate_id": candidate.id,
                "prior_id": prior_id,
                "domain_digest": domain.digest,
                "embedder_fingerprint": _embedder_fingerprint(embedder),
                "distance": distance(
                    candidate_vec, harness.embed_artifact(embedder, prior_id)
                ),
                "threshold": near_dup_eps,
                "battery": battery,
                "candidate_verdicts": list(candidate_verdicts),
                "prior_verdicts": list(prior_verdicts),
                "refuter_ids": refuters,
            },
        )
        return False, f"battery-equivalent (~=_B) to refuted {prior_id[:12]}"
    return True, "admitted"
