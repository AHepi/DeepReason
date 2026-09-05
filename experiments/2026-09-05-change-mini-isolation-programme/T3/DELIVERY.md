# Delivered: T3 — the mini source adapter and the three shells (S5, S6)
Sub-tranche T3 of the mini isolation programme.
Branch: `claude/mini-isolation-t3-t5-7tsc6d` @ `b2f2d48b3` (pushed, tree clean).
Base: `14cc5da495` (main, carrying T2's delivery). Validation: `T3/VALIDATION.md`, PASS.

## What changed

**A mini seat's brief is now a registered layout walked through the one
public road the full harness's seats share.** `deepreason.llm.packs` gains two
public entries, `render_seat_brief` and `allocate_seat_brief`, each exactly one
call to the private walk and allocator it fronts; the two shipped renderers
keep calling the private walk directly, which is why their bytes cannot have
moved and the goldens say they did not. Mini reaches those two names and no
private one, and an AST test over every mini module says so.

**Mini's record feeds the shipped plugins through one read-only projection.**
`mini/minireason/sources.py` turns a live mini session into the request the
section plugins already read. It appends nothing — log bytes, next sequence,
state digest, replay digest and `verify_root` are measured unchanged after
rendering — and it never reads an artifact's status, checked on the AST.

**Who sees what is decided by three layouts, and the critic's blinding is an
omission, not a filter.** The critic's layout registers problem, target
conjecture and directive, and NO section that could carry a commitment
proposal — there is no slot, blank or otherwise, which is the shape the
amended judge law already required of provenance blinding. Over a live root
carrying three planted proposals, not one byte of any proposal reaches the
critic's brief, while the conjecturer and the commitment seat see every
proposal and every conjecture, standing and refuted, whole. No mini brief
renders a status label of any kind; the refuted conjectures are still shown,
unlabelled, to the seats that see everything, because within mini a criticism
overturns nothing. Mutation-proven: a critic layout given the everything
section turns two tests red.

**"Everything so far" is shown in full, and what stays visible as the pool
grows is a rule the operator configures, never a verdict.** The legacy loop's
eight-survivor window and 300-character cut are gone from this road: twelve
~700-character prose conjectures render whole. A declared budget withholds the
OLDEST whole entries first, names them inside the section under the rule's id,
and never empties it. Two rules ship — everything (the default) and recency —
and a third is a registration.

**Three seats are shells, and the shell's form is finally read.**
`seat.mini.conjecturer.v0`, `seat.mini.critic.v0` and `seat.mini.commitment.v0`
each pair a layout with a relaxed form. `form_for_seat` takes the shell's
`form_id` as its declared default — the first consumer that field ever had —
so binding the critic's shell in the conjecturer's seat changes both the brief
rendered and the form asked for, which one test proves in one motion. The seat's
directive is data on the layout entry, so a file-declared layout rewords a
seat with no code. The full harness's two shells resolve exactly as before.

**The map covers the seam.** `docs/map/SEAM-llm-x-minireason.md` is new: fifty
symbol crossings one way and none back, four agreements each with a check
shown red under a mutation, and three traps. The one src/ change in T3 is the
29-line public entry; the full gate is unchanged at 5084 passed, 0 failed.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "mini needs to be tested in isolation" | done in T1; fence re-run at every module-adding step | `mini/tests/test_isolation_fence.py`, 3 passed |
| R2 | "mini artifact forms need to not limit prose length at all" | **done for all three limits on the shell road** (the third here); one further silent limit found one layer down and PARKED, not hidden | commit `fbf5b92f5`; VALIDATION sources suite; PARKED P8 |
| R3 | "run its full conjecture/criticism cycles with commitments disabled" | done in T2 | T2/DELIVERY.md |
| R4 | "a new kind of artifact that generates commitments, but does not force a strict format" | its form (T2), its shell and layout (here); its writer is T4 | commit `7be7326c0` |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | **done** | commits `fbf5b92f5`, `95eed62f9`; VALIDATION S5 accepts 1-3 |
| R6 | "conjecturers see everything generated so far and so do commitment artifacts" | **done-with-assumption A4** (everything in the run) | commit `fbf5b92f5`; VALIDATION S5 accept 1 |
| R7 | "all three seats … the same pluggable interface with relaxed forms and have the information they say calibrated on the fly and modifiable by the controller" | **the interface half done**; the calibration hook is T4 (S7) | commits `d661aadc1`, `7be7326c0`; VALIDATION S6 accepts 1-3 |
| R8 | "Don't change the controller just yet" | **honoured** | no hook, no controller call in T3 |
| R9 | "the mini flow … adjustable in a pluggable way" | the seat side is configuration now (layouts as data, directives as params, file-declared layouts); the flow is T5 | commit `fbf5b92f5` |
| R10 | "add new artifact types on the fly" | a new type's layout and shell are registrations; its stage is T5 | commit `7be7326c0` |
| R11 | "test this new config in isolation" | done in T1 | T1/DELIVERY.md |
| R12 | "It's starting input should be standard." | done in T1; the standard input's criteria now reach every mini brief | commit `0bcad7211`; `test_the_frozen_criteria_reach_the_request_only_from_the_standard_input` |
| R13 (Amdt 1) | "within mini, criticism can't overturn anything" | **honoured, and enforced one layer further** — no source reads a status, no brief renders a label | commit `95eed62f9` |
| R14 (Amdt 1) | "the point is content generation for now" | **honoured** — no authority path changed | `git diff --stat 14cc5da495 -- src/`: one file, 29 lines |
| R-stored | "the current default conjecture form needs stored but not deleted" | done in T2; one selection away from any mini seat here | `test_the_shell_is_the_default_and_the_declared_orders_still_win` |
| R-again | "the episodes … need to be tested again" | deferred | window: "episodes (R-again, later)" |
| R-history | "One more history conjecture experiment" | deferred | operator: "But before that:" |

## Assumptions the operator may override

**A2 — discharged on the shell road, with one residue named.** Field bounds
and the skeleton (T2), and now the truncation of what a seat is shown, are
gone. What remains is the profile clip in mini's call layer, which cuts every
prompt at the profile's pack budget (4 800 characters on compact) silently.
It is parked as P8 with a binding note: T5 must keep the shipped isolation
flow's briefs inside the clip by configuration or dispose of the clip with a
notice, and say which.

**A4 — exercised.** "Everything generated so far" is everything in the RUN.
A future multi-problem flow narrows it by a plugin parameter, not by an edit.

**Decided without asking (dominant under your recorded values):** the
retention rules shipped are everything (default) and recency; novelty by the
equivalence tiers is a registration when a run asks for it. Override any time.

A1, A3, A5, A6 (amended in T1), A7, A8 carried unchanged.

## Budget

**EXCEEDED and re-baselined.** 636 against 240, itemised per file in SPEC.md
§Budget with code separated from docstring, trimmed before disclosing. The
cause PARKED P7 already names, plus one specific to T3: the retention-as-a-rule
ruling arrived after the numbers were written. T3 restated as ~640, the
programme as ~2 100.

## Map delta

created: `docs/map/SEAM-llm-x-minireason.md` (5 checks).
changed: `docs/map/SUB-minireason.md` (who sees what, the shells, four
entry-point and where-to-change rows; 3 checks), `docs/map/INV-seat-section-
plugins.md` (the public road, the `form_id` consumer invariant; 2 checks),
`docs/map/CON-packs-and-token-economy.md` (the allocator's three callers; 1
check moved with the code), `docs/map/INDEX.md` (the seam row and why it
carries no count), `docs/map/SUB-llm.md` (the seam named).
new checks: 11, none flagged vacuous, each shown red under a mutation.
left stale: 22 documents, none of them this tranche's; the six whose checks
the full run re-derived at `f8100b9b0` carry that stamp.

## Errata

errata: none. No committed document was found to state something false. The
one map claim that became false ("only two renderers are on the IR") was true
until this tranche's own public entry made it false, and it moved in the same
commit — a document brought up to date with the code beside it, not a
committed claim found wrong.

## Parked (not done, not promised)

**One new entry, P8 — mini's call layer clips every prompt silently.**
`call.py` runs `clip_pack(prompt, profile)` on every prompt, a prefix cut at
the profile's pack budget with no notice in the brief and no marker in the
record — a third length limit S2(c) did not name, one layer below the two it
removed. Not fixed here: the call layer is none of T3's items, and the fix is a
priced fork (a typed disclosure in the brief, a raised or configurable pack
budget, or a retention budget that sits inside the clip). Its ready-to-send
prompt is in `PARKED.md`; it binds T5 to dispose of the clip before the
isolation flow dispatches a shell-rendered brief.

P1–P7 unchanged. P3's mini half is done here; its full-harness half stays
parked.

**recommended next: T4 (steps 32–38).** It is the next sub-tranche in the
programme's order, and it completes what T3 built the shell for: the
commitment seat that writes `mini.commitment-proposal.v1` into the record
through the layout and form registered here, the shape-buys-nothing test over
that kind, and the controller hook declared with a no-op default and — per the
window's ruling — zero callers.
