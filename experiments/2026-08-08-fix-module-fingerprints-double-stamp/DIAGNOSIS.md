# Diagnosis: the test's single-unpack assertion is a census claim that expired a second time; the writer is not defective

Primary cause: `tests/test_module_fingerprints.py:90`
(`(payload,) = recorded_module_fingerprints(Harness(root,
read_only=True))`) asserts "exactly one module-fingerprints stamp per
stamped root," a promise the writer never made and the design
deliberately declines to make. The writer
(`Scheduler._record_module_fingerprints`, `scheduler.py:479-509`) is
gated by `self._module_fingerprints_recorded`
(`scheduler.py:277`), a PER-INSTANCE guard reset on every
`Scheduler.__init__`. `deepreason continue` constructs a fresh
`Scheduler` against the resumed harness, so a continuation legitimately
appends a second stamp. The sibling `seat-bindings.v1` payload (Rung
S5) was built from the identical rung-4 template, deliberately copied
this same per-instance shape (`_seat_bindings_recorded`,
`scheduler.py:278,554-556`), and had its reader written as a partition
claim from day one specifically to avoid this exact test's failure
mode recurring. Rung S6's live run then positively demonstrated the
design is correct in production. The test is the defect, not the
writer.

Evidence:
  - `experiments/2026-08-06-change-seat-census-s1/PARKED.md` P3 ->
    symptom first recorded: root
    `.../home-testphase/runs/run-a518e33a75507207633f864ba6a864b1`
    (continued 2026-08-06 per that root's own
    `RESULTS.md` point 5) carries 2 `module_fingerprints` stamps; root
    cause explicitly deferred to `deepreason-orchestrator`.
  - `experiments/2026-08-07-change-seats-in-record-s5/REQUEST.md` C6 ->
    fresh diagnosis (re-verified again this session, unchanged):
    `Scheduler._module_fingerprints_recorded` is a per-instance guard
    that resets on every construction, so `continue`'s fresh
    `Scheduler` does not prevent a second stamp across a continuation
    boundary; named there as a "strong, freshly-verified candidate root
    cause for P1/P3," not yet adjudicated writer-vs-test.
  - `experiments/2026-08-07-change-seats-in-record-s5/SPEC.md` Q5/A5 ->
    the adjudication: "not necessarily a WRITER defect — a
    continuation genuinely CAN use different bindings than its
    original launch"; the rung deliberately copies the per-instance
    emission gate ("not implicated in the actual failure") but writes
    its OWN reader as a partition claim ("never `(x,) =
    recorded_module_fingerprints(...)`, always 'at least one, and the
    LAST one is what a reader asking "what does this run currently
    use" should read'") specifically so the sibling payload
    manufactures no new instance of this test's own brittleness.
  - `experiments/2026-08-08-live-two-seat-ab-s6/RESULTS.md`, second
    audit / criterion (d) -> live, positive confirmation: after
    `deepreason continue --budget cycles=2` on a real run,
    `seat_bindings_stamp_count: 2`, both stamps carrying the IDENTICAL
    digest and binding content, `replay_valid: true`,
    `verify_violations: []` — "bindings preserved byte-identically
    across the continuation boundary," the reader (returning every
    stamp, never a single-unpack) reading both correctly. Criterion (d)
    PASSED. This is the same mechanism this tranche's failing root
    exercises, on a payload deliberately modeled on
    `module-fingerprints.v1`.
  - `docs/map/SEAM-harness-x-verification.md` Traps ("A census check
    expires; a partition check does not") -> names this exact test's
    FIRST expiry ("asserted that NO committed root carries a
    module-fingerprint stamp — true only until the first run recorded
    after rung 4's writer was committed," fixed 2026-08-05 in
    `experiments/2026-08-05-fix-expired-census-readers/`) as one of
    three simultaneous instances of the same failure mode across the
    codebase. The current failure is the SAME test asserting a
    different, still-census-shaped claim ("exactly one" instead of
    "at least one") — the second occurrence of a pattern this document
    already names and already predicts.
  - `scheduler.py:277,507-509` and `scheduler.py:278,554-556` (code,
    read only after the record established the primary cause) ->
    confirms both guards share byte-identical shape: reset in
    `__init__`, checked-then-set in the `_record_*` method, both fired
    once from `Scheduler.run()` (`scheduler.py:2742-2743`).

Implicated code: `tests/test_module_fingerprints.py:90` (the
single-unpack assertion) and its surrounding loop
(`tests/test_module_fingerprints.py:89-93`). No `src/` file is
implicated — the writer's behavior matches its sibling's
deliberately-approved design.

Falsifiable prediction: `dr-reproduce` must show (a)
`python -m pytest tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after -q`
fails today on the committed root with
`ValueError: too many values to unpack (expected 1)`, and (b) the two
stamps on that root are BYTE-IDENTICAL (same `digest`), mirroring S6
audit2's seat-bindings finding — confirming the same payload was
legitimately re-emitted, not two disagreeing payloads (which would
instead point at a writer defect: two DIFFERENT payloads on one root
would mean the modules genuinely differed between launch and
continuation, a case this diagnosis does not claim to cover and did
not find).

Ruled out: the writer being defective (continuation-aware idempotency
needed in `_record_module_fingerprints`/`Scheduler.__init__`). Ruled
out because (1) SPEC.md Q5/A5 already considered and rejected this for
the sibling payload — a continuation can legitimately carry different
module content than its origin, so cross-continuation dedup would be
throwing away a real signal, not fixing a bug; (2) S6's live audit2
confirms in production that a re-stamped, replay-valid record with 2
byte-identical stamps is the design's own predicted, accepted shape,
not a verification violation; (3) `CLAUDE.md`'s governing principle —
"fix READERS so old roots stay valid; a change that invalidates
existing replay-valid roots is wrong by definition" — places the
burden of proof on a writer change to show an existing root is
actually broken. `run-a518e33a75507207633f864ba6a864b1` is not broken:
`verify_root` reports it valid; only the test's private "exactly one"
assumption fails. There is no invalidity for a writer change to fix.
