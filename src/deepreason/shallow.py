"""Explicit reduced-engine ("shallow") public reasoning entry.

Shallow mode runs the MiniReason generate/check/rotate loop against the
configured provider profile. It exists for two declared purposes: an
explicit low-cost option for end users, and the supported fallback for
small models that cannot complete production qualification. It never
consults or writes the qualification cache, and its result is always
labeled as shallow so it cannot be mistaken for a qualified V6 inquiry.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.provider_profile import (
    ProviderProfileV1,
    credential_present,
    provider_state_dir,
    resolve_provider_profile,
)

SHALLOW_RESULT_SCHEMA = "deepreason-shallow-result.v1"
SHALLOW_DEFAULT_TOKEN_BUDGET = 30_000
SHALLOW_MAX_TOKEN_BUDGET = 200_000
SHALLOW_DEFAULT_MAX_CYCLES = 64
SHALLOW_DISCLAIMER = (
    "shallow reduced-engine result: generate/check/rotate only, no V6 "
    "qualification, transactions, or terminal commitment authority"
)


class ShallowReasonError(ValueError):
    """Stable coded failure raised before or during a shallow run."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _shallow_runs_dir(environ: Mapping[str, str] | None = None) -> Path:
    return provider_state_dir(environ=environ) / "shallow-runs"


def _mint_run_id(question: str, *, now: str) -> str:
    digest = sha256_hex(
        canonical_json({"question": question, "started": now})
        + os.urandom(8)
    )
    return f"shallow-{digest[:24]}"


def _endpoint(profile: ProviderProfileV1, key: str):
    from minireason.call import HttpEndpoint

    return HttpEndpoint(
        profile.endpoint,
        profile.model_id,
        api_key=key,
        max_tokens=profile.maximum_completion_tokens,
    )


def run_shallow_question(
    question: str,
    *,
    cycles: int | None = None,
    token_budget: int | None = None,
    profile_path: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict:
    """Run one clearly-labeled shallow inquiry; return the summary payload."""

    question = (question or "").strip()
    if not question:
        raise ShallowReasonError("SHALLOW_QUESTION_REQUIRED", "provide one question")
    budget = SHALLOW_DEFAULT_TOKEN_BUDGET if token_budget is None else int(token_budget)
    if not 1 <= budget <= SHALLOW_MAX_TOKEN_BUDGET:
        raise ShallowReasonError(
            "SHALLOW_BUDGET_INVALID",
            f"token budget must be within 1..{SHALLOW_MAX_TOKEN_BUDGET}",
        )
    max_cycles = SHALLOW_DEFAULT_MAX_CYCLES if cycles is None else int(cycles)
    if max_cycles < 1:
        raise ShallowReasonError("SHALLOW_CYCLES_INVALID", "cycles must be positive")

    try:
        resolved = resolve_provider_profile(profile_path, environ=environ)
    except ValueError as error:
        raise ShallowReasonError(
            "SHALLOW_PROFILE_UNAVAILABLE", str(error)
        ) from error
    profile = resolved.profile
    environment = os.environ if environ is None else environ
    if not credential_present(profile, environ=environment):
        raise ShallowReasonError(
            "SHALLOW_CREDENTIAL_MISSING",
            f"set {profile.credential_env} or rerun deepreason setup",
        )

    try:
        from minireason.loop import run as mini_run
    except ImportError as error:  # pragma: no cover - packaging regression only
        raise ShallowReasonError(
            "MINI_ENGINE_UNAVAILABLE",
            "the minireason reduced engine is not installed",
        ) from error

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    run_id = _mint_run_id(question, now=now)
    root = _shallow_runs_dir(environ=environ) / run_id
    root.mkdir(parents=True, exist_ok=False)
    problem_id = f"q-{sha256_hex(canonical_json(question))[:12]}"

    summary = mini_run(
        [(problem_id, question)],
        _endpoint(profile, environment[profile.credential_env]),
        budget=budget,
        root=root,
        max_cycles=max_cycles,
    )
    return {
        "schema": SHALLOW_RESULT_SCHEMA,
        "mode": "shallow",
        "disclaimer": SHALLOW_DISCLAIMER,
        "run_id": run_id,
        "question_problem_id": problem_id,
        "provider": profile.provider,
        "model_id": profile.model_id,
        "summary": summary,
    }


__all__ = [
    "SHALLOW_DEFAULT_MAX_CYCLES",
    "SHALLOW_DEFAULT_TOKEN_BUDGET",
    "SHALLOW_DISCLAIMER",
    "SHALLOW_MAX_TOKEN_BUDGET",
    "SHALLOW_RESULT_SCHEMA",
    "ShallowReasonError",
    "run_shallow_question",
]
