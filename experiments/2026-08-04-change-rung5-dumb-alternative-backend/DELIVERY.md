# Delivered: rung 5 — one deliberately dumb alternative, swapped in
Branch: `claude/delivery-rungs-handover-m22sdy` @ `7fdff121` (pushed, tree clean)
8 commits from tranche base `494a8213`.

**Offline work complete. The live A/B is NOT done and is this report's
final ask — see "The stop".**

## What changed

The rung-3 socket is now demonstrably real rather than decorative.
`RoundRobinSchoolPopulationBackend` is registered under the non-default
name `"round-robin"`. It overrides `allocate` alone — handing each problem
to exactly one school by rotation, discarding the fan-out classes, the
ownership-by-provenance lookup and the cross-examination floor the default
encodes — and delegates the other four operations to the same module
functions the default delegates to, so any behavioural difference is
attributable to allocation.

A run selects it through `schools.population_backend(name)`, a scoped
override of `_ACTIVE_BACKEND_ID` that resolves the name before it mutates
anything and restores the previous value on the way out, including when
the run raises. **No `Config` field, and therefore no
`run_manifest.py` scrub line and no frozen-surface touch.** The seam
document had predicted rung 5 would have to pay that cost with operator
approval; it did not, and the prediction is corrected in place rather than
left standing.

Offline, a run configured with the alternative completes and
`verify_root` returns no violations, and the root names its own builder —
rung 4's stamp records `module_id == "round-robin"` where a default run
records `"default"`. Configurability did not have to buy observability;
rung 4 had already paid for it.

The whole change is one file: `src/deepreason/capture/schools.py`, 69
insertions and 1 deletion.

**Proof:** full gate 3338 passed / 0 failed; `docs_verify` 0 failed,
`--audit` 0, `--links` 0, `--coverage` 0; 42-root sweep byte-identical at
`6d6c3366…`; frozen-surface diff EMPTY on all five surfaces plus
`verification/` and `config.py`.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Route: `dr-change-orchestrator` for the module" | done | phase artifacts in order; VALIDATION S1 |
| R2 | "credentials … ask for them; never commit them" | done | no credential file created, read or committed; `git log -p` for the tranche has zero matches |
| R3 | "implement one trivial alternative … (e.g. round-robin school allocation)" | done | VALIDATION S2/S3 |
| R4 | "register it as a non-default entry" | done | `ids() == ("default", "round-robin")` |
| R5 | "offline, a run configured with the alternative completes and its root verifies" | done | VALIDATION S5/S6 |
| R6 | "the default path stays byte-identical" | done-with-assumption **A3** | VALIDATION S7 — the determinism instrument passes UNMODIFIED |
| R7 | "The live A/B … is valuable but OPTIONAL" | not-exercised | superseded in practice by R13's mandatory stop; the two agree |
| R8 | "Accept: full gate" | done | 3338 passed, 0 failed |
| R9 | "sweep byte-identical" | done | `6d6c3366…`, empty diff |
| R10 | "the alternative's offline run root replay-valid" | done-with-assumption **A2** | `verify_root(root)["violations"] == []` |
| R11 | "Proceed to rung 5 via dr-change-orchestrator" | done | this tranche |
| R12 | "Do the offline module work first" | done | offline work complete before the stop |
| R13 | "stop before the live A/B step and ask me for credentials" | **done — this is the ask** | see below |

No requirement is not-done.

## The stop — what I need from you

The offline half of rung 5 is finished and proven. The live A/B (same
question, default vs dumb, compare typed outcomes) needs credentials I do
not have and will not invent: the `env` file holding `OLLAMA_API_KEY` is
gitignored and did not survive the container rollback.

**To run it I need `OLLAMA_API_KEY`.** With it I would, per
`dr-drive-harness` §3: recreate `experiments/<ladder>/env` (never
committed), launch detached with `setsid nohup … & disown`, arm the
snapshot loop and a `progress.jsonl` monitor alerting on failure
signatures, and judge only typed outcomes — run state, stop_reason, the
ladder's audit JSON, `verify_root`, FINDINGS.md.

Two things worth knowing before you decide:
- **Qualification will rerun in full** (~14 min, ~1160 calls) if the home
  or provider profile differs from a cached subject digest. Budget for it.
- **The A/B's value is bounded.** The dumb backend allocates one school
  per problem, so the comparison mostly measures how much less work the
  run does. Offline it showed 20 vs 23 events at 2 cycles and 30 vs 42 at
  6 — a volume difference, not a quality one. A live A/B would say
  whether that volume difference produces a different epistemic outcome,
  which offline evidence genuinely cannot answer.

If you would rather skip it, rung 5's acceptance line is already met —
"full gate; sweep byte-identical; the alternative's offline run root
replay-valid" — and the A/B is marked OPTIONAL in the handover's own
words.

## Assumptions you may override

A1 — the alternative differs in `allocate` only; the other four delegate.
A2 — the offline run root is built in `tmp_path` and NOT committed, so the
sweep census stays at 42 and the baseline does not move. It is re-created
and re-verified on every gate run.
A3 — R6 proven as "a run that does not select the alternative is
unchanged", because rung 4 made the literal reading false for any
non-default backend.
A4 — "completes and verifies" is completion plus empty `verify_root`
violations; epistemic quality is not judged, since "deliberately dumb"
predicts it will be worse.

## Map delta

**changed:** `SEAM-schools-x-scheduler.md` (its "no second backend is
registered" section was this change's own precondition — rewritten; the
single-entry check updated rather than deleted; the identity check widened
to name both backends), `CON-schools.md` (two new rows),
`SEAM-manifest-x-schools.md` (exact import-set pin gains `contextlib`).
**created:** none. **new checks:** 3.

**Corrected in passing:** `SEAM-schools-x-scheduler`'s fingerprint row
said the stamp fires "at construction" while its own check two lines below
asserted it does not — rung 4 updated the check and not the sentence.
`docs_verify` validates checks, not the prose around them.

**left stale:** `CON-schools`, `SEAM-schools-x-scheduler`,
`SEAM-manifest-x-schools`, `SUB-scheduler` — `Verified-at:` not advanced
because this tranche did not re-run their full check sets; nothing they
assert is false.

## Parked (not done, not promised)

P1 the live A/B itself; P2 a map check can pass while its prose is false;
P3 the offline fixture cannot see allocation divergence in provenance,
only in volume; P4 `_ACTIVE_BACKEND_ID` is process-global mutable state,
restored by the scope but not defended against direct assignment; P5 rung
4's parked items remain open; P6 fixture-drift forecasting was the weakest
part of two consecutive specs.
