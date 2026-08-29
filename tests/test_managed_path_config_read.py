"""Regression (tranche 2026-08-29-defect-managed-path-config-read, P14):
`deepreason reason` must read the operator's run configuration.

The managed path constructs its `Config` from the provider profile
(`preparation._config_for_profile`) and never opens the file `--config` names,
so a `run-config.yaml` switch is neither carried into the run nor disclosed as
uncarried. Record evidence: 41 committed managed-path run roots share ONE
engine-config echo and carry zero compile notices
(`experiments/2026-08-29-defect-managed-path-config-read/probe/echo_census.out`).

Operator law this enforces (CLAUDE.md, 2026-08-28, verbatim): "configuration of
seats need to be able to turn gates on and off at will ... Gates are always
optional: with warnings."
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from deepreason import preparation
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.cli.main import _cmd_reason, build_parser
from deepreason.config import Config, load as load_config
from deepreason.preparation import (
    RunPreparationRequestV1,
    _request_digest,
    build_preparation_manifest,
    qualification_subject_manifest,
)
from deepreason.provider_profile import ProviderProfileV1
from deepreason.qualification import (
    qualification_subject_digest,
    resolve_completed_qualification,
)
from deepreason.run_manifest import (
    V3_CANONICAL_ROLES,
    RunManifestError,
    config_from_run_manifest,
)

STAMP = datetime(2026, 7, 23, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# The five switches P-T1's own run-config.yaml set and lost, plus the two the
# 2026-08-12 operator config sets. Values are the operator's, not invented.
OPERATOR_YAML = """\
JUDGE_SEATS_ENABLED: true
ADJUDICATION_STATUS_AUTHORITY_ENABLED: true
SCHOOL_SEATS_ENABLED: true
SCOPE_MAX_NODES: 41
JUDGE_SUMMONS_PER_CYCLE: 3
"""


def _profile() -> ProviderProfileV1:
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


def _managed_manifest(profile, operator: Config | None):
    """Prepare the MANAGED manifest, optionally under the operator's Config.

    THE ONE FIX-SHAPE ASSUMPTION IN THIS FILE, stated so a fix that chooses a
    different route updates one helper instead of three tests: the managed
    manifest builder must be able to be GIVEN the operator's configuration.
    Whether the route is a `Config` object, a path, or a field on
    `RunPreparationRequestV1` is the fix's business; that some route exists is
    the defect.
    """
    if operator is None:
        return build_preparation_manifest(
            profile, question="Why is the sky blue?", compiled_at=STAMP
        )
    try:
        return build_preparation_manifest(
            profile,
            question="Why is the sky blue?",
            compiled_at=STAMP,
            config=operator,
        )
    except TypeError as error:
        pytest.fail(
            "MANAGED PATH HAS NO CONFIGURATION INPUT: build_preparation_manifest "
            f"cannot be given the operator's Config at all -- {error}"
        )


def test_reason_forwards_the_operator_config_to_preparation(tmp_path, monkeypatch):
    """`deepreason --config FILE reason Q` must let FILE reach preparation.

    Deliberately neutral about HOW: the assertion is satisfied by forwarding
    the path, or the loaded Config, or anything carrying the operator's value.
    It fails only if NOTHING about FILE reaches the preparation service, which
    is the state of the tree today.
    """
    config_path = tmp_path / "run-config.yaml"
    config_path.write_text(OPERATOR_YAML)

    seen: dict[str, object] = {}

    class _Stop(Exception):
        pass

    class _CapturingService:
        def __init__(self, *args, **kwargs):
            seen["init_args"] = args
            seen["init_kwargs"] = kwargs

        def prepare(self, request, *args, **kwargs):
            seen["request"] = request
            seen["prepare_args"] = args
            seen["prepare_kwargs"] = kwargs
            raise _Stop()

    monkeypatch.setattr(preparation, "RunPreparationService", _CapturingService)
    monkeypatch.setattr(
        "deepreason.cli.main._reasoning_disabled_refusal", lambda _profile: None
    )

    args = build_parser().parse_args(
        ["--config", str(config_path), "reason", "Why is the sky blue?"]
    )
    assert args.config == str(config_path), "the global --config flag must parse"

    with pytest.raises(_Stop):
        _cmd_reason(args)

    forwarded = repr(seen)
    assert str(config_path) in forwarded or "JUDGE_SEATS_ENABLED" in forwarded, (
        "deepreason reason discards --config: nothing about the operator's "
        f"configuration file reached RunPreparationService. Captured: {forwarded}"
    )


def test_managed_manifest_carries_or_discloses_every_operator_setting(tmp_path):
    """Field by field: carried into the run, OR disclosed as not carried.

    This is GOAL.md's success criterion verbatim, and it is the disjunction the
    2026-08-28 operator law requires -- a gate is either on because the
    configuration turned it on, or the record says why it is not.
    """
    config_path = tmp_path / "run-config.yaml"
    config_path.write_text(OPERATOR_YAML)
    operator = load_config(config_path)

    default = Config()
    configured = {
        name: getattr(operator, name)
        for name in type(default).model_fields
        if getattr(operator, name) != getattr(default, name)
    }
    assert configured, "the fixture must set something away from its default"

    profile = _profile()
    manifest = _managed_manifest(profile, operator)
    runtime = config_from_run_manifest(manifest)
    disclosed = {
        notice.pointer
        for notice in (manifest.compile_notices or ())
        if notice.code == "ENGINE_CONFIG_FIELD_NOT_CARRIED"
    }

    unanswered = [
        name
        for name, value in configured.items()
        if getattr(runtime, name, object()) != value
        and f"/engine_config/{name}" not in disclosed
    ]
    assert not unanswered, (
        f"{len(unanswered)} of {len(configured)} operator settings are neither "
        f"carried into the run nor disclosed as uncarried: {sorted(unanswered)}"
    )


def test_a_default_valued_operator_config_changes_nothing(tmp_path):
    """The half that must NOT move: reading a config costs nothing at defaults.

    Passes today (vacuously -- nothing is read) and must keep passing after the
    fix, or every existing home owes a ~14-minute qualification battery for a
    configuration that asked for nothing.
    """
    profile = _profile()
    baseline = _managed_manifest(profile, None)

    config_path = tmp_path / "run-config.yaml"
    config_path.write_text("{}\n")
    operator = load_config(config_path)
    assert operator == Config(), "an empty profile must load as the typed defaults"

    try:
        carried = build_preparation_manifest(
            profile,
            question="Why is the sky blue?",
            compiled_at=STAMP,
            config=operator,
        )
    except TypeError:
        pytest.skip(
            "no configuration route exists yet; this test pins the post-fix "
            "guarantee and is asserted by the fix tranche"
        )
    assert carried.sha256 == baseline.sha256
    assert carried.source_config_hash == baseline.source_config_hash


# --------------------------------------------------------------------------
# R4-R8: the limbs stage 2 measured and stage 1 did not see.
#   probe/lifecycle_gap.out         -- 8 of 8 committed configs REFUSED
#   probe/school_seat_deadlock.out  -- --school-seat unreachable for every profile
#   probe/request_identity_baseline.out -- the historical digest R6 pins
# --------------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[1]

# probe/request_identity_baseline.out, re-derived on this tree. A question-only
# request must keep this identity: admitting configuration into run identity is
# conditional, exactly as `dossier_digest` was admitted.
QUESTION_ONLY_REQUEST_DIGEST = (
    "7ea3afd5a387993d19999918ea26698529245bbf1c1ba23dc5ac6a22e03c93e9"
)


def _committed_configs() -> list[Path]:
    """Every committed operator configuration, or none -- absence-tolerant."""
    return sorted(REPO.glob("experiments/*/run-config.yaml"))


def _distinct_profile() -> ProviderProfileV1:
    return ProviderProfileV1.create(
        provider="openai",
        endpoint="https://distinct.example.test/v1",
        model_id="model-b",
        model_revision="rev-b",
        family="family-b",
        context_window_tokens=262144,
        maximum_completion_tokens=4096,
        credential_env="DEEPREASON_TEST_KEY_B",
    )


def _passing_battery(manifest):
    """A production-contract battery that passes every case, without a provider."""
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


def test_qualify_and_reason_agree_on_the_subject_for_every_configuration():
    """ARCHITECTURE TEST (modularity law, 2026-08-26): one configuration door.

    `deepreason qualify` warms a subject; `deepreason reason` needs one. If the
    two builders can diverge on what a configuration means, a configured run is
    unqualifiable -- the operations-parity failure of 2026-08-13. This goes RED
    the moment either consumer stops going through the same `config=` door.
    """
    profile = _profile()
    cases: list[tuple[str, Config | None]] = [("<defaults>", None)]
    cases.extend((str(path.parent.name), load_config(path)) for path in _committed_configs())

    disagreed = []
    for label, operator in cases:
        qualify_subject = qualification_subject_digest(
            qualification_subject_manifest(profile, config=operator), profile
        )
        reason_subject = qualification_subject_digest(
            build_preparation_manifest(
                profile,
                question="Why is the sky blue?",
                compiled_at=STAMP,
                config=operator,
            ),
            profile,
        )
        if qualify_subject != reason_subject:
            disagreed.append((label, qualify_subject[:16], reason_subject[:16]))

    assert not disagreed, (
        "qualify and reason address DIFFERENT qualification subjects for "
        f"{len(disagreed)} of {len(cases)} configurations, so the battery one "
        f"warms is not the battery the other needs: {disagreed}"
    )


def test_a_configured_run_is_refused_nowhere_a_default_run_starts(tmp_path):
    """The operational consequence of the test above, measured end to end.

    probe/lifecycle_gap.out recorded 8 of 8 committed configurations REFUSED
    QUALIFICATION_NOT_CONFIGURED on a home that had fully qualified, with no
    committed command able to clear the refusal. Seed the cache the way
    `deepreason qualify --config F` would, then prepare the way
    `deepreason reason --config F` would: it must start.
    """
    profile = _profile()
    cases: list[tuple[str, Config | None]] = [("<defaults>", None)]
    cases.extend((str(path.parent.name), load_config(path)) for path in _committed_configs())

    refused = []
    for label, operator in cases:
        cache = tmp_path / f"cache-{abs(hash(label))}"
        resolve_completed_qualification(
            qualification_subject_manifest(profile, config=operator),
            profile,
            cache_dir=cache,
            executor=_passing_battery,
        )
        prepared = build_preparation_manifest(
            profile,
            question="Why is the sky blue?",
            compiled_at=STAMP,
            config=operator,
        )
        try:
            resolve_completed_qualification(prepared, profile, cache_dir=cache)
        except ValueError as error:
            refused.append((label, getattr(error, "code", type(error).__name__)))

    assert not refused, (
        f"{len(refused)} of {len(cases)} configurations are refused on a home "
        f"that just qualified THAT configuration: {refused}"
    )


def test_run_identity_covers_the_configuration(tmp_path):
    """Two configurations of one question are two runs, not one refused run.

    Both directions in one test, because both mutations are real: omitting the
    configuration from the request digest collides the two ids (the second run
    is refused RUN_ALREADY_STARTED against the first's root), and admitting it
    UNCONDITIONALLY moves every historical question-only run id.
    """
    profile = _profile()
    question = "Why is the sky blue?"

    question_only = RunPreparationRequestV1(question=question)
    assert _request_digest(question_only, profile) == QUESTION_ONLY_REQUEST_DIGEST, (
        "a question-only request digest moved: every historical managed run id "
        "is derived from it"
    )
    assert (
        _request_digest(question_only, profile, config=None)
        == QUESTION_ONLY_REQUEST_DIGEST
    ), "an ABSENT configuration must contribute nothing to run identity"

    judges_on = tmp_path / "judges-on.yaml"
    judges_on.write_text("JUDGE_SEATS_ENABLED: true\n")
    judges_off = tmp_path / "judges-off.yaml"
    judges_off.write_text("JUDGE_SEATS_ENABLED: false\n")

    request_on = RunPreparationRequestV1(question=question, config_path=str(judges_on))
    request_off = RunPreparationRequestV1(question=question, config_path=str(judges_off))
    digest_on = _request_digest(request_on, profile, config=load_config(judges_on))
    digest_off = _request_digest(request_off, profile, config=load_config(judges_off))

    assert digest_on != digest_off, (
        "two different configurations of one question share a managed run id, "
        "so the second run is refused against the first's root"
    )
    assert digest_on != QUESTION_ONLY_REQUEST_DIGEST

    # Semantic, not textual: reformatting a file does not mint a new run.
    reformatted = tmp_path / "judges-on-reformatted.yaml"
    reformatted.write_text("# a comment the operator added\nJUDGE_SEATS_ENABLED:   true\n")
    request_reformatted = RunPreparationRequestV1(
        question=question, config_path=str(reformatted)
    )
    assert (
        _request_digest(request_reformatted, profile, config=load_config(reformatted))
        == digest_on
    ), "run identity must follow the configuration's VALUES, not its bytes"


def test_the_provider_profile_owns_routes_under_a_configured_run():
    """The deterministic resolution rule, in the one place it must not slip.

    A configuration file may not redirect a managed run to an arbitrary
    endpoint: the provider profile holds the credential and the seat-binding
    mechanism owns per-role divergence. The rule is a resolution, never a
    refusal (all-configurations law, 2026-08-12) -- the file still compiles.
    """
    profile = _profile()
    other = _distinct_profile()
    hijack = Config(
        roles={role: dict(other.endpoint_spec()) for role in V3_CANONICAL_ROLES}
    )

    baseline = build_preparation_manifest(
        profile, question="Why is the sky blue?", compiled_at=STAMP
    )
    configured = build_preparation_manifest(
        profile, question="Why is the sky blue?", compiled_at=STAMP, config=hijack
    )

    assert configured.roles == baseline.roles, (
        "a configuration file redirected a managed run's routes, bypassing the "
        "provider-profile credential model"
    )
    endpoint_ids = {
        route.endpoint_id
        for routes in configured.roles.values()
        for route in (routes if isinstance(routes, list) else [routes])
    }
    assert endpoint_ids == {profile.endpoint_id}


def test_a_configured_school_seat_opt_in_compiles():
    """probe/school_seat_deadlock.out: `--school-seat` was unreachable, always.

    `_config_for_profile` synthesised SCHOOL_SEATS_ENABLED=False for every
    provider profile, so the gate refused for all of them -- while the shipped
    `--school-seat` help text says the master gate "is still set via --config",
    the file that was never read. A flag that gates a seat-configuration path
    and cannot be turned on is the sharpest form of the 2026-08-28 law's
    violation.
    """
    profile = _profile()
    distinct = _distinct_profile()

    # Control: the gate still refuses typed when nothing turned it on.
    with pytest.raises(RunManifestError, match="SCHOOL_SEATS_DISABLED"):
        build_preparation_manifest(
            profile,
            question="Why is the sky blue?",
            compiled_at=STAMP,
            school_seats={"school-1": distinct},
        )

    manifest = build_preparation_manifest(
        profile,
        question="Why is the sky blue?",
        compiled_at=STAMP,
        school_seats={"school-1": distinct},
        config=Config(SCHOOL_SEATS_ENABLED=True),
    )
    conjecturer_routes = manifest.roles["conjecturer"]
    assert len(conjecturer_routes) == 2
    assert conjecturer_routes[0].endpoint_id == profile.endpoint_id
    assert conjecturer_routes[1].endpoint_id == distinct.endpoint_id
    assert manifest.control_plane_policy.school_execution.mode == "route_bound"
