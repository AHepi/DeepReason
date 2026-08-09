# Request: judge-evidence review — read-only archaeology over committed runs
Captured: 2026-08-09 from the executor task assignment (operator's suggestion,
routed to this session as the tranche brief)

Map preflight (recorded per dr-change-orchestrator, before REQUEST.md is
acted on): `docs/map/INDEX.md` → `INV-frozen-surfaces.md` →
`SUB-adjudication.md`, `SUB-evaluation.md`. Resolved ids for this tranche:
`DR-SUB-evaluation` (owns `informal/audits.py`, `informal/trial.py`,
`programs.py`, `oracle.py`, `measures/`), `DR-SUB-adjudication` (status
semantics judge rulings must pass through as warrants), `DR-CON-authority`
(the `observe_only`/`status` decision at trial time), `DR-CON-schools`
(cross-school judge substitute guarantee). This tranche is READ-ONLY: no
surface in `INV-frozen-surfaces.md` is touched, and the map itself is not
expected to change (no new behavior, no new check) unless the sweep finds a
document gap worth noting.

## Verbatim

> You are the executor for the judge-evidence review — a READ-ONLY
> archaeology tranche over the committed record. No code, no live calls, no
> new runs; your deliverable is a review document. Route through
> dr-change-orchestrator from dr-capture-request; the operator's verbatim
> words, the authority:
>
> Turning on judges at all should be done with caution. I would prefer to do
> without, since they prosecute without any discernable discrimination.
> There have been trials done previously that prove this exact point. I
> think a review of long since redundant runs is in order. Particularly the
> ones that cover testing judges.
>
> Your job is to make the record answer: what do the committed runs and
> experiments actually prove about LLM-judge discrimination? The operator's
> claim is a HYPOTHESIS to verify, not a conclusion to decorate — if the
> record supports it, show the numbers; if it contradicts or only partially
> supports it, say so with equal prominence. Sweep, at minimum: the judge
> audit machinery and its outputs (deepreason report's planted-flaw /
> self-preference / verbosity audits — find every committed root or results
> file carrying their numbers, including experiments/results/), the
> trial-protocol experiments (the prose-can-refute tranche, informal/trial.py's
> guard design and any committed roots where trials actually ran —
> order-swap consistency, paraphrase-flip, ensemble-agreement rates), the
> adjudication-blindness fix tranche (2026-08-01), the stress-triplet and
> any lambda/experiment-module runs with judge involvement, and
> EXPERIMENT_PROGRAM_2026-07.md's own judge items. For every claim: the
> root/file pointer and the number, pasted. Distinguish three things the
> operator's phrase could mean, and score each separately from evidence:
> (a) judges rule incorrectly (planted-flaw error rates), (b) judges rule
> without discrimination (pass/fail rates insensitive to case quality —
> flip rates under paraphrase/order-swap), (c) judges over-prosecute
> (fail-rate bias vs ground truth). Close with the design consequence
> section the new CLAUDE.md law requires: given the measured evidence, what
> would a judge-free or judge-minimal road to status-changing criticism in
> SOLO runs have to look like — enumerate the candidate mechanisms already
> in the tree (program/predicate commitments refute mechanically with no
> judge; counterexample execution; the trial guard's non-judge program
> checks — referential integrity, order-swap — as standalone screens) and
> what each can and cannot adjudicate, priced, recommendations included,
> decisions not made. Deliverable: REVIEW.md in the tranche + RESULTS.md
> honest ledger; deliver through dr-validate-change/dr-deliver-change; full
> gate once at the boundary (read-only tranche — prove it: tripwire diff
> pasted empty). Commit and push each phase boundary. Stop when delivered.

> Setup FIRST: git fetch origin main && git checkout -B claude/<your-branch-name>
> origin/main, verify git merge-base --is-ancestor b5921b3a HEAD succeeds,
> preflight (which deepreason || pip install -e . --break-system-packages
> -q; pip install pytest pytest-xdist jsonschema --break-system-packages
> -q). THEN read CLAUDE.md (the new "solo run with everything on" law is
> this tranche's origin), .claude/skills/dr-explain-to-operator/SKILL.md
> (Read tool, follow for every message), .claude/skills/README.md.

## Requirements

R1 (artifact): "your deliverable is a review document" — produce REVIEW.md
answering "what do the committed runs and experiments actually prove about
LLM-judge discrimination?"

R2 (process): "READ-ONLY archaeology tranche over the committed record. No
code, no live calls, no new runs."

R3 (process): "Route through dr-change-orchestrator from dr-capture-request"
— follow the full change-workflow phase sequence.

R4 (behavior): "The operator's claim is a HYPOTHESIS to verify, not a
conclusion to decorate — if the record supports it, show the numbers; if
it contradicts or only partially supports it, say so with equal
prominence."

R5 (behavior): sweep, at minimum, five named areas:
  R5a: "the judge audit machinery and its outputs (deepreason report's
  planted-flaw / self-preference / verbosity audits — find every committed
  root or results file carrying their numbers, including
  experiments/results/)"
  R5b: "the trial-protocol experiments (the prose-can-refute tranche,
  informal/trial.py's guard design and any committed roots where trials
  actually ran — order-swap consistency, paraphrase-flip, ensemble-agreement
  rates)"
  R5c: "the adjudication-blindness fix tranche (2026-08-01)"
  R5d: "the stress-triplet and any lambda/experiment-module runs with judge
  involvement"
  R5e: "EXPERIMENT_PROGRAM_2026-07.md's own judge items"

R6 (behavior): "For every claim: the root/file pointer and the number,
pasted."

R7 (behavior): "Distinguish three things the operator's phrase could mean,
and score each separately from evidence: (a) judges rule incorrectly
(planted-flaw error rates), (b) judges rule without discrimination
(pass/fail rates insensitive to case quality — flip rates under
paraphrase/order-swap), (c) judges over-prosecute (fail-rate bias vs ground
truth)."

R8 (artifact): "Close with the design consequence section the new
CLAUDE.md law requires: given the measured evidence, what would a
judge-free or judge-minimal road to status-changing criticism in SOLO runs
have to look like — enumerate the candidate mechanisms already in the tree
(program/predicate commitments refute mechanically with no judge;
counterexample execution; the trial guard's non-judge program checks —
referential integrity, order-swap — as standalone screens) and what each
can and cannot adjudicate, priced, recommendations included, decisions not
made."

R9 (artifact): "Deliverable: REVIEW.md in the tranche + RESULTS.md honest
ledger"

R10 (process): "deliver through dr-validate-change/dr-deliver-change"

R11 (process): "full gate once at the boundary (read-only tranche — prove
it: tripwire diff pasted empty)"

R12 (process): "Commit and push each phase boundary."

R13 (process): "Stop when delivered."

## Standing constraints

C1: "No code, no live calls, no new runs" — R2. No production code, no
`deepreason` CLI invocations that start a run, no new experiment roots.
C2: "tripwire diff pasted empty" — the diff against `src/deepreason/` (and
any other production surface) must be empty at validation; VALIDATION.md
must paste this proof.
C3 (from CLAUDE.md, cited by the brief as this tranche's origin): "A solo
run with everything on should be an option... However, turning on judges
at all should be done with caution. I would prefer to do without, since
they prosecute without any discernable discrimination." — this is the
hypothesis under test (R4), not an instruction to conclude judges are bad.
C4 (from CLAUDE.md): "judge seats are suspect-by-default: any design
leaning on LLM judges must first consult the judge-audit evidence in the
committed record (see the judge-evidence review tranche) rather than
assume judges discriminate" — this tranche IS that consultation; its
output should be citable by that future design work.
C5: gate discipline from CLAUDE.md applies to the one full-gate run at the
boundary — "0 failed is the only acceptable result" — but this tranche
makes no code change, so 0 failed is expected trivially; the gate run here
is a tripwire, not a target of iteration.

## Open questions (for dr-spec-change)

Q1: "long since redundant runs" — does this mean the sweep should also
identify and recommend retiring specific stale run roots, or only read
them as evidence? (R5 lists sweep targets but the deliverable list, R9,
names only REVIEW.md + RESULTS.md — no retirement action.)
Q2: Scope of "committed record" — experiments/ tracked in git only, or also
any gitignored/local roots this session's container currently holds? (R2's
"no new runs" plus C1 suggest committed/git-tracked only; gitignored roots
would not survive container rollback and are not "the committed record".)
Q3: Depth of "priced" in R8's design-consequence section — operator design
laws in CLAUDE.md ("Tokens are cheap; the agent is not") suggest pricing in
agent/implementation effort and live-run token cost, not a literal dollar
figure; smallest reasonable interpretation recorded here, confirmed in
SPEC.md.

## Amendments

(none yet)
