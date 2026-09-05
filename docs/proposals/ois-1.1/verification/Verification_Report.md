# Verification report

## Actual run

The finite reference passed **66 tests**. The test suite includes independent enumeration of **2,304** two-node dependency/attack/readiness combinations. All **9 selected mutations were detected** by compiling the mutated checker and running tests against it. The two fixture generators produced **8 grounded, application-bound appraisal slices**.

Run timestamp: `2026-09-05T09:15:49.858228+00:00`. Runtime: Python `3.13.5`. The code uses the standard library only.

These are results about the delivered finite reference and stipulated interpretations. They do not prove semantic truth, creativity, explanation quality, physical realizability, or universal capacity. Passing the small exhaustive family is not a proof of every graph size. The specification supplies a separate mathematical argument for the finite policy.

## Exact document bindings

Authority SHA-256: `66839c4aff0095015965dd6083347f2e3e78340170fa3d9ffe26caa337015d4e`.

Specification SHA-256: `c5e75456d46f7d2ac3fdf47abd29077b23c34a70bd65a69ac59cb77271c63799`.

Checker SHA-256: `6edcbd90ce0e99d0af7058e3fc0f7dd4d87e496b228f79156ceae8d8ea3392e6`.

## Fixture reports

The balances-r1 query concerns the original adequacy case. All subsequent displayed queries concern the fixture's local progress case. Raw and usable are summaries of evidence applications, not semantic verdicts. Full labels, exact claim keys, sources, and stamps are in `fixture_results.json`.

| Fixture | Entries at cut | Raw cases | Usable cases | Semantic decision |
|---|---:|---|---|---|
| balances-r1 | 6 | POSITIVE_CASE_ONLY | NO_CASE | NOT_EVALUATED |
| balances-r2 | 13 | POSITIVE_CASE_ONLY | POSITIVE_CASE_ONLY | NOT_EVALUATED |
| balances-r3 | 15 | POSITIVE_CASE_ONLY | NO_CASE | NOT_EVALUATED |
| balances-r4 | 17 | POSITIVE_CASE_ONLY | POSITIVE_CASE_ONLY | NOT_EVALUATED |
| balances-r5 | 19 | POSITIVE_CASE_ONLY | POSITIVE_CASE_ONLY | NOT_EVALUATED |
| seasons-r1 | 9 | POSITIVE_CASE_ONLY | POSITIVE_CASE_ONLY | NOT_EVALUATED |
| seasons-r2 | 12 | POSITIVE_CASE_ONLY | NO_CASE | NOT_EVALUATED |
| seasons-r3 | 14 | POSITIVE_CASE_ONLY | POSITIVE_CASE_ONLY | NOT_EVALUATED |

## Selected live mutations

| Mutation | Result | Reported failing checks |
|---|---|---:|
| M01-failed-body-counts | detected | 3 |
| M02-criticism-dependency-exemption | detected | 3 |
| M03-missing-activation-counts | detected | 1 |
| M04-incompatible-history-allowed | detected | 2 |
| M05-ungrounded-reference-allowed | detected | 4 |
| M06-boundary-erased | detected | 1 |
| M07-contribution-erased | detected | 1 |
| M08-empty-family-counts | detected | 1 |
| M09-nested-reference-ignored | detected | 1 |

A detected mutation is not counted from a syntax failure or timeout. The individual failures are retained in `mutation_results.json`. The runner does not claim that each mutation is an independent semantic axiom or that every specification requirement is covered.

## Coverage and limits

The implementation covers finite reference grounding, unique artifact IDs, partial-order cuts, alternative-history constraints, initial ancestry, immutable input-payload snapshots, atomic local references, typed claim-key identity, supplied application dependency and attack graphs, DA-1 labels, evidence-presence summaries, source binding for the integrated fixtures, and selected projection guards. It includes simple absorption and finite-variation reporting helpers.

The implementation does not discover hidden premises or determine whether a supplied activation judgment is sound. It does not implement full natural-language parsing, persistent storage, a complete target-history interpreter, the typed derivation adapter, semantic authorship or reason-use judgment, generalized progress assessment, or a capacity detector. Some tests use stipulated semantic counterexamples to expose a logical mismatch; those are not experiments on real thinkers.

## Reproduce

From the `verification` directory, run:

```sh
python -m unittest -v
python run_mutations.py
python build_reports.py
```

`build_reports.py` repeats the tests and mutations and regenerates this report and the JSON results using the document bytes present at execution. A later rerun has a new timestamp. It does not modify the authority or specification.
