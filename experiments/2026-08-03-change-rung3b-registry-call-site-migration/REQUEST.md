# Request: rung 3, tranche B — migrate the call sites through the registry
Captured: 2026-08-03. Rung 3's second and (intended) final tranche.
Tranche A (`experiments/2026-08-03-change-rung3-registry-in-front-of-
school-population/`) built the registry and delivered it; this tranche
wires the live callers to it and adds the end-to-end determinism proof
Tranche A's own scope split deferred. Authority is three sources, all
quoted verbatim below.

## Verbatim

> ### Rung 3 — a registry in front of one thing, changing nothing  [EXECUTE]
> Route: `dr-change-orchestrator`.
> Goal: school population (`capture/schools.py`: `init_schools`/`roster`/
> `allocate`/`reseed`) resolves through a named registry entry with the
> current behavior as the only, default entry. Copy the proven shape from
> `verification/registry.py` (name → backend, fingerprint pinned at
> registration, re-checked on call). Map preflight will name the seams —
> read them BEFORE the subsystems (`docs/map/SEAM-<a>-x-<b>.md`; recipe
> `docs/map/REC-change-a-seam.md`).
> Accept: full gate 0 failed; root sweep byte-identical; a determinism test
> proving a run's outputs are byte-identical before/after the registry
> (reuse the offline no-provider fixture pattern from
> `tests/test_attached_evidence_citation.py`).
>
> — `docs/HANDOVER_2026-08-03.md`, "The program: seven rungs, in order,"
> Rung 3; first captured in `experiments/2026-08-03-change-rung3-registry-
> in-front-of-school-population/REQUEST.md`, re-quoted here so this
> tranche is self-contained

> Tranche B, not opened here, is the call-site migration plus the full
> offline-no-provider-run determinism test the operator's own words
> describe.
>
> — Tranche A's `DELIVERY.md`, "What changed"

> **Tranche B: migrating call sites to resolve through `SCHOOL_POPULATION`.**
> Nothing live consumes the registry yet. `scheduler/scheduler.py`'s two
> call sites (`init_schools`, `allocate`) are the clearest candidates —
> they ARE "school population" in the rung's own sense. `capture/
> ladder.py`'s `roster`/`reseed` call sites (both inside the response
> ladder's live intervention logic) and `cli/main.py`'s `reseed` command
> (a manual write, same underlying action) are plausible but not
> pre-decided here — SPEC.md's own Q3 leaves this open for Tranche B's
> own `dr-spec-change`. `report.py`'s `roster()` call and `cli/main.py`'s
> read-only `schools` display command are plausibly OUT of scope for
> migration (pure diagnostics, no backend-dependent branching), but that
> too is Tranche B's decision, not this tranche's.
>
> — Tranche A's `PARKED.md`, first bullet

> proceed
>
> — operator's message this session, sent immediately after my closing
> report on Tranche A. That report's final line read: "Tranche B —
> migrating those call sites and adding the full determinism test — is
> not opened. That's your call whenever you want it." Per
> `dr-ask-the-right-question`'s reading table, a terse "proceed" after a
> stated plan is approval of EXACTLY that stated plan: open Tranche B,
> migrate the call sites, add the full determinism test — and nothing
> wider.

## Requirements

R1 (process): "Route: `dr-change-orchestrator`."

R2 (behavior): "school population (`capture/schools.py`:
`init_schools`/`roster`/`allocate`/`reseed`) resolves through a named
registry entry with the current behavior as the only, default entry." —
Tranche A satisfied this only for the registry's own existence; this
tranche is where LIVE callers actually resolve through it.

R3 (behavior): "the current behavior as the only, default entry" — no
second backend is registered by this tranche either.

R4 (process): "Map preflight will name the seams — read them BEFORE the
subsystems (`docs/map/SEAM-<a>-x-<b>.md`; recipe
`docs/map/REC-change-a-seam.md`)."

R5 (process): "full gate 0 failed."

R6 (process): "root sweep byte-identical."

R7 (artifact): "a determinism test proving a run's outputs are
byte-identical before/after the registry (reuse the offline no-provider
fixture pattern from `tests/test_attached_evidence_citation.py`)." —
the FULL end-to-end form this time, which Tranche A's A2 explicitly
deferred to this tranche.

R8 (process): "the call-site migration plus the full
offline-no-provider-run determinism test" — Tranche A's own definition
of this tranche's deliverable, quoted from its DELIVERY.md.

R9 (process): "proceed" — this session's authorization to open now,
approving exactly the plan stated to the operator (migrate the call
sites, add the full determinism test) and nothing wider.

## Standing constraints

C1: "One rung per tranche, minimum. A rung may take several tranches;
never let one tranche touch two rungs. Never begin rung N+1 in a tranche
that touched rung N." — `docs/HANDOVER_2026-08-03.md`, "Executor
calibration." This tranche is rung 3 only, same rung as Tranche A;
rungs 4-7 remain untouched.

C2: "Every rung ends with: acceptance commands run and pasted, tranche
committed and pushed, PARKED.md holding everything you noticed but did
not do." — same source.

C3: "Do not write to `docs/ERRATA_EXECUTOR.md` (operator-directed,
2026-08-03, superseding this file's earlier feed-instruction). That
ledger has ONE writer: the monitoring session. When anything in this
file or the skills misleads you, contradicts the record, or is silent
where you needed it to speak, record the observation in your own
tranche's artifacts (PARKED.md or the phase document where it
surfaced) with the evidence pointer, then resolve the question itself
via `dr-ask-the-right-question`." — same source.

C4: "The frozen surfaces (`docs/map/INV-frozen-surfaces.md`) bind every
rung: state digests, harness event application, replay-validation
formats, manifest schemas AND validators, qualification subjects.
Readers may be fixed; formats may not; a change that moves a committed
root's verdict is wrong by definition." — same source.

C5 (inherited, standing across this session): known flake
`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
can fail once under `-n 4`, rerun before diagnosing; commit and push at
every phase boundary; stop conditions are hard stops; where a spec is
silent, load `dr-ask-the-right-question` and route to the cheapest
authority — do not improvise; full gate must be run with `python -m
pytest`, never bare `pytest`.

C6 (this tranche specifically): `scheduler/scheduler.py` is the single
most sensitive file this program has touched — Tranche A's own SPEC.md
named it as the reason the rung was split at all ("bundling all of this
into one tranche means one commit touching the live scheduler with no
independent checkpoint if something goes wrong partway"). The
byte-identity instruments (full gate, root sweep, the new determinism
test) are what stand between this migration and a silent behavior
change.

## Open questions (for dr-spec-change)

Q1: WHICH call sites migrate. Verified fresh against the current tree
at capture time:
- `scheduler/scheduler.py:272` (`init_schools`), `:1804` (`allocate`)
- `capture/ladder.py:28`, `:73` (`roster`); `:39`, `:81` (`reseed`)
- `cli/main.py:1064` (`roster`) + `:1068` (`reseed`) — the manual
  `reseed` command
- `cli/main.py:906` (`roster`) — the read-only `schools` display command
- `report.py:402` (`roster`) — the read-only report
Explicitly NOT candidates (none is among the rung's four named
functions): `scheduler.py:951`/`:952`/`:955`
(`STANCE_LIBRARY`, `stance_weight`, `crossover_exemplars`),
`cli/main.py:911`/`:912` and `report.py:407`/`:408` (`stance_weight`,
`lineage_size`).

Q2: How a call site names WHICH backend to resolve. Rung 3 says "the
current behavior as the only, default entry", so hard-coding the name
`"default"` at each site may suffice; rung 5's "a run configured with
the alternative" implies a `Config` knob eventually. Whether that knob
belongs to rung 3 or rung 5 is underdetermined by both rungs' words.

Q3: R7's determinism test says "byte-identical before/after the
registry" — with the migration landing inside this tranche, "before"
and "after" cannot both be observed from the post-migration tree by a
single test run. Needs an interpretation that is actually executable
(e.g. a committed expected-output fixture, or a test asserting the
migrated path equals the bare-function path within one run) rather than
a literal two-tree comparison the test framework cannot express.

## Amendments

(none yet)
