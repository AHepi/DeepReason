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

### Amendment 5 (2026-08-09, operator's own words, "the spec is APPROVED on this basis")

> Let's do it. And I think I'm going to bench the mid run gate flips for
> now since it's not necessary for modes. But abstracting signals is still
> a helpful move since historical runs have proven that dynamic behaviour
> can be helpful.
>
> Binding readings, confirmed by the monitor: every decision-sheet
> recommendation is approved as written — 5.1 Road A (mint-time), 5.2 Road
> A (judge opt-in surface ships first; the standoff-summons wiring is its
> own later tranche), 5.3 Road A (no calibrated_status verifier), 5.4 Road
> A with Road B as the named follow-up, 5.5 Road B (no new critic/judge
> seat vocabulary — existing school/family levers only), and Road E folded
> into the legacy-criticism opt-in as its concrete surface. The benching
> amendment scopes the whole tranche: every gate in this implementation is
> STATIC and mint-time frozen — no dynamic flip machinery, no mid-run
> signal consumption, nothing that changes behavior after compile. Signal
> abstraction stays IN scope in its static form: the liveness census's
> confirmed-live signals (config-critique verdicts, gate-block/convergence
> counts, and peers) get a uniform typed read surface consumable at run
> boundaries (report/audit/operator), so future packages read one shape
> instead of scraping logs — but nothing consumes them mid-run to change
> anything. docs/proposals/GATES_AND_PACKAGES_PREPLAN.md (now on main,
> Stage 2 marked BENCHED) records this staging; cite it.
>
> Proceed to dr-plan-steps: convert the approved SPEC plus this amendment
> into CHECKLIST.md. Ordering requirement: Road E first — the v6
> transaction contract for the school-free argumentative-criticism phase is
> the smallest change with the largest decoupling, and everything else
> layers on a tree where criticism no longer silently depends on schools;
> then the opt-in surfaces (adjudication, judge seats, schools, legacy path
> — each defaulting byte-identical to today, each with its
> absence-tolerant reader before any writer per the standing template);
> then the static signal-read surface; map documents in the same commits as
> the behavior they describe. Every step: one done-criterion, R/S
> citations, tools/diff_budget.py at every [COMMIT] step against a computed
> ceiling. Frozen surfaces: honor the SPEC's own contact forecast exactly
> — any contact the forecast marked as requiring authorization is
> presented AT THE CHECKLIST STOP as a named, scoped grant request (the R19
> wording pattern), never assumed; any contact the forecast did not predict
> is a hard STOP. Reader tests are partition claims. Commit and push
> CHECKLIST.md, then STOP for review before any dr-execute-step.

### Requirement resolution from Amendment 5

The decision sheet's six forks (SPEC.md §5.1-5.5 plus Road E) are RESOLVED,
not open questions any more:

- §5.1: Road A (Config-knob-value-projected-into-existing-manifest-field).
- §5.2: Road A (opt-in surface ships first; live standoff-summons wiring —
  the O1a-style even-cycle detection wired into the scheduler, and the
  suspended-pair→pairwise-trial connection — is its own later tranche,
  NOT this one; §5.6's M1-M3 rungs and R12's Road C also move to that
  later tranche, per the benching amendment's static-only scope).
- §5.3: Road A (`calibrated_status` stays inert; no verifier built).
- §5.4: Road A now, Road B named as the follow-up if disclosure alone
  proves insufficient.
- §5.5: Road B (no new critic/judge seat vocabulary; existing school/family
  routing gets an operator-facing surface instead).
- R13's Road E: folded into the legacy-criticism-paths opt-in (§2(c)) as
  its concrete surface, and — per the operator's explicit ordering
  requirement — built FIRST in the checklist, ahead of the other three
  opt-ins.

R14 (process, new): the entire implementation is STATIC/mint-time-frozen
gates only. No dynamic flip machinery, no mid-run signal consumption. This
benches: the live O1a-summons wiring (§5.2/§5.6's M1-M2), the adaptive
judge-throttle-from-signals design (§5.6 M2), and any other mid-run
gate-flip mechanism this SPEC's decision sheet gestured toward as future
work. `docs/proposals/GATES_AND_PACKAGES_PREPLAN.md` (merged to main,
commit `b19c5661b`) is the authority for this staging — Stage 1 (static
mint-time gates) is what this tranche builds; Stage 2 (dynamic flips) is
explicitly BENCHED there.

R15 (behavior/artifact, new): signal abstraction survives, in STATIC form
only — a uniform, typed READ surface over the liveness census's
confirmed-live signals (config-critique verdicts from `config_referee`,
gate-block/convergence counts, and peers), consumable at run boundaries
(report/audit/operator tooling) — never consumed mid-run to change
behavior.

C13 (process): "Proceed to dr-plan-steps... Commit and push CHECKLIST.md,
then STOP for review before any dr-execute-step." — the next and only
deliverable this phase is CHECKLIST.md; no step of it executes yet.

### Amendment 6 (2026-08-09, operator's own words, frozen-surface grant + execution authorization)

> Grant, ledgered as the next amendment, operator words: "For this
> tranche only: run_manifest.py may gain additive .pop(...) lines inside
> _versioned_source_config_data for the new opt-in flags, per the
> ENGAGED_CRITICISM_AUTHORITY trap pattern the map documents — zero
> change to any hash, schema, or validator, proven by steps 12, 13, and
> 52's own done-criteria; any other run_manifest.py hunk is a stop, not a
> judgment call; this grant is not transitive to any later tranche."
> CHECKLIST.md is approved — begin dr-execute-step from step 1, one step
> per invocation, all stop conditions live, push at every [COMMIT] step.
> Work through the full list, then dr-validate-change, and STOP after
> VALIDATION.md — delivery waits for review.

R16 (frozen-surface authorization, narrowest reading, mirroring R19's own
form from the S5 precedent): "run_manifest.py may gain additive .pop(...)
lines inside _versioned_source_config_data for the new opt-in flags... —
zero change to any hash, schema, or validator... any other run_manifest.py
hunk is a stop, not a judgment call." This authorizes EXACTLY one class of
touch, repeated once per new Config field this tranche adds
(`LEGACY_CRITICISM_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED`,
`JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_PER_CYCLE`, `JUDGE_SUMMONS_COOLDOWN`,
`SCHOOL_SEATS_ENABLED`): an unconditional `.pop("<FIELD_NAME>", None)` line
inside `_versioned_source_config_data`. Nothing else in `run_manifest.py`.
Satisfies CHECKLIST.md's "Requested grant 1."

R17 (process, non-transitivity, explicit, mirroring R20): "This grant is
not transitive to any later tranche."

R18 (process): "CHECKLIST.md is approved — begin dr-execute-step from step
1, one step per invocation, all stop conditions live, push at every
[COMMIT] step. Work through the full list, then dr-validate-change, and
STOP after VALIDATION.md — delivery waits for review." Routes this session
into `dr-execute-step`, repeated once per checklist step, then
`dr-validate-change`; the STOP after VALIDATION.md is the next and only
valid stop (supersedes C12/C13 for this later phase of the same tranche —
`dr-deliver-change` does not run until a further operator review).

C14 (process): the frozen-surface grant (R16) is scoped "for this tranche
only" and is not transitive (R17) — a later tranche touching
`run_manifest.py` needs its own explicit grant, this one does not carry
forward.

### Amendment 7 (2026-08-09, mid-execution, resolves the step-3 STOP, operator's own words)

> No I need a clean separation between school and criticism. Although they
> still need to interact.

Sent in response to the step-3 STOP report (`crit_argumentative_batch`'s
`active_v6` branch hard-requires `critic_school_id`, coupling criticism
dispatch to school routing at the guard level) and the git-blame finding
that the coupling predates both the tranche system and the school
mechanism's own maturity (commit `8cf27e850b`, 2026-07-19, "Implement
transactional inquiry runtime v6 remediation" — operator's own earlier
commit, written before an alternative to school-routed dispatch existed to
separate from).

R19 (behavior, new — supersedes the step-3 stop report's Road A/Road B
framing): "a clean separation between school and criticism" — the v6
criticism-dispatch mechanics (transactional payload construction, provider
call, case observation/counterexample/authority-gate handling — the
reusable logic in `crit_argumentative`'s body and `crit_argumentative_batch`'s
`active_v6` branch) must not INTRINSICALLY require a school; a school is
one way to supply routing (`endpoint_lease`/`critic_school_id`), not a
precondition criticism dispatch is built around.

R20 (behavior, new): "Although they still need to interact" — when a
school IS configured, criticism dispatch must still carry/record the
`critic_school_id` (for foreign-coverage counting, audit, and the existing
`_foreign_criticism_coverage` mechanism) — the separation is architectural
(criticism does not REQUIRE school to function), not a severing of the
existing, working interaction when a school is present.

C15 (process): this amendment resolves the step-3 STOP's fork with a THIRD
shape — neither Road A (widen the existing coupled guard/payload with a
bypass flag) nor Road B (a fully parallel, duplicate dispatch function) as
originally priced, but a refactor that removes the coupling at its root.
Per this session's standing discipline, a change of this shape routes back
through `dr-spec-change` before CHECKLIST.md's Road E steps are
re-planned — R19/R20 state the requirement; the concrete code shape (which
payload schema, which recovery contract, how the existing school-routed
`_foreign_arg_crit` path keeps working byte-identically) is SPEC work, not
assumed here.

### Amendment 8 (2026-08-09, mid-execution, operator's own words, response to the blast-radius report)

> Conduct blast radius analysis before changing any code. Then return
> results here.

> The separation between schools and criticism need to exist.

The first message paused execution before Step 7 to conduct a full census
of the remaining Road E and opt-in touch points. That census surfaced a
serious, previously-unread architectural boundary
(`docs/map/SEAM-scheduler-x-rules.md`'s checked invariant: the scheduler's
call into criticism must carry zero keywords, enforcing "the scheduler
never chooses a prose authority") that the originally-planned scheduler
wiring (S13f) would have violated. Two candidate resolutions were priced
and reported; the operator's second message reaffirms R19/R20's standing
requirement rather than picking the boundary-weakening option, which
resolves the choice: the separation must be achieved WITHOUT touching the
scheduler-authority boundary.

R21 (process, reaffirming R19/R20, resolving the blast-radius report's
fork): "The separation between schools and criticism need to exist." —
read together with R19/R20 and Amendment 8's first message, this rules
out the report's option (b) (revising `SEAM-scheduler-x-rules.md`'s
documented boundary) and directs the resolution toward option (a)
(`crit_argumentative_batch` self-detects v6-ness and self-resolves its own
route, with no new scheduler-supplied keywords) — subsequently verified
fully viable: `LLMAdapter` already stores a private manifest reference
(`_v6_authority_manifest`, bound once at `Scheduler.__init__` via
`adapter.bind_v6_authority`, `scheduler.py:203`) that a small new
read-only accessor can expose, and redefining `policy_call` to key on
`critic_school_id` presence rather than `call_kwargs` non-emptiness is
confirmed behaviorally identical to today for every combination reachable
before S13h (checked: every existing test/map check on `policy_call`/
`_resolve_authority` supplies `policy_call` explicitly, never depends on
its internal computation). Recorded as SPEC.md's S13i.

### Amendment 9 (2026-08-10, mid-execution of Part D, operator's own words, not yet actioned — frozen-surface grant request pending)

> A few questions. When this is done: will judge seats be assignable at the
> beginning without restriction. No rules about different families
> required. Is installing no judge or one judge optional? Also, can I swap
> out schools criticism mechanism for another one if I make it in the
> future? Or can I swap out schools for the legacy criticism route without
> causing a crash?

> Ok. Judge seat assignment needs to be without restriction. That's why I
> wanted everything to be modular. it isn't about the quality of work
> done, but the testability of various model configurations. Also, the
> split between schools and criticism needs to happen. That's what I said
> above. But that's later. What are you building instead?

> Same model grading it's own answer should be a legitimate and minting
> should still happen. Observe only should also be an optional config.

R22 (behavior, new): "judge seat assignment needs to be without
restriction. No rules about different families required" +
"Same model grading it's own answer should be a legitimate and minting
should still happen" — a genuinely single-model judge configuration (the
same model occupying every judge seat, no cross-family or cross-school
diversity at all) must be constructible AND must be able to mint a real,
status-changing warrant when a defended/rubric trial rules — not be
silently forced to `observe_only`, and not refused at compile or dispatch
time on independence grounds. The operator's own framing: "it isn't about
the quality of work done, but the testability of various model
configurations" — this is a request for CONFIGURABILITY of the
independence guarantee, not a claim that self-graded rulings are
epistemically as strong as cross-family ones.

R23 (process, new, explicit non-removal): "Observe only should also be an
optional config." — R22 must not remove or narrow `observe_only`'s
existing standing as a selectable, judge-free, zero-cost floor
(`ADJUDICATION_STATUS_AUTHORITY_ENABLED=False`/`TrialAuthority.OBSERVE_
ONLY`'s current default path, S2(a)/S2(b) as already shipped this
tranche); it must remain reachable exactly as it is today, alongside the
new same-model-mints road R22 adds.

C16 (process, standing, restated from R19/Amendment 7): "the split between
schools and criticism needs to happen... But that's later" — the operator
explicitly defers the schools/criticism separation beyond R19/R20/R21's
already-delivered architectural separation (S13i) to a FURTHER, unscoped
future tranche; not a requirement of this window.

**Blast radius (read, not yet touched, per Amendment 6's "any other
run_manifest.py hunk is a stop, not a judgment call"):** R22 requires
relaxing an INDEPENDENCE GUARANTEE enforced at two frozen layers, both
outside Amendment 6's narrow pop-line grant:
- `run_manifest.py`'s compile-time `V4_CRITICISM_CROSS_FAMILY_JUDGES_
  REQUIRED` validator (`SECOND_JUDGE_FAMILY_REQUIRED`, four raise sites:
  `run_manifest.py:1524,2397,2832,3207,3797`) and the `single_model`
  branch of `compile_run_manifest` (SPEC.md's own "Road C" finding,
  §5.2's decision sheet: genuinely single-model, same-model-in-both-
  judge-seats "is not constructible through any operator-facing surface
  today", explicitly priced as Road C and deferred by Amendment 5's own
  resolution to "that later tranche" — R22 now pulls this back into
  scope).
- `llm/firewall.py`'s runtime gate: `is_single_model_run`/
  `is_single_family_run` (`firewall.py:300-338`) and
  `require_cross_family_judge_ensemble` (`firewall.py:341-358`, raises
  `JudgeEnsemblePolicyError`/`SECOND_JUDGE_FAMILY_REQUIRED` whenever
  `len(seats) < 2 or len(families) < 2`) — consulted from
  `LLMAdapter._select_judge_ensemble`/`require_cross_family_judges`
  (`adapter.py:648-674`). A same-school substitute already exists
  (`require_cross_school_judge_ensemble`, gated on
  `school_judge_bindings` + `is_single_family_run`) but requires DISTINCT
  schools, not merely the same model — R22 asks for a road with NEITHER
  family NOR school diversity.

Both sites carry explicit design-rationale comments stating the opposite
of R22 today (`is_single_model_run`'s docstring: "this predicate unlocks a
substitute for an independence guarantee... must not fire on a run that
has more independence available than it thinks") — R22 is a genuine
reversal of that rationale's scope (from "no substitute without SOME
diversity axis" to "a substitute is available with zero diversity, as an
explicit operator choice"), not a bug in it. This is exactly the shape of
contact Amendment 5/6 name as a hard stop rather than a judgment call: not
predicted by SPEC.md's frozen-surface forecast (Road C was priced and then
explicitly deferred), and reaching both `run_manifest.py` beyond its pop-
line grant and (arguably) `llm/firewall.py`. Per this tranche's own rule,
this needs its own scoped grant, ledgered as its own numbered amendment,
before any implementation — not assumed from R22's behavioral statement
alone. STOP, pending that grant.

### Amendment 9, clarification (2026-08-10, response to the STOP report, operator's own words — GRANT)

> As long as the judges never know where the content came from and who
> generated it, this should be fine. The judge seats should be stateless,
> so it's completely blind to source or extenuating context. The
> guarantee should be about blindness. I must not have made that clear.
> So long as complete blindness is guaranteed, that's fine

This resolves R22's open design question and supplies the grant the STOP
report asked for, on a NARROWER basis than R22's own words first read: not
"no independence guarantee at all," but "the guarantee IS blindness, not
family/school diversity" — family/school diversity was always a proxy for
an unstated blindness property; the operator is naming the actual property
directly and asking that IT be the enforced condition instead of the proxy.

R24 (behavior, refines/narrows R22): the cross-family/cross-school
diversity requirement on judge ensembles may be replaced by an explicit,
verified CONTENT-BLINDNESS guarantee — the judge-facing pack/prompt must
never disclose the target's provenance (authoring role, model identity,
model family, school id, or any "extenuating context" beyond the rubric,
precedents, the target text itself, the critic's case, and the defender's
answer). A same-model (even a single literal model in every judge seat)
ensemble may mint a real, status-changing warrant once this guarantee is
established and pinned as an enforced invariant, not merely assumed.

**Pre-implementation finding (read-only, before any code changed):**
blindness of this kind already holds structurally in the current rubric-
trial dispatch path, verified by reading (not yet pinned as a checked
invariant):
- `informal/trial.py::_judge_pack` (`trial.py:174-194`) builds the judge's
  pack from `body["rubric"]`, `precedent_slice(...)`, `target_text`
  (`programs.py::content_text` — raw content bytes only, no
  `Provenance`/role/model fields), `case`, and `answer` — no artifact
  metadata field is interpolated anywhere in this function.
- `llm/roles.py::TEMPLATES["judge"]` (`roles.py:83-88`) is fixed
  instructional boilerplate plus `{pack}` — no per-call identity is ever
  spliced in.
- `school_id`/`endpoint_lease` (`adapter.py::call`, `adapter.py:901-902`)
  are ROUTING parameters only, consumed for lease selection and receipt
  bookkeeping (`adapter.py:973,1055,1062`); neither is ever written into
  prompt text.

This is NOT a claim that self-preference/stylistic self-recognition risk
is zero — SPEC.md's judge-audit evidence review already found that
specific risk unmeasured (R22's blast-radius report, and the `--judge-
seats` CLI disclosure this tranche already ships). The operator's words
read as accepting that residual, unmeasured risk explicitly ("So long as
complete blindness is guaranteed, that's fine") rather than asking this
tranche to also resolve it — blindness-of-metadata is the bar, not
proof against every route by which a model might recognize its own prose.

C17 (process, standing): future changes to judge pack construction must
preserve this blindness property; the concrete enforcement mechanism
(a pinned test, an `INV-` frozen-surface document, or both) is SPEC work
for the upcoming addendum, not decided here.

**GRANT (frozen-surface, scoped, mirroring R16/Amendment 6's form):** the
operator's clarification, read together with R24, authorizes touching
`llm/firewall.py`'s `require_cross_family_judge_ensemble`/
`is_single_model_run`/`is_single_family_run` and `run_manifest.py`'s
`V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` validator (the `single_model`
branch of `compile_run_manifest` and its `SECOND_JUDGE_FAMILY_REQUIRED`
raise sites) — SPECIFICALLY to relax the family/school-diversity
condition to a pinned content-blindness condition, per R24. This is not a
blanket run_manifest.py grant; a hunk unrelated to this specific
relaxation remains a stop, per Amendment 6's standing rule (C14). The
concrete design (new SPEC.md section, CHECKLIST.md steps) follows before
any of these files change, per this tranche's own "SPEC before CHECKLIST
before code" discipline.

### Amendment 9, second clarification (2026-08-10, response to the S16 design report, operator's own words — CONFIRMED)

> That's fine. The switch needs to be exposed to CLI is all. Otherwise
> it's not a setting.

R25 (process, new, refines S16's design choice): approves proceeding with
the S16 design as reported, on the explicit condition that whatever
mechanism governs same-model judge minting is reachable from the command
line — a `Config` field settable only by hand-editing a YAML profile does
not count ("it's not a setting" otherwise). This rules out the originally
drafted `JUDGE_BLIND_SAME_MODEL_ALLOWED` Config-only flag and directs the
design toward SPEC.md's revised S16: a CLI flag on `deepreason config
compile` (`--blind-same-model-judges`) as the actual reachable lever,
with the independence-substitute check itself made structural (reading
the manifest's/adapter's own frozen route shape, mirroring the existing
cross-school substitute) rather than gated by a separately-threaded
boolean — SPEC.md's S16 section revised accordingly, same commit as this
ledger entry.

### Amendment 10 (2026-08-10, confirms Part E's scope before execution, operator's own words)

> Yes. School opt in. But for both criticism and conjecture.

R26 (process, confirms R5/C6, no new design): directs execution to begin
on Part E (the schools opt-in, CHECKLIST.md steps 42-51) and confirms
`SCHOOL_SEATS_ENABLED` must cover BOTH school mechanisms together, not
either in isolation — a school-seat binding must be usable to give BOTH
the conjecture-side routing (`SchoolExecutionPolicyV1.mode="route_bound"`)
AND the criticism-side routing (`CriticismPolicyV1.bindings`'s per-school
distinct endpoint) simultaneously. This matches SPEC.md §2(d)'s design as
already written ("gating whether `SchoolExecutionPolicyV1.mode` may be
set to `route_bound` (conjecture side) **and/or** whether
`CriticismPolicyV1.bindings` may carry per-school distinct `endpoint_id`s
(criticism side)") — the operator's words resolve the "and/or" toward
"and": when `--seat school-N=<profile>` binds a school to a distinct
route, that binding is available to both mechanisms for that school, not
a forced choice between them. No CHECKLIST.md step needs renumbering;
Step 44's design already names both structures as targets of the same
flag.

### Amendment 11 (2026-08-10, corrects R26's reading, operator's own words — NOT YET ACTIONED, one open question below)

> What does that mean? School and criticism should be separate. Meaning
> either the schools just work on conjecture, or they can be plugged into
> criticism. Schools, by default, is a conjecture tool. Meant to minimise
> the attractor problem. What I meant by "swapping out schools" is that
> you can use a different attractor minimisation tool for the conjecture
> route. Criticism can be wired in to any conjecture tool. Or stay
> completely separate. Legacy should be the default. Other routes are
> attached to different types of conjecture tools. That's what
> independence and modularity mean. The DeepReason as a whole still
> treats criticism as a minimum operator that it hands conjectures to in
> order to find objections. But that one purpose can be attached to
> schools so that the criticism seats are primed by a school. But they
> are always separate from the conjectures.

R27 (behavior, corrects R26): a school is fundamentally a CONJECTURE-side
mechanism — a pluggable attractor-minimization tool (diversifying what
gets conjectured, so the run doesn't collapse onto one voice). "Swapping
out schools" (the operator's original question this session) means
swapping in a DIFFERENT attractor-minimization tool for the conjecture
route in the future — schools must not be architecturally assumed to be
the only possible such tool, even though it's the only one that exists
today. Criticism stays a generic, minimal operator ("hand it a
conjecture, it looks for objections") that is ALWAYS structurally
separate from whichever conjecture tool produced the candidate — this
restates and does not weaken R19/R20/R21's already-delivered separation.
Criticism MAY optionally be "primed" by a school (attached, so its
seats know the stance context) when an operator wants that, but this is
an explicit, separate attachment, never an automatic consequence of a
school existing or being seat-bound for conjecture. R26's reading
("a school-seat binding is available to both mechanisms... not a forced
choice") was too coupled — corrected here to: conjecture-side school
seats and criticism's attachment-to-a-school are two INDEPENDENTLY
toggleable things, not one flag driving both.

R28 (behavior, new, one open question before Part E resumes): "Legacy
should be the default." Read plainly this contradicts a measured fact:
`Config.LEGACY_CRITICISM_ENABLED` (Part B, already shipped this tranche)
defaults `False` today, and `v6_policy.py`'s `engaged` preset — the
actual default real public runs compile — routes criticism through
`engaged_criticism_policy(...)` (school-routed), NOT the school-free
legacy circuit. Two readings are both consistent with the operator's
words and need disambiguating before any further Part E code:
(a) a general architecture principle for Part E's NEW school-seat opt-in
specifically — when an operator turns on conjecture-side school seats
(`SCHOOL_SEATS_ENABLED`), criticism does not automatically follow into
school-routing; it stays on whatever it already defaults to (today:
`engaged`'s school-routed criticism, unaffected by this tranche's byte-
identical-default law) unless separately, explicitly attached; or
(b) a directive to flip the ALREADY-SHIPPED `engaged` preset's default
so real production runs route criticism through the legacy/school-free
circuit by default, a materially bigger and higher-blast-radius change
than anything Part E has touched so far (touches `v6_policy.py`'s public
preset, not just a new opt-in) and would need its own explicit scoping,
not an assumption made from this sentence alone. Not resolved here —
flagged back to the operator per dr-ask-the-right-question's rule that a
statement contradicting a measured fact gets surfaced, not silently
picked either way.
