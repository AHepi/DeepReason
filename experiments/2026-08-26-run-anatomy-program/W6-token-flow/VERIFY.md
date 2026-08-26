# VERIFY — W6 against its own GOAL.md

Each criterion, the instrument that discharges it, and the check that shows
it discharged. Re-derivation is the test: every output below was produced
twice from the committed roots and compared byte for byte.

## The reproduction test

    md5sum FLOW_AGGREGATE.json PACK_ANATOMY.json CROSS_ARM.json \
           PC1_POSTMORTEM.json METER_RECONCILIATION.json > before.md5
    python3 flow.py && python3 pack_anatomy.py && \
      python3 cross_arm.py && python3 pc1_postmortem.py
    md5sum -c before.md5

Result: **5 of 5 OK**, byte-identical. GOAL.md's failure condition — "any
number reported that cannot be re-derived by running the committed
instrument against the committed roots" — is not met.

## Criterion by criterion

**1. A per-call flow table covering every provider attempt in every root,
with contract, seat, cycle, purpose, repair flag, prompt/completion split,
work terminal, reason code and admission outcome — classes taken from the
record's own fields.** ✅

`FLOW_CALLS.jsonl`: **3 155 rows over 54 roots**, against the shared
`ROOT_INVENTORY.json`'s 3 155 attempts over 54 roots. Every required field
is present on every row. Four fields carry a null anywhere, all of them
typed absences reported as such rather than defaulted: `cycle` on 144 calls
in 7 roots that never completed a cycle, and `terminal_status`,
`terminal_reason_code`, `admission_outcome` on the single call whose work
had no terminal (RESULTS.md residue 8, 9).

Classes are record-native: `purpose` from `contract_id`, `call_kind` from
the `work_prepared` lifecycle trigger, `outcome` from the work terminal's
`status`, `admission_outcome` from the semantic admission's `outcome`. An
unlisted contract or trigger lands in an `unclassified` bucket loudly; both
buckets are empty.

**2. Aggregate by-purpose and by-outcome tables, prompt- and
completion-side separately, per root and program-wide.** ✅

`FLOW_AGGREGATE.json`: `program_by_purpose`, `program_by_purpose_detail`,
`program_by_contract`, `program_by_role_seat`, `program_by_model`,
`program_by_outcome`, `program_by_outcome_reason`, `program_by_call_kind`,
`program_by_fate_class`, plus `per_root` with `by_purpose`, `by_outcome`,
`by_call_kind` and `by_fate_class` for all 54 roots. Every rollup carries
`prompt_tokens`, `completion_tokens` and `prompt_share`.

**3. The three token instruments reconciled root by root, every
disagreement classified and its residual attributed.** ✅

`METER_RECONCILIATION.json`: 54 rows. 27 disagreements, in two classes —
18 Class A (`run-status.json` zero on a non-terminal root) and 9 Class B
(accounting undercounts the log). 8 of the 9 Class B residuals are exactly
the report-purpose spend, and the instrument asserts that per row rather
than asserting it once in prose (`residual_explained_by_report_purpose`).
The ninth is reported as unexplained and diagnosed in RESULTS.md.

**4. Pack anatomy for at least 10 packs per priority root, spread across
cycles, split by the allocator's own emission format and sized with its own
estimator.** ✅

`PACK_SAMPLES.json`: **13 packs from P-C1 ARM H across cycles 1–16** and
**16 from P-R1 across cycles 1–12**. `PACK_ANATOMY.json` covers all 3 155
prompts, 0 blobs missing. `PACK_GROWTH.json` carries the growth curves as
data, split by contract, prompt form and cycle.

The estimator is asserted equal to
`deepreason.packs.allocate.approximate_tokens` at every startup, on four
probe strings; a divergence fails the run rather than shifting the numbers.

**5. The two-call (split-budget) protocol answered from the record.** ✅

`FLOW_AGGREGATE.json` → `split_budget`: 717 attempts carry the split
fields, **0 carry a non-empty `split_leg`**, and the only split content in
the record is 96 `split-budget:repair-authorization-is-single-leg` notices.
Reported in RESULTS.md as "no field measurement yet", not as a zero cost.

**6. The cross-arm ratio for P-C1.** ✅

`CROSS_ARM.json`: ARM H 46 852.6 tokens per valid candidate, ARM S
30 845.8, **overhead ratio 1.519**. Above the registered floor ARM H's cost
is reported as `undefined_because: "denominator is zero"` rather than as a
number or an omission. ARM H's status column is re-derived from a read-only
replay rather than taken from the other tranche's scoring artifact; the two
agree (all 132 constructions refuted).

## The scope contract

**Read-only on `src/` and `tests/`:**

    $ git diff --stat origin/main -- src tests
    (empty)

**Writes confined to this directory:** every path in
`git diff --name-only origin/main` plus every untracked file is under
`experiments/2026-08-26-run-anatomy-program/W6-token-flow/`. `../PROGRAM.md`,
`../inventory.py` and `../ROOT_INVENTORY.json` — W1's files this round —
are consumed read-only and unmodified.

**No committed run root modified:** roots are opened with plain file reads
and, for the replay, `Harness(root, read_only=True)`. Nothing in the diff
touches a root.

## The two self-checks, and what they would have caught

Both run on every invocation and both gate the exit code.

1. **Unique join**, 3 155 / 3 155, 0 ambiguous. Had a control event
   referenced two provider-attempt objects, every token in that row would
   have been attributed to the wrong call.
2. **Window rule vs the record's own backref**, 465 agree / 0 disagree.
   This is the check that makes the "what did it buy" column admissible; a
   single disagreement would have invalidated it.

Two instrument errors were caught during construction and are recorded in
RESULTS.md rather than quietly fixed, because both changed headline
numbers: reading `attempt_trace.repair_scope` as the repair marker
understated the repair bill 3.6x, and keying the schema split to one
contract family's cue sentence reported the atomic contracts' pack body as
zero.
