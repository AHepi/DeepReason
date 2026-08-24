# Parked — Rung 5 (promotion problems and their criteria as programs)

Found while doing Rung 5, not done, not promised. Each carries a
ready-to-send prompt so the follow-up costs a paste rather than an
authoring session.

---

## P1 — Re-nomination: a subject conjectured AFTER nomination can never be judged

**What.** The reach certificate freezes its candidate subject pool at
nomination (SPEC.md A5). A subject that did not exist then is absent from the
environment, so `promotion_subject_demarcation` and `promotion_accounts_for`
answer `overrun` with `subject-not-in-environment` — honest and typed, and it
means a genuinely better rival authored later cannot be adjudicated against the
incumbent on that promotion problem. Today the pool is adequate because a frame
assertion's SUBJECT is normally an existing artifact and a subject with no reach
case cannot be promoted anyway. It stops being adequate the moment a live run
produces a second reach event on the same lineage set.

**Ready-to-send prompt:**

```
Change tranche: re-nomination for promotion problems. Route through
dr-change-orchestrator.

AUTHORITY: experiments/2026-08-24-change-rung5-promotion-criteria/
PARKED.md P1, and that tranche's SPEC.md assumption A5, which states the
boundary being lifted: the reach certificate freezes its candidate subject
pool at nomination, so a subject conjectured later answers `overrun` with
`subject-not-in-environment` on two of the five criteria.

WORK: decide and implement how a promotion problem acquires a SECOND
frozen environment without editing its first. The shape the tree already
has for "reshape the question without losing the epistemic state" is
`deepreason amend`'s amendment epochs (docs/proposals/AMENDMENT_EPOCHS.md)
— check whether a promotion problem can carry an amendment-shaped second
certificate, or whether re-nomination should mint a second promotion
problem whose id encodes the certificate. Do NOT edit a registered
certificate: it is content-addressed and the criteria are bound to its
digest by their own commitment ids.

GATE PROVES: a rival conjectured after nomination is adjudicated rather
than answered `overrun`; the FIRST certificate's verdicts are byte-
unchanged; and the `subject-not-in-environment` overrun still fires for a
subject in neither environment (the honest answer must survive).

SIZE: unestimated — the first step is the design decision, so this is a
DESIGN-AND-STOP unless the operator says otherwise.
```

---

## P2 — Rider 5 clause (4) names four frozen artifacts; this rung shipped one

**What.** The external implementation advice (REQUEST.md Amendment 8, Rider 5
clause 4) says programs consume frozen fence-stamped input artifacts —
`ReachCertificate`, `IncumbentWoundLedger`, `ScopeEnvironment`, `CaptureWindow`.
Rung 5 ships ONE artifact carrying the wound ledger and scope environment as
SECTIONS, and no capture window at all. The deviation is recorded as SPEC.md A4
and was taken for the size budget, which the tranche then overran anyway — so
the reason no longer holds even though the decision may still be right. Capture
integration is Rung 8's, so the fourth artifact is scheduled regardless.

**Ready-to-send prompt:**

```
Question, not a change tranche: should the promotion criteria's frozen
input stay ONE artifact or become the four Rider 5 clause (4) names?

Read experiments/2026-08-24-change-rung5-promotion-criteria/SPEC.md A4 and
src/deepreason/calculus/claims.py::ReachCertificateV1. The single
certificate carries reach_records, problems, commitments, subjects,
consulted and truncated; splitting it would give each section its own
content address and its own attack surface — "your wound ledger is wrong"
would land separately from "your scope environment is wrong" — at the cost
of four registrations per nomination and four digests in every criterion
spec. Answer A (keep one) or B (split), and if B, whether it lands before
or with Rung 8's capture integration.
```

---

## P3 — `load-bearing` demarcation is never written, so no promotion candidate can clear criterion 1

**What.** `FrozenSubjectV1.demarcation` has three values and nomination only
ever writes two: `declared-only` (the typed abstention) or `no-attack-surface`
(a settled failure). `load-bearing` is reserved for a sweep that holds a
variator seat, and no such sweep exists. Consequence, stated plainly:
`promotion_subject_demarcation` today returns `pass` for NO candidate — it is
`fail` or `overrun`. That is honest (the run genuinely has not taken the second
reading) and it is not a defect of this rung, whose §12.2 obligation was to
implement the clause. But it means the criterion cannot yet CONFIRM anything,
only refuse, and a reader could mistake a run with no promotions for a run with
no promotable subjects.

**Ready-to-send prompt:**

```
Change tranche: take the §12.2 `load` reading for promotion subjects.
Route through dr-change-orchestrator.

AUTHORITY: experiments/2026-08-24-change-rung5-promotion-criteria/
PARKED.md P3. `calculus/nomination.py::_demarcation` writes only
`declared-only` or `no-attack-surface`; the `load-bearing` value exists and
nothing produces it, so `promotion_subject_demarcation` can refuse and
abstain but never confirm.

WORK: give nomination (or a sweep beside it) the variator seat, taking
Rung 2's cost answer unchanged — cache per subject, ONE sample for the life
of the run, and the typed abstention when the seat is absent, which is
`premises.py::premise_rent_sweep`'s exact shape and is already what the
frozen `declared-only` value means.

GATE PROVES: a subject whose role variants draw a different verdict vector
freezes as `load-bearing` and its candidate PASSES criterion 1; a solo run
with no variator still completes the whole promotion path (L-3) and still
records the abstention rather than a pass.
```

---

## P4 — `Verified-at:` stamps on eight map documents are stale from earlier tranches

**What.** `python tools/docs_verify.py --stale` lists eight documents whose
owned files moved under commits that pre-date this branch:
`CON-criticism-source`, `CON-run-identity`, `CON-seats`, `INV-signal-contract`,
`SEAM-llm-x-scheduler`, `SEAM-llm-x-workflow`, `SUB-llm`, `SUB-verification`.
This tranche cleared the seven it made stale and deliberately did NOT touch
these: advancing a stamp over checks read for another tranche's sake is the
false stamp the map's own rule forbids.

**Ready-to-send prompt:**

```
The operator asks what is out of date: run dr-audit-orchestrator's
docs-drift dimension, scoped to the eight documents `python
tools/docs_verify.py --stale` lists. For each, re-read the document
against its owned files, re-run its checks, and either advance
`Verified-at:` or record what actually drifted. Read-only: findings
become parked prompts, no fixes.
```

---

**Recommended next: P3.** It is the only one of the four that changes what a
live run can currently DO — without it the promotion path can refuse candidates
and never confirm one, so a first live promotion is not reachable. P1 and P2 are
design questions with no live consequence yet, and P4 is housekeeping.
