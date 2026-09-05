# Delivered: T5 — the pluggable flow and the architecture tests (S8, S9)
Sub-tranche T5 of the mini isolation programme.
Branch: `claude/mini-isolation-t3-t5-7tsc6d` (pushed, tree clean; head in the step-45 commit).
Base: `d800b622b` (T4's delivery head). Validation: `T5/VALIDATION.md`, PASS.

## What changed

**The three seats are a flow, and the flow is data.** `mini/minireason/flow.py`
registers `MiniFlowV1`s by id: a tuple of stages, each naming a seat, the
shell it renders through, the kind it produces and the kinds it reads; the
SET of artifact kinds the flow may carry; its commitment policy; its
calibration hook. A stage naming a kind the flow does not declare is refused
at construction. Two ship. The default, `mini.flow.legacy-v0`, is one
conjecturer stage under a legacy shell that renders today's prompt byte for
byte through the same road as every other seat and fills the stored form
with both commitment channels on. `mini.flow.isolation.v1` is conjecture,
then criticism once per conjecture this cycle, then commitment once per
conjecture this cycle, with both channels off and the typed warning.
Selection is an argument, then `DEEPREASON_MINI_FLOW`, then the default.

**The loop walks the flow and names nothing.** Each cycle walks the selected
flow's stages in order. Every stage renders its brief through the shell,
resolves its form through the shell, dispatches through the one leased
route, and disposes of the reply by the form's own shape: a form that
declares how to read records off its reply writes one record per item about
the conjecture the seat was shown, keeping what the seat itself named; a form
without that declaration is the conjecture road, lifted unchanged into its
own function. No string constant in the loop equals any registered seat,
shell, layout, flow, stage or kind id, and the legacy prompt text has moved
out of the loop into a plugin.

**A new artifact kind is a registration.** A successor-question seat —
form, layout, shell, stage and a flow naming them — declared entirely in a
test file runs two cycles end to end against the stub, its kind lands in the
record, the next cycle's conjecturer sees it whole, and every file under the
engine has the same modification time before and after. A second proof in
the architecture suite does the same under unique ids.

**Five architecture checks go red on a bypass**, each shown red under a
planted mutation before it was written down: the loop names no seat, kind or
stage (enumerated from the registries, matched as whole string constants);
no evidence-side path reads a mini seat name or kind; a section added to a
mini brief needs no source edit; a new artifact kind needs no source edit;
only the no-op calibration hook is registered.

**Both flows run offline, and the record holds.** In the isolation run the
critic's briefs carry no proposal and no objection, the later seats see the
earlier cycle's objection and proposal whole, no status moves, the record
replays and verifies, and the meter equals the log. Selecting nothing walks
the legacy flow: today's prompt, no mini record, no mini marker. T5 changed
nothing under `src/`; the full gate is unchanged at 5084 passed.

**The silent clip is disposed.** The loop hands the everything section its
share of the profile's prompt budget, so the retention rule withholds and
names what does not fit rather than the call layer cutting it, and any brief
that still overruns the clip is written to the record as clipped with both
sizes. The call layer itself is untouched.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "mini needs to be tested in isolation" | done in T1; the fence holds over the isolation flow | `mini/tests/test_isolation_fence.py`, 3 passed |
| R2 | "not limit prose length at all" | done (T2, T3); P8 DISPOSED here | commit `af8be33a8`; `test_the_isolation_flow_runs_end_to_end` (no brief clipped) |
| R3 | "run its full conjecture/criticism cycles with commitments disabled" | done in T2; the isolation flow declares it | commit `33a9de950` |
| R4 | "a new kind of artifact that generates commitments on conjectures, but does not force a strict format" | done in T4 (as a record); its stage runs here | commit `af8be33a8` |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | done in T3; re-proven live here | VALIDATION S8 accept 1 |
| R6 | "conjecturers see everything generated so far and so do commitment artifacts" | done in T3; re-proven live here | VALIDATION S8 accept 1 |
| R7 | "all three seats need the same pluggable interface … calibrated on the fly and modifiable by the controller" | **done** — one road, one dispatch by form shape; the hook declared (T4) and named on the flow as data | commits `33a9de950`, `af8be33a8` |
| R8 | "Don't change the controller just yet" | **honoured and enforced** | architecture check 5, `proof/mutation_5.txt` |
| R9 | "The mini flow also needs to be adjustable in a pluggable way" | **done** | commit `33a9de950`; VALIDATION S8 accepts 1-2 |
| R10 | "and add new artifact types on the fly if I can see it might help" | **done-with-assumption A7** (at run configuration time) | commits `a50a6edfe`, `3cad7b3a3`; VALIDATION S8 accept 3, S9 accept 1 |
| R11 | "The last part is to test this new config in isolation without the larger harness activated" | **done** — the isolation flow runs end to end offline, fenced | `test_the_isolation_flow_runs_end_to_end`; the fence |
| R12 | "It's starting input should be standard." | done in T1; every stage's brief carries it | `mini.problem` in every layout |
| R13 (Amdt 1) | "within mini, criticism can't overturn anything" | **honoured, structural** — a criticism is a record outside the artifact map; `refuted == 0` in the isolation run | commit `af8be33a8`; architecture check 2 |
| R14 (Amdt 1) | "the point is content generation for now" | **honoured** — nothing under `src/` changed | `git diff --stat d800b622b -- src/`: empty |
| R-stored | "the current default conjecture form needs stored but not deleted" | done in T2; the DEFAULT flow fills it | `test_the_legacy_flow_is_todays_loop` |
| R-again | "the episodes … need to be tested again" | deferred | window: "episodes (R-again, later)" |
| R-history | "One more history conjecture experiment" | deferred | operator: "But before that:" |

## Assumptions the operator may override

**A7 — "on the fly" is at run configuration time.** A flow is resolved once
before the first call and never changes during a run; a fourth kind is
registered before the run starts. If you want kinds added while a run is in
flight, that is a change to what a replay of one log can disagree about, and
it needs its own design.

**Every mini stage's call carries the role of the one leased route,
`conjecturer`, even when the critic or commitment seat spoke.** The manifest
refuses roles it does not know, so a per-seat role is a grant on a frozen
surface. The seat is named by the record event that carries the call's
spend, so the record is not silent about who spoke; one field is. Parked as
P9 with a ready-to-send prompt.

**The legacy road's prompt gains one header line** from the shared
allocator. No committed test pinned the old bytes; the new golden pins them
with the header asserted. Byte-exact reproduction would cost a second
renderer in mini or a change under `src/`.

A1–A6, A8 carried; A9 is your ruling.

## Budget

**EXCEEDED and re-baselined.** 619 insertions against 240 by the gate's
count, 401 net lines, 256 of code, itemised per file in SPEC.md §Budget. The
T5-specific cause: the loop rewrite lifts two hundred lines of the existing
conjecture road into a function the stage walk can call, which the line
count reads as new. The programme total by the gate's count is ~2 850 against
the 1 320 it was priced at; P7 records why and the shape every re-baseline
took.

## Map delta

changed: `docs/map/SUB-minireason.md` (the flow section, the enforcement
section, the `flow` parameter on the entry point; 4 checks),
`docs/map/SEAM-llm-x-minireason.md` (the loop crosses the seam; P8 disposed;
the role trap).
created: none.
new checks: 4, none flagged vacuous, each red under a mutation.
left stale: 22 documents, none of them this tranche's; the two edited carry
`2b6440d28`.

## Errata

errata: none. No committed document was found to state something false.
SPEC S8's substring check has a pre-existing false positive (a relapse-domain
label), recorded where it is disposed rather than corrected as an erratum;
the SPEC's claim was right and its sketch of the check was loose.

## Parked (not done, not promised)

**P8 is DISPOSED** (road (c) plus a typed marker); the entry stays with its
prompt for whoever wants the cut disclosed inside the brief itself.

**One new entry, P9 — a mini call's role names the leased route, not the
seat.** Its prompt is in `PARKED.md`; it is P2's sibling and may be taken with
it.

P1–P7 unchanged.

**recommended next: T6 (steps 46–51), in the last window.** It is the
programme's regression sub-tranche: the full gate on an idle box, mini's own
suite, the two goldens, a mini isolation run that verifies and replays, and
the wheel smokes that no gate runs. Everything it will check has been run at
every delivery here; T6 records it once, as the programme's own boundary,
before T7 measures whether any of this is better than a single call.
