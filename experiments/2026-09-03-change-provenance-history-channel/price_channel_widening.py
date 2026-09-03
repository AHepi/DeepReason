"""Priced stop, C7: what does a MODEL-REQUESTABLE provenance channel cost?

Read-only probe. Writes nothing, touches no committed root, changes no file
under ``src/``. Phase 1 forbids production code (C8), so Road A is simulated
in-process by patching the module constant and re-deriving, never by editing
``run_manifest.py``.

The question SPEC.md has to answer before it can pick a road:

  ROAD A -- reuse ``RetrievalChannel`` + ``permitted_retrieval_channels`` and
    add the provenance channels to ``_ATTENTION_CHANNELS``.  That is frozen
    surface 4 (``run_manifest.py``, "manifest schemas AND their validators"),
    and specifically the case ``INV-frozen-surfaces`` names as the live
    example: admitting a value a validator previously rejected.

  ROAD B -- a parallel provenance vocabulary that never enters
    ``_ATTENTION_CHANNELS``, on the ``direct_open`` precedent (a
    ``RetrievalChannel`` member that is deliberately NOT a manifest attention
    channel and NOT model-requestable).

Three prices are measured, not asserted:

  P1  the qualification subject digest over every committed run-config, before
      and after the widening.  A moved digest means every cached qualification
      in every home is invalidated -- ~14 min and ~1160 calls per home.
  P2  the number of COMMITTED manifests that stop validating.  Two sibling
      validators are total rather than subset: ``channel_priority`` must
      contain EVERY channel in frozen order, and ``per_channel_limits`` must
      name EVERY channel.  A manifest written before the widening names 11 of
      12, so it is not a widening for them at all -- it is a break.
  P3  the model-requestable gate.  ``direct_open`` proves a channel can exist
      in ``RetrievalChannel`` and be refused as a model request; the probe
      re-derives whether Road B's channels would hit the same refusal, which
      is what decides whether Road B can satisfy R3 at all.

Usage:  python experiments/2026-09-03-change-provenance-history-channel/\
price_channel_widening.py [--json]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# The channels a provenance query surface would need if it reused the
# attention vocabulary.  Named here only to price them; nothing registers them.
PROPOSED = ("provenance", "episode_pool")


def _committed_run_configs() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "experiments/*/run-config*.yaml"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO / line for line in out.stdout.split() if line]


def _committed_manifests() -> list[Path]:
    out = subprocess.run(
        ["git", "grep", "-l", "channel_priority", "--", "*.json"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    return [REPO / line for line in out.stdout.split() if line]


def _digests(_configs: list[Path]) -> dict[str, str]:
    """Qualification subject digest over the SAME fixture the frozen-surface
    checks use.

    An earlier version of this probe compiled the ten committed
    ``run-config*.yaml`` files instead.  Every one of them raised
    ``QUALIFICATION_V6_REQUIRED`` -- they name a reusable production
    qualification that is not in this container -- so "0 digests moved" was
    ten identical error strings compared against themselves, not a
    measurement.  Recorded rather than quietly replaced: a probe that cannot
    fail is the thing ``docs_verify --audit`` exists to refuse, and the same
    standard is owed here.

    ``tests/test_reusable_qualification._manifest`` is the fixture that
    ``INV-frozen-surfaces`` pins its own digest checks against (the
    2026-08-23 and 2026-08-26 grants both quote digests derived from it), so
    a delta here is the same delta those grants priced.
    """
    sys.path.insert(0, str(REPO))
    from deepreason.qualification import qualification_subject_digest
    from tests.test_reusable_qualification import _manifest, _profile

    result: dict[str, str] = {}
    for label, kwargs in (
        ("default", {}),
        ("question-B", {"question": "Question B"}),
    ):
        try:
            profile = _profile()
            manifest = _manifest(profile, **kwargs)
            result[label] = qualification_subject_digest(manifest, profile)
        except Exception as exc:  # noqa: BLE001 - the error IS the datum
            result[label] = f"ERROR:{type(exc).__name__}:{exc}"[:200]
    return result


def _validate_manifests(paths: list[Path]) -> dict[str, str]:
    from deepreason.run_manifest import RunManifest

    result: dict[str, str] = {}
    for path in paths:
        key = str(path.relative_to(REPO))
        try:
            RunManifest.model_validate_json(path.read_text(encoding="utf-8"))
            result[key] = "VALID"
        except Exception as exc:  # noqa: BLE001
            result[key] = f"INVALID:{type(exc).__name__}"
    return result


def _widen() -> None:
    """Simulate Road A in-process. Never writes to src/."""
    from deepreason import run_manifest as rm

    rm._ATTENTION_CHANNELS = rm._ATTENTION_CHANNELS + PROPOSED


def _road_b_gate() -> dict[str, object]:
    """P3 -- can a non-attention channel be model-requestable at all?

    ``direct_open`` is refused in two places.  If those refusals are keyed to
    the specific member, Road B's channels pass; if they are keyed to
    "not in the attention list", Road B cannot satisfy R3 and only Road A can.
    """
    import inspect

    from deepreason import conjecture_turn
    from deepreason.workflow import models as wf_models

    turn_src = inspect.getsource(conjecture_turn)
    wf_src = inspect.getsource(wf_models)
    return {
        "conjecture_turn_refuses_by_member": "RetrievalChannel.DIRECT_OPEN in value"
        in turn_src,
        "workflow_refuses_by_member": "RetrievalChannel.DIRECT_OPEN in value" in wf_src,
        "any_refusal_keyed_to_attention_list": "_ATTENTION_CHANNELS" in turn_src
        or "_ATTENTION_CHANNELS" in wf_src,
    }


def _road_b_grantable() -> dict[str, object]:
    """P4 -- could a Road B channel ever be GRANTED, not merely un-refused?

    P3 only shows the two ``direct_open`` refusals are keyed to that member.
    The binding question is different: ``rules/conj.py`` grants an expansion
    only when ``desired - permitted`` is empty, and ``permitted`` is
    ``context_policy.permitted_retrieval_channels``, which ``run_manifest.py``
    validates against ``_ATTENTION_CHANNELS``.  If a channel cannot enter that
    tuple it can never enter ``permitted``, so every request naming it is
    denied ``channel_not_permitted`` forever.

    This is re-derived by construction rather than read off the source: build
    the policy with the proposed channel and see what the validator says.
    """
    from pydantic import ValidationError

    from deepreason.run_manifest import ConjectureContextPolicyV1

    base = dict(
        mode="harness_plus_model_request",
        initial_max_blocks=8,
        initial_max_guides=2,
        max_context_expansion_requests=2,
        max_extra_blocks=8,
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )
    try:
        ConjectureContextPolicyV1(
            permitted_retrieval_channels=("focus", PROPOSED[0]), **base
        )
        admitted = True
        detail = ""
    except ValidationError as exc:
        admitted = False
        detail = str(exc).splitlines()[1].strip() if len(str(exc).splitlines()) > 1 else str(exc)[:120]
    return {
        "road_b_channel_admitted_to_permitted_list": admitted,
        "validator_says": detail,
        "consequence": (
            "grantable through the existing request path"
            if admitted
            else "permanently denied channel_not_permitted; Road B needs its OWN "
            "request field and permitted list, not RetrievalChannel"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    configs = _committed_run_configs()
    manifests = _committed_manifests()

    before_digests = _digests(configs)
    before_valid = _validate_manifests(manifests)
    gate = _road_b_gate()
    grantable = _road_b_grantable()

    _widen()

    after_digests = _digests(configs)
    after_valid = _validate_manifests(manifests)

    moved = sorted(k for k in before_digests if before_digests[k] != after_digests.get(k))
    broke = sorted(
        k
        for k in before_valid
        if before_valid[k] == "VALID" and after_valid.get(k) != "VALID"
    )

    report = {
        "probe": "PROVENANCE_CHANNEL_PRICE_V1",
        "proposed_channels": list(PROPOSED),
        "P1_run_configs_priced": len(configs),
        "P1_digests_moved": len(moved),
        "P1_moved_list": moved,
        "P2_committed_manifests_checked": len(manifests),
        "P2_valid_before": sum(1 for v in before_valid.values() if v == "VALID"),
        "P2_broken_by_widening": len(broke),
        "P2_broken_list": broke[:20],
        "P3_road_b_gate": gate,
        "P4_road_b_grantable": grantable,
        "before_digests": before_digests,
        "after_digests": after_digests,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PROVENANCE_CHANNEL_PRICE_V1")
        print(f"  proposed channels           : {', '.join(PROPOSED)}")
        print(f"  P1 run-configs priced       : {len(configs)}")
        print(f"  P1 subject digests MOVED    : {len(moved)}")
        for k in moved:
            print(f"       - {k}")
            print(f"           before {before_digests[k]}")
            print(f"           after  {after_digests[k]}")
        print(f"  P2 committed manifests      : {len(manifests)}")
        print(f"  P2 valid before widening    : {report['P2_valid_before']}")
        print(f"  P2 BROKEN by widening       : {len(broke)}")
        for k in broke[:20]:
            print(f"       - {k}")
        print("  P3 Road B model-request gate:")
        for k, v in gate.items():
            print(f"       {k} = {v}")
        print("  P4 Road B grantable through existing path:")
        for k, v in grantable.items():
            print(f"       {k} = {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
