# STOP — diff budget EXCEEDED at the end of phase A

Raised: 2026-08-16, after step 12 (phase A complete, phase B not begun).
Trigger: `dr-execute-step`'s `[COMMIT]` gate — `tools/diff_budget.py`
returned `verdict: EXCEEDED`, which the skill requires be raised as a
stop in the standard format, never a footnote.

## The measurement

    $ python tools/diff_budget.py d52c739ff --ceiling 301 \
        --paths pyproject.toml src/deepreason tests docs CLAUDE.md
    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "d52c739ff",
     "areas": {"pyproject.toml": 13, "src/deepreason": 108,
               "tests": 154, "docs": 33, "CLAUDE.md": 16},
     "total_insertions": 324, "ceiling": 301, "verdict": "EXCEEDED"}

Per file:

        16 +     0 -  CLAUDE.md
         4 +     2 -  docs/EXPERIMENT_PROGRAM_2026-07.md
         7 +     4 -  docs/SCRATCHPAD_GROUNDED_BRIDGE.md
        22 +     1 -  docs/map/SUB-llm.md
        13 +     8 -  pyproject.toml
        85 +     0 -  src/deepreason/cli/main.py
        18 +     8 -  src/deepreason/config.py
         5 +     1 -  src/deepreason/llm/embedder.py
       149 +     4 -  tests/test_embedder.py
         5 +     0 -  tests/test_schema_v3_consumers.py

The tranche directory (REQUEST/SPEC/CHECKLIST) is excluded, correctly:
SPEC.md's 301 itemized the CHANGE (S1-S12), not its artifacts.

## Where the estimate was wrong

| area | SPEC estimate | actual | delta |
|---|---|---|---|
| tests (S9) | 90 | 154 | +64 |
| `src/` (S3 55 + S5 6 + S8 msg ~5) | ~66 | 108 | +42 |
| docs (S4 12 + S8 15) | 27 | 49 | +22 |
| pyproject (S1) | 8 | 13 | +5 |

The overrun is concentrated in tests and comments, not in behaviour
surface. Nothing was built that SPEC.md did not specify: the shipped
behaviour is exactly S1-S5 and S8-S12. What ran long:

- **tests +64.** Three CLI tests for the warm-up rather than one, and
  docstrings that name the motivating record verbatim, which repo
  discipline requires ("Regression (run-<id>): ..."). The mutation
  proofs themselves cost no lines — they were run, not committed.
- **`src/` +42.** `_cmd_embedder_warmup` plus `embedder_cache_dir`
  came to 85 lines in `cli/main.py` against a 55-line estimate for S3,
  most of it the unset-model branch (which the all-configurations law
  requires be a report, not a refusal) and the comments explaining why
  the cache path is derived rather than hardcoded.
- **docs +22.** The `config.py` comment carried three false claims
  rather than the one S5 predicted, and correcting them honestly cost
  more than replacing a phrase.

## Remaining work, priced

Phase B (S6, the loud fallback) ~60 lines src+tests; phase C (S10, the
evidence-honesty append) ~40 doc lines. Projected total at close:
**~424 lines, ~40% over the 301 ceiling.**

## The decision

**Which of these three, given the ceiling was my estimate and not your
constraint?**

**A — raise the ceiling to 450 and finish as specified (RECOMMENDED).**
You lose nothing. The behaviour delivered is exactly what SPEC.md
specified and what your words asked for; the overrun bought test
docstrings that name the grounded-extension run and a warm-up command
that reports rather than refuses an unset model. Cost: two more phases,
no scope change.

**B — cut the terminal-summary half of S6, keeping `deepreason results`
only.** Saves ~15 lines. Cost: R8 names two surfaces in one sentence
("`deepreason results` and the run's terminal summary"); delivering one
is a partial requirement, and the terminal summary is the one an
operator sees without asking.

**C — split S6/S10 into a follow-up tranche.** Saves ~100 lines here.
Cost: this is the one option SPEC.md's Budget section argued against in
advance, and the argument still holds — S1 arms the neural default by
install, and S6 is the instrument that makes a failure of that arming
visible. Shipping S1 alone recreates your original complaint one layer
up: a run that silently measures with the wrong embedder, with nobody
looking at the place it is recorded.

Recommendation: **A**, because the overrun is in evidence and comments,
and B and C both pay for the line count with the half of the change that
prevents a recurrence.
