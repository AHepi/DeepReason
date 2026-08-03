<!-- DR-SEAM-schools-x-scheduler -->
Verified-at: 5eaf4bcb
Verify: python tools/docs_verify.py
Owns: src/deepreason/capture/schools.py, src/deepreason/scheduler/scheduler.py, src/deepreason/capture/ladder.py
Sides: DR-CON-schools, DR-SUB-scheduler

# Schools x scheduler

## The agreement

The scheduler no longer reaches school population directly. Every caller of
the four population operations — `init_schools`, `roster`, `allocate`,
`reseed` — resolves a NAMED BACKEND out of a registry first, and calls the
operation on that. `Scheduler.__init__` does
`schools.active_backend().init_schools(harness, config)`; `Scheduler.step`
does `schools.active_backend().allocate(...)`; the response ladder and the
CLI do the same for `roster`/`reseed`. The registry is
`SchoolPopulationRegistry` in `capture/schools.py`, mirroring
`verification/registry.py`'s proven shape (named registration, fingerprint
pinned at registration, re-checked on resolve), and it holds exactly one
entry, `"default"`, whose backend delegates to the same module-level
functions the callers used before — so the migration is behaviour-preserving
by construction, not by inspection.

The point of the indirection is rung 5: "one deliberately dumb alternative,
swapped in." An alternative population strategy registers under a SECOND
name, and no caller changes — only which name is resolved. That is why the
name lives in exactly one place (`_ACTIVE_BACKEND_ID`) rather than being
spelled at each of the ten call sites: rung 5 changes one constant's source,
not ten files.

Built across two tranches, both rung 3: Tranche A
(`experiments/2026-08-03-change-rung3-registry-in-front-of-school-population/`)
built and proved the registry with no caller consuming it; Tranche B
(`experiments/2026-08-03-change-rung3b-registry-call-site-migration/`)
migrated the callers and added the determinism proof.

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Backend contract | `capture/schools.py` | `SchoolPopulationBackend` (`Protocol`) | any registered backend must implement `fingerprint`, `init_schools`, `roster`, `allocate`, `reseed` — the same four operations the scheduler and response ladder already call today, named as a closed set |
| Default backend | `capture/schools.py` | `DefaultSchoolPopulationBackend` | delegates unchanged to the existing module-level `init_schools`/`roster`/`allocate`/`reseed` functions; today's behavior, made resolvable by name rather than removed |
| Registry mechanics | `capture/schools.py` | `SchoolPopulationRegistry` | `register`/`get`/`resolve`/`ids`/`fingerprint`/`fingerprint_is_pinned`, mirroring `verification/registry.py` field-for-field; a backend's fingerprint is pinned at `register` time and re-checked before every `get`, so a backend that mutates after registration is refused rather than silently trusted |
| Resolution point | `capture/schools.py` | `SCHOOL_POPULATION` (module singleton) | one pre-populated registry with `"default"` registered — mirrors `workloads/registry.py`'s `WORKLOADS` singleton precedent |
| The one place the NAME lives | `capture/schools.py` | `_ACTIVE_BACKEND_ID`, `active_backend()` | every caller goes through `active_backend()`; no call site spells a backend name, so rung 5 changes one constant's source rather than ten files |
| Population at construction | `scheduler/scheduler.py` | `Scheduler.__init__` | `schools.active_backend().init_schools(harness, config)`, guarded by `config.N_SCHOOLS > 0` |
| Allocation per cycle | `scheduler/scheduler.py` | `Scheduler.step` | `schools.active_backend().allocate(harness, problem, self.schools, config)` — which schools work a problem |
| Ladder interventions | `capture/ladder.py` | `respond` | four sites: `roster` then `reseed` on the school-convergence branch, and again on the attractor-orbiting branch |
| Operator commands | `cli/main.py` | the `schools` and `reseed` subcommands | three sites (`roster` twice, `reseed` once) |
| Report assembly | `report.py` | the schools section | one `roster` site |

`check: python -c "from deepreason.capture.schools import SCHOOL_POPULATION, DefaultSchoolPopulationBackend, active_backend; assert SCHOOL_POPULATION.ids() == ('default',); assert isinstance(SCHOOL_POPULATION.get('default').backend, DefaultSchoolPopulationBackend); assert isinstance(active_backend(), DefaultSchoolPopulationBackend)"`

Each check below asserts BOTH that the migrated form is present the exact
number of times expected AND that no bare call survives, so reverting any
single call site fails the check rather than passing on a leftover count.

`check: python -c "import pathlib,re; s=pathlib.Path('src/deepreason/scheduler/scheduler.py').read_text(); assert s.count('schools.active_backend()') == 2; assert not re.search(r'schools\.(init_schools|allocate)\(', s)"`
`check: python -c "import pathlib,re; s=pathlib.Path('src/deepreason/capture/ladder.py').read_text(); assert s.count('schools.active_backend()') == 4; assert not re.search(r'schools\.(roster|reseed)\(', s)"`
`check: python -c "import pathlib,re; c=pathlib.Path('src/deepreason/cli/main.py').read_text(); r=pathlib.Path('src/deepreason/report.py').read_text(); assert c.count('active_backend()') == 3 and r.count('active_backend()') == 1; assert not re.search(r'schools(_mod)?\.(roster|reseed)\(', c + r)"`

`Owns:` names the three files where this agreement is expressed in live-run
behaviour. `cli/main.py` and `report.py` carry migrated call sites too and
appear in the table above, but they are operator surfaces owned by
`DR-SUB-periphery` rather than either side of THIS seam; claiming them here
would add `Owns:` overlap without adding navigational truth.

## What is deliberately absent

**No second backend is registered.** Rung 3's own words: "the current
behavior as the only, default entry." A second, deliberately-dumb backend
(round-robin allocation or similar) is rung 5's job, not this one. Until it
exists, every resolution returns the same backend and the indirection is
provably behaviour-free — which is exactly what makes it safe to have landed
across the live scheduler.

`check: python -c "from deepreason.capture.schools import SCHOOL_POPULATION; assert len(SCHOOL_POPULATION.ids()) == 1"`

**No `Config` knob selects the backend, deliberately.** The obvious design —
a `Config` field naming the active backend — was rejected on evidence, not
taste: rung 2 tranche 2 established that ANY new top-level `Config` field
enters `source_config_hash`/`engine_config_json` and breaks pinned
canonical-hash goldens across several schema versions unless scrubbed inside
`run_manifest.py::_versioned_source_config_data`, which is
`DR-INV-frozen-surfaces` surface 4 and cost that tranche an explicit operator
approval gate. Rung 3 asks only for "the only, default entry"; rung 5's words
("a run configured with the alternative") are the ones that require
configurability. So the name sits in `_ACTIVE_BACKEND_ID`, and rung 5 pays
the frozen-surface cost then — with the operator's approval — if it decides a
`Config` field is the right source.

`check: python -c "import pathlib; s=pathlib.Path('src/deepreason/capture/schools.py').read_text(); assert '_ACTIVE_BACKEND_ID' in s; assert 'deepreason.config' not in s"`

**The other four school helpers do NOT go through the registry.**
`stance_weight`, `lineage_size`, `crossover_exemplars` and `STANCE_LIBRARY`
are still called as bare module functions from `scheduler.py`, `cli/main.py`
and `report.py`. That is scope, not oversight: rung 3 names exactly four
operations, and widening the protocol to cover conditioning helpers would
have made a bigger backend contract than the rung asked for. A reader who
expects them behind the registry should read this line, not file a defect.

`check: python -c "import pathlib,re; s=pathlib.Path('src/deepreason/scheduler/scheduler.py').read_text(); assert re.search(r'schools\.(stance_weight|crossover_exemplars)\(', s); assert 'schools.STANCE_LIBRARY' in s"`

## How to change it

1. **A second backend (rung 5) registers under a NEW name, never
   `"default"`.** `SchoolPopulationRegistry.register` already refuses a
   duplicate name (mirroring `VerifierRegistry`); this is the mechanical
   guarantee behind "the default path stays byte-identical."
2. **Change where the NAME comes from, not the call sites.** Ten call
   sites resolve through `active_backend()`; none of them names a backend.
   A run-selected backend therefore changes `_ACTIVE_BACKEND_ID`'s source
   only. If that source becomes a `Config` field, read "What is
   deliberately absent" first — that path touches a frozen surface and
   needs the operator.
3. **The bare module functions (`init_schools`/`roster`/`allocate`/
   `reseed`) are not to be deleted or folded into the backend class.**
   `DefaultSchoolPopulationBackend` delegates to them; they remain the
   actual implementation. Deleting them would break the default backend
   itself.
4. **A new call site uses `active_backend()`, and this document's counts
   move with it.** The three checks above pin exact per-file counts (2, 4,
   3+1). Adding a call site without updating them fails the map gate — by
   design: the counts are what make "every caller resolves" checkable
   rather than aspirational.
5. **Finish with the two byte-identity instruments.** The full gate and
   `python tools/root_sweep.py`; plus
   `tests/test_school_population_determinism.py`, which runs two
   mock-endpoint schedulers and asserts their event logs are byte-identical
   — the proof that the indirection changed nothing.

## Traps

- **Assuming the registry replaces the module functions.** It does not.
  `DefaultSchoolPopulationBackend` delegates to `schools.allocate` and its
  three siblings; they are still the implementation. A reader who expects
  those functions to be gone is looking for a deletion that was never
  planned — and would break the default backend if they performed it.
- **Testing the migration with the offline no-provider fixture.** Tranche
  B's spec recorded this the hard way: rung 3's own acceptance text names
  `tests/test_attached_evidence_citation.py`'s fixture, which
  `monkeypatch.setattr`s `deepreason.ops.run_scheduler` — and
  `ops.run_scheduler` is exactly where the `Scheduler` is constructed. That
  fixture therefore never reaches `init_schools` or `allocate`, so a
  byte-identity test built on it passes without executing one migrated
  line. `tests/test_school_population_determinism.py` uses the
  mock-endpoint `Scheduler` pattern from `tests/test_schools.py` instead,
  and asserts in-test that the roster is non-empty precisely so it cannot
  silently degrade into the same false pass.
- **Reading a per-file count in the checks above as decoration.** They are
  the enforcement. `grep -c` counting 2/4/3/1 plus a negative bare-call
  assertion is what distinguishes "every caller resolves through the
  registry" from "some do".
