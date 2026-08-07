# Checklist for: seats in the typed record — Rung S5 of role-seat separation
State: next=4 blockers=none
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

- [ ] 2. (S2, R4, R5, R6, R16, A1) Create `src/deepreason/seat_events.py`:
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

- [ ] 4. (S2) [COMMIT] Mutation-prove the absence reader can fail:
      replace `recorded_seat_bindings`'s `getattr(event, "seat_bindings",
      None)` with a direct attribute read, confirm the absence tests go
      RED, restore, confirm GREEN. Commit `seat_events.py` +
      `tests/test_seat_bindings_record.py`.
      done-when: the RED failure output and the restored GREEN run are
      both pasted, and `git log --oneline -1` shows the commit.

- [ ] 5. (S3, R5, R14) Add `seat_bindings_for_run(harness, manifest) ->
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

- [ ] 6. (S3) [COMMIT] Commit the projection reader + its test.
      done-when: `git log --oneline -1` shows the commit.

- [ ] 7. (S4, R7, C3, C4) Add `Event.seat_bindings:
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

- [ ] 8. (S4) Write the contract-fence tests in
      `tests/test_seat_bindings_record.py`: an `Event` with
      `rule=Rule.MEASURE`, correct `inputs`, and a `seat_bindings`
      payload validates; the same construction with `rule=Rule.CONTROL`
      (and, separately, with wrong `inputs` or a nonempty `outputs`)
      raises `ValueError`.
      done-when: `python -m pytest tests/test_seat_bindings_record.py -q
      -k contract` passes, covering one positive and at least two
      distinct negative cases.

- [ ] 9. (S2) Re-run step 3's reader-absence tests unchanged now that
      the field exists — absence must still be valid, the half of
      R4/R5 that only becomes testable at this point.
      done-when: the absence test functions added at step 3 are
      byte-unedited since step 4's commit (`git diff` on those
      functions is empty) and `python -m pytest
      tests/test_seat_bindings_record.py -q` -> "0 failed".

- [ ] 10. (S4) [COMMIT] Commit the `Event.seat_bindings` field, its
      fence, and the fence tests.
      done-when: `git log --oneline -1` shows the commit, and `git diff
      --stat <step-8-commit>..HEAD -- src/deepreason/ontology/event.py`
      shows only the new field and fence clause.

- [ ] 11. (S5, R3, R8, R17, R19, C1, M6) Add the writer:
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

- [ ] 12. (S2, Q5, A5) Add the reader PARTITION test: call
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

- [ ] 13. (S5) [COMMIT] Commit the writer + the partition test.
      done-when: `git log --oneline -1` shows the commit.

- [ ] 14. (S6, M1-M4, Q3, A3) Add
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

- [ ] 15. (S6, Q3) Wire `RunPreparationService.prepare()` to build a
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

- [ ] 16. (S6) [COMMIT] Commit the mint-time carrier
      (`seat_bindings.py` helper + `preparation.py` write + tests).
      done-when: `git log --oneline -1` shows the commit.

- [ ] 17. (S7, R2, R3, R8, M3, M5, Q3, Q5, C6, A5) Add
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

- [ ] 18. (S7, R13, Q4, A4) Write the two-profile regression test: a
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

- [ ] 19. (S7, R14, Q4, A4) Write the default-home regression test: a
      zero-binding `prepare()`d root's `Scheduler` run asserts
      `recorded_seat_bindings` returns `()` AND `seat_bindings_for_run`
      projects the single "default" entry. Offline regression
      satisfies R14 per A4, same reasoning as step 18.
      done-when: `python -m pytest tests/test_seat_bindings_record.py -q
      -k default_home` passes.

- [ ] 20. (S7) Mutation-prove the writer+emission tests (durable-test
      rule 3): perturb the recorded seat-bindings snapshot before the
      stamp is built (e.g. corrupt one bound provider name), watch
      steps 18 and 19's new tests go RED where applicable, restore,
      confirm GREEN.
      done-when: the RED output and the restored GREEN run are both
      pasted.

- [ ] 21. (S7) [COMMIT] Commit the emission site + its tests.
      done-when: `git log --oneline -1` shows the commit.

- [ ] 22. (S11, all) Map update, in the same tranche as the behaviour
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
