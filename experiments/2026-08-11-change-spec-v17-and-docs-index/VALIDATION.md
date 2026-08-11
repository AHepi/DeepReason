# Validation for: v1.7 spec amendment + docs/INDEX.md (Q1+Q2 approved)

## Acceptance checks

S1: `test -f docs/harness-spec-v1.7-amendment.md` -> exists : PASS
    Six surface citations re-confirmed by grep: `seat-bindings.v1`,
    `conjecturer.turn.v7`, `candidate_checker`,
    `resolve_school_role_lease`, `adjudication-blindness`,
    `config_referee`/"config referee" — all present : PASS

S2: `grep -q "v1.4/v1.5/v1.6/v1.7" CLAUDE.md` -> match : PASS

S3: `test -f docs/INDEX.md` -> exists : PASS
    All five target link strings (`map/INDEX.md`,
    `harness-spec-v1.3.md`, `ERRATA.md`, `ERRATA_EXECUTOR.md`,
    `proposals/`) confirmed present : PASS

## Full gate

    1 failed, 3437 passed, 7 skipped in 591.77s (0:09:51)

`tests/test_bronze_report.py::test_census_totals_internally_consistent`
(`assert 159 == 165`) — the SAME pre-existing failure documented in
`experiments/2026-08-11-program-closeout/CLOSEOUT.md` (already run once
this session, before this tranche's commits, with identical result:
`1 failed, 3437 passed, 7 skipped`). This tranche's diff touches only
`docs/harness-spec-v1.7-amendment.md`, `docs/INDEX.md`, and one line of
`CLAUDE.md` — none of `experiments/bronze_flat_2026-07-13/`,
`tests/test_bronze_report.py`, `scripts/bronze_census.py`. Confirmed
pre-existing and unrelated, not re-diagnosed a third time (already
parked twice: `experiments/2026-08-09-change-judge-evidence-review/
PARKED.md` P1). Verdict: PASS (the one failure is not this tranche's).

## Record-behavior preservation

n/a — this tranche touches no reader or validator of the append-only
record; zero `src/` files changed.

## Frozen-surface diff

    git diff --stat ccfe59c3d..HEAD -- src/deepreason/capabilities/state.py \
      src/deepreason/harness.py src/deepreason/invariants.py \
      src/deepreason/run_manifest.py src/deepreason/qualification.py \
      src/deepreason/llm/firewall.py
    (empty)

PASS — empty, as SPEC.md forecast.

## Packaging-surface check

Packaging surface untouched — smoke not owed. This tranche adds two
Markdown files and edits one line of `CLAUDE.md`'s prose; no
`pyproject.toml`, CLI entry point, MCP tool, or wheel-layout file is in
this tranche's target list.

## Map

    docs_verify [full]: 53 documents, 853 checks, 4 workers
    docs_verify: 3 failed

The 3 failures are the pre-existing `CON-run-identity.md` shallow-clone
git-history failures (lines 195/197/199), identical to the baseline
recorded in `experiments/2026-08-11-sweep-smoke-currency/REPORT.md` and
`experiments/2026-08-09-change-judge-evidence-review/VALIDATION.md`'s
own prior confirmation of the same cause. Not caused by this tranche —
neither new file is under `docs/map/`, and `docs_verify`'s document/
check counts (53/853) are UNCHANGED from this tranche's pre-change
baseline. PASS (0 new failures).

    docs_verify --audit: 0 finding(s) : PASS
    docs_verify --links: 0 dangling reference(s), 53 document(s) : PASS
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header,
      0 finding(s) : PASS (the 16 are pre-existing, unrelated seam
      documents this tranche does not touch)
    docs_verify --stale: 0 document(s) worth re-reading : PASS

new checks added by this change: none — this tranche adds
`docs/INDEX.md` and `docs/harness-spec-v1.7-amendment.md`, neither
under `docs/map/`'s ID grammar (SUB-/CON-/SEAM-/INV-/REC-), so neither
carries a `check:` line by the map's own convention (`docs/map/
SCHEMA.md` scopes checks to map documents; this tranche's content is
descriptive prose about ALREADY-shipped, already-tested behavior, not
a new claim about `src/deepreason/` that would need its own
re-derivation check).

record observables added vs sweep probes: none — this tranche adds no
typed-record field, event, or finding; it documents six that already
exist and are already read by existing readers (`tools/root_sweep.py`
already covers `seat-bindings.v1` and module fingerprints per Item 1's
2026-08-11 fix; the other four surfaces are not append-only-record
observables in the sweep's sense — they are wire contracts, routing
functions, and verification-check names, not new digest-bearing
payload types).

wheel smoke: packaging surface untouched — smoke not owed (see above).

## Requirement sweep

R1: demonstrated by S1's pasted output above (all six surfaces present
with concrete citations) and S2's pasted output (CLAUDE.md line
updated in the same commit).
R2: demonstrated by S3's pasted output above (docs/INDEX.md exists,
links all four required targets — actually five, including the
harness-spec series link, all confirmed).
R3: demonstrated by absence — `git diff --stat ccfe59c3d..HEAD` (full
program diff, this follow-on tranche included) touches no file under
`experiments/2026-08-11-change-qualification-messages-s4b/` and no
`src/` file; Q3/Q4 remain exactly as designed and stopped, untouched.

## Assumptions carried

A1: v1.7's internal structure follows v1.6's established
"Status and scope" → lettered-sections pattern — held, confirmed by
reading the finished file.
A2: `docs/INDEX.md` is new navigational content, not a copy of any
underlying document's facts — held; every section is a pointer + one
line of orientation, no restated technical claims.

## Verdict: PASS
