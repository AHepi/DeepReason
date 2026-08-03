# Request: rung 3 — a registry in front of one thing, changing nothing
Captured: 2026-08-03, from `docs/HANDOVER_2026-08-03.md`'s Rung 3
section and this session's continuation message opening it.

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
> Rung 3

> Continue to run 3. Read Claude.md first then proceed.
>
> — operator's message this session, after rung 2's three tranches
> (inventory, criticism-authority switch, bridge unification) all
> delivered; the explicit go-ahead to open rung 3 now

## Requirements

R1 (process): "Route: `dr-change-orchestrator`."

R2 (behavior): "school population (`capture/schools.py`:
`init_schools`/`roster`/`allocate`/`reseed`) resolves through a named
registry entry with the current behavior as the only, default entry."

R3 (behavior): "Copy the proven shape from `verification/registry.py`
(name → backend, fingerprint pinned at registration, re-checked on
call)."

R4 (process): "Map preflight will name the seams — read them BEFORE the
subsystems (`docs/map/SEAM-<a>-x-<b>.md`; recipe `docs/map/REC-change-a-
seam.md`)."

R5 (process): "full gate 0 failed."

R6 (process): "root sweep byte-identical."

R7 (artifact): "a determinism test proving a run's outputs are
byte-identical before/after the registry (reuse the offline no-provider
fixture pattern from `tests/test_attached_evidence_citation.py`)."

R8 (process): "Continue to run 3. Read Claude.md first then proceed." —
this session's explicit go-ahead to open now.

## Standing constraints

C1: "One rung per tranche, minimum. A rung may take several tranches;
never let one tranche touch two rungs. Never begin rung N+1 in a tranche
that touched rung N." — `docs/HANDOVER_2026-08-03.md`, "Executor
calibration." This tranche is rung 3 only; rung 2's own work (all three
tranches) is already fully delivered and out of scope here.

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
via `dr-ask-the-right-question`." — same source. Binding: no
`docs/ERRATA_EXECUTOR.md` entries from this session for this tranche.

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

## Open questions (for dr-spec-change)

Q1: R2/R3 name `capture/schools.py`'s four functions
(`init_schools`/`roster`/`allocate`/`reseed`) and
`verification/registry.py`'s "proven shape" but do not specify exact
new symbol names, module location for the registry, or which of the
four functions actually needs to change vs. which are read-only
call-through. Needs a fresh read of both files before any interpretation.

Q2: R7 says "reuse the offline no-provider fixture pattern from
`tests/test_attached_evidence_citation.py`" — needs reading that file to
understand what pattern is actually meant before deciding the new
determinism test's shape.

Q3: The rung text does not specify whether the registry must support
registering MULTIPLE backends now (even though only one, "the current
behavior," is used today) or whether a single-entry registry shape
suffices for rung 3, with multi-backend support deferred to rung 5
("one deliberately dumb alternative, swapped in... register it as a
non-default entry"). Rung 5's own text implies rung 3 only needs to
support ONE default entry; rung 5 is where a second entry gets added —
this should resolve without asking, but needs confirming against both
rungs' exact words before proceeding.

## Amendments

(none yet)
