# Request: budget ceiling checked at commit time, not only at plan time

Captured 2026-08-05, monitor session.

## Operator's words (verbatim)

Monitor's offer, grounded in V1's self-reported miss ("The commit is 193
insertions against a ≤150 ceiling — that should have tripped the
orchestrator's stop condition and sent the plan back to you, and it
didn't"):

> the 193-vs-≤150 overrun *should* have tripped the stop and didn't,
> because the ceiling is checked against the estimate at plan time, not
> against actual insertions at commit time. That's a one-sentence fix in
> the execute/implement skills — "before committing, compare actual
> changed lines against the spec's ceiling; exceeding it is a stop, not
> a footnote." Say the word and I'll add it to both repos' skills.

> do it

## Requirements

- R1: `dr-execute-step` and `dr-implement-fix` check ACTUAL changed
  lines (`git diff --stat`) against the governing document's budget
  ceiling before committing; exceeding it is a stop in the
  stop-with-recommendation format, not a footnote.
- R2: The same rule lands in the Heddle repo's `execute_step` and
  `implement` skills, in that harness's grammar (its own branch and
  commit).

## Constraints

- C1: Skill files only, both repos.
- C2: General-use wording.
