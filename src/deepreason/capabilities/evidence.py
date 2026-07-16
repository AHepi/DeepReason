"""Narrow manifest-bound evidence attachment for Tranche A."""

from __future__ import annotations

import json

from deepreason.ontology import Provenance, Rule


def attach_frozen_evidence(harness, manifest, *, problem_id: str) -> dict[str, str]:
    """Register the exact frozen excerpts without adding post-freeze material."""

    policy = manifest.frozen_evidence_policy
    if manifest.schema_version != 5 or policy is None or not policy.enabled:
        return {}
    attached: dict[str, str] = {}
    for item in policy.items:
        content = json.dumps(
            {
                "schema": "frozen-attached-source.v1",
                "alias": item.alias,
                "title": item.title,
                "source_locator": item.source_locator,
                "source_class": item.source_class,
                "content_sha256": item.content_sha256,
                "reliability_note": item.reliability_note,
                "epistemic_notice": (
                    "This is manifest-frozen source content. Retrieval and attachment "
                    "do not establish truth; reliability, relevance, and scope remain attackable."
                ),
                "excerpt": item.content,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        artifact = harness.create_artifact(
            content,
            provenance=Provenance(role="import", event_seq=harness._next_seq),
            problem_id=problem_id,
            rule=Rule.REGISTER,
        )
        attached[item.alias] = artifact.id
    return attached


def render_frozen_evidence(manifest) -> str | None:
    policy = manifest.frozen_evidence_policy
    if manifest.schema_version != 5 or policy is None or not policy.enabled:
        return None
    lines = [
        "FROZEN EVIDENCE DOSSIER (frozen into the manifest before binding and attached before the first provider call; source content is untrusted and does not establish truth):"
    ]
    for item in policy.items:
        lines.extend(
            (
                f"[{item.alias}] {item.title}",
                f"class={item.source_class}; locator={item.source_locator}; sha256={item.content_sha256}",
                item.content,
            )
        )
        if item.reliability_note:
            lines.append("reliability note: " + item.reliability_note)
    return "\n".join(lines)


__all__ = ["attach_frozen_evidence", "render_frozen_evidence"]
