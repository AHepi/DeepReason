# Delivered: T1 — isolation, the standard input, the fence (S1, S11a)
Sub-tranche T1 of the mini isolation programme.
Branch: `claude/mini-isolation-t0-t2-upwc47` @ `29d096f16` (pushed, tree clean).
Base: `d319f2d6c` (T0's delivery head). Validation: `T1/VALIDATION.md`, PASS.

## What changed

**A mini run can start from the standard input.** `deepreason reason --shallow
--run-input ROOT` takes the `RunInputManifestV2` that `deepreason input
freeze` writes and the full harness already takes — a problem and its criteria
— instead of a bare question. The frozen record decides the problem's id and
its description, and is bound to the run root in place of mini's constant
process root. The bare-question form is unchanged, and mechanically so: the
frozen input is passed to the engine only when there is one, so the test that
proves it takes no `**kwargs` and would fail on any extra argument.

Four things are refused rather than guessed at, each typed at the point of
use: an unreadable or v1 frozen input; a dossier naming evidence sources,
whose blobs would have to be staged into the run root before the record could
be bound there truthfully; a question that contradicts the frozen one; and
reopening a root against a different frozen input, because a root's identity
includes what it was asked. Frozen criteria reach the root's identity but are
not compiled into commitments by the reduced engine, and the result says so
with its own notice rather than leaving a reader to infer it from a count.

**"In isolation" is a test now, not a claim.**
`mini/tests/test_isolation_fence.py` has three parts: mini's own sources
import no fenced module directly; importing mini adds no fenced package beyond
what the record modules it is allowed to use already bring; and a run imports
no fenced module that was not loaded when it started. Each was shown red under
its own mutation (`proof/fence_mutation.txt`), and the third mutation shows
why the third part exists — a lazy `import deepreason.qualification` inside
the run loop walks straight past the first two.

Two real violations were found and fixed. `compat.py` imported
`deepreason.bridge.retry` directly; it takes the same class from
`deepreason.run_manifest` now, so mini depends on the record's schema rather
than on the subsystem that defines it. And importing
`deepreason.application.conjecture` — a boundary a reduced-engine run
legitimately uses — dragged the whole v6 text-run stack in, because the
package eagerly re-exported it. Those three names are lazy now; the public
surface is unchanged.

**The map covers mini for the first time.** `docs/map/SUB-minireason.md` is
the first document for `mini/minireason/` — 2 700 lines reached by a public
CLI flag that were under no document's `Owns:` header. Eleven checks, none
vacuous. `INDEX.md` gains the routing row, the subsystem row, and a corrected
coverage statement, closing the programme's parked P6.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "mini needs to be tested in isolation" | **done** | commit `12ed86b97`, `f5499b227`; VALIDATION S1 accept 1 |
| R2 | "not limit prose length at all" | owned by T2 (S2) | — |
| R3 | "cycles with commitments disabled" | owned by T2 (S3) | — |
| R4 | "a new kind of artifact that generates commitments" | owned by T4 (S4) | — |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | owned by T3 (S5) | — |
| R6 | "conjecturers see everything generated so far" | owned by T3 (S5) | — |
| R7 | "all three seats … the same pluggable interface" | prerequisites done (T0); shells are T3 | T0/DELIVERY.md |
| R8 | "Don't change the controller just yet" | **honoured** | no hook declared, no controller called in T1 |
| R9 | "the mini flow … adjustable in a pluggable way" | file-declared half done (T0); flow is T5 | T0/DELIVERY.md |
| R10 | "add new artifact types on the fly" | file-declared half done (T0); rest is T5 | T0/DELIVERY.md |
| R11 | "test this new config in isolation without the larger harness activated" | **done-with-amendment (A6)** | commit `f5499b227`; VALIDATION S1; SPEC.md §S1 states what the fence does NOT prove |
| R12 | "It's starting input should be standard." | **done** | commit `f2b736b6a`; VALIDATION S1 accept 2 |
| R13 (Amdt 1) | "within mini, criticism can't overturn anything" | **honoured** | T1 builds no elimination road |
| R14 (Amdt 1) | "the point is content generation for now" | **honoured** | no authority path changed |
| R-stored | "the current default conjecture form … stored but not deleted" | owned by T2 (S2) | nothing in T1 touches any form |
| R-again | "the episodes … need to be tested again" | deferred | window: "episodes (R-again, later)" |
| R-history | "One more history conjecture experiment" | deferred | operator: "But before that:" |

## Assumptions the operator may override

**A6 was amended during this sub-tranche, before any code was written.** SPEC's
S1 said a mini isolation run "must not import, at run time" any of eleven
packages. Four of them are already loaded by the modules S1 itself allows,
because the event ontology imports its bridge and capability payload types and
the harness imports the adjudicator's edge builders — and those modules ARE
the record rather than the harness around it, which is why they were allowed.
So the fence now proves what can be proven: mini reaches for nothing in the
larger harness, and adds nothing to what the record already carries. It does
not prove that no code inside those four packages ever executes; the spec, the
map document and the test's own docstring all say so.

Every other assumption (A1–A5, A7, A8) is carried unchanged from SPEC.md.

## Budget

**EXCEEDED and re-baselined rather than absorbed.** 218 insertions against
170, before `SUB-minireason.md`. SPEC.md §Budget now carries the per-file
itemisation: S1 priced accepting a flag, and three obligations came with it
that standing laws require — a typed refusal at the point of use, a disclosure
that frozen criteria are bound but not compiled, and refusals keeping an
optional question from becoming a silent difference between the two paths.
T1 restated at ~300; the programme total 1 320 → ~1 450.

## Map delta

created: `docs/map/SUB-minireason.md` (11 checks).
changed: `docs/map/INDEX.md` (routing row, subsystem row, corrected coverage
statement with its own check), `docs/map/SUB-application.md` (the
`--run-input` road, the lazy text-run re-export).
new checks: 13, none flagged vacuous by `--audit`.
left stale: 23 documents, none of them this tranche's.

## Errata

errata: none. No committed document was found to state something false. The
one thing found wrong was **this programme's own SPEC.md §S1**, which is a
live tranche artifact rather than a committed document `docs/ERRATA.md`
covers — it was amended in place, on the record, with the measurement that
falsified it (commit `33b4c7040`).

## Parked (not done, not promised)

No new parked item. Two existing ones moved:

- **P6 — nothing says where `mini/` is documented: CLOSED by this
  sub-tranche.** `INDEX.md` now routes to `SUB-minireason.md` and its
  coverage statement carries a check.
- **P1 — mini's tests are outside the gate: still open, and now WRITTEN DOWN
  where a reader will hit it.** `SUB-minireason.md`'s first Trap states it,
  with a check that goes red the day the gate starts reaching mini.

One new thing worth the operator's attention that is NOT a parked defect: this
tranche twice scoped map work to the single document a checklist step named
while other steps changed files a different document owned. Both were caught
by `docs_verify --stale` before validation closed, and both were repaired as
their own steps (8a, 14a). The lesson belongs in the checklist-writing habit,
not in a fix tranche.

**recommended next: T2 (steps 16–22).** It is the next sub-tranche in the
programme's order, and it is the one that makes R2 and R3 real — the mini form
registry with the stored default registered beside it, and the commitment
switch. The design already measured that R2 without R3 produces a run with
zero survivors, so the two must land together, which is how T2 is scoped.
