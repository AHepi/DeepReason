# VALIDATION — W7

Every acceptance check in `SPEC.md`, with its pasted proof. Verdict at
the foot. Validation only: nothing was patched to reach it.

## Verdict: **PASS**

25 of 25 requirements discharged. No row is unproven, and no assertion
was weakened to reach green.

---

## The gates

### `docs_verify` full (R22)

    $ python tools/docs_verify.py
    docs_verify [full]: 64 documents, 1073 checks, 4 workers
    docs_verify: 0 failed

**One thing happened on the way to that, and it is recorded rather than
quietly fixed.** The first run reported **3 failed**, all three in
`docs/map/CON-run-identity.md`, a document this tranche does not touch:

    FAIL CON-run-identity.md:202: git log -1 --format=%s 1637e808 | grep -qi retire
      -> fatal: ambiguous argument '1637e808': unknown revision or path
         not in the working tree.

Cause, established before any remedy was attempted: the container's
checkout was a SHALLOW clone, and those three checks address commits by
hash.

    $ git rev-parse --is-shallow-repository
    true
    $ git rev-list --count HEAD
    138
    $ for c in 1637e808 f304fec1 6a8758a5; do git cat-file -t $c; done
    fatal: Not a valid object name 1637e808
    fatal: Not a valid object name f304fec1
    fatal: Not a valid object name 6a8758a5
    $ git diff --stat origin/main -- docs/map/CON-run-identity.md
    (no output)                      # untouched by this tranche

    $ git fetch --unshallow origin   # real 0m5.280s
    $ git rev-list --count HEAD
    2536
    $ for c in 1637e808 f304fec1 6a8758a5; do git cat-file -t $c; done
    commit
    commit
    commit

Then the run above, 0 failed. The three checks are correct and were
never at fault; the clone was. Parked as **W7-P1** — the gate's reporting
should name a shallow clone rather than an unknown revision. No check was
edited, skipped or weakened.

### The diff gate (R2, R3, R23)

    $ git diff --stat origin/main
     docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md            | 811 +++++++++++++
     .../CHECKLIST.md                                    |  42 ++
     .../PARKED.md                                       | 127 +++
     .../REQUEST.md                                      | 130 +++
     .../SPEC.md                                         | 129 +++
     .../VALIDATION.md                                   |  ...
     6 files changed

Exactly ONE new file under `docs/`, plus this tranche's directory.

    $ git diff --name-only origin/main | grep -E '^(src|tests)/'
    (no output)                      # READ-ONLY GATE PASS

No pytest gate is owed: no byte under `src/` or `tests/` changed.

---

## Requirement by requirement

| R | Acceptance check | Proof | Verdict |
|---|---|---|---|
| R1 | target repository is `AHepi/DeepReason` | `git remote -v` → `origin https://github.com/AHepi/DeepReason (fetch)`. Verified before any other work. | PASS |
| R2 | one document, nothing else | diff gate above: one file under `docs/`, rest inside the tranche dir | PASS |
| R3 | read-only on `src/` and `tests/` | `git diff --name-only origin/main \| grep -E '^(src\|tests)/'` empty | PASS |
| R4 | branch and environment | `be9bcff54 ancestor: OK`; `imports OK: deepreason /home/user/DeepReason/src/deepreason/__init__.py`, `pytest`, `xdist`, `jsonschema` all import; `deepreason` on PATH at `/usr/local/bin/deepreason` | PASS |
| R5 | CLAUDE.md read in full; `dr-drive-harness` and `dr-explain-to-operator` loaded | both skills invoked this session before the first operator-facing message; `dr-change-orchestrator` loaded as the routing family | PASS |
| R6 | final-output style: worry-first, terms glossed in-line, exactly ONE analogy | opening sentence is the verdict, before any mechanism; a glossary paragraph defines committed run root / provider call / dispatch / seat / wire contract / `verify_root` before §1, and each organ row glosses its own subject in the row; `grep -icE 'belt\|lathe\|workshop\|motor'` → 4 hits, all inside the single closing paragraph, and the draft's second belt image in the opening was removed to keep the count at one | PASS |
| R7 | every named input read in full before drafting | read log below | PASS |
| R8 | every claim cites a named input; no re-derivation | no instrument was run against any root by this tranche; every figure is quoted with its source artifact and that artifact's own label | PASS |
| R9 | all six W windows cited | `W1` 16 refs, `W2` 16, `W3` 18, `W4` 10, `W5` 8, `W6` 14, `PROGRAM.md` 1 | PASS |
| R10 | P-R1 and the P-C1 arm comparison cited | `poietics-program` 2 refs, `constructive-frontier` 7 refs, including the strengthened P5 refutation in §3.1 item 3 | PASS |
| R11 | the three RESEARCH_ notes cited | `RESEARCH_STRUCTURED_OUTPUT_COERCION` 2, `RESEARCH_FINDINGS_Q1Q10` 3, `RESEARCH_SHAPE_CRITIQUE` 1 | PASS |
| R12 | LESSONS_LEARNED as the frame | 2 refs; §1.3 quoted in the header as the rule the document is written under, and named again in road (a) | PASS |
| R13 | four sections, nothing else | `grep -n '^## '` → `## 1.`, `## 2.`, `## 3.`, `## 4.`, `## Appendix`. The header's explanatory block was demoted to `###` so the section count is exactly four plus the appendix R21 requires. | PASS |
| R14 | organ table: verdict + number + citation, every row | 11 rows; a per-row scan for an empty number or citation cell returns nothing; verdicts drawn only from the five-value vocabulary (WORKS 4, HARMFUL-AS-WIRED 3, INERT 2, PHANTOM 1, UNEXERCISED 1) | PASS |
| R15 | five causes, in the given order, one paragraph each, each tied to its table | §2.1 41.2 % (W6 T12) → §2.2 24.6 % (W6 T5) → §2.3 zero coupling (W2 §5, §3a) → §2.4 10× collinearity (W1 P-C1 headline) → §2.5 invented handles (W1 §2, §3). §2.6 adds recombination, which R16 names explicitly. | PASS |
| R16 | HARNESS-DESIGN / MODEL-BEHAVIOR / WIRING-NEVER-BUILT on every cause | three labels defined at the head of §2 and each used twice across the six causes; §2.2 is labelled as harness design amplifying model behaviour, which is what the record shows and is stated as such rather than forced into one bucket | PASS |
| R17 | three lists; refuted-as-wired distinguished from refuted-in-principle | §3.1 (8 entries, each marked **as wired** or **outright**), §3.2 (9), §3.3 (9) | PASS |
| R18 | record machinery, scratch, guards, two-call protocol in WORKS with numbers | §3.3 items 1, 2, 3, 4 — 0 violations / 463 of 463 / 60 of 60 / 0 of 3 155 join failures; 18.1 % vs 4.3 %, p = 0.0004; 114 of 122; 22 regressions and 3 857 passed 0 failed, with 96 live typed declines | PASS |
| R19 | three roads as named; NO recommendation | §4 opens **"No recommendation is made here."**; the only other occurrence of the word inside §4 is a citation to the external note's own "recommendation 2" | PASS |
| R20 | each road: agent cost, token cost, success evidence | each of (a) (b) (c) carries the three labelled paragraphs; road (b) additionally registers its FAILURE condition in advance | PASS |
| R21 | one appendix line per W1–W6 parked prompt | 32 rows: W1 6, W2 5, W3 6, W4 4, W5 6, W6 5 — matching the six source `PARKED.md` files exactly | PASS |
| R22 | docs_verify full, 0 failed; no `check:` lines; header says why | gate above; `grep -c '^check:'` → 0; the header carries the "This document carries no `check:` lines, deliberately" paragraph and its reason | PASS |
| R23 | one new file under `docs/` plus the tranche dir | diff gate above | PASS |
| R24 | commit and push at every phase boundary | three pushed commits: request+spec, the document, and this closing set | PASS |
| R25 | DELIVERY closes with the document's own opening sentence, quoted | `DELIVERY.md`, checked against the document byte for byte | PASS |

---

## The read log (R7)

Read in full before a word of the document was drafted.

| input | where | read |
|---|---|---|
| `PROGRAM.md` | `main` | full — the ten dimensions, the concurrency contract, the 54-root inventory table |
| W1 `GOAL.md`, `README.md`, `RESULTS.md`, `PARKED.md`, `AGGREGATE.md` | `main` | full |
| W2 `GOAL.md`, `RESULTS.md`, `TABLES.md`, `PARKED.md` | branch `claude/criticism-anatomy-w2-1z2029` | full |
| W3 `GOAL.md`, `RESULTS.md`, `PARKED.md` | branch `claude/run-anatomy-w3-census-p5pgmb` | full |
| W4 `GOAL.md`, `RESULTS.md`, `FUNNEL.md`, `PARKED.md` | `main` | full |
| W5 `GOAL.md`, `RESULTS.md`, `PARKED.md`, `LAW_CHECK.md`, `STALENESS.md` | `main` | full |
| W6 `GOAL.md`, `RESULTS.md`, `PARKED.md`, `TABLES.md` (T12, T13), `VERIFY.md`, `FLOW_AGGREGATE.json` outcome table | `main` | full |
| `experiments/2026-08-25-poietics-program/RESULTS.md` and `PARKED.md` P5 (strengthened) | `main` | full |
| `experiments/2026-08-25-change-constructive-frontier/RESULTS.md` | `main` | full |
| `docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md` | `main` | consumption points and the PhantomFill section in full |
| `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q4, Q5 | `main` | full |
| `docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md` §(C) and the scorecard | `main` | full |
| `docs/LESSONS_LEARNED_2026-08-17.md` | `main` | §1–§2 in full, §1.3 quoted |
| `experiments/2026-08-22-change-two-call-seat-protocol/DELIVERY.md` | `main` | read to source §3.3 item 4's numbers rather than assert them |
| `CLAUDE.md`, `docs/map/INDEX.md`, `docs/map/INV-frozen-surfaces.md` | `main` | full / map preflight |

## One correction made during validation, recorded rather than hidden

The draft's organ-table row 7 and §3.3 item 3 broke the trial-guard
declines down as "39 formal supremacy, 62 ensemble-split, 37 defence, 12
referential integrity, 22 paraphrase". That sums to 172 against 153
actual declines, for two reasons: the 39 taken by formal supremacy leave
BEFORE the trial convenes and so are not among the 114 turned away, and
W4's headline figure of 62 ensemble-splits combines gate T6's 43 with the
19 re-ruling splits already inside gate T9's 22. Corrected to the
gate-by-gate figures in `W4 FUNNEL.md` leg 2: 43 + 37 + 12 + 22 = 114
turned away of 122 convened, 8 minted, with the 39 stated separately.
161 entered − 153 declined = 8, and `objects/warrant/` holds exactly 8
`w:argtrial:` warrants.
