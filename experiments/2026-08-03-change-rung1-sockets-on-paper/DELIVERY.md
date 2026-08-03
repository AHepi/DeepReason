# Delivered: rung 1 — sockets on paper, and the parked R8 job
Branch: `claude/delivery-rungs-handover-m22sdy` @ `8785ed44` (pushed, tree
clean).

## What changed

Five candidate "sockets" from `docs/HANDOVER_2026-08-03.md`'s
modularisation ladder now each have a map document stating what they
promise the rest of the system, what they are handed, and what they must
never do — every claim backed by a real, individually-verified check.
`docs/map/CON-schools.md` and `docs/map/CON-authority.md` were extended in
place (they already existed); `docs/map/CON-conjecture-source.md`,
`docs/map/CON-criticism-source.md`, and `docs/map/CON-scheduler-ranking.md`
are new. Separately, all 16 `docs/map/SUB-*.md` documents now carry a
`## Seams` section that turns their `Seams:`/`Seams-undocumented:` header
into a reader-facing table — documented seams glossed from the seam
document's own agreement, undocumented pairs either confirmed real
(several straight from each package's own existing checks, e.g. "llm/
never imports harness/scheduler/verification"), confirmed deliberately
absent, or honestly marked "not yet analyzed." `docs/map/SCHEMA.md` gained
a mechanical triage rule — seam-document membership or multi-document
`Owns:` overlap means a change is seam-guided and must follow
`REC-change-a-seam.md`; otherwise it's isolated. No `src/` file changed.

This tranche also found and fixed a real, pre-existing map defect while
doing R2's work: `INDEX.md`'s seam matrix listed seven real seam documents
as "not yet written," and eight `Seams:` header citations were missing
across six files — none of it caused by this tranche, all of it recorded
as `docs/ERRATA.md` E9. And it found two defects in its OWN work before
delivery: roughly 30 checks across the five socket documents were
written as indented markdown-bullet continuations, which
`docs_verify.py`'s parser (deliberately anchored to column 0) never
registered at all — caught by `--audit` ("no checks — every claim in it
is unverifiable") and fixed by converting to the codebase's own
established check-placement convention. And a first validation pass
(`VALIDATION.md`, since superseded) caught that one of the eight E9 header
fixes — `CON-schools.md`'s side of `manifest x schools` — had been missed
during execution; a narrow re-plan (steps 25-28) fixed it and a second,
independent validation pass confirmed zero remaining gaps.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "for each candidate socket ... one map document ... stating what it promises ... what it is handed ... what it must never do, with checks" | done-with-assumption A1, A2 | commits `01898d05`, `9ae772e6`, `445ca295`, `d2660928`, `41de680b`; VALIDATION.md S1-S5 (second pass) |
| R2 | "SUB documents surface their Seams:/Seams-undocumented: in prose" | done-with-assumption A4 | commits `38e7978d`, `06c4c1c6`, `10549d1e`, `d057f306` (16 files), `ebf8728d` (the one header fix the first validation pass caught missing); VALIDATION.md S6, second pass |
| R3 | "SCHEMA.md (or the SUB template) gains the isolated-vs-seam triage rule" | done | commit `eefb3917`; VALIDATION.md S7 |
| R4 | "In scope: docs/map/ only. NOT in scope: any src/ change" | done | `git diff --stat 9a319c10..HEAD -- src/` empty, both validation passes |
| R5 | "Accept: docs_verify 0 failed; --audit 0; --links 0 dangling; every new claim carries a check that can fail" | done | VALIDATION.md (second pass): 793 checks/0 failed, --audit 0 findings, --links 0 dangling, 49 documents |

## Assumptions the operator may override

A1: `CON-schools.md`/`CON-authority.md` were EXTENDED, not duplicated —
a second document for an already-covered concept would violate both R1's
literal "one map document" and SCHEMA.md's own anti-duplication design.

A2: conjecture source, criticism source, and scheduler ranking each got a
NEW, narrowly-scoped `CON-` document rather than subsections in the much
broader `SUB-rules.md`/`SUB-scheduler.md`, since neither socket had a
document at its own grain and each reaches beyond one package's directory
(matching the `CON-` grammar).

A3: "with checks" was read as SCHEMA.md's ordinary per-claim check rule
— this was never actually an open question.

A4: R2's "SUB documents" was read as literally every `SUB-*.md` file on
disk (16), including three (`amendment`/`application`/`periphery`) not
yet listed in `INDEX.md`'s Subsystems table.

A5: this stayed ONE tranche directory with many small, individually
committed and pushed steps (28 of them, plus a validation-driven re-plan),
rather than splitting rung 1 into separate sub-tranches. The operator may
prefer an actual split for future rungs — see budget note in SPEC.md.

## Map delta

**Changed:** `docs/map/INDEX.md` (seven stale matrix rows fixed, three
new Concepts-table rows), `docs/map/CON-schools.md`, `docs/map/CON-authority.md`,
`docs/map/SCHEMA.md`, all 16 `docs/map/SUB-*.md` files, `docs/ERRATA.md`
(E9).
**Created:** `docs/map/CON-conjecture-source.md`,
`docs/map/CON-criticism-source.md`, `docs/map/CON-scheduler-ranking.md`.
**New checks:** 35 (verified individually and by two independent full
`docs_verify` runs, 793 checks total in the final tree, 0 failed).
**Left stale, with reason (from `docs_verify --stale`):**
`INV-frozen-surfaces.md`, `SEAM-harness-x-verification.md`,
`SUB-verification.md` — all three cite one commit (`2456da55`) that
predates this tranche by roughly four hours; none of the three was
touched here. `REC-change-a-seam.md` — its `Owns:` header is the whole
`docs/map/` directory, so any map commit trivially "touches" it; this is
a structural artifact of that declaration, not a sign its own prose is
wrong, and this tranche never edited its content.

## Parked (not done, not promised)

See `PARKED.md` in full. Summary: rungs 2-7 of the modularisation ladder
(next tranche, when the operator wants to proceed); the `INDEX.md`
Subsystems-table gap for `amendment`/`application`/`periphery`; roughly 30
`Seams-undocumented` pairs across the 16 `SUB-*.md` files marked "not yet
analyzed" rather than resolved (R2 asked for honest naming, not
resolution); 14 of 20 seam documents with no `Sweep:` header (advisory,
not ratcheted by this tranche); writing the seam documents themselves for
any undocumented-but-real pair; `bridge × ontology`, the one INDEX.md row
this tranche's own E9 fix correctly left as "not yet written" because it
actually is.
