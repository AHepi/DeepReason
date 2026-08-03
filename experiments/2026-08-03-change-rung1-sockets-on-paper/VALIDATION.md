# Validation for: rung 1 — sockets on paper, and the parked R8 job
(Second, fresh pass — the first VALIDATION.md, commit `0b133f25`, returned
FAIL on one gap: `CON-schools.md`'s header. That gap is fixed, commits
`ebf8728d`/`fc347df1`/`c4806e74`. This document supersedes the first
entirely — every check below was re-run from scratch, not copied forward.)

## Acceptance checks

S1: `grep -q "The socket contract" docs/map/CON-schools.md` -> exit 0 :
PASS.

S2: `grep -q "The socket contract" docs/map/CON-authority.md` -> exit 0 :
PASS.

S3/S4/S5: `python tools/docs_verify.py --links` -> `0 dangling
reference(s), 49 document(s)` : PASS. `grep -q "CON-conjecture-source.md"
docs/map/INDEX.md`, `grep -q "CON-criticism-source.md" docs/map/INDEX.md`,
`grep -q "CON-scheduler-ranking.md" docs/map/INDEX.md` -> all exit 0.

S6: `for f in docs/map/SUB-*.md; do grep -q "^## Seams" "$f" || exit 1;
done` -> exit 0, all 16 files, re-run fresh this pass.

S7: `grep -q "Triage: is a change isolated" docs/map/SCHEMA.md` -> exit 0.
`python tools/docs_verify.py --self-test` -> `docs_verify --self-test: ok`
: PASS.

S8 (R4): `git diff --stat 9a319c10..HEAD -- src/` -> empty, exit 0 : PASS.

S9 (R5) — all three commands re-run fresh, this pass:
```
python tools/docs_verify.py
docs_verify [full]: 49 documents, 793 checks, 4 workers
docs_verify: 0 failed
```
```
python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)
```
```
python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 49 document(s)
```
: PASS on all three.

**The specific FAIL condition from the first pass, re-checked directly:**
`grep -n "^Seams:" docs/map/CON-schools.md` ->
`Seams: DR-SEAM-schools-x-scratch, DR-SEAM-manifest-x-schools`. Fixed.

**The Sides:-vs-Seams: cross-reference audit that caught the first FAIL,
re-run independently this pass** (not reused from the execution-time
script — retyped fresh against the current tree): walked all 20
`SEAM-*.md` documents' `Sides:` lines against all 25 `SUB-*.md`/`CON-*.md`
documents' `Seams:` headers. Result: `Zero mismatches — every seam
document is cited by both its Sides:.` (20 seam docs, 25 SUB-/CON- docs
checked — 16 SUB + 9 CON, the 6 pre-existing plus the 3 this tranche
created).

## Full gate

Not re-run a third time this session: `git diff --stat 88e209fb..HEAD --
src/` (the commit whose pytest run is the last one on record, from
CHECKLIST.md step 23) is empty, exit 0 — no `src/` file has changed since
that run, so `3290 passed, 7 skipped in 573.44s` (step 23's pasted output)
still describes the current tree exactly. Re-running would spend ~10
minutes re-proving a number that cannot have moved. PASS by citation.

## Record-behavior preservation

n/a — no reader, guard, or authority rule under `src/` changed; no
committed run root was opened.

## Frozen-surface diff

```
git diff --stat 9a319c10..HEAD -- \
  src/deepreason/capabilities/state.py src/deepreason/harness.py \
  src/deepreason/invariants.py src/deepreason/run_manifest.py \
  src/deepreason/qualification.py
```
Empty output, re-confirmed this pass. PASS.

## Map

`docs_verify`: 49 documents, 793 checks, 0 failed : PASS
`docs_verify --audit`: 0 findings : PASS
`docs_verify --links`: 0 dangling, 49 documents : PASS
`docs_verify --coverage`: `6 seam(s) swept, 14 without a Sweep: header, 0
finding(s)` : PASS (0 findings is the gate; unchanged from the first
pass — this tranche edited no `SEAM-*.md` document body, only cited them
from the `SUB-`/`CON-` side, so the ratchet is not triggered).

`docs_verify --stale`: same 4 documents as the first pass, judged again:
- `INV-frozen-surfaces.md`, `SEAM-harness-x-verification.md`,
  `SUB-verification.md` — all cite commit `2456da55`
  (2026-08-03T01:33:27Z), which predates this tranche's base (`9a319c10`,
  2026-08-03T05:22:58Z) by ~4 hours. Dismissed: pre-existing, untouched by
  this tranche.
- `REC-change-a-seam.md` — now 34 commits (one more than the first pass,
  since a further tranche commit landed), including several of this
  tranche's own. Its `Owns:` header is `docs/map/` — the whole
  directory — so any commit to any map document trivially counts here;
  this is a structural artifact of a self-referential `Owns:`
  declaration, not a signal that its own prose became less accurate.
  This tranche never edited `REC-change-a-seam.md`'s content. Dismissed,
  same reasoning as the first pass.

New checks added by this change: unchanged from the first pass —
`CON-schools.md` (+4), `CON-authority.md` (+8), `CON-conjecture-source.md`
(7, new), `CON-criticism-source.md` (9, new), `CON-scheduler-ranking.md`
(6, new), `SCHEMA.md` (+1). 35 new checks total, all individually verified
standalone during execution and again by the fresh full/`--audit`/`--links`
runs above. (The header-only fix in steps 25-26 added no new checks — a
`Seams:`/`Seams-undocumented:` header line carries no `check:` of its
own; its accuracy is what the Sides:-vs-Seams: audit above verifies.)

## Requirement sweep

R1: demonstrated by S1-S5 — five socket documents, each with a verified
"socket contract" section.

R2: demonstrated by S6 (all 16 `SUB-*.md` files) **and, this pass, the
gap the first VALIDATION.md found is closed**: `CON-schools.md`'s header
now correctly cites `DR-SEAM-manifest-x-schools`, confirmed by the
independent Sides:-vs-Seams: re-audit above (zero mismatches across
every seam document, both sides, not just the one previously flagged).

R3: demonstrated by S7 (the triage rule, `--self-test` clean).

R4: demonstrated by S8 (empty `src/` diff, re-confirmed fresh).

R5: demonstrated by S9 (all three `docs_verify` modes, re-run fresh this
pass).

## Assumptions carried

A1: `CON-schools.md`/`CON-authority.md` extended in place rather than
duplicated.
A2: conjecture source, criticism source, and scheduler ranking each get
one new, focused `CON-` document.
A3: "with checks" means SCHEMA.md's ordinary per-claim rule.
A4: R2's "SUB documents" read as literally every `SUB-*.md` file on disk
(16), including three not yet in `INDEX.md`'s Subsystems table.
A5: tranche stayed as ONE tranche directory, many small committed steps.

## Verdict: PASS

Every acceptance check (S1-S9), both process constraints (R4, R5), all
five requirements (R1-R5), the frozen-surface diff, and the full map gate
in all four modes (`docs_verify`, `--audit`, `--links`, `--coverage`) are
green on a fresh, independent re-run — including a second, from-scratch
Sides:-vs-Seams: cross-reference audit specifically aimed at re-catching
the class of error the first validation pass found. `--stale`'s four
entries are judged and dismissed with reasons, none newly introduced by
this tranche. Route: `dr-deliver-change`.
