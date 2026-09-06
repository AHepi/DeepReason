# Delivered: T4 — the commitment seat and the controller hook (S4, S7, S11b)
Sub-tranche T4 of the mini isolation programme.
Branch: `claude/mini-isolation-t3-t5-7tsc6d` (pushed, tree clean; head in the step-38 commit).
Base: `e83df7dfd` (T3's delivery head). Validation: `T4/VALIDATION.md`, PASS.

## What changed

**The commitment seat writes a record, never an artifact.** After its call,
the seat's proposals go into the run's record through
`record_commitment_proposals`: each becomes a Measure event naming the
marker, the kind `mini.commitment-proposal.v1`, the conjecture it is about
and a content-addressed blob holding its free-prose body, with the call's
spend attached exactly once. That puts a proposal in the record — typed,
append-only, replayable — and outside the one map every authority path reads,
so nothing it writes can change a status by construction rather than by
anyone's restraint. The tests hold the writer to exactly that: after two
proposals the artifact map, the commitment map and every status are
identical, the replay digest matches, and the verifier reports nothing.

**The only requirement is enforced at both ends.** The form refuses a
proposal with no `about`; the writer drops one whose `about` names nothing
in this run, with a typed event saying which and why, and writes the rest.
Nothing else is required, bounded or ranked.

**The road not taken is on the record.** A proposal as an artifact under a
new provenance role was measured first: the blast-radius gate reads widening
`Provenance` as CONTACT on the harness surface, and no grant exists. So T4
changed nothing under `src/` at all, and the full gate is unchanged at 5084
passed.

**"Everything so far" merges artifacts and records in record order.** The
pool a conjecturer or the commitment seat is shown now carries conjectures
and proposals together, each labelled by KIND and never by status, ordered by
the event that first wrote it. The T3 exposure test is re-planted through the
real writer and still passes byte for byte: the critic sees no proposal.

**Shape buys nothing, enumerated.** No rank, admission, immunity or
refutation path — the full harness's scheduler, adjudication, rules, event
application and replay validation, and mini's own nine admit/register/guard/
refute functions — names the kind or the record marker; every mini schema
carries none of score, rank, weight, confidence, priority, authority,
severity; a proposal about a standing conjecture and one about a refuted
conjecture moves neither status.

**The controller hook is declared, and nothing calls it.** `MiniCalibrationHookV1`
is a protocol, a registry selected by id with typed refusals, and one
registered implementation that returns `None`. Exactly two source lines name
the registration; zero calls to the hook exist anywhere under `src/` or
`mini/minireason/`, asserted on the AST. The window's ruling supersedes the
SPEC's earlier "the loop calls it between cycles", and the supersession is
written down.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "mini needs to be tested in isolation" | done in T1; fence re-run (3 passed) | `mini/tests/test_isolation_fence.py` |
| R2 | "not limit prose length at all" | done on the shell road (T2, T3); the call-layer clip stays PARKED P8 | T3/DELIVERY.md |
| R3 | "run its full conjecture/criticism cycles with commitments disabled" | done in T2 | T2/DELIVERY.md |
| R4 | "a new kind of artifact that generates commitments on conjectures, but does not force a strict format" | **done-with-assumption** (a record, not an artifact — see below) | commit `ee3f9a382`; VALIDATION S4 accepts 1-3 |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | done in T3; re-proven here with the real writer | `test_the_seats_that_see_everything_see_the_proposal_and_the_critic_does_not` |
| R6 | "conjecturers see everything generated so far and so do commitment artifacts" | done in T3; the pool now carries records too | commit `ee3f9a382` |
| R7 | "… calibrated on the fly and modifiable by the controller" | **the calibration half DECLARED**: the hook, its registry, the no-op | commit `05ed9ce20`; VALIDATION S7 accepts 1-2 |
| R8 | "Don't change the controller just yet" | **honoured and enforced** — zero callers on the AST | commit `908340f00` |
| R9 | "the mini flow … adjustable in a pluggable way" | seat side done (T3); the flow is T5 | — |
| R10 | "add new artifact types on the fly" | a new type's record road is a registration (`record_mini_output(kind, …)`); its stage is T5 | commit `ee3f9a382` |
| R11 | "test this new config in isolation" | done in T1 | T1/DELIVERY.md |
| R12 | "It's starting input should be standard." | done in T1 | T1/DELIVERY.md |
| R13 (Amdt 1) | "within mini, criticism can't overturn anything" | **honoured, and structural now** — a record is outside the artifact map | commit `98e0906b9` |
| R14 (Amdt 1) | "the point is content generation for now" | **honoured** — nothing under `src/` changed | `git diff --stat e83df7dfd -- src/`: empty |
| R-stored | "the current default conjecture form needs stored but not deleted" | done in T2 | T2/DELIVERY.md |
| R-again | "the episodes … need to be tested again" | deferred | window: "episodes (R-again, later)" |
| R-history | "One more history conjecture experiment" | deferred | operator: "But before that:" |

## Assumptions the operator may override

**R4 is done-with-assumption: a commitment proposal is a RECORD, not an
artifact.** Your words say "a new kind of artifact"; what ships is a new kind
of thing in the record — a typed event with its body in a blob — rather than
an entry in the artifact map. Decided without asking because every value you
have stated points the same way: no frozen surface without a grant (the
artifact road measured CONTACT on the harness surface), criticism overturns
nothing (a record cannot be attacked or refuted; an artifact can), smallest
correct change (nothing under `src/`). If you want it in the artifact map
proper, the cost is a grant to widen the provenance role on the harness
surface, and the road is otherwise ready.

**SPEC S7's "the loop calls it between cycles" is superseded** by the
window's ruling that the hook has zero callers. The later word wins.

A7 unchanged and the hook is built to it (selected once per run by id). A1–A6,
A8 carried; A9 is your ruling.

## Budget

**EXCEEDED and re-baselined.** 332 against 180, itemised per file in SPEC.md
§Budget with code separated from docstring. T4 restated as ~330; the
programme as ~2 250. The T4-specific cause: the record shape was chosen over
the artifact shape after measuring a contact the forecast did not cover.

## Map delta

changed: `docs/map/SUB-minireason.md` (the record shape and the closed road;
the hook and the supersession; four rows; 3 checks),
`docs/map/CON-packs-and-token-economy.md` (the reduced engine's rows; 1
check), `docs/map/INV-render-layout.md` (mini's compositions and the
retention knobs; 1 check).
created: none.
new checks: 5, none flagged vacuous, each shown red under a mutation.
left stale: 22 documents, none of them this tranche's; the three edited
carry `9d87325c3`.

## Errata

errata: none. No committed document was found to state something false.
SPEC S7's "called between cycles" and CHECKLIST step 34's wording were
superseded by a later operator ruling, not found wrong; both say so in
place.

## Parked (not done, not promised)

No new entry. P8 (the silent clip) stays binding on T5. P3's full-harness
half stays parked.

**recommended next: T5 (steps 39–45).** It is the last sub-tranche of this
window and the one that makes the three seats a FLOW: a registered
`MiniFlowV1` whose stage order and artifact-kind set are data, a loop that
walks stages and names no seat, a fourth artifact kind added by registration
alone, and the five architecture tests with their mutation proofs. It must
also dispose of P8 before the isolation flow dispatches a shell-rendered
brief.
