"""Shallow-fitness battery: N live cases against the MINI compact wire contract.

A model that fails the full V6 production battery may still be able to serve
the reduced (MiniReason) engine.  This battery decides that question with a
small, announced, bounded number of live provider calls: each case is one
MiniReason-style compact conjecture call through the shared ``call`` kernel,
using mini's own bounded-repair protocol (one initial generation plus at most
two repairs).  Only sanitized case outcomes leave this module — raw provider
content is written to a temporary blob store that is deleted before return.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

from deepreason.provider_profile import ProviderProfileV1, credential_present
from deepreason.qualification import (
    SHALLOW_FITNESS_CASES,
    SHALLOW_FITNESS_MAX_REPAIRS,
    QualificationError,
    ShallowFitnessCaseResultV1,
)

# One case may spend the initial generation plus mini's two bounded repairs.
SHALLOW_FITNESS_MAX_PROVIDER_CALLS = SHALLOW_FITNESS_CASES * (
    SHALLOW_FITNESS_MAX_REPAIRS + 1
)
# Generous hard ceiling for the entire battery; the per-call completion bound
# comes from the profile's own maximum_completion_tokens.
SHALLOW_FITNESS_TOKEN_BUDGET = 60_000

_CASE_TOPICS = (
    "why independent checks can improve reliability",
    "why a recurring failure can survive repeated fixes",
    "why two rival mechanisms can fit the same observation",
    "why a bounded schedule can miss its deadline",
    "why a cached result can silently go stale",
    "why a measurement can drift between environments",
)
assert len(_CASE_TOPICS) == SHALLOW_FITNESS_CASES


def shallow_fitness_maximum_provider_calls() -> int:
    """Return the frozen worst-case shallow-fitness call count."""

    return SHALLOW_FITNESS_MAX_PROVIDER_CALLS


def _case_prompt(case_index: int) -> str:
    """Render one bounded, representative MiniReason conjecture task.

    The wording mirrors mini's own generate prompt: propose criticizable
    explanations with typicality estimates.  The shared ``call`` kernel
    prepends the exact wire schema and syntax example, so this text carries
    only the task.
    """

    topic = _CASE_TOPICS[case_index]
    return (
        f"Shallow-fitness case {case_index + 1:03d}. You are the conjecture "
        "operator: propose bold, criticizable explanations for the PROBLEM "
        "below. Return a distribution of 2 diverse candidates, each with a "
        "typicality estimate in [0,1]. Each candidate's content is one short "
        "self-contained explanatory mechanism.\n\n"
        f"PROBLEM: Explain {topic}."
    )


def _failure_code(error: BaseException) -> str:
    code = str(getattr(error, "code", "") or "").strip().upper()
    if code and all(item.isalnum() or item == "_" for item in code):
        return code[:128]
    name = error.__class__.__name__
    normalized = "".join(
        ("_" + item if item.isupper() and index else item.upper())
        for index, item in enumerate(name)
        if item.isalnum()
    )
    return (normalized or "SHALLOW_FITNESS_CASE_FAILED")[:128]


def _profile_endpoint(profile: ProviderProfileV1, environment: Mapping[str, str]):
    from minireason.call import HttpEndpoint

    return HttpEndpoint(
        profile.endpoint,
        profile.model_id,
        api_key=environment[profile.credential_env],
        max_tokens=profile.maximum_completion_tokens,
    )


def run_shallow_fitness_battery(
    profile: ProviderProfileV1,
    *,
    environ: Mapping[str, str] | None = None,
    endpoint=None,
) -> tuple[ShallowFitnessCaseResultV1, ...]:
    """Run the complete battery; return sanitized outcomes or fail closed.

    A schema-invalid case is a recorded negative outcome.  A transport or
    budget failure is NOT an outcome: it aborts the battery with a typed
    error so no durable tier is concluded from an outage.
    """

    from deepreason.llm.contracts import ConjecturerOutput
    from deepreason.llm.profiles import ModelProfile
    from deepreason.llm.wire import ReferenceFreeConjecturerWireContract
    from minireason.call import (
        BudgetExceeded,
        EndpointError,
        SchemaError,
        TokenMeter,
        call,
    )
    from minireason.log import BlobStore

    if endpoint is None:
        environment = os.environ if environ is None else environ
        if not credential_present(profile, environ=environment):
            raise QualificationError(
                "PROVIDER_CREDENTIAL_MISSING",
                "configured provider credential is absent",
            )
        endpoint = _profile_endpoint(profile, environment)

    meter = TokenMeter(SHALLOW_FITNESS_TOKEN_BUDGET)
    cases: list[ShallowFitnessCaseResultV1] = []
    with tempfile.TemporaryDirectory(prefix="deepreason-shallow-fitness-") as scratch:
        blobs = BlobStore(Path(scratch) / "blobs")
        for case_index in range(SHALLOW_FITNESS_CASES):
            case_id = f"case-{case_index + 1:03d}"
            try:
                _output, spend = call(
                    endpoint,
                    _case_prompt(case_index),
                    ConjecturerOutput,
                    meter,
                    blobs,
                    retry_max=SHALLOW_FITNESS_MAX_REPAIRS,
                    role="conjecturer",
                    model_profile=ModelProfile.COMPACT,
                    wire_contract=ReferenceFreeConjecturerWireContract(),
                )
            except SchemaError as error:
                cases.append(
                    ShallowFitnessCaseResultV1(
                        case_id=case_id,
                        first_pass_valid=False,
                        eventual_valid=False,
                        repair_count=SHALLOW_FITNESS_MAX_REPAIRS,
                        failure_code=_failure_code(error),
                    )
                )
                continue
            except (EndpointError, BudgetExceeded):
                raise QualificationError(
                    "QUALIFICATION_SHALLOW_EXECUTION_FAILED",
                    "the shallow-fitness battery did not complete; "
                    "no qualification tier was recorded",
                ) from None
            attempts = max(1, int(getattr(spend, "attempts", 1) or 1))
            cases.append(
                ShallowFitnessCaseResultV1(
                    case_id=case_id,
                    first_pass_valid=attempts == 1,
                    eventual_valid=True,
                    repair_count=min(attempts - 1, SHALLOW_FITNESS_MAX_REPAIRS),
                )
            )
    return tuple(cases)


__all__ = [
    "SHALLOW_FITNESS_MAX_PROVIDER_CALLS",
    "SHALLOW_FITNESS_TOKEN_BUDGET",
    "run_shallow_fitness_battery",
    "shallow_fitness_maximum_provider_calls",
]
