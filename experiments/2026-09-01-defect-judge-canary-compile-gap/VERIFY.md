# Verification

`defender[0] provider_result/completed -> judge[0] provider_result/completed -> judge[1] provider_result/completed`

The full filtered critical path was `argumentative_critic[0] -> defender[0] -> judge[0] -> judge[1]`. Every row was transaction-authorized; `first_refusal` was `null`.

| Dispatch | Typed task / step | Result |
|---|---|---|
| `argumentative_critic[0]` | `criticism` / `primary` | authorized, `provider_result`, `completed` |
| `defender[0]` | `defended_trial_step` / `defender` | authorized, `provider_result`, `completed` |
| `judge[0]` | `defended_trial_step` / `judge:0` | authorized, `provider_result`, `completed` |
| `judge[1]` | `defended_trial_step` / `judge:1` | authorized, `provider_result`, `completed` |

## R1 — reproduction

On untouched `3cb51b14e`, `python experiments/2026-09-01-defect-judge-canary-compile-gap/reproduce_compile_gap.py` exited 1: requested `defended_trial`, stored policy `null`, effective authority `observe_only`, empty defender/judge contracts, `silent_gap=true`, ending `DEFENDED_TRIAL_NOT_COMPILED: authority will resolve observe_only; trial contracts will be empty`. On this tree it exits 0 with stored `defended_trial`, effective `trial_required`, `silent_gap=false`, and grants `defender.direct.v1` plus both `judgeruling.direct.v1` seats.

## R2 — Road B

One shared `configured_criticism_policy` helper now serves preparation and direct compilation. Direct compilation invokes it only for v6, only for an omitted argument, after route resolution with the actual critic endpoint, and derives `Config.N_SCHOOLS` bindings. Explicit policies always win; explicit `observe_only` and the legacy default remained pinned. No compatibility preservation was attempted: the seven accepted future subjects moved and `price_compile_gap.py --expect fixed` passed; historical roots were not changed.

Mutation proof against `3cb51b14e`: the byte-identical compile-gap test was `2 failed, 2 passed`; both shared-helper tests failed because the seam did not exist. GREEN was `6 passed in 0.98s`. The wider manifest ring was `46 passed in 2.44s`.

| Four-row control | Manifest SHA-256 | Qualification subject |
|---|---|---|
| default explicit observation-only | `de66096f79454255f3b0a4db932186c8573de9000d1ddcc881fc76c6abe45322` | `02ee7e098bb9239011708a4aa0bce4b7479619b3aff28eff46188125a869e713` |
| defended Config, policy omitted | `0299510d31e292900b36a7d4e20ad9ab9dee9f976a3b9f69b3cca558a3a41fbb` | `de322caa1c8b9d4fefb598bc158ada98376f9f922191409e6168cfc7450057bb` |
| defended Config, explicit `observe_only` | `2fb3ab698ee6777f038adcb9833fb32b628e1b3ec822946fd34975e162f2c58c` | `c4b7ab8ccb3bd123372d9f434b1788a1d257004c22fbba3a63a82baf99d11ab8` |
| defended Config, explicit defended | `0299510d31e292900b36a7d4e20ad9ab9dee9f976a3b9f69b3cca558a3a41fbb` | `de322caa1c8b9d4fefb598bc158ada98376f9f922191409e6168cfc7450057bb` |

The omitted and explicit-defended manifests are byte-for-byte equal. Both observation controls stayed unchanged.

## R3 — offline canary

`python experiments/2026-09-01-defect-judge-canary-compile-gap/run_stubbed_canary.py` compiled manifest `e9ac129bda8ef3f25e09ff9b890742b88a4e215390534e4df074e11dd7a3095a`, preseeded an accepted non-formally-backed target, and drove exactly one scheduler cycle. The critical sequence and typed results are the table at the top; the target ended `refuted`. The complete callback trace also contains a conjecturer call before and after that filtered sequence. Regression ring: `python -m pytest tests/test_judge_canary_dispatch.py tests/test_judge_canary_compile_gap.py -q` -> `5 passed in 7.91s`.

## R4 — live canary

`PREREG.md` was frozen and pushed in `926e77f9b`. R4 was not run because the operator supplied no post-freeze API key.

## Boundary

Full gate: `python -m pytest tests/ -q -n 4` -> `15 failed, 4561 passed, 26 skipped in 1967.82s (0:32:47)`. Twelve nodes reproduced against untouched `3cb51b14e`; two MCP nodes and the parallel-gate three-root concurrency timeout were timing-flaky and passed fresh isolated reruns. No failure asserts Road B, but this container did not meet the required zero-failure boundary.

Full docs verification: `python tools/docs_verify.py` -> `71 documents, 1294 checks, 7 failed`. The failures are the recorded parse/census/pin baselines, missing `bc`, the anchor-reproduced simulation fixture, and the documented 300-second conditional timeout; every new owner-map check passed.

This deterministic stub proves compilation and behavioral-grant creation, transactional authorization, and provider-dispatch reachability through defender and both judges inside one scheduler cycle. It does not prove live provider success, judge unanimity on real outputs, general guard acceptance, or useful live judge behaviour.
