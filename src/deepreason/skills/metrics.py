"""Status-free process metrics for skill snapshots, retrieval, and adoption."""

from __future__ import annotations

from collections.abc import Iterable

from deepreason.skills.models import (
    AdoptionResult,
    SkillLibrarySnapshot,
    SkillMetrics,
    SkillRetrievalReceipt,
)


def skill_metrics(
    snapshots: Iterable[SkillLibrarySnapshot] = (),
    receipts: Iterable[SkillRetrievalReceipt] = (),
    adoptions: Iterable[AdoptionResult] = (),
) -> SkillMetrics:
    snapshot_rows = tuple(snapshots)
    receipt_rows = tuple(receipts)
    adoption_rows = tuple(adoptions)
    evaluations = tuple(
        evaluation for adoption in adoption_rows for evaluation in adoption.evaluations
    )
    return SkillMetrics(
        snapshots=len(snapshot_rows),
        retrievals=len(receipt_rows),
        ranked_capsules=sum(len(item.ranking) for item in receipt_rows),
        selected_capsules=sum(len(item.selected_bytes) for item in receipt_rows),
        blind_schools=sum(
            int(school.blind)
            for receipt in receipt_rows
            for school in receipt.school_slices
        ),
        revoiced_capsules=sum(len(item.summaries) for item in receipt_rows),
        adopted_tests=len(evaluations),
        adopted_passes=sum(item.verdict == "pass" for item in evaluations),
        adopted_failures=sum(item.verdict == "fail" for item in evaluations),
        adopted_overruns=sum(item.verdict == "overrun" for item in evaluations),
    )
