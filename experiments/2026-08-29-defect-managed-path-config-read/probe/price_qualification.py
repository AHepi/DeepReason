"""Price the qualification cost of admitting the operator Config into preparation.

Re-runnable, offline, deterministic:

    PYTHONPATH=src:mini python \
      experiments/2026-08-29-defect-managed-path-config-read/probe/price_qualification.py

The managed path today synthesises a Config from the provider profile
(`preparation._config_for_profile`). This probe measures, for every committed
`run-config.yaml` on the tree, what the qualification subject digest of the
MANAGED preparation manifest would become if the operator's own Config were the
base instead. It changes nothing: the carriage is simulated by patching
`_config_for_profile` for the duration of one compile, so the real code path
(`build_preparation_manifest` -> `compile_run_manifest`) is what produces every
manifest measured.

Exit code 0 always: this is a measurement, not a test.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from deepreason import preparation  # noqa: E402
from deepreason.config import Config, load as load_config  # noqa: E402
from deepreason.preparation import build_preparation_manifest  # noqa: E402
from deepreason.provider_profile import ProviderProfileV1  # noqa: E402
from deepreason.cli.doctor import (  # noqa: E402
    PRODUCTION_CASES_PER_PAIR,
    production_contract_pairs,
)
from deepreason.qualification import qualification_subject_digest  # noqa: E402
from deepreason.run_manifest import (  # noqa: E402
    _unconditionally_dropped_config_fields,
    config_from_run_manifest,
)

QUESTION = "Why is the sky blue?"
STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def profile() -> ProviderProfileV1:
    """The deterministic offline profile tests/test_run_preparation_service.py uses."""
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


PROFILE_DERIVED = (
    # Exactly the fields `preparation._config_for_profile` sets from the
    # provider profile. Carriage means: start from the operator's Config
    # instead of Config(), then let these seven win. Everything else is the
    # operator's. This is the SMALLEST carriage that could satisfy the goal,
    # so the price below is a FLOOR -- any wider carriage costs at least this.
    "engine_profile",
    "model_profile",
    "scratchpad",
    "bridge",
    "EMBEDDER_MODEL",
    "CHANNELS_DISABLED",
    "roles",
)


_UNSET = object()

# Fields whose alternative value is not derivable from the default's TYPE.
# Each value here is a real registered alternative, not an invented string:
# the two criticism/protocol Literals, the other registered discharge preset,
# a real declared evidence-channel id, and the one policy id `wander.py`
# registers beside the default (there is none, so the alternative is the
# unregistered-but-parseable form the all-configurations law admits).
_EXPLICIT_ALTERNATIVES = {
    "ENGAGED_CRITICISM_AUTHORITY": "defended_trial",
    "SPLIT_BUDGET_SEAT_PROTOCOL": "on",
    "DISCHARGE_POLICY": "off",
    "CHANNELS_DISABLED": ("research",),
    "ATTENTION_ALLOCATION_POLICY": "wander-cap.v2",
}


def _non_default_value(field, default):
    """A different, still-valid value for one Config field, or _UNSET."""
    if field in _EXPLICIT_ALTERNATIVES:
        return _EXPLICIT_ALTERNATIVES[field]
    if isinstance(default, bool):
        return not default
    if isinstance(default, int):
        return default + 1
    if isinstance(default, float):
        return _UNSET if default in (0.0, 1.0) else round(default / 2, 4)
    return _UNSET


def manifest_for(
    operator: Config | None,
    prof: ProviderProfileV1,
    *,
    only: tuple[str, ...] | None = None,
):
    """Compile the MANAGED preparation manifest, optionally carrying `operator`.

    ``only`` restricts carriage to those Config field names; everything else
    stays exactly as the provider profile synthesises it today.
    """
    if operator is None:
        return build_preparation_manifest(prof, question=QUESTION, compiled_at=STAMP)

    original = preparation._config_for_profile

    def carried(p, **kwargs):
        # Merge through model_validate, never model_copy: model_copy does not
        # revalidate, so a typed submodel (scratchpad, bridge) would be carried
        # as a bare dict and the serialised bytes would differ for that reason
        # alone -- a measurement artefact, not a price. The CONTROL row below
        # is what catches that mistake if it is ever reintroduced.
        synthesised = original(p, **kwargs).model_dump(mode="python")
        operator_data = operator.model_dump(mode="python")
        if only is None:
            merged = operator_data
            for key in PROFILE_DERIVED:
                merged[key] = synthesised[key]
        else:
            merged = dict(synthesised)
            for key in only:
                if key not in PROFILE_DERIVED:
                    merged[key] = operator_data[key]
        return Config.model_validate(merged)

    preparation._config_for_profile = carried
    try:
        return build_preparation_manifest(prof, question=QUESTION, compiled_at=STAMP)
    finally:
        preparation._config_for_profile = original


def main() -> int:
    prof = profile()
    base_manifest = manifest_for(None, prof)
    base_subject = qualification_subject_digest(base_manifest, prof)

    print("== BASELINE: the managed path as it is today ==")
    print(f"  manifest sha256          {base_manifest.sha256}")
    print(f"  source_config_hash       {base_manifest.source_config_hash}")
    print(f"  qualification subject    {base_subject}")
    print(f"  compile_notices          {base_manifest.compile_notices!r}")
    print()

    # Control: a Config with every field at its default must be free.
    default_manifest = manifest_for(Config(), prof)
    default_subject = qualification_subject_digest(default_manifest, prof)
    print("== CONTROL: carrying a DEFAULT-valued Config ==")
    print(f"  manifest sha256          {default_manifest.sha256}")
    print(f"  qualification subject    {default_subject}")
    print(
        "  verdict                  "
        + (
            "FREE (byte-identical to baseline)"
            if default_manifest.sha256 == base_manifest.sha256
            and default_subject == base_subject
            else "MOVED -- carriage is not free even at defaults"
        )
    )
    print()

    configs = sorted(REPO.glob("experiments/*/run-config.yaml"))
    print(f"== PRICE: {len(configs)} committed operator run-config.yaml files ==")
    print()
    moved = 0
    rows = []
    for path in configs:
        operator = load_config(path)
        try:
            carried_manifest = manifest_for(operator, prof)
        except Exception as error:  # a config the carriage cannot compile
            rows.append((path, "COMPILE-ERROR", type(error).__name__, str(error)[:120]))
            print(f"{path.parent.name}")
            print(f"  carriage             REFUSED {type(error).__name__}: {str(error)[:110]}")
            print()
            continue
        subject = qualification_subject_digest(carried_manifest, prof)
        subject_moved = subject != base_subject
        sha_moved = carried_manifest.sha256 != base_manifest.sha256
        moved += 1 if subject_moved else 0

        default = Config()
        differing = sorted(
            name
            for name in type(default).model_fields
            if getattr(operator, name) != getattr(default, name)
        )
        echo_now = json.loads(base_manifest.engine_config_json)
        echo_then = json.loads(carried_manifest.engine_config_json)
        echo_delta = sorted(
            k for k in set(echo_now) | set(echo_then)
            if echo_now.get(k) != echo_then.get(k)
        )
        notices = tuple(
            n.pointer for n in (carried_manifest.compile_notices or ())
            if n.code == "ENGINE_CONFIG_FIELD_NOT_CARRIED"
        )
        runtime = config_from_run_manifest(carried_manifest)
        actually_carried = sorted(
            name for name in differing
            if getattr(runtime, name, None) == getattr(operator, name)
        )

        rows.append((path, subject, sha_moved, subject_moved))
        print(f"{path.parent.name}")
        print(f"  fields set away from default   {len(differing)}: {', '.join(differing)}")
        print(f"  echo keys that would move      {len(echo_delta)}: {', '.join(echo_delta) or '(none)'}")
        print(f"  manifest sha256                {'MOVED' if sha_moved else 'unchanged'}  {carried_manifest.sha256[:16]}")
        print(f"  qualification subject          {'MOVED' if subject_moved else 'UNCHANGED'}  {subject[:16]}")
        print(f"  of those fields, carried to run time  {len(actually_carried)}: {', '.join(actually_carried) or '(none)'}")
        print(f"  ENGINE_CONFIG_FIELD_NOT_CARRIED notices {len(notices)}: {', '.join(notices) or '(none)'}")
        print()

    print("== VARIANT: carry ONLY the 25 fields the echo already drops ==")
    print("   (the cheapest carriage that could satisfy the operator law, because")
    print("    a dropped field never enters engine_config_json at all)")
    print()
    dropped = _unconditionally_dropped_config_fields()
    print(f"   drop set, derived from run_manifest itself: {len(dropped)} fields")
    print()
    narrow_moved = 0
    for path in configs:
        operator = load_config(path)
        narrow = manifest_for(operator, prof, only=dropped)
        subject = qualification_subject_digest(narrow, prof)
        subject_moved = subject != base_subject
        narrow_moved += 1 if subject_moved else 0
        print(
            f"  {path.parent.name:<46} subject "
            f"{'MOVED    ' if subject_moved else 'UNCHANGED'} {subject[:16]}"
        )
    print()

    print("== ISOLATION: each dropped field carried ALONE, at a non-default value ==")
    print("   MOVED means this one switch costs a home a qualification battery.")
    print()
    default = Config()
    isolated = {"free": [], "priced": [], "skipped": [], "refused": []}
    for field in dropped:
        if field in PROFILE_DERIVED:
            isolated["skipped"].append(
                f"{field} (profile-derived: `only=` carriage cannot reach it)"
            )
            continue
        value = _non_default_value(field, getattr(default, field))
        if value is _UNSET:
            isolated["skipped"].append(f"{field} (no derivable alternative value)")
            continue
        try:
            one = Config.model_validate(
                {**default.model_dump(mode="python"), field: value}
            )
            manifest = manifest_for(one, prof, only=(field,))
        except Exception as error:
            isolated["refused"].append(f"{field} ({type(error).__name__})")
            continue
        subject = qualification_subject_digest(manifest, prof)
        if subject == base_subject:
            isolated["free"].append(field)
        else:
            isolated["priced"].append(f"{field} -> {subject[:16]}")
    for label in ("free", "priced", "skipped", "refused"):
        print(f"  {label.upper():<8} {len(isolated[label])}")
        for row in isolated[label]:
            print(f"           {row}")
    print()

    print("== SUMMARY ==")
    print(f"  committed operator configs measured               {len(configs)}")
    print(f"  FULL carriage: subject would MOVE for             {moved} of {len(configs)}")
    print(f"  DROPPED-ONLY carriage: subject would MOVE for     {narrow_moved} of {len(configs)}")
    print(f"  default-valued carriage is free                   {default_subject == base_subject}")
    print(f"  dropped fields free to carry, measured one by one {len(isolated['free'])}")
    print(f"  dropped fields that cost a battery                {len(isolated['priced'])}")
    pairs = len(production_contract_pairs(base_manifest))
    print(
        f"  battery size on THIS manifest                     {pairs} pairs x "
        f"{PRODUCTION_CASES_PER_PAIR} cases = {pairs * PRODUCTION_CASES_PER_PAIR}"
        " provider calls MINIMUM (repair turns add more)"
    )
    print(f"  battery cost recorded for a live home (CLAUDE.md) ~14 min, ~1160 provider calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
