# Reproduction

Form: record-replay (the smoke's own recorded terminal payload, replayed
through the smoke's own assertion), plus one structural unit check.

Artifact:
`tests/test_wheel_operational.py::test_a_converged_terminal_with_only_deferral_debt_is_resumable`
and
`tests/test_wheel_operational.py::test_the_seated_variator_holds_no_behavioral_contract_without_a_trial`

Evidence committed under
`experiments/2026-08-21-fix-wheel-smoke-reason-stage/evidence/`, copied
verbatim out of the retained root
`run-e9d4bb16796b8aa4b560c632b33d6500` before the container could reclaim
`/tmp`:

| File | What it is |
|---|---|
| `run-e9d4bb16-run-result.json` | the terminal payload the smoke asserts on |
| `run-e9d4bb16-run-status.json` | state `completed`, stop `converged`, cycle 9 |
| `run-e9d4bb16-REPLAY_VALIDATION.json` | `"valid": true`, whole `terminal_binding` |
| `run-e9d4bb16-run-manifest.json` | v6, `criticism_policy: null`, one `variator` seat |
| `run-e9d4bb16-deferral-markers.json` | the single log marker, seq 34 |

The first test is a RECORD REPLAY, not a hand-built fixture: it loads the
verbatim `run-result.json` the smoke's own `deepreason reason` invocation
produced and feeds it to the smoke's own `_assert_resumable_terminal`. A
hand-written payload would prove only that the assertion accepts what its
author expected.

## Current output

    $ python -m pytest \
        tests/test_wheel_operational.py::test_a_converged_terminal_with_only_deferral_debt_is_resumable \
        tests/test_wheel_operational.py::test_the_seated_variator_holds_no_behavioral_contract_without_a_trial \
        -q

    >       OPERATIONAL._assert_resumable_terminal(payload)
    tests/test_wheel_operational.py:4273:
    ...
        def _assert_resumable_terminal(payload: dict) -> None:
            _assert_committed_terminal(payload)
            verification = payload.get("verification") or {}
            required = (
                "completion_satisfied",
                "epistemic_checks_passed",
                "operational_checks_passed",
            )
            if not all(verification.get(name) is True for name in required):
    >           raise AssertionError("terminal verification is incomplete")
    E           AssertionError: terminal verification is incomplete
    scripts/wheel_operational_smoke.py:2061: AssertionError

    FAILED tests/test_wheel_operational.py::test_a_converged_terminal_with_only_deferral_debt_is_resumable
    1 failed, 1 passed in 1.14s

The failing test reproduces the live failure exactly — same assertion, same
message, same source line (`scripts/wheel_operational_smoke.py:2061`) — in
1.14 seconds instead of ~20 minutes, with no wheel build, no venv, no
provider and no live run.

The second test PASSES today and is the structural half: loading the
recorded manifest and calling the real
`run_manifest._route_seat_behavioral_contract_assignments` shows the seated
`variator` receives no behavioral contract, because
`criticism_policy is None` and the trial-role grant is conditioned on
`criticism_policy.authority == "defended_trial"`. That is why
`_premise_rent_step` defers, and why it defers on every run of this path
rather than on some runs.

## Confirms diagnosis

Yes. The assertion that fails is the one DIAGNOSIS.md named, on the exact
payload the record holds, and the payload's other four channels
(`valid`, `integrity_valid`, `security_valid`, `epistemic_checks_passed`,
`operational_checks_passed`) plus `stop.reason == "converged"` are all
asserted green in the same test before the failing call — so the test also
pins that the terminal is otherwise perfect, which is the whole claim.

## Post-fix expectation

`test_a_converged_terminal_with_only_deferral_debt_is_resumable` passes:
the narrowed `_assert_resumable_terminal` accepts a converged, replay-valid,
resumable terminal whose only completion debt is deliberate deferral debt.
`test_the_seated_variator_holds_no_behavioral_contract_without_a_trial`
keeps passing unchanged.

The fix must also come with MUTATION PROOF that the narrowed assertion
still refuses what it exists to catch — a non-converged stop, a failed
epistemic or operational channel, a missing terminal commitment, and
completion debt that is NOT deferral debt (the `transaction-terminal
… budget_denied` and `run-terminal: reasoning was cancelled` findings the
smoke's other two roots carry). Designing that is `dr-propose-fix`'s job;
this phase changed no production code.
