# Spec for: Rung 6 — qualify plugins the way models are qualified
Traces: every item cites R/C numbers. Untraceable items are bugs.
DESIGN-AND-STOP: this document is the whole deliverable. No CHECKLIST.md,
no code change, follows in this tranche.

## Items

S0 (R1, R2): preflight, process only — resync branch, editable install,
read `CLAUDE.md`, read `docs/HANDOVER_2026-08-03.md` and the newest
`experiments/*/DELIVERY.md` files. Completed before `REQUEST.md` was
opened (REQUEST.md itself records both as DONE at capture time).
    accept: `git log --oneline -1` on branch
    `claude/delivery-rungs-handover-m22sdy` shows a head at or after
    `d2129791` (rung 5's delivered head) with a clean tree at the start
    of this tranche; `python -c "import deepreason"` exits 0.

S1 (R8): `docs/map/CON-*.md` (9 documents, all read in full), `CLAUDE.md`
(hard-won invariants list), `docs/ERRATA.md` (E1-E10, all read) | before:
no inventory exists of which promises about registered-module behavior
are enforced only by prose/recall vs. by a machine gate | after: the
"Folklore-promise inventory" section below, one row per candidate
promise, each with a source pointer, a gate-able-today verdict, and (for
gate-able ones) the check that would enforce it.
    accept: the inventory section exists, cites all 9 `CON-*.md`
    documents by name, cites `CLAUDE.md`'s hard-won-invariants list, and
    states `ERRATA.md`'s contribution explicitly (methodological, not
    inventory content — see below).

S2 (R11, C7, C8): NEW `src/deepreason/module_conformance.py` (protocol +
report model + battery runner, registry-agnostic) and
`src/deepreason/capture/schools.py` (wires it to `SCHOOL_POPULATION`) |
before: `SchoolPopulationRegistry.register`/`.get` check only that a
backend HAS the five protocol methods (`hasattr`) and that its
fingerprint stays pinned — nothing checks that those methods BEHAVE
according to the socket's stated promises, for any backend beyond the
two hand-written ones that happen to satisfy them by inspection (M1-M4
below) | after: on the first `get()`/`resolve()` of a given
`backend_id` (i.e., the first time a run would actually select it —
`population_backend()` and `active_backend()` both route through
`resolve`), the registry runs a small property battery (F1-F3 from the
inventory, the only three that are properties of the
`SchoolPopulationBackend` protocol itself rather than of one
implementation or of a different, unregistered socket) against a
throwaway `Harness`, caches a `ModuleConformanceReportV1` on the
registration, and refuses selection with a new typed error,
`SchoolPopulationBackendUnqualified` (subclass of
`SchoolPopulationRegistryError`, so existing `except
SchoolPopulationRegistryError` callers still catch it), naming which
check(s) failed. A backend that never gets resolved is never battery-run
— registration alone stays as cheap as it is today.
    accept (future execute tranche): a new test file mirroring
    `tests/test_rung5_alternative_backend.py`'s style proves, per check,
    (a) both shipped backends pass it (M1-M4), (b) a deliberately
    violating fixture backend fails it with the check named in the
    refusal (the durable-test-doctrine companion mutation, exactly as
    `test_a_call_order_rotation_would_fail_that_comparison` already does
    for one property today), and (c) `population_backend("<violating
    id>")` raises `SchoolPopulationBackendUnqualified` before any
    `Config`/`Scheduler` object is constructed.

S3 (R9, C3): no file in this tranche or in the proposed future
implementation names, reads, or fixes P7 (Arm B's `attempt-validity`
`verify_root` violation, `experiments/2026-08-04-change-rung5-dumb-alternative-backend/DELIVERY.md`,
"Post-delivery 3"). It stays parked.
    accept: `grep -n "attempt-validity" experiments/2026-08-04-change-rung6-plugin-conformance/SPEC.md`
    matches only this exclusion note (Items S3, its own accept line, and
    the Out-of-scope bullet) — no line proposes a fix.

S4 (R10, C4): this SPEC contains no rung-7 content (authority-as-policy,
`CON-authority.md`'s socket redesigned as a gate). `CON-authority.md`'s
promises appear in the inventory (S1) because R8 names "every
docs/map/CON-*.md document" without exception, and are marked
not-gate-able-today for the same structural reason as the other three
non-schools candidate sockets (no registry exists) — not implemented,
not planned, not scheduled by this document.
    accept: `grep -n "Rung 7\|authority as a declared policy" experiments/2026-08-04-change-rung6-plugin-conformance/SPEC.md`
    → hits only this sentence's own accept line and the Out-of-scope
    bullet; the inventory's `F-auth-1`/`F-auth-2` rows cite
    `CON-authority.md` by name without the literal phrase.

S5 (R3, R4, R5, R6, R7): route via `dr-change-orchestrator` →
`dr-capture-request` → `dr-spec-change`, stop. No `CHECKLIST.md`,
`VALIDATION.md`, or `DELIVERY.md` in this tranche directory; SPEC.md is
committed and pushed and the turn ends presenting it.
    accept: `ls experiments/2026-08-04-change-rung6-plugin-conformance/`
    → `REQUEST.md SPEC.md` only, at the point this tranche ends.

## Folklore-promise inventory (R8)

Walked, in full, per R8: all 9 `docs/map/CON-*.md` documents' socket-contract
("Promises"/"Must never do"), "The rules it obeys", and "Traps" sections;
`CLAUDE.md`'s "Hard-won invariants" list; `docs/ERRATA.md` E1-E10.

**Gate-able today** means: a `SchoolPopulationRegistry`-registered module
could be mechanically checked for it, because `SCHOOL_POPULATION` is the
only registry of swappable modules that exists in the tree (rung 3;
scope confirmed to `SCHOOL_POPULATION` alone by the operator in rung 4's
post-delivery A1). The four other candidate sockets rung 1 named
(conjecture source, criticism source, scheduler ranking, authority) are
each a single hard-coded implementation behind a documented contract —
"sockets on paper" — with no registry object to gate at all yet.

| ID | Promise | Source | Gate-able today? | Currently enforced by |
|---|---|---|---|---|
| F1 | A school-population backend is a pure function of the append-only log: it may add its OWN new artifacts, but must never change an existing artifact's `Status`/`hv`/`reach`, and must never touch `att`/`dep`/`carries` at all. | `CON-schools.md` socket contract ("Promises: the roster is a pure function of the append-only log") + "The rules it obeys" (same sentence, restated with its check) | **Yes** | A `grep` over `capture/schools.py`'s own harness-call surface (`CON-schools.md` line 37/109) — proves it for the two bare module functions both shipped backends delegate to, not for the `SchoolPopulationBackend.*` methods generically. A third backend with its own method bodies would not be caught. Verified empirically this session (M1) that both shipped backends satisfy the PROPERTY, not merely the grep. |
| F2 | `roster()` and `allocate()` are deterministic functions of `(log, config)` — repeated calls with no intervening log write return identical output; a hidden call-counter (or any other in-memory state) is a defect, because a reopened run must allocate exactly as the session that wrote it did, or replay diverges. | `CON-schools.md` "The rules it obeys" ("Allocation is a deterministic function of (log, config)") + `RoundRobinSchoolPopulationBackend`'s own docstring, which states the replay consequence explicitly | **Yes** | `tests/test_rung5_alternative_backend.py::test_allocation_is_a_function_of_the_log_not_of_call_order` and its companion mutation test — both scoped to `RoundRobinSchoolPopulationBackend` by name, not to the protocol. `DefaultSchoolPopulationBackend` has an equality-to-bare-function test, not a repeat-call determinism test. No check any THIRD backend would inherit. |
| F3 | `reseed()` is succession, not deletion: the predecessor artifact is never removed from the record. | `CON-schools.md` "The rules it obeys" ("Reseed is succession, not deletion... the roster is replayable because the log still holds both") | **Yes** | `tests/test_schools.py -k forced_convergence_triggers_reseed_and_replays`, scoped to the bare `reseed` function both shipped backends delegate to. A backend overriding `reseed()` itself (neither shipped one does) is unchecked. |
| — | A backend's fingerprint is pinned at registration and re-checked on every `get`/`resolve`. | `CON-schools.md` "The registry pins a backend's fingerprint..." + `SEAM-schools-x-scheduler.md` | N/A — already machine-gated | `SchoolPopulationRegistry.fingerprint_is_pinned`, exercised by `tests/test_school_population_registry.py::test_fingerprint_pinned_at_registration_and_rechecked_on_get`. Listed as a contrast: not everything found while walking the sources turned out to be folklore. |
| F-sched-1 | The operator's `SEED` question always wins a rank tie, in both scheduler selection modes. | `CON-scheduler-ranking.md` socket contract ("Promises") **and** `CLAUDE.md` hard-won invariants ("The operator's seed question always wins scheduler rank ties...") — the operator's own example in this rung's instruction quotes this exact promise | **No** | `Scheduler._select_problem` is one hard-coded method; no `SchedulerRankingRegistry` exists (scheduler ranking is a socket-on-paper only, rung 1). Enforced today by `tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero` — a regression test on the one implementation, not a conformance gate any alternative would have to pass, because there is no alternative path. |
| F-sched-2 | Import-role admission records never count as a "survivor" in the liveness-age term. | `CON-scheduler-ranking.md` + `CLAUDE.md` hard-won invariants | **No** | Same reason as F-sched-1: no registry to gate. |
| F-auth-1 | Everything defaults to `observe_only`; the calibration receipt defaults to absent. | `CON-authority.md` socket contract + "The rules it obeys" | **No** | `Config()` field defaults, consulted through `trial_authority_for` — a `Config`-driven branch inside `rules/crit.py`/`informal/trial.py`, not a registered/pluggable module. No `AuthorityRegistry` exists (rung 7's subject, DESIGN-AND-STOP, not this rung — C4). |
| F-auth-2 | The manifest authority vocabulary may never be widened. | `CON-authority.md` "The rules it obeys" (frozen-surface-adjacent) | **No** | Same reason; also frozen-surface territory (`INV-frozen-surfaces.md` surface 4), independent of any module boundary. |
| F-conj-1 | Every candidate's interface is compiled from the problem's own criteria, never invented independently. | `CON-conjecture-source.md` socket contract | **No** | `rules/conj.py::conj` is one function; no `ConjectureSourceRegistry` exists. |
| F-crit-1 | A manifest-bound criticism call never rediscovers authority from a mutable `Config`; passing no explicit policy value on a policy call raises. | `CON-criticism-source.md` socket contract + "The rules it obeys" | **No** | `rules/crit.py` is one module; no registry. |
| F-warr-1 | No registered warrant, no attack edge — and no registered target, no edge either. | `CON-warrants-and-attacks.md` "The rules it obeys" | **No** — not a module-registry concept at all | `adjudication/edges.py::build_att`; adjudication is not pluggable in this codebase. |
| F-cap-1 | A capability budget meters ONLY its own capability's records — the shared state maps pool ALL capabilities, so every count must filter by type. | `CON-capability-lifecycle.md` "The rules it obeys" **and** `CLAUDE.md` hard-won invariants (verbatim: "Per-capability budgets meter only their own capability's records...") | **No** — and notably this is NOT a promise currently held everywhere: `CON-capability-lifecycle.md`'s own Traps section records that `SimulationCapabilityController.consume` and `.accounting()` still pool both kinds today, unfixed. Simulation and research are two hard-coded capability KINDS, not entries in a registry — there is no module boundary to gate. Recorded here as the strongest evidence for WHY rung 6 exists: an ungated boundary (capability kind, not even a formal registry) already let an inconsistency this exact SHAPE of promise ship and stay unfixed. | (defect, not a held promise) |

**`CON-packs-and-token-economy.md` and `CON-run-identity.md`**: read in
full; neither owns a registry or a socket rung 1 named, and neither
states a promise about module-swappable behavior. Walked, no rows —
recorded so the walk is auditable as complete rather than silently
partial.

**`docs/ERRATA.md` (E1-E10)**: read in full. No entry states a promise
about registered-module behavior — every entry is about map-document
accuracy (a stale census number, a missing seam, a check pinned to an
uncommitted root). Its contribution to this tranche is methodological,
already adopted as C7/C8: E10 is the direct precedent for "state
properties, not mechanisms" (S2's F1-F3 are phrased as properties for
exactly this reason), and the Options table below follows E10's sibling
lesson from the same tranche (`docs_verify --fast` vs full mode) by
citing the FULL-mode-equivalent measurement, not a cached assumption.

**Count:** 3 gate-able-today (F1-F3, all `SCHOOL_POPULATION`-scoped —
S2's design), 8 walked-and-recorded-as-not-gate-able (F-sched-1/2,
F-auth-1/2, F-conj-1, F-crit-1, F-warr-1, F-cap-1), plus the two CON
documents confirmed to contribute nothing. No entry was invented outside
these three named sources; a handful of adjacent candidates found
elsewhere (an `init_schools` idempotence claim in `schools.py`'s own
docstring, not in any of R8's three sources; an empty-roster robustness
test) are listed under Assumptions/Out of scope rather than folded in.

## Assumptions (operator may override)

A1 (Q2): the battery is designed against the `SchoolPopulationBackend`
protocol generically (`module_conformance.py` takes no
`SCHOOL_POPULATION`-specific import), but is WIRED to `SCHOOL_POPULATION`
only — the one registry that exists — smallest reading consistent with
rung 4's operator-confirmed A1 ("`SCHOOL_POPULATION` only, other
registries stay parked"). `VerifierRegistry`/`WORKLOADS` (rung 4's P1)
and any future `SchedulerRankingRegistry`/`AuthorityRegistry` are
explicitly not this rung's job; the framework being registry-agnostic is
what makes adopting it for those later cheap, without claiming that
adoption here.

A2 (Q3): failure mode is refusal at `get()`/`resolve()` — the same point
`fingerprint_is_pinned` already gates on — via a new typed error rather
than a silent warning or a refusal at `register()`. Registration stays
possible for a non-conforming backend (so its report is inspectable);
selection is not. Chosen because it mirrors the existing fingerprint
mechanism exactly rather than adding a second gating shape.

A3 (Q3, corollary): the battery is LAZY and memoized per `backend_id`
(first `get()`/`resolve()` pays the cost once; every later call in the
process reads a cached boolean), not eager at `register()` — registration
happens at `capture/schools.py` import time, and `scheduler.py` imports
`capture.schools` at module scope (verified, M5); an eager battery
exercising a real `Scheduler` cycle would require importing
`scheduler.scheduler` from inside `schools.py`, a circular import
(Option A, rejected). A `Harness`/`Config`-only eager battery would avoid
the cycle (verified, M6) but would tax every process that imports
`deepreason.capture.schools` — including ones that never select a
backend — which the lazy design avoids entirely (Option D, rejected on
cost, not correctness).

A4 (Q4): "cost analysis" is answered by direct measurement this session
(M1-M7 below), not by building the feature and measuring it after the
fact — consistent with the DESIGN-AND-STOP discipline (measure, don't
reason) and with the rung-4 M1-M5 precedent this skill's own guardrails
(C8) now require.

A5: the first `get()`/`resolve()` of a given `backend_id` creates a
throwaway `Harness` under a fresh `tempfile.mkdtemp()` directory as a
side effect (consistent with how `CON-schools.md`'s own embedded check
and every existing school-population test already do this). This makes
`get()` no longer disk-side-effect-free on a cold cache — a real,
if minor, behavior change from today's pure in-memory resolution, flagged
here rather than left implicit.

## Out of scope (explicit)

- Rung 7 (authority as a declared policy) — C4, S4.
- P7 (Arm B's `verify_root` `attempt-validity` violation) — C3, S3.
- `VerifierRegistry`/`WORKLOADS` conformance (rung 4 PARKED P1) — not
  this registry.
- A `SchedulerRankingRegistry`, `AuthorityRegistry`,
  `ConjectureSourceRegistry`, or `CriticismSourceRegistry` — none exist;
  creating one is a modularization decision far larger than "qualify
  plugins," not requested, and would be its own rung.
- `init_schools`'s "idempotent across reloads" docstring claim and the
  empty-roster robustness test (`test_an_empty_roster_allocates_to_nobody`)
  — real properties, but not sourced from R8's three named documents;
  offered here as a possible Option D-lite follow-up (2 more checks,
  ~20 more lines) rather than folded into F1-F3 unasked.
- Stamping the conformance verdict into the run's typed record (mirroring
  rung 4's fingerprint stamp) — plausible follow-on, priced separately
  under Options as a rejected-for-now extension, not requested by R11's
  words ("must pass before a run accepts it" is satisfied by refusing
  selection; recording that it passed is a different, additive promise).
- CLI surface (a `deepreason plugins qualify` command) — considered and
  priced as Option C, rejected on cost grounds (M1-M4 below).

## Frozen-surface contact forecast

none expected — checked against `INV-frozen-surfaces.md`'s five surfaces
and the `Config`-field trap:

- `capabilities/state.py`, `harness.py` (write path), `invariants.py`,
  `run_manifest.py`, `qualification.py` — S2 touches none of these
  files. `module_conformance.py` and `capture/schools.py` only READ
  `Harness` (construct one, call existing public methods); they do not
  modify `harness.py`, add an event type, or touch `_apply_event`.
- No new `Config` field is proposed (A3's design deliberately mirrors
  rung 5's precedent of keeping backend-selection state off `Config` and
  out of `source_config_hash`/the manifest entirely — `population_backend`
  already does this; S2 adds no new knob at all, so
  `_versioned_source_config_data` needs no new line and the
  `Config`-field trap (`INV-frozen-surfaces.md` Traps, last entry) does
  not apply).
- No qualification-subject-digest contact: `module_conformance.py` does
  not import or touch `qualification.py`.

## Blast-radius census

Every existing hit on the symbols S2 would change, from
`grep -rn "SCHOOL_POPULATION\b" tests/ docs/map/`,
`grep -rn "SchoolPopulationRegistry\|SchoolPopulationBackend\b" tests/ docs/map/`,
`grep -rn "population_backend(" tests/ docs/map/`, and
`grep -rn "SchoolPopulationRegistryError\|UnknownSchoolPopulationBackend" tests/ docs/map/`
(full hit lists pasted below the table; every hit classified, none
omitted):

| File | What it asserts | Classification |
|---|---|---|
| `tests/test_school_population_registry.py` (9 tests, `SCHOOL_POPULATION`/`SchoolPopulationRegistry`/error-class hits) | Registration, resolution, fingerprint pinning, and default-backend/bare-function equivalence, all against the two SHIPPED backends | MUST NOT MOVE — both shipped backends satisfy F1-F3 (verified, M1-M4); `get()`/`resolve()` must keep succeeding for `"default"` |
| `tests/test_rung5_alternative_backend.py` (15 tests, all `SCHOOL_POPULATION.get("round-robin")`/`population_backend(...)` hits) | Registration, allocation behavior, and the scoped-selection context manager, all against `"round-robin"`, plus one already-existing mutation test (`_CallOrderRotation`) proving F2 is falsifiable | MUST NOT MOVE for the 14 hits against the two shipped backends; the `_CallOrderRotation` test is a private local subclass never registered — EXPECTED TO MOVE ONLY IN SPIRIT: S2's future test file adds a REGISTERED version of the same shape (Item S2's accept criterion (b)), this test itself is untouched |
| `tests/test_module_fingerprints.py` (2 `SCHOOL_POPULATION.fingerprint(...)` hits) | Rung 4's fingerprint-recording, unrelated to conformance | MUST NOT MOVE — S2 does not touch `fingerprint()` or `module_events.py` |
| `docs/map/SEAM-schools-x-scheduler.md` (5 hits: the backend-contract row, the registry-mechanics row, two embedded checks, prose) | The registry's current shape and its two embedded checks | EXPECTED TO MOVE — a future execute tranche owes this document a new row (the conformance gate) and possibly a widened embedded check; not touched by THIS tranche (no `src/` change lands here) |
| `docs/map/CON-schools.md` (2 hits: the rung-5 table row, the fingerprint-pinning paragraph) | Registry shape and fingerprint-pinning prose | EXPECTED TO MOVE — same reason; `Owns:` would gain `module_conformance.py` in a future execute tranche |
| `module_conformance.py` (new file) | nothing yet — file does not exist | no hits, correctly — new file |

No hit was omitted. No test anywhere asserts a closed/exhaustive set of
`SchoolPopulationRegistryError` subclasses, so adding
`SchoolPopulationBackendUnqualified` as a new subclass breaks nothing
(checked: `grep -rn "SchoolPopulationRegistryError\|UnknownSchoolPopulationBackend" tests/ docs/map/`
above is the complete hit list).

## Measurements

M1: both shipped backends satisfy F1 (purity) today, checked as a
PROPERTY (not the existing file-level grep) —
```
$ python -c "<script constructing a fresh Harness, snapshotting state.status/hv/reach/att/dep/carries, running init_schools/allocate/reseed for each registered backend, and diffing>"
default    att_unchanged= True dep_unchanged= True carries_unchanged= True status_existing_preserved= True
round-robin att_unchanged= True dep_unchanged= True carries_unchanged= True status_existing_preserved= True
```
— supports S2's design not breaking either shipped backend (both would
pass F1 on day one).

M2: both shipped backends satisfy F2 (determinism) and F3 (reseed
succession) today —
```
default    allocate_deterministic= True roster_deterministic= True reseed_predecessor_persists= True
round-robin allocate_deterministic= True roster_deterministic= True reseed_predecessor_persists= True
```
— supports the same claim for F2/F3.

M3: per-check cost, warm process —
```
$ python -c "<time 20 cycles of Harness()+init_schools()+allocate()>"
20 harness+init_schools+allocate cycles: 0.2262s total, 11.31ms each
```
— supports the cost-analysis claim that a battery entry costs
single-digit-to-low-double-digit milliseconds, dominated by real `Harness`
disk I/O in a temp directory, not by computation.

M4: full 3-check battery, both shipped backends, one process —
```
$ python -c "<run F1+F2+F3-equivalent calls for both registered backends and time it>"
full battery, both shipped backends: 31.9ms total
```
— supports the headline cost-analysis number: ~32ms, one-time, lazy,
for the whole `SCHOOL_POPULATION` registry as it stands today.

M5: `scheduler.py` imports `capture.schools` at module scope (the
circular-import risk Option A/A3 depends on) —
```
$ grep -n "capture.schools\|capture import schools\|from deepreason.capture" src/deepreason/scheduler/scheduler.py
16:from deepreason.capture import detection, ladder, schools
```

M6: `Harness`/`Config` do not import `capture.schools` or
`scheduler.scheduler`, directly or transitively — an eager,
`Harness`-only battery inside `schools.py`'s own module body would NOT
create a cycle (this is what makes Option D viable in principle, even
though it is rejected on cost, not correctness) —
```
$ python -c "import sys; import deepreason.harness; import deepreason.config; print('schools pulled in:', 'deepreason.capture.schools' in sys.modules); print('scheduler pulled in:', 'deepreason.scheduler.scheduler' in sys.modules)"
schools pulled in: False
scheduler pulled in: False
```

M7: reference cost for the analogy this rung's title makes ("qualify
plugins the way models are qualified") — model qualification's full
battery, already established and cited rather than re-run (re-running it
costs real provider spend and is out of scope for a design tranche):
~14 minutes, ~1160 provider calls per `(home, provider profile)` subject
digest (`CLAUDE.md` "Qualification caches by subject digest";
`docs/HANDOVER_2026-08-03.md` "Environment facts that bite"; corroborated
live in `experiments/2026-08-04-change-rung5-dumb-alternative-backend/DELIVERY.md`
"Post-delivery 3": "1140 calls, `cache_reused: false`").

M8: existing test suite for the registry runs in ~1.2s today (24 tests,
no battery yet) —
```
$ python -m pytest tests/test_school_population_registry.py tests/test_rung5_alternative_backend.py -q
........................                                                 [100%]
24 passed in 1.22s
```
— baseline for comparing S2's future added test file's cost.

## Options

**A — eager battery at `register()` time, using a live `Scheduler` +
`MockEndpoint` cycle** (mirrors `CON-schools.md`'s existing embedded
fingerprint check). Files: `capture/schools.py` only. Frozen contact:
none directly, but REJECTED — cites M5: `schools.py` would need to
import `scheduler.scheduler`, and `scheduler.py` already imports
`capture.schools` at module scope, so this is a circular import that
would break `import deepreason.scheduler.scheduler` outright, not a
subtle risk. ~lines: ~100 (fewer checks needed, since one full cycle
exercises more implicitly) but architecturally broken. Risk: fatal.

**B — eager battery at `register()` time, `Harness`/`Config`-only (no
`Scheduler`, no LLM adapter)**. Files: `capture/schools.py`,
`module_conformance.py`. Frozen contact: none (M6). ~lines: ~300-350.
Risk: low correctness risk, but taxes EVERY process that imports
`deepreason.capture.schools` (which `scheduler.py` does unconditionally,
so effectively every process that imports the scheduler) with ~32ms
(M4) even when that process never selects a school-population backend
at all — e.g. `deepreason status`, `deepreason --help`, or any test file
that imports `Scheduler` for an unrelated reason. REJECTED — cites M4
(the cost is real, even if small, and paid by callers who derive no
benefit from it) in favor of C.

**C — a `deepreason plugins qualify <registry> <backend>` CLI command,
producing an on-disk cached `PluginConformanceRecordV1` (mirrors
`QualificationTierRecordV1`), with `get()`/`resolve()` refusing any
backend with no on-disk PASSING record**. Files: `cli/main.py`, a new
cache module, `capture/schools.py`. Frozen contact: none expected, but a
much larger blast radius — EVERY existing hit in the census above
(`tests/test_school_population_registry.py`,
`tests/test_rung5_alternative_backend.py`,
`tests/test_module_fingerprints.py`) would start failing on a clean
checkout until the new command has been run once, because there would be
no cached record yet; today's tests construct backends and resolve them
with no setup step. ~lines: ~550-650 (CLI + cache plumbing on top of
D's ~300-350). Risk: medium — the UX mirrors model qualification's own
shape faithfully, but M4 shows the operation this mirrors costs 5 orders
of magnitude less than what it is being modeled on (~32ms vs ~14 min,
M4 vs M7); a disk cache buys speed the operation does not need, at the
cost of a new stateful precondition every caller must now satisfy.
REJECTED — cites M4 and M7 together, and the blast-radius census.

**D — lazy, memoized battery on first `get()`/`resolve()` of a given
`backend_id`, `Harness`/`Config`-only, cached in-process on the
registration (no disk cache)**. Files: `capture/schools.py`,
`module_conformance.py` (new), plus a future execute tranche's map
delta to `CON-schools.md`/`SEAM-schools-x-scheduler.md`. Frozen
contact: none (M6, same as B). ~lines: ~350-450 including tests (M8
gives the current 24-test/1.22s baseline this would extend) and the
owed map delta. Risk: low — pays the ~32ms (M4) only in processes that
actually select a backend, exactly once per `backend_id` per process,
and mirrors the EXISTING `fingerprint_is_pinned`-on-`get()` gating shape
(A2) rather than inventing a new one. First cold `get()`/`resolve()`
becomes disk-side-effect-free no longer (A5) — the one behavior change
worth naming, and it is the same side effect every existing test in the
census already produces via `tmp_path`/`tempfile.mkdtemp()`.
**CHOSEN — cites M4, M5, M6, M7, and the blast-radius census together.**

## Budget

~350-450 lines across 2-3 files (`module_conformance.py` new,
`capture/schools.py` edited, `docs/map/CON-schools.md` +
`docs/map/SEAM-schools-x-scheduler.md` edited in the same commit as the
code per `SCHEMA.md` rule 1) plus a new test file (~150-200 lines,
sized against M8's 24-test/1.22s baseline), IF the operator approves
Option D and a future tranche executes it. Frozen surfaces touched: none
(forecast above). Estimated 2-3 commits: (1) `module_conformance.py` +
wiring + `SchoolPopulationBackendUnqualified`, (2) tests including the
three per-check mutation fixtures, (3) map delta. Exceeds the ~300-line
soft guideline; if approved, `dr-plan-steps` should group the checklist
as framework-plus-two-checks then the third check plus map polish rather
than splitting into two tranches, since `SCHEMA.md` rule 1 (map moves in
the same COMMIT as the code) makes a clean file-level split across
tranches awkward for no real isolation benefit.

**This tranche itself spends 0 `src/` lines and 0 commits beyond this
SPEC** — R4/R6 (DESIGN-AND-STOP) mean nothing above is built now.

Rubric: 6/6 yes — every R has a spec item with a machine-decidable
accept (S1-S5, table above); blast-radius census pasted and every hit
classified (table above, "no hits" stated for the one genuinely new
file); frozen-surface contact forecast recorded (none, with the
`Config`-field trap explicitly checked and found inapplicable); every
mechanism the request's own words name — "the operator's seed question
always wins rank ties" — traced to real code (`CON-scheduler-ranking.md`
+ `CLAUDE.md`) and correctly excluded from the concrete design rather
than silently adopted, because no registry reaches it (F-sched-1); every
design claim in Options is measured (M1-M8), not asserted, and every
rejection cites a measurement; nothing above is untraceable to an R/C
number (S1-S5's headers, A1-A5's `(Qn)` tags, and Out-of-scope's bullets
all cite one).
