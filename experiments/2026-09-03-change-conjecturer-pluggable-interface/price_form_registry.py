"""Read-only digest price for the three roads in FEASIBILITY.md.

Frozen surfaces 4 (`run_manifest.py` schemas) and 5 (qualification subjects)
are the candidate contacts. This probe MEASURES what each road costs instead
of asserting it, modelled on
`experiments/2026-09-01-defect-judge-canary-compile-gap/price_compile_gap.py`.

What is priced, per committed manifest:

  baseline            the manifest sha and its qualification subject digest
  road-A-off-manifest a section-plugin layout selected the way
                      DR-INV-render-layout selects an arrangement -- by
                      argument or environment, touching neither Config nor
                      the manifest. Priced by construction: the payload is
                      unchanged, so the digest is unchanged. Printed so the
                      claim is a measured row rather than an assurance.
  road-B-config-field one new knob reaching `Config`. `run_manifest.py`
                      `_source_config_data` dumps every Config field into
                      `engine_config_json`, which `qualification.py`
                      `qualification_subject_payload` folds into
                      `manifest_behavior`; simulated here by adding one key
                      to that map and re-deriving the subject digest.
  road-C-form-select  the conjecturer turn contract selected through the
                      manifest (`ContractVersionPolicyV3
                      .conjecturer_turn_contract`), v6 -> v7 -- the exact
                      move the D2 rev 2 scoped grant already made once.

A moved digest means every qualification bundle in the tree misses its cache
and the ~14-minute, ~1160-call battery reruns. That is the price, and it is
the operator's to accept or refuse.

    python experiments/2026-09-03-change-conjecturer-pluggable-interface/\
price_form_registry.py
"""

from __future__ import annotations

import json
import pathlib
import sys

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import (
    qualification_subject_digest,
    qualification_subject_payload,
)
from deepreason.run_manifest import RunManifest

# The domain separator qualification.py hashes the subject under. Read from
# the module rather than restated, so a change there breaks this probe
# instead of silently making it price the wrong thing.
from deepreason.qualification import _SUBJECT_DOMAIN

CASES = (
    "experiments/2026-08-25-change-constructive-frontier/run/run-manifest.json",
    "experiments/2026-08-25-poietics-program/run/run-manifest.json",
    "experiments/2026-08-26-pc2-rematch/run/run-manifest.json",
    "experiments/2026-08-26-pc2-rematch/run_h3/run-manifest.json",
)


def _digest_of_payload(payload: dict) -> str:
    return sha256_hex(_SUBJECT_DOMAIN + canonical_json(payload))


def main() -> int:
    profile = ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.com/v1",
        model_id="model-a",
        model_revision="rev-a",
        family="family-a",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY",
    )
    rows = []
    for path in CASES:
        source = pathlib.Path(path)
        if not source.is_file():
            print(f"SKIP (absent): {path}", file=sys.stderr)
            continue
        manifest = RunManifest.model_validate_json(source.read_text())
        baseline_payload = qualification_subject_payload(manifest, profile)
        baseline = qualification_subject_digest(manifest, profile)
        assert _digest_of_payload(baseline_payload) == baseline, (
            "the probe's own re-derivation must agree with qualification.py"
        )

        # Road A: nothing reaches Config or the manifest. The payload is the
        # SAME OBJECT the baseline hashed, so this row is a tautology by
        # design -- it exists to state, as a measured row, that the road
        # whose price is zero really is priced at zero.
        road_a = _digest_of_payload(qualification_subject_payload(manifest, profile))

        # Road B: one knob on Config. `run_manifest.py`
        # `_versioned_source_config_data` decides whether a Config field is
        # CARRIED into `engine_config_json` (a JSON *string* inside
        # manifest_behavior) or unconditionally DROPPED with an
        # ENGINE_CONFIG_FIELD_NOT_CARRIED notice that
        # `qualification_subject_payload` then strips. Both variants are
        # priced, because the difference between them is the whole road.
        carried_payload = json.loads(json.dumps(baseline_payload))
        engine_raw = carried_payload["manifest_behavior"].get("engine_config_json")
        carried = isinstance(engine_raw, str)
        if carried:
            engine = json.loads(engine_raw)
            engine["CONJECTURER_PACK_LAYOUT_ID"] = "conj-pack.legacy-v0"
            carried_payload["manifest_behavior"]["engine_config_json"] = json.dumps(
                engine, sort_keys=True, separators=(",", ":")
            )
        road_b = _digest_of_payload(carried_payload)
        # The DROPPED variant: the field never reaches engine_config_json, and
        # its carriage notice is the one code qualification strips. The payload
        # is therefore byte-identical to the baseline.
        road_b_dropped = _digest_of_payload(
            qualification_subject_payload(manifest, profile)
        )

        # Road C: the form selected through the manifest's contract versions.
        contracts = manifest.control_plane_policy.contract_versions
        current = contracts.conjecturer_turn_contract
        other = (
            "conjecturer.turn.v7"
            if current == "conjecturer.turn.v6"
            else "conjecturer.turn.v6"
        )
        moved = manifest.model_copy(
            update={
                "control_plane_policy": manifest.control_plane_policy.model_copy(
                    update={
                        "contract_versions": contracts.model_copy(
                            update={"conjecturer_turn_contract": other}
                        )
                    }
                )
            }
        )
        # Qualification refuses a manifest whose control-plane policy is not
        # the repository-owned preset, so road C's own price is measured in
        # two parts: the refusal, and (when it is reachable at all) the moved
        # digest. Whichever comes back is the price.
        try:
            road_c_payload = qualification_subject_payload(moved, profile)
            road_c = _digest_of_payload(road_c_payload)
            road_c_refusal = None
        except Exception as error:  # QualificationError, by design
            road_c = None
            road_c_refusal = f"{type(error).__name__}: {error}"
        rows.append(
            {
                "case": path,
                "baseline_manifest_sha256": manifest.sha256,
                "baseline_subject_digest": baseline,
                "road_A_off_manifest": road_a,
                "road_A_moves": road_a != baseline,
                "engine_config_json_carried": carried,
                "road_B_config_field_carried": road_b,
                "road_B_carried_moves": road_b != baseline,
                "road_B_config_field_dropped": road_b_dropped,
                "road_B_dropped_moves": road_b_dropped != baseline,
                "road_C_from": current,
                "road_C_to": other,
                "road_C_form_selected_in_manifest": road_c,
                "road_C_moves": road_c != baseline,
                "road_C_qualification_refusal": road_c_refusal,
            }
        )

    print("PRICE_FORM_REGISTRY_V1")
    print(json.dumps(rows, indent=2, sort_keys=True))
    print()
    print("VERDICT")
    for row in rows:
        print(
            f"  {row['case']}\n"
            f"    road A (off-manifest selection): "
            f"{'MOVES' if row['road_A_moves'] else 'digest unchanged -- price 0'}\n"
            f"    road B (Config knob, CARRIED):   "
            f"{'MOVES -- full battery reruns' if row['road_B_carried_moves'] else 'unchanged'}\n"
            f"    road B (Config knob, DROPPED):   "
            f"{'MOVES -- full battery reruns' if row['road_B_dropped_moves'] else 'digest unchanged -- price 0'}\n"
            f"    road C (form id in manifest):    "
            + (
                f"REFUSED at qualification -- {row['road_C_qualification_refusal']}"
                if row["road_C_qualification_refusal"]
                else ("MOVES -- full battery reruns" if row["road_C_moves"] else "unchanged")
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
