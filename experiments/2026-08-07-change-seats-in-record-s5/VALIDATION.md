# Validation for: seats in the typed record — Rung S5 of role-seat separation

Re-read REQUEST.md (Amendments 1-3), SPEC.md, and CHECKLIST.md in full
before running anything below. Every check re-run FRESH in this phase,
not merely re-cited from CHECKLIST.md's own step evidence, except the
sweep (see S9's own note).

## Acceptance checks

**S1** (R1, R15) — tranche artifacts exist in phase order:
`REQUEST.md`, `SPEC.md`, `CHECKLIST.md` exist and are committed;
`VALIDATION.md` is this document, being committed now; `PARKED.md`
exists (written this phase, below); `DELIVERY.md` is the NEXT phase's
own artifact, not owed until `dr-deliver-change` runs. **PASS** for
every artifact owed at this phase.

**S2** (R4, R5, R6, C4, C5) —
```
$ python -c "from deepreason.seat_events import SeatBindingV1, SeatBindingsEventPayloadV1, recorded_seat_bindings"
S2 import OK
$ python -m pytest tests/test_seat_bindings_record.py -q -k fresh_harness
1 passed
```
**PASS**

**S3** (R5, R14) —
```
$ python -m pytest tests/test_seat_bindings_record.py -q -k default_when
1 passed
```
`seat_bindings_for_run` returns exactly one `group == "default"` entry
naming the manifest's own provider/model_id. **PASS**

**S4** (R7, R17, C3, C4) —
```
$ python -m pytest tests/test_seat_bindings_record.py -q -k contract
1 passed  (1 positive + 3 negative cases inside the one test)
```
**PASS**

**S5** (R8, R17, C1, M6) —
```
$ git diff --stat 54feb5cc..HEAD -- src/deepreason/harness.py
 src/deepreason/harness.py | 21 +++++++++++++++++++++
 1 file changed, 21 insertions(+)
$ python -c "... AST check on Harness._apply_event ..."
OK: _apply_event has no seat_bindings branch
```
Exactly the appender plus the one `_commit` keyword (three git `@@`
regions mapping onto R19's two named units — see CHECKLIST.md step 11
for the full trace of why an import was NOT needed). `_apply_event`
byte-identical. **PASS**

**S6** (M1-M4, Q3) —
```
$ python -m pytest tests/test_seat_bindings.py -q -k by_group
3 passed
$ python -m pytest tests/test_run_preparation_service.py -q -k "seat_bindings_writes_no or seat_binding_writes_the"
2 passed
```
`resolve_seat_bindings_by_group` returns a 2-entry dict keyed by literal
group names; `prepare()` with no bindings leaves `seat-bindings.json`
absent (not an empty file); one bound group writes it. **PASS**

**S7** (R2, R8, R13, R14, M3, M5, Q3, Q5, C6) —
```
$ python -m pytest tests/test_seat_bindings_record.py -q -k "two_profile or default_home"
2 passed
```
Two-profile home: one stamp naming both bound groups (R13). Default
home: `recorded_seat_bindings` returns `()` AND `seat_bindings_for_run`
projects the single "default" entry (R14). **PASS**

**S8** (R10) — see "Full gate" below. **PASS**

**S9** (R9, R11, R12) — evidence carried forward from CHECKLIST.md
steps 1/27 (pristine-tree and post-src-change sweep, byte-identical,
sha `8b928c08b1...`, 45 rows / 11 ERROR) and steps 29-31 (probe's own
before/after, byte-identical, sha `76e7970c0e...`, 34 openable rows,
mutation-proven — a fabricated stamp moved all 34 `seats=` values,
restored byte-identical). **Not re-run in this phase**: each sweep
takes ~20 minutes and the tree has not changed since those captures
(confirmed by `git status --porcelain` empty and `git log -1` matching
the commit each capture was taken against) — re-running would
reproduce byte-identical output by construction, so the already-fresh
evidence from this same continuous session is cited rather than
re-spending ~60 minutes to reproduce a foregone conclusion. Record-
behavior spot-check (this phase's own, see below) independently
confirms the same two roots the sweep covers are unchanged. **PASS**

**S10** (R15) —
```
$ git diff --name-status 54feb5cc..HEAD | grep -iE "qualification\.py|_run\.sh"
no match (PASS)
```
**PASS**

**S11** (all, map) — see "Map" below. **PASS**

## Full gate

Re-run fresh in this phase (second independent run of the full suite
since the tranche's own step 25):
```
FAILED tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after
ValueError: too many values to unpack (expected 1)
1 failed, 3382 passed, 7 skipped in 832.15s (0:13:52)
```
Proven pre-existing, not caused by this tranche, via `git worktree add
<tmp> 54feb5cc` (this tranche's own base commit) and re-running the one
failing test there:
```
FAILED ... ValueError: too many values to unpack (expected 1)
1 failed in 59.54s
```
Identical failure on the pristine base commit. Net of P1/P3: **3382
passed, 0 failed** : **PASS** (R10's own named exception). Full detail
and root-cause evidence in `PARKED.md`.

## Record-behavior preservation

- `experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752`
  (known-good v6 root): `verify_root` -> `valid=True, violations=[]`
  fresh this phase; unchanged from the sweep's own before/after capture
  (`valid=True epistemic_passed=False att=0 blind=1 modules=-` in both
  `sweep-before.txt` and `sweep-after.txt`).
- `experiments/2026-08-05-testphase-live-validation/home-testphase/runs/run-a518e33a75507207633f864ba6a864b1`
  (the P1/P3 defect-era continued root, module_fingerprints-stamped
  twice): `verify_root` -> `valid=True, violations=[]` fresh this
  phase; unchanged from the sweep's own capture
  (`valid=True epistemic_passed=False att=0 blind=1 modules=default`
  in both). This is the ROOT `verify_root` itself still calls valid
  even though `test_module_fingerprints.py`'s own single-unpack
  assertion trips on it — exactly the distinction Q5/A5 designed this
  rung's own reader around (never single-unpack).

Both roots: **unchanged**.

## Map

```
docs_verify [full]: 52 documents, 829 checks, 4 workers
docs_verify: 0 failed                                          : PASS
docs_verify --audit: 0 finding(s)                               : PASS
docs_verify --links: 0 dangling reference(s), 52 document(s)    : PASS
docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0 finding(s) : PASS
```
`--coverage`'s 16 headerless seams are pre-existing and advisory
(`SCHEMA.md` sanctions the omission when stated; `SEAM-harness-x-
verification.md` itself explains its own omission in its own text,
predating this tranche) — 0 findings means the instrument itself
considers this non-blocking.

`docs_verify --stale`: 19 documents listed as worth re-reading (owned
files changed since their own `Verified-at`). Judged individually:

- **`CON-seats.md`, `SEAM-schools-x-scheduler.md`, `CON-schools.md`,
  `CON-run-identity.md`** do NOT appear (their `Verified-at` was
  advanced to `bdc476e8` at step 22, after their owned files' own last
  change in this tranche) — up to date by construction.
- **`SEAM-harness-x-verification.md`, `SEAM-harness-x-workflow.md`,
  `SEAM-ontology-x-rules.md`, `SEAM-scheduler-x-rules.md`,
  `SEAM-scheduler-x-workflow.md`, `SEAM-schools-x-scratch.md`,
  `SUB-harness.md`, `SUB-ontology.md`, `SUB-scheduler.md`** — all list
  this tranche's own commits (the `harness.py`/`ontology/event.py`/
  `scheduler.py` touches) among their reasons for staleness. Dismissed:
  every one of these documents' own CHECKS still passes (confirmed by
  the full `docs_verify` run above, 0 failed), and the AGREEMENT each
  describes did not move by design — the new field/appender/emission
  site are purely additive, ride the existing `Rule.MEASURE` vehicle
  exactly as the four other optional payloads already do, and
  `_apply_event`/well-formedness are confirmed byte-identical (S5).
  No prose claim in these documents is now false; re-reading them found
  nothing to update.
- **`REC-change-a-seam.md`, `SEAM-bridge-x-manifest.md`,
  `SEAM-llm-x-manifest.md`, `SEAM-manifest-x-schools.md`,
  `SUB-manifest.md`, `SUB-periphery.md`, `SUB-verification.md`** — all
  list ONLY pre-existing commits from unrelated prior tranches (rung 2
  tranche 2/3, rung 3 tranches A/B, an earlier attached-evidence fix).
  Pre-existing staleness, unrelated to and not caused by this rung; not
  this validation's obligation to resolve.

New checks added by this change: 4 — `CON-seats.md` (import +
`hasattr` check on the reader/payload/writer trio), `SEAM-schools-x-
scheduler.md` (AST placement/gating check for `_record_seat_bindings`,
mirroring the fingerprint's own), `CON-schools.md` (behavioral
scheduler-run check for the stamp), `CON-run-identity.md` (behavioral
`prepare()` check for the conditional snapshot's absence).

Record observable added vs sweep probe: `seat-bindings.v1` (via
`Event.seat_bindings`) -> `tools/root_sweep.py`'s new `seats=` column
(CHECKLIST.md steps 29-31, mutation-proven).

Wheel smoke: packaging surface untouched — smoke not owed (no
`pyproject.toml`, CLI entry point, MCP tool/schema, or wheel-layout
file in this tranche's diff).

## Requirement sweep

R1: demonstrated by S1 (tranche routed through `dr-change-orchestrator`
phase by phase, artifacts in order).
R2: demonstrated by S7 (every scheduled run stamps or projects a seat).
R3: demonstrated by SPEC.md's M1-M6 measurements and the landed design
mirroring `module_events.py`'s exact shape.
R4: demonstrated by CHECKLIST.md's own step ordering (reader, steps
2-4, lands before the writer, step 11).
R5: demonstrated by S3 (the exact "single seat, the manifest's
provider" projection).
R6: demonstrated by SPEC.md's Q1 resolution (sibling payload, measured
against the tree, not inherited untraced).
R7: demonstrated by S4.
R8: demonstrated by CHECKLIST.md's ordering (writer, step 11, after the
fence, step 7-10).
R9: demonstrated by S9 (steps 1/27/29-31).
R10: demonstrated by "Full gate" above.
R11: demonstrated by S9 (byte-identical both before/after the src
change and the probe's own before/after).
R12: demonstrated by S9 (step 31's mutation-proof).
R13: demonstrated by S7's two-profile test.
R14: demonstrated by S7's default-home test.
R15: demonstrated by S10 (no `qualification.py`, no new ladder script)
plus this tranche's own diff naming no Rung S6 file.
R16: demonstrated by `SeatBindingV1`'s own fields (`group`, `provider`,
`model_id`, `profile_digest`).
R17: demonstrated by the same evidence as R4-R9 (its own restatement).
R18: **legitimately deferred** — the plan document's own
"testphase-style live audit" clause is Rung S6's stated scope, placed
out of bounds by the operator's own R15 ("S4b and S6 untouched"); A4
records this disposition. Not built here, by the operator's own words.
R19: demonstrated by S5 and the frozen-surface diff (harness.py bounded
to exactly the two authorized units).
R20: demonstrated by there being no OTHER `harness.py` touch in this
tranche beyond R19's own grant — the non-transitivity rule is
self-consistent (nothing here presumes it extends further).
R21: demonstrated by REQUEST.md Amendment 2 itself (the corrected
500-650 budget).
R22: demonstrated by REQUEST.md Amendment 3 itself (the second
authorization) and this document's own final-total disclosure below.

Every R has a demonstrating check or an operator-worded deferral. None
is unaddressed.

## Assumptions carried

A1: sibling payload `seat-bindings.v1`, not an extension of
`module-fingerprints.v1` (structural fit + the plan's own literal
words, both measured, not preferred).
A2: no manifest touch anywhere (Rung S2's "manifest record" phrasing
was informal prose, not a locked decision; the operator's own "follow
the rung-4 template exactly" is the more specific, more recent
authority).
A3: the mint-time snapshot lives in a new file, `seat-bindings.json`,
not as a field on `RunPreparationRecordV1` (avoids that record's own
digest/identity re-validation logic; operator may override toward
folding it in later — behavior is identical either way).
A4: R13/R14 are satisfied by an offline regression (MockEndpoint), not
a live provider-backed run; R18's live-audit clause is Rung S6's own
scope, explicitly out of bounds here (R15).
A5: the writer copies the rung-4 template's per-instance idempotency
gate exactly, unmodified — not implicated in P1/P3 per M-verification
(the TEST's single-unpack assumption is) — while this rung's OWN reader
tests are written as partition claims from the start (Q5), so no new
instance of that specific test-brittleness is manufactured. P1/P3
itself remains parked (see `PARKED.md`).

## Budget disclosure (R21, R22)

Final actual: `git diff --stat 54feb5cc..HEAD -- src/ tests/ docs/map/
tools/` = **804 insertions** (792 through the main phase + 13 for the
probe's `seats=` column extension, minus 1 already-counted overlap),
against R21's own corrected 500-650 ceiling. This is disclosed plainly, per R22's own binding
condition, not glossed: two overruns occurred during execution (at
361/650 already trending high, confirmed exceeding at 729/650 before
the map landed), both raised via `AskUserQuestion` STOPs and resolved
by explicit operator authorization (REQUEST.md Amendments 2 and 3).
The excess is test/docstring density consistent with this program's
own established style (Rung 4's own `test_module_fingerprints.py`
landed at 493 lines against a much smaller per-item estimate) — no
symbol, file, or requirement beyond SPEC.md's declared Items S1-S11 was
touched at any point.

## Verdict: PASS
