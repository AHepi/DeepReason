# Results — judge-evidence review

## 2026-08-09 — the record splits the operator's hypothesis into two different mechanisms with two different answers

**What was asked.** The operator's verbatim claim: "turning on judges at
all should be done with caution. I would prefer to do without, since they
prosecute without any discernable discrimination." A read-only sweep
(`REVIEW.md`, this tranche) over every committed root and results file
this review could find carrying judge-audit numbers, the trial-protocol
guard design, the adjudication-blindness fix, the stress-triplet/lambda
runs, and `EXPERIMENT_PROGRAM_2026-07.md`'s own E0.2 judge-red-team
predictions.

**What the record shows.** The pipeline has two distinct actors easy to
collapse under "judge" (`REVIEW.md` §2.0): the argumentative CRITIC, which
proposes an objection, and the JUDGE, which rules inside a rubric trial or
audit. Three independent live studies (`court_calibration_v1`,
`bronze_court_cross_v1`, `schema_comparator_v1` — `REVIEW.md` §2.5, §7b)
measured the CRITIC objecting to ~100% of everything shown to it, sound or
flawed alike — genuinely, repeatedly content-blind. The JUDGE-gated
conviction step that actually changes `Status` is the opposite problem:
`court_calibration_v1` measured 11.9% sensitivity against 42 planted,
ground-truth defects (`REVIEW.md` §2.5) — it almost never convicts, even
on a real defect. Judges also generalize poorly outside their certified
flaw taxonomy: cross-family catch on unknown flaws was 0.175 vs 0.925 on
known flaws (`e02_judge_redteam_t1`, `REVIEW.md` §2.3), falsifying
`EXPERIMENT_PROGRAM_2026-07.md`'s own P1 (`REVIEW.md` §6.2). On the
harness's actual frozen configuration (cross-family, unanimous judges),
false conviction of sound work is 0-2.5% (`REVIEW.md` §2.4, §2.5); loosen
that to same-family pairing or any either-suffices vote rule and it jumps
to 47-60% (`REVIEW.md` §2.4, independently confirmed not a corpus artifact
by `e02_t2b`'s re-adjudication finding zero of 11 flagged items actually
defective). One specific reading — self-preference/verbosity bias — has
never been measured live anywhere in the record; only a synthetic test
fixture exists (`tests/test_audits.py`, `REVIEW.md` §2.2).

**Three-way scoring** (`REVIEW.md` §7, full reasoning there):

- (a) judges rule incorrectly: **SUPPORTED**, but lopsided toward
  under-catching (too lenient), not over-convicting.
- (b) judges rule without discrimination: **MIXED** — true of the CRITIC's
  raw objection stage (confirmed three independent ways), false of the
  JUDGE-gated conviction stage, which discriminates between recognized and
  novel content and is self-consistent under order-swap.
- (c) judges over-prosecute: **MIXED** — false of the harness's actual
  frozen configuration (which under-prosecutes), true of every looser
  configuration this record measured, and untested for the specific
  self-preference/verbosity-bias reading.

**Design consequence** (`REVIEW.md` §8). Five non-judge or
judge-consistency mechanisms already exist in the tree: program/predicate
commitments, counterexample execution, referential-integrity screening,
order-swap consistency screening, and `observe_only` (already the default
in 26 of 31 measured roots, per the adjudication-blindness tranche's own
blast-radius count, `REVIEW.md` §4). None of them can adjudicate
open-ended prose without an LLM in some role — eliminating judges as a
category means accepting that prose cannot refute anything, which is
already the actual state of most of the committed record. Two operator
design laws bound any future design here regardless of what the numbers
say: a solo run with everything on must remain possible, and informal
conjectures may never be penalized relative to formal ones.

**The residue — what remains unproven.** Self-preference and verbosity
bias, the most literal reading of "discernable discrimination," have zero
live measurements anywhere in the committed record (`REVIEW.md` §2.2,
§7c) — this is a genuine gap this review could not close by reading,
because the record does not contain the number. Whether the
`observe_only` default is sufficient for solo runs going forward, or
whether a new non-judge status-changing path for prose should be built,
is a decision this review supplies evidence for but does not make
(`REVIEW.md` §8.3). Whether the referential-integrity screen's demonstrated
~2% combined block rate (39 blocks / 1801 live judge calls inside trials,
`REVIEW.md` §3.3) is worth widening is unresolved. One number in a
committed config file (`config/deepseek.yaml`'s judge-reasoning
calibration comment) cites a results file, `judge_battery_report.json`,
that does not exist in the current working tree and could not be
independently verified (`REVIEW.md` §6.2). "Accepted does not mean true":
this review reports what the committed record shows and what it does not;
it does not settle the operator's authority-configuration question, which
remains theirs to make.
