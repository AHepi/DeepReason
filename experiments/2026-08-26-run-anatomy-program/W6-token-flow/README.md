# W6 — the token-flow map

Window 6 of the RUN ANATOMY PROGRAM (`../PROGRAM.md`), dimension **D10 —
run economy**: "where the tokens went, by seat, contract, cycle and phase".

Read-only on `src/` and `tests/`. No committed run root is opened writable
or modified. This window writes only this directory.

## Read this first

- **`RESULTS.md`** — the honest ledger: findings, and the residue.
- **`TABLES.md`** — every table, rendered from the JSON below.
- **`PARKED.md`** — five findings as ready-to-send prompts. Nothing is
  fixed here.
- **`GOAL.md`** — the falsifiable success criterion this window is held to.

## The instruments

Run in this order; each consumes the previous one's output.

| command | time | writes |
|---|---|---|
| `python3 flow.py` | ~5 min | `FLOW_CALLS.jsonl`, `FLOW_AGGREGATE.json`, `METER_RECONCILIATION.json` |
| `python3 pack_anatomy.py` | ~2 s | `PACK_ANATOMY.json`, `PACK_GROWTH.json`, `PACK_SAMPLES.json` |
| `python3 cross_arm.py` | ~10 s | `CROSS_ARM.json` |
| `python3 pc1_postmortem.py` | ~5 s | `PC1_POSTMORTEM.json` |

`flow.py` spends its five minutes on 54 read-only harness replays; the rest
is seconds. It exits non-zero if either of its two self-checks fails.

## The outputs

| file | one row per | what it is for |
|---|---|---|
| `FLOW_CALLS.jsonl` | provider call (3 155) | the substrate: root, seq, cycle, role, seat, model, contract, purpose, call kind, prompt/completion split, work terminal, admission outcome, fate class |
| `FLOW_AGGREGATE.json` | — | by-purpose, by-outcome, by-fate, by-call-kind rollups, per root and program-wide |
| `METER_RECONCILIATION.json` | root (54) | the three token instruments side by side, with each disagreement classified |
| `PACK_ANATOMY.json` | — | prompt split into preamble / schema / interstitial / `## ` sections, per contract AND prompt form |
| `PACK_GROWTH.json` | root | mean prompt size by contract, prompt form and cycle |
| `PACK_SAMPLES.json` | sampled pack | 13 and 16 packs from the two priority roots, spread across cycles |
| `CROSS_ARM.json` | — | P-C1 ARM H vs ARM S: cost per candidate, valid candidate, above-floor candidate |
| `PC1_POSTMORTEM.json` | — | ARM H's 702 789 tokens as line items, cut by the problem each call was posed against |

## The two self-checks

Both are asserted on every run, not sampled:

1. **The join is unique.** Each `llm` log event's control refs contain
   exactly one `workflow-provider-attempt-v1` object id. 3 155 of 3 155
   across all 54 roots; `flow.py` prints the ambiguous count and exits
   non-zero if it is not 0.
2. **The attribution rule agrees with the record's own backref.** Tokens
   are attributed to the artifacts created between a call and the next
   call. Conjecturer calls also carry an explicit `conjecture-call:<seq>`
   backref; the two agree 465 times and disagree 0. `flow.py` exits
   non-zero on any disagreement.

A third check is structural rather than printed: `pack_anatomy.py` asserts
at startup that its copy of `approximate_tokens` still equals
`deepreason.packs.allocate.approximate_tokens`, so the instrument keeps
re-deriving budgeting decisions with the arithmetic that made them.

And one cross-instrument agreement worth naming, because neither
instrument knows about the other: `flow.py` counts 456 repair re-asks from
the lifecycle transitions, and `pack_anatomy.py` counts 456 repair-shaped
prompt blobs.

## What this window cannot see

Stated here rather than only in the residue, because it bounds every number
above:

- **Qualification tokens are not in the record at all.** All spend figures
  are inquiry-only.
- **Embedder and preflight usage are typed absences**, not zeroes — the
  accounting says so itself.
- **A pack section the allocator dropped leaves no trace in the prompt.**
  Pack anatomy reports what the model was shown, never what the budget cut.
- **`batch-critic.v2` has no sections** — 25.6 % of the program's spend is
  split three ways and no further.
