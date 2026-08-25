# VALIDATION — close-out prune

Verdict: **PASS**, after one R5 remedy cycle.

## Acceptance checks

| # | check | result | proof |
|---|---|---|---|
| AC1 | `experiments/OPEN_PARKS.md` carries every open park item | **PASS** — 71 items from 18 tranches (audit's 60 corrected) | `proof/extraction-fidelity.txt` |
| AC2 | nothing summarized or truncated | **PASS** — 71/71 byte-identical; 0 non-blank lines left outside an item | `proof/extraction-fidelity.txt` |
| AC3 | 70 directories removed | **PASS then CORRECTED** — 70 removed, 1 restored per R5; net 69 | `proof/r5-remedy.txt` |
| AC4 | every KEEP directory still present | **PASS** — 82/82, 0 missing | `proof/keep-intact.txt` |
| AC5 | `docs_verify` FULL, no non-baseline failure | **PASS on re-run** — 3 failed, all `CON-run-identity` git-history (shallow clone) | `proof/gate-docs-verify-rerun.txt` |
| AC6 | full pytest gate, 0 failed | **PASS on re-run** — 4162 passed, 6 skipped, 0 failed | `proof/gate-pytest-rerun.txt` |
| AC7 | nothing changed outside `experiments/` | **PASS** — empty status | `proof/scope-intact.txt` |
| AC8 | P5 untouched | **PASS** — 13/13 docs present | `proof/scope-intact.txt` |

## The first gate pass went red, and that is recorded rather than smoothed over

R5 names a stop condition: "Either instrument going red means something
load-bearing left the tree." It fired.

| | first pass | after remedy |
|---|---|---|
| `docs_verify` | 4 failed — 1 non-baseline (`SUB-application.md:111`) | 3 failed, all baseline |
| pytest | 1 failed, 4161 passed | 0 failed, 4162 passed |

**Both gates found the same single cause**, independently:
`tests/test_results_command.py::test_results_embedder_absence_is_typed_not_a_failure`
died with `UnsupportedRunManifestVersionError` because
`experiments/live_compare_2026-07-28` held the smallest committed run root
carrying no embedder stamp, and the prune removed it. The selector fell
through to a schema-version-3 root the current reader refuses.

R5's remedy was applied exactly as written: restored, rowed KEEP in
`experiments-census.md` (row 143) with the reason, and the failing
question named — **Q-E1**, which could not have caught it. The test
reaches run roots by enumeration (`git ls-files experiments`) and selects
by size and property, never by path; the directory's path appears in no
source file, so a path grep has nothing to find. Parked as **P3** with a
proposed fifth census question.

Measured, not assumed: 53 of 113 committed run roots were removed and
exactly ONE test broke — one failure in 4162, one non-baseline doc check
in 1069. The other 52 removed roots were not selected by any test. P3
records that this is luck rather than design.

## Final state

| | before | after |
|---|---|---|
| `experiments/` directories | 154 | 85 |
| — rowed KEEP | 82 | 82 |
| — restored per R5 | — | 1 (`live_compare_2026-07-28`) |
| — tranche directories | 2 | 2 |
| committed run roots | 113 | 61 |
| open park items, findable in one file | 0 | 71 |

Both gates at baseline. Nothing outside `experiments/` touched. Every
deleted directory retrievable at `6e64330fe`.
