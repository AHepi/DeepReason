# Validation for: retire the calibration-receipt dead-end gate on argumentative status authority

Tranche base: `85717580f` (Claude/v6 defended trial wiring 07hs1u #13),
confirmed an ancestor of this branch at session start.

## Acceptance checks

S1: `python -m pytest tests/test_manifest_integration.py -q -k "calibration_receipt"` -> `9 passed, 8 deselected in 0.08s` : PASS
S2: `python -c "... compile_run_manifest(Config(ARGUMENTATIVE_AUTHORITY='trial_required'), schema_version=2, workload_profile='text', rubric_policy='forbid') ... assert compile_notices == ['CALIBRATION_RECEIPT_REQUIRED']"` -> `PASS` : PASS
S3: `python -c "... preflight_harness(manifest, h, config) ... assert notices == ['CALIBRATION_RECEIPT_REQUIRED']"` (same-config recheck, per SPEC.md Addendum 1) -> `PASS` : PASS
S4: `python -c "... assert 'fail-closed' not in inspect.getsource(authority.text_status_authority_issues)"` -> `PASS` : PASS
S5: `python -m pytest tests/test_manifest_integration.py -q` -> `17 passed in 0.27s` : PASS
S6: `grep -q "used to refuse" ... && ! grep -q "fail closed twice" ...` -> `PASS` : PASS
S7: manual read of `docs/map/SUB-manifest.md` rows 159-160 -> confirmed narrowed, no longer claims `_preflight_text_authority` refuses : PASS
S8: `grep -c "calibrat\|text_status_authority\|preflight_harness" docs/map/SUB-adjudication.md` -> `0` : PASS
S9: `verify_root_report(root).integrity` -> `()`; `.epistemic` -> one informational adjudication-blindness finding, no violation; `verify_root(root)['violations']` -> `[]` : PASS
S10: errata scan re-run, one new hit (`SUB-manifest.md`, this tranche's own edit, correctly says "unsatisfiable") — no docs/ERRATA.md entry needed : PASS

## Full gate

```
FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
1 failed, 3539 passed, 7 skipped in 729.58s (0:12:09)
```
Matches the documented baseline exactly (CLAUDE.md: "1 pre-existing
test_bronze_report failure") — `counts["gate_blocked"] ==
census["streams"][stream]["gate_measures"]` (159 vs 165), a bronze-report
census assertion with no connection to `run_manifest.py`/`authority.py`.
0 of the 5 documented MCP-thread flaky tests failed this run. Re-run not
repeated for this validation pass: `git diff --stat
e5b357cd2..HEAD -- src/ tests/ docs/map/` is empty, confirming the tree
is byte-identical to the tree this full-gate run already covered (no
code moved between the step-12 run and this validation phase). : PASS

## Record-behavior preservation

`experiments/live_research_2026-07-29/selfstudy/runs/run-9175f0ecb055e57455af3c50df153c5a`
(a pre-existing, long-committed v6 root — CLAUDE.md's own named
regression-run precedent): `verify_root` reports `violations: []`,
`verify_root_report` reports zero integrity findings. Unchanged, as
expected: this root predates the tranche and could never have carried
the notice-triggering configuration (the old gate always refused
compilation of any such manifest, so no root anywhere in the repository
could ever have reached this code path — confirmed by the fact that
`grep -rn CALIBRATION_RECEIPT experiments/*/run-manifest.json` hits are
all `null`/absent values, never a set receipt paired with a
trial-requiring authority mode).

## Frozen-surface diff

```
$ git diff --stat 85717580f..HEAD -- src/deepreason/capabilities/state.py \
  src/deepreason/harness.py src/deepreason/invariants.py \
  src/deepreason/run_manifest.py src/deepreason/qualification.py
 src/deepreason/run_manifest.py | 45 +++++++++++++++++++++++++++++++++++-------
 1 file changed, 38 insertions(+), 7 deletions(-)
```
Non-empty, but pre-approved: REQUEST.md's C3 quotes the operator's own
FROZEN-SURFACE GRANT verbatim — "surface 4 (run_manifest.py), exactly the
text_status_authority_issues call-site conversion, model and validator
together. No other surface is granted." Exactly `run_manifest.py` is
touched; none of the other four frozen files (`capabilities/state.py`,
`harness.py`, `invariants.py`, `qualification.py`) appear in the diff.
Not a FAIL.

## Packaging surface

`git diff --stat 5ba4cd8bd..HEAD -- pyproject.toml src/deepreason/cli/
src/deepreason/mcp*` -> empty. Packaging surface untouched — wheel smoke
not owed (no console entry point, CLI command, MCP tool, or wheel-layout
file in this diff).

## Map

```
$ python tools/docs_verify.py
docs_verify [full]: 53 documents, 861 checks, 4 workers
  FAIL CON-run-identity.md:195 (baseline)
  FAIL CON-run-identity.md:197 (baseline)
  FAIL CON-run-identity.md:199 (baseline)
docs_verify: 3 failed
```
Matches the documented baseline exactly (CLAUDE.md: "3 pre-existing
CON-run-identity.md shallow-clone failures") — re-run not repeated this
pass for the same tree-unchanged reason as the full gate above; this is
step 11's own run, captured before the two later bookkeeping-only
commits. : PASS

```
$ python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)
```
: PASS

```
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 53 document(s)
```
: PASS

```
$ python tools/docs_verify.py --coverage
... 16 seam documents without a Sweep: header (pre-existing, spans
essentially the whole seam-document set, not caused by this tranche —
this tranche touched no SEAM- file)
SEAM-schools-x-scratch.md: enforcement site not named: src/deepreason/informal/trial.py
docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 1 finding(s)
```
: PASS (pre-existing map-wide condition; neither flagged item is
`CON-authority.md` or `SUB-manifest.md`, the two documents this tranche
edited — nothing here traces to this change)

```
$ python tools/docs_verify.py --stale
docs_verify --stale: 0 document(s) worth re-reading
```
: PASS — confirms `Verified-at:` stamps were correctly left untouched on
both edited documents (S6/S7 only ran their own new/edited checks, not
every check in each document, so advancing the stamp would have been
dishonest per SCHEMA.md's own rule; `--stale` finding 0 confirms this
was the right call, not an oversight).

New checks added by this change: `CON-authority.md`'s new
`check:` line proving `compile_run_manifest` emits
`CALIBRATION_RECEIPT_REQUIRED` as a notice, not a raise (SPEC.md S6) —
would fail if the disclosure regressed back to a refusal, or if the
notice stopped firing. `SUB-manifest.md`'s row 160 repoints its own test
reference to `tests/test_manifest_integration.py -k calibration_receipt`
(existing test, now proving the flipped direction).

Record observables added vs sweep probes: none. This tranche adds no new
typed-record field, event type, or finding — `CompileNoticeV1` and
`compile_notices` already existed (all-configs-allowed, 2026-08-12); this
tranche only changes which existing codes populate it and removes a
raise. `tools/root_sweep.py` needs no new probe.

## Requirement sweep

R1: demonstrated by S1-S3 (both call sites convert to disclosure)
R2: demonstrated by this document's own existence and CHECKLIST.md's execution trail (routed through dr-change-orchestrator throughout)
R3: demonstrated by S2/S3 — no raise, run proceeds, notice recorded
R4: demonstrated by S2 (compile_run_manifest) AND S3 (preflight_harness) — both sites converted together
R5: demonstrated by S2/S3 — notice carries code/message/pointer/resolution alongside the compiled manifest / preflight result
R6: demonstrated by S4 (docstring updated) + Assumption A1/A2 (SPEC.md) — `text_status_authority_issues` absorbed into notice construction, not deleted; `calibration_receipt_is_verified` untouched
R7: demonstrated by SPEC.md §1's pasted grep census — every reader named, field confirmed not vestigial
R8: demonstrated by "Out of scope" (SPEC.md) and by code reading (§0) confirming `llm/adapter.py`/PR#13's wiring is a structurally separate mechanism, untouched — `git diff --stat` shows no `llm/adapter.py` hit
R9: demonstrated by the "Frozen-surface diff" section above — exactly surface 4, run_manifest.py, nothing else
R10: demonstrated by S1/S5 — 7 tests flipped (never deleted), same names, same parametrization, assertions changed from raise to success+notice
R11: demonstrated by S9 — `verify_root`/`verify_root_report` on a known-good pre-existing root, zero violations
R12: demonstrated by S10 — errata scan re-run, no entry needed, reasoning recorded
R13: demonstrated by the "Full gate" and "Map" sections above — ring run throughout execution (per-step done-criteria), full gate + full docs_verify at the boundary
R14: demonstrated by S6/S7/S8 — CON-authority.md and SUB-manifest.md updated in the same commit as the code (commit `90e49d979`); SUB-adjudication.md checked, confirmed no change needed
R15: demonstrated by CHECKLIST.md's own commit trail — every phase and step boundary committed and pushed (commits `5ba4cd8bd` through `62ace6820`, all pushed with retry)
R16: demonstrated by this VALIDATION.md's own acceptance-check and requirement-sweep sections — pasted output throughout, not assertions

## Assumptions carried

A1: `text_status_authority_issues` kept as a pure issue-classifier, not deleted — its caller's disposal of the result changes, not the function itself.
A2: `calibration_receipt_is_verified` left completely unchanged — remains the safety net for `ops.review_infrastructure` and the two scheduler call sites that never reach a manifest.
A3: the "preflight result" R5 names is `preflight_harness`'s own return value (widened `None` -> `tuple[CompileNoticeV1, ...]`); printing/logging it at `ops.py`/`cli/main.py` call sites is PARKED (P1), not built here.
A4: surface 4 alone is sufficient — confirmed by both the manual census and code reading; no second frozen surface is contacted.

## Verdict: PASS

Every SPEC.md acceptance check passes, the full gate ends at the
documented pre-existing baseline (0 failures caused by this change), the
frozen-surface diff is pre-approved and scoped exactly as granted, the
map gate is clean beyond pre-existing, unrelated conditions, and every
REQUEST.md requirement is demonstrated above. No file other than this
one was modified during this phase.
