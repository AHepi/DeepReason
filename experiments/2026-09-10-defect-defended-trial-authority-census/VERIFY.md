# Verification

Verdict: **PASS (offline).** No live run was launched and the goal did not ask
for one — the defect is in a reader, and every criterion is decidable against
committed bytes and offline stubs.

---

## 1. Criterion 1a — a trial-bearing run COMPLETED after the fix verifies valid

This is the operator's own wording of proof ("Proof means a trial-bearing run
completed after the fix verifies valid") and GOAL.md's amended criterion 1a.

    python experiments/2026-09-10-defect-defended-trial-authority-census/proof/stub_terminalized_root.py <tmpdir>

BEFORE (`proof/REPRO_stub_terminalized_before.txt`) / AFTER
(`proof/VERIFY_stub_terminalized_after.txt`):

| | before | after |
|---|---|---|
| `verify_root_violations` | 0 | 0 |
| `integrity` | 0 | 0 |
| `security` | 4 | **0** |
| `security_checks` | `{run-result-verification: 1, transaction-authority: 3}` | `{}` |
| `unknown_task_kinds` | `{'defended_trial_step': 3}` | `{}` |
| stored `security_valid` | false | **true** |
| stored `valid` | false | **true** |
| report `valid` | false | **true** |

The run reaches `state: completed`, carries three `defended_trial_step`
transactions, and now writes `security_valid: true` into its own
`run-result.json`. That stored summary is the thing the whole defect turned on,
and it is now correct at the moment it is frozen.

## 2. Criterion 1b — the cycle-only stub

    python .../proof/stub_defended_trial_root.py <tmpdir> 1

`proof/VERIFY_stub_cycle_after.txt`: `valid: true`, `security: 0`,
`security_checks: {}`, `unknown_task_kinds: {}`, `verify_root_violations: 0`,
`integrity: 0`, three `defended_trial_step` transactions. Before:
`valid: false`, `security: 3`.

## 3. Criterion 2 — a forged trial step is still reported (mutation-proven)

    python -m pytest tests/test_defended_trial_transaction_authority.py -q
    -> 9 passed

Six of the nine were RED on the pre-fix tree and are the mutation proof: each
goes green — wrongly — if the arm is replaced by an unconditional accept.

| test | what it forges | what must still be reported |
|---|---|---|
| `..._on_a_run_that_never_authorized_a_trial_...` | `observe_only` manifest | "defended trial work is not authorized by the manifest" |
| `..._that_borrows_another_seats_authority_...` | payload `judge`, lease `defender` | "role 'defender' differs from authorized 'judge'" |
| `..._naming_a_role_the_trial_cannot_seat_...` | payload role `conjecturer` | "names a role the trial cannot seat" |
| `..._swapping_a_contract_the_same_seat_holds_...` | `judge[0]` carrying `groundingverdictwirev1.direct.v1` | contract differs from `judgeruling.direct.v1` |
| `..._with_no_recognized_trial_task_...` | payload schema `criticism.semantic-task.v1` | "has no recognized trial task" |
| `..._on_a_seat_outside_the_frozen_roster_...` | `judge[5]` | "route judge[5] is absent from the frozen manifest" |

And the arm did not eat the closing `else`:
`test_a_task_kind_outside_the_enum_still_reports_as_unknown` builds a
preparation whose kind is `wander_step` and asserts
`unknown v6 task kind 'wander_step'` — reported exactly as it was before this
tranche.

## 4. Criterion 3 — the five committed roots, re-verified without being edited

    python .../proof/recheck_committed_roots.py

Both censuses are committed side by side:
`proof/COMMITTED_ROOT_CENSUS_before.txt` and `..._after.txt`. Each row carries
the root's STORED `REPLAY_VALIDATION.json` verdict beside the verdict
recomputed now; both readers open the committed bytes read-only and no root was
touched.

CENSUS_TABLE_PLACEHOLDER

Read the table this way. `verify_root` violations do not move on any root —
including `experiments/2026-09-02-live-p-a2-corrected/run`, which was ALREADY
replay-dirty at 1 violation before this tranche and stays at 1, and whose
stored `REPLAY_VALIDATION.json` already said `valid: false`. Nothing went from
clean to dirty. Every root's `transaction-authority` findings go to zero, and
exactly ONE security finding remains on each: `run-result-verification`.

**That remaining finding is correct and must stay.** At its terminal each run
asked this same reader for a verification summary and froze the answer into its
own `run-result.json`; the defective reader answered `security_valid: false`,
and that is now part of the record. Editing it is forbidden — a committed root
is evidence, and evidence that changes when the code changes is not evidence.
So the five roots keep `valid: false`, honestly, as their own testimony about
what the instrument told them at the time. What the fix makes true is §1: a run
completed on the fixed code stores `security_valid: true`.

## 5. What this does to the continuation gate

Stated because GOAL.md required it, and PARKED as P1 rather than changed.

Before this tranche the two readings of "is this record sound" disagreed on the
live root: `deepreason stop-report` §5 reported
`verify_root: violations 0`, `continue: ACCEPTED`, `amend: ACCEPTED`, and the
run's `terminal.continuation_authority` was `true` with
`record_security_violations` empty, while `deepreason results --verify` on the
same bytes reported `valid: false` with 76 security findings. `DR-SUB-workflow`'s
own Traps entry says a STOPPED receipt "never AUTHORIZES a continuation, which
the SECURITY-channel integrity gate decides at continue/amend time"
(`docs/ERRATA.md` E61), so the disagreement was not cosmetic: one of the two
was wrong about a security boundary.

After the fix they still disagree, and the gap is now one finding wide instead
of seventy-six. Continuation is still ACCEPTED on the live root; the report
still says `valid: false`, now solely because the run stored the old reader's
answer about itself. **The important change is not that the numbers converged —
it is that they now disagree for a reason a person can read.** Before, a real
containment breach on a trial-bearing run would have arrived as finding 77 of
77 and been indistinguishable from the noise. Now any new security finding on
such a run is finding 2 of 2.

What this tranche did NOT settle, and deliberately: whether the gate is meant
to consult the report's security channel at all. The 2026-08-29 law
("continuation is integrity-gated"; a tampered record must not buy a resumable
run) reads as though it should. If it is, the gate has been open on records the
instrument called invalid, and it will stay open on the five roots above whose
stored summaries say `security_valid: false`. That is a decision about which
runs may be continued, not a defect fix, so it is PARKED (P1) with a
ready-to-send prompt rather than decided here.

## 6. Frozen surface and the map

  - The grant is recorded verbatim at `FIX.md` §10 and as
    **"Granted contact, 2026-09-10 — the defended trial's own task kind"** in
    `docs/map/INV-frozen-surfaces.md` under surface 3, in the same commit as
    the code, carrying three `check:` lines. The second is the one the grant
    asked for and it is proved falsifiable rather than assumed: run against the
    committed root `failed-epoch3-run-1b89ed64e050c354` on the PRE-FIX tree it
    reports 26 unknown-kind findings and fails; on the fixed tree it reports
    zero and passes.
  - `docs/map/SUB-verification.md` carries the `Traps` entry, naming both run
    ids (the live `run-02818acc38961781e2e820d0d6b591fb` and the offline stub)
    and the reason the defect was possible: **verification × workflow has no
    seam document**, so nothing states that a kind declared in
    `workflow/models.py` obliges an arm in the census. Its check enumerates
    `WorkflowTaskKind` and fails when the NEXT kind is added without an arm —
    the whole class, not this instance.
  - `tools/blast_radius.py` returned `CLEAR` for this file because its registry
    spells surface 3 as `invariants.py` alone. Disclosed with the grant request
    (FIX.md §3), disclosed again in the map entry, parked as P2. This tranche
    did not fix the instrument.

## 7. Instruments

DOCS_VERIFY_PLACEHOLDER

GATE_PLACEHOLDER

Diff budget: `EXCEEDED` against my own plan-time ceiling — 63 insertions
against 40, of which 17 are comment lines and 1 deletion is an import line
reformatted. Recorded in full at FIX.md §11, reported to the operator, not
trimmed by deleting comments that state constraints the code cannot show.

## 8. Residue (honest)

  - **The five committed roots still report `valid: false`**, and always will.
    §4 says why that is correct. Anyone reading those roots' verdicts needs
    §4 to read them right; that is what this file is for.
  - **The continuation gate's disagreement with the report is narrowed, not
    resolved** (§5). PARKED P1.
  - **`tools/blast_radius.py` still reports CLEAR for every path under
    `src/deepreason/verification/`**, which is half of a frozen surface.
    PARKED P2. Until it is fixed, a window that trusts the tool over
    `DR-INV-frozen-surfaces` will edit a frozen surface believing it was told
    there was none.
  - **verification × workflow still has no seam document.** The Traps entry
    and its enum check are a tripwire, not a seam. Writing the seam is a
    larger job than this tranche and was not attempted.
  - **No live run.** Everything here is committed roots and offline stubs
    against deterministic endpoints. The fix is in a reader, so a live run
    would add cost and no evidence — but it means no defended trial has yet
    been driven end to end against a real provider on the fixed tree.
  - **The `hv-variation-step.v1` payload rides the trial's task kind.** The arm
    accepts it, because 48 of the 721 committed steps carry it and the manifest
    grants the variator seat under the same condition. Whether the demarcation
    sampler should have its own kind is a design question this tranche did not
    open.

## 9. Errata

ERRATA_PLACEHOLDER
