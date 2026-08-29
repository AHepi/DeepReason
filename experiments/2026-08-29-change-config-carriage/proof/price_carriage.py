#!/usr/bin/env python3
"""Re-measure road A's qualification price, field by field.

Re-runnable, offline, no provider. For every field the engine-config echo
drops UNCONDITIONALLY, set it to a non-default value and report two things:

  * whether the QUALIFICATION SUBJECT DIGEST moves, and
  * which compile notices the manifest carries.

Why the subject digest is the price. A home requalifies -- one battery,
about fourteen minutes -- exactly when its subject digest changes. So
"what does carriage cost?" is answerable before carriage exists: it is
whichever fields already move that digest, plus whichever the carrier
would newly move.

Why carriage through the NOT_CARRIED notice is free. `qualification.py`
`qualification_subject_payload` strips every `ENGINE_CONFIG_FIELD_NOT_CARRIED`
notice out of the subject before digesting it, and pops the key entirely
when nothing else remains. A value riding that notice is therefore invisible
to the subject by construction, not by luck.

Run:  python experiments/2026-08-29-change-config-carriage/proof/price_carriage.py
"""

from deepreason.config import Config
from deepreason import run_manifest as rm
from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import qualification_subject_digest

PROFILE = ProviderProfileV1.create(
    provider="openai",
    endpoint="https://api.example.com/v1",
    model_id="model-a",
    model_revision="rev-a",
    family="family-a",
    context_window_tokens=262144,
    maximum_completion_tokens=4096,
    credential_env="DEEPREASON_TEST_KEY",
)


def subject(**updates):
    config = Config().model_copy(update=updates) if updates else Config()
    manifest = qualification_subject_manifest(PROFILE, config=config)
    return qualification_subject_digest(manifest, PROFILE), manifest


# Explicit non-default values for the fields whose type has no arithmetic
# successor. Every one is a value the field's own annotation admits, so the
# measurement covers all 25 dropped fields and not just the countable ones --
# a partial census here would understate the price by construction.
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
    """A different value the field's annotation admits."""
    if field in EXPLICIT_NON_DEFAULTS:
        return EXPLICIT_NON_DEFAULTS[field]
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    return None


def main() -> int:
    dropped = rm._unconditionally_dropped_config_fields()
    base, base_manifest = subject()
    print(f"dropped fields: {len(dropped)}")
    print(f"base subject digest: {base}")
    print(f"base compile notices: {[n.code for n in (base_manifest.compile_notices or ())]}")
    print()
    moved, same, skipped = [], [], []
    for field in dropped:
        default = getattr(Config(), field, None)
        value = non_default(field, default)
        if value is None:
            skipped.append(field)
            print(f"{field:42s} SKIP  (no non-default of this type)")
            continue
        try:
            digest, manifest = subject(**{field: value})
        except Exception as error:  # a typed refusal is a result, not a gap
            skipped.append(field)
            print(f"{field:42s} REFUSED {type(error).__name__}: {error}")
            continue
        codes = [n.code for n in (manifest.compile_notices or ())]
        verdict = "SAME " if digest == base else "MOVED"
        (same if digest == base else moved).append(field)
        print(f"{field:42s} {str(default)[:6]:>6} -> {str(value)[:6]:<6} {verdict} notices={codes}")
    print()
    print(f"MOVED   ({len(moved)}): {moved}")
    print(f"SAME    ({len(same)}): {len(same)} fields")
    print(f"SKIPPED ({len(skipped)}): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
