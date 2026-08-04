# Parked — noticed or deferred during this tranche, deliberately not done

- **A2's counter-argument: the two read-only diagnostic call sites
  (`cli/main.py:906`'s `schools` display, `report.py:402`'s report) were
  migrated, and arguably should not have been.** A diagnostic reader
  arguably should read the raw log truth rather than whatever an active
  backend reports, so that a broken backend is visible in diagnostics
  instead of being described self-consistently by the thing that broke
  it. Behaviourally identical today (one backend, delegating unchanged);
  the question only becomes live once rung 5 registers an alternative.
  Recorded in SPEC.md's "Out of scope", VALIDATION.md's assumption audit,
  and DELIVERY.md so the operator has what they need to overrule it.
  Reverting is two lines in two files plus a map-check update.

- **Rung 5's second backend ("one deliberately dumb alternative, swapped
  in").** Registering one now would be inert and would pre-empt rung 5's
  own scoped work. Rung 3's words are explicit: "the current behavior as
  the only, default entry." Carried forward unchanged from Tranche A's
  PARKED.md.

- **A `Config` knob selecting the backend.** Rung 5's job, not rung 3's
  (A1). Building it here would touch `DR-INV-frozen-surfaces` surface 4
  — `run_manifest.py::_versioned_source_config_data` must scrub any new
  top-level `Config` field or pinned canonical-hash goldens break, as
  rung 2 tranche 2 proved — for zero rung-3 benefit. When rung 5 does
  this, `_ACTIVE_BACKEND_ID`'s VALUE is what changes, not the ten call
  sites.

- **Rung 2's remaining inventory candidates, unchanged from the inventory
  tranche's own PARKED.md and still the operator's call**: Group C's
  env-var-sourced switches (`DEEPREASON_SIMULATION_RUNNER`,
  `DEEPREASON_RESEARCH_ALLOWLIST`/`_MAX_REQUESTS`/`_MAX_SOURCES`,
  `DEEPREASON_CONFIG_REFEREE`) — converting an env-var invocation surface
  to a `Config` field changes how operators invoke a preset, not just
  where a literal lives; and Group D's `STANCE_LIBRARY`
  (`capture/schools.py`) — content curation, not a mode switch, with no
  alternative value to choose between. Neither addressed here; this
  tranche is rung 3 only, per C1.

- **`docs_verify --fast` cannot see a check broken by an edit to a file
  the document merely READS.** Step 6's `--fast` reported 0 failed and
  missed `SEAM-scheduler-x-rules.md`; only the full run at step 10 caught
  it. This tranche worked around it (always run the full sweep before
  claiming the map is intact) but did NOT change the instrument. A real
  fix — invalidating a document's cache when any file its checks read has
  changed — was neither designed nor requested. Recorded here and in
  DELIVERY.md because it generalises to every future tranche, not just
  this one.

- **Fifteen seam documents carry no `Sweep:` header**, including this
  tranche's own `SEAM-schools-x-scheduler.md` (carried forward from
  Tranche A's PARKED.md, still true after the rewrite). `--coverage`
  reports 0 findings on the 6 seams that DO have one. Adding a `Sweep:`
  header was not requested and the majority of seam documents in this
  repo lack one, so this tranche matched the prevailing pattern rather
  than unilaterally changing it. Now that the migration gives the
  document something concrete to sweep for (`SCHOOL_POPULATION` /
  `active_backend()` usage sites), it would be cheap to add — but it is a
  map-hygiene tranche, not this one.

- **The pre-existing `Owns:` overlap between `docs/map/CON-schools.md`
  and `docs/map/SUB-periphery.md` for `capture/schools.py`.** Both
  documents listed this file before Tranche A. Per `docs/map/SCHEMA.md`,
  an `Owns:` overlap is itself evidence of an undocumented seam. This
  tranche extended `SEAM-schools-x-scheduler.md`'s `Owns:` to
  `scheduler/scheduler.py` and `capture/ladder.py` but deliberately did
  NOT claim `cli/main.py` or `report.py` (they are `DR-SUB-periphery`'s),
  saying so in-line rather than silently. The older overlap is untouched
  and unresolved — outside this tranche's scope and not requested.

- **No structural guard against a future call site bypassing the
  registry.** The three new `SEAM-schools-x-scheduler.md` checks pin the
  per-file migrated counts and assert no bare call survives in the four
  migrated files — so reverting an existing site fails the map gate — but
  a NEW file added later that calls `schools.roster(...)` directly would
  pass every check in the repo. A stronger form (sweeping all of `src/`
  rather than four named files) was considered and not built: it was not
  requested, and the four-file form is what the migration's own claim
  needs. Noted as possible future hardening.

- **The determinism test excludes two named wall-clock fields (`ts` and
  `llm.ms`) rather than comparing raw log bytes.** Raw bytes never match
  between any two runs. Before asserting anything I measured what
  actually differs across the 14 events: those two fields and nothing
  else — every content address, rule, input and output id already
  matched. The exclusion is therefore narrow and named, not a weakening
  to something trivially true, and the companion mutation test proves the
  remaining comparison still fails when behaviour changes. A stricter
  proof (injecting a deterministic clock so raw bytes could be compared)
  was not built; it would test the clock injection as much as the
  migration.
