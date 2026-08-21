# Fix: the smoke's resumable-terminal assertion counts DECLARED deferral debt instead of demanding zero completion debt

Guarantee restored: `_assert_resumable_terminal` accepts a converged,
replay-valid, resumable terminal whose completion debt is exactly the
deferrals the run itself declared in its log, and still refuses any terminal
carrying completion debt it did not declare, a non-convergence stop, a failed
epistemic or operational channel, or a missing terminal commitment.

## Why this shape and not another

Three candidate fixes were on the table. Two are wrong:

1. **Drop `completion_satisfied` from the assertion.** That is weakening: it
   would also stop catching budget-denied work, a cancelled reasoning span,
   and `foreign-criticism` coverage debt — every real completion finding the
   channel exists to surface. Prohibited by GOAL.md and by CLAUDE.md's gate
   discipline.
2. **Change the harness so a seated-but-uncontracted `variator` stops
   producing completion debt.** That inverts three separate design records
   (`_defer_untransactional_v6_phase`'s docstring, `v6_policy.py:170-179`,
   and the operator's all-configurations-allowed law: disclose typed, never
   die), and it would change what is WRITTEN to the record to fix what is
   READ from it — the exact inversion `dr-propose-fix` forbids.

The third is this fix. The typed record already distinguishes the two kinds
of completion debt, and the instrument was simply not reading the
distinction: `v6-model-phase-deferred.v1` markers are DECLARED debt (the run
saying, in the log, "this optional phase did not run and here is the exact
authority tuple that was missing"), and `verification/report.py::
_deferred_model_phase_findings` emits exactly one completion finding per
well-formed marker event. Every other completion finding is UNDECLARED debt.
Comparing `finding_counts["completion"]` against the marker count is
therefore not a loosening at all — it is the assertion the smoke should
always have made, and it is STRICTLY STRONGER than the old one in one
direction: the old assertion could not tell a run that declared three
deferrals and also lost work to a budget denial from a run that declared
four deferrals, because it refused both without looking.

## Change sites (exhaustive)

- `scripts/wheel_operational_smoke.py`, new helper next to
  `_assert_durable_replay` (~22 lines) — `_declared_model_phase_deferrals(
  run_root: Path) -> int`: stream `<run_root>/log.jsonl`, count events whose
  `inputs` is a 6-tuple of non-empty strings beginning
  `"v6-model-phase-deferred.v1"`. It mirrors
  `verification/report.py::_deferred_model_phase_findings` exactly, INCLUDING
  its malformed-marker branch: a malformed marker becomes an INTEGRITY
  finding there, so it must NOT be counted here — and `integrity_valid` is
  already required by `_assert_committed_terminal`, so a malformed marker
  still fails the assertion, one channel earlier. Guarded by the script's
  existing `_is_regular_file`.
- `scripts/wheel_operational_smoke.py:2052-2065` — `_assert_resumable_terminal`
  gains a keyword-only `run_root: Path`, and its body becomes:
  1. `_assert_committed_terminal(payload)` (unchanged: schema, `state ==
     "completed"`, `valid`/`integrity_valid`/`security_valid`,
     `terminal_commitment_ref` starts `sha256:`);
  2. `epistemic_checks_passed` and `operational_checks_passed` must be
     `True` — message unchanged, `"terminal verification is incomplete"`;
  3. `finding_counts["completion"]` must EQUAL the declared deferral count —
     new message, `"terminal carries undeclared completion debt"`;
  4. `completion_satisfied` must be `(declared == 0)` — message unchanged,
     `"terminal verification is incomplete"`. This keeps the ORIGINAL
     condition alive in the form that is actually satisfiable: a run that
     declared nothing must still report `completion_satisfied: true`;
  5. `completion_status` must be `"satisfied"` when `declared == 0` and
     `"incomplete"` otherwise — message unchanged, `"terminal completion was
     not satisfied"`. This now pins the reader/writer agreement
     (`application/models.py:1230` derives one from the other) instead of
     restating step 4;
  6. `stop.reason == "converged"` — unchanged.
- `scripts/wheel_operational_smoke.py:3565` and `:3652` — both call sites pass
  `run_root=home / ".deepreason" / "runs" / <run id>`. Line 3565 uses
  `resumable_result["run_id"]`, line 3652 uses `resumable_run_id`; the
  continued epoch shares the same root, and the scheduler deduplicates
  deferral markers across resume, so the same count covers both.

## Map moves (same commits, per CLAUDE.md)

- `docs/map/SUB-verification.md` Traps — new entry: `completion_satisfied` is
  unreachable on the public `deepreason reason` path, because
  `Scheduler._premise_rent_step` defers unconditionally on every v6 run whose
  seated `variator` has no behavioral contract. Sits directly beside the
  existing "**`valid` does not mean good**" trap, which already says
  completeness is a separate boolean; this entry says how separate. Carries a
  `check:` that would fail if the deferral stopped being completion debt or
  the smoke went back to demanding zero.
- `docs/map/SUB-application.md` Traps — the existing entry "That decision
  changed a property an out-of-map instrument asserted, and nothing pointed
  at it" gets a RECURRENCE note: it happened a second time, on 2026-08-15
  (`a476c564f`), in the same shape and for the same reason — `docs/map/`
  owns nothing under `scripts/`. Rewritten, never deleted, per `SCHEMA.md`.
- GOAL.md recorded the map GAP (no document covers the wheel smokes as an
  instrument). This fix does NOT create that document: it is a change of
  ownership scope, not a defect fix, and inventing a `SUB-` for a directory
  the map deliberately excludes is a design decision for the operator, not a
  side effect of a one-function repair. PARKED with a ready-to-send prompt.

## Regression artifact

The REPRO artifact must invert:
`tests/test_wheel_operational.py::test_a_converged_terminal_with_only_deferral_debt_is_resumable`
— currently FAILS at `scripts/wheel_operational_smoke.py:2061`, must PASS.

NEW conditions the fix must be tested against (the mutation proof — one
parametrized test, each case a single-field mutation of the same recorded
payload, each expected to RAISE):

| Mutation of the recorded payload / root | Must raise |
|---|---|
| `stop.reason` → `"budget_exhausted"` | `terminal is not a resumable convergence stop` |
| `verification.epistemic_checks_passed` → `False` | `terminal verification is incomplete` |
| `verification.operational_checks_passed` → `False` | `terminal verification is incomplete` |
| `verification.integrity_valid` → `False` | `terminal verification failed` |
| `verification.security_valid` → `False` | `terminal verification failed` |
| `terminal_commitment_ref` removed | `terminal result lacks durable terminal authority` |
| `state` → `"running"` | `reasoning did not complete` |
| `finding_counts.completion` → `2` (root still declares 1) | `terminal carries undeclared completion debt` |
| root declares 0 markers, payload keeps `completion: 1` | `terminal carries undeclared completion debt` |
| root declares 0 markers, payload `completion: 0` but `completion_satisfied: False` | `terminal verification is incomplete` |
| root declares 1 marker, payload `completion_status` → `"satisfied"` | `terminal completion was not satisfied` |
| marker line malformed (5 inputs, not 6) | `terminal carries undeclared completion debt` |

The last row is the one that proves the helper mirrors the reader rather than
merely resembling it: a malformed marker is an INTEGRITY finding on the
report side, so it must not count as a declared deferral, and the assertion
must notice the shortfall.

Fixture inputs are verbatim record: the payload is
`evidence/run-e9d4bb16-run-result.json`, and the deferral log line is
`evidence/run-e9d4bb16-log-deferral-events.jsonl`, extracted byte-for-byte
from the retained root's `log.jsonl`. The test writes those lines into a
`tmp_path` root so the counter reads real recorded bytes.

## Existing tests at risk

From `grep -rn "_assert_resumable_terminal" tests/ scripts/`, the only
callers are the two smoke call sites and this tranche's own new test — there
is no third caller to update.

Nearby tests that pin the smoke's assertion surface and must KEEP PASSING
unchanged (none of them touches `_assert_resumable_terminal`):
- `tests/test_wheel_operational.py::test_operational_smoke_requires_exact_non_resumable_rejection`
- `tests/test_wheel_operational.py::test_operational_smoke_witnesses_an_accepted_continuation`
- `tests/test_wheel_operational.py::test_operational_poll_waits_for_a_new_terminal_commitment`
- `docs/map/SUB-application.md`'s Traps `check:` for the continuation half,
  which greps for `_assert_continuation_accepted`, `_await_cancellable_cycle`
  and `_assert_non_resumable_rejection` by name — none of which this fix
  renames or removes.

No fixture anywhere depended on the defective behaviour, so nothing is being
"minimally updated": the only test that changes is the one this tranche wrote
to fail.

## docs/AUDIT_BASELINES.md

The wheel-smoke entry (lines 42-47) currently says both smokes are expected
exit 0 and carries a KNOWN-STALE carve-out for MCP schema-sha / tool-set pin
failures. This fix MOVES the value: `wheel_operational_smoke.py` goes from
"fails at `reason`" to exit 0. The entry is updated in the same commit to
record the new expectation and to name this tranche as the one that moved it.
It does NOT gain a carve-out for the failure being fixed — that would launder
the finding the prior tranche deliberately refused to launder.

## Explicitly not changed

- **`Scheduler._premise_rent_step` and `_defer_untransactional_v6_phase`.**
  The tempting neighbour, and the one the diagnosis rules out: the harness is
  doing what three design records say. Touching it would change bytes written
  to every future record to satisfy one instrument.
- **`verification/report.py`'s channel classification.** `DR-INV-frozen-
  surfaces` surface 3 covers replay-validation record formats, and
  `SUB-verification.md`'s own trap warns that a check's channel decides
  `valid` on every recorded root. Nothing here needs it.
- **`_assert_committed_terminal`.** Used by four other stages; unchanged, and
  the narrowed assertion still calls it first.
- **The first `reason` stage's own assertions.** Out of scope; that stage
  passes today.

## Frozen surfaces

None touched. The change is confined to `scripts/`, plus two map Traps
entries and one baselines line. No state digest, no event application, no
replay-validation record format, no manifest schema, no qualification
subject.

## Estimated diff

- `scripts/wheel_operational_smoke.py`: ~45 lines (the whole semantic change
  is one function plus one helper)
- `tests/test_wheel_operational.py`: ~75 lines (one rewritten test + one
  parametrized mutation table of 12 cases)
- `docs/map/SUB-verification.md`: ~10 lines
- `docs/map/SUB-application.md`: ~5 lines
- `docs/AUDIT_BASELINES.md`: ~8 lines
- `experiments/.../evidence/`: 1 new 1-line file

~145 lines across 6 files. Stated honestly rather than rounded down: the
SEMANTIC change is ~45 lines in one file; the remainder is the regression
table, the two map entries and the baseline line that CLAUDE.md requires in
the same commit. If the mutation table needs more cases than 12 to be
honest, it gets them, and the overage is reported rather than trimmed —
GOAL.md's budget bounds the fix, not the proof that the fix is correct.

## Approval gate

GOAL.md class is `defect`; the estimate is at the budget, not over it; no
frozen surface is touched. Proceeding to `dr-implement-fix`.

---

## AMENDMENT (dr-implement-fix, 2026-08-21) — the estimate was wrong; measured verdict is EXCEEDED

The estimate above (~145 lines) was wrong, and it is corrected here rather
than quietly absorbed. Measured against the tranche base with the same
instrument `dr-implement-fix` step 8 requires:

    python tools/diff_budget.py c7e605553 --ceiling 150 --paths \
      scripts/wheel_operational_smoke.py tests/test_wheel_operational.py \
      docs/map/SUB-verification.md docs/map/SUB-application.md \
      docs/AUDIT_BASELINES.md

    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "c7e605553",
     "areas": {"scripts/wheel_operational_smoke.py": 53,
               "tests/test_wheel_operational.py": 186,
               "docs/map/SUB-verification.md": 20,
               "docs/map/SUB-application.md": 9,
               "docs/AUDIT_BASELINES.md": 8},
     "total_insertions": 276, "ceiling": 150, "verdict": "EXCEEDED"}

Where the 276 sits, so the number is not a headline:

| Area | Insertions | What it is |
|---|---|---|
| `scripts/wheel_operational_smoke.py` | 53 | the whole semantic change: one new 22-line helper, one rewritten assertion, two call sites |
| `tests/test_wheel_operational.py` | 186 | 66 from the dr-reproduce commit (the record-replay fixture + the structural variator check) and 120 here (the 14-case mutation table and its two helpers) |
| `docs/map/SUB-verification.md` | 20 | the Traps entry CLAUDE.md requires in the same commit |
| `docs/map/SUB-application.md` | 9 | the recurrence note on the existing out-of-map-instrument trap |
| `docs/AUDIT_BASELINES.md` | 8 | the baseline line this tranche moved |

One compression pass was already taken before recording this: the standalone
negative tests were folded into the parametrized table and docstrings cut,
which removed 28 insertions (304 -> 276) with no case lost. Nothing further
comes out without removing proof.

**No option reaches 150.** Deleting the two map entries and the baseline line
(37 insertions) is forbidden by CLAUDE.md — the map moves in the same commit
as the code, and the baseline moves in the tranche that moved the value.
Trimming the mutation table to its four highest-value cases saves roughly 30
and lands near 245. The 150 was this tranche's OWN estimate in GOAL.md, not
an operator constraint, and it was set before the shape of the proof was
known.

The verdict is surfaced as a STOP to the operator rather than absorbed,
because absorbing it is the recorded failure (`dr-implement-fix` step 8: the
2026-08-05 V1 tranche landed 193 insertions against a <=150 ceiling with no
stop). The work is committed to the working branch so it is not lost to a
container rollback; nothing is merged and the trim remains available.

### OPERATOR RULING (2026-08-21) — the overage is ACCEPTED, tranche closes as is

The EXCEEDED verdict was presented to the operator as a STOP, with the
53/186/39 breakdown, the one compression pass already taken (304 -> 276), and
three priced roads: keep it as is (recommended), trim the mutation table to
its four highest-value cases (~245, and it deletes the cases proving the
assertion still refuses a cancelled span, a broken integrity channel, a
missing terminal commitment and a malformed marker), or split into two
tranches (leaves the map temporarily saying something untrue, which
CLAUDE.md's same-commit rule exists to prevent).

The operator chose **keep it as is**. No trim, no split. The final measured
verdict stands on the record as EXCEEDED at 278 insertions (the last two
lines being the `Verified-at:` stamps advanced in the verification commit),
accepted deliberately rather than absorbed silently — which is the whole
point of the step-8 gate.

The estimate itself remains a recorded miss: ~145 predicted, 278 actual, an
error of roughly 90%. The lesson for a future tranche's `dr-set-goal`, stated
so the next reader does not repeat it: a line budget written before the
SHAPE OF THE PROOF is known is a guess about the fix, not about the commit.
When the fix is an assertion, the proof is a mutation table, and a mutation
table costs more lines than the assertion does.
