# Parked — noticed or deferred during this tranche, deliberately not done

- **`INV-frozen-surfaces.md`'s "A `Config` value costs nothing to add and
  is invisible to replay" line overstates the case.** This tranche proved
  it false as a blanket claim: a new `Config` field DOES enter
  `source_config_hash`/`engine_config_json`/the compiled manifest's
  `sha256` unless `_versioned_source_config_data` is explicitly told to
  scrub it, per schema version. The line is true of the manifest's own
  *schema* (no new field, no widened `Literal`), but not of the *replay
  digest* the same section discusses two sentences later. Step 13 added a
  new Traps entry recording the failure mode and its fix, but did not
  edit this older, now-overstated sentence — that edit wasn't in step
  13's stated scope (a Traps *addition*, not a correction to existing
  prose) and touching it would have meant re-deriving/re-verifying a
  claim outside this tranche's own R1-R8. Worth a `docs/ERRATA.md` entry
  (not `ERRATA_EXECUTOR.md` — that ledger is now monitor-only per the
  charter update in commit `87b2828d`) the next time anyone is in this
  document for an unrelated reason.
- **Rung 2's remaining inventory candidates** (Group B bridge settings,
  Group C env-var switches, Group D `STANCE_LIBRARY`) — unchanged from
  the inventory tranche's own PARKED.md; still the operator's call, still
  not this tranche's scope.
- **`docs/map/INV-frozen-surfaces.md`'s new Traps entry only pins**
  `ENGAGED_CRITICISM_AUTHORITY` **appearing in** `run_manifest.py` **(the
  pop-list call site), not the ABSENCE of any future field from the
  echo.** A future tranche that adds a sixth `Config` field and forgets
  to update `_versioned_source_config_data` would not be caught by this
  check — only by the golden tests themselves failing, as happened here.
  No stronger structural guard (e.g. a test that fails on ANY untracked
  new top-level `Config` field) was designed or requested; noted as a
  possible future hardening, not built here.
