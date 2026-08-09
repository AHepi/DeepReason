# Spec: the two-tier hard question set

Interprets REQUEST.md (all citations below are R-numbers from that
file). Every place the request is silent, the smallest reasonable
reading is chosen and recorded as an assumption (A-numbers); two
readings that differ materially are asked, not guessed (none arose —
see "Questions resolved without asking" below).

## Map ids carried over

`DR-CON-run-identity`, `DR-SUB-manifest`, `DR-CON-seats`,
`DR-SUB-scheduler`. Confirmed this tranche touches none of the five
frozen surfaces (`docs/map/INV-frozen-surfaces.md`): no `src/` change
is planned (R18 forbids it outright).

## Research performed for this spec (facts, not guesses)

- `scripts/validate.py` reads `experiments/validation_questions*.json`
  (array of `{"id", "q", "accept"}`) for a standalone bake-off study —
  it is NOT the DeepReason harness itself. `deepreason reason` (the
  actual harness entry point used by the pilot) takes ONE question as
  a positional string argument (`deepreason reason "<question text>"
  --cycles N --token-budget N [--shallow]`) — there is no
  multi-question batch mode. **This means the pilot's "question in,
  typed record out" proof (R16) necessarily runs ONE representative
  problem per tier through the harness, not the whole file** — see A1.
- `deepreason qualify` writes a durable tier record: `full` (complete
  battery passed), `shallow` (reduced battery passed, `reason
  --shallow` required), or `unqualified`
  (`src/deepreason/qualification.py` lines 52-56, 472-536). This is
  exactly the mechanism R15's "full tier → normal pilots; shallow tier
  → `--shallow` pilots" refers to.
- Confirmed by direct fetch: the Hendrycks **MATH** dataset
  (github.com/hendrycks/math) and OpenAI's **HumanEval**
  (github.com/openai/human-eval) are both MIT-licensed — satisfies
  R5's "e.g. MIT/Apache-licensed" bar. MATH problems (AMC/AIME-style,
  competition math, numeric/short boxed answers) source Tier V math;
  HumanEval problems (docstring + reference solution + `check(candidate)`
  test function) source Tier V coding — HumanEval's own checker
  convention is reused directly rather than reinvented (R6).
- Tier O statements are the operator's own words: "mathematical
  statements are facts; state them in your own words" (R7) — a
  restated mathematical fact carries no copyright, so Tier O has no
  licensing question; the obligation is accuracy (source URL,
  attribution) and currency (R8: verified still open, dated).
  Wikipedia's "List of unsolved problems in mathematics" is the index
  used to shortlist candidates; each one's open status is re-verified
  independently (not trusted from the index alone) during authoring,
  with its own citation — Erdős's discrepancy problem is EXCLUDED from
  the shortlist because it is a known **resolved** case (Tao, 2015) an
  index can misfile under "unsolved" by category rather than status.
- `experiments/2026-08-08-parked-bronze-census-env/PARKED.md` and
  `jsonschema`-not-declared are the two named "environment-only" gate
  items R19 anticipates; `jsonschema` 4.26.0 is already installed this
  session (preflight), so only the bronze-census environment coupling
  is a plausible residual if it appears.
- `experiments/2026-08-08-live-two-seat-ab-s6/` is the cited "proven
  recipe" tranche (R13's "per the proven recipe"): its `s6_run.sh` is
  the ladder-script template (setup → qualify → reason → audit →
  continue → re-audit), reused here MINUS its `--seat coder=...`
  binding (R14: no seat flags at all).

## File layout (all new; nothing in `src/`, `tests/`, `tools/` touched — R18)

    experiments/validation_questions_tier_v.json        # R3, R4, R11
    experiments/validation_questions_tier_o.json         # R3, R7, R11
    experiments/tier_v_checkers/<id>_checker.py           # R6, R11 (one file per Tier V problem)
    experiments/2026-08-09-change-hard-question-set/
      REQUEST.md SPEC.md CHECKLIST.md                     # already/to be written
      PREREG.md                                            # R10, hygiene scoring rules
      PARKED.md                                            # R18's defect ledger (this family's convention)
      env                                                  # R12, gitignored, chmod 600, NEVER committed
      pilot-tier-v/, pilot-tier-o/                         # DEEPREASON_HOME roots for the two live runs, R13
      VALIDATION.md DELIVERY.md RESULTS.md                 # R19, R20

## R1 — deliver the corpus

Two files above, plus their checkers and metadata, are the corpus.
Acceptance: both files exist, are valid JSON, parse against the schema
below, and their problem counts satisfy R4/R7's ranges.

## R2 — difficulty target: gemma4:31b-class and below

Acceptance check, per problem: not solvable correctly by a single
unaided completion at default settings from a model in this class on
the FIRST attempt for a random sample check — but a live per-problem
difficulty gate is out of scope-of-effort for 20-30 problems (would
itself be a mini pilot per problem). **A2**: difficulty is established
by SOURCE, not by a live probe: MATH problems are drawn from its
`level 4-5` competition-difficulty split (the dataset's own hardest
tiers, calibrated against far larger models than gemma4:31b-class in
the original paper); HumanEval problems are hand-selected for
multi-step algorithmic content (graph/DP/number-theory, not
single-line string ops) rather than trusted uniformly, since HumanEval
spans a wide internal difficulty range. This is a recorded assumption,
falsifiable directly by the pilot: if the one live Tier V problem run
through the harness is answered correctly by sole-model gemma on the
first pass, that is evidence (not proof, n=1) the calibration erred
high; RESULTS.md records the outcome honestly either way (R16
explicitly treats a correct pilot answer as fine — judging is on typed
outcomes, not on re-litigating difficulty after the fact).

## R3/R11 — schema (extends, does not break, the existing format)

Existing format element: `{"id": str, "q": str, "accept": [str, ...]}`.
Both tiers keep `id` and `q` (so any future tool built for the old
format's minimal shape — id+q — still finds them) and ADD the fields
R11 requires:

Tier V (`validation_questions_tier_v.json`), array of:

    {
      "id": "tv-01",
      "tier": "V",
      "q": "<problem statement>",
      "kind": "math" | "coding",
      "accept": ["<answer>", ...],        // kind=math only; numeric/short-answer
      "checker": "experiments/tier_v_checkers/tv-01_checker.py",  // always present
      "source": {"dataset": "...", "problem_id": "...", "url": "..."},
      "license": "MIT",
      "verification": "checker script (run against known answer before commit)"
    }

For `kind=coding`, `accept` is omitted (a test suite, not a short
string, is the ground truth) and the checker embeds the reference
`check(candidate)` function plus the known-good reference solution
used to prove the checker fires green (R6).

Tier O (`validation_questions_tier_o.json`), array of:

    {
      "id": "to-01",
      "tier": "O",
      "q": "<problem statement, own words>",
      "attribution": "<person/community the conjecture is named for>",
      "source_url": "...",
      "still_open_verified": "2026-08-09",
      "computable_special_case": "<what finite instance a run can check, or null>",
      "verification": "open — hygiene scored"
    }

Acceptance: `python -c "import json; json.load(open(P))"` on both
files; every record has every field above present (a small schema
validator script is written as part of CHECKLIST, since `tools/` is
off-limits — it lives at
`experiments/2026-08-09-change-hard-question-set/schema_check.py`,
which is NOT `tools/`).

## R4 — Tier V, 20-30 problems

**A3**: target the low end, 20 (10 math from MATH level 4-5, 10 coding
from HumanEval), to keep checker-authoring and per-checker sandbox
execution (R6) tractable inside this tranche's effort budget while
still satisfying "20-30." Mix satisfies "hard math AND coding
problems" (R4's own conjunction) rather than picking one.

## R5 — licensing

MATH and HumanEval are both confirmed MIT (see Research above).
`source.dataset`, `source.url`, and top-level `license` are populated
per problem, verbatim from the confirmed license. No restrictively
licensed source is used, so the "reformulate only if legally clean,
else skip" branch does not trigger for this tranche; recorded here so
a future tranche adding more problems knows the branch exists and
carries no precedent yet.

## R6 — checkers must actually run

CHECKLIST step(s) execute every checker script directly in this
session's sandbox (this container — the same sense "sandbox" is used
in R6, not the harness's own simulation-channel concept, which is a
different mechanism entirely and not what checks a committed final
answer) against the problem's own known answer/reference solution, and
paste the exit code / test output as the step's done-criterion. A
checker that has never produced a passing run for the known answer is
never committed (R6 verbatim).

## R7/R8/R9 — Tier O, 10-15 problems

**A4**: target the low end, 10, same effort-tractability reasoning as
A3. Shortlist (subject to the individual open-status re-verification
CHECKLIST performs, which may swap an entry — R8 is authoritative over
any list written here): Collatz, Goldbach, Twin Prime, Legendre's,
Erdős–Straus, Lonely Runner, Beal's, odd-perfect-number existence,
Riemann Hypothesis, Union-closed sets. Each gets its own citation +
check-date (R8) at authoring time, not copied from this spec's
research pass. Preference order for R9 ("computable finite special
cases"): Collatz (verify one trajectory reaches 1), Goldbach (check
one even number), Erdős–Straus (search x,y,z for one n),
Legendre's (check one interval), odd-perfect (primality/perfection
check on one candidate), Union-closed (check one small family) —
six of ten with a genuinely runnable special case; Twin Prime,
Riemann Hypothesis, Beal's, Lonely Runner are included for breadth
even though their "special case" is more of a search/verification-up-
to-bound than a single decidable check, and each entry says so
honestly in `computable_special_case` rather than overstating it.

## R10 — prereg file, before the pilot phase

`PREREG.md`, committed and pushed BEFORE `pilot-tier-v`/`pilot-tier-o`
are launched (enforced by CHECKLIST step ordering). Contents: the
exact hygiene rule from R10 verbatim, the specific typed-record fields
the audit script reads to classify a Tier O run's final state as
"claims resolution" (fail) vs "honest inconclusive/partial" (success),
and the Tier V checker-invocation rule (R16) — written BEFORE any
pilot output exists, so it cannot be reverse-fitted to what the pilot
produces.

## R12 — credential handling

`experiments/2026-08-09-change-hard-question-set/env`, confirmed
`git check-ignore`'d this session (exit 0). CHECKLIST step: write the
key, `chmod 600`, confirm `git status` shows it untracked, confirm
`git check-ignore` again post-write. Never `cat` the file into any
committed artifact or into this conversation's tool output in a form
that would be persisted to a file under version control.

## R13 — pilot execution, two live runs

**A1** (already justified above): "one per tier" (R13's own words)
means ONE representative question per tier is passed to `deepreason
reason`, selected from that tier's committed file — not a batch of
all 20/10. Ladder scripts `pilot_tier_v_run.sh` / `pilot_tier_o_run.sh`
follow the S6 template (setup → qualify → reason → audit → continue if
resumable → re-audit), each with its own `DEEPREASON_HOME` so the two
runs cannot collide. `--cycles 10 --token-budget 195000` at `reason`;
`continue --budget cycles=2` after a `budget_exhausted` stop, up to
twice (R13 verbatim), each attempt's typed `stop_reason` recorded.

## R14 — sole-model gemma, no seat flags

`deepreason setup --provider ollama --endpoint https://ollama.com/v1
--model gemma4:31b --model-revision gemma4:31b --family gemma
--credential-env OLLAMA_API_KEY [--context-window-tokens ...]
[--maximum-completion-tokens ...] --reasoning none` — **no `--seat`
flag at all**, so every role (conjecturer, coder, scratch, simulation)
resolves to this one profile per the CLI's own documented default
("no `--seat` leaves every role on the profile above"). Context
window / completion-token values: **A5**, reuse the S6 tranche's
proven `gemma4:31b` values from its `coder-profile.yaml` /
`easy.py`'s `"gemma4_31b"` preset (`temperature=0.7, max_tokens=4000,
reasoning="none"`) rather than guessing new ones, raising
`--maximum-completion-tokens` live only if a run dies exhausting it
(R16's named known behavior).

## R15 — gemma-sole-model calibration bonus

CHECKLIST step captures `deepreason qualify --json`'s tier verdict
(full/shallow/unqualified) for the sole-gemma subject BEFORE deciding
how to invoke `reason`. Full → `reason` runs without `--shallow`.
Shallow → `reason --shallow` (R15 verbatim), stated plainly in
RESULTS.md either way, and reported as the answer to the operator's
standing question regardless of which branch fires — both are useful,
typed answers, not one being a "better" outcome than the other.

## R16 — pilot judging discipline

Post-run audit script (per tier) reads ONLY typed fields: `run-status.json`
state/`stop_reason`, `verify_root`, and for Tier V the final committed
answer (via `deepreason findings`/`export` or the log's terminal
artifact state — CHECKLIST pins the exact reader once the run exists)
fed through that problem's checker; for Tier O, the hygiene classifier
PREREG.md defines. A hard question burning its completion cap is
handled by raising `--maximum-completion-tokens` and re-running that
one leg, not by treating the typed seat failure as a tranche failure.

## R17 — no-key fallback

Not exercised: Q1 (REQUEST.md) resolved that the key is present. If a
later step discovers the value does not authenticate (mirroring the
positive/negative-auth-probe technique the S6 PLAN.md used), the
tranche falls back to R17 at that point and says so plainly, rather
than treating a bad key as a stop-the-whole-tranche condition.

## R18 — scope lock

Enforced procedurally: every CHECKLIST `[COMMIT]` step's `git diff
--numstat` is checked to touch nothing under `src/`, `tests/`,
`tools/`. Any defect noticed while sourcing/checking problems (e.g. in
`scripts/validate.py`, the CLI, qualification) is written to
`PARKED.md` with a ready-to-send prompt, never fixed here. Failure
budget for the pilot phase specifically: 6 (R18 verbatim), tracked in
RESULTS.md as an S6-style numbered ledger as it is spent.

## R19 — gate at the boundary

`python -m pytest tests/ -q -n 4` run ONCE, at the validation
boundary (after all data/checker/prereg/pilot work, before
`dr-validate-change`). Expected 0 failed; the bronze-census
environment-coupling item (parked, see Research above) is the one
named exception this environment might reproduce — if it appears,
VALIDATION.md names it and cites the existing PARKED.md rather than
re-diagnosing a known issue.

## R20/R21 — delivery and commit discipline

Standard `dr-validate-change` → `dr-deliver-change` route; RESULTS.md
written before delivery with the honest ledger (what the pilot
proved, what it could not — e.g. a single live attempt per tier is
demonstration, not statistical proof, consistent with CLAUDE.md's
"Capability-channel use ... is STOCHASTIC" doctrine). Commit and push
after every CHECKLIST phase boundary, retry 2s/4s/8s/16s on push
failure (already demonstrated working this session).

## Diff budget (Rung G1)

Ceiling for the non-run-artifact diff (JSON files, checkers, docs):
**2500 lines**. Committed pilot run roots (typed log/objects/blobs)
are EXCLUDED from this ceiling — they are evidence, not authored
diff, and their size is a function of how many cycles the harness
actually runs, not of anything this tranche writes by hand;
`dr-execute-step`'s `[COMMIT]` gate is told to pass `--paths` scoped
to the authored paths (the two JSON files, `tier_v_checkers/`,
`PREREG.md`, `PARKED.md`, `RESULTS.md`, `schema_check.py`, ladder
scripts) when checking this ceiling, and to report run-root byte
counts separately, uncapped.

## Questions resolved without asking (dominance test, `dr-ask-the-right-question`)

- Q1 (REQUEST.md, key provided?) — resolved YES from the record, see
  REQUEST.md and above.
- Q2 (REQUEST.md, sourcing pipeline) — resolved above: MATH (math) +
  HumanEval (coding) for Tier V, Wikipedia-indexed/independently
  reverified for Tier O.
- Q3 (REQUEST.md, "proven recipe") — resolved above:
  `experiments/2026-08-08-live-two-seat-ab-s6/s6_run.sh`, minus its
  seat binding.

No open question in this spec rises to "stop and ask" — every fork
was either dominance-killed by REQUEST.md's own words (R14 explicitly
overrides any seat-binding reading) or is a smallest-reasonable-choice
assumption (A1-A5) that the pilot itself will falsify or confirm
honestly, per this tranche's own R16 discipline.
