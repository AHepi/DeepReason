# Fix: a run that measures on the hashing scale records WHY, including when nothing asked for the neural one

Guarantee restored: every run's log answers "why is this run's geometry
hashing?" with one of exactly three typed records — the neural stamp, the
`embedder-fallback` naming a backend that could not be built, or a new
`embedder-unconfigured` naming a compiled configuration that named no embedder
model at all — so no run's measurement scale can change without the record
saying so.

## Why this shape and not the two more obvious ones

Two roads were examined against the record and rejected before this one, both
recorded here so a reviewer does not re-derive them.

**Not a compile notice.** The compiler's own disclosure channel,
`ENGINE_CONFIG_FIELD_NOT_CARRIED`, looks like the natural home — the drop
happens at compile time and `preparation.py:505-508` names the seven host-owned
values as the stated exception to it. It is the wrong channel twice over.
First, `run_manifest.py:1200-1203` says of the notice's `value` field:
"a disclosure is also the road back: `config_from_run_manifest` restores it."
A carriage notice carrying the dropped model would RE-ARM the neural embedder on
the managed path, which is a change to which embedder a configuration selects —
explicitly out of scope in GOAL.md, and a decision that belongs to the operator,
not to a defect tranche. Second, a notice under any OTHER code is kept by
`qualification.py:269` when it builds the qualification subject payload, so it
would move every subject digest and cost every home a ~14-minute battery —
frozen surface 5, a hard stop.

**Not a reused `embedder-fallback`.** Firing the existing signal whenever
`EMBEDDER_MODEL` is falsy is a four-line change and contradicts a committed
requirement: `tests/test_embedder.py::test_hashing_escape_survives_the_armed_neural_default`
implements R3/R15 of tranche 2026-08-16-change-embedder-auto-install, which
states that taking the deliberate `EMBEDDER_MODEL=None` escape "is NOT a
degradation — no `embedder-fallback` measure is recorded, because nothing
failed." A run-time builder cannot tell an operator who chose hashing from a
host that forced it; both arrive as `EMBEDDER_MODEL is None`. A separately named
signal keeps R3/R15 true to the letter (no `embedder-fallback` for the escape)
while still writing down the cause, which is what the tranche brief requires
even when the fallback is legitimate.

## Change sites (exhaustive)

- `src/deepreason/signals.py:~447-710` (the `_DECLARED` tuple) — one new
  `SignalDeclaration`: name `embedder-unconfigured`, unit `event`, staleness
  `run`, producer-agnostic semantics naming what one occurrence means and what
  it is NOT evidence of. Follows `docs/map/REC-add-signal.md` step 2; carries a
  real unit and staleness, so `tests/test_signal_contract.py`'s migration-debt
  census cannot rise.
- `src/deepreason/ops.py:152-176` (`make_embedder`) — the first branch stops
  returning silently. When the compiled configuration names no embedder model it
  records `["embedder-unconfigured", <the model the shipped default names, or
  "-">, <where the value was lost>]` and then returns `None` as before. The
  return value, and therefore every caller's behaviour, is unchanged: this adds
  a record, never a decision.
- `src/deepreason/views/narrate.py:76-84` — one narration entry for the new
  signal, category `progress` (a fact about the run's instrument, not a
  setback), so the narrate view does not meet an undocumented tag.
- `src/deepreason/application/results.py:368-414` (`embedder_summary`) — read
  the new signal into two new keys, `unconfigured` and, reusing the existing
  pair, `configured_model` / `fallback_reason`. `fallback` stays `False`: the
  run did not fall back, nothing was asked for.
- `src/deepreason/application/results.py:736-756` (`embedder_line`) — the
  no-fallback branch appends the recorded reason when one is present, so
  `deepreason results` prints why rather than only what. The existing fallback
  branch is left alone except to append its own recorded reason, which it
  already receives and discards.

## Regression artifact

Must invert: `python -u experiments/2026-09-09-neural-embedder-fallback/repro_embedder_drop.py`
— exit 1, with section 2 printing a Measure record and section 1 unchanged (the
compiled manifest still carries `embedder_model: null` and no compile notice,
because this fix does not touch the compile stage). REPRO.md's post-fix
expectation is amended accordingly: the compile-notice half of it was written
before the carriage-restores-the-value finding above ruled that road out, and
the honest post-fix output has the notice on the LOG, not on the manifest.

New conditions this fix must be tested against, mutation-proven (each fails when
the fix line is reverted):

1. A run whose compiled configuration names no embedder model records exactly
   one `embedder-unconfigured` naming the shipped default's model, and
   `embedder_summary_for_root` surfaces its reason.
2. The deliberate escape still records no `embedder-fallback` — R3/R15 stays
   true.
3. A configured-but-unbuildable backend still records exactly one
   `embedder-fallback` and no `embedder-unconfigured` — the two causes never
   both fire.
4. The MANAGED path specifically: a manifest built by
   `preparation.build_preparation_manifest` from an operator `Config` that
   explicitly names the neural model produces a runtime configuration whose
   `make_embedder` records the new signal. This is the arm roots' exact
   condition, and it is the test the five arms would have failed.
5. A run that DOES build the neural backend records neither signal.

## Existing tests at risk (from grep over `embedder-fallback`, `make_embedder`)

- `tests/test_embedder.py::test_make_embedder_fallback_lands_on_the_log` — its
  third case asserts no `embedder-fallback` for `Config(EMBEDDER_MODEL=None)`.
  KEEPS PASSING unchanged; extended with condition 2 above so the escape's
  silence is pinned on the right signal.
- `tests/test_embedder.py::test_hashing_escape_survives_the_armed_neural_default`
  — R3/R15. Keeps passing; exercises `build_embedder` only.
- `tests/test_manifest_integration.py:111-116` — asserts exactly one
  `embedder-fallback` under the fallback policy. Keeps passing.
- `tests/test_scratch_similarity.py:190-200` — asserts an `embedder-fallback`
  reaches the log through the repository seam. Keeps passing.
- `tests/test_signals.py` — its AST scan fails on an emitted tag that is not
  declared, which is why the declaration lands in the same commit.
- `tests/test_signal_contract.py` — pins `MIGRATION_DEBT`. The new signal
  declares a real unit and staleness, so the census does not rise.
- `tests/test_results_command.py::test_absent_facts_are_typed_absences_not_omitted_keys`
  and `::test_results_surfaces_the_embedder_and_names_a_fallback_loudly` —
  read the embedder summary's shape. Verified against the ring before the
  boundary gate; updated only if a fixture pinned the silence.
- UNKNOWN until measured: any test asserting an exact event count or sequence
  number for a run whose `EMBEDDER_MODEL` is unset now sees one more event. The
  ring (`tests/test_embedder.py tests/test_results_command.py
  tests/test_signals.py tests/test_signal_contract.py
  tests/test_manifest_integration.py tests/test_scratch_similarity.py
  tests/test_managed_path_config_read.py`) is run first for exactly this, and
  the full gate at the boundary decides it.

## Map, in the same commit

- `docs/map/SUB-llm.md` — a new `Traps` entry beside the 2026-08-16 embedder
  trap, naming the five arm roots
  (`experiments/2026-09-04-experiment-brief-variation-step1/roots/{A0,A1,A1P,A2,A3}-run-fe00609058e10605590206d51ab2b7a0`)
  and stating the recurrence: the 2026-08-16 fix armed the default by install
  and surfaced the fallback in `results`, and the managed path throws the armed
  default away one stage earlier than the fallback machinery watches. The
  existing entry is not deleted or reworded. The new entry carries a `check:`
  that fails if the emission is removed.

## Explicitly not changed

- `preparation._config_for_profile`'s `owned` dictionary. The host override
  stands. Making the managed path honour a configured embedder is a change to
  which embedder a configuration selects — GOAL.md's NOT-in-scope line, the
  operator's decision under the modularity and all-configurations laws, and a
  question this tranche can only make VISIBLE. It is parked with a
  ready-to-send prompt, because the operator's own instruction to run
  `deepreason embedder-warmup` "in the setup phase of any session that will run
  the harness" cannot be satisfied on the managed path as it stands, and they
  should be the one to decide that.
- The five sealed arm roots. A committed root's contents are never edited;
  their readings stay on the hashing scale and PARKED.md P2 says so.
- The `pyproject.toml` declaration gap (parked 2026-08-30 S5) and the other six
  host-owned values (PARKED.md P1).

## Frozen surfaces

NONE. `INV-frozen-surfaces.md` names five surfaces across seven paths —
`capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`,
`run_manifest.py`, `qualification.py` — plus the frozen-adjacent
`route_fingerprint` in `llm/firewall.py`. This fix touches `signals.py`,
`ops.py`, `views/narrate.py` and `application/results.py`, none of which is on
that list, and it adds a Measure record without altering `harness.py`'s event
application or any replay-validation record format. The two roads that WOULD
have contacted a frozen surface (the compile notice, in both its restoring and
its non-restoring form) are the reason this fix is shaped as it is; see above.

Estimated diff: ~55 lines of production code across 4 files, plus tests and one
map entry. Under the 150-line budget.

## Approval gate

Class `defect` per GOAL.md, diff estimate <=150 lines, no frozen surface.
Proceeds to `dr-implement-fix`.
