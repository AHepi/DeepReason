#!/usr/bin/env python3
"""W4 Q3: reproduce the dominant terminator offline, from the committed config.

The claim under test, stated so it can fail: *P-R1's judge road ended at
the AUTHORITY GATE because its compiled manifest carried no
`criticism_policy` at all, and `ENGAGED_CRITICISM_AUTHORITY: defended_trial`
was discarded at compile time with no typed disclosure.*

Three probes, each over the tranche's OWN committed `run-config.yaml`. No
provider call, no run, no root touched, no `src/` byte changed.

  P1  The config says what the operator says it says.
  P2  Compiled the way `build_manifest_pr1.py` compiled it -- i.e. without
      passing `criticism_policy=` -- the manifest carries criticism_policy
      None, no compile notice mentioning criticism or engaged authority, and
      no echo of the knob in `engine_config_json`. Three silences.
  P3  Compiled the way `preparation.py::build_preparation_manifest` and the
      grounded-extension builder both do it -- passing the policy the config
      asks for -- the same config yields authority `defended_trial`.

P3 is what makes P2 a finding rather than an observation: the same bytes
produce a defended trial through one door and observe_only through the
other, so the difference is the door, not the configuration.

Exit 0 means every probe held. Any probe that fails prints its own
comparison and exits 1 -- this script is the falsifier, so it must be able
to say no.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason.config import load as load_config  # noqa: E402
from deepreason.run_manifest import compile_run_manifest  # noqa: E402
from deepreason.v6_policy import (  # noqa: E402
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
    engaged_inquiry_capability_policy,
    engaged_local_simulation_toolchain,
)

CONFIG = REPO / "experiments/2026-08-25-poietics-program/run-config.yaml"
COMMITTED = REPO / "experiments/2026-08-25-poietics-program/run/run-manifest.json"
OUT = HERE / "disclosure_probe.json"

# Byte-identical to build_manifest_pr1.py's own call. `run_input_digest` is
# read from the COMMITTED manifest rather than recomputed: schema v5+ refuses
# to compile without one, and reusing the root's own digest keeps this probe
# from having to re-admit the twelve-file dossier to ask a question about a
# policy field.
_COMMITTED_MANIFEST = json.loads(COMMITTED.read_text())

COMMON = dict(
    schema_version=6,
    workload_profile="text",
    rubric_policy="require_cross_family",
    single_model=None,
    concurrency=2,
    compiled_at="2026-08-25T00:00:00Z",
    control_plane_policy=engaged_control_plane_policy_v3(),
    toolchains=(engaged_local_simulation_toolchain(),),
    inquiry_capability_policy=engaged_inquiry_capability_policy(
        attached_evidence=True
    ),
    run_input_digest=_COMMITTED_MANIFEST["run_input_digest"],
)


def fail(label: str, detail: object) -> None:
    print(f"PROBE FAILED: {label}\n  {detail}")
    raise SystemExit(1)


def main() -> int:
    config = load_config(CONFIG)
    results: dict = {}

    # P1 -- what the operator wrote.
    p1 = {
        "ENGAGED_CRITICISM_AUTHORITY": config.ENGAGED_CRITICISM_AUTHORITY,
        "LEGACY_CRITICISM_ENABLED": config.LEGACY_CRITICISM_ENABLED,
        "ADJUDICATION_STATUS_AUTHORITY_ENABLED": (
            config.ADJUDICATION_STATUS_AUTHORITY_ENABLED
        ),
        "JUDGE_SEATS_ENABLED": config.JUDGE_SEATS_ENABLED,
        "ARGUMENTATIVE_AUTHORITY": config.ARGUMENTATIVE_AUTHORITY,
    }
    results["P1_config_as_written"] = p1
    if p1["ENGAGED_CRITICISM_AUTHORITY"] != "defended_trial":
        fail("P1: the config does not ask for a defended trial", p1)
    if p1["LEGACY_CRITICISM_ENABLED"]:
        fail("P1: the config still enables legacy criticism", p1)
    if not p1["ADJUDICATION_STATUS_AUTHORITY_ENABLED"]:
        fail("P1: the master adjudication gate is off in the config", p1)

    # P2 -- the builder's own call shape: no criticism_policy argument.
    as_built = compile_run_manifest(config, **COMMON)
    notices = [n.code for n in (as_built.compile_notices or ())]
    echo = as_built.engine_config_json
    if isinstance(echo, str):
        echo = json.loads(echo)
    p2 = {
        "criticism_policy": (
            None
            if as_built.criticism_policy is None
            else as_built.criticism_policy.authority
        ),
        "compile_notices": notices,
        "notices_mentioning_criticism_or_authority": [
            code
            for code in notices
            if "CRITICISM" in code or "AUTHORITY" in code or "JUDGE" in code
        ],
        "ENGAGED_CRITICISM_AUTHORITY_in_engine_config_echo": (
            "ENGAGED_CRITICISM_AUTHORITY" in echo
        ),
        "judge_seats_frozen_in_roles": len(as_built.roles.get("judge", ()) or ()),
    }
    results["P2_compiled_as_the_builder_did"] = p2
    if p2["criticism_policy"] is not None:
        fail("P2: expected no criticism policy from the builder's call shape", p2)
    if p2["notices_mentioning_criticism_or_authority"]:
        fail("P2: a typed disclosure DOES exist; the finding is wrong", p2)
    if p2["ENGAGED_CRITICISM_AUTHORITY_in_engine_config_echo"]:
        fail("P2: the knob IS echoed into engine_config_json", p2)
    if p2["judge_seats_frozen_in_roles"] != 2:
        fail("P2: the judge ensemble was not frozen into the manifest", p2)

    # P3 -- the managed shape: same config, policy passed as preparation.py
    # and the grounded-extension builder both pass it.
    as_managed = compile_run_manifest(
        config,
        criticism_policy=engaged_criticism_policy(
            as_built.roles["argumentative_critic"][0].endpoint_id,
            authority=(
                config.ENGAGED_CRITICISM_AUTHORITY
                if config.ADJUDICATION_STATUS_AUTHORITY_ENABLED
                else "observe_only"
            ),
        ),
        **COMMON,
    )
    p3 = {
        "criticism_policy": (
            None
            if as_managed.criticism_policy is None
            else as_managed.criticism_policy.authority
        )
    }
    results["P3_compiled_the_managed_way"] = p3
    if p3["criticism_policy"] != "defended_trial":
        fail("P3: the managed shape did not produce a defended trial", p3)

    # The committed root agrees with P2, not P3 -- which is the whole point.
    committed = _COMMITTED_MANIFEST
    results["committed_root"] = {
        "criticism_policy": committed.get("criticism_policy"),
        "compile_notices": committed.get("compile_notices"),
    }
    if committed.get("criticism_policy") is not None:
        fail("committed P-R1 manifest DOES carry a criticism policy", committed)

    results["verdict"] = (
        "P-R1's judge road ended at the AUTHORITY GATE. The same committed "
        "config compiles to observe_only through the builder's call shape and "
        "to defended_trial through the managed one; the difference is which "
        "door was used, and compile discloses nothing either way."
    )
    OUT.write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
    print(json.dumps(results, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
