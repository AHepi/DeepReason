# Spec for: retire the calibration-receipt dead-end gate on argumentative status authority
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight (dr-drive-harness §4): resolved ids —
`DR-CON-authority` (src/deepreason/authority.py, run_manifest.py's
authority-relevant functions), `DR-SUB-manifest` (src/deepreason/run_manifest.py
generally), `DR-SUB-adjudication` (src/deepreason/adjudication/ — checked,
owns nothing this change touches), `DR-INV-frozen-surfaces` surface 4
(manifest schemas AND validators, run_manifest.py). No `DR-SEAM-authority-x-manifest`
document exists — `CON-authority.md`'s own header already lists
`Seams-undocumented: authority x manifest, authority x rules, authority x
scheduler`, so this is a pre-existing, already-disclosed gap, not one this
change discovers. See "Map delta" below for the resolution.

## 0. What the current code does (read before any edit)

Two call sites share ONE helper, `_preflight_text_authority` (run_manifest.py):

- `compile_run_manifest` calls it at line 3310, before route resolution
  ("This must precede route resolution: a rejected authority policy cannot
  spend an endpoint/model-discovery call merely to learn that it is unsafe").
- `preflight_harness` calls it at lines 4066-4070, as a re-check against the
  LIVE `Config` (which can differ from the config the manifest was compiled
  under, e.g. after a resume) before the adapter is built.

The helper (lines 4023-4037) calls `authority.py::text_status_authority_issues`,
which is UNCONDITIONAL whenever `ARGUMENTATIVE_AUTHORITY` is
`trial_required`/`single_family_trial`, or any of the three surface knobs
(`TEXT_RUBRIC_AUTHORITY`/`PAIRWISE_AUTHORITY`/`INFRASTRUCTURE_REVIEW_AUTHORITY`)
is `calibrated_status`: it ALWAYS appends an `AuthorityPolicyIssue`
(`CALIBRATION_RECEIPT_REQUIRED` if no receipt string is set,
`CALIBRATION_RECEIPT_UNVERIFIED` if one is) — it never calls
`calibration_receipt_is_verified` at all, because no receipt value could
ever change the outcome. `_preflight_text_authority` then raises
`RunManifestError` on the first issue. **Confirmed: no `CALIBRATION_RECEIPT`
value, real or fabricated, can ever avoid this refusal** — this is the
"dead-end denial" REQUEST.md names.

Separately (and NOT part of this refusal, NOT touched by this change):
`authority.py::trial_authority_for` (the RUNTIME per-call authority
resolver used by `rules/crit.py`, `informal/trial.py`,
`ops.review_infrastructure`, and the scheduler's rubric/pairwise call
sites) calls `calibration_receipt_is_verified(config)` directly and falls
back to `TrialAuthority.OBSERVE_ONLY` when it returns `False` (always).
This is the SAFE, already-existing fallback CON-authority.md's Traps
section documents as "the entire gate" for the three paths that never go
through `compile_run_manifest`/`preflight_harness` at all. This tranche
does not touch `trial_authority_for` or `calibration_receipt_is_verified`'s
behavior — only the redundant hard-refusal at the two manifest-preflight
call sites, which duplicated a check that the runtime path already handles
safely.

## 1. Census (R7) — every reader of CALIBRATION_RECEIPT / calibration_receipt_is_verified

Pasted `grep -rn` output, every hit, src/scripts/tools only (test hits
enumerated separately in §4):

```
$ grep -rn "CALIBRATION_RECEIPT" --include="*.py" src/ scripts/ tools/
src/deepreason/authority.py:163:    value = _get(config, "CALIBRATION_RECEIPT", None)
src/deepreason/authority.py:192:                    "CALIBRATION_RECEIPT_REQUIRED",
src/deepreason/authority.py:193:                    "text prose status authority requires CALIBRATION_RECEIPT",
src/deepreason/authority.py:194:                    "/engine_config/CALIBRATION_RECEIPT",
src/deepreason/authority.py:200:                    "CALIBRATION_RECEIPT_UNVERIFIED",
src/deepreason/authority.py:202:                    "/engine_config/CALIBRATION_RECEIPT",
src/deepreason/authority.py:212:                        "CALIBRATION_RECEIPT_REQUIRED",
src/deepreason/authority.py:213:                        f"{field}=calibrated_status requires CALIBRATION_RECEIPT",
src/deepreason/authority.py:214:                        "/engine_config/CALIBRATION_RECEIPT",
src/deepreason/authority.py:220:                        "CALIBRATION_RECEIPT_UNVERIFIED",
src/deepreason/authority.py:222:                        "/engine_config/CALIBRATION_RECEIPT",
src/deepreason/authority.py:237:        "CALIBRATION_RECEIPT": calibration_receipt(config),
src/deepreason/config.py:373:    # CALIBRATION_RECEIPT before any endpoint is built.  observe_only records
src/deepreason/config.py:394:    CALIBRATION_RECEIPT: str | None = None
src/deepreason/jolts.py:662:    if config.CALIBRATION_RECEIPT is not None:
src/deepreason/jolts.py:663:        raise JoltError("JOLT_CALIBRATION_RECEIPT_FORBIDDEN")

$ grep -rn "calibration_receipt_is_verified" --include="*.py" src/ scripts/ tools/
src/deepreason/authority.py:128:            if calibration_receipt_is_verified(config)
src/deepreason/authority.py:140:def calibration_receipt_is_verified(config) -> bool:
```

**Reading:** `CALIBRATION_RECEIPT` (the `Config` field) has exactly two
consumer families: `authority.py` (the block this tranche touches:
`calibration_receipt()`, `text_status_authority_issues()`,
`authority_policy_snapshot()`) and `jolts.py`'s `JOLT_CALIBRATION_RECEIPT_FORBIDDEN`
(a jolt-pilot precondition — a jolt run must declare NO status authority
at all; unaffected, since it forbids the field being set, not the
verification outcome). `calibration_receipt_is_verified` has exactly ONE
caller, `trial_authority_for` (line 128) — the runtime fallback path,
explicitly out of scope per C2/§0 above. **The field is not vestigial**
(R7): it remains fully read, fully parseable, and this tranche does not
touch `config.py`'s field definition at all.

## 2. The shape

Both call sites CONVERT `_preflight_text_authority`'s raise into
`CompileNoticeV1` notices (the existing all-configs-allowed model, no new
model needed — `run_manifest.py:1167`), reusing the exact
`(code, message, pointer)` triple `AuthorityPolicyIssue` already carries,
plus a `resolution` string naming the safe fallback that already applies
today via `trial_authority_for`. `text_status_authority_issues` itself is
UNCHANGED — it stays a pure, testable "what the old rule would have
flagged" classifier (Assumption A1); only what its caller DOES with the
result changes, at both of the two run_manifest.py call sites.

## Items

S1 (R4, R5, R6, R9): `src/deepreason/run_manifest.py::_preflight_text_authority`
(lines 4023-4037) | before: raises `RunManifestError(issue.code, ...)` on
the first `AuthorityPolicyIssue`, refusing compilation/preflight |
after: takes an optional `notices: list[CompileNoticeV1] | None = None`
keyword parameter (mirrors `_compile_bridge_policy`'s existing pattern,
line 2620); when given, converts EVERY issue `text_status_authority_issues`
returns into a `CompileNoticeV1` via the existing `_emit_compile_notice`
helper (line 1180), with `resolution="status authority stays observe_only
for this surface until a calibration-receipt verifier exists"`; never
raises for these codes again.
    accept: `python -m pytest tests/test_manifest_integration.py -q -k
    "calibration_receipt"` -> all pass, 0 raise on these codes

S2 (R4, R5): `compile_run_manifest`'s call site (line 3310) | before:
`_preflight_text_authority(config, schema_version, workload_profile)` |
after: `_preflight_text_authority(config, schema_version, workload_profile,
notices=notices)` (the `notices: list[CompileNoticeV1]` sink already
constructed at line 3176 and already threaded through every other
converted code in this function).
    accept: `python -c "from deepreason.config import Config; from
    deepreason.run_manifest import compile_run_manifest; m =
    compile_run_manifest(Config(ARGUMENTATIVE_AUTHORITY='trial_required'),
    schema_version=2, workload_profile='text'); assert [n.code for n in
    m.compile_notices] == ['CALIBRATION_RECEIPT_REQUIRED'], m.compile_notices"`

S3 (R4, R5): `preflight_harness` (lines 4058-4130) | before: returns `None`
implicitly, calls `_preflight_text_authority(config, manifest.schema_version,
manifest.workload_profile)` with no sink, discarding the issues entirely |
after: return type becomes `tuple[CompileNoticeV1, ...]`; builds a local
`notices: list[CompileNoticeV1] = []`, passes it to
`_preflight_text_authority`, and returns `tuple(notices)` at the function's
end (after every other still-live raise in the function — the property/
rubric refusals below it in the same function stay untouched, out of
scope). The docstring gains one paragraph stating the return value now
carries this disclosure and why (manifest is already frozen, so it cannot
gain a fresh `compile_notices` entry after the fact). Every existing
caller (`ops.py:372`, `scripts/jolt_positive_headroom_v3_1.py:280`,
`scripts/jolt_trigger_glm52_pilot.py:324`) calls this as a bare statement
today and is unaffected by a return-type widening from `None` to a tuple
they already discard.
    accept: `python -c "from deepreason.config import Config; from
    deepreason.harness import Harness; from deepreason.run_manifest import
    compile_run_manifest, preflight_harness; import tempfile, pathlib; m =
    compile_run_manifest(Config(), schema_version=2, workload_profile='text');
    unsafe = Config(TEXT_RUBRIC_AUTHORITY='calibrated_status'); h =
    Harness(pathlib.Path(tempfile.mkdtemp())/'run'); notices =
    preflight_harness(m, h, unsafe); assert [n.code for n in notices] ==
    ['CALIBRATION_RECEIPT_REQUIRED'], notices"`

S4 (R6): `src/deepreason/authority.py` docstrings only | before:
`text_status_authority_issues`'s docstring says "A receipt reference is a
fail-closed gate for this tranche" (stale — nothing fails closed on this
path anymore) | after: docstring updated to say the issues are now
disclosed as notices by the manifest-side callers rather than causing a
refusal, and why (no configuration can ever satisfy
`calibration_receipt_is_verified`, so refusing was a dead end, not a real
point-of-use failure). `calibration_receipt_is_verified`'s own docstring
and the function itself are UNCHANGED (Assumption A2) — it remains the
one attachment point for a future verifier and the entire safety net for
`ops.review_infrastructure` and the two scheduler call sites (CON-authority.md
Traps, unaffected by this tranche).
    accept: `python -c "import inspect; from deepreason import authority;
    assert 'fail-closed' not in inspect.getsource(authority.text_status_authority_issues)"`

S5 (R10): `tests/test_manifest_integration.py` | before: 7 test functions
(2 parametrized ×4 cases, `test_blank_calibration_receipt_is_missing`,
`test_materialized_text_status_authority_is_rechecked_before_adapter_build`,
`test_runtime_calibrated_status_is_unverified_before_adapter_build`) assert
`pytest.raises(RunManifestError, match=<code>)` | after: every one flips to
calling `compile_run_manifest`/`preflight_harness` normally (no raise) and
asserting the returned/attached notices carry the same code the retired
raise used to. Test names, parametrization, and configs are UNCHANGED —
only the assertion shape flips, per R10's "never weakened... a test
deleted instead of flipped." `test_runtime_cannot_mutate_frozen_text_authority_policy`
(TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH) is UNTOUCHED — frozen-record
protection, explicitly out of scope (C3, and the operator's own
"STAYS" classification of this exact code in the prior tranche's census,
`experiments/2026-08-12-change-all-configs-allowed/SPEC.md` line 228).
    accept: `python -m pytest tests/test_manifest_integration.py -q` ->
    all pass, 0 failed, 0 skipped

S6 (R14): `docs/map/CON-authority.md` | before: "Where it lives" row 95
names `_preflight_text_authority`/`preflight_harness` only as "Compile-time
and pre-adapter preflight" (still true, unchanged label); "The rules it
obeys" (lines 194-199) states "Manifest-mediated runs fail closed twice:
at compile, and again before the adapter is built" for exactly these two
codes (now FALSE — this is the claim this tranche falsifies); Traps entry
(lines 242-248) "Assuming the manifest preflight covers every path" says
`text_status_authority_issues` "refuses an unverified receipt" (now
imprecise — it still generates the issue, but the manifest-side callers no
longer refuse on it) | after: the "fail closed twice" paragraph rewritten
to describe the notice, with a new `check:` proving `compile_run_manifest`
no longer raises for these codes; the Traps entry's phrasing corrected
("the function that used to refuse an unverified receipt" or equivalent,
dated). `check: python -m pytest tests/test_manifest_integration.py -q -k
calibration_receipt` (existing check line 199, still valid, now proving
the opposite direction — success, not raise).
    accept: `python tools/docs_verify.py` -> 0 new failures beyond the
    documented baseline (3 pre-existing CON-run-identity.md shallow-clone
    failures)

S7 (R14): `docs/map/SUB-manifest.md` | before: line 159's "Where to change
what" row, "What is refused before the first provider call |
`preflight_payload`, `preflight_harness`, `_preflight_text_authority`" —
now FALSE for the calibration-receipt codes specifically (the row's other
two refusal families — rubric-forbid, property-rubric-trial — are
unaffected and still true); lines 69-71's one-line summary of
`preflight_harness`'s purpose says "text status authority drift" which
refers to the STILL-refusing `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`
check, so it stays accurate and needs no edit | after: line 159's row
narrowed to name only the checks that still refuse at that boundary, with
a forward pointer to `DR-CON-authority` for what the calibration-receipt
codes now do instead.
    accept: `python tools/docs_verify.py` -> 0 new failures beyond baseline

S8 (R14, process only — no file change): `docs/map/SUB-adjudication.md` |
checked against `Owns: src/deepreason/adjudication/` — neither
`run_manifest.py` nor `authority.py` is owned or referenced by this
document; no claim in it describes the calibration-receipt refusal.
Nothing to falsify, nothing to move. Recorded here (not silently
skipped) because REQUEST.md named this document explicitly.
    accept: `grep -c "calibrat\|text_status_authority\|preflight_harness"
    docs/map/SUB-adjudication.md` -> `0`

S9 (R11): targeted `verify_root_report` on one known-good committed root,
run at `dr-validate-change` time (after the code lands), pasted as PROOF —
demonstrates the change is invisible to replay. Root chosen at execution:
any committed root whose manifest is openable (the change touches no
digest, no event-application order, and no schema field — old roots were
NEVER able to reach the notice-triggering condition in the first place,
since the condition always raised before any such root could be
committed, so byte-identity is expected trivially, not merely hoped for).
    accept: `python -c "from deepreason.verification.report import
    verify_root_report; import json; print(json.dumps(verify_root_report('<root>'),
    default=str)[:200])"` -> no exception, `valid` unchanged from the
    pre-change baseline

S10 (R12): errata scan (see §3 below) — pasted command + output.

## Assumptions (operator may override)

A1 (R6): `text_status_authority_issues` (authority.py) is KEPT as a pure
issue-classifier and NOT deleted; only its caller's disposal of the
result changes (raise -> notice). Chosen over literal deletion because
(a) the function has exactly one caller (`_preflight_text_authority`) so
deleting it would only relocate its ~25 lines of branching inline with no
behavioral difference, and (b) REQUEST.md's own line-range citation for
"the stub" (`authority.py`, "lines ~140-225") spans from
`calibration_receipt_is_verified` (140) through the end of
`text_status_authority_issues` (225) — i.e. names the whole dead-end
BLOCK, not literally the one-line stub function — so "absorb it into the
notice construction" is the reading this SPEC adopts: the block's output
is absorbed into notices, the block's code is not deleted line-for-line.
Smallest reasonable interpretation; not material (same files touched
either way).

A2 (R6, C2): `calibration_receipt_is_verified` itself is UNCHANGED —
still always `False`, still the single attachment point for a future
verifier, still the entire safety net for `ops.review_infrastructure` and
the two scheduler call sites that never reach a manifest at all
(CON-authority.md Traps: "On those three paths `calibration_receipt_is_verified`
is the entire gate"). Deleting or altering it would remove that safety
net for paths this tranche has no authorization to touch (C2's "do not
touch" boundary, read as covering the whole runtime-authority fallback
mechanism, not only `llm/adapter.py` literally). Not material: the
alternative (inlining `False` at its one call site) touches the same file
for the same reason with no behavioral difference to anything in scope.

A3 (Q2): the "preflight result" R5 says the disclosure is recorded
"alongside" is `preflight_harness`'s own return value (S3) — the function
already returns nothing meaningful (`None`) today, so widening it to a
typed tuple is the direct, minimal analogue of `compile_run_manifest`
returning a manifest with `.compile_notices`. Not extended into printing
or logging at `ops.py`/`cli/main.py` call sites: R5's text names the
compiled manifest and the preflight *result*, not every caller's display
layer, and this repo's own precedent (compile_notices are dropped from
`canonical_bytes`/the persisted `run-manifest.json` for schema_version<6,
i.e. even the EXISTING compile-time notice mechanism is not universally
persisted or displayed today) shows an in-memory typed value, uncaptured
by most callers, is already the accepted shape for this kind of
disclosure. A future tranche wiring `ops.run_scheduler`/`cli/main.py` to
print `preflight_harness`'s notices (mirroring `cli/main.py:857`'s
existing `NOTICE {code}: {message}` stderr print for compile_notices) is
a natural follow-up, PARKED below, not built here.

A4 (Q3): surface 4 alone is sufficient — confirmed by both the manual
census (§1) and the blast-radius tool's `frozen_surface_contacts` (§Frozen-surface
contact forecast below): every reader of `CALIBRATION_RECEIPT` /
`calibration_receipt_is_verified` outside `run_manifest.py` either belongs
to the explicitly-out-of-scope runtime fallback (`trial_authority_for` and
its three callers) or to an unrelated jolt precondition (`jolts.py`). No
second frozen surface is contacted.

## Questions for operator

(none — every open question from REQUEST.md resolved above as an
assumption; none differ materially in files touched or effort)

## Out of scope (explicit)

- `llm/adapter.py`'s `transaction_authority_required` guard and the
  defended-trial transactional wiring (PR #13) — C2, untouched; confirmed
  by code reading (§0) that it is a structurally separate mechanism
  (`CriticismPolicyV1.authority` manifest vocabulary) from the
  `ARGUMENTATIVE_AUTHORITY` Config vocabulary this tranche's refusal reads.
- `trial_authority_for` / `calibration_receipt_is_verified`'s runtime
  fallback behavior for `ops.review_infrastructure` and the two scheduler
  call sites — A2, untouched; remains the safety net CON-authority.md
  documents.
- Every OTHER refusal code the prior all-configs-allowed tranche catalogued
  as `CONVERT-SPEC'D` but not yet converted (`RUBRIC_INPUT_FORBIDDEN`,
  `PROPERTY_RUBRIC_TRIAL_FORBIDDEN`, `V4_SCHOOL_ROLE_UNSUPPORTED` cluster,
  `V4_CRITICISM_ACTIVE_REQUIRED` cluster, etc.) — not requested here;
  REQUEST.md names only the calibration-receipt codes.
- Printing/logging `preflight_harness`'s new return value at `ops.py`/
  `cli/main.py` call sites — A3, PARKED (see PARKED.md).
- Creating a `SEAM-authority-x-manifest.md` document — the pair is
  pre-existing-undocumented per `CON-authority.md`'s own header, and this
  narrow call-site conversion does not newly create or measurably widen
  the `authority.py` x `run_manifest.py` coupling (same two functions
  call the same one function as before; only what the caller does with
  the result changes). Writing a full seam document (coupling
  measurement + write-up per `SCHEMA.md`) for a change this narrow would
  be disproportionate, mirroring `CON-authority.md`'s own precedent of
  documenting the "adjacent, not authority" hygiene fix for
  `v6_policy.py`/`preparation.py` in-place rather than opening a new file
  for a small addition with no better home.

## Frozen-surface contact forecast

`python tools/blast_radius.py --files src/deepreason/run_manifest.py
src/deepreason/authority.py --symbols _preflight_text_authority
preflight_harness compile_run_manifest text_status_authority_issues
calibration_receipt_is_verified` (full JSON in this tranche's working
notes; `frozen_surface_verdict` and `frozen_surface_contacts` pasted
verbatim below, per the gate's own requirement):

```
"frozen_surface_verdict": "CONTACT"
"frozen_surface_contacts": [
  {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "DIRECT",
   "target": "src/deepreason/run_manifest.py",
   "detail": "target file is surface path src/deepreason/run_manifest.py"},
  {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "SYMBOL_INDIRECT",
   "target": "_preflight_text_authority",
   "detail": "'_preflight_text_authority' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"},
  {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "SYMBOL_INDIRECT",
   "target": "preflight_harness",
   "detail": "'preflight_harness' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"},
  {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "SYMBOL_INDIRECT",
   "target": "compile_run_manifest",
   "detail": "'compile_run_manifest' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"},
  {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "SYMBOL_INDIRECT",
   "target": "text_status_authority_issues",
   "detail": "'text_status_authority_issues' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"}
]
"frozen_adjacent_contacts": []
```

**This is EXPECTED, not a stop.** It is exactly surface 4
(`run_manifest.py`, manifest schemas AND validators), and REQUEST.md's own
FROZEN-SURFACE GRANT (C3, ledgered above) pre-authorizes precisely this
contact: "surface 4 (run_manifest.py), exactly the
`text_status_authority_issues` call-site conversion, model and validator
together." The "model" (`CompileNoticeV1`) is UNCHANGED (already exists,
already used by six other converted codes); only the "validator"
(`_preflight_text_authority`'s disposal of `text_status_authority_issues`'s
output) changes — both move together in the same commit, satisfying the
grant's own condition and `INV-frozen-surfaces.md`'s Trap ("Reading a
model and not its validator"). No `frozen_adjacent_contacts` (the
`route_fingerprint` frozen-adjacent surface is untouched). No other
frozen surface (1, 2, 3, 5) is contacted by any file this SPEC touches.

## Blast-radius census

Tool-backed `consumers.tests` / `consumers.map_checks`, every hit
classified (full tool JSON in working notes; the two targets this tranche
actually changes are `_preflight_text_authority` and `preflight_harness` —
`compile_run_manifest`'s ~160 test hits are `text_status_authority_issues`'s
grandparent function and are listed for completeness, but the change to
it is a one-line call-site edit passing an already-existing `notices`
sink, so only tests that construct a manifest WITH a triggering
`ARGUMENTATIVE_AUTHORITY`/surface-authority value are affected):

| Target | Hit | Classification |
|---|---|---|
| `preflight_harness` | `tests/test_manifest_integration.py:18,72,197,216,233` | EXPECTED TO MOVE — lines 72 (`# must not raise`, unaffected — no triggering config, stays passing as a bare statement) is MUST NOT MOVE; 197, 216 are the two tests S5 flips |
| `preflight_harness` | `tests/test_run_manifest.py:23,735,752` | MUST NOT MOVE — checked (§below): no triggering `ARGUMENTATIVE_AUTHORITY`/surface value in either call |
| `preflight_harness` | `tests/test_runtime_workload_integration.py:373,415` | MUST NOT MOVE — both monkeypatch `preflight_harness` itself (`unreachable(...)`, `lambda *_a: None`), never call the real function |
| `preflight_harness` | `tests/test_v6_global_dispatch_guard.py:106,234,278,967` | MUST NOT MOVE — all four monkeypatch `preflight_harness` with a forbidding stub or a no-op lambda; never exercise the real function's body |
| `compile_run_manifest` | ~160 hits across the test suite (full list in tool JSON) | MUST NOT MOVE, except `tests/test_manifest_integration.py`'s calibration-receipt tests (S5) — every other hit constructs a manifest with `ARGUMENTATIVE_AUTHORITY`/surface authority left at the default `observe_only`, so `text_status_authority_issues` returns no issues and `notices=notices` is a no-op passthrough for them |
| `text_status_authority_issues` | `docs/map/CON-authority.md:79,245` | EXPECTED TO MOVE — S6 |
| `calibration_receipt_is_verified` | `docs/map/CON-authority.md:64,66,77,177,180,219,239,247` | MUST NOT MOVE — A2, this function and every claim about it are unchanged |
| `src/deepreason/run_manifest.py` (file-level) | `docs/map/CON-authority.md`, `SUB-manifest.md`, `INV-frozen-surfaces.md`, `SEAM-bridge-x-manifest.md`, `SEAM-llm-x-manifest.md`, `SEAM-manifest-x-schools.md`, `CON-conjecture-kinds.md`, `CON-packs-and-token-economy.md`, `CON-run-identity.md`, `CON-schools.md`, `CON-seats.md`, `SUB-scheduler.md`, `SUB-scratch.md` | MUST NOT MOVE except `CON-authority.md` (S6) and `SUB-manifest.md` (S7) — every other hit is a generic `Owns:`/reference line unrelated to the calibration-receipt codes (checked individually via the grep census in §1 and manual reading, §0) |
| `src/deepreason/authority.py` (file-level) | `docs/map/CON-authority.md`, `SEAM-adjudication-x-authority.md`, `SUB-evaluation.md:177` | MUST NOT MOVE except `CON-authority.md` (S4/S6) — `SEAM-adjudication-x-authority.md:90`'s check exercises `trial_authority_for`, unaffected (A2); `SUB-evaluation.md:177` checked, unrelated (informal-trial evaluation topic, not this refusal) |

Manual cross-check (`grep -rn "<symbol>" tests/ docs/map/`) for the two
targets this tranche actually edits, confirming the tool's classification:

```
$ grep -n "ARGUMENTATIVE_AUTHORITY\|TEXT_RUBRIC_AUTHORITY\|PAIRWISE_AUTHORITY\|INFRASTRUCTURE_REVIEW_AUTHORITY" tests/test_run_manifest.py
(no output)
```

Confirms `tests/test_run_manifest.py`'s three `preflight_harness` calls
(lines 735, 752) never set a triggering authority value — MUST NOT MOVE,
as classified above.

## Measurements

(not DESIGN-AND-STOP — this SPEC both designs and implements in the same
tranche, per the routing table; measurements are inline in §0/§1/Frozen-
surface section above rather than a separate section)

## Budget

Itemized estimate (insertions only, matching `diff_budget.py`'s own
metric), scoped to the files this SPEC actually edits — `--paths
src/deepreason/run_manifest.py src/deepreason/authority.py
tests/test_manifest_integration.py docs/map/CON-authority.md
docs/map/SUB-manifest.md` (tranche narrative artifacts — REQUEST/SPEC/
CHECKLIST/VALIDATION/DELIVERY/PARKED — are not code and are not counted
against this ceiling, matching this repo's own precedent of scoping the
diff-budget gate to the surfaces a change actually claims):

- S1+S2 (`_preflight_text_authority` rewrite + call site): ~28 lines
- S3 (`preflight_harness` signature/docstring/return): ~20 lines
- S4 (`authority.py` docstring): ~12 lines
- S5 (`tests/test_manifest_integration.py`, 7 tests flipped): ~70 lines
- S6 (`docs/map/CON-authority.md`): ~50 lines
- S7 (`docs/map/SUB-manifest.md`): ~15 lines

```
$ python3 -c "print(28+20+12+70+50+15)"
195
```

~195 lines, well under the ~300-line split threshold — no sub-tranche
split proposed. Ceiling set at 260 (a ~33% buffer over the itemized
estimate, for docstring/comment prose that tends to run longer than
code). Frozen surfaces touched: **surface 4 only** (`run_manifest.py`),
pre-granted per C3 above. Estimated commits: 2 (one for S1-S5 — code +
tests move together per R10's "updated in the same commit as the site it
pins" — one for S6-S8, the map delta, per SCHEMA.md's "same commit as the
code" rule interpreted here as "the commit that makes the map's claims
true again," landing immediately after or combined with the first if the
diff stays small; final count decided at `dr-plan-steps`).

No wheel-smoke re-pin needed: `blast_radius.py`'s `wheel_smoke_pins` field
was empty for every target in this SPEC — neither `preflight_harness` nor
`_preflight_text_authority` is a console entry point or an MCP tool, and
their signatures are not part of the pinned public surface.

## 3. Errata scan (R12)

```
$ grep -rln "calibration.receipt\|CALIBRATION_RECEIPT" docs/
docs/map/SEAM-adjudication-x-authority.md
docs/map/CON-authority.md

$ grep -rln "trial_required" docs/
docs/map/SUB-workflow.md
docs/map/SEAM-rules-x-workflow.md
docs/map/CON-criticism-source.md
docs/map/CON-authority.md
docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md
```

Every hit read (§0 above cross-references the `trial_required` hits
against the SEPARATE `defended_trial`/PR#13 mechanism they actually
describe — none claims the Config-side `ARGUMENTATIVE_AUTHORITY=trial_required`
+ text-workload path was ever reachable). `CON-authority.md`'s own
existing text already states the true, unflattering fact plainly:
"`calibration_receipt_is_verified` returns `False` unconditionally today:
no receipt verifier exists" (line 177) — this is not a claim the
mechanism worked; it is the correct claim this whole tranche acts on.
**No document claims the calibration receipt was a working, satisfiable
mechanism, or that `trial_required` was reachable via this path. No
docs/ERRATA.md entry is needed.** (Next free number confirmed: E25 — tail
of `docs/ERRATA.md` re-read in full this session, last entry is E24.)

## Map delta (planned)

- `docs/map/CON-authority.md` — S6 (rewritten "fail closed twice"
  paragraph, corrected Traps entry, one new `check:`).
- `docs/map/SUB-manifest.md` — S7 (narrowed refusal-boundary row).
- `docs/map/SUB-adjudication.md` — S8, checked, no change (recorded, not
  silently skipped).
- No new seam document (see "Out of scope").

## Rubric pass

- every R has a spec item with a machine-decidable accept?: YES — R1-R2
  are process/routing (covered by this document's own existence and the
  orchestrator's routing table, not a code item); R3-R6, R9-R11 map to
  S1-S3, S9; R7 to §1; R8/C2 to "Out of scope"; R10 to S5; R12 to S10/§3;
  R13 covered by CHECKLIST/VALIDATION gate steps (not a SPEC item, a
  process obligation); R14 to S6-S8; R15-R16 are process, covered by the
  workflow's own commit/push and delivery phases.
- blast-radius census pasted (or pasted-empty) and every hit classified?:
  YES (§Blast-radius census).
- frozen-surface contact forecast recorded?: YES, tool output pasted
  verbatim (§Frozen-surface contact forecast).
- every mechanism the request names traced to code it actually reaches?:
  YES — both named call sites (compile_run_manifest ~4023-4037 in the
  request's line numbers, actually at 3310/4023-4037 in the current tree;
  preflight_harness) verified by direct reading in §0; the "stub... lines
  ~140-225" citation verified to span calibration_receipt_is_verified
  through text_status_authority_issues, informing A1.
- DESIGN-AND-STOP only: n/a, not a DESIGN-AND-STOP request.
- nothing in the spec untraceable to an R/C number?: YES, checked —
  every item and assumption above cites at least one R/C number.

Rubric: 5/5 yes

## Addendum 1 — execution discovery: the two `preflight_harness` tests' original scenario collides with an out-of-scope check

Found executing step 1 of CHECKLIST.md (code lands correctly; the
discovery is about the two tests S5/S3 planned to flip, not about the
code). Verbatim contradiction: `preflight_harness`'s body runs
`_preflight_text_authority` FIRST, then the separate
`TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH` check (`authority_policy_snapshot(config)
!= authority_policy_snapshot(frozen_config)`) SECOND. The two pre-existing
tests this SPEC planned to flip
(`test_materialized_text_status_authority_is_rechecked_before_adapter_build`,
`test_runtime_calibrated_status_is_unverified_before_adapter_build`) both
construct their `unsafe` config by overriding a text-authority field
(`TEXT_RUBRIC_AUTHORITY`) AWAY from what the manifest was compiled with.
`authority_policy_snapshot` includes that same field, so this scenario
was ALWAYS a manifest-vs-runtime mismatch too — before this tranche, the
calibration-receipt raise fired first and permanently masked the
mismatch check for this exact input; the mismatch branch was live code
but dead for this specific test shape. Converting the calibration check
to a non-raising notice UNMASKS the mismatch check: run against the real
code,
```
$ python -c "... unsafe = apply_overrides(_config(), {'TEXT_RUBRIC_AUTHORITY': 'calibrated_status'}); preflight_harness(manifest_compiled_with_default_config, harness, unsafe) ..."
RunManifestError: TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH at /engine_config: runtime text authority policy differs from the frozen manifest
```
i.e. the literal flip SPEC S5 planned (raise -> success + notice) is
FALSE for this exact scenario — it is now raise -> a DIFFERENT, still
in-scope-to-KEEP raise (C3: `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`
stays a hard refusal, frozen-record protection, untouched by this
tranche).

**Resolution (smallest change, no new files, no budget growth):** these
two tests' SCENARIO changes from "compile with the default config, then
recheck with a diverging config" to "compile with the SAME
already-triggering config used for the recheck" — i.e. no
`authority_policy_snapshot` divergence, so the mismatch guard stays
silent and the recheck exercises exactly what S3 claims: `preflight_harness`
independently reproduces the notice from a live, non-frozen
`text_status_authority_issues` call, not merely by inheriting
`manifest.compile_notices`. Verified directly:
```
config = apply_overrides(_config(), {'TEXT_RUBRIC_AUTHORITY': 'calibrated_status'})
manifest = compile_run_manifest(config, schema_version=2, workload_profile='text', rubric_policy='require_cross_family')
# compile_notices: ['CALIBRATION_RECEIPT_REQUIRED']
notices = preflight_harness(manifest, Harness(...), config)  # SAME config
# preflight notices: ['CALIBRATION_RECEIPT_REQUIRED']
```
No coverage is lost: the "runtime config diverges unsafely from the
frozen manifest" scenario these two tests used to exercise incidentally
remains fully covered by the untouched
`test_runtime_cannot_mutate_frozen_text_authority_policy`, which
diverges on `CALIBRATION_RECEIPT` specifically to prove exactly that
mismatch path — this tranche does not touch it and does not need a
second test proving the same guard.

S3 and S5's items above are amended in place by this addendum (their
accept-checks and CHECKLIST.md step 6/1 are updated to the same-config
scenario); no other item changes. Not a material fork requiring the
operator (dominance test: the alternative — asserting
`TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH` instead of a notice for these
two tests — would silently drop the very coverage S5/R10 exists to keep,
so it is not a live option, not a 50/50 choice).
