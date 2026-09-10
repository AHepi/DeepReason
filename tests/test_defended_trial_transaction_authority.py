"""The security census recognises the defended trial's own task kind.

Regression (solo-criticism run-02818acc38961781e2e820d0d6b591fb, 22 trials,
and the offline stub of
`experiments/2026-09-10-defect-defended-trial-authority-census/proof/
stub_defended_trial_root.py`): `verification/report.py::_transaction_findings`
decided a v6 work transaction's authority by an if/elif chain over
`task_kind`, and `DEFENDED_TRIAL_STEP` -- added with the 2026-08-13 trial
wiring -- had no arm. Every trial step fell to `else: unknown v6 task kind`
and became a `security :: transaction-authority` finding, so ONE trial made a
completed, replay-clean run report `valid: false`: 75 findings on that live
root against zero `verify_root` violations, and 3 on the one-cycle stub.

The arm this file guards is the frozen-surface-3 contact the operator granted
on 2026-09-10 (`DR-INV-frozen-surfaces`). Its value is not that it accepts the
trial -- an unconditional accept would do that -- but that it accepts only what
the frozen manifest authorised. Every test below except the first is a mutation
proof of that: replace the arm with a bare `pass` and each one goes green when
it must stay red.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from deepreason.config import Config
from deepreason.llm.firewall import route_fingerprint
from deepreason.run_manifest import compile_run_manifest
from deepreason.v6_policy import (
    configured_criticism_policy,
    engaged_control_plane_policy_v3,
)
from deepreason.verification.report import _transaction_findings
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind


def _spec(endpoint_id: str) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": "offline-model",
        "provider": "fixture",
        "family": "offline-family",
        "max_tokens": 512,
        "context_window_tokens": 262_144,
    }


def _manifest(authority: str):
    """A real compiled v6 manifest, not a SimpleNamespace.

    The arm re-derives the authorised contract through the same
    `wire_contract_for` the manifest's own behavioral grant uses, resolved
    against the route seat's own presentation profile. A hand-built stand-in
    cannot answer that, and a test that stubbed it would prove nothing about
    the derivation -- which is the only part of the arm that could invent
    findings on a committed root.
    """

    config = Config(
        N_SCHOOLS=2,
        LEGACY_CRITICISM_ENABLED=False,
        ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ENGAGED_CRITICISM_AUTHORITY=authority,
        model_profile="standard",
        roles={
            "conjecturer": [_spec("r-conj")],
            "argumentative_critic": [_spec("r-crit")],
            "defender": [_spec("r-def")],
            "judge": [_spec("r-j0"), _spec("r-j1")],
            "variator": [_spec("r-var")],
        },
    )
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-09-10T00:00:00Z",
        control_plane_policy=engaged_control_plane_policy_v3(),
        criticism_policy=configured_criticism_policy(config, "r-crit"),
        run_input_digest="e" * 64,
    )


@pytest.fixture(scope="module")
def trial_manifest():
    return _manifest("defended_trial")


@pytest.fixture(scope="module")
def observe_only_manifest():
    return _manifest("observe_only")


def _step(
    manifest,
    *,
    role: str,
    seat: int = 0,
    declared_role: str | None = None,
    contract_id: str | None = None,
    schema: str = "defended-trial-step.v1",
    task_kind: str = "defended_trial_step",
):
    """One durable trial preparation, shaped exactly as the writer shapes it.

    `informal/trial.py::_v6_transactional_trial_call` is the only writer of
    this kind; `measures/hv.py` reaches it through the same bracket under the
    `hv-variation-step.v1` payload schema. Defaults reproduce an honest step;
    each keyword is one forgery.
    """

    route = manifest.roles[role][seat]
    contracts = {
        "defender": "defender.direct.v1",
        "judge": "judgeruling.direct.v1",
        "variator": "variator.direct.v1",
    }
    preparation = SimpleNamespace(
        manifest_digest=manifest.sha256,
        route_lease=RouteLeaseRefV1(
            role=role,
            seat=seat,
            endpoint_id=route.endpoint_id,
            route_sha256=route_fingerprint(route),
        ),
        task_kind=SimpleNamespace(value=task_kind),
        contract_id=contract_id or contracts.get(role, "defender.direct.v1"),
        task_payload_value={
            "schema": schema,
            "role": declared_role or role,
            "target_id": "artifact-" + "a" * 8,
            "step": "defender",
        },
    )
    return SimpleNamespace(
        preparation=preparation,
        issued=True,
        terminal=SimpleNamespace(status="completed", reason_code=None),
    )


def _findings(tmp_path, monkeypatch, manifest, items):
    work = {
        "sha256:" + f"{index:x}".rjust(64, "0"): item
        for index, item in enumerate(items)
    }
    (tmp_path / "run-manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "deepreason.harness.Harness",
        lambda *_a, **_k: SimpleNamespace(
            workflow_state=SimpleNamespace(transaction_work=work)
        ),
    )
    monkeypatch.setattr(
        "deepreason.run_manifest.load_run_manifest", lambda *_a, **_k: manifest
    )
    return _transaction_findings(tmp_path)


def _security(findings):
    return [item for item in findings if item.channel == "security"]


def test_the_kind_the_trial_writes_is_a_member_of_the_enum_the_census_walks():
    """The premise of every test below: one kind, one writer, two payloads."""

    assert WorkflowTaskKind.DEFENDED_TRIAL_STEP.value == "defended_trial_step"


def test_every_shape_the_committed_roots_carry_is_authorized(
    tmp_path, monkeypatch, trial_manifest
):
    """The five shapes of all 721 trial steps in the five committed roots.

    Census: `experiments/2026-09-10-defect-defended-trial-authority-census/
    proof/TRIAL_STEP_SHAPE_CENSUS.txt`. Before the fix every one of these was
    a security finding.
    """

    findings = _findings(
        tmp_path,
        monkeypatch,
        trial_manifest,
        [
            _step(trial_manifest, role="judge", seat=0),
            _step(trial_manifest, role="judge", seat=1),
            _step(trial_manifest, role="defender"),
            _step(trial_manifest, role="variator"),
            _step(
                trial_manifest,
                role="variator",
                schema="hv-variation-step.v1",
            ),
        ],
    )

    assert findings == ()


def test_a_trial_step_on_a_run_that_never_authorized_a_trial_is_reported(
    tmp_path, monkeypatch, observe_only_manifest
):
    """Forgery 1: a trial claiming an authority the manifest withheld.

    `criticism_policy.authority` is the SAME condition
    `run_manifest.py::_route_seat_behavioral_contract_assignments` uses to
    grant the three trial roles their contracts, so an `observe_only` run has
    no trial grant at all.
    """

    findings = _findings(
        tmp_path,
        monkeypatch,
        observe_only_manifest,
        [_step(observe_only_manifest, role="defender")],
    )

    security = _security(findings)
    assert len(security) == 1
    assert security[0].check == "transaction-authority"
    assert "defended trial work is not authorized by the manifest" in security[0].detail


def test_a_trial_step_that_borrows_another_seats_authority_is_reported(
    tmp_path, monkeypatch, trial_manifest
):
    """Forgery 2: the payload says judge, the route lease spent the defender."""

    findings = _findings(
        tmp_path,
        monkeypatch,
        trial_manifest,
        [_step(trial_manifest, role="defender", declared_role="judge")],
    )

    security = _security(findings)
    assert len(security) == 1
    assert "role 'defender' differs from authorized 'judge'" in security[0].detail


def test_a_trial_step_naming_a_role_the_trial_cannot_seat_is_reported(
    tmp_path, monkeypatch, trial_manifest
):
    """Forgery 3: a call dressed as a trial step to reach a granted seat."""

    findings = _findings(
        tmp_path,
        monkeypatch,
        trial_manifest,
        [_step(trial_manifest, role="defender", declared_role="conjecturer")],
    )

    security = _security(findings)
    assert len(security) == 1
    assert "names a role the trial cannot seat" in security[0].detail


def test_a_trial_step_swapping_a_contract_the_same_seat_holds_is_reported(
    tmp_path, monkeypatch, trial_manifest
):
    """Forgery 4, the one a plan-membership check would miss.

    `judge[0]` legitimately holds the grounding-verdict contract as well as the
    ruling contract on runs that enable grounding review, so "is this contract
    in the seat's granted set" is not enough: the arm re-derives the ONE
    contract the trial's own output model renders on that seat.
    """

    findings = _findings(
        tmp_path,
        monkeypatch,
        trial_manifest,
        [
            _step(
                trial_manifest,
                role="judge",
                contract_id="groundingverdictwirev1.direct.v1",
            )
        ],
    )

    security = _security(findings)
    assert len(security) == 1
    assert "groundingverdictwirev1.direct.v1" in security[0].detail
    assert "judgeruling.direct.v1" in security[0].detail


def test_a_trial_step_with_no_recognized_trial_task_is_reported(
    tmp_path, monkeypatch, trial_manifest
):
    """A preparation carrying the kind but not either payload the writer emits."""

    findings = _findings(
        tmp_path,
        monkeypatch,
        trial_manifest,
        [
            _step(
                trial_manifest,
                role="defender",
                schema="criticism.semantic-task.v1",
            )
        ],
    )

    security = _security(findings)
    assert len(security) == 1
    assert "defended trial work has no recognized trial task" in security[0].detail


def test_a_trial_step_on_a_seat_outside_the_frozen_roster_is_reported(
    tmp_path, monkeypatch, trial_manifest
):
    """A judge seat the manifest never froze is caught before the arm runs."""

    route = trial_manifest.roles["judge"][0]
    item = _step(trial_manifest, role="judge", seat=0)
    item.preparation.route_lease = RouteLeaseRefV1(
        role="judge",
        seat=5,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )

    security = _security(_findings(tmp_path, monkeypatch, trial_manifest, [item]))
    assert len(security) == 1
    assert "route judge[5] is absent from the frozen manifest" in security[0].detail


def test_a_task_kind_outside_the_enum_still_reports_as_unknown(
    tmp_path, monkeypatch, trial_manifest
):
    """The arm is added BEFORE the closing else, never in place of it.

    A kind that is not a member of `WorkflowTaskKind` at all must report
    exactly as it did before this tranche.
    """

    findings = _findings(
        tmp_path,
        monkeypatch,
        trial_manifest,
        [_step(trial_manifest, role="defender", task_kind="wander_step")],
    )

    security = _security(findings)
    assert len(security) == 1
    assert "unknown v6 task kind 'wander_step'" in security[0].detail
