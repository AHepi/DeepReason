# Results — live full-judge seat/configuration census

## Current exact result

```text
ORDERED_JUDGE_PAIR_PREFIX EXPECTED=324 TERMINAL=9 POSSIBLE=8 IMPOSSIBLE=1 PROVIDER_INDETERMINATE=0 INTERRUPTED=0 PENDING=315 DUPLICATE=0 PEAK_IN_FLIGHT<=3
```

This is a stopped, resumable prefix over the 18-model authenticated catalog.
It is not an exhaustive result for the seat-only projection or the superseding
full configuration cross.

`POSSIBLE=8` means the shipped v6 defended-trial path reached the critic,
defender, judge 0, and judge 1 and produced a typed trial outcome.
`IMPOSSIBLE=1` means the frozen configuration received a deterministic shipped
configuration refusal. `INTERRUPTED=0` counts case-level terminal receipts:
unfinished work remains pending rather than being relabelled as an outcome.

## Frozen identity

| Item | Exact value |
|---|---|
| Catalog models | 18 |
| Catalog model-list digest | `77a5a11f946b21e82488ddc66473f1bfa50c6bd6c394fd420ad1baacc81754b4` |
| Seat-domain file digest | `1be915b5cccb5164b17691cb6602fa630d26603064d0096f4b3600fd2975442d` |
| Full-cross file digest | `148793d2bd570869a5e2be7b1d1a3845c1fb69095ac987e4396f3c99b9d9322e` |
| Prefix | All 324 ordered judge pairs; critic and defender fixed to the first catalog model |
| Fixed critic and defender | `deepseek-v4-flash:0731` |
| Live settings | standard profile, JSON object through JSON text, explicit `low`, split off, 8,192 output tokens, 131,072 context tokens |
| Live source | Smoke at `d3cbed718d946c0b2cdb2ebef96856673d8127f9`; clean prefix segment at `dfe5bebd2dd987e82e050888a9d7c8400819a583` |

## Terminal configuration rows

Judge 0 is `deepseek-v4-flash:0731` in every row below. Critic and defender are
the same fixed anchor named above. These are reachability/configuration
findings, not model rankings or claims about truth.

| Judge 1 | Terminal status | Typed outcome or boundary | Full required dispatch |
|---|---|---|---|
| `deepseek-v4-flash:0731` | trial outcome | `defence-sustained` | yes |
| `deepseek-v4-pro:0813` | configuration refused | `SECOND_JUDGE_FAMILY_REQUIRED` | no |
| `gemma4:31b` | trial outcome | `ensemble-split` | yes |
| `glm-5.1` | trial outcome | `defence-sustained` | yes |
| `glm-5.2` | trial outcome | `ensemble-split` | yes |
| `glm-5.3` | trial outcome | `defence-sustained` | yes |
| `glm-5.3-flash` | trial outcome | `referential-integrity` | yes |
| `gpt-oss:120b` | trial outcome | `defence-sustained` | yes |
| `gpt-oss:20b` | trial outcome | `defence-sustained` | yes |

The single refusal occurred at shipped trial preflight after critic
compatibility dispatch. Its exact boundary was `/roles/judge`: the rubric trial
required two frozen judge seats from distinct route families. No provider
timeout, malformed response, model silence, or unexpected driver error was
observed among the nine counted rows.

## Resume and integrity state

The next frozen row is ordinal 9,
`sha256:8aa2e4b74b70124d7511bea92162ceb0edfeddca14d64934522d64a9b7653ae2`,
with judge 0 `deepseek-v4-flash:0731` and judge 1 `kimi-k2.6`. Kimi K3 remains
the sole typed catalog exclusion; Kimi K2.6 is in scope.

Two retained attempt roots (`attempt-0001` and `attempt-0003`) are closed with
interruption markers so resume rotates to a fresh immutable root. During the
first prefix launch, an external monitor misread a PID from a nested namespace
and an interruption marker was written while `attempt-0002` was still active.
That worker was stopped; all seven of its terminal files remain byte-preserved,
but the whole attempt is marked `quarantined` and excluded from every count and
resume decision. A regression test now enforces that exclusion. The clean
replacement segment produced eight terminal receipts.

## Larger-domain status

| Domain | Expected | Terminal | Pending | Claim |
|---|---:|---:|---:|---|
| Ordered-judge-pair prefix | 324 | 9 | 315 | stopped resumable prefix |
| Seat-only projection | 1,994,544 | 9 | 1,994,535 | incomplete projection |
| Superseding per-seat full cross | 71,141,539,390,075,109,376 | 0 | 71,141,539,390,075,109,376 | immutable membership registry; not begun |

Arbitrary future models, role counts, strings, numbers, and provider fields
remain open dimensions. No percentage or completed projection is renamed as
universal exhaustiveness.

## Safety and verification

The prefix used one coordinator with three worker threads and the shared hard
bound `PEAK_IN_FLIGHT<=3`. No high, max, xhigh, omitted/default, observe-only,
or Kimi-K3 road was dispatched. The credential was held only in process memory.
An exact-byte scan of tracked files and the ignored runtime root found zero
credential-bearing files. All 39 campaign regression tests pass, the frozen
surface gate is clear, and the cumulative code/test change is 3,745 of the
5,000-line ceiling.
