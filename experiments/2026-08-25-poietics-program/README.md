# The Poietics research program — external record and three registered runs

Operator-supplied 2026-08-25 as `POIETICS_FULL_RECORD.zip`, committed
verbatim under `record/` below the rule. **This is EXTERNAL material.**
Claims in it are unverified by this repository's instruments; it is
evidence ABOUT someone else's project, never evidence about DeepReason.

## The record's own caution, quoted — read this before using any number

The bundle's `README.md` closes with two cautions. Both bind every use of
this material in this repository, and the first is the reason `report/14`
is in the committed set at all:

> 1. **The report's author is the same agent that did the work.** Section 14
>    exists because this record shows that agent repeatedly compressing
>    toward a cleaner story. Treat the narrative sections as the agent's
>    account, and `data/` and `sources/` as the evidence. The extracted
>    episode records in 03–09 were produced by independent passes over the
>    sources and are a partial check on the narrative.
> 2. **Numbers in this bundle supersede numbers in the git history.** Two
>    coverage figures — "6/6 held" and "59 caught / 3 survived" — were
>    published in commit messages before being found wrong. They remain in
>    `data/commits.json` because the history is append-only. The correct
>    figures are **16 caught, 46 survived, 3 of 26 decisions held.**

Section 14 states the same discipline in its own voice:

> *This section exists because the project's own diagnosed failure mechanism
> is **compression under narrative pressure** (`treadle0.5/FIELD_REPORTS.md`,
> header). Every claim below was made in good faith, recorded, and later
> found wrong. They are kept rather than deleted: the record of how a
> measurement went wrong is worth more than the measurement.*

**The operative split, applied here:** `record/report/*` is the agent's
ACCOUNT — treat every sentence as a claim. `record/data/*.json` is the
EVIDENCE — machine-readable extracts that can be recomputed. Where the two
disagree, `data/` wins. Where a narrative number is contradicted by
`report/14`, the §14 correction wins over both.

## What is committed here, and what is not

The operator holds the full `POIETICS_FULL_RECORD.zip` (118 files:
`README.md`, `report/` 16 sections, `data/` 7 JSON extracts, `sources/` 94
files). **Committed here is a curated subset of 12 files.** The rest of the
`report/` tree and the whole `sources/` tree are deliberately NOT committed;
to consult them, go back to the operator's zip.

| committed | bytes | why this one |
|---|---|---|
| `record/README.md` | 4,873 | the bundle's own framing and both cautions |
| `record/report/00_EXECUTIVE_SUMMARY.md` | 6,045 | the whole cycle in two pages |
| `record/report/12_MUTATION_TESTING.md` | 75,865 | the measurement that produced the 3-of-26 result |
| `record/report/14_CORRECTIONS_AND_WITHDRAWN_CLAIMS.md` | 10,802 | every claim made and later found wrong |
| `record/report/15_INSIGHTS.md` | 12,089 | transferable findings, each with its evidence limits |
| `record/data/` (7 JSON) | 861,036 | the evidence layer: commits, mutations, review ledger, episodes, tests, engine, metrics |

Deliberately absent: `report/01`–`11`, `report/13`, and all 94 files of
`sources/` — including the byte-pinned core specification, the 31
independent review outputs, and the three instrument scripts. **Any claim
that needs those cannot be checked from this repository.** Say so rather
than inferring.

## Verbatim proof

Every committed file is byte-identical to its counterpart in the operator's
zip. SHA-256, computed against the extracted bundle at commit time:

```
a0a64514712b0c27859f1da10c66db2201d86b59d6a89c3efa461584843dd1a5  README.md
550763b627cd359492773e94cfd58e7976e3bc81ee43b84312fd1c6d75e4d20a  report/00_EXECUTIVE_SUMMARY.md
ab642b0f57bb5c1012438da340025e37387ba608e3ac3c6ce523f4aff76cf978  report/12_MUTATION_TESTING.md
557948f391fc1194569555e2bf71a72ecaaa034f5d198e1a29ea88944e6e61bb  report/14_CORRECTIONS_AND_WITHDRAWN_CLAIMS.md
592907c9a0e2b569f3efcc505ecd91f929f3b4dd8b0f403d4cc585ca7f4fd946  report/15_INSIGHTS.md
4fac3a708cd60997ad570760614a0f7e95e3d0836b73a9475dc808ac76d5e31f  data/commits.json
fec896b4db2bba2b348de193bb6cbeb9c61aca19f28a930241e046cddd4d0354  data/engine.json
e3f898877e3637800173227b2a51d46d7c055c8923aa933035be4a2641b3cf9c  data/extracted_episodes.json
8288e741635542d6d280a16b9593d59da136e12bd75bf73339d02cf341197563  data/metrics.json
8f0fdbc24b746a50499f73b9d29d50c0cf3a8cc6af9610ef9793f898e3c2eb91  data/mutations.json
4d86bd4a2a3439849a6ce4482a9c883c4ebffe83f4985621c7658cc48297e2b1  data/review_ledger.json
2a1a393a611784c7334cf985d04eae2c6be284794697b5ca01075a1fa90a36dd  data/tests.json
```

Re-check with `sha256sum` against `record/` at any later commit; a moved
digest means the "verbatim" claim has stopped being true.

## What this record is for

It is the attached evidence for **P-R1**, the explanation run — the first of
three registered runs in `PROGRAM.md`. P-R1 asks under what conditions a test
constrains its subject rather than describing it, and must account for the
record's central distribution: `compile.py`, the one module whose guards were
installed under a shown-to-fail-first rule, lost 1 of 9 mutations; every
ordinarily-guarded module lost 4/4 to 6/7. Same author, same week, same care.

Two things this record is NOT. It is not evidence about DeepReason's own
guards — nothing here was measured on this repository. And it is not a
replication: the bundle contains no engine or test tree, so no pass/fail or
CAUGHT/SURVIVED claim in it is re-executable from these bytes. The honest
maximal claim available is internal consistency, which is what the record
itself says (`report/15`, and the bundle README's caution 1 above).

## Also supplied, deliberately not committed

The operator additionally uploaded two files in the same session. Neither is
part of the record set and neither is committed:

- `treadle0.5.zip` — the treadle 0.5.0 method library (24 files). This is the
  bundle's own `sources/method/` material, which the curation excludes. The
  repository separately vendors an earlier treadle at `tools/treadle/`; see
  CLAUDE.md's third-lane section for what routes there.
- `POIETICS_FINDINGS_REPORT.md` — an independent analyst's pass OVER the
  bundle. It is a secondary source about the record, not part of it, and is
  NOT bound into the P-R1 dossier: P-R1 explains the record, not an analysis
  of the record.

Both are ledgered verbatim as amendments A1 and A2 in `REQUEST.md`.
