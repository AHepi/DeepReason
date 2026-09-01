#!/usr/bin/env python3
"""Offline cycle soak: drive the managed run path deep, on a REAL config shape.

Why this exists, in one paragraph. Four consecutive live runs died before
cycle 3 with four DIFFERENT typed operational causes -- route-seat capability
exhaustion, a route/lease mismatch, a denied work budget, and a reservation
bound that disagreed with the rendered request -- while
``wheel_operational_smoke.py`` stayed green throughout. The smoke misses them
for two independent reasons. It never renders this configuration's SHAPE:
operator-authored ``predicate:`` criteria reach a run only through the
manifest surface, because the managed preparation service hardcodes
``criteria=()``. And it never runs past its short reason stage, while three of
the four deaths are at cycle 2. This instrument removes both gaps: it compiles
a run from a committed config, enables attached evidence, carries the real
criteria, and drives ``TextRunApplicationService`` -- the one run path -- for
N cycles (default 8, the carrier threshold) against the smoke's own
deterministic stub.

It is an INSTRUMENT, not a gate. No pytest gate runs it; it is minutes-long
and joins the wheel smokes as a pre-launch check. Run it on a launch config
before a live launch.

    python -u scripts/cycle_soak.py                    # epoch3, 8 cycles
    python -u scripts/cycle_soak.py --case epoch3 --cycles 12
    python -u scripts/cycle_soak.py --list-cases
    python -u scripts/cycle_soak.py --keep --out /tmp/soak

Exit status is three-valued so a known-red seam stays visible without
masking a real regression:

    0  every assertion held; every covered seam clean
    1  a soak assertion failed, or a seam failed by name unexpectedly
    3  ONLY expected-red seams failed (see EXPECTED_RED below)

The stub is REUSED, never re-minted: ``ProviderState``, ``_provider_server``,
``response_for_schema`` and the fixture credential are imported from
``wheel_operational_smoke``. A second stub would be a second thing to keep
true.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(SCRIPTS))

import wheel_operational_smoke as _smoke  # noqa: E402  (the ONE stub, reused)
from wheel_operational_smoke import (  # noqa: E402
    TEST_CREDENTIAL,
    TEST_CREDENTIAL_ENV,
    ProviderState,
    _provider_server,
)

REACH_RICH = REPO / "experiments" / "2026-08-22-live-reach-rich-run"
EPOCH3 = REPO / "experiments" / "2026-08-22-change-epoch3-second-lineage"
POIETICS = REPO / "experiments" / "2026-08-25-poietics-program"
FRONTIER = REPO / "experiments" / "2026-08-25-change-constructive-frontier"
REMATCH = REPO / "experiments" / "2026-08-26-pc2-rematch"
SYMMETRIC = REPO / "experiments" / "2026-08-27-pc2b-symmetric-reasoning"
SPLIT_LEGS = REPO / "experiments" / "2026-08-27-defect-split-leg-recording"
ALL_MODULES = REPO / "experiments" / "2026-09-01-live-all-modules-p-a1"

# The deepest cycle any of the four recorded deaths reached.  A soak that
# stops at or below this depth has not looked where they died.
DEEPEST_RECORDED_DEATH_CYCLE = 2

# A seam listed here may fail without failing the soak outright (exit 3
# instead of 1).  The value is the branch whose merge is expected to clear
# it.  Remove the entry when that branch lands -- an expected-red seam that
# nobody clears is indistinguishable from a seam nobody fixed.
# Empty is the correct resting state: every seam listed here is one nobody has
# cleared yet, so an entry that outlives its fix makes exit 3 meaningless.
# D4-reservation-bound was cleared by
# experiments/2026-08-23-fix-reservation-bound-authority/ and removed by
# experiments/2026-08-25-defect-workflow-call-pairing/.  While this map is
# empty, _verdict cannot return 3 at all.
EXPECTED_RED: dict[str, str] = {}


# --------------------------------------------------------------------------
# The four recorded death shapes (REQUEST.md R1, quoted from run-status.json)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Seam:
    """One formerly-fatal seam: how to see it was REACHED, and how it FAILS."""

    id: str
    what: str
    # Record object types under <root>/objects/ whose presence proves the
    # seam was exercised.  Reach is measured from the typed record, never
    # from prose -- an assertion that only checks for absence goes green on
    # a run that never reached the code at all.
    reached_by: tuple[str, ...]
    # Object types whose mere presence IS the failure.
    fatal_objects: tuple[str, ...] = ()
    # Substrings that, in the terminal message, name this seam's death.
    fatal_messages: tuple[str, ...] = ()
    # Extra evidence counted for the report but not required for reach.
    notes: str = ""


SEAMS: tuple[Seam, ...] = (
    Seam(
        id="D1-seat-contract",
        what="seat contracts with repairs",
        reached_by=(
            "workflow-contract-decomposition-transition-v1",
            "workflow-provider-attempt-v1",
        ),
        fatal_objects=("workflow-route-seat-insufficient-capability-v1",),
        fatal_messages=("V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY",),
        notes="repairs are attempts with attempt_index > 0",
    ),
    Seam(
        id="D2-route-lease",
        what="lease-checked routes with tuning",
        reached_by=("workflow-provider-attempt-v1",),
        fatal_messages=("ROUTE_LEASE_MISMATCH",),
        notes="every attempt must carry a route_lease with role/seat/route_sha256",
    ),
    Seam(
        id="D3-budget-auth",
        what="budget authorization",
        reached_by=("workflow-dispatch-authorization-v1",),
        fatal_messages=("token budget denied", "WorkBudgetDenied"),
    ),
    Seam(
        id="D4-reservation-bound",
        what="reservation/dispatch bounds",
        reached_by=("workflow-token-reservation-v2",),
        fatal_messages=(
            "transactional reservation bound differs from rendered request",
            "transactional repair requires a new authorization bundle",
            "WorkflowAuthorizationError",
        ),
    ),
)


# --------------------------------------------------------------------------
# Cases -- a case is a REAL config shape, not a synthetic one
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SoakCase:
    """One configuration shape to soak.

    ``config_path`` is READ, never restated: the case overrides exactly the
    two fields that must not reach a real provider (``endpoint``,
    ``api_key_env``) and inherits every other field from the committed file.
    A drift in the real config is therefore a drift in the soak.
    """

    id: str
    description: str
    config_path: Path
    builder: str  # module under experiments/ that owns QUESTION/CRITERIA
    attached_evidence: bool
    default_cycles: int = 8
    default_token_budget: int | None = None
    # The directory ``builder`` is imported from.  Defaults to the reach-rich
    # tranche because the first two cases live there; a case whose builder
    # lives elsewhere cannot be expressed without this.
    builder_dir: Path = REACH_RICH
    # Whether the builder OWNS root construction.  The default path below
    # compiles a single-model, rubric-forbidding manifest with an empty
    # dossier, which is the true shape of the first two cases and the wrong
    # shape for any case carrying cross-family seats or a bound dossier.
    # Such a case must delegate, or the soak would drive a configuration the
    # launch will never use -- and an instrument that soaks the wrong shape
    # is worse than no instrument, because it reports green.
    delegates_to_builder: bool = False


CASES: dict[str, SoakCase] = {
    "epoch3": SoakCase(
        id="epoch3",
        description=(
            "the epoch-3 second-lineage shape: solo glm-5.2 across all 11 "
            "canonical roles, three operator-authored predicate: criteria, "
            "attached evidence ENABLED, engaged control plane v3"
        ),
        config_path=REACH_RICH / "run-config.yaml",
        builder="build_manifest",
        attached_evidence=True,
    ),
    "pr1": SoakCase(
        id="pr1",
        description=(
            "the Poietics P-R1 explanation shape: CROSS-FAMILY seats "
            "(deepseek-v4-pro:0813 conjecturer, kimi-k3 critic, a two-seat "
            "qwen3.5/glm-5.2 judge ensemble), everything on, and the twelve "
            "curated record files bound as a dossier AT SEED"
        ),
        config_path=POIETICS / "run-config.yaml",
        builder="build_manifest_pr1",
        builder_dir=POIETICS,
        attached_evidence=True,
        delegates_to_builder=True,
        default_cycles=12,
        default_token_budget=3_000_000,
    ),
    "pc1": SoakCase(
        id="pc1",
        description=(
            "the P-C1 ARM H constructive shape: SOLO glm-5.2 across all 11 "
            "canonical roles, everything on EXCEPT judges (rubric_policy "
            "forbid, JUDGE_SEATS_ENABLED false), an EMPTY dossier, and three "
            "predicate: criteria that score a Heilbronn construction"
        ),
        config_path=FRONTIER / "run-config.yaml",
        builder="build_manifest_pc1",
        builder_dir=FRONTIER,
        attached_evidence=False,
        # The builder owns root construction: the default path would bind a
        # manifest with rubric_policy left alone and a differently-shaped
        # dossier, and an instrument that soaks the wrong shape is worse
        # than no instrument, because it reports green.
        delegates_to_builder=True,
        # R20's "cycles sized deep"; the launch's own depth, not a sample
        # of it -- the soak must drive the configuration the launch uses.
        default_cycles=24,
        default_token_budget=3_000_000,
    ),
    "pc2": SoakCase(
        id="pc2",
        description=(
            "the P-C2 ARM H2 REBUILT shape: P-C1's constructive shape with "
            "REBUILD F1's discharge channel LIVE (discharge-required.v1), F2's "
            "reference menus and F3's default-on evidence channels, driving "
            "the same three predicate: criteria that score a Heilbronn "
            "construction"
        ),
        config_path=REMATCH / "run-config.yaml",
        builder="build_manifest_pc2",
        builder_dir=REMATCH,
        attached_evidence=False,
        # Same reason as pc1: the builder owns root construction, and an
        # instrument that soaks the wrong shape is worse than no instrument
        # because it reports green.
        delegates_to_builder=True,
        # The launch's own depth and budget, not a sample of them.
        default_cycles=24,
        default_token_budget=3_000_000,
    ),
    "pc2b": SoakCase(
        id="pc2b",
        description=(
            "the P-C2b ARM H shape: P-C2's rebuilt constructive shape with the "
            "model's REASONING MODE ON (the `reasoning` field removed, which "
            "also arms llm/split.py's two-leg protocol under its `auto` "
            "default), the discharge channel live, and timeout_s raised to 900"
        ),
        config_path=SYMMETRIC / "run-config.yaml",
        builder="build_manifest_pc2b",
        builder_dir=SYMMETRIC,
        attached_evidence=False,
        delegates_to_builder=True,
        default_cycles=24,
        # PREREG §5: the LAUNCH's own budget, not a sample of it.
        default_token_budget=200_000,
    ),
    "split-legs": SoakCase(
        id="split-legs",
        description=(
            "the P-C1 ARM H constructive shape with the model's REASONING "
            "MODE ON -- its committed config with the single line "
            "`reasoning: \"none\"` deleted, which is the whole of the wiring "
            "that arms llm/split.py's two-leg split-budget protocol under "
            "its `auto` default. The one case in this file that drives a "
            "SPLIT seat call, and therefore the one that can see a split "
            "leg recorded as a repair attempt"
        ),
        config_path=SPLIT_LEGS / "run-config.yaml",
        # The P-C1 builder, unchanged and imported rather than copied: the
        # shape under test differs from pc1 by the config's one line, so a
        # second builder could only drift away from it.
        builder="build_manifest_pc1",
        builder_dir=FRONTIER,
        attached_evidence=False,
        delegates_to_builder=True,
        default_cycles=24,
        default_token_budget=3_000_000,
    ),
    "pa1": SoakCase(
        id="pa1",
        description=(
            "the P-A1 all-modules shape: FOUR models across eleven roles "
            "(a two-seat deepseek/glm-5.3 conjecturer ensemble, deepseek "
            "critic, glm-5.3 defender, a cross-family qwen3.5/gpt-oss judge "
            "ensemble), an EXPLICIT defended-trial criticism policy, the "
            "grounded two-stage bridge, route-bound schools, both evidence "
            "channels on with a raised simulation budget, the config referee "
            "armed, and NEAR_DUP_EPS calibrated rather than None"
        ),
        config_path=ALL_MODULES / "run-config.yaml",
        builder="build_manifest_pa1",
        builder_dir=ALL_MODULES,
        # The dossier is EMPTY but the CHANNEL is on, and the builder owns
        # that distinction along with the explicit criticism policy, the
        # engaged capability preset and the route-bound control plane. The
        # default root-construction path can express none of them, and an
        # instrument that soaks the wrong shape is worse than no instrument
        # because it reports green.
        attached_evidence=True,
        delegates_to_builder=True,
        # The LAUNCH's own depth and budget, not a sample of them.
        default_cycles=24,
        default_token_budget=3_000_000,
    ),
    "reach-rich": SoakCase(
        id="reach-rich",
        description=(
            "the reach-rich epoch-1 shape: identical to epoch3 except "
            "attached evidence DISABLED (the one field epoch 3 moved)"
        ),
        config_path=REACH_RICH / "run-config.yaml",
        builder="build_manifest",
        attached_evidence=False,
    ),
}


# --------------------------------------------------------------------------
# Root construction
# --------------------------------------------------------------------------


def _loopback_config(source: Path, dest: Path, port: int) -> Path:
    """Copy a committed config, redirecting every role to the stub.

    Two fields move and nothing else.  ``endpoint`` must not name a real
    provider, and ``api_key_env`` must name the fixture credential rather
    than the operator's live key -- reading OLLAMA_API_KEY here would make
    an offline instrument depend on a secret it has no use for.
    """

    import yaml

    document = yaml.safe_load(source.read_text())
    roles = document.get("roles") or {}
    endpoint = f"http://127.0.0.1:{port}/v1"

    def _redirect(route):
        # A role may carry a LIST of routes (a judge ensemble).  Skipping
        # those would leave the ensemble pointing at the real provider with
        # the operator's key -- an offline instrument reaching the network.
        if isinstance(route, (list, tuple)):
            return [_redirect(entry) for entry in route]
        if not isinstance(route, dict):
            return route
        route["endpoint"] = endpoint
        route["api_key_env"] = TEST_CREDENTIAL_ENV
        return route

    document["roles"] = {name: _redirect(route) for name, route in roles.items()}
    dest.write_text(yaml.safe_dump(document, sort_keys=True))
    return dest


# Cases whose value depends on an IN-RUN EVALUATION actually firing and
# actually reaching the writer.  Listed rather than inferred: a case acquires
# this obligation by DESIGN, and a soak that guessed would either miss the
# obligation or invent one.
IN_RUN_EVALUATION_CASES = frozenset({"pc2", "pc2b"})


def _case_symbols(case: SoakCase):
    """QUESTION / CRITERIA / COMPILED_AT, imported from the committed builder.

    Imported rather than restated for the same reason
    ``build_manifest_epoch3.py`` imports from ``build_manifest.py``: two
    copies of a question and three predicates cannot be kept in agreement,
    and the soak is worthless the moment its shape drifts from the one that
    actually launches.
    """

    return (
        _case_module(case).QUESTION,
        _case_module(case).CRITERIA,
        _case_module(case).COMPILED_AT,
    )


def _case_module(case: SoakCase):
    """Import the committed builder that owns this case's shape."""

    sys.path.insert(0, str(case.builder_dir))
    return __import__(case.builder)


def build_root(case: SoakCase, root: Path, *, port: int) -> dict:
    """Write dossier, run-input, manifest and problem.json under ``root``."""

    from deepreason.config import load as load_config
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        EvidenceDossierV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )
    from deepreason.preparation import _question_digest
    from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
    from deepreason.v6_policy import (
        engaged_attached_evidence_policy,
        engaged_control_plane_policy_v3,
    )

    question, criteria, compiled_at = _case_symbols(case)
    config_path = _loopback_config(
        case.config_path, root.parent / "soak-config.yaml", port
    )

    if case.delegates_to_builder:
        # The builder writes dossier, run-input, manifest and problem.json
        # itself, from the loopback-redirected config.  Nothing about the
        # launch shape is restated here, so the soak cannot drift from it.
        summary = _case_module(case).build(root, config_path=config_path)
        summary["case"] = case.id
        return summary

    config = load_config(config_path)

    problem_id = f"question-{_question_digest(question)[:32]}"
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by=f"cycle_soak.py case={case.id}",
            acquisition_method="no attached evidence",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=question, criteria=criteria
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)

    common = dict(
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        single_model="glm-5.2",
        concurrency=2,
        compiled_at=compiled_at,
        control_plane_policy=engaged_control_plane_policy_v3(),
        run_input_digest=run_input.run_input_digest,
    )

    inquiry_policy = None
    if case.attached_evidence:
        # The derived all-disabled policy is the baseline that must be
        # reproduced exactly; it cannot be hand-assembled, because flipping
        # `enabled` on the engaged policy leaves the engaged bounds behind
        # and the model refuses a disabled capability carrying non-zero
        # bounds.  Compile once in memory, read the derived policy back,
        # move the one field -- the same move build_manifest_epoch3.py makes.
        baseline = compile_run_manifest(config, **common)
        inquiry_policy = baseline.inquiry_capability_policy.model_copy(
            update={
                "attached_evidence": engaged_attached_evidence_policy(attached=True)
            }
        )

    manifest = compile_run_manifest(
        config, inquiry_capability_policy=inquiry_policy, **common
    )
    bind_run_manifest(manifest, root)

    (root / "problem.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-text-workload-v1",
                "problem": {"id": problem_id, "description": question},
                "criteria": [json.loads(c.model_dump_json()) for c in criteria],
                "sources": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    return {
        "case": case.id,
        "manifest_sha256": manifest.sha256,
        "run_input_digest": run_input.run_input_digest,
        "problem_id": problem_id,
        "criteria": [c.id for c in criteria],
        "attached_evidence_enabled": (
            manifest.inquiry_capability_policy.attached_evidence.enabled
        ),
        "compile_notices": [
            {"code": n.code, "message": n.message}
            for n in (manifest.compile_notices or ())
        ],
    }


# --------------------------------------------------------------------------
# Qualification and the drive
# --------------------------------------------------------------------------


def qualify(root: Path, home: Path, *, port: int, timeout: int) -> dict:
    """Run the production-contract doctor against the stub.

    The doctor is a subprocess for the same reason the ladder runs it as
    one: it owns its own report writing, and the loopback server in THIS
    process serves it over ordinary TCP.
    """

    out = root / "production-contract-qualification.json"
    environment = dict(os.environ)
    environment[TEST_CREDENTIAL_ENV] = TEST_CREDENTIAL
    environment["DEEPREASON_HOME"] = str(home)
    environment["DEEPREASON_QUALIFY_CONCURRENCY"] = "2"
    environment["NO_PROXY"] = "127.0.0.1,localhost"
    environment["no_proxy"] = "127.0.0.1,localhost"
    environment.pop("HTTP_PROXY", None)
    environment.pop("HTTPS_PROXY", None)
    environment.pop("http_proxy", None)
    environment.pop("https_proxy", None)

    started = time.monotonic()
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "deepreason",
            "doctor",
            "--run-manifest",
            str(root / "run-manifest.json"),
            "--production-contracts",
            "--out",
            str(out),
        ],
        cwd=str(REPO),
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.monotonic() - started
    return {
        "returncode": completed.returncode,
        "elapsed_s": round(elapsed, 1),
        "report_written": out.exists(),
        "stdout_tail": completed.stdout[-1200:],
        "stderr_tail": completed.stderr[-1200:],
    }


def drive(root: Path, *, cycles: int, token_budget: int | None) -> dict:
    """Drive the managed path and return its typed terminal.

    ``start_manifest_run`` IS the one run path: ``deepreason run
    --run-manifest`` is a rendering shell over it (operator law 2026-08-13),
    so calling it directly drives identical code with one less process
    boundary -- and, unlike the CLI, lets this instrument keep the progress
    stream.
    """

    from deepreason.application import TEXT_RUN_SERVICE, InspectTextRunIntentV1
    from deepreason.run_manifest import load_run_manifest

    manifest = load_run_manifest(root / "run-manifest.json")
    progress: list[dict] = []

    def on_progress(event: dict) -> None:
        progress.append(event)

    started = time.monotonic()
    typed_error = None
    terminal_payload: dict = {}
    try:
        accepted = TEXT_RUN_SERVICE.start_manifest_run(
            root=root,
            manifest=manifest,
            problem_path=root / "problem.json",
            cycles=cycles,
            token_budget=token_budget,
            progress_callback=on_progress,
        )
        TEXT_RUN_SERVICE.wait(accepted.root)
        terminal = TEXT_RUN_SERVICE.result(
            InspectTextRunIntentV1(root=accepted.root)
        )
        terminal_payload = terminal.presentation_payload()
    except (OSError, ValueError) as error:
        # A typed refusal is a legitimate outcome to REPORT; only an untyped
        # exception escaping to the caller is an instrument failure.
        typed_error = f"{type(error).__name__}: {error}"

    return {
        "elapsed_s": round(time.monotonic() - started, 1),
        "typed_error": typed_error,
        "terminal": terminal_payload,
        "progress_events": len(progress),
        "max_cycle_seen": max(
            (int(e.get("cycle", 0) or 0) for e in progress), default=0
        ),
    }


# --------------------------------------------------------------------------
# Assessment -- S1 terminal assertions, S2 seam census, S4 honesty
# --------------------------------------------------------------------------


def _status(root: Path) -> dict:
    path = root / "run-status.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _object_counts(root: Path) -> dict[str, int]:
    objects = root / "objects"
    if not objects.is_dir():
        return {}
    return {
        child.name: sum(1 for _ in child.glob("*.json"))
        for child in sorted(objects.iterdir())
        if child.is_dir()
    }


def _channel_facts(root: Path, criteria: list[str]) -> dict:
    """Did the in-run checker FIRE, and did its refutations REACH the writer?

    Two counts, and they are separate on purpose because the failure this
    answers is the one P-C1 paid a whole run for: a battery that is present,
    configured and INERT produces a record that reads exactly like "the model
    could not do it".  The rebuilt shape adds a second way to be silently
    inert -- a discharge channel that is on in the YAML and off at runtime
    (`DR-INV-frozen-surfaces`; the field is popped from the manifest's config
    echo) -- and that one is invisible in the same way.

    ``refutations`` counts DEMONSTRATIVE fail warrants naming one of this
    case's own criteria, read from the log rather than from any summary: the
    record is the only admissible evidence.  ``channel_measures`` counts the
    three Measures REBUILD F1 declares in ``signals.py`` -- ``discharge-reask``,
    ``discharge-undischarged`` and ``discharge:<kind>``.  A run with the first
    and not the second executed every candidate and told nobody.
    """
    wanted = set(criteria)
    facts: dict = {"criteria_watched": sorted(wanted)}

    # The two halves are read INDEPENDENTLY and each records its own failure.
    # A single try would let one reader's exception report the other's count as
    # absent, and "the channel carried nothing" is exactly the finding that
    # must never be manufactured by a bug in the instrument.
    try:
        refutations = 0
        directory = root / "objects" / "warrant"
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text())["data"]
            if data.get("verdict") == "fail" and data.get("commitment") in wanted:
                refutations += 1
        facts["demonstrative_refutations"] = refutations
    except Exception as error:
        facts["refutation_error"] = f"{type(error).__name__}: {error}"

    try:
        from deepreason.harness import Harness

        measures: dict[str, int] = {}
        for event in Harness(root, read_only=True).log.read():
            inputs = list(event.inputs)
            if not inputs:
                continue
            head = str(inputs[0])
            if head.startswith("discharge"):
                key = head.split(":", 1)[0] if head.startswith("discharge:") else head
                measures[key] = measures.get(key, 0) + 1
        facts["channel_measures"] = measures
    except Exception as error:
        facts["measure_error"] = f"{type(error).__name__}: {error}"

    return facts


def _attempt_facts(root: Path) -> dict:
    """Repair depth and lease completeness, from the attempt records."""

    directory = root / "objects" / "workflow-provider-attempt-v1"
    attempts = 0
    repairs = 0
    leaseless = 0
    contracts: set[str] = set()
    roles: set[str] = set()
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            try:
                data = json.loads(path.read_text())["data"]
            except (OSError, KeyError, json.JSONDecodeError):
                continue
            attempts += 1
            if int(data.get("attempt_index", 0) or 0) > 0:
                repairs += 1
            lease = data.get("route_lease") or {}
            if not all(k in lease for k in ("role", "seat", "route_sha256")):
                leaseless += 1
            else:
                roles.add(str(lease["role"]))
            if data.get("contract_id"):
                contracts.add(str(data["contract_id"]))
    # `repairs` above counts provider attempts past index 0, which is NOT the
    # same fact as a repair task having been written and read back.  The modes
    # below are read from the repair preparations themselves, so a D1 verdict
    # cannot claim the repair ladder was walked on the strength of an attempt
    # index alone.
    modes: list[str] = []
    preparations = root / "objects" / "workflow-work-preparation-v1"
    if preparations.is_dir():
        for path in sorted(preparations.glob("*.json")):
            try:
                payload = json.loads(path.read_text())["data"]["task_payload_value"]
            except (OSError, KeyError, TypeError, json.JSONDecodeError):
                continue
            if (
                isinstance(payload, dict)
                and payload.get("schema") == "repair.semantic-task.v1"
            ):
                modes.append(str(payload.get("mode")))
    return {
        "attempts": attempts,
        "repairs": repairs,
        "repair_payloads": len(modes),
        "repair_modes": sorted(set(modes)),
        "attempts_without_complete_lease": leaseless,
        "distinct_contracts": sorted(contracts),
        "distinct_roles": sorted(roles),
    }


def _terminal_text(status: dict, driven: dict) -> str:
    parts = [
        str(status.get("message") or ""),
        str(status.get("stop_reason") or ""),
        str(driven.get("typed_error") or ""),
        json.dumps(driven.get("terminal") or {}),
    ]
    return "\n".join(parts)


def assess_seams(root: Path, status: dict, driven: dict) -> list[dict]:
    """One row per formerly-fatal seam: reached, failed, or not-coverable."""

    counts = _object_counts(root)
    facts = _attempt_facts(root)
    text = _terminal_text(status, driven)
    rows: list[dict] = []

    for seam in SEAMS:
        reached = {name: counts.get(name, 0) for name in seam.reached_by}
        fatal_present = {
            name: counts.get(name, 0)
            for name in seam.fatal_objects
            if counts.get(name, 0)
        }
        named = [needle for needle in seam.fatal_messages if needle in text]

        detail: dict = {"reached_by": reached}
        if seam.id == "D1-seat-contract":
            detail["repairs"] = facts["repairs"]
            detail["repair_payloads"] = facts["repair_payloads"]
            detail["repair_modes"] = facts["repair_modes"]
            detail["distinct_contracts"] = facts["distinct_contracts"]
        if seam.id == "D2-route-lease":
            detail["attempts"] = facts["attempts"]
            detail["attempts_without_complete_lease"] = facts[
                "attempts_without_complete_lease"
            ]

        if named or fatal_present:
            disposition = "failed"
            reason = "; ".join(
                named + [f"{k} x{v}" for k, v in fatal_present.items()]
            )
        elif not any(reached.values()):
            # Absence of failure over code that never ran is not coverage.
            disposition = "not-coverable"
            reason = (
                "no record object of "
                + ", ".join(seam.reached_by)
                + " was written -- this run never reached the seam"
            )
        elif seam.id == "D1-seat-contract" and facts["repair_payloads"] == 0:
            # Judged on repair PAYLOADS, not on `repairs`: an attempt past
            # index 0 is not proof that a repair task was written and read.
            disposition = "partial"
            reason = (
                "seat contracts exercised, but zero repair tasks recorded: an "
                "un-induced stub always returns a schema-valid response, so "
                "no repair is ever requested. Re-run with --induce-repairs N "
                "(and --induce-repair-kind unparseable, or alternate, to "
                "reach whole_object_syntax as well as patch)"
            )
        elif seam.id == "D2-route-lease" and facts["attempts_without_complete_lease"]:
            disposition = "failed"
            reason = (
                f"{facts['attempts_without_complete_lease']} attempt(s) carry "
                "an incomplete route_lease"
            )
        else:
            disposition = "covered"
            reason = ""

        rows.append(
            {
                "id": seam.id,
                "what": seam.what,
                "disposition": disposition,
                "reason": reason,
                "expected_red_until": EXPECTED_RED.get(seam.id),
                "detail": detail,
            }
        )
    return rows


def assess_run(
    root: Path, driven: dict, *, cycles: int, case: SoakCase | None = None,
    criteria: list[str] | None = None,
) -> list[dict]:
    """S1's four terminal assertions, plus any the case itself requires.

    A1-A4 are universal.  A5/A6 are added only for a case that declares an
    IN-RUN EVALUATION, because for such a case "the run reached cycle N" is
    not the whole question: a battery that never fired, or that fired and
    reached nobody, produces a green soak and a dead experiment.
    """

    status = _status(root)
    stop_reason = str(status.get("stop_reason") or "")
    state = str(status.get("state") or "")
    reached_cycle = max(
        int(status.get("cycle", 0) or 0), int(driven.get("max_cycle_seen", 0) or 0)
    )

    try:
        from deepreason.invariants import verify_root

        verdict = verify_root(root)
        violations = list(verdict.get("violations") or [])
        verify_error = None
    except Exception as error:  # an unreadable root is itself the finding
        violations = []
        verify_error = f"{type(error).__name__}: {error}"

    checks = [
        {
            "id": "A1-typed-terminal",
            "ok": bool(state) and bool(stop_reason) and driven["typed_error"] is None,
            "detail": (
                f"state={state!r} stop_reason={stop_reason!r} "
                f"typed_error={driven['typed_error']!r}"
            ),
        },
        {
            "id": "A2-no-operational-failure",
            "ok": stop_reason != "operational_failure",
            "detail": (
                f"stop_reason={stop_reason!r}"
                + (
                    f" message={status.get('message')!r}"
                    if stop_reason == "operational_failure"
                    else ""
                )
            ),
        },
        {
            "id": "A3-verify-root-clean",
            "ok": verify_error is None and not violations,
            "detail": (
                verify_error
                if verify_error
                else f"{len(violations)} violation(s)"
                + (f": {violations[:3]}" if violations else "")
            ),
        },
        {
            "id": "A4-cycles-reached",
            "ok": reached_cycle > DEEPEST_RECORDED_DEATH_CYCLE,
            "detail": (
                f"reached cycle {reached_cycle} of {cycles} requested; the "
                f"deepest recorded death was cycle "
                f"{DEEPEST_RECORDED_DEATH_CYCLE}"
            ),
        },
    ]

    if case is not None and case.id in IN_RUN_EVALUATION_CASES:
        facts = _channel_facts(root, criteria or [])
        checks.append(
            {
                "id": "A5-in-run-checker-fired",
                "ok": int(facts.get("demonstrative_refutations") or 0) > 0,
                "detail": (
                    f"{facts.get('demonstrative_refutations')} demonstrative "
                    f"fail warrant(s) naming {facts.get('criteria_watched')}"
                    + (f" -- {facts['refutation_error']}" if facts.get("refutation_error") else "")
                ),
            }
        )
        checks.append(
            {
                "id": "A6-discharge-channel-carried-them",
                "ok": bool(facts.get("channel_measures")),
                "detail": (
                    f"REBUILD F1 channel Measures on the record: "
                    f"{facts.get('channel_measures')}"
                    + (f" -- {facts['measure_error']}" if facts.get("measure_error") else "")
                ),
            }
        )

    return checks


# --------------------------------------------------------------------------
# Repair induction -- the one seam a always-valid stub cannot reach
# --------------------------------------------------------------------------


# What an induced first response looks like, and therefore WHICH repair mode
# the session can take against it.  This is not a style choice: a parseable
# response leaves a JSON baseline, so the repair turn is `patch`; only an
# UNPARSEABLE one leaves no baseline, and that is the sole route to
# `whole_object_syntax` -- the mode that killed technique run-456885c569c0f4f7
# at cycle 2 and that no offline instrument could reach before.
INDUCTION_KINDS = ("invalid", "unparseable", "alternate")


def install_repair_inducer(limit: int, *, kind: str = "invalid") -> dict[str, str]:
    """Make the stub answer the FIRST request per wire schema unusably once.

    D1's recorded death is route-seat capability exhaustion, and a seat only
    exhausts a contract by REPAIRING against it.  A stub that always returns
    a schema-valid response can never drive ``attempt_index`` past 0, so the
    repair ladder -- and everything downstream of it -- is invisible to an
    otherwise faithful soak.  Rather than mint a second fixture, this wraps
    ``wheel_operational_smoke.response_for_schema`` in place: the first
    response for each distinct wire schema title is replaced, and every later
    response for that title is the smoke's own value, so the run proceeds.

    ``kind`` selects what the replacement is, which selects the repair MODE
    the run then takes: ``invalid`` is well-formed JSON satisfying no closed
    schema (-> `patch`), ``unparseable`` is not JSON at all (->
    `whole_object_syntax`), ``alternate`` walks the two so one soak drives
    both.  Returns the induced titles mapped to the kind each received.

    Bounded by ``limit`` distinct titles so induction cannot become an
    unbounded fault injector: the point is to REACH the repair path, not to
    starve the run.
    """

    if kind not in INDUCTION_KINDS:
        raise ValueError(f"unknown induction kind {kind!r}")
    induced: dict[str, str] = {}
    original = _smoke.response_for_schema

    def wrapper(schema: dict, prompt: str):
        title = str(schema.get("title") or "<untitled>")
        if title not in induced and len(induced) < limit:
            chosen = kind
            if kind == "alternate":
                chosen = "unparseable" if len(induced) % 2 == 0 else "invalid"
            induced[title] = chosen
            if chosen == "unparseable":
                # RawResponse is served without JSON encoding, so the adapter
                # has nothing to parse and no pointer can be authorized
                # against a baseline that does not exist. A plain str would be
                # encoded into a quoted JSON string, which parses.
                return _smoke.RawResponse("I cannot answer that as JSON. {{{")
            # Well-formed JSON, no property any closed wire schema declares.
            return {"soak_induced_repair": title}
        return original(schema, prompt)

    _smoke.response_for_schema = wrapper
    return induced

# --------------------------------------------------------------------------
# Reporting and entry point
# --------------------------------------------------------------------------


def _render(report: dict) -> None:
    print()
    print("=" * 72)
    print(f"CYCLE SOAK -- case {report['case']['case']}")
    print("=" * 72)
    print(f"  manifest sha256        {report['case']['manifest_sha256']}")
    print(f"  criteria               {', '.join(report['case']['criteria'])}")
    print(f"  attached evidence      {report['case']['attached_evidence_enabled']}")
    print(f"  cycles requested       {report['cycles']}")
    print(f"  qualification          rc={report['qualification']['returncode']} "
          f"({report['qualification']['elapsed_s']}s)")
    print(f"  drive                  {report['drive']['elapsed_s']}s, "
          f"{report['drive']['progress_events']} progress events")

    print()
    print("-- S1 run assertions " + "-" * 51)
    for check in report["checks"]:
        print(f"  [{'PASS' if check['ok'] else 'FAIL'}] {check['id']:<28} "
              f"{check['detail']}")

    print()
    print("-- S2/S4 seam coverage " + "-" * 49)
    for row in report["seams"]:
        mark = {
            "covered": "PASS",
            "failed": "FAIL",
            "partial": "PART",
            "not-coverable": "N/CV",
        }[row["disposition"]]
        suffix = ""
        if row["disposition"] == "failed" and row["expected_red_until"]:
            suffix = f"  (EXPECTED RED until {row['expected_red_until']})"
        print(f"  [{mark}] {row['id']:<24} {row['what']}{suffix}")
        if row["reason"]:
            print(f"         reason: {row['reason']}")
        print(f"         reached: {row['detail']['reached_by']}")

    print()
    print("-- record census " + "-" * 55)
    for name, count in sorted(report["object_counts"].items()):
        print(f"  {count:>6}  {name}")
    print()


# A2 and A4 are DOWNSTREAM of the terminal: when a seam kills the run, the
# stop reason is that seam's message (A2) and the cycle depth is wherever it
# died (A4).  Scoring those as unexpected failures would make every
# expected-red seam report exit 1, which is the one distinction this exit
# status exists to draw.  A1 and A3 are never downstream in this way -- an
# untyped exception or a corrupt record is a real failure whatever killed the
# run -- so they are never downgraded.
_TERMINAL_DOWNSTREAM_CHECKS = frozenset({"A2-no-operational-failure",
                                         "A4-cycles-reached"})


def _verdict(report: dict) -> int:
    failed_seams = [r for r in report["seams"] if r["disposition"] == "failed"]
    failed_checks = [c for c in report["checks"] if not c["ok"]]
    only_expected_red = bool(failed_seams) and all(
        r["expected_red_until"] for r in failed_seams
    )

    if only_expected_red:
        # Downgrade only the checks this seam's own terminal explains, and
        # only when the terminal message actually names it.
        named = any(
            needle in str(report.get("status", {}).get("message") or "")
            for seam in SEAMS
            if seam.id in {r["id"] for r in failed_seams}
            for needle in seam.fatal_messages
        )
        if named:
            failed_checks = [
                c for c in failed_checks
                if c["id"] not in _TERMINAL_DOWNSTREAM_CHECKS
            ]

    if failed_checks:
        return 1
    if not failed_seams:
        return 0
    return 3 if only_expected_red else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline cycle soak over the managed run path."
    )
    parser.add_argument("--case", default="epoch3", help="config case to soak")
    parser.add_argument("--list-cases", action="store_true")
    parser.add_argument("--cycles", type=int, default=None)
    parser.add_argument("--token-budget", type=int, default=None)
    parser.add_argument("--out", default=None, help="working directory")
    parser.add_argument(
        "--keep", action="store_true", help="keep the working directory"
    )
    parser.add_argument("--qualify-timeout", type=int, default=1800)
    parser.add_argument(
        "--induce-repairs",
        type=int,
        default=0,
        metavar="N",
        help=(
            "force one repair for each of the first N distinct wire schemas, "
            "so the D1 seat-contract repair ladder is actually exercised "
            "(0 = faithful drive, the default)"
        ),
    )
    parser.add_argument(
        "--induce-repair-kind",
        choices=INDUCTION_KINDS,
        default="invalid",
        help=(
            "what the induced response is, and so which repair MODE the run "
            "takes: invalid = parseable but schema-invalid (-> patch, the "
            "default and the pre-existing behaviour); unparseable = not JSON "
            "(-> whole_object_syntax); alternate = both"
        ),
    )
    args = parser.parse_args(argv)

    if args.list_cases:
        for case in CASES.values():
            print(f"{case.id:<12} {case.description}")
        return 0

    if args.case not in CASES:
        print(f"unknown case {args.case!r}; try --list-cases", file=sys.stderr)
        return 2
    case = CASES[args.case]
    cycles = args.cycles if args.cycles is not None else case.default_cycles
    token_budget = (
        args.token_budget
        if args.token_budget is not None
        else case.default_token_budget
    )

    workdir = Path(args.out).resolve() if args.out else Path(
        tempfile.mkdtemp(prefix="cycle-soak-")
    )
    workdir.mkdir(parents=True, exist_ok=True)
    root = workdir / "run"
    root.mkdir(parents=True, exist_ok=True)
    home = workdir / "home"
    home.mkdir(parents=True, exist_ok=True)

    os.environ[TEST_CREDENTIAL_ENV] = TEST_CREDENTIAL
    os.environ["DEEPREASON_HOME"] = str(home)
    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    os.environ["no_proxy"] = "127.0.0.1,localhost"
    for proxy in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        os.environ.pop(proxy, None)

    state = ProviderState()
    server, thread = _provider_server(state)
    port = int(server.server_address[1])
    print(f"[soak] stub provider on 127.0.0.1:{port} "
          f"(reused from wheel_operational_smoke)")
    print(f"[soak] working directory {workdir}")

    induced: dict[str, str] = {}

    report: dict = {
        "cycles": cycles,
        "token_budget": token_budget,
        "induce_repairs": args.induce_repairs,
        "induce_repair_kind": args.induce_repair_kind,
    }
    try:
        report["case"] = build_root(case, root, port=port)
        print(f"[soak] built root: manifest {report['case']['manifest_sha256'][:16]}"
              f"…  criteria {report['case']['criteria']}")

        report["qualification"] = qualify(
            root, home, port=port, timeout=args.qualify_timeout
        )
        if report["qualification"]["returncode"] != 0:
            print("[soak] QUALIFY FAILED", file=sys.stderr)
            print(report["qualification"]["stderr_tail"], file=sys.stderr)
            print(report["qualification"]["stdout_tail"], file=sys.stderr)
            return 1
        print(f"[soak] qualified in {report['qualification']['elapsed_s']}s")

        # Induction is installed AFTER qualification, deliberately. The
        # battery dispatches its own wire schemas and runs first; inducing
        # against those would spend the whole budget before the run starts
        # (measured: the first three induced titles were qualification-only
        # candidate wires, and the run's own `conjecturer.turn.v6` never
        # induced) and would corrupt the very report the launch depends on.
        if args.induce_repairs:
            induced = install_repair_inducer(
                args.induce_repairs, kind=args.induce_repair_kind
            )
            print(f"[soak] repair induction ON ({args.induce_repair_kind}) for "
                  f"the first {args.induce_repairs} wire schema(s) of the RUN")

        print(f"[soak] driving {cycles} cycles …")
        report["drive"] = drive(root, cycles=cycles, token_budget=token_budget)
        report["status"] = _status(root)
        report["object_counts"] = _object_counts(root)
        report["attempts"] = _attempt_facts(root)
        report["checks"] = assess_run(
            root, report["drive"], cycles=cycles, case=case,
            criteria=list(report["case"].get("criteria") or []),
        )
        report["seams"] = assess_seams(root, report["status"], report["drive"])
        report["provider_calls"] = state.total_calls
        report["induced_schemas"] = dict(sorted(induced.items()))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    _render(report)
    exit_status = _verdict(report)
    report["exit_status"] = exit_status
    (workdir / "soak-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n"
    )
    print(f"[soak] report {workdir / 'soak-report.json'}")
    print(f"[soak] exit {exit_status} "
          f"({ {0: 'clean', 1: 'FAILED', 3: 'expected-red only'}[exit_status] })")

    if not args.keep and not args.out:
        shutil.rmtree(workdir, ignore_errors=True)
    return exit_status


if __name__ == "__main__":
    raise SystemExit(main())
