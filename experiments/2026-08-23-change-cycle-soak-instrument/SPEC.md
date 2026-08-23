# SPEC — offline cycle soak instrument

Traces: R2, R3 (S1), R4 (S2), R5 (S3), R6 (S4), R7, R9.
Budget: one new script under `scripts/`, one baseline row, two doc
sentences. **Zero `src/` files.** Estimated diff < 700 lines added.

## S0 — the defect this instrument exists to catch

R1's four deaths share one shape: the operational smoke is GREEN while the
managed path dies at cycle 0-2. The smoke misses them for two independent
reasons, both of which the soak must remove:

1. **Shape.** The smoke drives `deepreason setup/qualify/reason` over a
   short synthetic problem. It never renders operator-authored `predicate:`
   criteria, never enables attached evidence, never carries a supplement.
   `preparation.py` hardcodes `criteria=()` on the managed request, so the
   only surface that carries subject-substantive commitments is the
   manifest surface — the one all four deaths used.
2. **Depth.** The smoke's reason stage is short. Three of the four deaths
   are at cycle 2; the carrier threshold is cycle 8. A run that stops at
   cycle 1 cannot observe them.

## S1 — the soak (R3)

`scripts/cycle_soak.py`, alongside `wheel_smoke.py` and
`wheel_operational_smoke.py`.

**Config shape is READ, not restated.** The `epoch3` case loads the
committed `experiments/2026-08-22-live-reach-rich-run/run-config.yaml`
verbatim and overrides exactly two fields per role — `endpoint` (to the
loopback) and `api_key_env` (to the fixture credential). Every other field
— the 11 canonical roles on one profile, `max_tokens: 32768`,
`context_window_tokens: 131072`, `reasoning: none`, and the five posture
flags — is whatever that file says today. A drift in the real config is
therefore a drift in the soak, by construction.

The rest of the epoch-3 shape is imported from the committed builders
rather than restated, exactly as `build_manifest_epoch3.py` imports from
`build_manifest.py`: `QUESTION`, `CRITERIA` (the three operator-authored
`predicate:` commitments), `COMPILED_AT`, and the derived-then-moved
`inquiry_capability_policy` with `attached_evidence.enabled = True`.

**Cases are parameterized.** `CASES: dict[str, SoakCase]`; `--case` selects,
`--list-cases` enumerates. `epoch3` is the first and the default.

**Stub reuse (R3, binding).** The soak imports `ProviderState`,
`_provider_server`, `response_for_schema` and `TEST_CREDENTIAL` from
`scripts/wheel_operational_smoke.py`. It defines no handler, no schema
synthesizer, and no second fixture. The server is started in the soak's own
process and serves the qualification subprocess over loopback TCP as well.

**Drive path.** Exactly the ladder's three steps, with step 3 in-process:

1. build the root — dossier, run-input, manifest, `problem.json`;
2. `python -m deepreason doctor --run-manifest … --production-contracts
   --out <root>/production-contract-qualification.json`;
3. `TextRunApplicationService.start_manifest_run(root=…, manifest=…,
   problem_path=…, cycles=N, token_budget=…)`.

Step 3 is the requirement's "the one run path": `deepreason run
--run-manifest` is a rendering shell over this method (operator law
2026-08-13), so calling it directly drives the identical code with one less
process boundary.

**N defaults to 8** (`--cycles`), the committed carrier threshold.

**Terminal assertions (R3).** After the run:

- `A1 typed-terminal` — the run reached a typed terminal or typed
  completion; an untyped exception is a failure.
- `A2 no-operational-failure` — `stop_reason != "operational_failure"`.
  This is the assertion R1's four deaths would each have tripped.
- `A3 verify-root-clean` — `verify_root(root)` reports zero violations.
- `A4 cycles-reached` — the run advanced past the deepest recorded death
  cycle (2) and reached the requested depth or a typed non-operational
  stop.

## S2 — the regression seat (R4)

Each death shape becomes TWO assertions: the seam was REACHED (so a green
soak is coverage, not silence), and the seam did not FAIL by its recorded
name. Reach is measured from typed record objects under `<root>/objects/`,
never from prose.

| id | seam | reached-by | fails-by-name on |
|---|---|---|---|
| `D1-seat-contract` | seat contracts with repairs | `workflow-contract-decomposition-transition-v1` ≥ 1; repairs = attempts with `attempt_index > 0` | any `workflow-route-seat-insufficient-capability-v1` object, or a terminal naming `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` |
| `D2-route-lease` | lease-checked routes with tuning | every `workflow-provider-attempt-v1` carries a `route_lease` with `role`, `seat`, `route_sha256` | a terminal naming `ROUTE_LEASE_MISMATCH` |
| `D3-budget-auth` | budget authorization | `workflow-dispatch-authorization-v1` ≥ 1 | a terminal naming `token budget denied` / `WorkBudgetDenied` |
| `D4-reservation-bound` | reservation/dispatch bounds | `workflow-token-reservation-v2` ≥ 1 | a terminal naming `transactional reservation bound differs from rendered request` |

A seam whose reached-by count is 0 is NOT reported as passing. It is
reported `not-covered` and rows into the S4 table with its reason — a
soak that asserts only absence would go green on a run that never reached
the code at all, which is precisely the false comfort R1 describes.

**D4 and the parallel window (R7).** `D4-reservation-bound` is marked
`expected-red-until=<the parallel window's branch>` and is reported, never
skipped. Its status is printed on every run; when it is red the soak's exit
status still distinguishes it from an unexpected failure (exit 3, not 1),
so the instrument is usable before their fix merges without hiding a
genuine regression.

## S3 — gate placement (R5)

- **No pytest gate runs the soak.** It is minutes-long, and the smoke
  precedent (CLAUDE.md §Build and test: "NO gate runs them") governs. No
  file under `tests/` references `cycle_soak`.
- `docs/AUDIT_BASELINES.md` gains a row under Instruments: expected exit 0.
- `dr-drive-harness` §1 (Session preflight) gains one line: no live launch
  without a green soak on the launch config.
- `CLAUDE.md` §Live runs gains the same sentence.

All four move in the SAME commit as the script (R9, and CLAUDE.md's
same-commit map rule).

## S4 — honesty (R6)

The soak prints a COVERAGE table on every run, and writes it to
`<out>/soak-report.json`. Every seam in S2 appears in it with one of three
dispositions: `covered` (reached and not failed), `failed` (named), or
`not-coverable` with a stated reason. A seam that cannot be exercised
offline — because it needs real transport, real provider nondeterminism, or
a real cap burn — is rowed as `not-coverable` with that reason in the
report and in this tranche's RESULTS.md. It is never silently absent.

The dispositions are MEASURED on the first full run, not predicted here.

## Assumptions recorded (SPEC's job where REQUEST is silent)

- **A-i.** "typed completion" (R3) includes any `stop_reason` in the
  harness's resumable set (`converged`, `budget_exhausted`) as well as a
  committed terminal. Only `operational_failure` is a soak failure.
- **A-ii.** The soak writes its root under a caller-supplied `--out`
  (default: a temp dir), never inside the repo, per CLAUDE.md's
  scratch-files rule.
- **A-iii.** The qualification battery runs against the loopback and is
  therefore fast; no cache is shared with a real `DEEPREASON_HOME`. The
  soak sets its own `DEEPREASON_HOME` inside `--out`.

## Stop conditions (R8, and the orchestrator's standard list)

- Any step requiring an edit to `src/deepreason/llm/adapter.py` or the v6
  transaction code: STOP and report (R8), do not edit.
- Any step requiring frozen-surface contact: STOP; none is requested.
- A step failing twice the same way: STOP.
