# Validation for: rung 1 — sockets on paper, and the parked R8 job

## Acceptance checks

S1: `grep -q "The socket contract" docs/map/CON-schools.md` -> exit 0 :
PASS. (`--ring schools` does not resolve — CON- documents verify via the
whole tool, not a pytest ring; substituted `python tools/docs_verify.py`,
see below.)

S2: `grep -q "The socket contract" docs/map/CON-authority.md` -> exit 0 :
PASS. Same `--ring` substitution as S1.

S3: `python tools/docs_verify.py --links` -> `0 dangling reference(s), 49
document(s)` : PASS. `grep -q "CON-conjecture-source.md" docs/map/INDEX.md`
-> exit 0 (the accept text's literal `DR-CON-conjecture-source` string was
never the right one to grep for — `INDEX.md`'s Concepts table lists bare
filenames; this was caught and corrected during execution, see
CHECKLIST.md step 5).

S4: same as S3, for `CON-criticism-source.md`. PASS.

S5: same as S3, for `CON-scheduler-ranking.md`. PASS.

S6: `for f in docs/map/SUB-*.md; do grep -q "^## Seams" "$f" || exit 1;
done` -> exit 0 (re-run fresh, all 16 files, this validation pass).
`python tools/docs_verify.py --links` -> 0 dangling, as above : PASS.

S7: `grep -q "Triage: is a change isolated" docs/map/SCHEMA.md` -> exit 0.
`python tools/docs_verify.py --self-test` -> `docs_verify --self-test: ok`
: PASS.

S8 (R4, scope boundary): `git diff --stat 9a319c10..HEAD -- src/` -> empty
output, exit 0 (re-run fresh at validation time, base
`9a319c10b66f39963c64a5142311c07aa8460fa6` — the parent of REQUEST.md's
first commit) : PASS.

S9 (R5, full gate) — re-run fresh at validation time, not from the
execution-time record:
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
: PASS on all three commands as literally specified by R5/S9.

## Full gate

`python -m pytest tests/ -q -n 4` (re-run at validation time is the SAME
run already pasted at CHECKLIST.md step 23, since no `src/` file changed
between step 23 and now — re-running it a second time would burn ~10
minutes to confirm a number that cannot have moved):
`3290 passed, 7 skipped in 573.44s (0:09:33)` : PASS.

## Record-behavior preservation

n/a — no reader, guard, or authority rule under `src/` changed (R4 held);
no committed run root was opened or could be affected.

## Frozen-surface diff

```
git diff --stat 9a319c10..HEAD -- \
  src/deepreason/capabilities/state.py src/deepreason/harness.py \
  src/deepreason/invariants.py src/deepreason/run_manifest.py \
  src/deepreason/qualification.py
```
Empty output. PASS — no frozen surface touched, consistent with S8.

## Map

`docs_verify`: 49 documents, 793 checks, 0 failed : PASS
`docs_verify --audit`: 0 findings : PASS
`docs_verify --links`: 0 dangling, 49 documents : PASS
`docs_verify --coverage`: `6 seam(s) swept, 14 without a Sweep: header, 0
finding(s)` : PASS (0 findings is the gate; the 14-without-header count is
advisory per SCHEMA.md's own ratchet rule — "a seam without one is
reported by `--coverage` but not failed, and MUST gain one the next time
the document is edited". This tranche edited SUB-/CON- documents' headers
and added prose ABOUT these seams; it did not edit any `SEAM-*.md`
document's own body, so the ratchet is not triggered by this tranche).

`docs_verify --stale`: 4 documents listed. Judged individually:
- `INV-frozen-surfaces.md`, `SEAM-harness-x-verification.md`,
  `SUB-verification.md` — all three cite the same commit, `2456da55`
  (2026-08-03 01:33:27 UTC), which **predates this tranche's base**
  (`9a319c10`, 2026-08-03 05:22:58 UTC) by roughly four hours. This
  staleness existed before rung 1 began and this tranche did not touch
  any of these three documents. Dismissed: pre-existing, out of scope.
- `REC-change-a-seam.md` — 33 commits listed, including several of THIS
  tranche's own (`ab5d711f`, `eefb3917`, `9ae772e6`, ...). Its own `Owns:`
  header is `docs/map/` — the whole directory — so literally any commit
  touching any map document trivially "touches its owned files" by this
  instrument's accounting; it is not a signal that `REC-change-a-seam.md`'s
  own PROSE became less accurate. This tranche did not edit
  `REC-change-a-seam.md`'s content (only cited it by reference, as SPEC.md's
  "Out of scope" explicitly says it would). Dismissed: structural artifact
  of a self-referential `Owns:` declaration, not a content-accuracy signal;
  also predates this tranche (33 commits, oldest well before `9a319c10`).

New checks added by this change: `CON-schools.md` (+4: the socket-contract
section), `CON-authority.md` (+8), `CON-conjecture-source.md` (7, new
document), `CON-criticism-source.md` (9, new document),
`CON-scheduler-ranking.md` (6, new document), `SCHEMA.md` (+1, the triage
rule's `Owns:`-overlap check). Total new checks this tranche: 35 (of the
793 in the current full run). Confirmed each was individually verified
standalone during execution (CHECKLIST.md steps 1, 3, 5, 7, 9, 19) and
again collectively by the fresh full/`--audit`/`--links` runs above.

**A real defect surfaced during THIS validation pass, not carried forward
from execution-time records:** `CON-schools.md`'s header still lists
`manifest x schools` under `Seams-undocumented:`, even though
`DR-SEAM-manifest-x-schools.md` exists (confirmed by
`ls docs/map/SEAM-manifest-x-schools.md`) and `SUB-manifest.md`'s own
header was correctly fixed to cite it during batch C (commit `10549d1e`).
The systematic `Sides:`-vs-`Seams:` audit that found this exact fix
needed (recorded in `docs/ERRATA.md` E9 and in CHECKLIST.md's "Inserted
step 10b" note) correctly IDENTIFIED this as one of eight required fixes,
but the actual edit to `CON-schools.md`'s header was never made — only
`SUB-manifest.md`'s side of the same pair was. This is a real,
verifiable gap:

```
grep -n "^Seams:" docs/map/CON-schools.md
Seams: DR-SEAM-schools-x-scratch
grep -n "manifest x schools" docs/map/CON-schools.md
Seams-undocumented: adjudication x schools, llm x schools, manifest x schools, rules x schools, scheduler x schools, schools x workflow
```

Per `dr-validate-change`'s own procedure ("No file other than
VALIDATION.md ... modified. A map document that needs updating is a FAIL
routed back to `dr-execute-step`, not something validation fixes in
passing"), this is NOT corrected here. It is a genuine, if narrow, defect
in R2's completeness (E9's audit was supposed to fix exactly this pair on
both sides) and blocks a clean PASS.

## Requirement sweep

R1: demonstrated by S1-S5 (five socket documents, all with a "socket
contract" section carrying real, individually-verified checks).

R2: demonstrated by S6 (all 16 `SUB-*.md` files carry a `## Seams`
section) **WITH ONE KNOWN GAP**: `CON-schools.md` (a `CON-`, not `SUB-`,
document, so technically outside R2's literal "SUB documents" wording —
but the SAME E9 audit that R2's own execution triggered identified this
fix as necessary and it was missed). Recorded as the FAIL detail above
rather than silently accepted.

R3: demonstrated by S7 (the triage rule, with a real, verified
`Owns:`-overlap check).

R4: demonstrated by S8 (empty `src/` diff across the whole tranche,
re-confirmed fresh at validation time).

R5: demonstrated by S9 (all three `docs_verify` modes, re-run fresh at
validation time, not reused from execution-time output).

## Assumptions carried

A1: `CON-schools.md`/`CON-authority.md` extended in place rather than
duplicated (schools/authority already had a document; extension resolves
the ambiguity without operator input).
A2: conjecture source, criticism source, and scheduler ranking each get
one new, focused `CON-` document rather than subsections in the broader
`SUB-rules.md`/`SUB-scheduler.md`.
A3: "with checks" means SCHEMA.md's ordinary per-claim rule (never
actually ambiguous).
A4: R2's "SUB documents" read as literally every `SUB-*.md` file on disk
(16), including three not yet in `INDEX.md`'s Subsystems table.
A5: tranche stayed as ONE tranche directory, many small committed steps,
rather than splitting rung 1 into sub-tranches.

## Verdict: FAIL

FAIL detail: `CON-schools.md`'s `Seams:`/`Seams-undocumented:` header
still lists `manifest x schools` as undocumented despite
`DR-SEAM-manifest-x-schools.md` existing — one of the eight E9 header
fixes this tranche's own audit identified was never applied on this side
of the pair (only `SUB-manifest.md`'s side was fixed, in commit
`10549d1e`). Suspected step: the CHECKLIST step 11 (batch A) execution
record, where `CON-schools.md` was NOT among the four files that batch
covered, and no later step returned to it — the fix was scoped to "each
affected file's own S6 batch" per the step-10b note, but `CON-schools.md`
is a `CON-` document outside the four `SUB-*.md` batches, so it fell
through. Route: back to `dr-plan-steps` (a one-line addition:
`docs/map/CON-schools.md`'s header, moving `DR-SEAM-manifest-x-schools`
from `Seams-undocumented:` to `Seams:`), then re-validate.
