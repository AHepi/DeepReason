# Request: checkpoints need to be hardened, and a jailbroken run must not be continuable
Captured: 2026-08-30 from CLAUDE.md:519-535, the ledgered 2026-08-29 operator
law "Exhaustion is a clean stop, every stop secures continuation, and
continuation is integrity-gated" (the operator's own words, recorded verbatim
there when they decided the parked P2 question and extended it).

This tranche is LANE A of ultracode batch 2 and owns LIMBS TWO AND THREE of
that law. Limb one is owned elsewhere; R6 below records its state and R6b
bubbles the half that is still unshipped.

## Verbatim

The operator's own words, copied byte-for-byte from CLAUDE.md:521-526 (line
wrapping is CLAUDE.md's; the sentences are the operator's):

> "clean
> stop. with an assurance that continuing is possible. Too often an
> operational failure overlooks securing enough checkpoints to allow
> relaunches or forgets to ensure continuing is possible that trigger
> corrupted stops. On that note, checkpoints need to be hardned. I
> don't want a jailbroken run to be continuable."

The ledgered operational reading that accompanies those words in the same
CLAUDE.md entry, copied byte-for-byte from CLAUDE.md:526-535:

> Operational reading:
> a budget denial on an exhausted budget terminates as
> `budget_exhausted` (clean), never `operational_failure`; EVERY
> terminal — clean or failed — must leave checkpoints sufficient for
> relaunch, and a stop that cannot assure continuability is itself a
> defect (a "corrupted stop"); and `continue`/`amend` are gated on the
> record verifying intact — a run whose record fails replay validation
> or carries unresolved containment-breach evidence is REFUSED
> continuation with a typed refusal. Security boundary, not a
> convenience: tampering with a record must not buy a resumable run.

## Requirements

R1 through R5 are the operator's own sentences. R6 through R9 are the
operational reading ledgered with them in the same entry, which is repo law in
its own right; each is quoted, and each names the R it reads.

R1 (behavior): "clean stop." — a run that runs out of budget reaches a stop
that is typed as clean, not as a failure.

R2 (behavior): "with an assurance that continuing is possible." — the stop
must carry, on the record, the assurance that the run can be picked up again.

R3 (behavior): "Too often an operational failure overlooks securing enough
checkpoints to allow relaunches or forgets to ensure continuing is possible
that trigger corrupted stops." — the named defect class: a terminal that
leaves too little behind to relaunch from, or that silently cannot be
continued.

R4 (behavior): "On that note, checkpoints need to be hardned." — the
checkpoint set a terminal leaves is to be strengthened, not merely written.

R5 (behavior): "I don't want a jailbroken run to be continuable." — a run
whose record has been tampered with must not be resumable. This is the
security clause and it governs R8 and R9.

R6 (behavior, reads R1): "a budget denial on an exhausted budget terminates as
`budget_exhausted` (clean), never `operational_failure`".
  - R6a — token-meter exhaustion. SHIPPED before this tranche.
    `src/deepreason/workflow/lifecycle.py:25-28` declares
    `RESUMABLE_STOP_REASONS = frozenset({"converged", "budget_exhausted"})`
    under owner decision 4a (2026-07-27); `src/deepreason/application/
    text_runs.py:407-416` records a typed STOPPED lifecycle receipt for a
    `budget_exhausted` terminal, or a typed refusal when it cannot.
  - R6b — reservation denial (`WorkBudgetDenied`). NOT SHIPPED at HEAD, and
    OUT OF THIS LANE'S CONE (the fix lives in `src/deepreason/scheduler/
    scheduler.py` and `src/deepreason/workflow/`). Two committed roots end
    `failed` / `operational_failure` with `error_type: WorkBudgetDenied`:
    `experiments/2026-08-24-change-rung7-wounds-falls-succession/run` and
    `experiments/2026-08-22-change-epoch3-second-lineage/
    failed-attempt2-run-bb045538...`. BUBBLED as a stop; see SPEC.md's
    parked-fork section. This tranche does not implement it and does not
    claim it.

R7 (behavior, reads R2/R3/R4): "EVERY terminal — clean or failed — must leave
checkpoints sufficient for relaunch, and a stop that cannot assure
continuability is itself a defect (a \"corrupted stop\")". THIS LANE'S LIMB
TWO.

R8 (behavior, reads R5): "`continue`/`amend` are gated on the record verifying
intact — a run whose record fails replay validation or carries unresolved
containment-breach evidence is REFUSED continuation with a typed refusal."
THIS LANE'S LIMB THREE. Its two halves are not equally buildable: replay
validation exists and is consumable; "containment-breach evidence" names a
record type that does not exist in this repo (see Q4).

R9 (behavior, reads R5): "Security boundary, not a convenience: tampering with
a record must not buy a resumable run." This is the acceptance standard for
R8: a gate that a tamperer can walk past does not satisfy R8, however typed
its refusal.

## Standing constraints

C1: "FROZEN SURFACES ... src/deepreason/capabilities/state.py,
src/deepreason/harness.py, src/deepreason/invariants.py, anything under
src/deepreason/verification/, src/deepreason/run_manifest.py,
src/deepreason/qualification.py, plus the frozen-ADJACENT route_fingerprint in
src/deepreason/llm/firewall.py" — batch-2 lane brief, restating CLAUDE.md:88-96
and `docs/map/INV-frozen-surfaces.md`. This lane CONSUMES `verify_root` and
edits nothing inside a frozen surface.

C2: "Don't grant it verbally in chat" — the operator, recorded at
`docs/map/INV-frozen-surfaces.md:59`. A frozen-surface grant is written into
SPEC.md before any code exists, or it does not exist.

C3: "The root sweep is RETIRED as an instrument (operator ruling 2026-08-22:
\"it just wastes time\"). No tranche, gate, audit, or frozen-surface grant may
require sweeping committed roots" — CLAUDE.md:195-200. This lane owes no
sweep; targeted, mutation-proven regression tests on committed roots are the
proof instead.

C4: "Gate discipline: 0 failed is the only acceptable result. Never weaken an
assertion to get green. A fixture that depended on defective behavior may be
minimally updated only when the fix's design doc predicted it." —
CLAUDE.md:186-190. Every predicted fixture change is recorded in SPEC.md
BEFORE the edit.

C5: "The map moves in the SAME COMMIT as the code — a separate \"update docs\"
commit is the commit that gets dropped." — CLAUDE.md's map section and
`docs/map/SCHEMA.md:268-270`.

C6: "# Owner decision 4a (2026-07-27): a budget-exhausted public run is a
typed, quiescent stop and continues under a fresh explicit budget, exactly
like a converged one.  Failure terminals stay non-resumable." —
`src/deepreason/workflow/lifecycle.py:25-28`. A standing owner decision. R7 is
readable as overturning its last sentence; this tranche does not overturn it
(see Q1).

C7: "Scratch/temp files go in the session scratchpad, never the repo." —
CLAUDE.md:315.

C8: "STOPS BUBBLE, NEVER RESOLVE IN-BATCH ... Do not decide them. Write the
STOP brief and continue with everything else." and "DELIVER EVERYTHING NOT
BLOCKED. Scaling the work down is not your call." — the batch-2 lane brief
directing this tranche.

## Map preflight

Recorded here per CLAUDE.md's MAP PREFLIGHT rule ("Record the ids in the
tranche's first artifact so every later phase starts from the same map"), and
derived from each map document's own `Owns:` header rather than from
`INDEX.md` alone — see the two FINDINGS below for why that was necessary.

| id | document | why it covers this work |
|---|---|---|
| `DR-CON-run-identity` | `docs/map/CON-run-identity.md` | `Owns:` names `application/text_runs.py`, `runtime/continuation.py`, `runtime/progress.py`, `amendment/apply.py`, `amendment/models.py`, `amendment/state.py` — every site this lane writes to except `application/results.py`. Its "Where to change what" table already has the row "what `continue` demands before resuming". |
| `DR-SUB-application` | `docs/map/SUB-application.md` | `Owns:` names `src/deepreason/application/`, `src/deepreason/runtime/`, `src/deepreason/cli/`. Covers `terminalize_text_run`, `results_summary` and `prepare_continuation`. Carries the P6 Traps entry that explicitly parks P2. |
| `DR-SUB-amendment` | `docs/map/SUB-amendment.md` | `Owns: src/deepreason/amendment/`. Its opening prose says "twenty-two typed, durable refusal codes" and its check asserts `len(codes)==22`; a 23rd code moves both, in the same commit. |
| `DR-SUB-workflow` | `docs/map/SUB-workflow.md` | `Owns: src/deepreason/workflow/`. Home of `RESUMABLE_STOP_REASONS` and `build_stopped_lifecycle`. READ, not written — the widening question is parked (Q1). |
| `DR-SUB-verification` | `docs/map/SUB-verification.md` | `Owns: src/deepreason/invariants.py, src/deepreason/verification/, src/deepreason/signals_read.py`; marked **Frozen** in INDEX.md. CONSUMED ONLY: this lane calls `verify_root` and edits nothing here. |
| `DR-SUB-scheduler` | `docs/map/SUB-scheduler.md` | `Owns: src/deepreason/scheduler/`. READ ONLY, out of cone; two parked findings live here (R6b and the scheduler-side corrupted stop). |

Ordering rule obeyed as far as it can be: `INDEX.md:36-39` says read the SEAM
before the subsystems it joins. The seams this work actually joins are
application x verification and amendment x verification. Neither exists — see
FINDING 2 — so there was no seam to read first, and the subsystem documents
were read directly.

FINDING 1 (map gap, recorded not fixed): `docs/map/INDEX.md`'s subsystem table
routes to none of `SUB-application.md`, `SUB-amendment.md` or
`SUB-periphery.md`, although all three documents exist. The mandated preflight
therefore cannot reach the two documents that actually cover this lane by
following INDEX.md. Measured this session:

    $ grep -n -iE "application|amendment|periphery" docs/map/INDEX.md
    46:| `SUB-harness.md` | the append-only log, event application, state materialization. **Frozen** |
    54:| `SUB-bridge.md` | the grounded-application bridge: ledger, compose, evidence packs |
    129:| — | periphery × verification | `SEAM-periphery-x-verification.md` |
    136:the periphery × verification and calculus × rules cases — every import between

    $ ls docs/map/ | grep -E "application|amendment|periphery"
    SEAM-periphery-x-verification.md
    SUB-amendment.md
    SUB-application.md
    SUB-periphery.md

Not fixed here: `INDEX.md` is outside this lane's cone and belongs to the lane
that owns map repair. Handed on in SPEC.md's parked section.

FINDING 2 (map gap, recorded not fixed): the seam this work joins is
undocumented on BOTH sides. `docs/map/SUB-application.md:6` lists
`application x verification` under `Seams-undocumented:`, and
`docs/map/SUB-amendment.md:6` lists `amendment x verification` under the same
header. INDEX.md's matrix agrees. A seam document that does not exist means
the pair has not been written up, never that the two do not interact — and
this tranche is precisely an interaction between them.

## Open questions (for dr-spec-change)

Q1: Does R7 ("EVERY terminal — clean or failed — must leave checkpoints
sufficient for relaunch") require that failure terminals become RESUMABLE?
Sixteen committed roots hold the complete checkpoint FILE set and still cannot
be continued, because C6's owner decision keeps failure terminals
non-resumable. Reading R7 as requiring the widening overturns C6 inside a
change tranche.

Q2: Which verdict source does the R8 gate trust — the stored
`REPLAY_VALIDATION.json`, a re-derivation through `verify_root`, or the stored
verdict plus a proof that its binding was validated? R9 is the acceptance
standard, and the three options do not satisfy it equally.

Q3: What does "checkpoints sufficient for relaunch" mean for a terminal that
by C6 may never relaunch at all? The honest in-cone reading is that such a
terminal must RECORD that fact typed rather than be silent about it, but that
is a reading, not the operator's words.

Q4: R8's second clause names "unresolved containment-breach evidence". No
typed containment-breach record exists in this repo — no event kind, no
`verify_root` check, no receipt field. What should the gate consult?

Q5: The 2026-08-28 law says "Gates are always optional: with warnings." R8
says a failing record is "REFUSED". Is the R8 integrity gate switchable per
run like the gates that law names, or is it a refusal by construction because
R9 calls it a security boundary?

## Amendments

(append-only; later operator messages land here as R10... or "R7a supersedes
R7", each with its verbatim quote)

None.
