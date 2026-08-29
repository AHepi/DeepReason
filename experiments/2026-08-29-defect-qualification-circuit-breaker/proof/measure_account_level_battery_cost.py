#!/usr/bin/env python3
"""Generate the evidence the dispatch's own citation could not supply.

The symptom P7-A was dispatched to fix has NO surviving committed instance:
the file the brief named records an HTTP 401, which is not retryable, so the
backoff ladder never slept and that battery took about a minute -- not the
eighteen the audit reported. See FIX.md section 3.

So the evidence is generated instead of cited. This is the real doctor, the
real qualification-subject manifest, the real endpoint and the real retry
ladder. EXACTLY TWO symbols are faked and nothing else:

  1. `endpoints.urllib.request.urlopen` -- raises a scripted HTTPError and
     counts the call.
  2. `endpoints.time` -- a shim whose `sleep` records the mandated delay and
     returns immediately. The module ATTRIBUTE is replaced, never
     `time.sleep` itself, so the real clock is untouched process-wide.

Everything between them is shipped code: exercise_production_contract_case ->
_endpoint_from_spec -> OpenAICompatEndpoint.complete -> request_with_retries.

No credential is needed (`credential_env` names a variable no environment
defines, so `api_key` is None)
and the model id is concrete, so `resolve_model` never touches the network.

Run:
    python experiments/2026-08-29-defect-qualification-circuit-breaker/proof/\
measure_account_level_battery_cost.py
"""

from __future__ import annotations

import collections
import urllib.error
import urllib.request

from deepreason.cli import doctor
from deepreason.cli.doctor import (
    QualificationCircuitPolicyV1,
    production_contract_pairs,
    run_production_contract_doctor,
)
from deepreason.llm import endpoints as endpoints_module
from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import ProviderProfileV1

STATUSES = (401, 429)


class _Clock:
    """Stands in for the `time` module inside endpoints only."""

    def __init__(self) -> None:
        self.sleeps: list[float] = []

    def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)

    def __getattr__(self, name):  # any other time.* stays real
        import time as _real_time

        return getattr(_real_time, name)


def _profile() -> ProviderProfileV1:
    return ProviderProfileV1.create(
        provider="ollama",
        endpoint="https://example.invalid/v1",
        model_id="glm-5.2",
        model_revision="rev-1",
        family="glm",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        # A name no environment defines, so the endpoint builds with a None
        # api_key and the scripted urlopen is reached without a credential.
        credential_env="DEEPREASON_P7A_PROOF_ABSENT_KEY",
    )


def _pre_fix_failure_code(error: BaseException) -> str:
    """`_failure_code` EXACTLY as it stood before this tranche.

    Kept here, not imported, because the defect this file documents is the
    absence of the two branches the fix adds: without them every transport
    condition normalises the CLASS NAME and collapses to ENDPOINT_ERROR.
    Reproducing the collapse is the only way this file can show that a 401
    and a 429 once wrote byte-identical records.
    """

    code = str(getattr(error, "code", "") or "").strip().upper()
    if code and all(character.isalnum() or character == "_" for character in code):
        return code[:128]
    name = error.__class__.__name__
    normalized = "".join(
        ("_" + character if character.isupper() and index else character.upper())
        for index, character in enumerate(name)
        if character.isalnum()
    )
    return (normalized or "PRODUCTION_CONTRACT_FAILED")[:128]


def _measure(manifest, status: int, *, breaker: bool, legible: bool = True):
    calls: list[str] = []
    clock = _Clock()

    def fake_urlopen(request, timeout=None):
        calls.append(getattr(request, "full_url", "?"))
        raise urllib.error.HTTPError(
            "https://example.invalid/v1", status, "scripted account-level condition",
            {}, None,
        )

    real_urlopen = urllib.request.urlopen
    real_time = endpoints_module.time
    real_failure_code = doctor._failure_code
    urllib.request.urlopen = fake_urlopen
    endpoints_module.time = clock
    if not legible:
        doctor._failure_code = _pre_fix_failure_code
    try:
        report = run_production_contract_doctor(
            manifest,
            concurrency=1,
            circuit_policy=QualificationCircuitPolicyV1(enabled=breaker),
        )
    finally:
        urllib.request.urlopen = real_urlopen
        endpoints_module.time = real_time
        doctor._failure_code = real_failure_code

    codes: collections.Counter[str] = collections.Counter()
    for pair_report in report.pairs:
        for case in pair_report.cases + (pair_report.first_draw_cases or ()):
            codes[case.failure_code] += 1
    return report, calls, clock.sleeps, codes


def main() -> int:
    manifest = qualification_subject_manifest(_profile())
    pairs = production_contract_pairs(manifest)
    print(f"qualification subject: {len(pairs)} route/contract pairs")
    print(f"cases per pair: {doctor.PRODUCTION_CASES_PER_PAIR}")
    print()

    # Three modes, not two: the defect is only visible with the legibility
    # branches removed as well, because after this tranche a 401 and a 429
    # no longer write the same code even with the breaker off.
    modes = (
        ("PRE-FIX  ", dict(breaker=False, legible=False)),
        ("BREAKER  ", dict(breaker=True, legible=True)),
    )
    rows = {}
    for label, kwargs in modes:
        for status in STATUSES:
            report, calls, sleeps, codes = _measure(manifest, status, **kwargs)
            rows[(status, label)] = (len(calls), sum(sleeps), codes)
            print(
                f"{label} status={status} cases={report.summary.case_count} "
                f"http_calls={len(calls)} sleeps={len(sleeps)} "
                f"mandated_wait_s={sum(sleeps):g} "
                f"re_exercised={report.summary.re_exercised_pair_count}"
            )
            print(f"    record: {dict(codes)}")
            openings = report.circuit_breaker.openings if report.circuit_breaker else ()
            print(
                "    open circuits: "
                + str({o.endpoint_id: o.failure_code for o in openings})
            )
    print()

    pre_401, pre_429 = rows[(401, "PRE-FIX  ")], rows[(429, "PRE-FIX  ")]
    fix_401, fix_429 = rows[(401, "BREAKER  ")], rows[(429, "BREAKER  ")]

    print("THE DEFECT (pre-fix):")
    print(
        f"    mandated wait differs by {pre_429[1] - pre_401[1]:g}s "
        f"({(pre_429[1] - pre_401[1]) / 60:.1f} min) -- one condition clears "
        f"on its own, the other never will"
    )
    print(
        f"    records BYTE-IDENTICAL? {pre_401[2] == pre_429[2]}"
        f"  -> {dict(pre_401[2])}"
    )
    print("THE FIX:")
    print(
        f"    http calls {pre_401[0]} -> {fix_401[0]} (401), "
        f"{pre_429[0]} -> {fix_429[0]} (429)"
    )
    print(f"    mandated wait {pre_429[1]:g}s -> {fix_429[1]:g}s")
    print(f"    records still identical? {fix_401[2] == fix_429[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
