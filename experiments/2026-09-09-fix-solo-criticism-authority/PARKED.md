# Parked — found during this tranche, not fixed here

## P1 — a single-family, MULTI-model run can obtain no judge ensemble at all

**What.** `require_cross_family_judge_ensemble` accepts two judge seats of
different FAMILIES, or two seats of the exact same (provider, model_id). A run
whose judge seats carry two DIFFERENT models of ONE family satisfies neither
and raises `JudgeEnsemblePolicyError`, so its argumentative trial dies rather
than declines. `require_cross_school_judge_ensemble` and
`LLMAdapter.school_judge_bindings` were built for exactly this shape and cannot
be reached: `build_adapter` never populates the bindings, and both manifest
validators plus `resolve_school_route` refuse a `role="judge"` school binding.
This is the road the d8 tranche's SPEC.md M6 actually describes, and it is NOT
the road `ARGUMENTATIVE_AUTHORITY=single_family_trial` needed — that one asks
for a critic school, proved in this tranche's `REPRO.md`.

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator (dr-capture-request first). One goal: a
single-FAMILY, MULTI-model run can obtain a judge ensemble, or the code built
for that case is retired.

Evidence, all read-only:
- experiments/2026-09-09-fix-solo-criticism-authority/REPRO.md, "What this
  reproduction does NOT show" -- why this is a different road from the one that
  tranche closed, measured rather than argued.
- src/deepreason/llm/firewall.py:354-393 -- require_cross_family_judge_ensemble
  raises when families<2 AND models!=1, which is exactly this shape.
- src/deepreason/informal/trial.py:989 -- the else-branch that reaches it.
- src/deepreason/llm/adapter.py:692-706 -- _select_judge_ensemble, the only
  consumer of school_judge_bindings.
- docs/map/SEAM-manifest-x-schools.md, "There is no manifest surface for a
  judge school" -- and its check, which PINS the isolation.

Frozen-surface reading FIRST and in full: this is
experiments/2026-09-09-fix-solo-criticism-authority/FIX.md's road (a), already
priced there with tools/blast_radius.py's computed rows pasted -- CONTACT, 2 of
5 surfaces, DIRECT on run_manifest.py, plus frozen-adjacent route_fingerprint,
a moved qualification subject digest (one battery, ~14 min, ~1160 calls per
home) and 180-260 lines across 6-8 files. It exceeds a tranche's 150-line
budget: scope it as a programme with its own rungs, or price the retirement
road instead. Start from that FIX.md rather than re-deriving the pricing.

Two roads: (a) wire it end to end -- validators admit a judge school binding,
resolve_school_role_lease routes it, build_adapter populates the bindings, and
the three re-checks the seam names as inseparable move together
(plan_foreign_criticism, _criticism_contract, verify_root); (b) retire
require_cross_school_judge_ensemble and LLMAdapter.school_judge_bindings and
record in ERRATA that a single-family multi-model run must either add a second
family or run two judge seats on one model. Road (b) removes a capability the
solo law's spirit covers; do not take it without the operator's words.
```

## P2 — `Config.ARGUMENTATIVE_AUTHORITY`'s three values have no single place that says which reach a run

**What.** The Literal offers `observe_only`, `trial_required` and
`single_family_trial`. `trial_required` reaches a trial only through the
legacy, school-free criticism circuit; `single_family_trial` reaches none;
`defended_trial` — the value that DOES work on a solo run — is not on this knob
at all but on `ENGAGED_CRITICISM_AUTHORITY`, and needs
`LEGACY_CRITICISM_ENABLED=False` besides. Four knobs decide one behaviour and
no document holds the table. `docs/map/CON-authority.md` describes the two
vocabularies correctly and still does not answer "which configuration actually
tries a case".

**Ready-to-send prompt.**

```
Route through dr-change-orchestrator. One goal: one table says which
configuration of ARGUMENTATIVE_AUTHORITY, ENGAGED_CRITICISM_AUTHORITY,
LEGACY_CRITICISM_ENABLED and ADJUDICATION_STATUS_AUTHORITY_ENABLED actually
reaches an argumentative trial, with a check that goes red when it stops being
true.

Evidence: experiments/2026-09-09-fix-solo-criticism-authority/REPRO.md measures
two of the rows already (the Config road declines; the school-routed
defended_trial road mints a warrant on the same one-model shape), and its
proof/ carries both runnable stubs. docs/map/CON-authority.md is the owning
document; its "two vocabularies" section is correct and incomplete.

Smallest change: a table in CON-authority.md, one row per reachable
combination, each row carrying a check that compiles the configuration and
asserts whether a trial is reachable. Do NOT add a knob. Wait for the
criticism-authority tranche above to settle first -- its chosen road changes at
least one row.
```

## P3 — a map check names a run root that a later tranche retired by rename

**What.** `docs/map/INV-frozen-surfaces.md`'s record-claims check runs
`tools/record_claims.py --root experiments/2026-09-06-change-writers-room-
organiser-testing/runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`. That
directory does not exist: the root was retired by rename to
`failed-epoch1-run-36d9a22c3e2045ae1b8c7bfb9d95d092`, which is the correct
handling of a failed root and leaves the check pointing at nothing. It fails
with a JSON decode error, because `record_claims` writes its typed complaint
("no run-status.json (not a run root)") to stderr and an empty stdout into the
`python -c` on the other side of the pipe. Found while disposing of this
tranche's docs_verify delta; it is NOT in `docs/AUDIT_BASELINES.md`'s expected
list, so it is a finding, and it is not this tranche's doing — nothing here
touches that path.

**Ready-to-send prompt.**

```
Route through deepreason-orchestrator (dr-set-goal first). One goal: the
record-claims check in docs/map/INV-frozen-surfaces.md points at a run root
that exists, or the claim it backs is rewritten to one that does.

Evidence, read-only:
- python tools/docs_verify.py --failed  ->  the check fails with
  json.decoder.JSONDecodeError, which is the SYMPTOM.
- python tools/record_claims.py --claims experiments/2026-09-06-change-writers-
  room-organiser-testing/claims.json --root <the path the check names> --json
  -> "no run-status.json (not a run root)", which is the CAUSE.
- ls experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/
  -> failed-epoch1-run-36d9a22c3e2045ae1b8c7bfb9d95d092 and
  run-c3f3bf10bc57d63e224a9f1c68bf1057. The root was retired by rename, which
  is CON-run-identity's own prescribed handling; the check was not moved with it.
- docs/AUDIT_BASELINES.md's expected-failure list does NOT carry this row, so
  an audit comparing against that list will row it as a delta every time until
  it is fixed or baselined.

Decide which root the claim is actually about before repointing it: the
retired epoch-1 root and run-c3f3bf10 are different runs, and the three claim
ids the check asserts (RUN-STOP-01, CRIT-CAP-01, ARMH-STOP-01) may not hold on
both. If neither root supports the claim as written, rewrite the claim rather
than the path — a check repointed at a root that happens to pass is worse than
a red one.

Also worth one line in the same tranche: whether `record_claims` should exit
non-zero AND print typed JSON on stdout, so a piped check fails with its own
reason instead of a JSON decode error three layers away.
```

## P4 — every defended trial writes a record its own security check calls invalid

**What.** `verification/report.py::_transaction_findings` walks each v6 work
transaction and matches its task kind against an if/elif chain. There is no
branch for `defended_trial_step` (`workflow/models.py:160`), so every trial
step falls into `else: unknown v6 task kind` and is reported as
`transaction-authority :: work sha256:... exceeds frozen authority`. Because
`VerificationReportV2.valid` is `integrity_valid AND security_valid`, ONE
defended trial is enough to make a completed, replay-clean run report
`"valid": false` from `deepreason results --verify`.

Measured on two roots, one live and one stub
(`proof/LIVE_VERIFICATION_CHANNELS.txt`):

```
LIVE run-02818acc (this tranche's road, 22 trials)
  verify_root (integrity/replay) violations: 0
  report: integrity 0 security 76 completion 2 operational 16 valid False
      75  transaction-authority      unknown kinds: {'defended_trial_step': 75}
       1  run-result-verification

STUB pre-existing road (ENGAGED_CRITICISM_AUTHORITY, 1 trial)
  verify_root (integrity/replay) violations: 0
  report: integrity 0 security 3 completion 0 operational 5 valid False
       3  transaction-authority      unknown kinds: {'defended_trial_step': 3}
```

**Not this tranche's, and the second row is why.** The stub uses
`ENGAGED_CRITICISM_AUTHORITY=defended_trial` — the road that existed before
this tranche, with none of its switches — and shows the identical finding at
the identical check. The gap has been in the tree since the defended-trial
wiring of 2026-08-13; what this tranche changed is that a launchable
configuration now reaches the trial, so the gap became visible for the first
time. Integrity is 0 on both: the record REPLAYS correctly. It is the security
channel's authority census that does not recognise the work.

**Why it matters beyond a red instrument.** The operator's 2026-08-29 law gates
continuation on the record verifying intact, and makes tampering-that-buys-a-
resumable-run a security boundary. Today the two verdicts disagree: this run's
`terminal.continuation_authority` is `true` and `record_security_violations` is
empty, while `results --verify` says `valid: false` with 76 security findings.
One of those two readings is wrong, and which one it is decides whether a real
containment breach would be caught or lost in 75 false ones.

**Ready-to-send prompt.**

```
Route through deepreason-orchestrator (dr-set-goal first). One goal: a
completed defended trial writes a record its own verification calls valid, or
the check states in typed terms why it cannot.

Evidence, all read-only:
- experiments/2026-09-09-fix-solo-criticism-authority/proof/LIVE_VERIFICATION_CHANNELS.txt
  -- the two-root table above. The live root is
  runs/home-solo/runs/run-02818acc38961781e2e820d0d6b591fb (committed).
- src/deepreason/verification/report.py:972 -- the else branch that emits it.
- src/deepreason/workflow/models.py:160 -- DEFENDED_TRIAL_STEP, the kind with
  no branch.
- src/deepreason/informal/trial.py::_v6_transactional_trial_call -- what
  actually prepares these transactions, and therefore what the missing branch
  would have to authorize: role (defender/judge), contract id, seat.

FROZEN SURFACE, read first and in full: verification/ is frozen surface 3
(DR-INV-frozen-surfaces). Run tools/blast_radius.py on every target and paste
its computed list. This is a WIDENING of what the security channel admits, so
price it as one: a check that stops reporting something must be shown still to
report the thing it was for. Mutation-prove BOTH directions -- a correctly
authorized trial step passes, and a trial step whose role, seat or contract
does NOT match its preparation is still reported. A change that only silences
the 75 is worse than the defect.

Settle first, because it decides the shape: which of the two verdicts is
authoritative today. This run has terminal.continuation_authority=true and
record_security_violations=[] while results --verify says valid=false with 76
security findings. If continuation is meant to be gated on the security channel
(the 2026-08-29 law reads that way), then the gate is currently open on records
the instrument calls invalid, and that is a second finding inside this one.
```

## Not parked here, because another tranche already owns them

- `tools/blast_radius.py` reporting comment and string-literal occurrences as
  frozen-surface contacts —
  `experiments/2026-09-09-change-d8-criticism-experiment/PARKED.md` P4. Hit
  again in this tranche: road (c)'s three SYMBOL_INDIRECT rows all had to be
  checked by hand, and all three turned out to be real references. Recorded as
  a fifth measured instance, not re-parked.
- CLAUDE.md's provider-model sentence — same file, P2.
