# MiniReason stress report

*Date: 2026-07-06. Everything below is mechanical: seeded chaos runs,
crash injection, live gauntlets. Numbers come from the committed reports
(`experiments/results/mini_chaos_report.json`, `mini_gauntlet_report.json`)
and the regression tests that pin each finding.*

## What was thrown at it

1. **Chaos campaign** (`mini/scripts/chaos.py`): 400 seeded runs against an
   adversarial endpoint emitting garbage JSON, half-cut responses, exact
   duplicates (relapse bait), key-reshuffled paraphrases, unicode soup with
   control bytes, megabyte prose, syntax-error evals, out-of-range fields,
   partial/zero/absent usage blocks, fake length-truncations, and endpoint
   faults — across randomized budgets (500..200k), vs_k (1..8), retry
   (0..3), decay/turnover/window/floor knobs. After EVERY run, four
   invariants verified: meter==log, byte-replay, parent
   `verify_root == []`, mini/parent status agreement.
2. **Scale probe**: one 2,500-cycle run (~5.5k events, ~2.5k artifacts).
3. **Edge probes** (`mini/tests/test_chaos.py`): hostile content round-trips,
   predicate bombs, sandbox escapes, budget 0, max_cycles 0, empty queue,
   resume-append, torn-write crash injection, interior corruption, missing
   objects, seq gaps, concurrent writers, 500-case scoring-math property
   sweep.
4. **Live hot gauntlet** (`mini/scripts/gauntlet.py`): real provider,
   temperature 1.0, completion cap 900 (deliberately forcing length
   truncations and compression-hint repairs), 4 problems, 25k hard budget.

## Findings (each fixed + pinned by a regression test)

### F1 — crash recovery could destroy the NEXT event (mini AND parent)
A torn final line (crash mid-append) has no trailing newline. The next
`append()` wrote directly onto the fragment; the merged line was then
dropped as "torn" on the following read — **an acknowledged, fsynced event
silently lost after a clean recovery**. The parent's `EventLog` had the
identical flaw. Fix: repair-on-open truncates the never-durable tail (only
bytes whose append never returned); interior corruption still raises.
Tests: `mini/tests/test_chaos.py::test_torn_final_line_recovers_and_reuses_seq`,
`tests/test_torn_append.py`.

### F2 — concurrent writers corrupted silently (mini AND parent)
Two live sessions on one root each validated seqs against their own
in-memory counter, so the stale writer appended a **duplicate seq** —
corruption that only surfaced at the next replay. Fix: a single-writer
fence in `append()` (file-size check before every write) fails loudly at
the write, in both systems.
Tests: `test_chaos.py::test_concurrent_writers_conflict_loudly`,
`tests/test_torn_append.py::test_concurrent_harnesses_conflict_loudly`.

### F3 — predicate bombs could hang the loop (hardening)
A hostile forbidden case (`predicate:10**10**8`) ran unbounded inside
`eval`. Fix: a 2s wall deadline (POSIX SIGALRM); a bomb becomes a failed
verdict. Determinism is unaffected — verdicts are logged as warrants and
replay never re-evaluates, so a timeout can shape only the live run, never
fork the log. The parent's `programs.py` shares the exposure but re-runs
verdicts inside anti-relapse battery checks, where a wall-clock bound COULD
fork state — so the parent is deliberately left alone (its own budget
machinery is the right fix there).
Test: `test_chaos.py::test_predicate_bomb_is_bounded`.

## What held without any fix

- **Accounting (G1)**: meter == log in all 400 chaos runs + both live runs,
  through schema storms, budget death mid-retry, endpoint faults,
  partial/zero usage blocks, and all-blocked batches.
- **Replay (G2)**: byte-equal double replay on every root, hostile content
  included (NUL bytes, 200KB prose, `{`x5000, measure-format mimicry).
- **Graduation (G6)**: parent `verify_root` returned zero violations on
  every chaos root, the 5.5k-event scale root, and both live roots; parent
  and mini agreed on every status everywhere.
- **The gate/orbit contract**: 376 gate blocks and 494 rotations across the
  campaign; healthy runs logged zero blocks.
- **The sandbox**: `open`, `__import__`, `exec`, attribute pivots — all
  come back as failed verdicts, not executions.

## Scale numbers

| metric | 2.5k-cycle root |
|---|---|
| events / artifacts | ~5.5k / ~2.5k |
| log size | 1.5 MB |
| mini replay | **0.35 s** (linear) |
| parent `verify_root` | **70.6 s** (13.9 s at 2.6k events — superlinear) |

The parent's cost is its `transitions()` walk (per-event adjudication),
already known quadratic-ish upstream. Graduation at this scale works but
is a coffee break, not a blink; the mini's own replay stays linear.

## Documented edges (choices, not surprises)

- Symbol-only contents normalize to the empty token set, so one refuted
  symbol-only prior blocks all others. Harmless in v0 (skeleton-wf refutes
  such content anyway); pinned by test.
- Budget overshoot: the attempt that crosses the ceiling completes (the
  gauntlet's hard 25k ended at ~25.6k). Documented meter semantics, not a
  leak — the overshoot is on the log.
- A flipped byte INSIDE a valid JSON string (log or object file) is not
  detectable without per-record checksums — same posture as the parent;
  content-addressed ids cover artifact payloads but not event lines.
