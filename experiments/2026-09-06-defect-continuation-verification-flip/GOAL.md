# Goal: decide which of the two `attempt-validity` verdicts over events 142, 215 and 295 is correct, and make the two agree
Class: defect

Observed: the same root, the same three events, two contradictory verdicts from
the same instrument minutes apart. `experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/run-c3f3bf10bc57d63e224a9f1c68bf1057`
verified `valid true, violations 0, valid_typed_terminal true, amend_ready true`
at commit `ee962fb05` (before the continuation) and `valid false, violations 4,
valid_typed_terminal false, amend_ready false` at `5e01bcd9e` (after it), with
`token_spend 495362` on both. The stored `REPLAY_VALIDATION.json` names three
`attempt-validity` violations — "failed call must contain no valid attempt, got
[0]" — at events **142, 215, 295**. Those three events are byte-identical
across the two commits: sha256 `584145eedb0f0ddf6384f961…`,
`625ee4a13c7ca5a44c047060…`, `6629337a002121aeb55025e7…`, each 2 548 bytes,
each `rule: Control`, at both commits. The log grew from 1 168 to 1 451 events
and the continuation spent nothing (`logged_tokens_this_run: 0`).

Success criterion (machine-decidable):

    python -m pytest tests/<the new regression file> -q
    -> passes, and its stub root (one failed call carrying a valid attempt)
       verifies IDENTICALLY before and after a no-op continuation:
       red on the unfixed tree, green on the fixed one, mutation-proven.

    python tools/root_sweep.py   (or the targeted committed-root probe FIX.md
    names, if the sweep is not the right instrument for a reader change)
    -> no committed root's stored verdict moves except as FIX.md predicts.

In scope (max 3): the `attempt-validity` check and whatever it reads to decide
"failed call" and "valid attempt" — `src/deepreason/invariants.py` and
`src/deepreason/verification/` (**frozen surface 3**, so a change there STOPS at
FIX.md for an operator grant); the writer that produces those fields, if the
record shows the writer at fault (`src/deepreason/llm/`, `src/deepreason/workflow/`);
the continuation path's authority gate, READ ONLY unless the diagnosis lands there.

NOT in scope: P8 (the stop label), the organiser seat, the measure and its
arms, and any re-run of ARM R. Nothing about the writer's room.

Budget: <=150 changed lines, 1 commit, plus the tranche's own artifacts.
Stop conditions inherited from orchestrator: yes.

## Map preflight (ids resolved before any code was read)

Read in this order, per `dr-drive-harness` §4: `docs/map/INDEX.md` →
`INV-frozen-surfaces.md` → the seam before the subsystems.

| id | why |
|---|---|
| `DR-INV-frozen-surfaces` | surface 3 is `invariants.py` + `verification/`; replay-validation record formats are frozen; read FIRST, and every granted contact is a precedent for how a grant is asked |
| `DR-SEAM-llm-x-verification` | the seam whose whole subject is *what the fields of one record MEAN* to the other side — `attempt_trace` is the record `attempt-validity` reads, and the split-legs incident is this seam's own scar |
| `DR-SUB-verification` | `verify_root`, the epistemic-check report, the add-only rule for predicates |
| `DR-SUB-workflow` | the v6 transactional lifecycle, replay and recovery — where a call's outcome and its attempts are written |
| `DR-CON-run-identity` | continuation and amendment epochs: what a resume changes about a root |
| `DR-SUB-harness` | event application; the log the check replays (frozen surface 2, read only) |

## The two roads this tranche must choose between, stated before the evidence is read

R-STRICT: the check is too strict after a resume — the run was always valid,
the pre-continuation verdict was right, and the continuation changed something
the check reads that is not the events themselves.

R-WEAK: the check is too weak before a resume — the post-continuation verdict
was right, and **every pre-continuation clean verdict on a root carrying a
failed call is untrustworthy.** This is the more serious road. If the record
says this, it gets said plainly, in those words, whatever it costs the
tranche that produced the root.

The record decides between them; neither is assumed here.
