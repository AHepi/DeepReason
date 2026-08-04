# Delivered: Rung 7 — authority as a declared policy (SPEC approved; sub-tranche 7a executed)
Branch: `claude/delivery-rungs-handover-m22sdy` @ `575119f5` (pushed, tree clean)
Tranche base `2cc3fd50`. 7 commits.

## What changed

Two things: a design, and one document that makes its central finding
re-runnable.

**The design (approved, not built).** Rung 7 asked for "one narrow gate
consulting a declared policy" for status changes. Measured against the
tree, that sentence has two halves with opposite verdicts. The gate
already exists and is one line — `final_labels` is the only producer of
`Status`, `Harness._adjudicate` its only caller and the sole writer of
`state.status`. Consulting a policy *there* is forbidden: labels are
recomputed on every root open, never replayed, so patching the label
function to be policy-dependent and reopening `run-f4fa6663`'s unchanged
bytes moves its recorded `REFUTED` count from 1 to 0. Six committed
roots and 26 recorded verdicts sit in that blast radius. The same
experiment at the other end — sabotaging `register_fail_warrant` so any
mint execution raises, then reopening the same root — changes nothing,
because replay never executes `rules/`. So the approved design (Option
D) puts the declared policy at MINT time, where it is invisible to
replay, and forecasts zero frozen-surface contact conditional on exactly
that placement. Three alternatives were priced and rejected on
measurements: label-time (moves committed roots), manifest-declared
(frozen surface 4 plus every qualification digest), and a universal gate
over all 17 mint sites (six of the eight demonstrative-minting modules
deliberately consult no authority, and `code`/`formal` workloads bypass
the policy entirely).

**The document (built).** `docs/map/SEAM-adjudication-x-authority.md` is
new: the pair the map preflight found listed `Seams-undocumented:` on
`SUB-adjudication.md` and missing from `INDEX.md`'s matrix — and the
exact pair rung 7's finding is about. It carries eight column-0 checks,
two of which ARE the finding as executable commands. Both were
mutation-proven failable before being written down (`_adjudicate` made a
no-op; `build_att` gutted to `return set()`). It is wired in: the
`INDEX.md` matrix row, `SUB-adjudication.md`'s `Seams:` header and seam
table, and `CON-authority.md`'s `Seams:` header — which was entirely
EMPTY before this, the same ERRATA E9 shape rung 1 found in six other
documents.

**Proof:** `docs_verify` 51 documents / 815 checks (was 50 / 807 —
exactly the 8 added), `--audit` 0, `--links` 0 dangling, `--coverage` 0
findings; frozen-surface diff EMPTY; zero `src/` and `tests/` contact,
so 7b and 7c remain untouched.

## The tree this landed in is not clean — read this before the table

Four instruments are red, none of them from this tranche, all four
traced to one commit and one mis-specified test.

    docs_verify: 2 failed   SEAM-harness-x-verification.md:253, SEAM-manifest-x-schools.md:271
    full gate:   2 failed   test_module_fingerprints.py::test_every_committed_root_reads_as_having_no_module_fingerprints
                            test_module_fingerprints.py::test_the_census_of_committed_roots_is_unchanged
                            (2 failed, 3336 passed, 7 skipped)

Bisected: `f6d41bff` (rung 5's A/B arm A) is the first bad commit — 20
passed before it, 2 failed after — and both tests still fail at rung 7's
base `2cc3fd50` in a clean worktree holding none of this tranche's work.

The roots are not the problem. `test_module_fingerprints` asserts
`recorded_module_fingerprints(harness) == ()` for EVERY committed root,
while its own docstring states the intended claim as absence being valid
"on every root written **before this feature**". Those are different
claims: the implemented one says "no root has been committed since the
writer landed", which is a fact with an expiry date. Rung 4 shipped the
writer and the test together, so the first live run committed afterwards
was guaranteed to break it — and rung 5's A/B arms were that run,
correctly performed and correctly committed.

Consequently two of rung 5's `DELIVERY.md` proof claims — "full gate
3338 passed / 0 failed" and "`docs_verify` 0 failed" — were true when
measured at `7fdff121` and false from `f6d41bff`, inside that tranche's
own post-delivery segments. The arithmetic corroborates it: 3338 = 3336
+ 2, same population. Neither claim is dishonest; neither states the
commit it was measured at. **The generalizable gap:
`dr-deliver-change` measures before the live-evidence commits it
enables, and nothing re-measures afterwards.** Parked as P1, not fixed
— the operator scoped this tranche to 7a only, and cross-routing parks
a defect found mid-change.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Now Rung 7 via `dr-change-orchestrator`" | done | phase artifacts in order; VALIDATION R-sweep |
| R2 | "DESIGN-AND-STOP, through dr-spec-change ONLY" | done | held at `e1e23990`; resumed only on Amendment 1 |
| R3 | "STOP after committing SPEC.md and present it" | done | `e1e23990`, presented, then waited |
| R4 | "the frozen-surface contact forecast is where this spec lives or dies" | done | SPEC S2; forecast measured surface-by-surface; 4a2 diff empty; M5/M6 now executable as checks 1-2 |
| R5 | "One rung only." | done | rung 6's directory untouched; no rung 8 |
| R6 | "a SPEC for routing every status change through one narrow gate consulting a declared policy" | done-with-contradiction-recorded | SPEC's finding: half 1 already exists (M1), half 2 forbidden (M5). Property delivered at mint time per ERRATA E10's rule; contradiction written down, not redesigned around |
| R7 | "the most dangerous socket (CON-authority; adjudication; frozen-adjacent everywhere)" | done | all three read at preflight; the new document's `Sides:` names two, its body the third |
| R8 | "Do not write this SPEC before rungs 1–4 are delivered" | done | rungs 1-5 all have DELIVERY.md |
| R9 | "Option D … A1–A5 stand … mint-time placement … accepted" | done | Amendment 1; placement now enforced by check 1, not merely asserted |
| R10 | "Do NOT execute 7b or 7c" | done | `git diff --stat 2cc3fd50..HEAD -- src tests` empty |
| R11 | "You MAY execute 7a only (the seam document, docs-only)" | done | map delta at `725dcab1`; VALIDATION S8 |
| R12 | "then stop and confirm the program is complete" | done | the program table below — and the answer is *not* an unqualified yes |

No requirement is `not-done`. R6 is the one worth reading twice: what it
asked for was measured impossible in its literal form, so the property
was delivered and the contradiction recorded — which is what C5 (ERRATA
E10) prescribes.

## The rung program, rung by rung (R12)

| Rung | State | Evidence |
|---|---|---|
| 1 — sockets on paper | delivered | `2026-08-03-change-rung1-sockets-on-paper/DELIVERY.md` |
| 2 — buried choices become switches | delivered, 3 tranches | config-inventory, engaged-criticism-switch, bridge-unification |
| 3 — a registry in front of one thing | delivered, 2 tranches | rung3 (registry built), rung3b (call sites migrated) |
| 4 — every run records which modules built it | delivered | `2026-08-04-change-rung4-module-fingerprints/DELIVERY.md` |
| 5 — one deliberately dumb alternative | delivered; live A/B exercised | R7 moved `not-exercised` → `done` after the second credential worked |
| 6 — qualify plugins the way models are qualified | **SPEC approved, execution deferred** | SPEC `2cc3fd50`; REQUEST R13 defers, R14 owes temp-dir cleanup at plan time |
| 7 — authority as a declared policy | **SPEC approved; 7a delivered, 7b/7c deferred** | this tranche |

**Is the program complete? Structurally yes; cleanly no.** All seven
rungs have reached their intended terminal state — five built, two
designed-and-approved with execution deliberately deferred by the
operator. Nothing is half-finished and nothing is silently dropped.

But the program does not end green, and it would be false to report it
as though it did. Four instruments are red (above), two delivered proof
claims are stale, and three items of real work are outstanding by the
operator's own instruction: rung 6's implementation, rung 7b, and rung
7c. P1 is the first thing to fix, because until it is, no future tranche
can distinguish its own breakage from the inherited kind — which is
precisely the cost this tranche paid to discover it.

## Assumptions the operator may override

- **A1** — the scatter worth consolidating is the LLM-mediated-text
  authority decision only; deterministic, execution and formal paths
  stay exempt. Measured (M4d, M9b); now documented and checked.
- **A2** — "declared" means `Config`-projected, not manifest-declared.
- **A3** — the policy object adds no new `Config` field, so the
  `_versioned_source_config_data` trap does not apply. Untested until 7b.
- **A4** — no typed reason string moves (M10).
- **A5** — authority does NOT become a registered module in the
  rung-3/5 sense; rung 6's registry-agnostic framework would apply if
  you later want that.

All five confirmed by you in Amendment 1 and carried into 7b unchanged.

## Map delta

**created:** `docs/map/SEAM-adjudication-x-authority.md` (8 checks).
**changed:** `docs/map/INDEX.md` (matrix row; "last six" → "last
seven"), `docs/map/SUB-adjudication.md` (`Seams:` header + seam-table
row), `docs/map/CON-authority.md` (`Seams:` header, previously empty).
**new checks:** 8 (807 → 815).

**left stale:** `CON-authority.md` — `--stale` lists it (6 commits to
owned files since `d057f306`), and its stamp was deliberately NOT
advanced. This tranche edited only its header and did not re-run its
check set; advancing the stamp would be the one dishonest state
`SCHEMA.md` names. `SUB-adjudication.md` is not listed and its stamp is
likewise unchanged for the same reason.

## Parked (not done, not promised)

- **P1** — four red instruments since `f6d41bff`; the mis-specified
  `test_module_fingerprints` assertion; two stale rung-5 proof claims;
  and the workflow gap that lets a delivered tranche invalidate its own
  measurement by committing evidence afterwards. **The recommended next
  tranche.**
- **P2** — `SUB-adjudication.md`'s authority row, resolved by 7a. No
  action owed.
- **P3** — `CON-authority.md`'s three still-undocumented seams
  (`authority x manifest`, `authority x rules`, `authority x
  scheduler`); `authority x rules` is where 7b would land.
- **P4** — the `argumentative_authority_mode` error-message asymmetry;
  a natural 7b companion.
- **P5** — the dead `single_family_trial` Config value; 7b makes it
  more visible, removing it is a behaviour decision.
