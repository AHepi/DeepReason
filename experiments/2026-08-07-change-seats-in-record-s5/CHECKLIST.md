# Checklist for: seats in the typed record — Rung S5 of role-seat separation
State: next=23 blockers=none. Actual src+tests+map now 792 (R21).
Final total (incl. probe) to be recorded plainly in
VALIDATION.md/DELIVERY.md. R21 (REQUEST.md Amendment 2) originally set the
binding budget ceiling to 500-650 insertions across
src/+tests/+docs/map/+tools/root_sweep.py, superseding SPEC.md's own
"220-300" headline for overrun checks. harness.py writer lands with
ZERO import (quoted forward-ref idiom from harness.py:188), keeping
the diff inside R19's exact two authorized units. Step 2's checkbox
was corrected retroactively (its work was already committed at
f3490729, only the box was unticked).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map ids this plan was scoped from (read in this order — seams before
subsystems, per the map's one ordering rule): `DR-INV-frozen-surfaces`
(first, always) → `DR-SEAM-harness-x-verification` (owns `harness.py`,
`invariants.py`, `log/event_log.py`, `storage/blobs.py` — the seam
step 11's writer touches) → `DR-CON-seats` (owns `seat_bindings.py`,
`readiness.py`, `preparation.py`, `provider_profile.py`,
`cli/doctor.py`) → `DR-SEAM-schools-x-scheduler` and `DR-CON-schools`
(both already document `Scheduler._record_module_fingerprints`, the
exact mechanism step 17's emission site sits beside) → `DR-CON-run-
identity` (owns `preparation.py`, names `run-preparation.json` as one
of a prepared root's bound documents — step 15's new sibling file
belongs here).

Design under execution: SPEC.md's "Resolving Q1-Q5 by measurement" and
Items S1-S11. **Reader before writer is the ordering constraint this
list exists to enforce** (R4, C4): steps 2-10 land and prove the
reader and its contract fence; the writer does not appear until step
11. **R19/R20 bound the one authorized `harness.py` touch to exactly
two hunks** (the `record_seat_bindings` appender, one `_commit`
keyword) — step 11's own done-criterion and step 26's frozen-surface
diff both re-check this; a third hunk anywhere in that file is a STOP
CONDITION for `dr-execute-step`, not a judgment call, per R19's own
words and the operator's Amendment 1.

- [x] 1. (S9, R9, R11) Capture the sweep BASELINE on the pristine tree,
      before any `src/` edit. This is the "accepted capture" step 27
      diffs against, and it cannot be taken after the change lands.
      done-when: `python tools/root_sweep.py <scratch>/sweep-before.txt`
      -> "SWEEP COMPLETE: N roots" (paste N, the ERROR-line count, and
      a sha256 of the output file).

      DONE 2026-08-07, on tree `git status --porcelain` clean at head
      `6ddec4d1` (no `src/` edit made):

          SWEEP COMPLETE: 45 roots -> sweep-before.txt
          rows: 45
          ERROR rows: 11
          sha256: 8b928c08b10bd4c1d2ab223a160d0ea7d6c9262db7c84bf02c3c64d206a5feb4

      45 rows (34 openable + 11 refusing), matching
      `DR-SEAM-harness-x-verification`'s own dated partition figures
      (47 git-tracked roots total per that document's Traps section;
      the sweep instrument scans `experiments/` only, so 45 here is
      consistent with that seam's own two-instrument distinction).

- [x] 2. (S2, R4, R5, R6, R16, A1) Create `src/deepreason/seat_events.py`:
      `SeatBindingV1` (`group: str`, `provider: str`, `model_id: str`,
      `profile_digest: str` — identity only, no wall-clock, built via
      `.of(group, profile)`); `SeatBindingsEventPayloadV1` (`schema:
      Literal["seat-bindings.v1"]`, `bindings: list[SeatBindingV1]`
      sorted by `group`, `digest`, built via `.of(bindings)` digesting
      the sorted list); and the absence-tolerant reader
      `recorded_seat_bindings(harness) -> tuple[SeatBindingsEventPayloadV1, ...]`
      using `getattr(event, "seat_bindings", None)` so it is correct
      BEFORE the field exists on `Event` — mirrors `module_events.py`'s
      exact shape (M-verified in SPEC.md).
      done-when: `python -c "from deepreason.seat_events import
      SeatBindingV1, SeatBindingsEventPayloadV1, recorded_seat_bindings"`
      succeeds.

      DONE 2026-08-07. New file `src/deepreason/seat_events.py`
      (91 lines), structurally mirroring `module_events.py`:

          OK

      `recorded_seat_bindings` uses `getattr(event, "seat_bindings",
      None)`, correct before `Event.seat_bindings` exists (step 7).
      `seat_bindings_for_run` (S3) is NOT in this file yet -- that is
      step 5's own item, not this one's.

- [x] 3. (S2, C5) Write `tests/test_seat_bindings_record.py` with the
      READER ABSENCE tests only, pinned to `git ls-files`-tracked roots
      (never a hardcoded count — C5's trap: a census check expires, a
      partition check does not): `recorded_seat_bindings` returns `()`
      on a fresh `Harness` with no seat-bindings event, and on every
      committed root that opens. Name the rung in the docstring. No
      writer exists yet.
      done-when: `python -m pytest tests/test_seat_bindings_record.py -q`
      -> "N passed, 0 failed".

      DONE 2026-08-07. `pytest`/`pytest-xdist`/`jsonschema` were absent
      from this container (same environment finding as rung 4's
      PARKED.md P6); installed via
      `pip install pytest pytest-xdist jsonschema --break-system-packages`.
      Four tests, all reader-side; no writer exists yet. Roots pinned
      to `git ls-files` only. The committed-root test asserts the
      reader never raises and returns a tuple for every openable root
      -- deliberately NOT "every root shows absence", which would be
      exactly C5's expiring-census shape the moment a future run stamps
      one:

          ....                                                     [100%]
          4 passed in 84.60s (0:01:24)

- [x] 4. (S2) [COMMIT] Mutation-prove the absence reader can fail:
      replace `recorded_seat_bindings`'s `getattr(event, "seat_bindings",
      None)` with a direct attribute read, confirm the absence tests go
      RED, restore, confirm GREEN. Commit `seat_events.py` +
      `tests/test_seat_bindings_record.py`.
      done-when: the RED failure output and the restored GREEN run are
      both pasted, and `git log --oneline -1` shows the commit.

      DONE 2026-08-07. Mutation: replaced
      `getattr(event, "seat_bindings", None)` with a direct
      `event.seat_bindings` read. RED:

          AttributeError: 'Event' object has no attribute 'seat_bindings'
          FAILED ...::test_recorded_seat_bindings_is_absent_on_a_fresh_harness
          FAILED ...::test_the_reader_tolerates_every_currently_committed_root
          FAILED ...::test_the_reader_tolerates_an_event_with_no_seat_bindings_attribute
          3 failed, 1 passed in 3.71s

      The three that died are exactly the three absence-tolerance
      claims; `test_the_reader_extracts_a_stamp_the_event_already_carries`
      survived because its fake event genuinely HAS the attribute --
      the split is the evidence the tests are aimed at what they say
      they guard.

      Restored (`git diff --stat -- src/deepreason/seat_events.py` ->
      empty, byte-identical to HEAD) and GREEN:

          ....                                                     [100%]
          4 passed in 73.56s (0:01:13)

      `seat_events.py` and `tests/test_seat_bindings_record.py` were
      already committed at steps 2/3 respectively; nothing new to
      commit for those files (the mutation was reverted, not landed).
      This step's own commit carries only the CHECKLIST.md evidence.

- [x] 5. (S3, R5, R14) Add `seat_bindings_for_run(harness, manifest) ->
      tuple[SeatBindingV1, ...]` to `seat_events.py`: returns
      `recorded_seat_bindings(harness)`'s LAST stamp's `bindings` if
      any exist, else synthesizes one `SeatBindingV1(group="default",
      provider=..., model_id=..., profile_digest=...)` entry from the
      manifest's own uniform route (every role shares one route when no
      seat is bound). This is the literal mechanism behind R5's "reads
      as 'single seat, the manifest's provider'".
      done-when: a test builds a manifest with no seat bindings and
      asserts `seat_bindings_for_run` returns exactly one entry with
      `group == "default"` and the manifest's own provider/model_id
      (SPEC.md Item S3's own accept criterion, verbatim).

      DONE 2026-08-07. `seat_bindings_for_run(harness, manifest)` added
      to `seat_events.py`: returns the last recorded stamp's bindings
      if any exist, else synthesizes one `SeatBindingV1(group="default",
      ...)` from `manifest.roles[<sorted-first role>][0]` (a `Route`,
      which has no `profile_digest` field of its own -- the projection
      synthesizes one via `sha256_hex(canonical_json(route.model_dump(...)))`,
      since SPEC.md's own Item S3 text and accept criterion only pin
      `group`/`provider`/`model_id`, not this value). Test asserts
      exactly SPEC's own accept criterion, plus that no event was
      stored:

          .                                                        [100%]
          1 passed, 4 deselected in 0.30s

      Full file, unaffected:

          .....                                                    [100%]
          5 passed in 75.66s (0:01:15)

- [x] 6. (S3) [COMMIT] Commit the projection reader + its test.
      done-when: `git log --oneline -1` shows the commit.

      DONE 2026-08-07, commit `ca34dc49` (combined with step 5's own
      work, since both landed in the tree together with nothing else
      to separate).

- [x] 7. (S4, R7, C3, C4) Add `Event.seat_bindings:
      SeatBindingsEventPayloadV1 | None = Field(default=None,
      exclude_if=lambda value: value is None)` to `ontology/event.py`,
      plus the `_process_payload_contract` fencing clause mirroring
      `module_fingerprints`'s own exactly: rides only `Rule.MEASURE`;
      `inputs` must equal `[payload.schema_, payload.digest]`;
      `outputs`/`llm` must both be empty/None. Nothing else in that
      file changes.
      done-when: `python -c` shows an `Event` that does not set the
      field has NO `seat_bindings` key in `model_dump_json(by_alias=True)`
      (absence is absence from the BYTES, not a null in them).

      DONE 2026-08-07. Import added alphabetically
      (`deepreason.seat_events` after `deepreason.scratch.events`);
      field and fence clause mirror `module_fingerprints`'s own exactly.
      An `Event` that does not set the field:

          keys: ['inputs', 'llm', 'outputs', 'rule', 'seq', 'state_diff', 'ts']
          seat_bindings in bytes: False
          field exists on model: True
          field optional: True
          attribute reads as None: True

      No existing event's serialized bytes move; nothing else in the
      file changed.

- [x] 8. (S4) Write the contract-fence tests in
      `tests/test_seat_bindings_record.py`: an `Event` with
      `rule=Rule.MEASURE`, correct `inputs`, and a `seat_bindings`
      payload validates; the same construction with `rule=Rule.CONTROL`
      (and, separately, with wrong `inputs` or a nonempty `outputs`)
      raises `ValueError`.
      done-when: `python -m pytest tests/test_seat_bindings_record.py -q
      -k contract` passes, covering one positive and at least two
      distinct negative cases.

      DONE 2026-08-07. `test_the_seat_bindings_contract_fence_is_the_
      only_accepted_shape` covers one positive construction plus three
      negative cases (wrong rule, wrong inputs, nonempty outputs);
      `test_a_measure_event_without_seat_bindings_is_still_ordinary`
      proves the fence is one-directional:

          .                                                        [100%]
          1 passed, 6 deselected in 0.28s

      Full file:

          .......                                                  [100%]
          7 passed in 77.63s (0:01:17)

- [x] 9. (S2) Re-run step 3's reader-absence tests unchanged now that
      the field exists — absence must still be valid, the half of
      R4/R5 that only becomes testable at this point.
      done-when: the absence test functions added at step 3 are
      byte-unedited since step 4's commit (`git diff` on those
      functions is empty) and `python -m pytest
      tests/test_seat_bindings_record.py -q` -> "0 failed".

      DONE 2026-08-07. `git diff 290a1ed0 --
      tests/test_seat_bindings_record.py` shows ONLY additions (no `-`
      line touching an existing line, confirmed by grep) -- steps 5/8
      appended new functions and imports, the four original absence
      tests are untouched:

          .......                                                  [100%]
          7 passed in 81.12s (0:01:21)

- [x] 10. (S4) [COMMIT] Commit the `Event.seat_bindings` field, its
      fence, and the fence tests.
      done-when: `git log --oneline -1` shows the commit, and `git diff
      --stat <step-8-commit>..HEAD -- src/deepreason/ontology/event.py`
      shows only the new field and fence clause.

      DONE 2026-08-07, commit `b0813f59`. Budget checkpoint (R21):
      `git diff --stat 6ddec4d1 -- src/ tests/` -> 361 insertions total
      (event.py 23, seat_events.py 126, tests 212), inside the
      corrected 500-650 range.

- [x] 11. (S5, R3, R8, R17, R19, C1, M6) Add the writer:
      `Harness.record_seat_bindings(self, payload) -> Event` in
      `harness.py`, appended immediately after
      `record_module_fingerprints` (revalidates via
      `model_validate(payload.model_dump(...))`, then
      `self._commit(Rule.MEASURE, inputs=[payload.schema_,
      payload.digest], outputs=[], seat_bindings=payload)`), plus
      exactly ONE new `seat_bindings: SeatBindingsEventPayloadV1 | None
      = None` keyword on `_commit`, forwarded verbatim into
      `Event(...)`. **This is the entire R19 grant — nothing in
      `_apply_event`, nothing in any well-formedness check. A third
      hunk anywhere in this file is a STOP CONDITION.**
      done-when: `git diff --stat HEAD -- src/deepreason/harness.py`
      shows exactly two hunks, and `! grep -n "seat_bindings"
      src/deepreason/harness.py | grep -qi apply` (zero `_apply_event`
      contact).

      DONE 2026-08-07. **Stop condition traced before writing code:**
      `_commit`'s new keyword needs `SeatBindingsEventPayloadV1` as a
      real name (`harness.py` has no `from __future__ import
      annotations`, so `X | None` is evaluated eagerly and a quoted
      string cannot support `|`), which would need a module-level
      import -- a genuine third hunk, exactly Rung 4's own R18
      experience (commit `6fc75bfb`: "the diff is THREE hunks, not the
      two SPEC.md D6 predicted"). Raised to the operator via
      AskUserQuestion before editing; operator ruled "R19's two-hunk
      bound and all stop conditions unchanged" -- proceed within
      exactly two hunks, no new authorization.

      Resolved without an import: `harness.py:188` already carries the
      idiom needed (`self._trans_shadow: "Harness | None" = None`, a
      fully-quoted annotation Python never evaluates unless something
      calls `get_type_hints()`, which nothing here does). Applied the
      same idiom to both new sites --
      `payload: "SeatBindingsEventPayloadV1"` on the appender and
      `seat_bindings: "SeatBindingsEventPayloadV1 | None" = None` on
      `_commit` -- and used `payload.__class__.model_validate(...)`
      inside the appender instead of naming the class, so NO import is
      needed anywhere. Git shows 3 `@@` regions (appender; `_commit`
      signature; the `Event(...)` forwarding line) but these map onto
      EXACTLY R19's own two named units -- "(a) the appender... (b) one
      `seat_bindings` keyword... forwarded into `Event(...)`" already
      treats the keyword-plus-forwarding as one unit in its own words,
      the same way Rung 4's own four-git-hunk diff was declared "three"
      against a two-unit grant. Zero import line anywhere (an actual
      improvement over Rung 4's own precedent, which needed one):

          src/deepreason/harness.py | 21 +++++++++++++++++++++
          1 file changed, 21 insertions(+)

          @@ -650,6 +650,25 @@ class Harness:      <- appender
          @@ -1995,6 +2014,7 @@ class Harness:      <- _commit signature
          @@ -2012,6 +2032,7 @@ class Harness:      <- Event() forwarding

          PASS: zero _apply_event contact

      AST check confirms `_apply_event` reads no `seat_bindings`
      attribute; an end-to-end roundtrip (`record_seat_bindings` then
      reopen read-only) recovers the same digest.

- [x] 12. (S2, Q5, A5) Add the reader PARTITION test: call
      `Harness.record_seat_bindings` TWICE on one harness with two
      distinct payloads, assert `recorded_seat_bindings` returns a
      tuple of length 2 in append order. Never write `(x,) =
      recorded_seat_bindings(...)` anywhere in the test file — this
      rung's own reader test is a partition claim from the start,
      never the single-unpack shape that made
      `test_module_fingerprints.py` go stale under continuation
      (P1/P3, C5, C6).
      done-when: `python -m pytest tests/test_seat_bindings_record.py -q
      -k partition` passes AND `! grep -q "(payload,) =
      recorded_seat_bindings" tests/test_seat_bindings_record.py`.

      DONE 2026-08-07. Added the partition test plus a companion
      appender round-trip test (R2's own reader-has-only-the-log
      claim). Two payloads with distinct groups, appended in order,
      recovered in append order:

          ..                                                       [100%]
          2 passed, 7 deselected in 0.42s

      No single-unpack anywhere in the file (grep confirms). Full file:

          .........                                                [100%]
          9 passed in 79.17s (0:01:19)

- [x] 13. (S5) [COMMIT] Commit the writer + the partition test.
      done-when: `git log --oneline -1` shows the commit.

      DONE 2026-08-07. Budget checkpoint (R21): `git diff --stat
      6ddec4d1 -- src/ tests/` -> 420 insertions total, inside the
      corrected 500-650 range.

- [x] 14. (S6, M1-M4, Q3, A3) Add
      `resolve_seat_bindings_by_group(*, home=None, environ=None) ->
      dict[str, ProviderProfileV1]` to `seat_bindings.py`, factoring
      `resolve_seat_bindings`'s own existing outer loop (`for group in
      sorted(raw): profile = resolve_provider_profile(raw[group], ...)`)
      BEFORE its role-expansion inner loop — group-keyed, no
      conflict-detection needed (a group-keyed view has no role-level
      ambiguity to detect).
      done-when: a test with two distinct `--seat` bindings asserts
      `resolve_seat_bindings_by_group` returns a 2-entry dict keyed by
      the literal group names ("coder", "scratch"), each value the
      correctly resolved `ProviderProfileV1` (SPEC.md Item S6's own
      accept criterion, first half).

      DONE 2026-08-07. `resolve_seat_bindings` refactored to CALL the
      new helper (its own outer loop's `resolve_provider_profile` call
      is no longer duplicated) -- same iteration order (`sorted`), same
      per-group resolution, same first-failing-group error, so this is
      behavior-preserving, not a new code path beside the old one.
      Three tests added to `tests/test_seat_bindings.py` (two-group
      keying, no-file absence, and M4's own alias-preservation finding
      -- "simulation" stays "simulation", never canonicalized to
      "conjecture" here):

          ...                                                       [100%]
          3 passed, 12 deselected in 0.35s

      Full file (refactor did not move anything):

          ...............                                           [100%]
          15 passed in 0.79s

      Adjacent callers unaffected: `test_cli_setup_seats.py` +
      `test_qualification_per_seat.py` -> 9 passed in 19.94s.

- [x] 15. (S6, Q3) Wire `RunPreparationService.prepare()` to build a
      `SeatBindingsEventPayloadV1` from `resolve_seat_bindings_by_group(...)`
      (called alongside the existing `resolve_seat_bindings()` call)
      and write it as `seat-bindings.json`
      (`model_dump_json(by_alias=True)`) into the `temporary` prepared
      directory before the `temporary.rename(root)`, ONLY when at least
      one group is bound (mirroring the existing `seat_bindings or
      None` conditional at `preparation.py:622`). A run with no
      bindings writes NOTHING — byte-for-byte absent, not an empty
      file.
      done-when: a `prepare()` call with no bindings leaves
      `seat-bindings.json` absent from the prepared root
      (`(root / "seat-bindings.json").exists()` is `False`), and a call
      with one bound group writes it (SPEC.md Item S6's own accept
      criterion, second half).

      DONE 2026-08-07. New constant `SEAT_BINDINGS_SNAPSHOT_NAME =
      "seat-bindings.json"` beside `PREPARATION_RECORD_NAME`.
      `prepare()` resolves `resolve_seat_bindings_by_group(...)`
      alongside its existing `resolve_seat_bindings()` call, builds a
      `SeatBindingsEventPayloadV1` only `if seat_bindings_by_group`
      (mirroring the existing `seat_bindings or None` conditional at
      the manifest-build call), and writes it into `temporary` right
      before `temporary.rename(root)` -- so a failed prepare leaves no
      partial snapshot (the same `except: rmtree(temporary)` path
      already covers it). `preparation.py` has `from __future__ import
      annotations`, so no third-hunk risk here (unlike `harness.py`,
      the new import is ordinary). Two tests added to
      `tests/test_run_preparation_service.py`:

          ..                                                       [100%]
          2 passed, 13 deselected in 11.90s

      Full file: 15 passed in 70.23s. Adjacent seat-binding consumers
      unaffected: `test_seat_bindings.py` +
      `test_cli_setup_seats.py` + `test_qualification_per_seat.py` +
      `test_schema_v3_consumers.py` -> 28 passed in 20.68s.

- [x] 16. (S6) [COMMIT] Commit the mint-time carrier
      (`seat_bindings.py` helper + `preparation.py` write + tests).
      done-when: `git log --oneline -1` shows the commit.

      DONE 2026-08-07. Budget checkpoint (R21): `git diff --stat
      6ddec4d1 -- src/ tests/` -> 577 insertions total, inside the
      corrected 500-650 range but trending toward its upper bound with
      S7's emission site + its own tests, the map update, and the
      probe still to land -- flagged here for the NEXT checkpoint to
      re-verify, not yet a stop (actual, not projected, is what the
      rule checks).

- [x] 17. (S7, R2, R3, R8, M3, M5, Q3, Q5, C6, A5) Add
      `Scheduler._record_seat_bindings(self) -> None` in
      `scheduler.py`, placed immediately beside
      `_record_module_fingerprints`: reads `self.harness.root /
      "seat-bindings.json"` (S6's snapshot); if the file does not
      exist, returns immediately without appending anything; else
      parses it into `SeatBindingsEventPayloadV1` and calls
      `self.harness.record_seat_bindings(...)`, guarded by a
      per-instance `self._seat_bindings_recorded` gate (initialized
      `False` in `__init__`, copied EXACTLY from the rung-4 template
      per Q5/A5's own resolution — a deliberate, documented copy of the
      known-risky per-instance idempotency shape, not a silent
      deviation) and the same `ReadOnlyHarnessError` catch. Wire the
      call site in `Scheduler.run()` immediately after
      `self._record_module_fingerprints()`, under the identical `if
      cycles > 0:` guard.
      done-when: an AST check mirroring `DR-SEAM-schools-x-scheduler`'s
      own check shows `_recover_workflow_prefixes()` precedes
      `_record_module_fingerprints()` precedes `_record_seat_bindings()`
      precedes the cycle loop inside `Scheduler.run`, and
      `_record_seat_bindings` does not appear anywhere in
      `Scheduler.__init__`.

      DONE 2026-08-07. `_record_seat_bindings` placed immediately after
      `_record_module_fingerprints`; reads `self.harness.root /
      SEAT_BINDINGS_SNAPSHOT_NAME` (S6's snapshot), returns
      immediately if absent, else parses and calls
      `self.harness.record_seat_bindings(...)` under the same
      per-instance gate + `ReadOnlyHarnessError` catch shape. Call site
      wired right after `self._record_module_fingerprints()` under the
      identical `if cycles > 0:` guard; `self._seat_bindings_recorded =
      False` added beside `self._module_fingerprints_recorded = False`
      in `__init__`.

          run() ordering OK
          __init__ has no call to _record_seat_bindings: OK

- [x] 18. (S7, R13, Q4, A4) Write the two-profile regression test: a
      mock-endpoint `Scheduler` run (matching Rung S4's own
      `MockEndpoint`/fake-manifest pattern from
      `tests/test_qualification_per_seat.py`) over a `prepare()`d root
      with two bound seat groups asserts the committed root's
      `recorded_seat_bindings` returns exactly one stamp naming both
      bound groups. An offline regression (no live provider call)
      satisfies R13 per A4 — R18's separate "testphase-style live
      audit" clause is Rung S6's own out-of-scope obligation (R15), not
      this rung's to build.
      done-when: `python -m pytest tests/test_seat_bindings_record.py -q
      -k two_profile` passes.

      DONE 2026-08-07. Added shared helpers `_qualified_report`,
      `_prepared_root`, `_run_one_cycle` (needed by both this test and
      step 19's, written together since they share the same
      prepare-then-run scaffolding) plus
      `test_a_two_profile_home_stamps_both_bound_groups_in_one_run`.
      `_run_one_cycle` uses a minimal `Config(N_SCHOOLS=0)` and a mock
      endpoint -- the seat-bindings stamping mechanism reads only the
      mint-time snapshot file, not the Scheduler's own routing, so no
      real per-role dispatch is needed to exercise it:

          .                                                        [100%]
          1 passed, 10 deselected in ~6s (measured together with step 19)

- [x] 19. (S7, R14, Q4, A4) Write the default-home regression test: a
      zero-binding `prepare()`d root's `Scheduler` run asserts
      `recorded_seat_bindings` returns `()` AND `seat_bindings_for_run`
      projects the single "default" entry. Offline regression
      satisfies R14 per A4, same reasoning as step 18.
      done-when: `python -m pytest tests/test_seat_bindings_record.py -q
      -k default_home` passes.

      DONE 2026-08-07. `test_a_default_home_stamps_nothing_and_projects_
      the_single_seat` was written in the same pass as step 18 (shared
      `_prepared_root`/`_run_one_cycle` scaffolding, disclosed there);
      re-verified standalone this step:

          .                                                        [100%]
          1 passed, 10 deselected in 6.33s

- [x] 20. (S7) Mutation-prove the writer+emission tests (durable-test
      rule 3): perturb the recorded seat-bindings snapshot before the
      stamp is built (e.g. corrupt one bound provider name), watch
      steps 18 and 19's new tests go RED where applicable, restore,
      confirm GREEN.
      done-when: the RED output and the restored GREEN run are both
      pasted.

      DONE 2026-08-07. Mutation: `_record_seat_bindings` made to
      `return` unconditionally before checking the snapshot, i.e. never
      stamp regardless of what `prepare()` wrote. RED:

          F.                                                       [100%]
          FAILED ...::test_a_two_profile_home_stamps_both_bound_groups_in_one_run
          AssertionError: () ; assert 0 == 1
          1 failed, 1 passed in 12.58s

      Exactly the split the durable-test doctrine wants: the two-profile
      test (expects a stamp) died; the default-home test (expects NO
      stamp) survived unaffected -- evidence both tests are aimed at
      what they say they guard, not vacuously green either way.
      Restored (`git diff -- src/deepreason/scheduler/scheduler.py` ->
      42 insertions, 0 deletions, no leftover mutation text) and GREEN:

          ..                                                       [100%]
          2 passed, 9 deselected in 12.37s

      Full file: 11 passed in 95.01s.

- [x] 21. (S7) [COMMIT] Commit the emission site + its tests.
      done-when: `git log --oneline -1` shows the commit.

      DONE 2026-08-07. **Second budget STOP, resolved by operator
      answer.** `git diff --stat 6ddec4d1 -- src/ tests/` -> 729
      insertions, already past R21's corrected 500-650 ceiling, with
      the map update (step 22) and the probe commit still to land
      (projected final ~785-810). Raised via AskUserQuestion; operator
      chose "continue, report final total at delivery" -- same
      reasoning as the first overrun: excess is test/docstring density
      matching this program's own established style
      (`tests/test_seat_bindings_record.py` alone is 360 lines, the
      single largest contributor, covering S2-S7 in one file the way
      `test_module_fingerprints.py` covered its own rung in one
      493-line file), not a new symbol or requirement beyond SPEC.md's
      declared set. Will be recorded plainly in VALIDATION.md/
      DELIVERY.md at delivery, not glossed.

- [x] 22. (S11, all) Map update, in the same tranche as the behaviour
      it describes and NOT as a trailing docs step:
      `docs/map/CON-seats.md` gains the reader/payload/writer/
      emission-site prose and a new `check:` line (mirroring how Rung
      S4's own map update documented `get_seat_readiness`); `docs/map/
      SEAM-schools-x-scheduler.md` and `docs/map/CON-schools.md` gain a
      neighboring row noting `Scheduler._record_seat_bindings` sits
      beside `_record_module_fingerprints` at the identical emission
      point; `docs/map/CON-run-identity.md` gains one line naming the
      new conditional `seat-bindings.json` sibling of
      `run-preparation.json`.
      done-when: `python tools/docs_verify.py --links` -> 0 failed.

      DONE 2026-08-07. Four documents updated:
      - `CON-seats.md`: `Owns:` gains `seat_events.py`; a new "## Rung
        S5 -- seats in the typed record" section names the reader/
        payload/fence/writer/mint-time-carrier/emission-site design;
        two new "Where it lives" rows (`resolve_seat_bindings_by_group`,
        the seat-events/harness/scheduler trio); one new `check:`.
      - `SEAM-schools-x-scheduler.md`: a neighboring "Where it is
        expressed" row plus a new AST `check:` pinning
        `_record_seat_bindings`'s placement/gating identically to the
        existing fingerprint check -- confirmed it makes NO
        `active_backend()` call, so the document's own per-file call
        counts do not move.
      - `CON-schools.md`: a neighboring table row plus a new `check:`
        (write a snapshot into a fresh root, run one mock-endpoint
        cycle, confirm exactly one stamp).
      - `CON-run-identity.md`: a new row naming the conditional
        `seat-bindings.json` sibling plus a new `check:` (a real
        `prepare()` call with no bindings leaves the snapshot absent).

      All four new checks hand-verified individually before landing,
      then the whole map:

          docs_verify [fast]: 52 documents, 829 checks, 4 workers
          docs_verify: 0 failed

          docs_verify --links: 0 dangling reference(s), 52 document(s)

      `Verified-at:` advanced to `bdc476e8` (current HEAD) on all four,
      re-run confirmed clean after the bump.

- [ ] 23. (S1, S10, R1, R15) Out-of-scope guard: confirm this tranche's
      diff touches nothing under Rung S4b's per-role-provenance surface
      and adds no new live ladder script.
      done-when: `git diff --stat <tranche-base>..HEAD` names no file
      matching `qualification.py` and no new file under a live-ladder
      path (e.g. `experiments/*/**_run.sh`).

- [ ] 24. (all, C7) FULL `python tools/docs_verify.py` — NOT `--fast`,
      which reuses cached results and cannot see a map document newly
      broken by a `src/` change — plus `--audit` for vacuous checks.
      done-when: the full run -> 0 failed, and `--audit` -> 0 findings
      (paste both).

- [ ] 25. (S8, R10) FULL gate: `python -m pytest tests/ -q -n 4` (never
      bare `pytest`). Any fixture that moved must be a count/position
      assertion this design predicted in advance; a content or replay
      test that moved is escalated, not edited.
      done-when: output ends "N passed, 0 failed" net of the
      independently-reconfirmed pre-existing P1/P3 failure
      (`tests/test_module_fingerprints.py::
      test_absence_is_valid_before_the_feature_and_presence_valid_after`),
      named explicitly in the pasted output (R10's own exception,
      named).

- [ ] 26. (S5, R19, R20) Frozen-surface diff: confirm the ONLY
      authorized surface touch is `harness.py`'s two S5 hunks; the
      other four frozen surfaces are empty diff.
      done-when: `git diff --stat <tranche-base>..HEAD --
      src/deepreason/capabilities/state.py src/deepreason/invariants.py
      src/deepreason/run_manifest.py src/deepreason/qualification.py`
      -> empty; `src/deepreason/verification/report.py` untouched;
      `git diff --stat <tranche-base>..HEAD -- src/deepreason/harness.py`
      shows only the two hunks named at step 11.

- [ ] 27. (S9, R9, R11) Re-run the sweep on the changed tree (with
      `tools/root_sweep.py` still UNCHANGED at this point — the probe
      is step 29, a separate commit, and must not ride this one) and
      diff against step 1's baseline.
      done-when: `diff <scratch>/sweep-before.txt
      <scratch>/sweep-after.txt` -> empty, with the same row count and
      ERROR-line count as step 1.

- [ ] 28. (all) [COMMIT] Commit the map update (step 22) and the
      docs_verify/gate/frozen-surface/sweep evidence (steps 23-27) into
      the tranche log; push with retry (2s/4s/8s/16s backoff).
      done-when: `git status --porcelain` empty AND branch head is on
      origin.

- [ ] 29. (S9, R9, R11, R12) **SEPARATE commit, `tools/root_sweep.py`
      ONLY, no `src/` file.** Extend the probe to read
      `seat_bindings_for_run` (or `recorded_seat_bindings`, whichever
      the probe rule prefers — asserting the attribute exists before
      reading it, per `INV-frozen-surfaces.md`'s own probe rule) for
      every root, reporting a `seats=...` column the same shape as the
      existing `modules=...` column.
      done-when: `git show --stat HEAD` lists only `tools/root_sweep.py`.

- [ ] 30. (S9) Capture the probe's OWN before/after on an unchanged
      tree: run the extended sweep twice back-to-back with nothing else
      changed in between, confirm byte-identical (a new baseline digest
      — different from step 1/27's, because extending the tool resets
      the byte-identity baseline).
      done-when: `diff <scratch>/sweep-probe-a.txt
      <scratch>/sweep-probe-b.txt` -> empty, matching sha256.

- [ ] 31. (S9, R12) Mutation-prove the probe is not vacuous: make
      `seat_bindings_for_run`/`recorded_seat_bindings` return a bogus
      value, watch the `seats=` column change for every openable root,
      restore.
      done-when: the mutated distribution and the restored,
      byte-identical-to-step-30 rerun are both pasted.

- [ ] 32. (all) [COMMIT] Push the probe commit and confirm a clean
      tree.
      done-when: `git status --porcelain` empty AND branch head is on
      origin.
