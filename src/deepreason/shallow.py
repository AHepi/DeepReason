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
SHALLOW_SEAT_PLUGINS_SCHEMA = "deepreason-shallow-seat-plugins.v1"
SHALLOW_SEAT_PLUGINS_RECORD = "seat-plugins.json"
SHALLOW_DEFAULT_TOKEN_BUDGET = 30_000
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


def _record_operator_plugins(root: Path, environ: Mapping[str, str]) -> dict:
    """Load the operator's own section plugins, and record BOTH lists.

    Called once per run, during setup, before the first call -- a plugin
    registered after a brief was rendered would be a section the run says it
    had and did not.

    Neither list may be dropped. `loaded` is what this run's briefs can
    actually reach; `notices` is why the rest cannot. A run that silently
    omitted the second would leave the operator looking at a brief missing a
    section with no reason given, which is the failure the loader exists to
    prevent (all-configurations law: disclose, never die).
    """

    from deepreason.llm.seat_sections import load_operator_plugins

    loaded, notices = load_operator_plugins(environ=environ)
    record = {
        "schema": SHALLOW_SEAT_PLUGINS_SCHEMA,
        "loaded": list(loaded),
        "notices": [dict(notice) for notice in notices],
    }
    (root / SHALLOW_SEAT_PLUGINS_RECORD).write_text(
        canonical_json(record).decode("utf-8"), encoding="utf-8"
    )
    return record


def _load_frozen_input(run_input_root: Path | str):
    """Read the STANDARD frozen input: the record `deepreason input freeze`
    writes, and the one the full harness takes.

    R12's "standard" is this artifact and no other. A v1 manifest is refused
    rather than widened: v1 carries no criteria in the shape v2 does, so
    accepting one would mean a run silently answering a differently-shaped
    question.

    A dossier carrying evidence SOURCES is refused too, with its own code. The
    blobs it names would have to be staged into the run root before the record
    could be bound there, and staging them is not built. This is an
    impossibility surfacing at the point of use, which is where the
    all-configurations law says it belongs -- not a configuration refused at
    compile.
    """

    from deepreason.evidence import (
        RunInputManifestV2,
        load_evidence_dossier,
        load_run_input,
    )
    from deepreason.evidence.state import RunInputError

    path = Path(run_input_root)
    try:
        run_input = load_run_input(path)
        dossier = load_evidence_dossier(path)
    except (OSError, RunInputError, ValueError) as error:
        raise ShallowReasonError(
            "SHALLOW_RUN_INPUT_UNREADABLE",
            f"{path} does not hold a readable frozen input: {error}",
        ) from error
    if not isinstance(run_input, RunInputManifestV2):
        raise ShallowReasonError(
            "SHALLOW_RUN_INPUT_VERSION",
            "the reduced engine takes run-input-manifest.v2, the same record "
            f"the full harness takes; {path} holds {run_input.schema_}",
        )
    if dossier.sources:
        raise ShallowReasonError(
            "SHALLOW_RUN_INPUT_HAS_EVIDENCE",
            f"{path}'s dossier names {len(dossier.sources)} evidence "
            "source(s); staging their blobs into a reduced-engine run root is "
            "not built, so the record could not be bound there truthfully",
        )
    return run_input, dossier


def _run_input_report(frozen) -> dict:
    """What the run was started from, said in the result rather than implied.

    The criteria count carries a NOTICE when it is non-zero: the reduced
    engine binds the frozen record to its root, so the criteria are in the
    run's identity, but it does not yet compile them into commitments. A
    reader who saw only the count would reasonably assume it did.
    """

    if frozen is None:
        return {"source": "question", "criteria": 0, "notices": []}
    notices = []
    if frozen.problem.criteria:
        notices.append(
            {
                "code": "SHALLOW_RUN_INPUT_CRITERIA_NOT_COMPILED",
                "detail": (
                    f"{len(frozen.problem.criteria)} frozen criterion/criteria "
                    "are bound to this root's identity but are not compiled "
                    "into commitments by the reduced engine"
                ),
            }
        )
    return {
        "source": "frozen-input",
        "problem_id": frozen.problem.id,
        "run_input_digest": frozen.run_input_digest,
        "criteria": len(frozen.problem.criteria),
        "notices": notices,
    }


def _endpoint(profile: ProviderProfileV1, key: str):
    from minireason.call import HttpEndpoint

    return HttpEndpoint(
        profile.endpoint,
        profile.model_id,
        api_key=key,
        max_tokens=profile.maximum_completion_tokens,
    )


def run_shallow_question(
    question: str | None = None,
    *,
    cycles: int | None = None,
    token_budget: int | None = None,
    profile_path: Path | str | None = None,
    run_input_root: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict:
    """Run one clearly-labeled shallow inquiry; return the summary payload.

    Two starting inputs, and the second is the point of `run_input_root`: a
    bare question, exactly as before, or the STANDARD frozen input -- problem
    plus criteria -- that `deepreason input freeze` writes and the full
    harness takes. When one is supplied it decides the problem's id and its
    description, and it is bound to the run root instead of mini's constant
    process root.
    """

    frozen = None
    if run_input_root is not None:
        frozen, frozen_dossier = _load_frozen_input(run_input_root)
        supplied = (question or "").strip()
        if supplied and supplied != frozen.problem.description:
            raise ShallowReasonError(
                "SHALLOW_QUESTION_CONFLICTS_WITH_RUN_INPUT",
                "a frozen input already states the question; passing a "
                "different one would leave the record saying two things",
            )
        question = frozen.problem.description
    question = (question or "").strip()
    if not question:
        raise ShallowReasonError("SHALLOW_QUESTION_REQUIRED", "provide one question")
    budget = SHALLOW_DEFAULT_TOKEN_BUDGET if token_budget is None else int(token_budget)
    if budget < 1:
        raise ShallowReasonError(
            "SHALLOW_BUDGET_INVALID",
            "token budget must be positive",
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
    seat_plugins = _record_operator_plugins(root, environment)
    problem_id = (
        frozen.problem.id
        if frozen is not None
        else f"q-{sha256_hex(canonical_json(question))[:12]}"
    )

    # The frozen input is passed only when there IS one, so the bare-question
    # path calls the engine with exactly the arguments it always did. That is
    # the mechanical form of "the bare-question form keeps working unchanged":
    # a stub written against the old signature still serves it.
    frozen_binding = (
        {"run_input": frozen, "dossier": frozen_dossier} if frozen is not None else {}
    )
    summary = mini_run(
        [(problem_id, question)],
        _endpoint(profile, environment[profile.credential_env]),
        budget=budget,
        root=root,
        max_cycles=max_cycles,
        **frozen_binding,
    )
    stop = str(summary.get("stop", ""))
    return {
        "schema": SHALLOW_RESULT_SCHEMA,
        "mode": "shallow",
        # A run that died on the endpoint is a failure even when partial
        # work was logged; callers must not read it as a shallow answer.
        "completed": stop != "endpoint-error",
        "disclaimer": SHALLOW_DISCLAIMER,
        "run_id": run_id,
        "question_problem_id": problem_id,
        "provider": profile.provider,
        "model_id": profile.model_id,
        "seat_plugins": seat_plugins,
        "run_input": _run_input_report(frozen),
        "summary": summary,
    }


__all__ = [
    "SHALLOW_DEFAULT_MAX_CYCLES",
    "SHALLOW_DEFAULT_TOKEN_BUDGET",
    "SHALLOW_DISCLAIMER",
    "SHALLOW_RESULT_SCHEMA",
    "SHALLOW_SEAT_PLUGINS_RECORD",
    "SHALLOW_SEAT_PLUGINS_SCHEMA",
    "ShallowReasonError",
    "run_shallow_question",
]
