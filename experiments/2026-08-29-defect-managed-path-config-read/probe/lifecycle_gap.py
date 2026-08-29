"""Does a CARRIED configuration still have a lifecycle? Measured, offline.

Re-runnable:

    PYTHONPATH=src:mini python \
      experiments/2026-08-29-defect-managed-path-config-read/probe/lifecycle_gap.py

PRICE.md measured that carriage MOVES the qualification subject digest and
priced that move as one battery per home. This probe asks the question the
price presupposes: can that battery ever be RUN for a configured subject?

`deepreason reason` prepares through `RunPreparationService()` with
`qualification_executor=None`, so a subject the cache does not hold is a typed
REFUSAL, not an automatic battery (`qualification.py:804-818`). The battery is
run only by `deepreason qualify`, whose subject comes from
`preparation.qualification_subject_manifest(profile, ...)`.

Exit code 0 always: this is a measurement, not a test.
"""

from __future__ import annotations

import inspect
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from deepreason import preparation  # noqa: E402
from deepreason.cli.doctor import (  # noqa: E402
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.config import Config, load as load_config  # noqa: E402
from deepreason.preparation import (  # noqa: E402
    build_preparation_manifest,
    qualification_subject_manifest,
)
from deepreason.provider_profile import ProviderProfileV1  # noqa: E402
from deepreason.qualification import (  # noqa: E402
    QualificationError,
    qualification_subject_digest,
    resolve_completed_qualification,
)

QUESTION = "Why is the sky blue?"
STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

PROFILE_DERIVED = (
    "engine_profile",
    "model_profile",
    "scratchpad",
    "bridge",
    "EMBEDDER_MODEL",
    "CHANNELS_DISABLED",
    "roles",
)


def profile() -> ProviderProfileV1:
    return ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id="model-a",
        model_revision="rev-a",
        family="family-a",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )


def qualified_report(manifest):
    """A battery that passes every case, without a provider."""
    return run_production_contract_doctor(
        manifest,
        case_executor=lambda _m, _pair, index: ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}",
            first_pass_valid=True,
            eventual_valid=True,
            repair_count=0,
            semantic_admission=True,
        ),
    )


def carried_manifest(operator: Config, prof: ProviderProfileV1):
    """The managed manifest as it would be if the operator's Config were read."""
    original = preparation._config_for_profile

    def carried(p, **kwargs):
        synthesised = original(p, **kwargs).model_dump(mode="python")
        merged = operator.model_dump(mode="python")
        for key in PROFILE_DERIVED:
            merged[key] = synthesised[key]
        return Config.model_validate(merged)

    preparation._config_for_profile = carried
    try:
        return build_preparation_manifest(prof, question=QUESTION, compiled_at=STAMP)
    finally:
        preparation._config_for_profile = original


def main() -> int:
    prof = profile()

    print("== 1. What `deepreason qualify` can address ==")
    signature = inspect.signature(qualification_subject_manifest)
    print(f"  qualification_subject_manifest{signature}")
    print(
        "  config parameter         "
        + ("PRESENT" if "config" in signature.parameters else "ABSENT")
    )
    print()

    qualify_manifest = qualification_subject_manifest(prof)
    qualify_subject = qualification_subject_digest(qualify_manifest, prof)
    reason_manifest = build_preparation_manifest(
        prof, question=QUESTION, compiled_at=STAMP
    )
    reason_subject = qualification_subject_digest(reason_manifest, prof)

    print("== 2. The reuse property that makes `qualify` once / `reason` many work ==")
    print(f"  qualify subject          {qualify_subject}")
    print(f"  reason subject (today)   {reason_subject}")
    print(
        "  verdict                  "
        + ("SAME -- one battery serves every question" if qualify_subject == reason_subject
           else "DIFFERENT -- the reuse property does not hold today")
    )
    print()

    with tempfile.TemporaryDirectory() as raw:
        cache = Path(raw)
        # Stand in for a home that has already run `deepreason qualify --yes`
        # and passed: the completed bundle for the qualify subject is cached.
        resolve_completed_qualification(
            qualify_manifest, prof, cache_dir=cache, executor=qualified_report
        )
        print("== 3. A fully qualified home, then a CONFIGURED reason run ==")
        print(f"  cache holds              {qualify_subject}")
        print()

        # Control: an unconfigured reason run on that same home starts.
        try:
            resolve_completed_qualification(reason_manifest, prof, cache_dir=cache)
            control = "STARTS (cache hit)"
        except QualificationError as error:
            control = f"REFUSED {error.code}"
        print(f"  CONTROL  reason, no --config          {control}")
        print()

        configs = sorted(REPO.glob("experiments/*/run-config.yaml"))
        refused = 0
        for path in configs:
            operator = load_config(path)
            try:
                manifest = carried_manifest(operator, prof)
            except Exception as error:
                print(f"  {path.parent.name}")
                print(f"    carriage                            COMPILE-ERROR {type(error).__name__}")
                continue
            subject = qualification_subject_digest(manifest, prof)
            try:
                resolve_completed_qualification(manifest, prof, cache_dir=cache)
                verdict = "STARTS (cache hit)"
            except QualificationError as error:
                verdict = f"REFUSED {error.code}"
                refused += 1
            print(f"  {path.parent.name}")
            print(f"    subject                             {subject[:16]}...")
            print(f"    reason --config <this file>         {verdict}")
        print()
        print(
            f"== VERDICT: {refused} of {len(configs)} committed configurations are "
            "REFUSED on a fully qualified home =="
        )
        print(
            "   and `deepreason qualify` has no parameter that could address their\n"
            "   subject, so the refusal is not clearable by any committed command."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
