# Delivered: retire the calibration-receipt dead-end gate on argumentative status authority
Branch: `claude/calibration-receipt-notice-b6wp3k` @ `ee0e1352d` (pushed, tree clean)

## What changed

A configuration that asked for status-changing text-adjudication authority
(the `trial_required`/`single_family_trial` argumentative modes, or any of
the three `calibrated_status` surface knobs) used to have its run refused
before it could even start — at `compile_run_manifest` AND, redundantly,
again a moment later at `preflight_harness`. That refusal could never be
satisfied by any configuration: `calibration_receipt_is_verified()`
(`src/deepreason/authority.py`) has no verifier and always returns
`False`, so every `CALIBRATION_RECEIPT` value, real or fabricated, hit the
same wall. Per the operator's standing law ("All configurations should be
allowed," CLAUDE.md 2026-08-12), that dead end is retired at both call
sites. `src/deepreason/run_manifest.py`'s shared helper
`_preflight_text_authority` no longer raises; it converts each issue into
a typed `CompileNoticeV1` disclosure instead — the same code the retired
gate would have refused on, now recorded rather than fatal.
`compile_run_manifest` attaches it to `manifest.compile_notices` (the
existing all-configs-allowed notice mechanism, unchanged); `preflight_harness`
now RETURNS its own findings (`tuple[CompileNoticeV1, ...]` instead of
always `None`), since the manifest is already frozen by the time it runs
and cannot gain a fresh notice after the fact. The run proceeds either
way; the safe `observe_only` runtime fallback every other surface already
falls back to (`trial_authority_for`, untouched) still applies.

Seven tests in `tests/test_manifest_integration.py` flipped from
asserting a raise to asserting success plus the recorded notice — same
names, same parametrization, nothing deleted. Two of them
(`test_materialized_text_status_authority_is_rechecked_before_adapter_build`,
`test_runtime_calibrated_status_is_unverified_before_adapter_build`)
needed a scenario change, not just an assertion flip: their original
"compile with a safe config, recheck with an unsafe one" shape
incidentally ALSO diverged from the frozen manifest's authority snapshot,
which used to be masked by the calibration raise firing first but is now
unmasked into the separate, still-live, untouched
`TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH` refusal — found executing the
first checklist step, fixed by rechecking with the SAME config instead
(full account in SPEC.md's Addendum 1). `docs/map/CON-authority.md` and
`docs/map/SUB-manifest.md` were corrected in the same commit to describe
the disclosure instead of the retired "fail closed twice" refusal.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "retire the calibration-receipt dead-end gate... convert it to a typed disclosure at both call sites" | done | commit `90e49d979`; VALIDATION.md S1-S3 |
| R2 | "Route through dr-change-orchestrator... the workflow's own ledger, gate, and proof rules govern every artifact" | done | this tranche's own REQUEST/SPEC/CHECKLIST/VALIDATION/DELIVERY sequence |
| R3 | apply "All configurations should be allowed" verbatim | done | VALIDATION.md S2/S3 — no raise, run proceeds |
| R4 | remove the refusal at BOTH call sites | done | commit `90e49d979`; VALIDATION.md S2 (compile_run_manifest) + S3 (preflight_harness) |
| R5 | "Both sites CONVERT to a typed disclosure notice recorded alongside the compiled manifest / preflight result" | done-with-assumption A3 | VALIDATION.md S2/S3 |
| R6 | "The stub ceases to refuse anything; delete it or absorb it into the notice construction" | done-with-assumption A1, A2 | commit `90e49d979` (authority.py docstring); VALIDATION.md S4 |
| R7 | grep-proof every reader of CALIBRATION_RECEIPT / calibration_receipt_is_verified before declaring vestigial | done | SPEC.md §1, pasted census — field confirmed NOT vestigial, stays parseable, unchanged |
| R8 | llm/adapter.py's transaction_authority_required guard / defended-trial wiring NOT in scope | done | VALIDATION.md "Requirement sweep" R8 — `git diff --stat` confirms zero touch |
| R9 | frozen-surface grant scoped to surface 4, run_manifest.py, exactly the call-site conversion | done | VALIDATION.md "Frozen-surface diff" — exactly `run_manifest.py`, 38 insertions/7 deletions |
| R10 | every test flips (never deleted), enumerated in SPEC.md first, updated in the same commit | done | SPEC.md S5 (enumerated); commit `90e49d979` (same commit as the code); VALIDATION.md S1/S5 |
| R11 | old roots replay byte-unchanged, targeted verify_root_report as PROOF | done | VALIDATION.md "Record-behavior preservation" — `violations: []` on a pre-existing v6 root |
| R12 | ERRATA entry if any doc claims the mechanism worked, else scan-and-paste | done (no entry needed) | SPEC.md §3, VALIDATION.md S10 — scan pasted, no false claim found |
| R13 | ring while iterating, full gate once at boundary | done | VALIDATION.md "Full gate" — 3539 passed, 0 unexpected failed |
| R14 | map documents move in the same commits as the code | done | commit `90e49d979` — CON-authority.md + SUB-manifest.md landed alongside run_manifest.py/authority.py/tests; SUB-adjudication.md checked, no change needed |
| R15 | commit and push every phase boundary | done | 12 commits this tranche, all pushed with retry, `git rev-parse HEAD origin/...` matches |
| R16 | deliver with R-by-R reconciliation and pasted gate output as PROOF | done | this table; VALIDATION.md throughout |

No amendments were made to REQUEST.md; no requirement is deferred.

## Assumptions the operator may override

A1: `text_status_authority_issues` (authority.py) is kept as a pure
issue-classifier and not deleted — only its caller's disposal of the
result changed from raise to notice.

A2: `calibration_receipt_is_verified` is completely unchanged — it
remains the safety net for `ops.review_infrastructure` and the two
scheduler call sites that never reach a manifest at all.

A3: the "preflight result" the request's R5 names is `preflight_harness`'s
own return value (widened from always-`None` to
`tuple[CompileNoticeV1, ...]`) — not extended into printing or logging at
`ops.py`/`cli/main.py` call sites, which is PARKED below rather than
built here.

A4: surface 4 alone is sufficient — no second frozen surface is
contacted (confirmed by census + code reading).

## Map delta

Changed: `docs/map/CON-authority.md` (rewrote the "fail closed twice"
paragraph into a disclosure description, corrected one Traps entry, one
new `check:` line proving `compile_run_manifest` emits the notice, not a
raise), `docs/map/SUB-manifest.md` (split the "What is refused" row into
a refusal row and a new "What is DISCLOSED" row). Created: none. New
checks added: 1 (`CON-authority.md`'s new `check:` line — would fail if
the disclosure regressed back to a refusal). Left stale: none —
`python tools/docs_verify.py --stale` reports 0 documents worth
re-reading.

## Errata

None. The scan (SPEC.md §3, re-run at validation, VALIDATION.md S10)
found no committed document claiming the calibration receipt was ever a
working, satisfiable mechanism, or that `trial_required` was reachable
via this path — `CON-authority.md` already stated the true, unflattering
fact ("`calibration_receipt_is_verified` returns `False` unconditionally
today: no receipt verifier exists") before this tranche started, and
still does. `docs/ERRATA.md` tail re-read through E24; next free number
would be E25 if this tranche ever needed one.

## Parked (not done, not promised)

P1 — `preflight_harness`'s returned notices are not printed or logged at
any caller (`ops.run_scheduler`, `cli/main.py`'s `reason`/`continue`
commands). The information is available to any code that reads the
return value (tests do; a script could) but not yet visible to an
operator watching stderr the way `cli/main.py:857` already surfaces
`compile_run_manifest`'s notices. Full ready-to-send prompt in
`PARKED.md`.

recommended next: P1, if the operator wants live-run visibility into
this disclosure — otherwise no action needed; nothing is broken by
leaving it parked, since a compiled manifest already carries the
compile-time half of the same information for schema v6 runs.

## PROOF (gate output, not the word "done")

```
python -m pytest tests/ -q -n 4
1 failed, 3539 passed, 7 skipped in 729.58s (0:12:09)
  FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
  (documented pre-existing baseline — CLAUDE.md: "1 pre-existing
  test_bronze_report failure")

python tools/docs_verify.py
docs_verify: 3 failed
  (all CON-run-identity.md — documented pre-existing baseline —
  CLAUDE.md: "3 pre-existing CON-run-identity.md shallow-clone failures")

python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)

python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 53 document(s)

python tools/docs_verify.py --stale
docs_verify --stale: 0 document(s) worth re-reading

python -m pytest tests/test_manifest_integration.py -q
17 passed in 0.27s

verify_root(known-good v6 root)['violations']
[]
```

Everything above is reproducible from the branch head; full detail in
VALIDATION.md.
