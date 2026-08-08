# Results — Rung S6, the live two-seat A/B

Honest-ledger segments only. "Accepted does not mean true." Model prose
is never evidence; `run-status.json`, `verify_root`, `recorded_seat_
bindings`, and the LLM-call records in `log.jsonl` are.

## Failure ledger (numbered as spent, not retrospectively)

None yet.

## 2026-08-08 — launch

Ladder launched detached at `2026-08-08T03:24:53Z`, head `19a294ba`.
`setup` succeeded on the first attempt: `deepreason status --json`
(smoke-tested pre-launch against a throwaway home, then live) confirms
the `coder` seat bound to `gemma4:31b` alongside the default `glm-5.2`
profile. Qualification battery started (~1140 calls expected, ~14 min).
