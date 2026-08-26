# SPEC — W7, the RUN ANATOMY PROGRAM synthesis

Authority: `REQUEST.md` R1–R25. Every item below cites the requirement it
discharges. Where `REQUEST.md` is silent, the smallest reasonable reading
is taken and RECORDED as an assumption (A-numbers).

## Map preflight (resolved before designing, per CLAUDE.md)

| id | why it is in scope |
|---|---|
| `DR-INDEX` | routing; read first |
| `DR-INV-frozen-surfaces` | read before designing. **Not applicable by construction**: this tranche writes no byte under `src/`, `tests/` or `docs/map/`. The gate is `git diff --stat origin/main`. |
| `DR-SCHEMA` | read to establish that a document OUTSIDE `docs/map/` is not a map document and owes no `check:` lines (R22) |

No map document is written or modified, so nothing here may advance a
`Verified-at:` stamp. No seam is crossed: the tranche reads committed
measurement artifacts and writes prose.

## The deliverable

ONE new file: `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` (R13). Four
sections plus a header and an appendix. Nothing else is created,
modified, or deleted outside this tranche directory (R2, R23).

## Recorded assumptions

**A1 — W2 and W3 are read from their own branches, and the document says
so (R9).** `REQUEST.md` R9 names all six W directories as inputs. Only
W1, W4, W5 and W6 are on `origin/main` at `be9bcff54`, inside
`experiments/2026-08-26-run-anatomy-program/`. W2 and W3 were written on
their own branches and are not merged:

    W2  origin/claude/criticism-anatomy-w2-1z2029
        experiments/2026-08-26-run-anatomy-w2-criticism/
    W3  origin/claude/run-anatomy-w3-census-p5pgmb
        experiments/2026-08-26-run-anatomy-w3-evidence-scratch/

Smallest reasonable reading: read them from those branches, cite them
with the branch named at every citation site, and state the fact in the
document's header so a reader who checks a citation against `main` alone
is not misled. NOT assumed: that they will be merged. NOT done: merging
them, which is outside this tranche's one-document scope.

**A2 — "nine organ reports" is read as the program's ten DIMENSIONS
delivered across six windows plus the three prior tranches the request
names as inputs (R7, R9, R10).** `PROGRAM.md` registers ten dimensions
(D1–D10) and three concurrent windows for round 1; six W windows exist.
The organ table's row list is taken verbatim from R14 and not
re-derived, so the count is not load-bearing on this reading.

**A3 — the judge-road row is split into two rows (R14).** R14 names
"judge road + guards" as one item. The record gives the two opposite
verdicts — the road was never entered in 53 of 54 roots, and the guards,
on the one root that ran them, turned away 114 of 122 convened trials.
A single verdict would have to suppress one of the two numbers, and R14
forbids a verdict without its number. The two rows are adjacent and
labelled, and §1 states the split and its reason in one line. Everything
R14 names is covered; nothing is added.

**A4 — the two-call protocol appears in WORKS and in UNEXERCISED, split
by what each list is about (R17, R18).** R18 places it in WORKS. R17
requires the unexercised list to be honest. The record gives both: the
protocol is shipped and offline-proven (22 regressions, full gate 3 857
passed / 0 failed), its typed decline path fired 96 times live, and no
committed run has ever taken a split leg (0 of 3 155 attempts). It is
therefore listed in WORKS for the part the record proves and in
UNEXERCISED for the part that has never fired, with a sentence at each
site saying this is one mechanism seen from two sides, not two items.

**A5 — path corrections, applied silently in citations and noted here.**
R10 writes `experiments/2026-08-25-constructive-frontier`; the path the
program doc names is
`experiments/2026-08-25-change-constructive-frontier`. R11 writes
`docs/RESEARCH_STRUCTURED_OUTPUT_COERCION`; the file is
`docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md`, and likewise
`RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` and
`RESEARCH_SHAPE_CRITIQUE_2026-08-22.md`. R10 pre-authorises this
("or wherever the program doc names it — follow its pointers").

**A6 — "cites by file and line/table" is discharged by file plus the
cited artifact's own section, table or finding label (R8).** The inputs
label their own claims (`W1 RESULTS.md §3`, `W2 TABLES.md §3b`, `W3
RESULTS.md F1`, `W4 FUNNEL.md`, `W5 STALENESS.md`, `W6 TABLES.md T12`).
Those labels are stable under edit where a line number is not, so they
are the citation unit. Where a claim has no label, the file and the JSON
key are given.

## Acceptance checks, per requirement

| R | Acceptance check | How it is proven |
|---|---|---|
| R1 | `git remote -v` names `AHepi/DeepReason` | pasted in VALIDATION.md |
| R2 | exactly one file created outside the tranche dir, under `docs/` | `git diff --stat origin/main` |
| R3 | `git diff --name-only origin/main \| grep -E '^(src\|tests)/'` is empty | pasted output |
| R4 | `git merge-base --is-ancestor be9bcff54 HEAD` exits 0; `deepreason` importable; `pytest`, `xdist`, `jsonschema` importable | pasted output |
| R5 | CLAUDE.md read; both skills loaded this session | stated in VALIDATION.md |
| R6 | document opens worry-first; every term of art glossed in-line at first use; exactly ONE analogy, in the closing | hand-audited; the analogy count is grepped |
| R7 | every named input read in full before drafting | the read log in VALIDATION.md |
| R8 | every numeric claim in the document carries a citation to a named input | citation audit: count of numeric claims vs count of citations |
| R9–R12 | each named input appears at least once as a citation | grep per input path |
| R13 | file exists at `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` with exactly four `## ` sections plus header and appendix | grep of headings |
| R14 | one row per named subsystem; verdict drawn from the five-value vocabulary; a number and a citation in every row | table audit; **no row with an empty number cell** |
| R15 | five causes, in the order R15 gives, one narrative paragraph each, each naming its table | heading audit |
| R16 | every cause carries an explicit HARNESS-DESIGN / MODEL-BEHAVIOR / WIRING-NEVER-BUILT attribution | grep of the three labels |
| R17 | three lists exist; the refuted list distinguishes as-wired from in-principle explicitly | heading audit |
| R18 | record machinery, scratch, guards, two-call protocol all present in WORKS with numbers | grep |
| R19 | three roads (a)(b)(c) as R19 names them; NO recommendation anywhere in §4 | grep for "recommend" in §4 returns only the explicit statement that none is made |
| R20 | each road carries agent cost, token cost, and its success evidence | per-road subheading audit |
| R21 | one line per parked prompt from W1–W6 in the appendix | count against the source PARKED.md files |
| R22 | `python tools/docs_verify.py` full run, 0 failed; the document contains no `check:` line and its header says why | pasted output; `grep -c '^check:'` = 0 |
| R23 | `git diff --stat origin/main` shows exactly one new file under `docs/` plus the tranche directory | pasted output |
| R24 | a commit and a push at each phase boundary | `git log --oneline` |
| R25 | DELIVERY.md closes with the document's own opening sentence, quoted | hand-checked against the document |

## Budget

One new document, target 400–700 lines. Tranche artifacts: REQUEST,
SPEC, CHECKLIST, VALIDATION, DELIVERY, PARKED. Zero lines under `src/`,
`tests/` or `docs/map/`. No test-suite run is owed (no code changed);
`docs_verify` is the gate R22 names.

## Stop conditions

- A requirement contradicts the record → report the contradiction, do
  not pick a side.
- The synthesis would need a number no input carries → the number is not
  written; the absence is stated (R8 forbids re-derivation).
- Any temptation to fix a finding → PARKED.md, never implemented (the
  program fixes nothing in any window or round).
