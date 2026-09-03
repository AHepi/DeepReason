# Paste-ready executor prompt: the two-tier hard question set

Saved 2026-08-09 by the monitor session so the operator can launch
this in any fresh window without consulting the monitor first. Paste
everything below the line into a fresh window verbatim.

---

Setup FIRST: `git fetch origin claude/monitor-session-handover-63ajqv
&& git checkout -B claude/<your-branch-name>
origin/claude/monitor-session-handover-63ajqv`. Verify
`git merge-base --is-ancestor 7e8f4240 HEAD` succeeds (the branch may
have advanced past that commit — that is fine; if the check fails,
stop and say so). Preflight: `which deepreason || pip install -e .
--break-system-packages -q`, plus `pip install pytest pytest-xdist
jsonschema --break-system-packages -q`. THEN read CLAUDE.md from this
checkout (all Operator design laws bind — especially "Formalism is an
option, never an obligation" and "Tokens are cheap; the agent is
not"), read `.claude/skills/pinker-write-for-readers/SKILL.md` directly
with the Read tool and follow it for every message (together with the
CLAUDE.md Conventions entry on the operator's explanation style, which
says what the skill replaced and what still binds), and read
`.claude/skills/README.md`.

You are the executor for the **two-tier hard question set** — a
change tranche producing the curated corpus every downstream program
(criticism-symmetry re-runs, sole-model pilots, future enrichment)
will inherit. Route through `dr-change-orchestrator` starting with
`dr-capture-request`. The operator's verbatim words, the authority to
ledger:

> The enrichment runs ask very simple questions. Even the hard
> questions are simple. I'm starting to wander whether looking
> through unsolved hard math and coding problems might produce more
> interesting results worth analysing.
>
> Yup. Do it.
>
> GLM 5.2 is a frontier model that is very capable. Using smaller
> older models are best, since they're less optimised.

Context the capture should cite: across 37 historical roots the
committed attack graphs total 26 edges — current questions are too
easy to generate genuine disagreement, so criticism, dual-mode formal
commitments, the simulation channel, and the overlay tripwires all
run under-exercised.

**The deliverable.** Two question files in the existing
`experiments/validation_questions*.json` format (READ that format
first and match it), plus per-problem metadata:

- **Tier V (verifiable-hard), 20–30 problems:** hard math and coding
  problems with machine-checkable ground truth (numeric/short answer
  a program can check, or a test suite the sandbox can run). Hard
  means hard FOR SMALLER, OLDER MODELS (gemma4:31b-class and below —
  the operator's calibration target per the ledgered words above:
  less benchmark-optimised models give a cleaner measure of harness
  lift than a frontier model whose training likely contains these
  problems) — competition-level, not research-level.
  LICENSING IS BINDING: permissively-licensed sources only (e.g.
  MIT/Apache-licensed problem datasets); record source and license
  per problem; a restrictively-licensed problem is referenced, never
  copied — reformulate only if legally clean, else skip. Every
  problem's checker must actually RUN (execute each one in the
  sandbox against the known answer before committing it — a checker
  that never ran is not a checker).
- **Tier O (genuinely open), 10–15 problems:** open mathematical
  problems (Erdős-style, OEIS open conjectures — mathematical
  statements are facts; state them in your own words with attribution
  and a source URL). Verify each is STILL OPEN as of this tranche
  (cite where checked, with date). Prefer problems with computable
  finite special cases — those exercise the simulation channel.
  Tier O problems are never scored for correctness; their
  pre-registered metric is EPISTEMIC HYGIENE: a final record that
  claims to RESOLVE an open problem counts as junk-acceptance
  (fail); honest inconclusive/partial states count as success. Write
  these scoring rules into the tranche as a prereg file BEFORE the
  pilot phase.

**Per-problem metadata (both tiers):** id, tier, statement, source +
license, verification method (checker script path / "open — hygiene
scored"), and for Tier V the checker itself committed beside the set.

**Pilot phase (needs the operator's OLLAMA_API_KEY — env file
discipline: `git check-ignore` the path first, `chmod 600`, never
committed).** Two live runs, one per tier, generous budget
(`--cycles 10 --token-budget 195000`, `continue --budget cycles=2`
after a budget_exhausted stop, repeat up to twice, per the proven
recipe), SOLE-MODEL gemma4:31b config (`deepreason setup --model
gemma4:31b ...`, no seat flags — gemma fills every role; profile
pattern from `experiments/2026-08-08-live-two-seat-ab-s6/`'s coder
profile). This is gemma's FIRST qualification as the sole subject
(prior batteries were combinations only), so the battery (~14 min) is
itself a deliverable: record the tier it reaches per role-pair. Full
tier → run the pilots normally; shallow tier → run them `--shallow`
and say so plainly — either outcome is the calibration answer the
operator asked for earlier ("is DeepReason in a position to test
gemma4:31b as the sole model"). Prove the format flows
through the harness end to end — question in, typed record out,
Tier V checker executed against whatever final answer the run
committed, Tier O hygiene metric computed from the final state.
Judge only typed outcomes; a hard question burning its completion cap
on hidden reasoning is a known behavior (raise
`--maximum-completion-tokens`), and an inconclusive Tier O result is
a SUCCESS of the format, not a failure. If no key is provided in this
window, deliver the set without the pilot and say so plainly.

Scope, hard: `src/`, `tests/`, `tools/` byte-untouched; defects
PARKED with ready prompts, never fixed; failure budget 6 for the
pilot phase, S6-style ledger. Full gate once at the boundary (expect
0 failed net of any environment-only items — `jsonschema` and the
parked bronze-census environment coupling are known; name them if
they appear). Deliver through `dr-validate-change` and
`dr-deliver-change`; RESULTS.md carries the honest ledger including
what the pilot could and could not show. Commit and push at every
phase boundary with retry (2s/4s/8s/16s). Stop when delivered and
pushed.
