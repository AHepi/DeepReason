# Delivered — treadle as DeepReason's third lane, and what its limits pilot measured

Branch `claude/treadle-install-pilot-fqwjt5`, pushed, tree clean. Tranche base
`5d9b995ce`. Two releases installed: 0.4.1 (the driver the pilot ran) and 0.5.0
(the checker-and-skill library the operator sent mid-tranche).

## What changed

**A third lane exists, and it is narrower than it looked when this started.**
`treadle` 0.4.1 is vendored at `tools/treadle/` with its swarm gate at
`scripts/swarm_gate.py`, its config at `/treadle.toml`, and its skills at
`/skills/`. `treadle doctor` reads OK on every line. Its own suite passes 34 —
not the 5 its install doc promises, which is 0.1.0's count.

**The pilot ran four rungs and produced one result that changed the governance
it was testing.** T1 (mechanical) passed in one call. T2 (review) had the
reviewer refuse three truncated diffs and certify only the whole one. T3
(generation) produced a mutation-proven regression fixture on the third call.
T4 (the predicted limit) **falsified its own pre-registration** — correct on the
first generation. Then treadle 0.5 arrived, retired its own driver on field
evidence, and rung T5 measured the thing T2's residue had named as the most
valuable missing experiment: given a true document set and one falsified,
**the reviewer catches the falsehood in prose and does not move its typed
verdict.** `CLAUDE.md` now carries that as a binding limit — route a review
here to generate evidence, then read it; never let a stored PASS/FAIL stand in
for reading.

**The pilot's reviewer found two real defects in this repository**, which is the
independent review the operator asked about, delivered rather than promised: a
frozen-surface list this tranche itself made inconsistent (fixed here), and a
map document still prescribing an instrument retired two days earlier (parked,
because it is not this tranche's).

Files: `tools/treadle/` (33 vendored) and `tools/treadle0.5/` (23 vendored),
`scripts/{swarm_gate,consistency_packet,review_harness,ollama_transport}.py`,
`treadle.toml`, `claims.json`, `skills/` (15 + `VINTAGE.md`), `zoo/reviews/`,
`.swarm/`, `docs/TREADLE_ASSEMBLY.md`, and the tranche directory. Two
DeepReason files changed: `CLAUDE.md` (governance) and
`docs/AUDIT_BASELINES.md` (one instrument row). Two test files changed, to fix
the regression the install caused.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "install treadle 0.4.1 ... the treadle SOURCE is committed into the repo at tools/treadle/" | **done** | `diff -r` against the unpacked zip empty; 33 files tracked |
| R2 | "provenance header in a VENDORED.md noting version 0.4.1 and the two deviations" | **done, exceeded** | `VENDORED.md` records five deviations, not two — D3–D5 were forced by this repo and are named as such |
| R3 | "The venv and .treadle/ runtime dirs are gitignored" | **done** | `git check-ignore` exits 0 for both; nothing tracked under either |
| R4 | "Its own `pytest -q` must pass ... report the actual count for 0.4.1" | **done** | `34 passed`; the doc's 5 identified as 0.1.0's |
| R5 | "swarm gate at scripts/swarm_gate.py ... treadle.toml at repo root; its skills/ tree as shipped ... verify by listing" | **done** | listings pasted; `comm -12` over both skill trees empty |
| R6 | "`treadle doctor` — every line OK ... paste it verbatim" | **done** | pasted in RESULTS.md; exit 0, no MISS, no WARN |
| R7 | CLAUDE.md gains a "Third lane: treadle" paragraph, three clauses | **done, extended** | all three clauses present; two measured limits added after T5 |
| R8 | "GOVERNANCE, same commit as the install" | **done** | `99caedf1e` carries CLAUDE.md and AUDIT_BASELINES.md with the install |
| R9 | "AUDIT_BASELINES.md gains a treadle-doctor entry (expected: all OK)" | **done** | row added, then corrected when a third stage moved the line count — with the caveat that the arithmetic moves and the verdicts are what to compare |
| R10 | "verify the pilot cones against INV-frozen-surfaces.md" | **done** | `cone_frozen_check.sh`, four cones, all clean, run before any task was added |
| R11 | T1 mechanical, "names the 3 pre-existing failures" | **done** | board DONE; table names 200/202/204 and `3 failed` |
| R12 | T2 review over Rung D's real diff, "verdict recorded via the gate" | **done** | four typed `verdict` events; one PASS, three FAIL, all read from `.swarm/log.jsonl` |
| R13 | T3 "acceptance = pytest ... AND its mutation-proof script exits correctly" | **done** | independently re-verified: green on the real tree, RED under mutation, tree restored |
| R14 | T4 "Pre-register the prediction ... record HOW it fails" | **done — and the prediction was refuted** | pre-registration is a git ancestor of the run; outcome recorded as FALSIFIED, with an honest account of why the task was too easy |
| R15 | "record the board + calls.jsonl state between rungs" | **done** | captured at each rung; 10 calls, 58 gate events, chain intact |
| R16 | "Judge every rung on typed outcomes only ... Model prose is never evidence" | **done** | every verdict cites a board state, log event, ledger row or exit code |
| R17 | RESULTS.md ledger: "what it cost (calls, tokens from the ledger), where it broke and in which of its three failure modes" | **done, with a stated gap** | calls per rung recorded; **token cost is not fully recoverable** — the ledger holds prompt tokens on generate calls only. Said, not estimated. Failure modes: only "refine" ever fired |
| R18 | "a closing recommendation table: which task classes route to treadle tomorrow, which never" | **done** | ten rows, revised after T5 |
| R19 | "Obey every REFUSED_* ... never work around a refusal" | **done** | three encountered, three obeyed; `REFUSED_WIP_LIMIT` closed by issuing the missing verdicts, not by raising the limit |
| R20 | "Here's the updated. Install this" | **done** | 0.5 vendored and installed per its own SETUP.md steps 0–6; selftest 38 checks / 12 planted refused / 0 failed |
| R21 | "keep going" | **done** | rung T5 run, two real defects found, disposition written, governance updated on the measurement |

## Deviations and dispositions the operator should know about

1. **Five deviations, not two.** D1/D2 were yours. D3 (`.swarm/` committed) came
   from the shipped doc's own `git add` line. D4 (`treadle.toml` adapted) and D5
   (one added stage) were forced by the fact that the shipped config points at
   another programme's tree — without them, `doctor` could not read all-OK,
   which was your condition.
2. **The install broke the gate and the break was real.** Three tests opened the
   swarm gate's coordination log as if it were a DeepReason run log. Fixed by
   correcting the discovery predicate, proven by census (115 → 114, dropped
   exactly `.swarm`). No assertion weakened.
3. **R11–R18 are evidence about 0.4.1 and cannot be re-run under 0.5**, which
   ships no driver. Labelled that way throughout rather than quietly generalised.
4. **Escalation and BLOCKED never fired.** Named as NOT EXERCISED so nothing here
   is read as evidence about them.
5. **One correction of my own, in the record:** I first blamed T2's FAIL verdicts
   on context truncation. The cause was `--sha` order. Both the wrong diagnosis
   and the measurement that overturned it are in RESULTS.md.
6. **The API key you pasted is in a chat transcript.** It is in no tracked file —
   the key appears in 0 of them — and lived only in a scratchpad file outside the
   repo. Worth rotating anyway.

## Parked, not fixed

`PARKED.md` P1: `docs/map/INV-frozen-surfaces.md` still prescribes the root
sweep as "the instrument" and mentions its retirement zero times, while CLAUDE.md
and AUDIT_BASELINES record the 2026-08-22 ruling. Found by the external
reviewer, verified by grep, pre-existing. A ready-to-send prompt is filed — it
costs you a paste, not an authoring session.
