# Dimension: dead code

Method: a reference census over every top-level `def`/`class` in
`src/deepreason/`, across all 34 packages in one pass.

**Implementation differs from the 2026-08-13 audit, deliberately.** That
run issued a `rg` per symbol. This run builds one token index over every
`.py` file in `src/`, `tests/`, `scripts/` and `tools/` (excluding
`__pycache__` and `tools/treadle/.venv`) and answers each symbol's
question by set membership. The ladder is identical — referencing files
outside the defining file, then intra-file use ≥ 2, then quoted-string
reference, then `pyproject.toml` entry point, then `candidate-dead` — so
the two runs are directly comparable and the agreement below is a real
replication, not a shared bug.

## Totals

| | count |
|---|---|
| top-level symbols censused | 2947 |
| `referenced` | 2932 (of which 449 intra-file only) |
| `dynamic-ref` | 0 |
| `entry-point` | 0 |
| **`candidate-dead`** | **15** |

Per-package tally: `proof/dead-tally.txt`. Machine-readable:
`proof/dead-census.json`. Candidates: `proof/dead-candidates.txt`.

## The 15 candidates — identical to 2026-08-13, symbol for symbol

| symbol | file |
|---|---|
| `last_json_line` | `brain/log.py` |
| `retrieval_metrics` | `brain/metrics.py` |
| `_cmd_check_proof` | `cli/main.py` |
| `_cmd_code` | `cli/main.py` |
| `_cmd_simulate` | `cli/main.py` |
| `_slug` | `easy.py` |
| `_fresh` | `easy.py` |
| `_first_line` | `easy.py` |
| `suppressible_lineage_exemplars` | `jolts.py` |
| `_document_excerpt` | `llm/packs.py` |
| `alias_references` | `llm/packs.py` |
| `refl` | `rules/refl.py` |
| `domain_log_input` | `rules/guards/anti_relapse.py` |
| `materialize_run_config` | `run_manifest.py` |
| `record_trigger_decision` | `views/jolt_signals.py` |

**This is the same set the 2026-08-13 audit parked as its P2, with no
additions and no removals** — reproduced by a different model running a
different implementation twelve days and roughly a thousand tests later.
Two consequences, and they pull in opposite directions:

1. **P2 was never executed.** Nothing was deleted and nothing was
   annotated, so the list stands unchanged.
2. **The list is now independently corroborated.** A second method
   agreeing exactly is much stronger evidence than one method run twice.

## `candidate-dead` does not mean "delete" — one worked example

`_document_excerpt` (`llm/packs.py`) is on this list and **should not be
deleted**. `experiments/2026-08-01-change-prose-can-refute/PARKED.md`
records the decision explicitly: after that tranche's step 9 it had no
caller anywhere, and it was "deliberately kept rather than deleted,
because it is the right tool for this path if the operator wants R3
extended to it" — the batch crit path that still prefix-clips its targets.

That is exactly why `candidate-dead` is this worker's ceiling and why
deletion needs its own tranche: a mechanical scan cannot distinguish
"nobody calls this" from "nobody calls this yet, on purpose, and the
reason is written down elsewhere." At least one of the 15 has a recorded
reason to stay. The other fourteen have not been checked for one.

## No new dead code in twelve days

The tree grew by roughly a thousand tests and a dozen subsystems since
the comparison audit, and added zero new unreferenced top-level symbols.

**Count line: 2947 symbols censused, 15 `candidate-dead`, 0 new since
2026-08-13, 1 known deliberate keep among them.**
