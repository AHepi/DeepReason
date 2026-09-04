# Parked — noticed by this tranche, deliberately not fixed here

One tranche, one goal. Everything below was found while measuring
critics and is left exactly where it was found, with a prompt its future
runner can paste.

---

## P1 — two committed soak cases cannot compile a manifest at all

**What.** `python -u scripts/cycle_soak.py --case pc1` and `--case pc2`
both die before driving anything, on
`V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen
toolchain`. `epoch3` and `reach-rich` are green on the same container,
so this is not an environment-wide break. The soak is the gate that
CLAUDE.md and `dr-drive-harness` both put in front of every live launch,
and two of its eight cases currently cannot be used as that gate.

**Ready to send:**

```
Route: deepreason-orchestrator (defect).
Goal: `scripts/cycle_soak.py --case pc1` and `--case pc2` fail to compile a
RunManifest, raising `V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one
frozen toolchain`, before driving a single cycle. `--case epoch3` and
`--case reach-rich` are green on the same container and the same install, so
this is specific to those two case definitions rather than to the environment.
Evidence: experiments/2026-09-04-experiment-blind-critic/SOAK.txt records all
four outcomes; PARKED.md P1 is this entry.
End state: both cases either drive to cycle 8 and exit 0, or the case
definitions are corrected/retired with the reason recorded — the soak is the
documented precondition for every live launch, so a case that cannot run is a
gate with a hole in it.
```

---

## P2 — the provider now rejects the reasoning value the last committed launch config sends

**What.** `"reasoning": "none"` as a bare string is refused by Ollama
Cloud today: `json: cannot unmarshal string into Go struct field
ChatCompletionRequest.reasoning of type openai.Reasoning`. The newest
committed launch config
(`experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/.../run-manifest.json`)
binds exactly that value on its critic seat, and
`llm/endpoints.py::OpenAICompatEndpoint` carries a `reasoning` knob that
realises it per provider. Measured here as a four-model probe, recorded
in SPEC M5. This tranche did not hit it because it set no reasoning
value at all.

**Ready to send:**

```
Route: deepreason-orchestrator (defect).
Goal: decide whether `reasoning: "none"` is still a value the ollama provider
accepts, and make the endpoint send whatever the provider now expects. Today a
bare string is refused with `json: cannot unmarshal string into Go struct field
ChatCompletionRequest.reasoning of type openai.Reasoning`, so any run relaunched
from the newest committed launch config would fail typed at the first seat call.
Evidence: experiments/2026-09-04-experiment-blind-critic/SPEC.md measurement M5
(a four-model probe, pasted verbatim); the config that sends it is the critic
seat of run-5565bd1ef7011e3d25fef3197bdf1cdb's manifest.
Note the shape of the answer matters: the provider wants an object, not a
string, and `think: false` does NOT suppress reasoning either — both were probed.
End state: a live seat call on the committed launch config succeeds, with the
provider's current contract recorded in docs/OLLAMA_CLOUD_OPERATIONS.md.
```

---

## P3 — the sharpness rubric cannot fail, and no gate would have caught that

**What.** `docs_verify --audit` refuses map checks that cannot fail.
Nothing applies that standard to an experiment's own measures. This
tranche wrote five sharpness criteria in advance, ran 1,436 blind
judgements, and found that two criteria scored 3/3 on every single one
and two more on all but a handful. The rubric was reporting its own
definition back — the same failure the previous tranche recorded as its
standing lesson, in a new place.

**Ready to send:**

```
Route: dr-change-orchestrator (a change: an instrument, not a defect).
Goal: give experiment measures the same standard docs_verify --audit already
gives map checks — a measure that cannot fail is refused before it is used.
Concretely: a pre-registration check that, given a registered measure and a
handful of committed examples, reports whether the measure takes more than one
value; run at PREREG time, not at results time.
Evidence: experiments/2026-09-04-experiment-blind-critic/RESULTS.md, "The
sharpness rubric cannot fail" (4 of 5 criteria at ceiling over 1436
judgements); experiments/2026-09-03-change-provenance-history-channel/PARKED.md
"P7 CORRECTED", whose closing lesson is the same one, found the same way, one
tranche earlier.
End state: a measure whose value is constant across a committed sample is a
typed refusal at pre-registration, and this tranche's M5 is the regression
fixture that proves it fires.
```

---

## P4 — a critic that never looks at two of the four fields it is shown

**What.** On the blind panel, two planted defect classes were named
almost never, in every cell: `scope-contradiction` at 0.0-0.2 and
`vacuous-forbidden-case` at 0.00 in all four cells. Both are planted in
structured fields (`scope.excludes`, `counterconditions[0].case`) that
the brief renders in full. The other four classes, all planted in
`mechanism`, run 0.4-1.0. This is not about either factor under test; it
is about where the critic looks.

**Ready to send:**

```
Route: dr-change-orchestrator (a change).
Goal: establish whether the argumentative critic reads the structured fields of
a target at all, or only its prose. Measured incidentally here: a defect planted
in `counterconditions[0].case` was named in 0 of 240 blind-panel judgements
across all four briefs, and one planted in `scope.excludes` in at most 2 of 60
per cell, while defects planted in `mechanism` were named 40-100% of the time.
If confirmed, the fix is a brief that renders the target's commitments and
counterconditions as things to attack rather than as context — which is a
seat-section layout change, i.e. configuration, not a code edit.
Evidence: experiments/2026-09-04-experiment-blind-critic/M1_PRIMARY.json,
per_cell.per_class; DEFECT_KEY.json for what was planted where.
End state: a measurement that separates "the critic looked and disagreed" from
"the critic never read the field", and a recorded decision either way.
```

---

## P5 — no run in this tree has ever discharged a criticism

**What.** Looking for rebuttal history to show the critic, this tranche
censused every source root and found zero `revised`, zero `rebutted` and
zero `departure_declared` events — only `discharge-undischarged` (140
and 244 on two roots) and `discharge-reask`. The discharge channel is
built, wired and read; nothing has ever come back through it. That is
why factor F2 could only test prior-objection exposure.

**Ready to send:**

```
Route: deepreason-orchestrator (suspicious, not yet a defect).
Goal: find out why no conjecturer in any committed root has ever discharged an
open criticism. Census: across the five history-experiment roots, zero events of
kind revised / rebutted / departure_declared; hundreds of
`discharge-undischarged` and a handful of `discharge-reask`. The channel's own
design says an undischarged submission is returned ONCE with the open list and
then accepted with a typed disclosure — so the re-ask happens and the discharge
never does. Diagnosis comes from the record before any code reading: read what
the conjecturer was actually shown in the binding block on a re-ask, and what it
sent back.
Evidence: experiments/2026-09-04-experiment-blind-critic/PARKED.md P5 and its
SPEC Amendment A10; docs/map/CON-discharge-channel.md for what should happen.
End state: either a defect with a fix, or a recorded finding that the behaviour
is correct and the channel's value is disclosure rather than discharge.
```

---

## P6 — a committed test picks a run root by SIZE and assumes a property of it

**What.** `tests/test_provider_transport_faults.py::_a_root_without_provider_attempts`
takes every committed root under `experiments/`, sorts them by
`log.jsonl` size, and returns the SMALLEST — then two tests assert that
root recorded no provider attempts. Nothing makes the smallest committed
root a root without provider calls. This tranche committed 480 four-event
bench roots, each of which recorded exactly one provider call, and the
fixture immediately selected one: two map checks
(`SUB-application.md:300` and `SUB-llm.md:336`, which both run that test
file) went red on a branch that changed zero bytes under `src/`.

Measured: base `0f6bf2c854` = 6 failed; this branch with the roots
committed = 8 failed; the delta is exactly those two, and both recover
when the roots are not listed by `git ls-files experiments`.

The claim the tests guard — that `results_summary` carries
`provider_health` and TYPES its absence rather than omitting it — is
true and was never falsified. What failed is the fixture's assumption
about which root it would get. That is precisely the failure mode
`dr-execute-step`'s "durable tests" rule names: anchor to meaning, not
to a selector that any later tranche can move.

**Disposition here:** this tranche did not touch the test. It preserved
its 480 roots as `raw/roots.tar.gz` instead of 480 loose directories,
which is a change to how this tranche stores its OWN evidence and is
inside its own declared area. The fragility is untouched and is parked.

**Ready to send:**

```
Route: deepreason-orchestrator (defect).
Goal: `tests/test_provider_transport_faults.py::_a_root_without_provider_attempts`
selects the smallest committed root under experiments/ by log.jsonl size and two
tests then assert that root recorded no provider attempts. Nothing guarantees
that property of the smallest root, so any tranche that commits small roots
carrying a provider call turns two map checks red without touching src/ at all.
Reproduce: commit any run root with one Crit event and an llm block, then run
`python -m pytest tests/test_provider_transport_faults.py -q -k "progress or results"`.
Evidence: experiments/2026-09-04-experiment-blind-critic/PARKED.md P6 records the
measured delta (base 0f6bf2c854 = 6 docs_verify failures, the same tree plus 480
small roots = 8, the delta being SUB-application.md:300 and SUB-llm.md:336).
End state: the fixture SELECTS FOR the property it needs -- a root whose log
carries no llm block -- and skips typed if none exists, rather than sorting by
size and hoping. The claim under test (results_summary types provider-health
absence) is correct and must not be weakened to get there.
```
