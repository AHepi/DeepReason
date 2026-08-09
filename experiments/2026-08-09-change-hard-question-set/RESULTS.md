# Results: the two-tier hard question set

## 2026-08-09 — corpus delivered, both pilots run, honest ledger

### The corpus (R1, R3, R4, R7, R11)

- **Tier V** (`experiments/validation_questions_tier_v.json`, 20
  problems): 10 math (Hendrycks MATH, Level 4-5 competition split, MIT
  license) + 10 coding (OpenAI HumanEval, hand-picked for genuine
  algorithmic content, MIT license). Every problem has a checker
  (`experiments/tier_v_checkers/`, 20 files) that was RUN against its
  known answer/reference solution before commit (R6) and
  mutation-proven against a deliberately wrong answer/candidate.
- **Tier O** (`experiments/validation_questions_tier_o.json`, 10
  problems): Collatz, Goldbach, Twin Prime, Legendre's, Erdős–Straus,
  Lonely Runner, Beal's, odd-perfect-number existence, Riemann
  Hypothesis, Union-closed sets — each independently re-verified STILL
  OPEN on 2026-08-09 (not trusted from any single index), with a
  correction found in the process (Lonely Runner is now proven for
  k<=12 as of 2025-2026; the record names k=13 as the real open
  frontier, not "unproven in general"). Noteworthy: every one of the
  10 currently has an unreviewed, non-peer-reviewed "proof" claim in
  public circulation — direct motivation for PREREG.md's hygiene rule.
- **PREREG.md** committed before either pilot launched (R10): the
  scoring rules could not be fitted to what a pilot happened to
  produce.

### Failure ledger (pilot phase, budget 6)

## Failure ledger (pilot phase, budget 6)

| # | Leg | What happened | Charged? |
|---|-----|----------------|----------|
| — | Tier V | `setup`/`qualify`/`reason`/both `continue` legs/all three audits all returned rc=0; one `verify_root` violation (`foreign-criticism`) appeared on the FIRST audit and had cleared by the second — not a run failure, a mid-run state that resolved, recorded honestly | **0 charged** |
| — | Tier O | Same shape: every command rc=0, same transient `foreign-criticism` finding clearing by the second audit. The JUNK-ACCEPTANCE hygiene verdict (below) is the pilot correctly MEASURING a real failure mode in the model's output — that is the metric working, not the pilot failing | **0 charged** |

Running total: **0 / 6** spent after both pilot legs.

## Tier V pilot — typed outcome (full detail: CHECKLIST.md step 19)

- Qualification: **full tier**, 300/300 cases, fresh (not cached), 124s.
- Reason + 2x continue: 14 cycles total, `state=completed`,
  `stop_reason=budget_exhausted` (the full recipe budget was actually
  used, not just offered).
- `verify_root`: clean by the final audit (`replay_valid: true`, 0
  violations); the transient `foreign-criticism` finding on the first
  audit is PARKED (step 24) as a possible structural consequence of
  sole-model operation, not fixed here.
- Tier V checker (tv-m04, known answer 16592) run against all 102
  final accepted claims: **no match** (`checker_any_pass: false`).
  Acceptable typed outcome per R16/PREREG.md — the harness format
  worked end to end; the question was hard enough that gemma4:31b did
  not solve it within budget.

## Tier O pilot — typed outcome (full detail: CHECKLIST.md step 22)

- Qualification: **full tier**, 300/300 cases, fresh, 114s (consistent
  with the Tier V leg — gemma4:31b as sole model reaches full
  qualification reliably, not just once).
- Reason + 2x continue: 14 cycles total, `state=completed`,
  `stop_reason=budget_exhausted`.
- `verify_root`: clean by the final audit (same `foreign-criticism`→
  clears-on-continue pattern as Tier V — two independent live
  observations of the same shape strengthens the "transient, not
  persistent" reading, PARKED for a future tranche to confirm properly
  rather than asserted here as proven).
- **Hygiene verdict: JUNK-ACCEPTANCE (FAIL)** per PREREG.md. The final
  record (141 accepted positions, 0 refuted, 0 suspended) contains
  multiple `role=conjecturer` artifacts that directly target the run's
  own seed question and flatly assert the Collatz conjecture IS
  resolved — "settled in the negative: it is fundamentally
  undecidable...", "settled as 'True' in a probabilistic sense...",
  "settled in the negative: it is false, and the counterexample is a
  'near-cycle'..." — unretracted in the committed record. This is
  exactly the failure mode R10 exists to catch, and the pilot caught
  it on its first live attempt.
- **The more interesting finding**: the record ALSO contains multiple
  `role=critic` artifacts correctly calling several of these claims
  "factual errors" (undecidability is itself an unproven
  meta-hypothesis, not a settlement) — but `positions.refuted` is
  empty, so these valid criticisms never flip the overclaiming
  artifacts' status. A reader who only checks `positions.accepted`
  sees the overclaim standing, unqualified. This traces directly to
  CLAUDE.md's own recorded law ("no warrant, no edge, no REFUTED"):
  prose criticism without a formally wired attack/warrant leaves the
  target's status untouched. PARKED (below) as a genuine, evidenced
  gap — not fixed in this tranche (scope-locked to `src/` untouched)
  — and it is the clearest possible confirmation of the operator's own
  original diagnosis: on the OLD, too-easy question set, criticism and
  warrants ran under-exercised because there was rarely anything worth
  contesting; on a genuinely hard/open question, the gap between
  "criticism happened" and "criticism changed the record's standing
  claims" opened up immediately.

## What the pilot answers about gemma4:31b as sole model (operator's standing question)

**Full tier, both times, from a clean/fresh qualification battery.**
This tranche is gemma4:31b's first qualification as the SOLE subject
(prior batteries only ever tested it in combination with another
model, per REQUEST.md's framing of the question). The answer is
unambiguous and reproduced twice: DeepReason is in a position to test
gemma4:31b as the sole model at FULL capability, not the reduced
`--shallow` fallback — no `--shallow` retry branch fired in either
pilot.

### What the pilots proved, and what they did NOT (honest residue)

**Proved (typed, replay-verifiable):**
- The two-tier corpus format flows through the real harness end to
  end — question in, typed record out — for both a closed hard
  problem (Tier V) and a genuinely open one (Tier O).
- gemma4:31b qualifies at full tier as the sole model, reproduced
  twice.
- The corpus is materially harder than the prior set: across 37
  historical roots the baseline was 26 total attack-graph edges; a
  SINGLE Tier O pilot run alone produced 141 accepted positions with
  active, consequential (if imperfectly wired) criticism traffic —
  the under-exercise problem the operator named is measurably
  addressed by this corpus, at least on the two questions tried.
- A genuine, reproducible weakness: Tier O hygiene fails on first
  contact with a real open problem, and a real, evidenced gap exists
  between "criticism happened and was right" and "the record's own
  accepted-claims view reflects that" (PARKED.md item 2).

**NOT proved — residue, stated plainly:**
- **n=1 per tier.** One live attempt on one representative question
  per tier is a DEMONSTRATION, not a statistical claim, per CLAUDE.md's
  own stochasticity doctrine — capability-channel and criticism
  behavior varies run to run. Whether the Tier V checker-miss and the
  Tier O junk-acceptance verdict are TYPICAL of the other 19 Tier V and
  9 Tier O problems, or artifacts of these two particular questions, is
  unknown and unproven by this tranche. A full-corpus run is future
  work, not attempted here (R13 specified "one per tier," and the CLI's
  own `reason` command takes one question at a time — SPEC.md's A1).
- **The `foreign-criticism` transient violation's cause** is observed
  (twice) but not diagnosed — PARKED.md item 1, not investigated here
  by design (scope-locked, `src/` untouched).
- **Whether the criticism-status gap (PARKED.md item 2) is a defect or
  intended behavior** is an open question this tranche raises and
  explicitly does NOT answer — CLAUDE.md's "no warrant, no edge, no
  REFUTED" law is cited as the plausible intended-behavior explanation,
  not confirmed as the actual cause.
- **Difficulty calibration (R2/A2)** was picked by SOURCE (MATH's own
  Level 4-5 split; hand-picked non-trivial HumanEval problems), not
  validated by a systematic probe against gemma4:31b-class models
  before commit — the pilot's own no-match result on tv-m04 is n=1
  evidence consistent with the calibration, not proof of it.
