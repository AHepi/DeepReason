# Request: adjudication / judge-seats / legacy-criticism opt-ins; seat-assignment archaeology
Captured: 2026-08-09 from the operator's session-start task message (routed through
dr-change-orchestrator, spec-and-stop)

## Verbatim

> Ok here's what needs working on because I think it's been causing problems.
> Adjudication: Opt in. Judge seats: opt in. Optional legacy criticism paths:
> opt in. Right now, only two seats are assignable. I need to know why they
> were disconnected, why they wouldn't work now.

The task issuer additionally structured this window as SPEC-AND-STOP (no code
this window) with two deliverable halves. This structuring is the task
issuer's elaboration of HOW to satisfy the operator's words, not new operator
authority — captured here as C4/C5 (process constraints) rather than as a
requirement, per dr-capture-request's rule that only the operator's own words
generate R-numbers.

> This is SPEC-AND-STOP: capture, then a measurement-heavy SPEC.md, no code
> this window.

> Half 1 — the WHY, answered from record and tree, every claim with a pasted
> pointer. (a) The assignable-seat census as of today: seat_bindings.py::
> GROUP_ROLES, the alias table, the conflict rule, and which groups can
> actually fire in a live run with dual-mode off — reconcile with S6's
> dead-seat finding and the omnibus's parked no-critic-group gap. (b) The
> design archaeology: WHY the vocabulary is what it is — trace Rung S2's SPEC
> and the ROLE_SEAT_SEPARATION_PLAN's own scoping words; establish whether
> critic/judge seats were deliberately excluded (cite the words) or never
> considered. (c) The structural reconciliation problem: how
> argumentative_critic is actually routed today (manifest
> criticism_policy.bindings, school-keyed — paste a real manifest's bindings
> block), how judges are routed and gated (require_cross_family_judges,
> family-counting), and precisely what breaks or becomes ambiguous if seats
> rerouted these roles — the foreign-school coverage semantics, school
> identity, family gates — each named as a concrete conflict with file/line,
> not hand-waved. This answers "why they wouldn't work now" categorically.

> Half 2 — the opt-in redesign SPEC. Design the three opt-ins the operator
> names, each with today's actual default measured first: adjudication
> opt-in (status-changing criticism — currently observe_only by default, so
> ALREADY effectively opt-in; specify the explicit, typed opt-in surface and
> what opting in requires per the solo law — no configuration may strand
> solo runs); judge seats opt-in (judges never spend a token unless
> explicitly enabled — reconcile with the cross-family gate and the
> judge-suspicion law: opting in must surface the judge-audit evidence
> warning); legacy criticism paths opt-in (identify what "optional legacy
> criticism paths" exist — the executor enumerates candidates from the
> criticism dispatch census (D1's M6-M9) and the authority-mode map, labels
> each legacy-vs-current with evidence, and specifies the opt-in flag
> surface for each). Every opt-in: mint-time frozen into the manifest (the
> placement law), default = today's behavior byte-identical, R-g
> kind-blindness stated. Frozen-surface forecast from scratch (expect
> run_manifest.py adjacency — name it, authorize nothing). Decision sheet:
> every fork priced as roads with recommendations, including whether a
> critic/judge SEAT vocabulary should exist at all given Half 1's findings,
> or whether school/family routing subsumes it. Commit and push REQUEST.md
> and SPEC.md, then STOP for operator words.

## Requirements

R1 (behavior/artifact): "Adjudication: Opt in." — an explicit, typed opt-in
surface for status-changing criticism (adjudication) must be specified.

R2 (behavior/artifact): "Judge seats: opt in." — an explicit, typed opt-in
surface for judge seats must be specified, such that judges never spend a
token unless explicitly enabled.

R3 (behavior/artifact): "Optional legacy criticism paths: opt in." — legacy
criticism paths must be identified and given an explicit opt-in flag surface.

R4 (artifact): "Right now, only two seats are assignable. I need to know why
they were disconnected, why they wouldn't work now." — a WHY-archaeology
deliverable is required: the seat census, the design history of why
critic/judge seats are or are not assignable, and the concrete structural
conflicts that would arise from rerouting `argumentative_critic`/`judge`
through the seat mechanism.

## Standing constraints

C1: "This is SPEC-AND-STOP: capture, then a measurement-heavy SPEC.md, no
code this window." — task issuer's framing of this window's scope.

C2: "Every claim with a pasted pointer" (Half 1) — every WHY-archaeology
claim must carry a file/line or record pointer, not a paraphrase.

C3: "Every opt-in: mint-time frozen into the manifest (the placement law),
default = today's behavior byte-identical, R-g kind-blindness stated." —
design constraints on Half 2's opt-in surfaces, tracing to CLAUDE.md's
frozen-surfaces law, the "no configuration may strand solo runs" operator
design law, and the R-g formalism-is-never-an-obligation law.

C4 (process, task issuer's framing, not operator words): produce REQUEST.md
then SPEC.md this window; no CHECKLIST.md, no code.

C5 (process, task issuer's framing): "Commit and push REQUEST.md and SPEC.md,
then STOP for operator words." — end this window after SPEC.md is pushed;
do not proceed to dr-plan-steps.

## Open questions (for dr-spec-change)

Q1: Does "opt in" for all three (adjudication, judge seats, legacy criticism)
mean a single unified opt-in surface, or three independently toggleable
flags? The operator lists them as three separate sentences — dr-spec-change
should record the smallest-reasonable-interpretation assumption (three
independent flags) unless the record shows otherwise.

Q2: Is "the two assignable seats" the operator refers to `seat_bindings.py`'s
`GROUP_ROLES` groups (`conjecture`/`coder`/`scratch`/`simulation`-alias) as
they exist today, or a claim about a different, now-obsolete seat surface?
This must be resolved from the record (Half 1(a)) before Half 2 can specify
opt-ins that add a critic/judge seat group, if that is even the right
design — Half 1(b)/(c) findings will decide whether a SEAT vocabulary for
critic/judge is the right shape at all, per the task issuer's own decision
sheet requirement.

Q3: "Legacy criticism paths" — the operator does not name specific paths;
the task issuer directs the executor to enumerate candidates from D1's
criticism dispatch census (M6-M9) and the authority-mode map. This is
research, not an operator specification, and must be presented as findings
with evidence, not assumed.

## Amendments

### Amendment 1 (2026-08-09, mid-workflow, operator's own words)

> Yeah schools need to be opt in seats as well. The judge adjudication is
> meant to settle disputes. That's why they exist. Two conjectures that
> contradict each other, two attack edges drawn, no grounded extension can
> rule them out. The judge steps in. It doesn't need to be active, but we
> have configuration machinery to starve the judge if it's becoming too
> zealous. There's also an additional function that checks the config,
> figures out whether it's latest adjustments actually diagnose the problem
> properly, and sends out a config recommendation. The signals all exist for
> that reason. If these functions are dead and the signals are dead, then
> the workflow needs a makeover.

The task issuer's own message framed the binding scope consequences of this
amendment as follows (captured verbatim as elaboration, not new operator
authority, per the same rule applied to the original capture):

> Scope consequences, binding: (1) Schools join Half 2 as opt-in seat
> surfaces — measure how school identity is minted and bound today (the
> manifest's school-keyed criticism bindings from Half 1(c)) and spec what
> "school as an assignable, opt-in seat" means without breaking
> foreign-school coverage semantics — if binding schools to models changes
> what "foreign" counts, that consequence is priced explicitly, never
> absorbed silently. (2) The judge's design target in Half 2 is now the
> operator's own definition: dormant by default; SUMMONED only for
> grounded-undecidable standoffs (mutual/symmetric attack structures — the
> even-cycle inventory the O1a overlay scripts already compute is the
> summoning condition's measurement basis); ruling through the existing
> pairwise/trial guard machinery, never as an open-ended prosecutor; and
> STARVABLE — spec the throttle explicitly (budget/rate config that caps
> judge activity). (3) A liveness census joins Half 1, same discipline as
> the property_designer diagnosis (categorical, file/line, record evidence
> — a dispatch site that exists but is unreachable is DEAD): (a)
> config_referee — every dispatch site, every precondition, whether ANY
> committed root shows it firing; (b) the judge-starving configuration
> machinery the operator names — find it, or establish it does not exist;
> (c) the steering/config-recommendation signals (llm/budget.py and
> neighbors) — which are produced, which are consumed, and by what; a
> signal produced but never consumed is DEAD. (4) The conditional the
> operator set: if the liveness census finds these functions/signals dead,
> SPEC.md's decision sheet must include the workflow-makeover road — scoped
> as its own follow-up program with a rung sketch, priced, not designed in
> full here. Everything else stands: SPEC-AND-STOP, frozen forecast from
> scratch, defaults byte-identical, decision sheet with recommendations.
> Commit and push, STOP for operator words.

### New/superseding requirements from Amendment 1

R5 (behavior/artifact): "schools need to be opt in seats as well" —
supersedes nothing, adds a fourth opt-in seat surface (schools) alongside
R1-R3's three opt-ins, to be specified in Half 2 with today's actual
school-identity-minting/binding mechanism measured first.

R6 (artifact): "The judge adjudication is meant to settle disputes... The
judge steps in [on] two conjectures that contradict each other, two attack
edges drawn, no grounded extension can rule them out... It doesn't need to
be active" — the judge seats opt-in design (R2) must target this
operator-defined shape: dormant by default, summoned only for
grounded-undecidable standoffs, ruling through existing
pairwise/trial-guard machinery.

R7 (artifact): "we have configuration machinery to starve the judge if it's
becoming too zealous" — a claim to verify: find this machinery (file/line)
or establish it does not exist, as part of the liveness census.

R8 (artifact): "There's also an additional function that checks the config,
figures out whether it's latest adjustments actually diagnose the problem
properly, and sends out a config recommendation. The signals all exist for
that reason." — a second claim to verify: find this function/signal chain
(file/line) or establish it does not exist, as part of the liveness census.

R9 (process/artifact): "If these functions are dead and the signals are
dead, then the workflow needs a makeover." — conditional: IF the liveness
census (R7, R8, plus config_referee per the task issuer's framing) finds
these dead, SPEC.md's decision sheet must include a workflow-makeover road,
scoped as a priced follow-up program with a rung sketch — not designed in
full this window.

### Standing constraints added by Amendment 1

C6: "if binding schools to models changes what 'foreign' counts, that
consequence is priced explicitly, never absorbed silently" — task issuer's
framing of R5's acceptance bar.

C7: "STARVABLE — spec the throttle explicitly (budget/rate config that caps
judge activity)" — task issuer's framing of R6's acceptance bar.

C8: "a dispatch site that exists but is unreachable is DEAD" — task
issuer's framing of the liveness-census discipline (R7/R8/config_referee),
matching the already-established property_designer/S6 precedent from Half
1(a).

C9: "Everything else stands: SPEC-AND-STOP, frozen forecast from scratch,
defaults byte-identical, decision sheet with recommendations. Commit and
push, STOP for operator words." — reaffirms C1-C5 unchanged.

### Amendment 2 (2026-08-09, mid-workflow, operator's own words, "standing words for tonight")

> Standing words for tonight, ledger as an amendment: for any budget-overrun
> stop in this tranche, the answer is "continue, report the final total at
> delivery" — pre-authorized now. For any genuine design fork that would
> otherwise stop mid-flight: do not wait; record every road priced in the
> decision sheet, take no road, and continue to the SPEC-AND-STOP endpoint.
> The only valid stop is the final one.

### New standing constraints from Amendment 2

C10 (process, pre-authorization, scoped "for tonight"/this tranche): a
budget-overrun stop condition in this tranche is pre-answered — continue
the work, and report the actual final total (tokens/diff/whatever the
overrun metric is) at delivery rather than stopping to ask.

C11 (process, pre-authorization, scoped to this tranche): a genuine design
fork that would otherwise be a mid-flight stop-and-ask is NOT to be asked
mid-flight in this tranche — instead, price every road in SPEC.md's
decision sheet, select none of them (no silent pick), and continue to the
SPEC-AND-STOP endpoint (SPEC.md committed and pushed). This narrows, for
this tranche only, the change-orchestrator's normal "stop conditions"
list (estimated diff exceeds budget; a fork the operator must decide) —
both collapse into "keep going, ledger it, decide nothing unilaterally,
surface it in the decision sheet."

C12 (process): "The only valid stop is the final one." — no intermediate
STOP this window; the SPEC-AND-STOP endpoint (SPEC.md pushed, per C5) is
the sole stop point for this tranche.

### Amendment 3 (2026-08-09, post-STOP clarifying questions, operator's own words)

> Starving the judge should be something that's doable in config. There
> should be built in signals to detect active judges as well. Also, single
> model two judge seats should be possible. Is none of this possible?

Sent after SPEC.md was committed, pushed, and reported at the SPEC-AND-STOP
endpoint (C12). Read as clarifying questions plus a statement of intent for
the already-priced judge-seats design (§2b), not as a new implementation
directive — no code follows from this amendment; it sharpens Half 1/Half 2
with three additional measured findings, captured as a SPEC.md addendum.

R10 (artifact, refines R6/C7): "Starving the judge should be something
that's doable in config." — confirms the direction of §2(b)'s throttle
fields; no new requirement, a validation of the existing design.

R11 (artifact, refines R7/R9): "There should be built in signals to detect
active judges as well." — a claim to verify against the record: do such
signals exist, live or dead, generic-rate or quality-specific?

R12 (artifact, new): "single model two judge seats should be possible." —
a claim to verify: is a genuinely single-model run with two judge seats
(same model in both, independence carried by school rather than family)
reachable through any code path today?

### Amendment 4 (2026-08-09, post-STOP clarifying question, operator's own words)

> Can you trace the code for criticism before schools? Because it exists.
> And the circuit can be switched back on if schools are unwanted.

R13 (artifact, new): a claim to verify and trace: does a pre-school,
non-school-routed criticism dispatch path still exist in the code, and if
so, can it be reactivated as the school-free criticism circuit when
"schools: opt-in" is turned off?
