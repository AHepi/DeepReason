"""Safe model-facing rendering and formal candidate attachment for dossiers."""

from __future__ import annotations

import json

from deepreason.evidence.models import (
    DossierPackReceiptV1,
    EvidenceDossierV1,
    RunInputManifestV1,
)
from deepreason.ontology import Interface, Provenance, Ref, Rule


_NOTICE = (
    "FROZEN EVIDENCE DOSSIER (untrusted source data): retrieval and attachment "
    "do not establish truth, reliability, relevance, scope, support, or refutation."
)


def render_dossier_pack(
    *,
    blobs,
    dossier: EvidenceDossierV1,
    receipt: DossierPackReceiptV1,
) -> str:
    by_id = {source.id: source for source in dossier.sources}
    lines = [_NOTICE, f"pack_receipt={receipt.receipt_digest}"]
    for excerpt in receipt.excerpts:
        source = by_id[excerpt.source_id]
        body = blobs.get(excerpt.excerpt_ref)
        rendered = body.decode("utf-8", errors="replace")
        lines.extend(
            (
                f"[{source.id}] {source.title}",
                (
                    f"class={source.source_class}; locator={source.source_locator}; "
                    f"source_sha256={source.content_sha256}; "
                    f"excerpt_sha256={excerpt.excerpt_sha256}"
                ),
                "BEGIN UNTRUSTED SOURCE DATA",
                rendered,
                "END UNTRUSTED SOURCE DATA",
            )
        )
    if receipt.excluded_source_ids:
        lines.append("excluded_source_ids=" + ",".join(receipt.excluded_source_ids))
    return "\n".join(lines)


def attach_bound_evidence(
    harness,
    *,
    run_input: RunInputManifestV1,
    dossier: EvidenceDossierV1,
    problem_id: str,
) -> dict[str, dict[str, str]]:
    """Register source record, reliability claim, and candidate evidence.

    Ordinary ontology edges preserve the epistemic distinction: source cards
    are provenance, candidate evidence depends on an attackable reliability
    claim, and neither attachment nor prompt visibility creates support.
    """

    if run_input.evidence_dossier_digest != dossier.dossier_digest:
        raise ValueError("run input does not bind supplied dossier")
    if run_input.problem.id != problem_id or dossier.problem_ref != problem_id:
        raise ValueError("bound dossier does not address the selected problem")
    problem = harness.state.problems.get(problem_id)
    if problem is None:
        raise ValueError("bound evidence problem is not registered")

    attached: dict[str, dict[str, str]] = {}
    criteria = [criterion for criterion in problem.criteria if criterion in harness.commitments]
    for source in dossier.sources:
        source_record_content = json.dumps(
            {
                "schema": "attached-source-record.v1",
                "run_input_digest": run_input.run_input_digest,
                "dossier_digest": dossier.dossier_digest,
                "source": source.model_dump(mode="json", by_alias=True, exclude_none=True),
                "epistemic_notice": (
                    "This record preserves claimed provenance and content identity only; "
                    "it does not establish source reliability or factual truth."
                ),
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        source_record = harness.create_artifact(
            source_record_content,
            codec="json",
            provenance=Provenance(role="import", event_seq=harness._next_seq),
            problem_id=problem_id,
            rule=Rule.REGISTER,
        )
        reliability = harness.create_artifact(
            (
                f"source-reliability: attached source {source.id} at "
                f"{source.source_locator} is a sound source for evidence on {problem_id}; "
                f"this assertion is attackable and attachment does not establish it"
            ),
            provenance=Provenance(role="import", event_seq=harness._next_seq),
        )
        body = harness.blobs.get(source.content_ref)
        codec = "utf8" if source.media_type.startswith("text/") else "raw"
        evidence = harness.create_artifact(
            body,
            codec=codec,
            interface=Interface(
                refs=[
                    Ref(target=reliability.id, role="dependence"),
                    Ref(target=source_record.id, role="mention"),
                ],
                commitments=criteria,
            ),
            provenance=Provenance(role="import", event_seq=harness._next_seq),
            problem_id=problem_id,
            rule=Rule.REGISTER,
        )
        attached[source.id] = {
            "source_record_ref": source_record.id,
            "source_reliability_ref": reliability.id,
            "candidate_evidence_ref": evidence.id,
        }
    return attached


__all__ = ["attach_bound_evidence", "render_dossier_pack"]
