"""Architecture tests for the qualification circuit breaker.

Operator design law, 2026-08-26 (CLAUDE.md), verbatim: "There needs to be a
priority that enforces modularity. Customisation needs to be easy." And
2026-08-28: "Gates are always optional: with warnings."

"A modularity claim without a failable check is decoration." Both tests below
go RED on the BYPASS they name, not on a rename.

Tranche: experiments/2026-08-29-defect-qualification-circuit-breaker/.
"""

import pytest

from deepreason.cli.doctor import (
    PRODUCTION_CASES_PER_PAIR,
    ProductionContractCaseResultV1,
    QualificationCircuitPolicyV1,
    _CIRCUIT_ENV_BY_FIELD,
    _QualificationCircuit,
    _failure_code,
    run_production_contract_doctor,
)
from deepreason.llm.endpoints import EndpointError

from tests.test_cli_production_doctor_v6 import _admitted_case, _manifest


def _dead_route(failure_code, calls):
    def executor(_manifest, pair, case_index):
        calls[pair.role] = calls.get(pair.role, 0) + 1
        if pair.role == "argumentative_critic":
            return ProductionContractCaseResultV1(
                case_id=f"case-{case_index + 1:03d}",
                first_pass_valid=False,
                eventual_valid=False,
                repair_count=0,
                semantic_admission=False,
                failure_code=failure_code,
            )
        return _admitted_case(case_index)

    return executor


def test_switching_the_breaker_off_is_configuration_not_a_code_edit(monkeypatch):
    """Same source, two environments, two behaviours — and neither refuses.

    The bypass this forbids: a breaker whose OFF state needs a source edit,
    or a policy knob no configuration can reach.
    """

    on_calls = {}
    on = run_production_contract_doctor(
        _manifest(), case_executor=_dead_route("ENDPOINT_HTTP_401", on_calls)
    )

    monkeypatch.setenv(_CIRCUIT_ENV_BY_FIELD["enabled"], "0")
    off_calls = {}
    off = run_production_contract_doctor(
        _manifest(), case_executor=_dead_route("ENDPOINT_HTTP_401", off_calls)
    )

    assert on_calls["argumentative_critic"] == PRODUCTION_CASES_PER_PAIR
    assert off_calls["argumentative_critic"] == 4 * PRODUCTION_CASES_PER_PAIR
    # Switching a gate off WARNS. It never refuses and it is never silent.
    assert off.circuit_breaker is not None
    assert [n.code for n in off.circuit_breaker.notices] == [
        "QUALIFICATION_CIRCUIT_BREAKER_DISABLED"
    ]
    assert on.circuit_breaker is not None and on.circuit_breaker.notices == ()

    # The bypass detector: a policy field the environment cannot reach IS
    # "changing the behaviour required a code edit".
    assert set(QualificationCircuitPolicyV1.model_fields) == set(
        _CIRCUIT_ENV_BY_FIELD
    )


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500, 503, 599])
def test_no_provider_status_is_special_cased_in_source(status):
    """Part (a) of the arming test: every status travels the same path.

    Red the moment anyone writes `if status == 429:` into the failure-code
    derivation — which is exactly the code edit this law forbids.
    """

    assert _failure_code(EndpointError("x", http_status=status)) == (
        f"ENDPOINT_HTTP_{status}"
    )


def test_which_conditions_arm_the_breaker_is_configuration_not_a_code_edit(
    monkeypatch,
):
    """Parts (b) and (c): the arming predicate reads only the policy.

    The bypass this forbids: a hidden module-level list of "conditions that
    count", which would make retargeting the breaker a source edit.
    """

    # (b) The same battery, armed by configuration alone. SCHEMA_EXHAUSTED is
    # model incapacity and must NOT arm the shipped default.
    default_calls = {}
    default = run_production_contract_doctor(
        _manifest(), case_executor=_dead_route("SCHEMA_EXHAUSTED", default_calls)
    )
    assert default.circuit_breaker is None
    assert default_calls["argumentative_critic"] == 4 * PRODUCTION_CASES_PER_PAIR

    monkeypatch.setenv(_CIRCUIT_ENV_BY_FIELD["code_prefixes"], "SCHEMA_")
    retargeted_calls = {}
    retargeted = run_production_contract_doctor(
        _manifest(), case_executor=_dead_route("SCHEMA_EXHAUSTED", retargeted_calls)
    )
    assert retargeted.circuit_breaker is not None
    assert retargeted_calls["argumentative_critic"] == PRODUCTION_CASES_PER_PAIR

    # (c) The predicate consults policy.code_prefixes and nothing else.
    nothing = _QualificationCircuit(
        QualificationCircuitPolicyV1(code_prefixes=("ZZZ_",))
    )
    for code in (
        "ENDPOINT_HTTP_401",
        "ENDPOINT_HTTP_429",
        "ENDPOINT_TRANSPORT",
        "SCHEMA_EXHAUSTED",
        "PRODUCTION_CONTRACT_FAILED",
    ):
        assert nothing.arms(code) is False
