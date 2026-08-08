# Results — Rung S6, the live two-seat A/B

Honest-ledger segments only. "Accepted does not mean true." Model prose
is never evidence; `run-status.json`, `verify_root`, `recorded_seat_
bindings`, and the LLM-call records in `log.jsonl` are.

## Failure ledger (numbered as spent, not retrospectively)

**Failure #1 — qualification battery failure (combination fell to
shallow tier), diagnosed before any theory.** `qualify` completed
(rc=0, 477s) but the COMBINATION subject reached only
`qualification_state: "ready_shallow"` (`tier: "shallow"`), so `reason`
(full V6) refused typed on the very next step:

    QUALIFICATION_TIER_SHALLOW: this provider/model is qualified at
    tier "shallow" only; full V6 reasoning is refused. Use: deepreason
    reason --shallow "YOUR QUESTION"

Read the diagnostic blob (`home-s6/qualification-cache/f9295c2b....
unqualified-doctor.json`) before theorizing, per the driving manual's
own rule. `summary.qualified_pair_count: 14/15`; the one unqualified
pair (`pairs[11]`) is `role: "summarizer"`, `contract_id:
"scratch.cluster-guide.compact.v1"`, `model_id: "glm-5.2"`:
`eventual_valid_count: 19/20` (at the `eventual_valid_minimum_per_pair`
floor) but `scope_violations: 1` (case-004, `failure_code:
"REPAIR_SCOPE_VIOLATION"`). `cli/doctor.py:139` confirmed this is a
ZERO-TOLERANCE gate — `sum(item.scope_violations for item in cases) ==
0` is required regardless of the eventual-valid count, so 19/20 valid
plus one scope violation still fails the pair. `_is_scope_violation`
(`cli/doctor.py:431`) classifies `REPAIR_SCOPE_VIOLATION` as: the model,
during a JSON-repair retry, edited a field outside the allowed repair
scope — a content-shape/discipline issue on this one representative
case, not a config error or a run death.

**Remedy (knob, not code):** raised `--maximum-completion-tokens` from
8192 to 16384 and re-ran `setup` + `qualify`. This changes the
profile's own digest, forcing a FRESH, independently-sampled battery
(qualification caches by subject digest; re-running the SAME profile
would have replayed the identical cached failure) — the standard
adaptation for a stochastic single-case miss, not a certainty of fixing
the specific repair-scope behavior, but the cheapest knob available
that plausibly gives the model more room during a repair attempt.

## 2026-08-08 — launch

Ladder launched detached at `2026-08-08T03:24:53Z`, head `19a294ba`.
`setup` succeeded on the first attempt: `deepreason status --json`
(smoke-tested pre-launch against a throwaway home, then live) confirms
the `coder` seat bound to `gemma4:31b` alongside the default `glm-5.2`
profile. Qualification battery started (~1140 calls expected, ~14 min).
