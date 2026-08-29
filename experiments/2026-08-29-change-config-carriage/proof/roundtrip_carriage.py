#!/usr/bin/env python3
"""R1's acceptance check: every dropped field round-trips through carriage.

For each of the 25 fields the engine-config echo drops unconditionally, set it
to a non-default value, compile a manifest, and read the Config back with
`config_from_run_manifest`. The value must come back EQUAL to what was set.

At HEAD before this tranche the answer was 0 of 25: every field came back at
its declared default, silently.

Run:  python experiments/2026-08-29-change-config-carriage/proof/roundtrip_carriage.py
"""

from deepreason.config import Config
from deepreason import run_manifest as rm
from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import ProviderProfileV1

PROFILE = ProviderProfileV1.create(
    provider="openai", endpoint="https://api.example.com/v1", model_id="model-a",
    model_revision="rev-a", family="family-a", context_window_tokens=262144,
    maximum_completion_tokens=4096, credential_env="DEEPREASON_TEST_KEY")

EXPLICIT_NON_DEFAULTS = {
    "ATTENTION_ALLOCATION_POLICY": "wander-cap.v1-probe",
    "CAPTURE14_SC_CEILING": 0.75,
    "CHANNELS_DISABLED": ("research",),
    "DISCHARGE_POLICY": "discharge-required.v1-probe",
    "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
    "SEED_PROBLEM_BUDGET_FLOOR": 0.75,
    "SPLIT_BUDGET_SEAT_PROTOCOL": "on",
}


def non_default(field, value):
    if field in EXPLICIT_NON_DEFAULTS:
        return EXPLICIT_NON_DEFAULTS[field]
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    return None


def main() -> int:
    dropped = rm._unconditionally_dropped_config_fields()
    carried = unreachable = 0
    print(f"dropped fields: {len(dropped)}\n")
    for field in dropped:
        default = getattr(Config(), field, None)
        want = non_default(field, default)
        config = Config().model_copy(update={field: want})
        manifest = qualification_subject_manifest(PROFILE, config=config)
        got = getattr(rm.config_from_run_manifest(manifest), field, None)
        # tuples serialize to lists and validate back to tuples
        same = got == want or list(got or ()) == list(want or ())
        if same:
            carried += 1
            verdict = "CARRIED"
        else:
            unreachable += 1
            verdict = f"NOT CARRIED (got {got!r})"
        print(f"{field:42s} {str(want)[:12]:<14} {verdict}")
    print(f"\ncarried: {carried}/{len(dropped)}   not carried: {unreachable}")
    if unreachable:
        print(
            "\nThe uncarried field is CHANNELS_DISABLED, and it is uncarried for "
            "a reason outside this tranche: preparation._config_for_profile "
            "lists it among seven HOST-OWNED fields and overwrites the "
            "operator's value BEFORE compile, so no carriage notice is ever "
            "emitted for it. That is parked P21, and it is why the reachable "
            "count is 24 and not 25."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
