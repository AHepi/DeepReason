# Aggregate form census

Machine-readable source: `CENSUS_AGGREGATE.json`. 54 roots, 3155 provider attempts.

## Arrival validity by form (contract)

| contract | attempts | valid on arrival | rate | repair-scoped | truncated |
|---|---|---|---|---|---|
| `batch-critic.v2` | 1384 | 1282 | 0.9263 | 39 | 0 |
| `conjecturer.turn.v6` | 816 | 541 | 0.663 | 82 | 0 |
| `conjecturer.atomic-candidate.v1` | 373 | 354 | 0.9491 | 0 | 0 |
| `judgeruling.direct.v1` | 342 | 342 | 1.0 | 0 | 0 |
| `defender.direct.v1` | 122 | 122 | 1.0 | 0 | 0 |
| `critic.atomic-target.v1` | 34 | 34 | 1.0 | 0 | 0 |
| `variator.direct.v1` | 30 | 30 | 1.0 | 0 | 0 |
| `bridge.ledger.v3` | 18 | 10 | 0.5556 | 2 | 0 |
| `bridge.ledger-batch.v1` | 13 | 10 | 0.7692 | 1 | 0 |
| `bridge.composition.v2` | 12 | 9 | 0.75 | 2 | 0 |
| `config-referee.v1` | 6 | 5 | 0.8333 | 1 | 0 |
| `bridge.composition-batch.v1` | 5 | 4 | 0.8 | 1 | 0 |

## Arrival validity by model

| model | attempts | valid | rate | truncated | unnatural stop |
|---|---|---|---|---|---|
| `glm-5.2` | 2378 | 2022 | 0.8503 | 0 | 11 |
| `mistral-large-3:675b` | 200 | 195 | 0.975 | 0 | 0 |
| `qwen3.5:397b` | 171 | 171 | 1.0 | 0 | 0 |
| `kimi-k3` | 126 | 110 | 0.873 | 0 | 0 |
| `deepseek-v4-flash:0731` | 104 | 88 | 0.8462 | 0 | 0 |
| `deepseek-v4-pro` | 57 | 52 | 0.9123 | 0 | 0 |
| `kimi-k2.6` | 48 | 39 | 0.8125 | 0 | 0 |
| `deepseek-v4-pro:0813` | 37 | 36 | 0.973 | 0 | 0 |
| `gemma4:31b` | 34 | 30 | 0.8824 | 0 | 0 |

## Model × contract — the only admissible model comparison

`by_model` alone is confounded: models did not run the same forms.
Compare models only within a row of the same contract.

| model | contract | attempts | valid | rate |
|---|---|---|---|---|
| `glm-5.2` | `batch-critic.v2` | 1196 | 1113 | 0.9306 |
| `glm-5.2` | `conjecturer.turn.v6` | 659 | 408 | 0.6191 |
| `glm-5.2` | `conjecturer.atomic-candidate.v1` | 339 | 328 | 0.9676 |
| `qwen3.5:397b` | `judgeruling.direct.v1` | 171 | 171 | 1.0 |
| `mistral-large-3:675b` | `judgeruling.direct.v1` | 171 | 171 | 1.0 |
| `kimi-k3` | `batch-critic.v2` | 123 | 107 | 0.8699 |
| `glm-5.2` | `defender.direct.v1` | 122 | 122 | 1.0 |
| `deepseek-v4-flash:0731` | `conjecturer.turn.v6` | 52 | 44 | 0.8462 |
| `gemma4:31b` | `conjecturer.turn.v6` | 34 | 30 | 0.8824 |
| `glm-5.2` | `critic.atomic-target.v1` | 31 | 31 | 1.0 |
| `deepseek-v4-pro:0813` | `conjecturer.turn.v6` | 31 | 30 | 0.9677 |
| `deepseek-v4-flash:0731` | `variator.direct.v1` | 30 | 30 | 1.0 |
| `deepseek-v4-pro` | `batch-critic.v2` | 28 | 28 | 1.0 |
| `kimi-k2.6` | `batch-critic.v2` | 23 | 20 | 0.8696 |
| `deepseek-v4-flash:0731` | `conjecturer.atomic-candidate.v1` | 22 | 14 | 0.6364 |
| `deepseek-v4-pro` | `conjecturer.turn.v6` | 19 | 14 | 0.7368 |
| `mistral-large-3:675b` | `batch-critic.v2` | 14 | 14 | 1.0 |
| `kimi-k2.6` | `conjecturer.turn.v6` | 11 | 8 | 0.7273 |
| `mistral-large-3:675b` | `conjecturer.turn.v6` | 10 | 7 | 0.7 |
| `glm-5.2` | `bridge.ledger.v3` | 10 | 5 | 0.5 |
| `kimi-k2.6` | `bridge.ledger-batch.v1` | 7 | 7 | 1.0 |
| `deepseek-v4-pro:0813` | `conjecturer.atomic-candidate.v1` | 6 | 6 | 1.0 |
| `glm-5.2` | `bridge.composition.v2` | 6 | 4 | 0.6667 |
| `glm-5.2` | `config-referee.v1` | 6 | 5 | 0.8333 |

## Arrival validity by role and seat instance

| role#seat | attempts | valid | rate |
|---|---|---|---|
| `argumentative_critic#seat0` | 1424 | 1321 | 0.9277 |
| `conjecturer#seat0` | 1189 | 895 | 0.7527 |
| `judge#seat0` | 171 | 171 | 1.0 |
| `judge#seat1` | 171 | 171 | 1.0 |
| `defender#seat0` | 122 | 122 | 1.0 |
| `summarizer#seat0` | 31 | 20 | 0.6452 |
| `variator#seat0` | 30 | 30 | 1.0 |
| `thesis#seat0` | 17 | 13 | 0.7647 |

## What the seat spent its calls on

| workflow attempt index | attempts | valid | rate |
|---|---|---|---|
| 0 | 2699 | 2475 | 0.917 |
| 1 | 219 | 128 | 0.5845 |
| 2 | 115 | 70 | 0.6087 |
| 3 | 68 | 40 | 0.5882 |
| 4 | 54 | 30 | 0.5556 |

## How invalid arrivals failed

Class names are the record's own diagnostic `code` wherever one exists.

| failure class | count |
|---|---|
| `string_pattern_mismatch` | 457 |
| `value_error` | 336 |
| `extra_forbidden` | 206 |
| `V6_WIRE_REFERENCE_INVALID` | 115 |
| `WIRE_TRAILING_CONTENT` | 78 |
| `missing` | 56 |
| `TRUNCATED_MID_JSON` | 52 |
| `WIRE_NO_COMPLETE_JSON` | 34 |
| `SCRATCH_ALIAS_UNKNOWN` | 31 |
| `UNCODED_OTHER` | 24 |
| `list_type` | 13 |
| `repair.unrepairable.v1` | 11 |
| `BRIDGE_COMPOSITION_INVALID` | 8 |
| `too_short` | 7 |
| `string_too_short` | 3 |
| `too_long` | 2 |
| `BRIDGE_WIRE_REFERENCE_INVALID` | 1 |

## Which field failed, and how (top 40)

| contract | field | class | count |
|---|---|---|---|
| `conjecturer.turn.v6` | `/candidates/*/evidence_refs/*/block` | `string_pattern_mismatch` | 244 |
| `conjecturer.turn.v6` | `/scratch_proposal/unresolved_questions/*/related_refs` | `value_error` | 230 |
| `batch-critic.v2` | `/cases/*/premise_evidence/*/block` | `string_pattern_mismatch` | 129 |
| `conjecturer.turn.v6` | `/scratch_proposal/links/*/to_ref` | `string_pattern_mismatch` | 70 |
| `conjecturer.turn.v6` | `/candidates/*/optional_refs/*` | `V6_WIRE_REFERENCE_INVALID` | 64 |
| `conjecturer.turn.v6` | `/values` | `value_error` | 54 |
| `conjecturer.turn.v6` | `/scratch_proposal/cluster_suggestions/*/member_refs` | `value_error` | 25 |
| `conjecturer.turn.v6` | `/patch` | `extra_forbidden` | 23 |
| `conjecturer.turn.v6` | `/pointer` | `extra_forbidden` | 22 |
| `conjecturer.turn.v6` | `/repair` | `extra_forbidden` | 19 |
| `conjecturer.turn.v6` | `/candidates/*/analogy/transfer_claims` | `missing` | 16 |
| `conjecturer.turn.v6` | `/candidates/*/mechanism` | `missing` | 15 |
| `batch-critic.v2` | `/cases/*/preise` | `extra_forbidden` | 14 |
| `batch-critic.v2` | `/cases/*/counterexample` | `list_type` | 13 |
| `conjecturer.turn.v6` | `/requested_observables` | `value_error` | 12 |
| `conjecturer.turn.v6` | `/scratch_proposal/links/*/from_ref` | `string_pattern_mismatch` | 11 |
| `conjecturer.turn.v6` | `/baseline_sha256` | `extra_forbidden` | 11 |
| `bridge.ledger.v3` | `/entries/*` | `value_error` | 10 |
| `conjecturer.turn.v6` | `/candidates/*/neighbours/*` | `V6_WIRE_REFERENCE_INVALID` | 9 |
| `conjecturer.turn.v6` | `/candidates/*/analogy/overturn_conditions` | `missing` | 8 |
| `conjecturer.turn.v6` | `/scratch_proposal/new_blocks/*/body/local_key` | `extra_forbidden` | 7 |
| `conjecturer.turn.v6` | `/scratch_proposal/new_blocks/*` | `V6_WIRE_REFERENCE_INVALID` | 7 |
| `conjecturer.turn.v6` | `/repair_patch` | `extra_forbidden` | 7 |
| `batch-critic.v2` | `/patch` | `extra_forbidden` | 7 |
| `batch-critic.v2` | `/cases/*` | `V6_WIRE_REFERENCE_INVALID` | 5 |
| `batch-critic.v2` | `/contract` | `extra_forbidden` | 5 |
| `conjecturer.turn.v6` | `/values` | `extra_forbidden` | 5 |
| `conjecturer.turn.v6` | `/scratch_proposal/new_blocks/*/local_key` | `missing` | 4 |
| `batch-critic.v2` | `/$defs` | `extra_forbidden` | 4 |
| `conjecturer.turn.v6` | `/operations` | `extra_forbidden` | 4 |
| `batch-critic.v2` | `/cases/*/target_alias` | `missing` | 4 |
| `conjecturer.turn.v6` | `/candidates/*/analogy/source_memory_refs` | `too_short` | 4 |
| `batch-critic.v2` | `/repair` | `extra_forbidden` | 4 |
| `conjecturer.atomic-candidate.v1` | `/candidate/checker_specs/*/id` | `extra_forbidden` | 4 |
| `conjecturer.turn.v6` | `/scratch_proposal/links/*` | `value_error` | 4 |
| `conjecturer.turn.v6` | `/authorized_pointer` | `extra_forbidden` | 3 |
| `conjecturer.turn.v6` | `/*/content` | `extra_forbidden` | 3 |
| `conjecturer.turn.v6` | `/*/evidence_refs` | `extra_forbidden` | 3 |
| `conjecturer.turn.v6` | `/scratch_proposal/links_meta` | `extra_forbidden` | 3 |
| `batch-critic.v2` | `/pointer` | `extra_forbidden` | 3 |

## How the JSON arrived

| wire shape | count |
|---|---|
| `bare_json` | 1484 |
| `fenced_json` | 1254 |
| `prose_wrapped_fenced_json` | 3 |
| `prose_wrapped_bare_json` | 2 |
