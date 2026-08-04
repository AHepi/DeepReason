# Spec for: rung 4 — every run records which modules built it
Traces: every item cites R/C numbers. Untraceable items are bugs.

**VERDICT: DESIGN-AND-STOP.** No design that satisfies R2 ("into the
run's TYPED RECORD") has zero frozen-surface contact. R14 asked for one;
R13's measurements show there is none. Per R7, R15 and C10 this tranche
stops here, at spec time, with the options priced. `dr-plan-steps` does
not run until the operator's words arrive.

## What R13 established, by measurement, against the real write path

The operator's instruction was "verify against the real write path" —
not reason about it. Four probes were run against the live tree. All
are reproducible from
`/tmp/.../scratchpad/q1_probe{,2,3}.py`; their substance is restated
here because scratch files are not evidence.

**M1 — a new top-level `Config` field moves the qualification subject
digest.** `qualification_subject_payload` (`qualification.py`) builds
`manifest_behavior` as `manifest.model_dump(...)` and pops exactly two
keys, `compiled_at` and `run_input_digest`. It does NOT pop
`source_config_hash` or `engine_config_json`, both of which are declared
fields on `RunManifest` (`run_manifest.py:1210` and `:1216`, class at
`:1168`). Measured with a real added field:

    schema v1..v6: source_config_hash MOVED   (all six versions)
    'source_config_hash' in manifest_behavior : True
    'engine_config_json' in manifest_behavior : True
    new key echoed into engine_config_json    : True
    >>> QUALIFICATION SUBJECT DIGEST MOVED
    >>> manifest sha256 MOVED

So **R4 ("the fingerprint rides Config") directly violates R6 ("NEVER
anything entering the qualification subject digest")** and moves the
manifest's own `sha256` besides. This is not a re-citation of rung 2
tranche 2's Traps entry — R15 forbade that — it is re-established here on
its own measurement, and it is STRONGER than that entry: the Traps entry
records the manifest hash moving; this probe shows the *qualification
subject* moving too, which is surface 5 rather than surface 4.

**M1a — an instrument error, recorded rather than buried.** The first
probe put the new field on a `Config` SUBCLASS and reported that the
manifest refuses to compile at all
(`V3_ENGINE_CONFIG_INVALID: engine config cannot reconstruct Config`).
That was an artifact, not a finding: the reconstruction validator at
`run_manifest.py:2601` does `Config.model_validate(reconstructed)`
against the REAL `Config`, which has `extra="forbid"`, so a subclass's
extra key fails where a genuinely added field would not. Corrected by
patching `deepreason.config.Config` itself — which is what the real
change would do — and re-run. **The corrected probe is the one quoted
above.** Had the artifact been trusted, this spec would have reported a
hard compile failure that does not exist.

**M2 — the surface-4 scrub line does neutralise it, completely.**
Re-running M1 with one added line in
`run_manifest.py::_versioned_source_config_data` (`data.pop("MODULE_
FINGERPRINTS", None)`, the exact shape rung 2 tranche 2 added for
`ENGAGED_CRITICISM_AUTHORITY`):

    schema v1, v3, v6: source_config_hash same
    manifest sha256 UNCHANGED
    >>> WITH SCRUB LINE: subject digest UNCHANGED

So Option A below is *technically sound* — and costs exactly one
frozen-surface touch, on surface 4, which R15 says may not be assumed.

**M3 — the named mechanism does not reach an ordinary run (C11).**
`CONTAINED_WORKER_SHA256` is emitted by
`ContainedSimulationBackend.fingerprint()` (`contained.py:485-496`) and
reaches a record only through `contained.py:529`
(`fingerprint=self.fingerprint()`) on a simulation ATTEMPT record. That
backend is constructed only at `capabilities/simulation.py:143` and
`:725`, i.e. only when the simulation capability actually runs — and
CLAUDE.md's own standing fact is that capability-channel use "is
STOCHASTIC across identical runs". **The precedent therefore stamps a
fingerprint into a capability-attempt record on a path most runs never
execute; rung 4 asks that EVERY run record one.** Per C11 the SHAPE is
adoptable (an identity dict, pinned at construction, carried on a typed
record) and the LOCATION is not. Recorded, not silently adopted and not
silently deviated from. This is the same shape as ERRATA E10.

**M4 — the gap rung 4 names is real, and no registry closes it (Q2).**
Three registries pin fingerprints: `SCHOOL_POPULATION`
(`capture/schools.py:323`, rung 3), `VerifierRegistry`
(`verification/registry.py:30`), `WORKLOADS`
(`workloads/registry.py:30`). Each pins at registration and re-checks on
resolve. **None of the three writes its fingerprint into the run's
record.** The only fingerprints that reach a record come from
verification backends (`verification/simulation.py`, `lean.py`,
`contained.py`), all on capability paths per M3. So rung 4's goal is not
already satisfied, and its gap is exactly: registries know what they
are, and the run does not record it.

**M5 — R16's own instruction touches a frozen surface.** R16 requires
any new typed channel to land its `report.py` entry in the same commit.
The classifier is `verification/report.py::_legacy_channel`
(`:141-155`), whose fallback is `return "integrity"`, and
`integrity_valid` decides `valid` (`:67-68, :93`). `verification/` is
frozen **surface 3**. So a design that adds a new verify_root finding
cannot satisfy R16 without touching surface 3 — the operator's own
guardrail and the frozen-surface rule point at the same file. R16's
alternative clause, "or not exist yet", is the escape: a design that
adds no finding owes no `report.py` entry.

## The three candidate designs, with measured contact

**Option A — `Config` field + surface-4 scrub line.** Literally what R4
says. Add `MODULE_FINGERPRINTS` (or similar) to `config.py`, add one
`data.pop(...)` line to `_versioned_source_config_data`, carry it into
whatever writes the record.
*Contact: surface 4 (`run_manifest.py`), certain, measured (M2).*
Cost ~1 line on the frozen file plus its Traps entry. Precedent exists
(rung 2 tranche 2) but R15 explicitly denies its transitivity. Without
the scrub line this option violates R5 AND R6 (M1).

**Option B — optional payload field on `Event`.** `ontology/event.py` is
NOT on the frozen list, and `Event`'s existing payload fields all carry
`exclude_if=lambda value: value is None` (`event.py:361-377`), so a new
optional field is **absent from the serialized bytes of every event that
does not set it** — R8's absence-tolerance is a property of the model
shape, already proven by the four payload fields that use it. A field
materializing no state needs no new `_apply_event` branch (that function
dispatches on payload presence, `harness.py:2019-2031`), and no new
finding means no `report.py` entry (M5), so R16 is satisfied by "or not
exist yet".
*Contact: `harness.py` — the `record_*` seam is the only append path,
and `harness.py` is named in `INV-frozen-surfaces`' own `Owns:` line.*
Whether adding a `record_*` method counts as "event application and
well-formedness" is genuinely arguable — which under C10 ("ANY plausible
contact") is itself the stop condition, not a licence to proceed.

**Option C — object-store record only.** `harness.blobs.put(...)` is
callable from outside `harness.py`, so a fingerprint blob written by
e.g. `ops.py` at run start touches none of the four frozen files.
*Contact: none.*
But the object would be referenced by no event, read by no
`verify_root` check, and invisible to replay — so it is a file inside
the root rather than part of the run's TYPED RECORD, which is what R2
asks for. It also makes C13's sweep probe nearly vacuous. **This is the
only zero-contact option and it is the one that least delivers R2.**
Recorded because R14 asked for zero contact and honesty requires saying
that the zero-contact option exists and is weak, rather than that none
exists.

## Items (conditional on the operator's design choice)

Every item below is written against Option B, the recommendation. If the
operator picks A or C, `dr-spec-change` re-runs before planning.

S1 (R1, R12): route through `dr-change-orchestrator`, phase by phase.
    accept: this tranche's artifacts exist in phase order.

S2 (R2, R3, M3, M4): a fingerprint from the registered population
backend reaches the run's typed record on an ORDINARY run — not only a
capability run. Shape copied from the precedent (identity dict, pinned
at construction); location not.
    accept: a test asserting a mock-endpoint `Scheduler` run's record
    carries the backend fingerprint, with no capability exercised.

S3 (R8, C12): the READER lands before the writer. Absence of the
fingerprint is valid — every existing committed root has none.
    accept: `verify_root` on a committed pre-change root reports the
    same violations before and after; a new test asserts an event
    without the field validates.

S4 (R9): full gate.
    accept: `python -m pytest tests/ -q -n 4` -> "0 failed".

S5 (R10, C13): root sweep byte-identical.
    accept: `python tools/root_sweep.py` -> 42 rows, 11 ERROR, empty
    diff against the accepted capture.

S6 (R10, C13) **— separate commit, and NOT the same commit as S2**: a
sweep probe in `tools/root_sweep.py` that actually READS the new
observable, asserting the attribute exists before reading it. Ordered
after S5's baseline so it never rides the `src/` change it judges, with
its own before/after capture on an unchanged tree.
    accept: the probe commit contains `tools/root_sweep.py` and no
    `src/` file; sweep re-run byte-identical on an unchanged tree.

S7 (R4, R5, R6, C10): frozen-surface diff empty.
    accept: `git diff --stat <base>..HEAD -- capabilities/state.py
    harness.py invariants.py run_manifest.py qualification.py` -> empty,
    OR the operator's approving words quoted in REQUEST.md.

S8 (C9): FULL `docs_verify` before any commit touching `src/`, never
`--fast` alone.
    accept: full run 0 failed pasted at each such commit.

S9 (R16, M5): if any new typed channel is built, its `report.py` entry
lands in the same commit — or no channel is built.
    accept: Option B builds no new finding, so no `report.py` entry is
    owed; asserted by the empty surface-3 diff in S7.

## Assumptions (operator may override)

A1 (Q2): "registered modules" = the school-population backend
(`SCHOOL_POPULATION`), the one rung 3 built, as the first and possibly
only module stamped. Smallest reading that makes rung 4 follow rung 3.
The other two registries (`VerifierRegistry`, `WORKLOADS`) are equally
eligible by the rung's words and would be a mechanical extension of the
same design — worth one sentence from the operator, folded into the
design question below rather than asked separately.

A2 (Q3): the fingerprint rides an optional payload field on an EXISTING
record rather than a new `Rule`/channel, because a new channel triggers
both C7's integrity-default trap and M5's surface-3 contact, and R16
explicitly sanctions "or not exist yet".

A3 (Q4): C13 already answered this — a byte-identical sweep does NOT by
itself prove absence-tolerance, so S6's probe is owed. No assumption
needed beyond adopting C13's rule as written.

## Questions for operator (STOP — non-empty)

**Q-OP1. Which design, given that none is both faithful to R4 and free
of frozen-surface contact?**

| Option | Contact | Delivers R2? | Cost |
|---|---|---|---|
| A — `Config` + scrub line | **surface 4**, certain (M1, M2) | yes | ~1 frozen line + Traps entry |
| **B — optional `Event` payload field** | `harness.py`, arguable (surface 2 owner) | yes | ~40-60 lines, no new channel |
| C — object-store blob only | **none** | barely — no event refers to it, `verify_root` never reads it | ~15 lines |

**Recommendation: Option B**, with the caveat stated plainly — it is the
only option that delivers R2 properly while adding nothing to a frozen
*format*. Its contact is with `harness.py` as a FILE (the `record_*`
seam), not with `_apply_event`'s dispatch logic, which is what surface 2
actually protects. `Event`'s `exclude_if` shape means no existing root's
bytes change and no existing event becomes invalid. But C10 says any
plausible contact stops for your words, and `harness.py` is named in
`INV-frozen-surfaces`' `Owns:` line, so I am not treating that
distinction as mine to make.

Option A is faithful to R4's literal words and is proven to work (M2),
but R15 forbids me assuming rung 2 tranche 2's approval carries over —
so if you want A, it needs your words for this touch specifically.

Option C is the only zero-contact answer to R14 and I do not recommend
it: it satisfies the letter of "object records" while producing
something replay cannot see, which is the opposite of "cross-run
comparisons are honest."

Please also confirm A1's scope in the same reply: **`SCHOOL_POPULATION`
only, or all three registries?**

## Out of scope (explicit)

- Rungs 5-7 — not requested; C1 forbids touching a second rung here.
- Widening any manifest schema or validator — R5, and surface 4.
- A second population backend — rung 5's job, as rung 3 already recorded.
- Retrofitting fingerprints into existing committed roots — impossible
  by definition (append-only) and forbidden by C7.

## Frozen-surface contact forecast

**NOT "none expected". Contact is plausible on every option that
delivers R2, and certain on Option A.** Checked against
`docs/map/INV-frozen-surfaces.md`'s five surfaces:

- **Surface 1** (`capabilities/state.py`): no contact on any option.
- **Surface 2** (`harness.py` event application): **plausible** on
  Option B — the `record_*` seam lives in `harness.py`, which the
  document's `Owns:` line names, though `_apply_event`'s dispatch would
  not change (`harness.py:2019-2031`).
- **Surface 3** (`invariants.py`, `verification/`): avoided by A2/A3 —
  no new finding, so no `report.py` entry (M5). Would become **certain**
  if a new typed channel were built.
- **Surface 4** (`run_manifest.py`): **certain** on Option A, measured
  (M1, M2). Avoided entirely by B and C.
- **Surface 5** (`qualification.py` subject digests): **certain** on
  Option A without the scrub line (M1); neutralised by it (M2); no
  contact on B or C.

Per C10 and R15 this stops the tranche here. SPEC.md is committed; the
operator's words are required before `dr-plan-steps` runs.

## Budget

Option B: ~40-60 lines across `ontology/event.py`, `harness.py`, the
population backend, and one new test; plus ~30 lines of map update; plus
a SEPARATE probe commit of ~10 lines in `tools/root_sweep.py` (S6).
3 commits, ordered: reader+writer+map, then gate/sweep, then the probe
alone. Under the 300-line guideline.
Frozen surfaces touched: **flagged — see the forecast above. STOP.**
