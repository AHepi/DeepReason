# Request: retire the calibration-receipt dead-end gate on argumentative status authority

Captured: 2026-08-13 from the operator's task-description message
(delivered as the initiating GitHub-issue-style task for this session).

## Verbatim

> Change tranche: retire the calibration-receipt dead-end gate on
> argumentative status authority — convert it to a typed disclosure at both
> call sites. Route through dr-change-orchestrator as merged on current
> main; the workflow's own ledger, gate, and proof rules govern every
> artifact.

> AUTHORITY for REQUEST.md — two layers, ledger both verbatim:
> (1) The operator's standing law (CLAUDE.md, 2026-08-12): "All
> configurations should be allowed." Compile-time denial is abolished;
> former refusals become typed disclosures; runtime keeps only real,
> config-specific point-of-use failures.
> (2) The finding, confirmed by the operator via the monitor (2026-08-12):
> calibration_receipt_is_verified() (src/deepreason/authority.py, block at
> lines ~140-225) is a stub permanently wired to False — no configuration
> can ever satisfy it, regardless of what CALIBRATION_RECEIPT names. It is
> therefore a dead-end denial (a nailed-shut switch with no key anywhere in
> the codebase), categorically different from an unreachable model or a
> zero budget, and it goes — at BOTH call sites:
> text_status_authority_issues() invoked from compile_run_manifest
> (run_manifest.py ~4023-4037) AND the identical re-check in
> preflight_harness(), which would otherwise refuse the run a moment after
> a successful compile. Removing one site and not the other is the named
> failure mode; removing both WITHOUT the disclosure is also wrong.

> THE SHAPE (confirmed design, not open for re-derivation):
> - Both sites CONVERT to a typed disclosure notice recorded alongside the
>   compiled manifest / preflight result: trial_required (or any
>   status-changing argumentative authority) active with no verified
>   calibration receipt for the judge ensemble. The run proceeds; the
>   record says what the old gate would have said.
> - The stub ceases to refuse anything; delete it or absorb it into the
>   notice construction — SPEC.md's choice, recorded.
> - CALIBRATION_RECEIPT (the config field): before declaring it vestigial,
>   grep-proof every reader of CALIBRATION_RECEIPT and
>   calibration_receipt_is_verified in the census — pasted output, not the
>   word "none". If vestigial, it stays parseable (a config naming it
>   still compiles; the notice records it as unverified).
> - llm/adapter.py's transaction_authority_required guard and the
>   defended-trial transaction wiring (merged, PR #13) are NOT in scope —
>   the wired path is the road this gate was blocking; do not touch it.

> FROZEN-SURFACE GRANT (ledgered here, scoped): surface 4
> (run_manifest.py), exactly the text_status_authority_issues call-site
> conversion, model and validator together. No other surface is granted;
> per the workflow's own stop condition, spec-time discovery that more is
> needed is a stop — report with the census, priced options, one
> recommendation.

> TESTS: every test asserting the refusal flips to asserting success plus
> the recorded notice — enumerated in SPEC.md BEFORE any is touched,
> updated in the same commit as the site it pins, never weakened (the
> watch-for: a test deleted instead of flipped). Old roots replay
> byte-unchanged: targeted verify_root_report on a known-good committed
> root at validation, output pasted as PROOF.

> ERRATA: if any committed document describes the calibration receipt as a
> working, satisfiable mechanism — or claims trial_required was reachable
> — that is a docs/ERRATA.md entry (next free number; check the ledger
> tail, it has moved repeatedly this week). Otherwise the errata checkpoint
> records the scan command and its empty output, per the workflow's
> proof-of-looking rule.

> GATE: ring while iterating; full gate once at the boundary (baselines: 1
> pre-existing test_bronze_report failure; 5 MCP-thread tests known-flaky
> under -n 4 — isolate before attributing). docs_verify full (baseline: 3
> pre-existing CON-run-identity.md shallow-clone failures). Map documents
> (SUB-adjudication, CON-authority, and whichever seam covers
> authority-x-manifest) move in the same commits as the code. Commit and
> push every phase boundary (retry 2s/4s/8s/16s). Deliver with R-by-R
> reconciliation and pasted gate output as PROOF throughout — the merged
> workflow's G1 rule: "done" is an assertion, output is evidence.

## Requirements

R1 (behavior): "retire the calibration-receipt dead-end gate on
argumentative status authority — convert it to a typed disclosure at both
call sites."

R2 (process): "Route through dr-change-orchestrator as merged on current
main; the workflow's own ledger, gate, and proof rules govern every
artifact."

R3 (behavior): apply the operator's standing law verbatim — "All
configurations should be allowed." Compile-time denial is abolished;
former refusals become typed disclosures; runtime keeps only real,
config-specific point-of-use failures.

R4 (behavior): remove the refusal at BOTH call sites — "text_status_authority_issues()
invoked from compile_run_manifest (run_manifest.py ~4023-4037) AND the
identical re-check in preflight_harness()... Removing one site and not the
other is the named failure mode; removing both WITHOUT the disclosure is
also wrong."

R5 (behavior): "Both sites CONVERT to a typed disclosure notice recorded
alongside the compiled manifest / preflight result: trial_required (or any
status-changing argumentative authority) active with no verified
calibration receipt for the judge ensemble. The run proceeds; the record
says what the old gate would have said."

R6 (behavior/artifact): "The stub ceases to refuse anything; delete it or
absorb it into the notice construction — SPEC.md's choice, recorded."

R7 (process): "CALIBRATION_RECEIPT (the config field): before declaring it
vestigial, grep-proof every reader of CALIBRATION_RECEIPT and
calibration_receipt_is_verified in the census — pasted output, not the
word 'none'. If vestigial, it stays parseable (a config naming it still
compiles; the notice records it as unverified)."

R8 (process): "llm/adapter.py's transaction_authority_required guard and
the defended-trial transaction wiring (merged, PR #13) are NOT in scope —
the wired path is the road this gate was blocking; do not touch it."

R9 (process): frozen-surface grant is scoped exactly to "surface 4
(run_manifest.py), exactly the text_status_authority_issues call-site
conversion, model and validator together. No other surface is granted;
per the workflow's own stop condition, spec-time discovery that more is
needed is a stop — report with the census, priced options, one
recommendation."

R10 (process): "every test asserting the refusal flips to asserting
success plus the recorded notice — enumerated in SPEC.md BEFORE any is
touched, updated in the same commit as the site it pins, never weakened
(the watch-for: a test deleted instead of flipped)."

R11 (process): "Old roots replay byte-unchanged: targeted
verify_root_report on a known-good committed root at validation, output
pasted as PROOF."

R12 (process): "if any committed document describes the calibration
receipt as a working, satisfiable mechanism — or claims trial_required was
reachable — that is a docs/ERRATA.md entry (next free number; check the
ledger tail, it has moved repeatedly this week). Otherwise the errata
checkpoint records the scan command and its empty output, per the
workflow's proof-of-looking rule."

R13 (process): "ring while iterating; full gate once at the boundary
(baselines: 1 pre-existing test_bronze_report failure; 5 MCP-thread tests
known-flaky under -n 4 — isolate before attributing). docs_verify full
(baseline: 3 pre-existing CON-run-identity.md shallow-clone failures)."

R14 (artifact): "Map documents (SUB-adjudication, CON-authority, and
whichever seam covers authority-x-manifest) move in the same commits as
the code."

R15 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s)."

R16 (process): "Deliver with R-by-R reconciliation and pasted gate output
as PROOF throughout — the merged workflow's G1 rule: 'done' is an
assertion, output is evidence."

## Standing constraints

C1: "All configurations should be allowed." — CLAUDE.md operator design
law, 2026-08-12, quoted again in this task's AUTHORITY section.

C2: "llm/adapter.py's transaction_authority_required guard and the
defended-trial transaction wiring (merged, PR #13) are NOT in scope — the
wired path is the road this gate was blocking; do not touch it." — task
description, THE SHAPE section.

C3: "FROZEN-SURFACE GRANT (ledgered here, scoped): surface 4
(run_manifest.py), exactly the text_status_authority_issues call-site
conversion, model and validator together. No other surface is granted;
per the workflow's own stop condition, spec-time discovery that more is
needed is a stop — report with the census, priced options, one
recommendation." — task description, FROZEN-SURFACE GRANT section.

C4: SETUP section (verbatim): "git fetch origin main && git checkout -B
claude/calibration-receipt-notice-b6wp3k origin/main; git merge-base
--is-ancestor 85717580f HEAD || re-fetch. pip install -e .
--break-system-packages -q; pip install pytest pytest-xdist jsonschema
--break-system-packages -q. Use `python -m pytest`, never bare pytest.
Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator."
(already performed this session)

## Open questions (for dr-spec-change)

Q1: Whether the stub `calibration_receipt_is_verified()` is deleted
outright or absorbed into the notice-construction code is left to
SPEC.md's choice per R6 — needs a recorded decision with reasoning once
the census (R7) is in hand.

Q2: The exact shape of the "typed disclosure notice" (field name(s),
where it is attached on the compiled-manifest object and the
preflight-result object, and whether one shared model serves both call
sites) is not specified verbatim and needs to be designed in SPEC.md
against the actual current code at both sites.

Q3: Whether CALIBRATION_RECEIPT / calibration_receipt_is_verified are
referenced anywhere outside the two named call sites (which would bear on
whether surface 4 alone is sufficient, per the frozen-surface stop
condition in C3) is unknown until the grep-proof census (R7) is run.

## Amendments

(none yet — append-only; future operator messages land here)
