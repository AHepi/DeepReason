# Request: rung 1 — sockets on paper, and the parked R8 job
Captured: 2026-08-03 from `docs/HANDOVER_2026-08-03.md` (operator-adopted
handover; operator's own instruction for this session was "read CLAUDE.md
→ dr-drive-harness → skills README → ERRATA → this handover, then open
rung 1 through dr-change-orchestrator") and
`experiments/2026-08-03-change-driving-skill/PARKED.md` (the R8 job this
rung explicitly merges with).

## Verbatim

> ### Rung 1 — sockets on paper, and the parked R8 job  [EXECUTE]
> Route: `dr-change-orchestrator` (operator words authorizing it: this
> handover, adopted by the operator; quote this file in REQUEST.md).
> Goal: for each candidate socket — schools, conjecture source, criticism
> source, scheduler ranking, authority — one map document (CON- or SUB-
> sections per `docs/map/SCHEMA.md`) stating what it promises the rest of
> the system, what it is handed, what it must never do, with checks. PLUS
> the deferred R8 job it merges with (quoted in
> `experiments/2026-08-03-change-driving-skill/PARKED.md`): SUB documents
> surface their `Seams:`/`Seams-undocumented:` in prose, and SCHEMA.md (or
> the SUB template) gains the isolated-vs-seam triage rule.
> In scope: `docs/map/` only. NOT in scope: any `src/` change.
> Accept: `python tools/docs_verify.py` 0 failed; `--audit` 0; `--links` 0
> dangling; every new claim carries a check that can fail.
>
> — `docs/HANDOVER_2026-08-03.md`, "The program: seven rungs, in order"

> R8, deferred in the operator's own words ("the sub documents never
> mentions the seam documents they're involved with, and how to tell
> whether a modification is just isolated or requires directions from
> rec-seam document. But this job is a later task. For now, focus on the
> others."): a later tranche should (a) make every `docs/map/SUB-*.md`
> cross-reference the SEAM documents it participates in — note the
> `Seams:`/`Seams-undocumented:` headers already exist, so the job is
> likely surfacing them in prose plus the missing half — and (b) add a
> triage rule to SCHEMA.md or the SUB template for deciding isolated
> modification vs. REC-change-a-seam-guided modification. Ready-made
> inputs: `docs/map/SCHEMA.md` anatomy section, `REC-change-a-seam.md`
> steps 1-2, INDEX.md's seam matrix.
>
> — `experiments/2026-08-03-change-driving-skill/PARKED.md`

## Requirements

R1 (artifact): "for each candidate socket — schools, conjecture source,
criticism source, scheduler ranking, authority — one map document (CON-
or SUB- sections per `docs/map/SCHEMA.md`) stating what it promises the
rest of the system, what it is handed, what it must never do, with
checks."

R2 (artifact): "SUB documents surface their `Seams:`/`Seams-undocumented:`
in prose" (the first half of the merged R8 job).

R3 (artifact): "SCHEMA.md (or the SUB template) gains the isolated-vs-seam
triage rule" (the second half of the merged R8 job) — "how to tell whether
a modification is just isolated or requires directions from rec-seam
document."

R4 (process): "In scope: `docs/map/` only. NOT in scope: any `src/`
change."

R5 (process): "Accept: `python tools/docs_verify.py` 0 failed; `--audit`
0; `--links` 0 dangling; every new claim carries a check that can fail."

## Standing constraints

C1: "One rung per tranche, minimum. A rung may take several tranches;
never let one tranche touch two rungs. Never begin rung N+1 in a tranche
that touched rung N." — `docs/HANDOVER_2026-08-03.md`, "Executor
calibration."

C2: "step by step" = rung-by-rung with per-rung gates; rungs 6-7 always
stop for your approval; one rung per tranche." — A2,
`experiments/2026-08-03-change-driving-skill/DELIVERY.md`. This tranche
is rung 1 only; ledgered context, not itself an obligation of rung 1's
scope, but binding on this tranche's boundary.

C3: "Where a rung's words are silent, do NOT generalize from a
neighboring rung or from the codebase's 'spirit' — load
`dr-ask-the-right-question` and route the question to the cheapest
authority (record → framework → operator)." — `docs/HANDOVER_2026-08-03.md`,
"Executor calibration."

C4: "The frozen surfaces (`docs/map/INV-frozen-surfaces.md`) bind every
rung... Readers may be fixed; formats may not; a change that moves a
committed root's verdict is wrong by definition." — same section. Not
expected to bind R1-R5 since scope is `docs/map/` only, but recorded as
standing law.

## Open questions (for dr-spec-change)

Q1: "schools" and "authority" already have `CON-` documents
(`CON-schools.md`, `CON-authority.md` per `docs/map/INDEX.md`). R1 says
"one map document... for each candidate socket" — does this mean one NEW
document per socket, or may an existing CON- document be extended with
the promise/handed/must-never-do sections if it does not already state
them? The words do not distinguish "write" from "extend."

Q2: "conjecture source" and "criticism source" are not named as
subsystems in `INDEX.md` — they appear to be facets of `SUB-rules.md`
(rules/spawn.py conjecture rule, rules/crit.py criticism rule). Does R1
require one document PER facet (two new sub-documents or CON- documents),
or sections within the existing `SUB-rules.md`?

Q3: "scheduler ranking" is a facet of `SUB-scheduler.md` (which already
exists, covering "problem selection, cycles, budgets, school and
capability dispatch"). Same question as Q1/Q2 for this socket.

Q4: R1's checks ("with checks") — SCHEMA.md's check rule (`docs/map/SCHEMA.md`,
"The one rule") requires a check per load-bearing claim; does "for each
candidate socket... with checks" mean each of the three new sections
(promises / what it is handed / what it must never do) needs its own
check, or a check per socket document as a whole?

## Amendments

(none yet)
