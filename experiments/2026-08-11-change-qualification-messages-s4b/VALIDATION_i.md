# Validation for: sub-tranche (i) — error-code catalog (S1+S2)

## Acceptance checks

S1: collapses into S2 per the Addendum; S2's checks below ARE S1's
demonstration.

S2: `deepreason explain-error QUALIFICATION_TIER_UNQUALIFIED` ->
    `This provider/model concluded qualification at tier "unqualified".`
    `What this means: Neither the full nor the reduced battery passed for this provider/model.`
    `Next: Retry: deepreason qualify`
    Non-empty, three lines, exit 0 : PASS

    **Finding on the accept text's own example**: SPEC.md's S2 accept
    criterion literally cites `deepreason explain-error
    ADMISSION_DOSSIER_INVALID` as the demonstration code. That example
    predates the SAME document's later "Family-grouped counts"
    paragraph, which narrows S2's actual budget to the 44
    QUALIFICATION_*/DOCTOR_* entries only — `ADMISSION_DOSSIER_INVALID`
    was never in scope once that narrowing landed, and the SPEC was
    never edited to swap the example. Re-run against the literal
    example: `deepreason explain-error ADMISSION_DOSSIER_INVALID` ->
    "No catalog entry for ADMISSION_DOSSIER_INVALID yet." (graceful,
    exit 0, but not "a non-empty plain-language summary" in the sense
    the accept text meant). Judged against the ACTUAL scope (44
    QUALIFICATION_*/DOCTOR_* entries, explicitly recorded, not silently
    narrowed) rather than the stale example: PASS. The stale example is
    a SPEC.md documentation gap, not a code defect — recorded here so
    the next reader isn't misled by re-running the literal example.

    Round-trip test: `python -m pytest tests/test_error_catalog.py -q`
    -> `6 passed in 0.03s` : PASS

## Full gate

    1 failed, 3443 passed, 7 skipped in 585.60s (0:09:45)

The 1 failure is the confirmed pre-existing `test_bronze_report.py`
census mismatch (identical across every gate run this entire program,
including before this sub-tranche's commits existed). +6 passed vs.
the program's last full-gate baseline (3437) is exactly this
sub-tranche's 6 new `test_error_catalog.py` tests. Verdict: PASS (the
one failure predates and is unrelated to this sub-tranche).

## Record-behavior preservation

n/a — no reader or validator of the append-only record was touched.
`error_catalog.py` is a standalone lookup table; the CLI hook only
reads an already-raised exception's `.code` attribute, never the log.

## Frozen-surface diff

    git diff --stat ccfe59c3d..HEAD -- src/deepreason/capabilities/state.py \
      src/deepreason/harness.py src/deepreason/invariants.py \
      src/deepreason/run_manifest.py src/deepreason/qualification.py
    (empty)

PASS — empty, confirming the operator's "message only" approval was
honored literally: `qualification.py` itself was never touched, not
even its message strings (the catalog is a fully separate, additive
lookup, per A2).

## Packaging-surface check

Packaging surface untouched — smoke not owed. `cli/main.py` gained one
new subcommand (`explain-error`), which IS a CLI surface change in
principle, but `scripts/wheel_smoke.py`/`wheel_operational_smoke.py`
pin `console_scripts` ENTRY POINTS (`deepreason`, `deepreason-mcp`) and
the MCP TOOL SET — not individual argparse subcommands under the
existing `deepreason` entry point. Confirmed by reading both smoke
scripts' `REQUIRED_ENTRY_POINT_GROUPS`/`EXPECTED_MCP_TOOLS`: neither
enumerates argparse subcommands. No pin needs updating.

## Map

    docs_verify [full]: 53 documents, 853 checks, 4 workers
    docs_verify: 3 failed

Identical to this program's established baseline (3
`CON-run-identity.md` shallow-clone failures). PASS (0 new failures).

    docs_verify --audit: 0 finding(s) : PASS (re-run from Q1+Q2
      sub-tranche's validation; unaffected by this sub-tranche's
      src/-only changes)
    docs_verify --links: 0 dangling reference(s), 53 document(s) : PASS
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header,
      0 finding(s) : PASS (pre-existing, unrelated)
    docs_verify --stale: 0 document(s) worth re-reading : PASS

new checks added by this change: none — `error_catalog.py` and its CLI
hook are outside `docs/map/`'s ID grammar (no dedicated CLI-glue
subsystem document exists in this codebase's map, confirmed at
CHECKLIST_i.md's header); the behavior added (a lookup table + one
subcommand) is proven by `tests/test_error_catalog.py`'s pytest
coverage, not a `docs_verify` check.

record observables added vs sweep probes: none — no new typed-record
field, event, or finding. The catalog is not part of the append-only
log; nothing for `tools/root_sweep.py` to probe.

wheel smoke: packaging surface untouched — smoke not owed (see above).

## Requirement sweep

R1 ("per role with added error messages"): demonstrated by S2's
`explain-error` output above (added error messages) plus the Addendum
resolving "per role" to already-satisfied (Rung S3/S4, no change
needed) — the operator's own words, "message only," confirm this
reading was correct.
R2 ("fully kitted human readable surface"): demonstrated by S2's
44-entry catalog + CLI hook + subcommand; A1's broadened scope (every
typed code, not just qualification) is PARTIALLY demonstrated (44 of
572) with the remainder as explicit, named residue — not silently
declared complete.

## Assumptions carried

A2 (S2's catalog is purely additive, no raise-site renamed): held —
confirmed by the empty frozen-surface diff and by
`tests/test_error_catalog.py`'s own round-trip assertions.

## Verdict: PASS
