# PARKED — found in this tranche, deliberately not fixed here

One tranche, one goal (GOAL.md). Each entry below is written for its
FUTURE RUNNER, while the context is free: one line of WHAT, then a
ready-to-send prompt. Starting the follow-up should cost a paste.

---

## P1 — `cycle_soak --induce-repairs` cannot induce a repair on a SPLIT call

**What.** The soak's repair inducer replaces the FIRST stub response per
wire-schema title with an unusable value, so the adapter rejects it into
a repair. On a split seat call the DELIBERATION leg consumes that first
response — it is unconstrained and never validated, so an unusable value
there costs nothing — and the emission leg then receives the good one.
Measured: `--case split-legs --induce-repairs 3` drove 96 calls, every
one `(1 attempt, 2 legs)`, **zero** repair attempts, with the inducer
confirmed armed in the log ("repair induction ON for the first 3 wire
schema(s)"). D1 reports `[PART]` for a reason that is now wrong: not
"the stub always returns a schema-valid response" but "the leg that
received the invalid one does not validate".

This tranche's coexistence proof is therefore a unit regression
(`tests/test_split_leg_recording.py::test_a_split_call_and_a_genuine_repair_coexist`),
which is mutation-proven and stronger — but the SOAK's blind spot is
real, and a soak that reports `[PART]` for a stale reason will mislead
the next reader.

```
Defect: scripts/cycle_soak.py's --induce-repairs flag silently fails to
induce any repair on a split-budget seat call. It wraps
wheel_operational_smoke.response_for_schema and replaces the first
response per wire-schema title; on a split call the unconstrained
DELIBERATION leg consumes that response and is never validated, so the
emission leg gets the good value and attempt_index never advances.
Measured on the fixed tree: `python -u scripts/cycle_soak.py --case
split-legs --induce-repairs 3` drives 96 calls, all (1 attempt, 2 legs),
zero repair attempts, with induction confirmed armed in the log. D1's
[PART] reason string states a cause that is no longer the operative one.

Route: deepreason-orchestrator. Goal: --induce-repairs reaches the
repair ladder on a SPLIT call, and D1's reason names the real cause when
it does not. Evidence:
experiments/2026-08-27-defect-split-leg-recording/PARKED.md P1 and
soak-after-repairs.out. Frozen surfaces: none expected (scripts/ only).
Acceptance: `--case split-legs --induce-repairs 1` records at least one
attempt with attempt_index > 0 AND that call also carries split_legs, so
the soak exercises the coexisting shape the unit test currently owns
alone; verify_root stays clean.
```

---

## P2 — `INV-frozen-surfaces.md`'s governing principle is the RETIRED law

**What.** That document opens by quoting "fix READERS so old roots stay
valid; a change that invalidates existing replay-valid roots is wrong by
definition", and the same section still calls the root sweep its
instrument. CLAUDE.md retired the cross-version law on 2026-08-14 and
retired the sweep on 2026-08-22. Already ledgered as `docs/ERRATA.md`
E36 — so this is a KNOWN, RECORDED drift, not a new finding, and it is
noted here only because this tranche read that section to request a
grant and had to reconcile it against ERRATA by hand. Not fixed here:
rewriting a frozen-surfaces preamble is its own change with its own
authority question, and doing it inside a defect tranche would be
exactly the scope creep the contract forbids.

```
Change: docs/map/INV-frozen-surfaces.md's "The governing principle"
section still states the cross-version compatibility law CLAUDE.md
retired on 2026-08-14, and still names the root sweep (retired
2026-08-22) as its instrument. Recorded at docs/ERRATA.md E36. Every
reader requesting a frozen-surface grant currently has to reconcile the
document against ERRATA by hand.

Route: dr-change-orchestrator. The operator's words are the authority:
CLAUDE.md's 2026-08-14 law with its SCOPE BOUNDARY (within-version
integrity is untouched) and the 2026-08-22 sweep retirement. Acceptance:
the section states the current law with its boundary, names no retired
instrument, docs_verify stays at baseline, and E36 gains a closing note
saying where the correction landed.
```

---

## P3 — `ProposalReceiptV1.attempt_count` was one repair away from refusing

**What.** `workflow/models.py`'s `attempt_count` is
`Field(ge=1, le=3)` and `workflow/shadow.py` writes it as
`max(1, len(trace))`. Before this fix a split call put 2 entries in the
trace, so a split call that also repaired twice would have written 4 and
been REFUSED by its own model. Never observed, because the protocol
never ran live. **This tranche's fix removes it** — the trace now holds
attempts only, so `len(trace)` is bounded by the repair ceiling again —
so there is nothing left to fix and this is recorded as a near-miss
rather than as work.

No prompt: nothing to do. Kept because the next person to widen what
`attempt_trace` holds should know this field is downstream of it and
cannot absorb a fourth entry.
