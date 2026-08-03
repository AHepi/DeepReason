<!-- DR-SEAM-schools-x-scheduler -->
Verified-at: 5eaf4bcb
Verify: python tools/docs_verify.py
Owns: src/deepreason/capture/schools.py
Sides: DR-CON-schools, DR-SUB-scheduler

# Schools x scheduler

## The agreement

Today the scheduler reaches school population directly: `Scheduler.__init__`
calls `schools.init_schools(harness, config)` and `Scheduler.step` calls
`schools.allocate(harness, problem, self.schools, config)`, both bare
module-level functions in `capture/schools.py`. This seam document exists
because rung 3 of `docs/HANDOVER_2026-08-03.md` asks that population resolve
through a NAMED REGISTRY ENTRY instead — "copy the proven shape from
`verification/registry.py`" — so a future alternative population strategy
(rung 5: "one deliberately dumb alternative, swapped in") can be registered
under a second name without the scheduler's own code changing at all, only
which name it resolves.

**This document is being written in Tranche A, before the scheduler side of
the agreement exists.** `capture/schools.py` gains a `SchoolPopulationBackend`
protocol, a `DefaultSchoolPopulationBackend` wrapping today's four functions
UNCHANGED, and a `SchoolPopulationRegistry` (mirroring `verification/
registry.py`: named registration, fingerprint pinned at registration,
re-checked on resolve) with exactly one registered entry, `"default"` — the
current behavior, and the only entry, per rung 3's own words. The scheduler
does not consume any of this yet; `Owns:` above names only
`capture/schools.py` for that reason. `docs/map/SUB-scheduler.md` gains
`DR-SEAM-schools-x-scheduler` to its own `Seams:` line now, in anticipation —
the interaction is real and identified even though only one side of it exists
in code today, which is exactly what this document exists to say plainly
rather than leave as a silent gap.

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Backend contract | `capture/schools.py` | `SchoolPopulationBackend` (`Protocol`) | any registered backend must implement `fingerprint`, `init_schools`, `roster`, `allocate`, `reseed` — the same four operations the scheduler and response ladder already call today, named as a closed set |
| Default backend | `capture/schools.py` | `DefaultSchoolPopulationBackend` | delegates unchanged to the existing module-level `init_schools`/`roster`/`allocate`/`reseed` functions; today's behavior, made resolvable by name rather than removed |
| Registry mechanics | `capture/schools.py` | `SchoolPopulationRegistry` | `register`/`get`/`resolve`/`ids`/`fingerprint`/`fingerprint_is_pinned`, mirroring `verification/registry.py` field-for-field; a backend's fingerprint is pinned at `register` time and re-checked before every `get`, so a backend that mutates after registration is refused rather than silently trusted |
| Resolution point | `capture/schools.py` | `SCHOOL_POPULATION` (module singleton) | one pre-populated registry with `"default"` registered — mirrors `workloads/registry.py`'s `WORKLOADS` singleton precedent; the ready-made point a future caller resolves against |

`check: python -c "from deepreason.capture.schools import SCHOOL_POPULATION, DefaultSchoolPopulationBackend; assert SCHOOL_POPULATION.ids() == ('default',); assert isinstance(SCHOOL_POPULATION.get('default').backend, DefaultSchoolPopulationBackend)"`

## What is deliberately absent

**No call site resolves through the registry yet.** `scheduler/scheduler.py`'s
two call sites (`init_schools`, `allocate`), `capture/ladder.py`'s four call
sites (`roster` and `reseed`, each twice, inside the response-ladder
interventions), and `cli/main.py`'s `reseed` command all still call
`capture.schools`'s bare module functions directly, exactly as before this
tranche. This is Tranche A of rung 3, split from the full rung because
building and proving the registry mechanism in isolation is smaller and
safer than bundling it with a live-scheduler migration in one commit
(`docs/HANDOVER_2026-08-03.md` rung 3's own "may take several tranches"
allowance). Reading this absence as an oversight would be wrong: the bare
functions are UNCHANGED and fully load-bearing today; the registry is an
additional, currently-unconsumed resolution path proven equivalent to them
(`tests/test_school_population_registry.py`), not a replacement that
something forgot to wire in. Tranche B is the wiring.

`check: ! grep -q "SCHOOL_POPULATION" src/deepreason/scheduler/scheduler.py`
`check: ! grep -q "SCHOOL_POPULATION" src/deepreason/capture/ladder.py`

**No second backend is registered.** Rung 3's own words: "the current
behavior as the only, default entry." A second, deliberately-dumb backend
(round-robin allocation or similar) is rung 5's job, not this one.

`check: python -c "from deepreason.capture.schools import SCHOOL_POPULATION; assert len(SCHOOL_POPULATION.ids()) == 1"`

## How to change it

1. **Tranche B's own scope, when it opens**: migrate `scheduler.py`'s two
   call sites and decide (its own `dr-spec-change`, not pre-decided here)
   whether `capture/ladder.py`'s and `cli/main.py`'s call sites — which
   perform live writes (`reseed`) or feed live decisions (`roster` inside
   `ladder.respond`) — also migrate, versus purely-diagnostic `roster()`
   reads (`report.py`; `cli/main.py`'s read-only `schools` display command)
   that carry no backend-dependent behavior and may reasonably stay direct.
2. **A second backend (rung 5) registers under a NEW name, never
   `"default"`.** `SchoolPopulationRegistry.register` already refuses a
   duplicate name (mirroring `VerifierRegistry`); this is the mechanical
   guarantee behind "the default path stays byte-identical."
3. **The bare module functions (`init_schools`/`roster`/`allocate`/
   `reseed`) are not to be deleted or folded into the backend class.**
   `DefaultSchoolPopulationBackend` delegates to them; they remain the
   actual implementation, callable directly by anything not yet migrated
   (which, per this document's own "What is deliberately absent" section,
   is everything, today).
4. **Update this document's `Owns:` to add `src/deepreason/scheduler/
   scheduler.py`** the moment Tranche B's migration lands — a call site
   that resolves through the registry is exactly the kind of agreement this
   document exists to track, and leaving `Owns:` unchanged after that
   migration would be the stale-seam mistake `docs/map/REC-change-a-
   seam.md`'s own Traps section warns about.

## Traps

- **Assuming the registry replaces the module functions.** It does not, and
  is not meant to in Tranche A at all — see "What is deliberately absent."
  A reader who sees `SchoolPopulationRegistry` and expects
  `schools.allocate` to be gone will be looking for a deletion that was
  never planned.
- **Registering a second backend before Tranche B lands.** Nothing today
  calls `SCHOOL_POPULATION.get(...)` at all, so a second registration would
  be inert — proving nothing, and pre-empting rung 5's own scoped work.
