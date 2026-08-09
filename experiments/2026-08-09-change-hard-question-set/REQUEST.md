# Request: the two-tier hard question set

Captured: 2026-08-09, from the operator's messages in this session plus
the paste-ready operative brief the operator pointed the executor at
(`docs/proposals/HARD_QUESTION_SET_PROMPT.md`, saved 2026-08-09 by the
prior monitor session and confirmed current/reconciled in this one).

## Map preflight (recorded per CLAUDE.md/dr-change-orchestrator)

- `DR-CON-run-identity` — pilot run ids, amend/continue semantics
- `DR-SUB-manifest` — qualification, sole-model gemma4:31b config, `--shallow` tier
- `DR-CON-seats` — no-seat-flags sole-model config (gemma fills every role)
- `DR-SUB-scheduler` — cycles/token-budget semantics for the pilot recipe

`docs/map/INV-frozen-surfaces.md` read this session: the five frozen
surfaces (`capabilities/state.py`, `harness.py`, `invariants.py`,
`run_manifest.py`, `qualification.py`) are not implicated — this
tranche's scope is data files under `experiments/` plus documentation,
not `src/`.

## Verbatim

> The enrichment runs ask very simple questions. Even the hard
> questions are simple. I'm starting to wander whether looking
> through unsolved hard math and coding problems might produce more
> interesting results worth analysing.

> Yup. Do it.

> GLM 5.2 is a frontier model that is very capable. Using smaller
> older models are best, since they're less optimised.

(Live follow-up, same session, offered explicitly as corrections to
the above — quoted from the operator's follow-up message):

> Difficulty recalibrated: "hard" now means hard for gemma4:31b-class
> and below — with the rationale stated: less benchmark-optimised
> models give a cleaner measure of what the harness contributes,
> versus a frontier model whose training likely contains the
> problems.

> Pilot runs sole-model gemma, no seat flags — gemma fills every
> role, glm nowhere in the loop.

> Bonus folded in: since gemma has only ever been qualified inside
> combinations, the pilot's battery is its first as the sole subject
> — so this tranche also answers your earlier question ("is
> DeepReason in a position to test gemma4:31b as the sole model") as
> a recorded deliverable: full tier → normal pilots; shallow tier →
> --shallow pilots. Either outcome is the calibration answer.

Context the operator supplied for the capture (not an instruction,
the stated reason for the change):

> across 37 historical roots the committed attack graphs total 26
> edges — current questions are too easy to generate genuine
> disagreement, so criticism, dual-mode formal commitments, the
> simulation channel, and the overlay tripwires all run
> under-exercised

The paste-ready brief at `docs/proposals/HARD_QUESTION_SET_PROMPT.md`
elaborates the same authority in the operator's own recorded words
(saved by the monitor session from the operator's design, already
reconciled with the three live corrections above). Its deliverable/
pilot/scope clauses are quoted and split below exactly as if spoken
in this window, since the operator directed the executor to treat it
as the operative brief.

## Requirements

R1 (artifact): "looking through unsolved hard math and coding
problems might produce more interesting results worth analysing" +
"Yup. Do it." — produce a curated corpus of hard math/coding
problems (two tiers, below) to replace the too-easy enrichment
questions.

R2 (behavior): difficulty target is "hard ... for gemma4:31b-class
and below" (per the live correction superseding the original "GLM
5.2 is a frontier model ... using smaller older models are best"
framing) — problems must be selected/authored to be hard for that
model class, not for glm-5.2 or research-level difficulty.

R3 (artifact): "Two question files in the existing
experiments/validation_questions*.json format (READ that format
first and match it)" — Tier V and Tier O each get their own file in
the pre-existing schema.

R4 (artifact): Tier V — "20-30 problems: hard math and coding
problems with machine-checkable ground truth (numeric/short answer a
program can check, or a test suite the sandbox can run)... hard means
hard FOR [gemma4:31b-class and below] ... competition-level, not
research-level."

R5 (process/behavior): Tier V licensing — "LICENSING IS BINDING:
permissively-licensed sources only (e.g. MIT/Apache-licensed problem
datasets); record source and license per problem; a
restrictively-licensed problem is referenced, never copied —
reformulate only if legally clean, else skip."

R6 (process): Tier V checkers — "Every problem's checker must
actually RUN (execute each one in the sandbox against the known
answer before committing it — a checker that never ran is not a
checker)."

R7 (artifact): Tier O — "10-15 problems: open mathematical problems
(Erdős-style, OEIS open conjectures — mathematical statements are
facts; state them in your own words with attribution and a source
URL)."

R8 (process): Tier O openness verification — "Verify each is STILL
OPEN as of this tranche (cite where checked, with date)."

R9 (behavior): Tier O selection preference — "Prefer problems with
computable finite special cases — those exercise the simulation
channel."

R10 (process/artifact): Tier O scoring — "Tier O problems are never
scored for correctness; their pre-registered metric is EPISTEMIC
HYGIENE: a final record that claims to RESOLVE an open problem counts
as junk-acceptance (fail); honest inconclusive/partial states count
as success. Write these scoring rules into the tranche as a prereg
file BEFORE the pilot phase."

R11 (artifact): per-problem metadata, both tiers — "id, tier,
statement, source + license, verification method (checker script path
/ "open — hygiene scored"), and for Tier V the checker itself
committed beside the set."

R12 (process): pilot credential handling — "needs the operator's
OLLAMA_API_KEY — env file discipline: git check-ignore the path
first, chmod 600, never committed."

R13 (behavior): pilot execution — "Two live runs, one per tier,
generous budget (--cycles 10 --token-budget 195000, continue --budget
cycles=2 after a budget_exhausted stop, repeat up to twice, per the
proven recipe)."

R14 (behavior): pilot model config — "Pilot runs sole-model gemma, no
seat flags — gemma fills every role, glm nowhere in the loop." (live
correction; supersedes the paste-ready brief's own paraphrase, which
already matches this).

R15 (artifact/behavior): gemma-sole-model calibration bonus — "since
gemma has only ever been qualified inside combinations, the pilot's
battery is its first as the sole subject — so this tranche also
answers your earlier question ('is DeepReason in a position to test
gemma4:31b as the sole model') as a recorded deliverable: full tier →
normal pilots; shallow tier → --shallow pilots. Either outcome is the
calibration answer." Record which tier the qualification battery
reaches per role-pair.

R16 (behavior): pilot judging discipline — "Prove the format flows
through the harness end to end — question in, typed record out, Tier
V checker executed against whatever final answer the run committed,
Tier O hygiene metric computed from the final state. Judge only typed
outcomes; a hard question burning its completion cap on hidden
reasoning is a known behavior (raise --maximum-completion-tokens),
and an inconclusive Tier O result is a SUCCESS of the format, not a
failure."

R17 (process): pilot contingency — "If no key is provided in this
window, deliver the set without the pilot and say so plainly."

R18 (process): scope lock — "src/, tests/, tools/ byte-untouched;
defects PARKED with ready prompts, never fixed; failure budget 6 for
the pilot phase, S6-style ledger."

R19 (process): gate — "Full gate once at the boundary (expect 0
failed net of any environment-only items — jsonschema and the parked
bronze-census environment coupling are known; name them if they
appear)."

R20 (process): delivery route — "Deliver through dr-validate-change
and dr-deliver-change; RESULTS.md carries the honest ledger including
what the pilot could and could not show."

R21 (process): commit discipline — "Commit and push at every phase
boundary with retry (2s/4s/8s/16s). Stop when delivered and pushed."

## Standing constraints

C1: "Tokens are cheap; the agent is not" (CLAUDE.md, Operator design
law, operator's words verbatim: "Ollama API tokens are cheap, you are
not. Running endless API experiments is preferred if it means you do
less work. Creating evidence from live runs is preferred if it means
less work.") — applies to how the pilot and any checker-verification
work should be done: prefer live/sandbox execution over hand-reasoning.

C2: "Formalism is an option, never an obligation" (CLAUDE.md,
Operator design law) — bears on how Tier O problems and any
dual-mode framing in the question files are authored: nothing may
require formal commitment.

C3: src/, tests/, tools/ byte-untouched (R18) — hard scope boundary
for this entire tranche.

## Open questions (for dr-spec-change)

Q1: Whether the operator's OLLAMA_API_KEY has in fact been provided
in this window (the task description opened with a bare string
labeled "This is an API key. Standby for further instructions," sent
before this tranche's instructions arrived) — R17's fallback
("deliver without the pilot") depends on this being resolved factually,
not assumed either way.

Q2: Exact selection process/sourcing pipeline for Tier V and Tier O
problems is not specified verbatim beyond "permissively-licensed
sources," "MIT/Apache-licensed problem datasets," "Erdős-style, OEIS
open conjectures" — dr-spec-change must pick concrete sources and
record the choice as an assumption.

Q3: "the proven recipe" (R13) for `continue --budget cycles=2` is
referenced but not restated in full; dr-spec-change should locate the
prior tranche it was proven in (`experiments/2026-08-08-live-two-seat-ab-s6/`
per the paste-ready brief's profile-pattern pointer) and cite it.

## Amendments

(none yet — this REQUEST.md already incorporates the operator's live
follow-up corrections as part of the initial capture, since they
arrived before any SPEC.md existed)
