# Poietics — full project record, 2026-08-17 to 2026-08-25

A complete evidentiary record of one nine-day working cycle on **Poietics**, a Python
implementation of the *PFF Core v0.1* specification (a typed admission boundary plus a
deterministic well-founded evaluator). Assembled for external analysis: **all primary
sources are included verbatim**, so every claim in the report can be checked against the
material it came from.

## The headline

A suite of **701 test methods and 2,985 subtests**, a **2.2 : 1** test-to-code ratio, and
three independent models confirming **15/15 conformance rows** — holding **3 of 26**
commitments when measured by mutation.

## Contents

```
README.md      this file
report/        16 sections, 683,702 bytes
data/          machine-readable extracts (JSON)
sources/       primary sources, verbatim
```

### `report/`

| section | bytes | subject |
|---|---|---|
| `00_EXECUTIVE_SUMMARY.md` | 6,045 | the whole cycle in two pages |
| `01_TIMELINE.md` | 9,050 | 50 commits over 9 days, phased |
| `02_ARTIFACT.md` | 6,581 | what exists: modules, tests, docs, proportions |
| `03_FOUNDATIONS.md` | 50,421 | evaluator, admission boundary, the profile-first method |
| `04_RULE_TARGET.md` | 44,718 | the longest thread: pins v0.1→v0.3, RT-1/RT-1a/RT-2/RT-6 |
| `05_DEFECT_LIFECYCLE.md` | 53,126 | a conclusion reversed; a capability found missing |
| `06_AUTHORITY_AUDIT.md` | 66,172 | the byte-pinned specification, AU-1…AU-7, two errata |
| `07_REGISTRY_PINNING.md` | 54,563 | what the package hash does *not* cover |
| `08_MILESTONES_5_8.md` | 72,958 | discernment report, predicate pack, canonical bytes, replay fold, CLI |
| `09_DECISIONS_AND_ATTACK.md` | 57,860 | the decision map, the attack that removed nine edges, boundary audits |
| `10_REVIEW_APPARATUS.md` | 64,502 | 53 hash-chained model calls; the guard that fired on the author |
| `11_ACCEPTANCE.md` | 6,410 | the sixteen accepted decisions and what implementing them cost |
| `12_MUTATION_TESTING.md` | 75,865 | the measurement that inverted the project's self-assessment |
| `13_METHOD_LIBRARY.md` | 92,540 | eighteen field reports verbatim, and the mechanism under them |
| `14_CORRECTIONS_AND_WITHDRAWN_CLAIMS.md` | 10,802 | every claim made and later found wrong |
| `15_INSIGHTS.md` | 12,089 | transferable findings, each with the limits of its evidence |

Sections 03–09 and the appendices to 10 and 13 are **extracted episode records**: 160
episodes, 311 key numbers, 113 open items and 319 verbatim quotations pulled
from the pins, batteries, review outputs and commit messages by nine independent passes over
the sources.

### `data/`

| file | contents |
|---|---|
| `commits.json` | all 50 commits with full message bodies (92,409 chars) |
| `mutations.json` | all 62 mutations: diff, decision, rationale, verdict |
| `review_ledger.json` | all 53 model calls: model, role, prompt digest, finish reason, reply size |
| `extracted_episodes.json` | the 160 extracted episodes, structured |
| `tests.json` | 33 test files, 701 test methods, by class |
| `engine.json` | 29 engine modules with line counts |
| `metrics.json` | headline counts |

### `sources/`

94 files verbatim: `docs/` (20 files, 871 KB, including the byte-pinned core specification),
`zoo/` (batteries, mappings, all 31 independent review outputs, round-trip packets and
back-translations, the call ledger, the mutation registry and its backlog), the method
library `treadle0.5/FIELD_REPORTS.md`, and the three instrument scripts
(`independent_review.py`, `mutation_probe.py`, `consistency_packet.py`).

## How to read it

**For the headline finding** — `00_EXECUTIVE_SUMMARY.md`, then `12_MUTATION_TESTING.md`.

**For transferable method** — `13_METHOD_LIBRARY.md` (eighteen field reports verbatim) and
`15_INSIGHTS.md`.

**For epistemic hygiene, read this first** — `14_CORRECTIONS_AND_WITHDRAWN_CLAIMS.md`. The
project's diagnosed failure mode is *compression under narrative pressure*, and that section
is the deliberate counterweight: every number that was wrong, and how.

## Two cautions for any analysis

1. **The report's author is the same agent that did the work.** Section 14 exists because
   this record shows that agent repeatedly compressing toward a cleaner story. Treat the
   narrative sections as the agent's account, and `data/` and `sources/` as the evidence.
   The extracted episode records in 03–09 were produced by independent passes over the
   sources and are a partial check on the narrative.
2. **Numbers in this bundle supersede numbers in the git history.** Two coverage figures —
   "6/6 held" and "59 caught / 3 survived" — were published in commit messages before being
   found wrong. They remain in `data/commits.json` because the history is append-only. The
   correct figures are **16 caught, 46 survived, 3 of 26 decisions held.**
