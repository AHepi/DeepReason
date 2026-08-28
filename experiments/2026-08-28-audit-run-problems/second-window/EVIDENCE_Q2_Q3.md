# Q2 + Q3 evidence ledger

## Q2 — why no judge was ever called

### What the ladder asked for
`run-config.yaml` (technique branch) lines 157-168:

```
JUDGE_SEATS_ENABLED: true
ADJUDICATION_STATUS_AUTHORITY_ENABLED: true
ARGUMENTATIVE_AUTHORITY: observe_only     # deliberate, with a comment
ENGAGED_CRITICISM_AUTHORITY: defended_trial
```

The comment states the tranche's belief: *"Real status-changing authority for
this run comes through the engaged criticism engine below."*

### What the compiled manifest carries
`run/run-manifest.json` on all three surviving manifests:
`criticism_policy: null`. `build_manifest_pt1.py` never constructs one
(grep: no `criticism_policy`, no `CriticismPolicy`).

The absence of the four Config keys from `engine_config_json` is NOT evidence
either way — `run_manifest.py:2378-2400` drops them deliberately so
qualification subject digests do not move (docs/ERRATA.md E44).

### The branch that decides
`src/deepreason/scheduler/scheduler.py:1430-1449`:

```python
criticism_policy = (
    self.run_manifest.criticism_policy
    if self.run_manifest is not None and ... schema_version in {4,5,6}
    else None
)
...
if criticism_policy is not None:
    self._foreign_arg_crit()      # the ONLY caller that passes
    return                        # argumentative_authority=policy.authority (:1650)
eligible = [...]
...
crit_argumentative_batch(harness, batch, self.adapter, config)   # :1488
```

The fallback call at `:1488` passes no `argumentative_authority`, no
`critic_school_id`, no `coverage_observer` → `policy_call=False`
(`rules/crit.py:1673-1678`) → `_resolve_authority` returns `_authority(config)`
(`rules/crit.py:51-63`) → `argumentative_authority_mode` reads
`ARGUMENTATIVE_AUTHORITY` (`authority.py:95`) = **observe_only**.

`observe_only` routes to `_observe_case`; `_TRIAL_MODES` — the only path to
`run_argument_trial_from_case` — is never entered
(`rules/crit.py:1608-1620` single, `:2189-2200` batch).

`ENGAGED_CRITICISM_AUTHORITY` is consumed at exactly one site,
`preparation.py:499-511`, which builds `criticism_policy` on the MANAGED
path. A hand-built manifest bypasses it, so the knob was inert.

### Record confirmation
Only occurrence of "judge" in epoch 6's `log.jsonl` is a seat-steerability
list naming `judge#0`, `judge#1` as steerable. Zero trial events; all 11
warrants are `type: demonstrative` (mechanical), none argumentative.

**Verdict: unreachable by construction, two independent sufficient reasons.**

---

## Q3 — why on-subject survivors collapsed

### The wander cap IS present and DID engage
`Config.SEED_PROBLEM_BUDGET_FLOOR = 0.5` (`config.py:295`, default, not
overridden by the ladder). `wander.py` present on the technique branch.

Recorded readings (`allocation.seed-lineage-share.v1` / `…wander-throttled.v1`):

| root | share readings | throttle events | last share/floor |
|---|---|---|---|
| epoch 0 | 3 | 0 | 0.500000 / 0.500000 |
| epoch 1 | 12 | 5 | 0.454545 / 0.500000 |
| epoch 5 | 3 | 0 | 0.500000 / 0.500000 |
| epoch 6 | **4** | 1 | 0.333333 / 0.500000 |

Epoch 6, seq 648-649: share 0.3333 below floor 0.5000 → throttled.

### Off-subject descends ENTIRELY from spawned problems
Accepted CONJECTURES (import-role excluded, per the CLAUDE.md invariant),
addressed by problem lineage, read through `Harness(read_only=True).state`:

| epoch | SEED lineage | `conn:` lineage | total | tranche's reported "on-subject" |
|---|---|---|---|---|
| 0 | **2** | 12 | 14 | 2 of 14 ✓ |
| 1 | **2** | 6 | 8 | 2 of 8 ✓ |
| 6 | **3** | 10 | 13 | 3 of 13 ✓ |

Exact match. "Off-subject" is precisely "descends from a `conn:` problem";
not one off-subject survivor descends from the seed question. This confirms
PARKED P9's correction ("the scheduler COMMISSIONS") at artifact level.

### The real cause of epoch 6's collapse — a budget-denial SPIN
Per-cycle attribution of epoch 6's 24 registered cycles, from the `cycle`
heartbeat Measures and the `llm` fields between them:

| cycle | heartbeat label | llm calls | tokens |
|---|---|---|---|
| 0 | `question-9e8800977c3e…` (seed) | 26 | 259,995 |
| 1 | `disc:question-9e8800977c3e…` | 0 | 0 |
| 2 | `conn:0a89b2b812ae` | 40 | 272,699 |
| 3 | `question-9e8800977c3e…` (seed) | 19 | 239,788 |
| 4 | `simulation-request:sha256:295ce6b0…` | 0 | 0 |
| **5–23** | `simulation-result:sha256:b5a7f812…` (the SAME crashed package, 19×) | **0** | **0** |

Every one of cycles 5–23 has the identical five-event shape (e.g. seq 835-842):

```
Measure  ["cycle","5","simulation-result:sha256:b5a7f812…"]
Control  [<work sha>, "conjecture:911d52d009af…"]
Control  [<work sha>, "budget-denied:token-budget"]
Measure  ["dropped-call","token budget denied transactional work <work sha>"]
Measure  ["allocation.seat-truncation.v1", …] ×4
```

Census: epoch 6 carries **19 `dropped-call` events and 40
`budget-denied:token-budget` occurrences**; epoch 0 carries 2 budget-denied
and 0 dropped-call.

Only 4 of 24 cycles reached `_select_problem` — which is exactly why the
wander cap logged 4 readings against a docstring promising one "every cycle"
(`scheduler.py:1229`). The capability paths emit their own heartbeat and
return before selection (`scheduler.py:1802`, `:1950`, `:2030`; the
simulation branch returns at `:2052-2053` before `_select_problem` at `:2055`
and `_disclose_wander` at `:2061`).

**Epoch 6 did 4 working cycles, not 24.** It exhausted its token budget in
cycles 0–3, then spun 19 no-op cycles on one dead simulation package until
the CYCLE budget ended it as `budget_exhausted` — reported as
"24 of 24 cycles".
