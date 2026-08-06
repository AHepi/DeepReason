# Test phase: live validation of the post-program head

Head under test: `02192978` (rungs 1-5 delivered; P1/T1/T2/S1/V1/W1
fixes; all offline instruments green: gate 3340? — see note — smokes
rc=0, docs_verify 0 failed). Written 2026-08-05 by the monitor session;
operator directive: "I want you to focus on DeepReason".

Note: gate count at W1's verify was 3339+1 regression test — VERIFY.md
of the W1 tranche holds the exact pasted number; this plan does not
restate instrument numbers it did not measure.

## Why a live phase at all

Everything proven since 2026-07-27 is offline or loopback: the gate,
the sweep, both smokes (deterministic provider). The rung-5 A/B is the
only live evidence of the program era and it ran at an earlier head.
Two behaviors have NEVER met a real provider at this head:

- the rung-4 module-fingerprint stamp on an ordinary (non-A/B) run;
- owner decision 4a (2d4ca2e1): a budget-exhausted public run is a
  typed, continuable stop — witnessed end-to-end only against the
  loopback fixture (V1/W1).

## Design: one home, one ladder, two proofs

Arm 1 (`testphase_run.sh`): setup (glm-5.2 via Ollama Cloud) →
qualify (fresh home → full battery, budget ~14 min / ~1140 calls) →
reason on the QUESTION below with a modest budget → audit.

Continuation step, same ladder: whichever typed stop arm 1 reaches —
`budget_exhausted` or `converged`, both in RESUMABLE_STOP_REASONS —
`deepreason --root <root> continue --budget cycles=2`, then re-audit.
If the run instead reaches a failure terminal, the continuation step is
SKIPPED and that is recorded as the finding (a failure terminal at
cycle 0 on this head would itself be the test result).

No research/attachment opt-ins; no round-robin arm (rung 5 already
proved the socket live; the sweep guards its regression).

## Success criteria (typed outcomes only, written before launch)

1. setup rc=0; qualify reaches tier=full.
2. reason rc=0; run-status.json shows state STOPPED with a typed
   stop_reason and (if budget_exhausted) a typed receipt.
3. `verify_root` on the root: no violations, before AND after continue.
4. `recorded_module_fingerprints` on the root: stamp present, exactly
   one, `module_id == "default"`, registry `SCHOOL_POPULATION`.
5. continue rc=0 and the resumed run reaches a second typed stop;
   `continuations.jsonl` present; no violation introduced.
6. The 42-root sweep is NOT an instrument here (new roots extend the
   population; the P1 partition tests are the reader-side proof and
   they run in the gate).

Any criterion unmet → recorded as the finding, not smoothed. Model
prose is not evidence anywhere in this plan.

## Question (fresh — run identity must not collide with any prior root)

    A regression test that pins an exact count of committed artifacts
    fails the first time legitimate new evidence arrives. What general
    property should such a test assert instead, and which published
    testing principles support that choice?

## Mechanics

- Detached launch from the ladder's dir: `setsid nohup
  ./testphase_run.sh & disown`; snapshot loop armed on this experiment
  dir; monitor on the newest root's progress.jsonl + driver log rc=
  lines.
- Credential: `env` file (OLLAMA_API_KEY=...) in this directory,
  gitignored, recreated from the operator — NEVER committed. BLOCKED
  until the operator supplies the key: this container has no env file
  (checked 2026-08-05: `ls experiments/*/env` empty).
- RESULTS.md in this directory gets the dated honest-ledger segment:
  what the record shows, and the residue.
