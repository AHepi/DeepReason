# Delivered: judge-evidence review — read-only archaeology over committed runs

Branch: `claude/judge-evidence-archaeology-bei2qt` @ `4575df852` (pushed,
tree clean)

## What changed

Nothing under `src/` — this was a read-only review tranche, and the
tripwire diff (`git diff origin/main...HEAD -- src/`) is empty, confirmed
twice (checklist step 11, VALIDATION.md S10). What was delivered is a
review document, `REVIEW.md` (~450 lines, 8 sections), plus `RESULTS.md`'s
honest-ledger entry, in
`experiments/2026-08-09-change-judge-evidence-review/`.

The review answers the operator's question — what the committed record
proves about LLM-judge discrimination — by first separating two actors the
record itself conflates under "judge" (the argumentative CRITIC that
raises objections, and the JUDGE that rules inside a trial), then pulling
every numeric claim from 17 results files, 2 tranches, 3 stress-triplet
roots, and `EXPERIMENT_PROGRAM_2026-07.md`'s own predictions, each cited
by exact path (and line, where the source is code or a doc rather than
JSON). It scores three separate readings of the operator's hypothesis
(judges err, judges don't discriminate, judges over-convict) and closes
with a design-consequence section enumerating five non-judge or
judge-consistency mechanisms already in the codebase, what each can and
cannot adjudicate, and four unresolved decisions for the operator.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "your deliverable is a review document" | done | REVIEW.md, VALIDATION S1 |
| R2 | "READ-ONLY... No code, no live calls, no new runs" | done | tripwire diff 0 twice (checklist step 11, VALIDATION S10); frozen-surface diff empty |
| R3 | "Route through dr-change-orchestrator from dr-capture-request" | done | commit log, REQUEST.md→SPEC.md→CHECKLIST.md→12 steps→VALIDATION.md→this document |
| R4 | "HYPOTHESIS to verify, not a conclusion to decorate" | done | REVIEW.md §7 verdicts are SUPPORTED/MIXED/MIXED, not uniform |
| R5a | sweep: audit machinery + `experiments/results/` | done | REVIEW.md §2, VALIDATION S2 |
| R5b | sweep: trial-protocol experiments | done | REVIEW.md §3, VALIDATION S3 |
| R5c | sweep: adjudication-blindness tranche (2026-08-01) | done | REVIEW.md §4, VALIDATION S4 |
| R5d | sweep: stress-triplet + lambda/experiment-module runs | done | REVIEW.md §5, VALIDATION S5 |
| R5e | sweep: `EXPERIMENT_PROGRAM_2026-07.md`'s judge items | done | REVIEW.md §6, VALIDATION S6 |
| R6 | "the root/file pointer and the number, pasted" | done | every numeric claim in REVIEW.md §2-§8 cites a path or path:line |
| R7 | three-way scoring, scored separately | done | REVIEW.md §7 (7a/7b/7c), VALIDATION S7 |
| R8 | design-consequence section, priced, recommended | done-with-assumption A3 | REVIEW.md §8 (5 mechanisms), VALIDATION S8 |
| R9 | "REVIEW.md in the tranche + RESULTS.md honest ledger" | done | both files present, VALIDATION S1/S9 |
| R10 | "deliver through dr-validate-change/dr-deliver-change" | done | VALIDATION.md (PASS), this document |
| R11 | "full gate once at the boundary... tripwire diff pasted empty" | done | VALIDATION.md "Full gate" section — run once, 3433 passed/2 failed (both proven pre-existing)/7 skipped; tripwire pasted empty |
| R12 | "Commit and push each phase boundary" | done | 12 commits, one per phase/step boundary, all pushed |
| R13 | "Stop when delivered" | done | this document is that stop |

## Assumptions the operator may override

A1 (Q1): "long since redundant runs" read as the sweep's SUBJECT, not a
retirement instruction — nothing was retired, renamed, or modified; a
retirement candidate would be a separate future tranche.
A2 (Q2): "the committed record" read as git-tracked content only — every
REVIEW.md citation resolves via `git ls-files`/`git log` on this branch.
A3 (Q3): "priced" in REVIEW.md §8 read as agent/implementation effort
(near-zero/zero for already-built mechanisms), not a dollar or token
figure.

## Map delta

No map change. This tranche added no `src/` behavior and touched no
`docs/map/` document — `docs_verify --links`/`--audit`/`--coverage` all
report 0 findings, unaffected by this tranche (VALIDATION.md "Map"
section). Three pre-existing `docs_verify` failures at
`CON-run-identity.md:195,197,199` were found during validation and are
environment-caused (shallow clone), not this tranche's — parked as P2,
not fixed here.

## Parked (not done, not promised)

**P1 — `test_census_totals_internally_consistent` fails deterministically,
independent of this tranche.** `tests/test_bronze_report.py`'s census
consistency assertion fails (`159 == 165`) on `origin/main` unchanged;
proven pre-existing by empty diff on every file it depends on.
Ready-to-send prompt in `PARKED.md` P1 — routes to
`deepreason-orchestrator`.

**P2 — three `docs_verify` checks in `CON-run-identity.md` fail under this
container's shallow git clone.** Each references a historical commit hash
outside the shallow fetch depth (`git rev-parse --is-shallow-repository`
→ `true`); proven environment-caused, not tranche-caused, by empty diff on
the document itself. Ready-to-send prompt in `PARKED.md` P2 — routes to
`deepreason-orchestrator` or a `docs/map/SCHEMA.md` documentation note.

**Recommended next: P2.** It is cheaper to resolve (either document the
shallow-clone caveat at session preflight, or add a depth guard to the
checks) and it currently makes `python tools/docs_verify.py`'s plain
invocation report FAIL in every fresh container — a false "something's
broken" signal at the start of every session until it's addressed. P1 is
a real but narrower discrepancy inside one archived bronze-run census and
does not block anything else in the gate.
