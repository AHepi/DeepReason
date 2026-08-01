# Request: "Prose can refute"

Captured: 2026-08-01, from the operator's message immediately following the
report closing `experiments/2026-08-01-fix-adjudication-blindness/` (commit
`7586a8c8`), in which I stated that `authority.py:97-101` hard-returns
`OBSERVE_ONLY` for every text workload and named the decision as theirs to make.

## Verbatim

> Who the hell made that decision. That's so unbelievably stupid. Get rid of
> that requirement. Prose can refute. the endpoint that wants to refute just
> needs access to the full argument. It's only formal claims in formal prose
> that require formal refutation.

## Requirements

R1 (behavior): "Get rid of that requirement."

R2 (behavior): "Prose can refute."

R3 (behavior): "the endpoint that wants to refute just needs access to the
full argument."

R4 (behavior): "It's only formal claims in formal prose that require formal
refutation."

## Standing constraints

C1: "Never touch run-root records or replay validation." — operator, standing,
earlier this session.

C2: "the full gate must end 0 failed" — operator, standing, earlier this
session. Restated in CLAUDE.md: "Gate discipline: 0 failed is the only
acceptable result. Never weaken an assertion to get green."

C3: "The append-only record itself: fix READERS so old roots stay valid; a
change that invalidates existing replay-valid roots is wrong by definition."
— CLAUDE.md, Frozen surfaces.

C4: "Don't ask permission unless what you're doing is out of scope" /
"stop asking permission unless it's out of scope" — operator, standing, twice
this session.

C5: "Route ALL substantive work through one of them" (the two skill families)
— CLAUDE.md. The operator enforced this directly this session: "Why are you not
following the skills in Claude.md".

## Context (NOT requirements — recorded so dr-spec-change does not re-derive it)

- `src/deepreason/authority.py`, `trial_authority_for`, computes
  `mode = text_authority_mode(config, surface)` and then unconditionally
  returns `TrialAuthority.OBSERVE_ONLY` for every text workload. The computed
  `mode` is discarded.
- That code came from the operator's own commit `83509657` (2026-07-14),
  "Make informal text adjudication advisory by default", whose message says
  "advisory by default" and "Direct helper status modes and legacy v1 routes
  remain explicit compatibility escape hatches". The implementation is
  unconditional where the message describes a default.
- Measured this session: no text run can mint a warrant, so no attack edge can
  exist. 26 of 42 recorded roots executed criticism and produced zero attacks,
  with every artifact vacuously ACCEPTED.
- The immediately preceding tranche (`7586a8c8`) added an epistemic finding
  that only REPORTS this state. It deliberately changed nothing about what a
  run is permitted to do.
- Evidence: `experiments/live_jolt_2026-07-31/INVESTIGATION.md`,
  `experiments/2026-08-01-fix-adjudication-blindness/VERIFY.md`.

## Open questions (for dr-spec-change)

Q1 (R1): "that requirement" is deictic. The nearest referent in my report was
the `OBSERVE_ONLY` hard-return in `authority.py:97-101`. But the same function
also refuses `calibrated_status` "until a receipt verifier exists", and
`text_authority_mode` distinguishes prose / rubric / infrastructure-review /
pairwise surfaces. Does R1 remove the hard-return only, or also the
calibration-receipt precondition?

Q2 (R2): "Prose can refute" — does a prose criticism mint a warrant and drive
`Status.REFUTED` through the ordinary attack-edge path, or a distinct
prose-warrant kind that adjudication treats differently?

Q3 (R3): "access to the full argument" is not yet a defined context object.
Which existing pack or exposure is "the full argument" — the target artifact's
content alone, its support chain, the criticism thread, or the whole problem
context? This determines whether R3 is a prompt/pack change or a new capability.

Q4 (R4): "formal claims in formal prose" — the codebase's nearest existing
distinction is `programs.evaluable(commitment)` (program/observation evals vs
rubric). Is R4 that distinction, or a new one about the claim's own text?

Q5 (scope): R1-R4 are stated for the refutation direction. Do they apply
symmetrically to prose ACCEPTANCE — can prose also accept, or only attack?

Q6 (C3 interaction): 26 committed roots were written under `OBSERVE_ONLY`.
Changing what future runs may do must not change how those roots verify. Is any
part of R1-R4 expected to apply retroactively to their interpretation?

## Amendments

(append-only)

### 2026-08-01, message 2 — during dr-spec-change, before any code was written

> Read claude.md again. The scratchpad authority chain needs to be completely
> separate from conjecture/criticism adjudication. They shouldn't exist
> together.

R5 (behavior): "The scratchpad authority chain needs to be completely separate
from conjecture/criticism adjudication."

R6 (behavior): "They shouldn't exist together."

**R5/R6 CLOSE Q3 in the negative.** Q3 asked what "access to the full argument"
(R3) denotes, and I had established that `rules/crit.py` never receives scratch
context — only `rules/conj.py` renders it (`conj.py:1368`) — and was heading
toward exposing scratch to the critic as the reading of R3. R5/R6 rule that
out. Whatever satisfies R3, it is NOT piping the scratchpad into criticism.

Q3 is therefore re-opened in a narrower form and recorded as Q3a below.

R5/R6 also RESTATE an existing boundary rather than inventing one:
`scratch/proposals.py` sets `SCRATCH_EPISTEMIC_BOUNDARY = "advisory_non_grounding"`
and the workshop prompt says "storage alone never makes it a fact, evidence, a
formal claim, or support for one". The operator is affirming and strengthening
that separation at the AUTHORITY-CHAIN level, not only at the grounding level.

Q3a (supersedes Q3): if the scratchpad is excluded, what IS "the full argument"
the refuting endpoint must be given? Candidates visible in the code: the target
artifact's content alone (today's `render_crit_pack`), plus its support chain,
plus the prior criticism thread on that target. None of these is the scratchpad.

C6 (process): "Read claude.md again." — operator, message 2. CLAUDE.md re-read
in full before this amendment was written. The governing line for this
situation: "Cross-routing: a defect found mid-change is PARKED, not fixed; a
change wished for mid-defect is PARKED, not implemented. One tranche, one goal."
