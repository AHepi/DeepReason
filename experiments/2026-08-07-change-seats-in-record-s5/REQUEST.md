# Request: seats in the typed record — Rung S5 of role-seat separation
Captured: 2026-08-07 from the operator's message opening this tranche
(sent immediately after accepting Rung S4's delivery) and the plan
document's own Rung S5 text.

## Verbatim

Operator's message opening this tranche:

> S4 accepted — multi-model launch is live via combination-subject
> qualification, M5's dispatch proof is the load-bearing evidence, S4b
> stays parked. Now Rung S5 via dr-change-orchestrator: seats in the
> typed record, per docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md. Every
> run's own record must permanently say which model sat in which seat
> — follow the rung-4 template exactly: absence-tolerant READER first
> (every existing committed root reads as "single seat, the manifest's
> provider"), then the payload (S2's spec expected a seat-bindings
> sibling of module-fingerprints.v1 — verify that shape against the
> tree, don't inherit it untraced), contract clause fencing it, writer
> last, sweep probe in its own SEPARATE commit with its own before/after
> capture on an unchanged tree. Accept: full gate 0 failed (P1's known
> pre-existing failure excepted, named); sweep byte-identical
> pre-probe; probe mutation-proven; a two-profile home's run shows the
> stamp naming both bindings, a default home's run shows the
> single-seat stamp. One rung only — S4b and S6 untouched.

The plan's own Rung S5 text, quoted verbatim from
`docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md` lines 109-117:

> ### Rung S5 — seats in the typed record  [EXECUTE, rung-4 template]
> Extend the module-fingerprint stamp (or a sibling `seat-bindings.v1`
> payload — S2 decides) so every run records role-group →
> provider/model/profile-digest. Reader first, absence-tolerant (old
> roots read as "single seat, the manifest's provider"); contract
> clause fencing the payload; sweep probe in its own separate commit
> with its own before/after capture. Accept: gate; sweep byte-identical
> pre-probe; probe mutation-proven; testphase-style live audit shows
> the stamp on a real run.

## Map preflight (resolved ids, recorded here so every later phase
## starts from the same map)

- `DR-INV-frozen-surfaces` — read IN FULL this turn. Surface 2 =
  `harness.py` event application and well-formedness (the file this
  rung's writer must touch, per the rung-4 template). Surfaces 3, 4, 5
  (`invariants.py`/`verification/`, `run_manifest.py`,
  `qualification.py`) are out of this rung's path per the plan's own
  "typed record" framing, to be re-confirmed at spec time, not assumed.
- `DR-SEAM-harness-x-verification` — read IN FULL this turn, before
  either subsystem it joins. `Owns: harness.py, invariants.py,
  log/event_log.py, storage/blobs.py`. "How to change it" step 2
  ("reader before writer, always... a new field on a durable record
  gets a default and a reader that decides what its ABSENCE means")
  and step 3 (the fixed order a new typed event channel must move in:
  `Rule`/payload field → `_apply_event` branch → `_reset` attribute if
  it materializes state → the `record_*` seam → a determinism finding
  in `verify_root` → a `report.py` channel entry — "stopping before
  the last step defaults the new finding to `integrity`... so every
  recorded root that trips it flips") both bind this rung's design
  directly. A Traps entry on this same document records that
  `tests/test_module_fingerprints.py` — the reader-side test this rung
  will directly parallel — already went stale once in exactly the way
  a new rung-4-shaped payload risks going stale again: "asserted that
  NO committed root carries a module-fingerprint stamp — true only
  until the first run recorded after rung 4's writer was committed."
- `DR-CON-seats` — owns `seat_bindings.py`, `readiness.py`,
  `preparation.py`, `provider_profile.py`, `cli/doctor.py`; carries
  Rungs S1-S4's own design record. `resolve_seat_bindings(*, home=None,
  environ=None) -> dict[str, ProviderProfileV1]` (per-ROLE, expanded
  from group aliases) and `load_seat_bindings(path) -> dict[str, str]`
  (raw `{group: path}`, unexpanded) are the two shapes available;
  neither is a registry with a `.fingerprint()` method the way
  `SCHOOL_POPULATION` is.
- The rung-4 precedent this rung is explicitly told to copy — every
  fact below verified fresh against the current tree this turn, not
  carried from memory or from the rung-4 tranche's own documents:
  - `src/deepreason/module_events.py`: `ModuleFingerprintV1` (registry:
    str, module_id: str, fingerprint: Mapping, fingerprint_sha256: str,
    built via `.of(registry, module_id, fingerprint)` which digests the
    mapping itself so no caller can record a disagreeing digest) and
    `ModuleFingerprintsEventPayloadV1` (`schema:
    Literal["module-fingerprints.v1"]`, `modules: list[...]`, `digest:
    str`, built via `.of(modules)`). `ModuleFingerprintV1`'s own
    docstring: "`registry` names the registry that resolved it, so
    further registries can be stamped later without a schema change" —
    i.e. this payload was explicitly designed to be EXTENSIBLE by
    adding more `ModuleFingerprintV1` entries with a different
    `registry` value, not necessarily requiring a sibling schema.
  - `recorded_module_fingerprints(harness)` (same file): scans
    `harness.log.read()` for `getattr(event, "module_fingerprints",
    None) is not None`, returns a tuple, empty for every root recorded
    before the payload existed — the absence-tolerant reader.
  - `src/deepreason/ontology/event.py:379-381`: `Event.module_
    fingerprints: ModuleFingerprintsEventPayloadV1 | None =
    Field(default=None, exclude_if=lambda value: value is None)` — the
    same `exclude_if` shape the four other optional payloads
    (`scratch`, `bridge`, `conjecture_turn`, `capability`) already use,
    which is what keeps an old event's serialized BYTES unchanged when
    the field is absent.
  - `event.py:451-469`, inside `_process_payload_contract`: when
    `module_fingerprints is not None`, the event's `rule` must be
    `Rule.MEASURE`, `inputs` must equal exactly `[payload.schema_,
    payload.digest]`, and `outputs`/`llm` must both be empty/None
    ("module fingerprints record identity, not work"). One-directional:
    a MEASURE event need not carry fingerprints, but fingerprints may
    ride nothing but a MEASURE event.
  - `src/deepreason/harness.py:631-651`: `record_module_fingerprints
    (self, payload)` — the appender. Revalidates the payload
    (`model_validate(payload.model_dump(...))`, rejecting a forged
    instance the way the other four payload appenders already do), then
    `self._commit(Rule.MEASURE, inputs=[payload.schema_,
    payload.digest], outputs=[], module_fingerprints=payload)`.
  - `harness.py` around lines 1997/2014: `_commit` takes
    `module_fingerprints: ModuleFingerprintsEventPayloadV1 | None =
    None` as one more keyword, forwarded verbatim into the `Event(...)`
    constructor beside the other five payload keywords. No change to
    `_apply_event` (confirmed: `module_fingerprints` does not appear
    there) and no change to any well-formedness check outside
    `_process_payload_contract`, which is on `Event` in `ontology/
    event.py`, not on `Harness`.
  - `src/deepreason/scheduler/scheduler.py:478-524`,
    `_record_module_fingerprints`: fires from `Scheduler.run()`, never
    from `__init__` (constructing a Scheduler to inspect ranking or
    recover from a crash must append nothing); fires AFTER workflow
    recovery and stop rehydration; fires unconditionally (outside the
    `N_SCHOOLS > 0` gate — a zero-school run was still built by the
    registered backend); catches the harness's own typed
    `ReadOnlyHarnessError` so a read-only Scheduler construction never
    raises or appends; gated by `self._module_fingerprints_recorded`
    (an instance attribute).
  - **A significant fresh finding, not carried from any prior tranche's
    documents:** `scheduler.py:277` sets `self._module_fingerprints_
    recorded = False` inside `Scheduler.__init__` — this is a
    PER-INSTANCE guard, reset every time a new `Scheduler` object is
    constructed. `deepreason continue` constructs a fresh `Scheduler`
    against the resumed harness, so this guard does NOT prevent a
    second stamp from being appended to the SAME run root across a
    continuation boundary. This is a strong, freshly-verified candidate
    root cause for **P1/P3** — the pre-existing
    `tests/test_module_fingerprints.py::
    test_absence_is_valid_before_the_feature_and_presence_valid_after`
    failure tracked in every one of Rungs S1-S4's `PARKED.md` files,
    where continued root `run-a518e33a75507207633f864ba6a864b1` carries
    2 `module_fingerprints` stamps and the reader's `(payload,) =
    recorded_module_fingerprints(...)` unpacking assumes exactly 1.
    This was NOT independently diagnosed by any prior rung — each
    PARKED.md entry recorded the symptom and deferred root-causing it
    to `deepreason-orchestrator`. Recorded here because it directly
    informs this rung's own design: if Rung S5 copies the SAME
    per-instance idempotency shape for its own new payload, it
    manufactures a SECOND instance of the identical known defect rather
    than avoiding it or fixing the template it is told to copy exactly.
  - `tools/root_sweep.py`: the committed sweep probe. Reads
    `recorded_module_fingerprints(harness)` for every root, asserts
    `hasattr(harness, "log")` before reading, and reports a
    `modules=...` column (comma-joined `module_id`s, or `-` when
    empty) — landed as its own commit per the rung-4 template's
    separate-probe-commit rule.
- Grepped `experiments/2026-08-06-change-seat-binding-design-s2/
  SPEC.md` for `module-fingerprints` and `seat-bindings.v1` this turn:
  **zero hits, both terms.** The plan document's own words say "S2
  decides" the payload shape (extend module-fingerprints.v1 vs. a
  sibling seat-bindings.v1), but S2's SPEC.md, read in full during its
  own tranche and re-checked here, never actually makes this decision
  — it only names "Rung S5's binding-provenance **manifest** record"
  once (S2 SPEC.md line ~507, `S3` item, discussing why Option B was
  rejected for S3), which is worth flagging: a MANIFEST-level record
  would touch frozen surface 4 (`run_manifest.py`), not the
  `harness.py` event-log path the rung-4 precedent and this rung's own
  operator instruction ("follow the rung-4 template exactly") both
  point at. This is a genuine, unresolved tension between what S2's
  prose called the future deliverable and what S5's own instructions
  now specify — recorded as an open question below, not resolved here.

## Requirements

R1 (process): "Now Rung S5 via `dr-change-orchestrator`: seats in the
typed record, per docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md."

R2 (behavior): "Every run's own record must permanently say which
model sat in which seat."

R3 (process/design): "follow the rung-4 template exactly" — the named
mechanism to copy (module-fingerprints.v1's reader/payload/contract-
fence/writer/sweep-probe shape), same as R3 in rung 4's own capture
named `CONTAINED_WORKER_SHA256` — a suggestion to verify for
reachability against the concrete new payload, not a mandate that
overrides a genuine design difference the tree reveals.

R4 (process, ordering): "absence-tolerant READER first (every existing
committed root reads as "single seat, the manifest's provider")".

R5 (behavior, the reader's exact absence contract): every existing
committed root reads as **"single seat, the manifest's provider"** —
not merely "empty"/"no stamp"; the reader's absence answer must
specifically project the manifest's single uniform profile as the
implicit single seat, not just return nothing.

R6 (process/design): "then the payload (S2's spec expected a
seat-bindings sibling of module-fingerprints.v1 — verify that shape
against the tree, don't inherit it untraced)" — an instruction to
VERIFY, not to assume; "don't inherit it untraced" directly echoes rung
4's own C11 ("never adopt a named mechanism unverified").

R7 (process, ordering): "contract clause fencing it" — a
`_process_payload_contract`-shaped fencing clause, positioned after the
payload and before the writer.

R8 (process, ordering): "writer last".

R9 (process, ordering + isolation): "sweep probe in its own SEPARATE
commit with its own before/after capture on an unchanged tree."

R10 (process): "Accept: full gate 0 failed (P1's known pre-existing
failure excepted, named)."

R11 (process): "sweep byte-identical pre-probe."

R12 (process): "probe mutation-proven."

R13 (behavior, acceptance): "a two-profile home's run shows the stamp
naming both bindings."

R14 (behavior, acceptance): "a default home's run shows the
single-seat stamp."

R15 (process): "One rung only — S4b and S6 untouched."

R16 (design, from the plan document, quoted above): "Extend the
module-fingerprint stamp (or a sibling `seat-bindings.v1` payload — S2
decides) so every run records role-group → provider/model/
profile-digest." — names the exact content shape: a mapping from
role-GROUP (not expanded per-role) to a provider/model/profile-digest
identity.

R17 (process, from the plan document): "Reader first, absence-tolerant
(old roots read as "single seat, the manifest's provider"); contract
clause fencing the payload; sweep probe in its own separate commit with
its own before/after capture." — restates R4-R9 in the plan's own
words; carried as its own requirement because it is the plan's
independent phrasing, not merely a paraphrase of the operator's
message.

R18 (process, from the plan document, acceptance): "Accept: gate; sweep
byte-identical pre-probe; probe mutation-proven; testphase-style live
audit shows the stamp on a real run." — the plan's own accept line adds
one clause the operator's message does not literally restate:
"testphase-style live audit" — worth flagging as a possible additional
obligation (a live, not merely offline-regression, demonstration) for
`dr-spec-change` to reconcile against R13/R14's own literal wording
("a two-profile home's run shows the stamp" / "a default home's run
shows the single-seat stamp" — ambiguous between "a test asserts this"
and "an actual live run demonstrates this").

## Standing constraints

C1 (from `docs/map/INV-frozen-surfaces.md`, read in full this turn,
standing project-wide law, not specific to this program): the five
frozen surfaces require explicit operator approval for contact.
Surface 2 (`harness.py` — event application and well-formedness) is
squarely on this rung's path, per R3/R8's instruction to follow the
rung-4 template, which itself required (and received, via that
tranche's own REQUEST.md Amendment 4, R18) a narrow, explicit
authorization scoped to exactly an appender method plus one `_commit`
keyword parameter — nothing in `_apply_event`, nothing in
well-formedness. That prior authorization is scoped to module-
fingerprints.v1's own touch and does NOT automatically extend to a new,
different payload; `dr-spec-change` must obtain fresh operator words
for any `harness.py` contact this rung's own design needs, per the
rung-4 program's own established rule ("do not assume [prior] approval
carries over to a new touch") — cited here as informative precedent
from the sister program, not as binding law of THIS program, but
`docs/map/INV-frozen-surfaces.md` itself IS binding law of this
program and requires the same thing independently.

C2 (from CLAUDE.md, standing project instruction, quoted in every prior
rung's REQUEST.md): "The append-only record itself: fix READERS so old
roots stay valid; a change that invalidates existing replay-valid roots
is wrong by definition."

C3 (from `docs/map/SEAM-harness-x-verification.md`, "How to change it"
step 3, read in full this turn): "A new typed event channel moves in
one order: `Rule` and the payload field in `ontology/event.py` → the
`_apply_event` branch → a `_reset` attribute if it materializes state →
the `record_*` seam → a determinism finding in `verify_root` → a
channel entry in `report.py`. Stopping before the last step defaults
the new finding to `integrity`, and `integrity` is what decides `valid`
— so every recorded root that trips it flips." The rung-4 precedent
avoided this entirely by adding NO new `Rule` (riding the existing
`Rule.MEASURE`) and therefore owing no `report.py` entry — whether this
rung's design can do the same is a design question, not an assumption.

C4 (from `docs/map/SEAM-harness-x-verification.md`, "How to change it"
step 2, read in full this turn): "Reader before writer, always. A new
field on a durable record gets a default and a reader that decides what
its ABSENCE means for a root written before the field existed. Only
then may the writer emit it." Directly restates R4/R17.

C5 (from `docs/map/SEAM-harness-x-verification.md`, a Traps entry, read
in full this turn): "A census check expires; a partition check does
not... `tests/test_module_fingerprints.py`, which asserted that NO
committed root carries a module-fingerprint stamp — true only until the
first run recorded after rung 4's writer was committed." This rung's
own reader-side regression test must be written as a PARTITION claim
(absence is valid AND presence is valid, per the existing module-
fingerprints test's own corrected shape — see `DR-SEAM-harness-x-
verification`'s adjacent Traps entry crediting rung 4's own fix), never
as a census claim that will expire the moment this rung's own writer
lands a first live stamp.

C6 (freshly derived this turn, NOT stated by any operator message —
recorded because it directly bears on this rung's design choice): the
pre-existing, independently-reconfirmed **P1/P3** failure
(`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`,
tracked in every PARKED.md from Rungs S1 through S4) has a strong
candidate root cause verified fresh this session:
`Scheduler._module_fingerprints_recorded` (`scheduler.py:277`) is a
PER-INSTANCE guard that resets on every `Scheduler.__init__`, so
`deepreason continue`'s fresh `Scheduler` construction does not prevent
a second `module_fingerprints` stamp on the same root across a
continuation boundary. This was never diagnosed by any prior rung
(each PARKED.md entry deferred it to `deepreason-orchestrator`).
Recorded here, not fixed here (fixing a pre-existing defect is out of
this change-tranche's scope per this program's own convention — a
defect goes to `deepreason-orchestrator`), but the DESIGN CHOICE of
whether this rung's own new writer copies the same per-instance
idempotency shape (and therefore has the identical latent double-stamp
risk under continuation) or uses a different, continuation-safe
idempotency check is squarely `dr-spec-change`'s to make, with this
finding as its evidence.

C7 (program convention, established across Rungs S1-S4, restated here
for continuity): frozen surfaces bind this rung; the map moves in the
same commit as the code; every checklist step cites its requirement
number; PARKED.md records anything noticed but not fixed, with a
ready-to-send prompt.

## Open questions (for dr-spec-change)

Q1 — **the payload-naming decision the plan document says "S2 decides"
was never actually made.** Grepped fresh this turn: neither
`module-fingerprints` nor `seat-bindings.v1` appears anywhere in
`experiments/2026-08-06-change-seat-binding-design-s2/SPEC.md`. Two
live options, both structurally plausible against the current tree: (a)
extend `ModuleFingerprintV1` with `registry="seat-bindings"` entries
per bound group (`ModuleFingerprintV1.of` already accepts an arbitrary
`registry` string and an arbitrary `fingerprint: Mapping[str, Any]`,
and its own docstring anticipates exactly this kind of extension); (b)
a genuinely new sibling payload/schema
(`SeatBindingV1`/`SeatBindingsEventPayloadV1`, `schema:
Literal["seat-bindings.v1"]`), structurally closer to what a
role-group→profile MAPPING actually is (not a single module identity
dict) and closer to the plan's own literal words ("a sibling
`seat-bindings.v1` payload"). Needs a real measurement against the
tree (does `ModuleFingerprintV1`'s shape actually fit a
role-group→profile mapping without contortion, or does it need a
second, different record type inside one event either way), not an
assumption either direction.

Q2 — **a tension between S2's own prose and this rung's instruction.**
S2's SPEC.md (S3 item, rejecting Option B for S3) calls the future
deliverable "Rung S5's binding-provenance MANIFEST record" — but the
operator's own instruction this turn says "follow the rung-4 template
exactly," and rung 4's template lives entirely in the harness.py
event-log path, explicitly to AVOID frozen surface 4
(`run_manifest.py`). Is S2's "manifest record" phrasing simply loose
prose (the plan's own Rung S5 text never says "manifest," only "typed
record"), or does it signal a genuinely different, manifest-level
design was once contemplated that this rung's instruction has now
superseded? Needs reconciling at spec time, not silently resolved by
picking whichever reading is more convenient.

Q3 — **WHERE the writer fires**, given seat bindings are not a
registry like `SCHOOL_POPULATION`. The rung-4 precedent's emission site
(`Scheduler._record_module_fingerprints`, called from `Scheduler.run()`)
works because `schools.active_backend()` is available process-wide with
no threading needed. Seat bindings are resolved via
`resolve_seat_bindings()`/`load_seat_bindings()`, which read a
`DEEPREASON_HOME`-relative YAML file — already threaded today through
`RunPreparationService.prepare` (Rung S3/S4's own work) into the
compiled `RunManifest.roles`, NOT into anything a bare `Scheduler`
instance has independent access to reconstruct. Candidate sites,
neither yet verified against the actual live-run call graph: (a)
`Scheduler.run()`, mirroring the precedent exactly, but requiring seat
bindings to be threaded into the `Scheduler` constructor or resolved
freshly there (re-reading the YAML at write time rather than from the
already-compiled manifest the run is actually using — a potential
staleness risk if the file changes between prepare and run); (b)
`RunPreparationService.prepare` itself, which already has the resolved
`seat_bindings`/manifest in hand at the exact moment it also has a
writable `Harness` — but whether `prepare` currently holds a writable
harness handle at all, or hands one off elsewhere, is unverified. This
is exactly rung 4's own Q3/D7/D7a/D7b arc (three corrections, one
forced by the full gate) — expect this rung's WHERE question to need
the same kind of real tracing, not a first guess adopted uncritically.

Q4 — **whether R13/R14/R18's "a two-profile home's run shows the
stamp" and "testphase-style live audit" require an actual live
provider-backed run**, or whether an offline regression (MockEndpoint,
matching this program's established evidentiary pattern from Rungs
S1-S4) satisfies R13/R14 and the live audit is R18's own additional,
separate obligation (matching Rung S6's own plan text, "the offline
regression is the proof; one live attempt is the demonstration" —
though S6 is explicitly out of scope for this rung per R15).

Q5 — **whether this rung's writer should copy or deliberately avoid**
the per-instance idempotency shape identified in C6 as P1/P3's likely
root cause. Copying it exactly (per R3/R8's "follow the rung-4 template
exactly") reproduces a known defect in a new form; deviating from it is
itself a deviation from "the template exactly" that needs to be
recorded, not silent, per this program's own C11-style discipline
(inherited from the rung-4 program, restated as C7 above). Not fixing
P1/P3 itself — that stays out of scope, a `deepreason-orchestrator`
matter — but choosing NOT to manufacture a second instance of the same
failure mode is squarely this rung's own design responsibility.

## Amendments

**Amendment 1 (2026-08-07, operator message, verbatim).** Sent after
SPEC.md was committed and presented, directly ratifying the frozen-
surface authorization SPEC.md flagged as its single most judgment-laden
call:

> Explicit authorization for Rung S5 only: you may add the record_seat_
> bindings appender plus one _commit keyword to harness.py — zero
> change to _apply_event or well-formedness. This grant is not
> transitive to any later rung.

New requirement, quoting the operator's own words:

R19 (frozen-surface authorization, the narrowest reading is the binding
one, mirroring how R18 bound the rung-4 precedent this rung copies):
"you may add the record_seat_bindings appender plus one _commit keyword
to harness.py — zero change to _apply_event or well-formedness." This
authorizes EXACTLY two things and no third: (a) a `record_seat_bindings`
appender method in `harness.py`; (b) one `seat_bindings` keyword
parameter on `_commit`, forwarded into `Event(...)`. Nothing in
`_apply_event`; nothing in any well-formedness check. Any diff hunk in
`harness.py` outside these two is OUTSIDE this authorization and is a
stop condition, not a judgement call — matches exactly SPEC.md Item S5's
own already-declared shape (M6, re-verified against the current tree),
so this ratifies SPEC.md's reading rather than changing it.

R20 (process, non-transitivity, explicit): "This grant is not
transitive to any later rung." Binding precedent for the future: Rung
S5's own harness.py authorization does NOT carry forward to Rung S4b
(parked, its own frozen-surface-5 gate already recorded a fresh
authorization is owed) or to any future rung touching `harness.py`
again — each such rung's own `dr-spec-change` must obtain its own
words, exactly as SPEC.md's own forecast already argued when reasoning
about why rung 4's R18 did not automatically extend to this rung.

**Amendment 2 (2026-08-07, operator message, verbatim).** Sent
mid-`dr-execute-step`, in response to a budget-overrun STOP raised
before step 10's commit: actual `src/` + `tests/` lines already at 361
(seat_events.py 126, ontology/event.py 23, tests/test_seat_bindings_
record.py 212) against SPEC.md's own Budget headline of "Estimated
220-300 lines" for the whole tranche, with the harness.py writer,
scheduler.py emission site, preparation.py/seat_bindings.py mint-time
carrier, remaining S5-S7 tests, the map update and the probe commit
still unlanded:

> Budget overrun accepted for Rung S5 — operator words, ledger this
> verbatim as a REQUEST.md amendment. The SPEC.md headline (220–300
> lines) understated its own component itemization; re-derive the
> budget from the itemized list plus the module_events.py mirror
> (~500–650 insertions including tests and map) and record the
> corrected number in the amendment. Scope unchanged: no symbol beyond
> the spec's declared set, all stop conditions unchanged. Continue
> from the next unchecked step through step 28, then stop for review
> as before.

New requirement, quoting the operator's own words:

R21 (process, budget correction): "the SPEC.md headline (220–300
lines) understated its own component itemization" — verified fresh:
summing SPEC.md's own per-file estimates at their upper bounds
(`seat_events.py` 80 + `event.py` 20 + `harness.py` 30 +
`scheduler.py` 50 + `preparation.py` 20 + `seat_bindings.py` helper 15
+ tests 140 + map 60 + probe 20) already totals 435, and rung 4's own
precedent (this program's own closest mirror: `module_events.py`
landed at 105 lines against a smaller per-item estimate, its test file
`test_module_fingerprints.py` at 493 lines, and its own tranche
recorded a ~3-4x per-item overrun that was NOT a stop because no
separate, higher ceiling was crossed) predicts every one of this
rung's own components running similarly over its own per-item
estimate. **The corrected, binding budget for this tranche is
500-650 insertions across `src/` + `tests/` + `docs/map/` +
`tools/root_sweep.py` combined, superseding SPEC.md's own "220-300"
headline for the purpose of any future overrun check in this
tranche** (SPEC.md's own text is not edited — R21 is the ledgered
correction of record). No symbol, file, or requirement beyond
SPEC.md's already-declared Items S1-S11 is authorized by this
amendment; every stop condition already recorded (R19/R20's harness.py
bound, the four other frozen surfaces empty, no content/replay test
moving) is unchanged and unrelated to this correction.
