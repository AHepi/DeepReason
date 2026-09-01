"""Read-only digest price for deriving an omitted defended-trial policy.

Fetch the read-only P-S1 branch before running this probe.  ``--expect
baseline`` pins the pre-fix price; ``--expect fixed`` is reserved for an
operator-authorized implementation and requires omission to equal the explicit
derived policy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml

from deepreason.config import Config
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import qualification_subject_digest
from deepreason.run_manifest import RunManifest, compile_run_manifest
from deepreason.v6_policy import engaged_criticism_policy


P_S1_REF = "origin/claude/deepreason-p-s1-commitments-wowcib"
CASES = (
    (
        "P-C1",
        "experiments/2026-08-25-change-constructive-frontier/run-config.yaml",
        "experiments/2026-08-25-change-constructive-frontier/run/run-manifest.json",
        "glm-5.2",
        None,
    ),
    (
        "P-R1",
        "experiments/2026-08-25-poietics-program/run-config.yaml",
        "experiments/2026-08-25-poietics-program/run/run-manifest.json",
        None,
        None,
    ),
    (
        "P-C2-H2",
        "experiments/2026-08-26-pc2-rematch/run-config.yaml",
        "experiments/2026-08-26-pc2-rematch/run/run-manifest.json",
        "glm-5.2",
        None,
    ),
    (
        "P-C2-H3",
        "experiments/2026-08-26-pc2-rematch/run-config-h3.yaml",
        "experiments/2026-08-26-pc2-rematch/run_h3/run-manifest.json",
        "glm-5.2",
        None,
    ),
    (
        "split-leg",
        "experiments/2026-08-27-defect-split-leg-recording/run-config.yaml",
        "experiments/2026-08-25-change-constructive-frontier/run/run-manifest.json",
        "glm-5.2",
        None,
    ),
    (
        "P-C2b",
        "experiments/2026-08-27-pc2b-symmetric-reasoning/run-config.yaml",
        "experiments/2026-08-27-pc2b-symmetric-reasoning/run/run-manifest.json",
        "glm-5.2",
        None,
    ),
    (
        "P-S1",
        "experiments/2026-08-31-p-s1-commitments/run-config.yaml",
        "experiments/2026-08-31-p-s1-commitments/run/run-manifest.json",
        None,
        P_S1_REF,
    ),
)

EXPECTED_BASELINE = {
    "P-C1": (
        "55468838bd863b0c01abde219bbee8af83a8edce13c18bf518c6d0b0ef54a70e",
        "d846931857253bacd8d8d88452107dc735159dc0add58c1ec48b16bf4cf2505e",
        "f7cfbb9c3dc37375103e0de968f017f8883e5525229c5ce63b8a72e309b5ef38",
        "3c3b6f544416319af2dd198206560fff821bdb558cc75f30fafa94a086fe0020",
    ),
    "P-R1": (
        "d11bb591ce886b21987004bae071abc4d34e54648d517413eaa34930433ddd6c",
        "2e4e1c6b9c53b7f41ae653fd683e2dec449ee016e618c8de7005e5b68dceecba",
        "0279485745575ffe9f246421837f630e26f1390c36a70e8ce71548bcc2e0d4d1",
        "5ec96a683ba6f3b1523f4a67af53263051add2f4c051542b9346d012b1bb0975",
    ),
    "P-C2-H2": (
        "bc45e70da8bbbc85d9066df647ebe5278a0afdf6b6cbd489f403b06c9cf8aa18",
        "6e9eb44cdd7d248956efc3f90f3d89c1e295b39465c8bd8d27de4dcd4748fe88",
        "4c635be9e9ab49cfa4c60c1e76828bbd31d6ed2e3c27cdfc7d9174e5a893f160",
        "a55350f4b1e615d91bfb357d75dc928f9d8170fb3e0ba4632d889acb7e0c1d1e",
    ),
    "P-C2-H3": (
        "cac25ef0515790efa42118df661045512ed0f78667053c30e03dcd5a63503883",
        "966048f60d3b76c746105123b495bf97c723e219cdf434ae72f44a6725f1517e",
        "6e086c401b2dfb141cf3bbe92eb2753b87ba1c6ff4d2a37cb0a63f4606fb36bd",
        "b742f59c55126d382072ea2286eb82eed68663864dd1d4c7e995393c54f2a995",
    ),
    "split-leg": (
        "644fd1b1f5d13b23eda64431a5ac647209f26da5447ba5ddbfe6c36dca5df1f4",
        "7d724bfbf27e87a40bb4c63c63be1be77a0f8c6caab8eba8edc2f15d6a914f99",
        "bd960bc34e6f8a7a53f288c065c34a412a4745435c5bc4be42a01a9fc3a548b2",
        "7234a9748f7b731ce17a33661503ba6019856fa49d8f90202022977c1105365e",
    ),
    "P-C2b": (
        "da89d429d9a7715681054051042c8cc52368d015faed964d0cb7aefe09139013",
        "752c4ee7ca9119385f9843f7e66e9a737c624105eed62b03ebeef07722ca1e49",
        "d6c8597e352d53300cc52e645d0a4c45fb9f5f4841ffa0ebbd569b858b38575d",
        "4a1dd1422bb07f0ccdee418f4ae95821a1127e9b6ec4296d3a9f819d162d29be",
    ),
    "P-S1": (
        "c37a92ad731064bcf17383828533efc1e5058dc24890443e816df45780652d46",
        "31216afdae5ae7c3d0eb01377d4fda30c4264f9022f628dc4ed8b271816220fc",
        "ac73c37da04364f7e4e63eaa31467e8663d2814d1f6ab6f6ac9ad08b83b2f84b",
        "7a1d0a063f359e75ef454e766adaa89c8428e8c15beb865abe46b7c1e8cfd8ba",
    ),
}


def _text(path: str, ref: str | None) -> str:
    if ref is None:
        return Path(path).read_text()
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], text=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", choices=("baseline", "fixed"), default="baseline")
    expectation = parser.parse_args().expect
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
    for name, config_path, manifest_path, single_model, ref in CASES:
        config = Config.model_validate(yaml.safe_load(_text(config_path, ref)))
        old = RunManifest.model_validate_json(_text(manifest_path, ref))
        assert config.LEGACY_CRITICISM_ENABLED is False
        assert config.ADJUDICATION_STATUS_AUTHORITY_ENABLED is True
        assert config.ENGAGED_CRITICISM_AUTHORITY == "defended_trial"
        kwargs = {
            "schema_version": 6,
            "workload_profile": "text",
            "rubric_policy": old.rubric_policy,
            "single_model": single_model,
            "concurrency": 2,
            "compiled_at": old.compiled_at,
            "control_plane_policy": old.control_plane_policy,
            "toolchains": old.toolchains,
            "inquiry_capability_policy": old.inquiry_capability_policy,
            "run_input_digest": old.run_input_digest,
        }
        omitted = compile_run_manifest(config, **kwargs)
        critic_endpoint = omitted.roles["argumentative_critic"][0].endpoint_id
        derived = compile_run_manifest(
            config,
            criticism_policy=engaged_criticism_policy(
                critic_endpoint, authority="defended_trial"
            ),
            **kwargs,
        )
        actual = (
            omitted.sha256,
            derived.sha256,
            qualification_subject_digest(omitted, profile),
            qualification_subject_digest(derived, profile),
        )
        if expectation == "baseline":
            assert actual == EXPECTED_BASELINE[name], (name, actual)
        else:
            expected_derived = EXPECTED_BASELINE[name][1::2]
            assert actual[0] == actual[1] == expected_derived[0], (name, actual)
            assert actual[2] == actual[3] == expected_derived[1], (name, actual)
        assert omitted.source_config_hash == derived.source_config_hash
        rows.append(
            {
                "case": name,
                "manifest": [actual[0], actual[1]],
                "qualification_subject": [actual[2], actual[3]],
                "source_config_hash": omitted.source_config_hash,
            }
        )
    print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
