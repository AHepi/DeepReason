# Reproduction

Form: **record-replay + offline stub root**, both, because the defect has two
things to show and one artifact cannot show both. The stub shows the defect
appearing where nothing else is going on; the committed roots show what a fix
must not disturb.

Artifact 1 (offline stub, the regression artifact):

    python experiments/2026-09-10-defect-defended-trial-authority-census/proof/stub_defended_trial_root.py <tmpdir> 1

Artifact 2 (record replay over every committed root that carries the kind):

    python experiments/2026-09-10-defect-defended-trial-authority-census/proof/recheck_committed_roots.py

## Current output — artifact 1 (`proof/REPRO_stub_before.txt`)

    {
      "completion": 0,
      "integrity": 0,
      "operational": 3,
      "security": 3,
      "security_checks": { "transaction-authority": 3 },
      "task_kinds": { "conjecture": 3, "criticism": 1, "defended_trial_step": 3 },
      "unknown_task_kinds": { "'defended_trial_step'": 3 },
      "valid": false,
      "verify_root_violations": 0
    }

One cycle. One trial. Three `defended_trial_step` transactions — the defender
and both judge seats — and three security findings, one per step. `verify_root`
returns **zero** violations over the same bytes; the integrity channel is empty.
The run is on `ENGAGED_CRITICISM_AUTHORITY=defended_trial`, the road that
existed before the 2026-09-09 solo tranche, with none of that tranche's
switches set.

## Current output — artifact 2 (`proof/COMMITTED_ROOT_CENSUS_before.txt`)

Every git-tracked root carrying a `defended_trial_step` preparation, each
root's STORED `REPLAY_VALIDATION.json` verdict beside the verdict recomputed
now. Nothing is edited: both readers open the committed bytes read-only. See
the file for the five rows; the shape of every one of them is the same —
`recomputed_verify_root_violations: 0`, `integrity: 0`, and a `security` count
equal to that root's `defended_trial_steps` count.

## Confirms diagnosis

Yes. The finding count equals the `defended_trial_step` count exactly, on both
artifacts, and the integrity channel is empty on both — so the record is
well-formed and only the reader's census objects. The stub isolates the cause
from the live tranche: no solo switches, a two-judge ensemble, mock endpoints,
one cycle.

## Post-fix expectation

Artifact 1:

    "security": 0, "security_checks": {}, "unknown_task_kinds": {},
    "valid": true, "verify_root_violations": 0, "integrity": 0

and the stub's `log.jsonl` byte-identical to the pre-fix run's, since only a
reader moves.

Artifact 2: every row keeps `recomputed_verify_root_violations: 0` and
`integrity: 0`; each row's `security` count drops by exactly that root's
`defended_trial_steps` count and by nothing else; no row's `security_checks`
gains a key.

A step of an UNKNOWN kind — one whose `task_kind` is not a member of
`WorkflowTaskKind` at all — must still report exactly as it does today, and a
FORGED trial step (one whose role, seat or contract does not match what the
manifest froze, or whose manifest never authorised a trial) must still be a
security finding. Both are mutation obligations on the fix, not on this phase.

## Production code untouched

    git diff --stat -- src/    ->  (empty)

## Added after the first pass: the terminal carries the defect too

`proof/stub_terminalized_root.py` drives the same one-trial stub through
`terminalize_text_run`. Pre-fix output
(`proof/REPRO_stub_terminalized_before.txt`), trimmed:

    "state": "completed",
    "verify_root_violations": 0,
    "integrity": 0,
    "security": 4,
    "security_checks": { "run-result-verification": 1, "transaction-authority": 3 },
    "stored_run_result_verification": {
        "integrity_valid": true, "security_valid": false, "valid": false,
        "finding_counts": { "integrity": 0, "security": 3, ... } },
    "valid": false

The whole chain in one artifact: three trial steps, three derived findings, a
stored `security_valid: false` frozen into the run's own terminal, and a fourth
finding that is the report reading that stored answer back. This is why a
committed completed run cannot flip after the fix, and why the goal's headline
needs a run completed ON the fixed code to prove it. See FIX.md §9 and GOAL.md's
same-day amendment.
