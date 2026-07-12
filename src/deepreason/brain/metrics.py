"""Process-only brain metrics, intentionally outside adjudication."""

from __future__ import annotations

from deepreason.brain.models import RetrievalResult


def retrieval_metrics(result: RetrievalResult) -> dict[str, int]:
    return {
        "brain_candidate_count": len(result.receipt.candidate_pool),
        "brain_selected_count": len(result.receipt.selected),
        "brain_expanded_count": len(result.receipt.expanded),
        "brain_expanded_bytes": sum(len(body) for body in result.bodies.values()),
        # No evidence or grounding field exists here by design.
    }
