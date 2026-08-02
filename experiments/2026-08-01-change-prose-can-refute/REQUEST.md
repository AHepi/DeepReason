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

### 2026-08-01, message 3 — answering SPEC.md's Q-A and opening a new line

> Ok. So keep the current path. But add an experimental path for same school
> criticisms. Leverage the schools architecture to create and mint criticisms.
> They key is that stateless endpoints don't have access to who created the
> conjecture artifact. Before figuring out how adjudication might work, you
> need to figure out what actually exists. Return with feasibility and risks.
> Your report must be returned without technical terms. Use subagents

**ANSWER to SPEC.md Q-A: reading (a).** "keep the current path" — the defended
cross-family trial stays. No self-certifying prose warrant. S1-S6 stand as
specified under (a). Q-B is therefore moot (the calibration-receipt
precondition is untouched under (a)); Q-C stays assumed attack-only.

R7 (behavior): "add an experimental path for same school criticisms."

R8 (behavior): "Leverage the schools architecture to create and mint
criticisms."

R9 (context/constraint): "They key is that stateless endpoints don't have
access to who created the conjecture artifact."

R10 (process): "Before figuring out how adjudication might work, you need to
figure out what actually exists. Return with feasibility and risks."

R11 (artifact): "Your report must be returned without technical terms."

R12 (process): "Use subagents"

**R10 GATES R7/R8.** No design and no adjudication scheme may be produced until
a feasibility report on what EXISTS is returned. This supersedes the normal
route from SPEC.md to dr-plan-steps for R7/R8 only; R1-R6 under reading (a) are
unaffected and remain specified.

C7 (process): "Your report must be returned without technical terms." — the
deliverable for R10 is prose, not a code map.

### 2026-08-01, message 4 — answering the feasibility report

> The second, obviously. I want this designed for single family runs. Also, as
> long as a critic isn't from the same school, it's fine. So build this
> architecture, but only make it active if a single model is running the entire
> harness. The architecture to distinguish between single and many should
> already exist. Read claude.md before running. Do not ask for permission to do
> anything unless it is out of scope.

**ANSWER to the feasibility report's blocking question: the second reading.**
Dispatch an author-side critic WITHOUT telling the model who wrote the target.
Nothing new is shown at the model boundary. This is the low-risk option the
report identified.

R13 (behavior): "I want this designed for single family runs."

R14 (behavior): "as long as a critic isn't from the same school, it's fine."

R15 (behavior): "only make it active if a single model is running the entire
harness."

R16 (context): "The architecture to distinguish between single and many should
already exist."

R17 (process): "Read claude.md before running." — done, in full, before this
amendment.

C8 (process): "Do not ask for permission to do anything unless it is out of
scope."

## APPARENT CONTRADICTION: R7 vs R14 — recorded, not silently resolved

R7 asked for "same school criticisms". R14 says "as long as a critic isn't from
the same school, it's fine". Read literally these are opposites, and the skill
forbids picking a side silently.

**Reading carried forward (state it, proceed under it, correct on operator
word):** R14 supersedes the literal sense of R7. The thing R7 was reaching for
is criticism that works INSIDE ONE MODEL FAMILY; the independence guarantee is
cross-SCHOOL, not cross-family.

Why this reading and not the literal one:
  - The report established that prose can never mint a defeat today because the
    path requires a defended trial across two DISTINCT MODEL FAMILIES
    (`llm/firewall.py:79`, "two frozen judge seats from distinct route
    families"). A single-family run can never satisfy that. That is exactly the
    blocker R13/R15 name.
  - R14 then supplies the substitute guarantee: cross-school independence
    standing in for cross-family independence, but only where cross-family is
    unavailable (R15).
  - Under the literal reading of R7, R14 would forbid the very thing R7 asks
    for, and R15's single-model gate would be pointless.
  - It also answers the report's worst finding: a school criticising its own
    work is marking its own homework, and this repository's own pre-registered
    study shows removing shared context does not buy independence. R14 avoids
    that failure entirely.

R7 is therefore marked `superseded-by:R14` for its literal sense, and retained
for its intent: use the schools architecture as the vehicle.

R16 CONFIRMED against the codebase before proceeding: `require_distinct_families`
exists as a policy flag (`v6_policy.py:69,119`, currently False),
`V4_SCHOOL_DISTINCT_FAMILY_REQUIRED` exists (`run_manifest.py:2704-2707`), and
`require_cross_family_judge_ensemble` exists (`llm/firewall.py:261`). The
distinction the operator expected does exist.

### 2026-08-02, message 5 — answering the delivery report

> you didn't listen. I didn't ask for same school criticism. It should be cross
> school  criticism. It should only work for single model runs. it should be
> exposed whenever a single model is occupying all positions

R18 (behavior): "It should be cross school  criticism."

R19 (behavior): "It should only work for single model runs."

R20 (behavior): "it should be exposed whenever a single model is occupying all
positions."

C9 (process): "you didn't listen. I didn't ask for same school criticism." —
the operator states that a settled decision was re-opened.

**R18 CONFIRMS A4 and CLOSES it.** A4 recorded, as an assumption the operator
could overturn in one word, that R14 supersedes R7's literal "same school
criticisms" and that the guarantee is cross-SCHOOL. R18 states that reading
back. A4 is therefore SETTLED, not assumed: cross-school is what was asked for
and cross-school is what was built. `S8`/`S9` do NOT invert.

**What C9 names.** The delivery report raised A4 to the operator as a live
question ("if you actually meant same-school, S8 and S9 invert and the extension
needs rebuilding") when the operator had already decided it in message 4 ("as
long as a critic isn't from the same school, it's fine"). Re-opening a settled
decision is the failure being reported. Recorded here so the delivery phase does
not repeat it: a recorded assumption that the operator has since confirmed is
CLOSED, and must be reported as a fact, not re-surfaced as a choice.

**R20 is the substantive change, and it is NOT satisfied by what was built.**
The cross-school ensemble is currently opt-in: `LLMAdapter.__init__` takes
`school_judge_bindings` defaulting to `()`, and `llm/adapter.py:1467` — the only
production construction of an adapter — never passes it. `_select_judge_ensemble`
therefore falls back to cross-family in every live run.
`VALIDATION.md` and `PARKED.md` both record this as unwired, and the delivery
report stated it as parked residue. R20 says it must be EXPOSED whenever a
single model occupies all positions. Opt-in that nothing opts into is not
exposed.

## Open questions (from message 5, for dr-spec-change)

Q7 (R19, R20 vs A5): **"single model" or "single family"?** Message 4 said "I
want this designed for single family runs" and "only make it active if a single
model is running the entire harness", and A5 read the latter as ONE ROUTE
FAMILY across the run's leases — explicitly not one model id and not one seat.
Message 5 says "single model runs" and "a single model is occupying all
positions", twice, and does not say family. This may mean the predicate should
key on model IDENTITY rather than family, which is strictly narrower: two
different glm models share a family but are not one model. `is_single_family_run`
implements the family reading today. NOT resolved here.

Q8 (R20): "exposed" — does the cross-school ensemble become the gate
automatically in a qualifying run with no configuration at all, or does it
become AVAILABLE and something in the run's own configuration still selects it?
The word "exposed" admits both. NOT resolved here.

Q9 (R20): if it is automatic, where do the judge seats' SCHOOL identities come
from? Nothing binds a school to a judge seat today: `SchoolRoleBindingV1` can
express one (`run_manifest.py:467`, its `role` field is an open pattern) but no
manifest authors one. NOT resolved here.

### 2026-08-02, message 6 — answering VALIDATION.md's FAIL

> they are both formal. I have a feeling a conjecture endpoint might not fill
> out the form properly for this distinction.

R21 (behavior): "they are both formal."

R22 (context/risk): "I have a feeling a conjecture endpoint might not fill out
the form properly for this distinction."

**R21 ANSWERS VALIDATION.md's FAIL, and answers it as reading (b).** The FAIL
asked whether R4's "formal claims" means `execution_backed` (exec-oracle
commitments only) or `programs.evaluable` (`predicate:` and known `program:`).
"They are both formal" selects the wider set: a `predicate:` commitment is a
formal claim, and so is a `program:` one. The prose-immunity line therefore
moves from `execution_backed` to the evaluable set. S4's first acceptance
clause becomes the thing to implement rather than the thing that failed.

**R22 is a warning about the mechanism R21 selects, and it is not a
side-remark.** The set of commitments an artifact carries is DECLARED BY THE
CONJECTURING ENDPOINT in its own output (`Interface.commitments`). R21 makes
that declaration decide whether the artifact is immune to prose criticism. R22
says the endpoint may not fill the form properly for this distinction. Recorded
here as the operator stated it; what follows from it is dr-spec-change's job,
not this phase's.

## Open questions (from message 6, for dr-spec-change)

Q10 (R21+R22): if a declared evaluable commitment confers prose immunity, what
stops an endpoint — by carelessness or otherwise — from declaring a cheap or
trivially-satisfied formal commitment and thereby immunising its own artifact
against criticism? R2 says "Prose can refute"; a self-conferred immunity would
take that back. NOT resolved here.

Q11 (R22): "not fill out the form properly" runs in both directions —
under-declaring (a formal claim carried as `rubric:`, so it gets no formal
protection) and over-declaring (a substantive prose claim carried with a formal
commitment, so it gets protection it should not have). Which direction the
operator means, or both, is not stated. NOT resolved here.

Q12 (R21): `execution_backed` also requires every exec commitment to currently
PASS — a failing one earns no protection, because execution already refutes it.
Does the widened line keep that "and all currently pass" clause? NOT resolved
here.

## RESOLVED — VALIDATION.md's FAIL is answered by message 6

The validation verdict was FAIL on S4's first acceptance clause: A1 named
`programs.evaluable` as the formal/informal line, the implemented line is
`execution_backed`, and a target carrying a `predicate:` commitment is therefore
refutable by prose (measured: `att=1`, not refused). Message 5 concerned the
schools/single-model axis only and left it open. **Message 6 answers it: "they
are both formal" — reading (b), the wider set.** See R21 above.

