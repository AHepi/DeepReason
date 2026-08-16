# PARKED — found during the embedder auto-install tranche, deliberately not fixed here

Cross-routing law (CLAUDE.md): a defect found mid-change is PARKED, not
fixed. One tranche, one goal. Each entry is written for its future
runner and should cost the operator a paste, not an authoring session.

---

## P1 — `wheel_operational_smoke.py` fails at the `reason` stage on an UNMODIFIED tree

**What.** The installed-wheel operational smoke — one of the three
instruments no test gate runs — fails with
`AssertionError: terminal verification is incomplete`
(`_assert_resumable_terminal`, `scripts/wheel_operational_smoke.py:2061`)
at `"stage":"reason"`. Proven pre-existing: a clean `git worktree` at
`d52c739ff`, with none of this tranche's changes, fails identically.
Observed 3 times on this container at that stage — passed once, failed
twice, including the base — so it is FLAKY rather than uniformly red,
which is the harder shape to diagnose and the reason it needs its own
tranche.

Per `docs/AUDIT_BASELINES.md` this is a FINDING, not baseline: that file
excuses only smoke failures naming the MCP schema sha or tool-set pins,
and this names neither. The baselines file was deliberately left
unedited — recording an undiagnosed failure there would turn a finding
into an expectation.

**Ready-to-send prompt:**

```
Defect tranche: the installed-wheel operational smoke fails at its
`reason` stage on an unmodified tree. Route through
deepreason-orchestrator (dr-set-goal -> dr-diagnose -> dr-reproduce ->
dr-propose-fix -> dr-implement-fix -> dr-verify-outcome). Diagnosis
comes from the typed record BEFORE code reading.

SETUP: git fetch origin main && git checkout -B claude/smoke-reason-stage
origin/main; pip install -e . --break-system-packages -q; pip install
pytest pytest-xdist jsonschema --break-system-packages -q. Use
`python -m pytest`, never bare pytest. Read CLAUDE.md in full; load
dr-drive-harness, dr-explain-to-operator.

EVIDENCE ALREADY ESTABLISHED (do not re-derive; cite it):
`python -u scripts/wheel_operational_smoke.py` fails with
  AssertionError: terminal verification is incomplete
raised by `_assert_resumable_terminal` at
scripts/wheel_operational_smoke.py:2061, with the failure envelope
carrying "stage":"reason", "failure_kind":"assertion_failed",
"mcp_liveness":"exited", and every terminalization phase counter at 0.
The assertion requires ALL THREE of verification.completion_satisfied,
verification.epistemic_checks_passed and
verification.operational_checks_passed to be true, plus
completion_status == "satisfied" and stop.reason == "converged".
Established 2026-08-16 by
experiments/2026-08-16-change-embedder-auto-install/ (CHECKLIST step 21):
the failure reproduces on a clean worktree at d52c739ff, so it is NOT
caused by that tranche, and it is FLAKY — 3 observations of the stage on
one container gave pass, fail, fail.

GOAL: establish WHICH of the five required conditions is false and why,
from the run root the smoke leaves behind, then decide whether the
defect is in the harness (a run that genuinely does not reach a complete
terminal) or in the instrument (an assertion that over-specifies a
non-deterministic outcome). Those two have opposite fixes and the
diagnosis must name one.

FIRST MOVE, record before code: the smoke cleans up after itself
("cleanup_completed":true), so the first task is to re-run it with
cleanup suppressed (or copy the root out at the failure point) and read
run-status.json, run-result.json's `verification` block,
REPLAY_VALIDATION.json and progress.jsonl from the failing run — the
typed record answers "which condition was false" directly. Do NOT
theorise from the assertion text before reading the blob; both recorded
cycle-0 deaths in this repo were misattributed by readers who skipped
that step.

FLAKINESS IS PART OF THE GOAL, not a nuisance to retry past: a stage
that passes sometimes means either a real race in terminalization or an
assertion on a value that is legitimately allowed to vary. Establish
which, with a repeat count, before proposing any fix.

DO NOT weaken the assertion to get green. If the instrument is wrong,
the fix is a narrower assertion that still fails on the condition it
exists to catch, with a mutation proof that it does.

GATE: full gate at the boundary; docs_verify full; BOTH wheel smokes
(`python scripts/wheel_smoke.py`; `python -u
scripts/wheel_operational_smoke.py`) — the second one is the instrument
under repair, so its verdict is the outcome. Update
docs/AUDIT_BASELINES.md's wheel-smoke entry in the same commit as
whatever moves the value. Map moves in the same commits. Commit and push
every phase boundary (retry 2s/4s/8s/16s).
```

---

## P2 — `experiments/jolt_architecture_2026-07-16/run` cannot be opened by any reader

**What.** `Harness()` refuses that committed root with
`UnsupportedRunManifestVersionError: RunManifest schema version 3 is
unsupported; only schema version 6 is accepted`, so every reader built
on a Harness — `deepreason results` included — cannot report on it.
Noticed while surveying committed roots for the embedder-stamp fixtures
(CHECKLIST step 14).

**Why it is parked and probably stays parked.** This is very likely NOT
a defect but the 2026-08-14 operator law working as intended ("old runs
do not need to be valid or returnable... new versions are optimised for
new functions"). It is recorded only so the next person who trips over
it does not spend a diagnosis on it. It becomes real work only if the
operator decides pre-v6 roots should stay READABLE (as opposed to
valid), which is a question for them, not a defect to route.

**Ready-to-send prompt (only if the operator wants pre-v6 roots
readable):**

```
Change tranche: pre-v6 committed run roots should remain READABLE by
`deepreason results` and `deepreason findings`, even though they are no
longer valid or replayable. Route through dr-change-orchestrator.

AUTHORITY: the operator's decision that old roots stay inspectable.
Note this NARROWS the 2026-08-14 law ("old runs do not need to be valid
or returnable") — capture that tension in REQUEST.md verbatim rather
than resolving it silently, since the law explicitly retired
cross-version obligations.

MECHANISM (verified 2026-08-16): Harness.__init__ ->
_load_workflow_manifest -> load_run_manifest ->
_discriminate_raw_run_manifest_version raises
UnsupportedRunManifestVersionError for schema_version 3
(src/deepreason/run_manifest.py:3890). The two pure readers already sit
OUTSIDE the V6 admission gate on purpose — `results` and `findings` are
excluded from _ROOT_ADMISSION_COMMANDS, and SUB-application.md states
the rationale ("a reader that refused a pre-V6 root would refuse exactly
the roots an operator most needs to inspect"). So the intent already
exists; the Harness constructor defeats it one level lower.

SCOPE: make the READER tolerate an unloadable workflow manifest and
report it as a typed fact, exactly as `results` already reports
identity.manifest_present / identity.manifest_schema_version. Do NOT
widen the manifest schema, do not make such a root valid, and do not
touch replay validation — this is reader tolerance only.
```
