"""Pure client parsing helpers that produce the shared typed vocabulary."""

from __future__ import annotations

from deepreason.application.models import (
    ContinueTextRunIntentV1,
    RunBudgetIntentV1,
    StartTextRunIntentV1,
)


def budget_intent(cycles, token_budget) -> RunBudgetIntentV1:
    def normalized(value, *, tokens: bool):
        if isinstance(value, str):
            value = value.strip().casefold()
            if value == "unlimited" or (tokens and value == "0"):
                return "unlimited"
            value = int(value)
        if tokens and value == 0:
            return "unlimited"
        return value

    return RunBudgetIntentV1(
        cycles=normalized(cycles, tokens=False),
        token_budget=normalized(token_budget, tokens=True),
    )


def start_text_run_intent(
    *, root, workload, run_manifest_ref, cycles, token_budget, experimental_v5=False
) -> StartTextRunIntentV1:
    return StartTextRunIntentV1(
        root=str(root),
        workload=workload,
        run_manifest_ref=str(run_manifest_ref),
        budget=budget_intent(cycles, token_budget),
        experimental_v5=experimental_v5,
    )


def continue_text_run_intent(
    *, root, cycles, token_budget, expected_manifest_digest=None, experimental_v5=False
) -> ContinueTextRunIntentV1:
    return ContinueTextRunIntentV1(
        root=str(root),
        budget=budget_intent(cycles, token_budget),
        expected_manifest_digest=expected_manifest_digest,
        experimental_v5=experimental_v5,
    )


__all__ = [
    "budget_intent",
    "continue_text_run_intent",
    "start_text_run_intent",
]
