# Delivered: T2 — relaxed forms and the commitment switch (S2, S3)
Sub-tranche T2 of the mini isolation programme.
Branch: `claude/mini-isolation-t0-t2-upwc47` @ `c09a10b18` (pushed, tree clean).
Base: `577365da4` (T1's delivery head). Validation: `T2/VALIDATION.md`, PASS.

## What changed

**A mini seat can be asked for prose, and the stored form did not move.**
`mini/minireason/forms.py` registers four forms by id, beside each other: the
stored conjecturer form, a relaxed conjecturer, a relaxed critic and a relaxed
commitment proposal. None of them bounds a string or a list at any nesting
depth, and none requires a skeleton, so a candidate that is one paragraph of
prose is a well-formed candidate. Choosing one is an argument, then
`DEEPREASON_MINI_FORM`, then the caller's declared default — never `Config`
and never the manifest, because a field there would move the digest of every
qualification bundle in the tree.

The stored form is registered beside the relaxed one rather than replaced by
it, and it HOLDS the shipped contract instance rather than a copy, so "stored,
not deleted" is a property of an object nobody rewrote. Its rendered bytes are
pinned by a golden that was committed **before** the registry that would have
made changing it easy.

**Cycles can now run with commitments disabled, and the run says so.** Two
switches, not one, because there are two channels and either must be
restorable: the mandatory well-formedness commitment compiled onto every
candidate, and the candidate's own `forbidden[]` cases. Both default ON.

This is the half without which relaxing the form buys nothing, and the numbers
say so. The same free-prose endpoint that ends **6 admitted, 6 refuted, zero
survivors** under the default policy ends **0 refuted, 6 survivors** with both
channels off — and the record still replays. Switching a channel off writes a
typed warning into the run's own record, one marker per disabled channel plus
a summary line, so a reader opening that root months from now can see which
checks did not run. Never a refusal, and never silence.

Within mini a criticism overturns nothing, and that is now enforced rather
than promised: the critic and commitment forms carry no score, rank, weight,
confidence, priority, authority or severity field, and a check enumerates every
registered schema to prove it.

T2 changed no file under `src/` at all. The full gate is unchanged from T1.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "mini needs to be tested in isolation" | done in T1 | T1/DELIVERY.md |
| R2 | "mini artifact forms need to not limit prose length at all" | **done for two of three limits; the third is named and assigned** | commit `a61817bca`; VALIDATION S2 accept 1. The third — truncating what a seat is SHOWN — is T3's S5 |
| R3 | "run its full conjecture/criticism cycles with commitments disabled" | **done** | commit `08692aab4`; VALIDATION S3 accepts 1 and 2 |
| R4 | "a new kind of artifact that generates commitments, but does not force a strict format" | its FORM ships (only requirement: name the conjecture); its seat is T4 | commit `a61817bca` |
| R5 | "critics see the conjecture artifact, not the proposed commitments" | owned by T3 (S5) | — |
| R6 | "conjecturers see everything generated so far" | owned by T3 (S5) | — |
| R7 | "all three seats … the same pluggable interface with relaxed forms" | **the relaxed-forms half done**, one per seat; the shells are T3 | commit `a61817bca` |
| R8 | "Don't change the controller just yet" | **honoured** | no hook declared, no controller called in T2 |
| R9 | "the mini flow … adjustable in a pluggable way" | file-declared half done (T0); the flow is T5 | T0/DELIVERY.md |
| R10 | "add new artifact types on the fly" | a form for a new type is a registration now; the rest is T5 | commit `a61817bca` |
| R11 | "test this new config in isolation" | done in T1 | T1/DELIVERY.md |
| R12 | "It's starting input should be standard." | done in T1 | T1/DELIVERY.md |
| R13 (Amdt 1) | "within mini, criticism can't overturn anything" | **honoured, and now enforced** | commit `a61817bca`; the shape-buys-nothing check over every registered schema |
| R14 (Amdt 1) | "the point is content generation for now" | **honoured** | no authority path changed |
| R-stored | "the current default conjecture form needs stored but not deleted" | **done** | commit `c31fb1811` (the golden, committed first) and `a61817bca` (registered beside, not replaced) |
| R-again | "the episodes … need to be tested again" | deferred | window: "episodes (R-again, later)" |
| R-history | "One more history conjecture experiment" | deferred | operator: "But before that:" |

## Assumptions the operator may override

**A1 was EXERCISED here and holds.** "Commitments disabled" means both
channels: with only the model-authored one off, the mandatory well-formedness
commitment still refutes every free-prose candidate on arrival. Both switches
are independent, so either can be restored.

**A2 is two-thirds discharged.** Two of R2's three limits are gone — field
bounds and the required skeleton. The third, the truncation of what a seat is
SHOWN, is T3's; a form that accepts unlimited prose feeding a brief that shows
300 characters of it would not be an unlimited channel.

A3, A4, A5, A7, A8 carried unchanged. A6 was amended in T1.

## Budget

**EXCEEDED and re-baselined.** 413 against 175, itemised per file in SPEC.md
with code separated from docstring, and trimmed before disclosing. Parked as
**P7**: this is the second consecutive overrun with the same cause — the
estimates priced the mechanism, not the obligations the standing laws attach to
it — so T3–T7's numbers should be read as lower bounds rather than ceilings.

## Map delta

changed: `docs/map/SUB-minireason.md` — one new section (forms, their
selection order and the measured reason it avoids `Config`; the two commitment
channels, the before/after measurement, the typed warning; the operator's
ruling that criticism overturns nothing), two `Where to change what` rows, and
three checks. One existing row was CORRECTED: it said mini owns "which
commitments a candidate must satisfy", which this change makes wrong in a way
that matters — mini owns which channels it COMPILES, never what a commitment
MEANS.
created: none.
new checks: 3, none flagged vacuous.
left stale: 23 documents, none of them this tranche's.

## Errata

errata: none. No committed document was found to state something false. The
one corrected claim is in `SUB-minireason.md`, which this programme created
four commits earlier — a document being brought up to date with the same
tranche's code, not a committed claim found wrong.

## Parked (not done, not promised)

**One new entry, P7 — SPEC.md's per-item line estimates are lower bounds, not
ceilings.** T1 overran 1.3x and T2 2.4x, both because the numbers priced the
mechanism and not the typed refusals, disclosure records and per-channel naming
the standing laws attach to it. It is not a defect and not a reason to write
less: the alternative in both cases was a smaller change that lies about
itself. Its note is in `PARKED.md` and it is addressed to whoever plans
T3–T7, not to a fix tranche.

P1–P6 unchanged, except that **P6 was closed by T1**.

**recommended next: T3 (steps 23–31).** It is the next sub-tranche in the
programme's order and it discharges the rest of R2 — the third length limit,
the truncation of what a seat is SHOWN — alongside R5 and R6, which are the
same mechanism seen from two sides. It is also where the relaxed forms this
sub-tranche registered acquire their first consumer, through
`SeatShellV1.form_id`.
