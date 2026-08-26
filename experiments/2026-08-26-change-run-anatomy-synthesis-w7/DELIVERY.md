# DELIVERY — W7, the RUN ANATOMY PROGRAM synthesis

Branch `claude/run-anatomy-synthesis-w7-fxpifz`, base `origin/main` at
`be9bcff54`. `VALIDATION.md` verdict: **PASS**, 25 of 25.

## What was delivered

One document: **`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md`**, 811 lines,
four sections and an appendix. Nothing else outside this tranche
directory. No byte under `src/`, `tests/` or `docs/map/`.

| gate | result |
|---|---|
| `python tools/docs_verify.py` | 64 documents, **1 073 checks, 0 failed** |
| `git diff --name-only origin/main \| grep -E '^(src\|tests)/'` | empty |
| `git diff --stat origin/main` | one new file under `docs/`, plus this tranche's directory |
| `grep -c '^check:'` on the new document | 0 — and the header says why |
| pytest | not owed; no code changed |

## Reconciliation, requirement by requirement

| R | The operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "TARGET REPOSITORY: AHepi/DeepReason — verify before anything else" | done | `git remote -v` → `origin https://github.com/AHepi/DeepReason`, checked before any other action |
| R2 | "this tranche WRITES one document and nothing else" | done | diff gate: one file under `docs/` |
| R3 | "READ-ONLY on src/ and tests/" | done | `git diff --name-only origin/main` names no such path |
| R4 | branch from main, `be9bcff54` an ancestor, editable install + test deps | done | `be9bcff54 ancestor: OK`; `deepreason`, `pytest`, `xdist`, `jsonschema` all import |
| R5 | "Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator" | done | both loaded before the first operator-facing message; `dr-change-orchestrator` loaded as the routing family |
| R6 | "worry-first, every technical term glossed inline, one closing analogy" | done | opening sentence is the verdict; a glossary paragraph precedes §1; exactly one analogy, in the closing paragraph — a second image in the draft's opening was removed to keep the count at one |
| R7 | "read IN FULL before writing a word" | done | `VALIDATION.md` read log, 15 rows |
| R8 | "no new measurement, no re-derivation; every claim cites one of these" | done | no instrument was run against any root; every figure quoted with its source artifact and that artifact's own label |
| R9 | PROGRAM.md and all six W directories | done, **with assumption A1** | W1/W4/W5/W6 from `main`; W2 and W3 from their own branches, named at every citation and in the header |
| R10 | P-R1 RESULTS and the strengthened P5; the P-C1 arm comparison | done | §3.1 item 3 refutes the strengthened P5 outright; §2 quotes the P-C1 margin |
| R11 | the three RESEARCH_ notes | done | coercion at §2.5, Q4 at §3.1 item 2 and road (b), Q5 at §2.3 and road (b), shape-critique at §2.6 |
| R12 | LESSONS_LEARNED, "honest ledgers outlive optimistic summaries" | done | §1.3 quoted in the header as the rule the document is written under, and named again in road (a) |
| R13 | four sections, nothing else | done | `## 1.` `## 2.` `## 3.` `## 4.` plus the appendix R21 requires |
| R14 | organ table, verdict + the one number + citation, no verdict without its number | done | 11 rows, no empty cell; WORKS 4, HARMFUL-AS-WIRED 3, INERT 2, PHANTOM 1, UNEXERCISED 1 |
| R15 | five causes, ordered by measured size, each tied to its table | done | 41.2 % → 24.6 % → zero coupling → 10× collinearity → invented handles, in that order |
| R16 | HARNESS-DESIGN / MODEL-BEHAVIOR / WIRING-NEVER-BUILT on each | done | three labels defined at the head of §2 and used twice each; §2.6 covers recombination, which R16 names |
| R17 | three honest lists; refuted-as-wired is not refuted-in-principle | done | §3.1 marks each entry **as wired** or **outright**; two are outright |
| R18 | record machinery, scratch, guards, two-call protocol in WORKS with numbers | done, **with assumption A4** | §3.3 items 1–4; the two-call protocol also appears in §3.2 for the half the record is silent on, with a sentence at each site saying it is one mechanism seen from two sides |
| R19 | three roads, NO recommendation made | done | §4 opens "No recommendation is made here." |
| R20 | agent cost, token cost, success evidence per road | done | three labelled paragraphs per road; road (b) also registers its failure condition in advance |
| R21 | one appendix line per W1–W6 parked prompt | done | 32 rows: W1 6, W2 5, W3 6, W4 4, W5 6, W6 5 |
| R22 | docs_verify full; no `check:` lines; the header says so | done | 1 073 checks, 0 failed; `grep -c '^check:'` → 0 |
| R23 | one new file under docs/ plus the tranche directory | done | diff gate |
| R24 | commit and push every phase boundary, with retry | done | three pushed commits: request+spec, the document, this closing set |
| R25 | close with the document's own worry-first opening sentence, quoted | done | below |

**Assumptions, both recorded in `SPEC.md` before the work and neither
silently absorbed:** A1 (W2 and W3 read from their own branches, cited
with the branch named), A3 (the judge road split into two adjacent rows,
because the record gives its entry and its guards opposite verdicts and
R14 forbids a verdict without its number), A4 (the two-call protocol in
both WORKS and UNEXERCISED, split by what each list is about). A2, A5 and
A6 are naming and citation-format decisions.

## Two things worth the operator's eye

**One correction was made during validation and is recorded, not
hidden.** The draft's trial-guard breakdown summed to 172 against 153
actual declines: it placed the 39 trials taken by formal supremacy
*inside* the 114 turned away, when those 39 leave before a trial
convenes, and it used W4's headline 62 ensemble-splits, which already
contains 19 of the 22 paraphrase-gate declines. Corrected to the
gate-by-gate figures. `VALIDATION.md` carries the arithmetic.

**The docs gate went red before it went green, for a reason that was not
this tranche's.** The first `docs_verify` run failed 3 checks in
`docs/map/CON-run-identity.md`, a document untouched here. The container's
clone was shallow (138 commits) and those three checks address commits by
hash. `git fetch --unshallow origin` took 5.3 seconds and the same run
came back 1 073 checks, 0 failed. No check was edited, skipped or
weakened. Parked as W7-P1: the gate should name a shallow clone rather
than an unknown revision.

## Parked, not fixed

- **W7-P1** — `docs_verify` reports a red gate on a shallow clone, and
  the failure text does not say so.
- **W7-P2** — W2 and W3 are not on `main`, so the synthesis's citations
  to them do not resolve there. A naive merge is wrong: both branches
  predate the W4/W5/W6 merges and their plain diffs read as deletions.

---

## The document's own opening sentence (R25)

> **Nothing in this document refutes the idea the harness was built on.**
