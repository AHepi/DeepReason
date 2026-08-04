# Delivered: rung 3, tranche B — migrate the call sites through the registry
Branch: `claude/delivery-rungs-handover-m22sdy` @ `b7e53f11` (pushed,
tree clean). **Rung 3 is complete across both its tranches.**

## What changed

Every live caller of school population now resolves through the registry
Tranche A built. `src/deepreason/capture/schools.py` gained two things: a
module-level `_ACTIVE_BACKEND_ID = "default"` constant and an
`active_backend()` helper that returns
`SCHOOL_POPULATION.resolve(_ACTIVE_BACKEND_ID).backend`. All ten call
sites of the rung's four named functions were then migrated to go through
it — `scheduler/scheduler.py` (2: `init_schools` in `Scheduler.__init__`,
`allocate` in `Scheduler.step`), `capture/ladder.py` (4: `roster` and
`reseed`, twice each, inside the response ladder's live intervention
logic), `cli/main.py` (3: the `schools` display command and the manual
`reseed` command), and `report.py` (1: the report's roster read).

Behaviour is unchanged by construction: the sole registered backend
delegates to the same module functions the callers used before, and no
second backend exists. `tests/test_school_population_determinism.py` is
the proof — two mock-endpoint `Scheduler` runs over identically seeded
harnesses, one through the migrated path and one with `active_backend`
patched to call the bare functions directly, asserted identical on both
applied state and the full event log (excluding two named wall-clock
fields). A companion test permanently checks that this comparison can
still fail, by swapping in a backend that reverses allocation.

Three map documents moved in the same commits as the code:
`SEAM-schools-x-scheduler.md` (rewritten; 4 checks → 7, and the two
checks that asserted the migration had NOT happened were inverted into
per-file migrated counts plus negative bare-call assertions),
`CON-schools.md` and `SEAM-scheduler-x-rules.md` (both carried
form-brittle checks broken by legitimate reformatting; each was recorded
as an amendment BEFORE being fixed, and each replacement was
mutation-tested before it was written down).

Proof: full gate `3303 passed, 7 skipped, 0 failed` (isolated); root
sweep 42 rows / 11 ERROR, byte-identical against two independent prior
captures; `docs_verify` full + `--audit` + `--links` + `--coverage` all
clean across 50 documents and 803 checks; frozen-surface diff empty.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Route: `dr-change-orchestrator`" | done | every phase ran in order; two amendments recorded before the fixes they authorise (REQUEST.md Amendments 1-2) |
| R2 | "school population ... resolves through a named registry entry with the current behavior as the only, default entry" | done | commits `c76eda34`; VALIDATION S1-S5. **Now FULLY satisfied** — Tranche A satisfied only the registry's existence; this tranche is where live callers resolve through it |
| R3 | "the current behavior as the only, default entry" | done | `SCHOOL_POPULATION.ids() == ('default',)`; VALIDATION S5 |
| R4 | "Map preflight will name the seams — read them BEFORE the subsystems" | done | SPEC.md's Map preflight section named `DR-CON-schools`, `DR-SUB-scheduler`, `DR-SEAM-schools-x-scheduler`; map moved in commit `c76eda34` alongside the code, plus `55b16ce9` for the amendment |
| R5 | "full gate 0 failed" | done | `3303 passed, 7 skipped in 537.03s`, isolated; VALIDATION "Full gate" |
| R6 | "root sweep byte-identical" | done | 42 rows / 11 ERROR, empty diff against BOTH this tranche's step-12 capture and Tranche A's accepted capture; VALIDATION "Record-behavior preservation" |
| R7 | "a determinism test proving a run's outputs are byte-identical before/after the registry (reuse the offline no-provider fixture pattern from `tests/test_attached_evidence_citation.py`)" | **done-with-assumption A3** | commits `6cbacb03` + `863a0fa3`; VALIDATION "Flake re-verification". The PROPERTY is delivered; the NAMED FIXTURE is not the one used — see "The R7 fixture deviation" below, which is the one item in this delivery the operator most needs to read |
| R8 | "the call-site migration plus the full offline-no-provider-run determinism test" | done-with-assumption A3 | R2 and R7 together |
| R9 | "proceed" | done | exactly the plan that word approved (migrate the call sites, add the determinism test), nothing wider; rungs 4-7 untouched per C1 |
| Amendment 1 (S9) | `CON-schools.md`'s check broken by a forced line-wrap | done | commit `c76eda34`; VALIDATION S9 |
| Amendment 2 (S10) | `SEAM-scheduler-x-rules.md`'s slice marker broken by the same edit | done | commit `55b16ce9`; VALIDATION S10 |

No requirement is `not-done`; no requirement is `deferred`.

## The R7 fixture deviation (requirement vs record, resolved by dominance)

R7's own words name a fixture: "reuse the offline no-provider fixture
pattern from `tests/test_attached_evidence_citation.py`". That pattern is
`monkeypatch.setattr("deepreason.ops.run_scheduler",
finish_without_provider)`. `ops.run_scheduler` (`ops.py:328`) is
**precisely where the `Scheduler` is constructed** — "Meter + adapter +
conjecturer check + `Scheduler.run`". Its replacement never builds one.

The two call sites this tranche migrated inside the scheduler are
`init_schools` at `scheduler.py:272` (inside `Scheduler.__init__`) and
`allocate` at `scheduler.py:1804` (inside `Scheduler.step`). Neither is
reachable when the function that builds the `Scheduler` has been replaced.
A byte-identity test built on the named fixture would therefore compare
two runs, **neither of which executes one line of this tranche's changed
code**, and would pass while proving nothing.

The delivered test uses the mock-endpoint `Scheduler` pattern already in
`tests/test_schools.py` — `Scheduler(harness, adapter, config)` with a
`MockEndpoint` — which constructs a real `Scheduler` (hitting
`init_schools`) and whose `.run()` reaches `allocate`. The test asserts
in-test that the roster is non-empty, so "it actually executed the
migrated code" is checked rather than assumed.

This was resolved by `dr-ask-the-right-question`'s dominance test rather
than sent to the operator: no reading of the operator's own standing rule
("never claim more than the record shows") prefers a test that passes
without touching the changed code. **The property R7 asked for is
delivered and is strictly stronger than the one literally specified; the
fixture R7 named is not the one used.** If you want the named fixture's
shape regardless — e.g. as an additional end-to-end root-level check
layered on top — that is a fresh tranche, and this is the evidence you
would be overruling.

## An instrument limitation worth knowing beyond this tranche

`python tools/docs_verify.py --fast` reuses cached results for documents
whose OWN text is unchanged. Step 6 ran it and got 0 failed; the FULL run
at step 10 then found a real breakage in `SEAM-scheduler-x-rules.md` —
a document this tranche never edited, whose check reads
`scheduler/scheduler.py`, which this tranche DID edit.

**A green `--fast` is not evidence that the map survived a `src/` change.
Only the full run is.** This is a property of the instrument, not of this
change: any tranche that edits source without editing the documents that
read it can be told the map is clean when it is not. Surfaced here rather
than left in an amendment because it applies to every future tranche.

## Assumptions the operator may override

**A1 (Q2):** the backend name lives in a module-level constant
(`_ACTIVE_BACKEND_ID`) plus one `active_backend()` helper, NOT a `Config`
field. Rung 3's words are "the only, default entry"; rung 5's are the ones
that require configurability. A `Config` field would additionally have
cost a frozen-surface touch — rung 2 tranche 2 proved that any new
top-level `Config` field breaks pinned canonical-hash goldens unless
scrubbed in `run_manifest.py::_versioned_source_config_data` (surface 4),
which required an explicit operator approval gate. Rung 5 replaces this
constant's VALUE, not the call sites.

**A2 (Q1) — the one most worth your explicit attention:** all ten call
sites migrated, including the two read-only diagnostic ones
(`cli/main.py:906`'s `schools` display, `report.py:402`'s report). The
counter-argument is real and I did not invent it to dismiss it: a purely
diagnostic reader arguably SHOULD read the raw log truth rather than
whatever an active backend says the roster is, so that a broken backend
shows up in diagnostics instead of being reported self-consistently by
the thing that broke it. Today there is exactly one backend and it
delegates unchanged, so the two readings are behaviourally identical and
nothing observable turns on the choice. **It only bites once rung 5 adds
an alternative backend.** Migrated for coherence with the rung's own
sentence ("school population ... resolves through a named registry
entry"). Reverting is two lines in two files plus a map check update —
say the word and it is a small tranche, or fold it into rung 5's scoping
where the question actually becomes live.

**A3 (Q3):** the determinism test uses the mock-endpoint `Scheduler`
pattern, not R7's named fixture. See "The R7 fixture deviation" above.

## Map delta

changed: `docs/map/SEAM-schools-x-scheduler.md` (substantially rewritten
— "The agreement", "What is deliberately absent", the "Where it is
expressed" table, "How to change it", "Traps", and the `Owns:` header),
`docs/map/CON-schools.md` (one check made whitespace-tolerant),
`docs/map/SEAM-scheduler-x-rules.md` (one slice marker shortened).
created: none — the seam document already existed from Tranche A.
new checks: **+3** (`SEAM-schools-x-scheduler.md` went from 4 checks to
7; repo total 800 → 803). The three new ones pin the per-file migrated
counts AND assert no bare call survives, so reverting any single call
site fails the map gate. The two repaired checks were made robust rather
than merely fixed, and both were mutation-tested before being written
down, per the map's own "run it before you write it down" rule.

`Owns:` now reads `capture/schools.py, scheduler/scheduler.py,
capture/ladder.py`. `cli/main.py` and `report.py` were deliberately NOT
claimed — they belong to `DR-SUB-periphery` — and the document says so
in-line, so the choice is visible rather than silent.

left stale: none unexplained. `--stale` lists 19 documents; all 19 are
dismissed with reasons in VALIDATION.md. Eleven are flagged only because
this tranche's commit touched a file they own (three of those this
tranche actively updated; the other eight own a touched file but their
own claims are unaffected, and all were re-verified clean by the full
run). Six were flagged by earlier tranches and already resolved there.
Two were flagged by the unrelated pre-existing commit `2456da55`. The
breadth is itself informative: `scheduler.py` is owned or co-owned by
many documents, which is exactly why C6 named it the most sensitive file
this program has touched.

## Parked (not done, not promised)

See PARKED.md. In short: the A2 counter-argument above; rung 2's
remaining inventory candidates (Group C env-var switches, Group D
`STANCE_LIBRARY`); the 15 seam documents lacking a `Sweep:` header,
including this tranche's own; the pre-existing `Owns:` overlap between
`CON-schools.md` and `SUB-periphery.md`; the overstated `Config`-costs-
nothing line in `INV-frozen-surfaces.md`; and rung 5's second backend,
which is a later rung's work by definition.

## Status

Rung 3 is complete: Tranche A built the registry, Tranche B wired the ten
live callers to it and delivered the end-to-end determinism proof. Rungs
4-7 are untouched and remain the operator's call — per C1, no tranche
that touched rung 3 may begin rung 4.
