# Pre-plan: role-seat separation — any model on any seat, then packages

Status: PARKED — a step-by-step program plan, not a captured request.
When picked up, each rung routes through `dr-change-orchestrator`
(`dr-capture-request` first, this document as input). Written
2026-08-06 by the monitor session on the operator's instruction:

> Actually make the step by step plan to separate them properly. Along
> with the simulation and scratch. Make them free to assign whatever
> model a user wants. Then use them in packages later.

## What the tree already gives us (anchors, verified 2026-08-06)

- **Roles are first-class** in `llm/roles.py` (spec §9): conjecturer,
  argumentative_critic, batch_critic, config_referee, defender,
  variator, judge, summarizer, synthesizer, embedder — each a prompt
  template + output contract + endpoint "routed by config".
- **The adapter already speaks seats and leases**: `select_lease(...,
  role, endpoint_index)`, per-role frozen-profile enforcement
  ("role must use its frozen model profile"), multiple endpoints
  zipped to seats. The routing seam EXISTS; today every lease resolves
  to the one provider profile `setup` bound.
- **The rung program built the whole enabling kit**: registry pattern
  (rung 3), fingerprint stamps into the typed record, registry-
  agnostic by design (rung 4), scoped selection + dumb-alternative
  proof (rung 5), conformance battery design, registry-agnostic
  (rung 6, approved/deferred), mint-time-vs-label-time placement law
  (rung 7), and live continuation of budget-exhausted runs (testphase).
- **Frozen constraints that shape everything**: provider identity is
  manifest-bound (surface 4) and qualification caches per
  (home, profile) subject digest (surface 5). Seats therefore touch
  operator-approval territory by construction — the plan isolates
  that contact into one rung instead of smearing it everywhere.

"Coder", in this plan, = the roles/call sites whose output is
executable or execution-adjacent (simulation authoring, code workload,
formal workload). "Conjecturer" = the conjecturer/variator text roles.
Scratch = the scratch-authoring call sites (`scratch/authoring.py`,
`scratch/conjecture.py`, service). The exact partition is Rung S1's
deliverable, not this paragraph's.

## The ladder

### Rung S1 — seat census  [MEASURE ONLY, no code]
Enumerate every provider call site and classify it by role and
consumer: rules/conj.py, rules/crit.py, informal/trial.py, scratch/*
(authoring, conjecture, service), capabilities/* (simulation +
research), workloads/* (code, formal, text, website), qualification,
doctor. For each: which `llm/roles.py` role it renders, which lease it
selects, whether its profile is frozen per-role today. Deliverable: a
measured table (M-numbers, pasted commands) in the tranche +
`docs/map/CON-seats.md` naming the seat concept. Also measure the
lease/seat mechanism's current degrees of freedom — what
`select_lease` can already vary. Accept: every call site in the table;
docs_verify green with the new document's checks.

### Rung S2 — seat binding design  [DESIGN-AND-STOP]
The one rung where all the danger lives; everything after it is
mechanical. SPEC only, priced options, measurements not arguments.
Decisions it must make (with the rung-7 placement law applied):

- **The binding surface.** A `SeatBinding` maps role-group → provider
  profile. Where declared? Options to price: (a) setup-time named
  profiles (`deepreason setup --seat conjecture=<profile>
  --seat coder=<profile> --seat scratch=<profile>
  --seat simulation=<profile>`, default: all seats → the single
  profile, exactly today's behaviour); (b) manifest-declared seat
  section. Expect (a) resolved at compile time with the RESULT
  recorded (see S5) to win — but the manifest half is measured, not
  assumed, because provider identity is manifest-bound today and a
  judged verdict's seat is epistemically load-bearing.
- **Qualification treatment (frozen surface 5).** Each distinct
  profile bound to any seat is its own qualification subject: full
  battery per profile (~14 min each, cached thereafter). Design
  question to price: does a seat-scoped battery exist (conjecturer
  seat qualified on conjecture cases only), or does every profile take
  the full battery? Cheaper first version: full battery per profile,
  seat-scoping deferred.
- **Replay validity.** Committed roots carry no seat bindings; every
  reader must treat absence as "single-seat run" (reader-before-writer,
  rung-4 guardrail). Old roots must never move — the S1 census feeds a
  blast-radius census here.
- **Continuation identity.** A continued run must continue under the
  SAME seat bindings its manifest/compiled config bound — a
  continuation that silently swaps a seat's model is the rung-7
  label-time mistake wearing a new hat. Typed refusal if bindings
  cannot be satisfied.
STOP: operator words required on the chosen option AND explicitly for
any manifest/qualification contact before S3 plans anything.

### Rung S3 — the binding, wired  [EXECUTE, after S2 approval]
Implement the approved design: named profiles in setup, SeatBinding
resolution where leases are built, default single-seat behaviour
byte-identical for existing configs (the whole gate must not notice).
Accept: full gate 0 failed; sweep byte-identical; a unit run with two
MockEndpoint-backed seats shows role-correct routing (each role's
calls land on its seat's endpoint — asserted from the typed attempt
records, which already carry work attribution per call).

### Rung S4 — qualification per seat  [EXECUTE]
`deepreason qualify` walks the distinct bound profiles, one battery
each, each cached by its own subject digest; `status` reports
readiness per seat; a run with any unqualified seat refuses with a
typed reason (the rung-6/fingerprint gating shape: refuse at
selection, not at registration). Accept: two-profile home qualifies
both and refuses when one battery is absent; single-profile homes hit
the existing cache exactly as today.

### Rung S5 — seats in the typed record  [EXECUTE, rung-4 template]
Extend the module-fingerprint stamp (or a sibling
`seat-bindings.v1` payload — S2 decides) so every run records
role-group → provider/model/profile-digest. Reader first,
absence-tolerant (old roots read as "single seat, the manifest's
provider"); contract clause fencing the payload; sweep probe in its
own separate commit with its own before/after capture. Accept: gate;
sweep byte-identical pre-probe; probe mutation-proven; testphase-style
live audit shows the stamp on a real run.

### Rung S6 — the dumb-alternative proof  [LIVE A/B, rung-5 template]
Two-seat live run: conjecturer on one real model, coder/simulation
seat on a different real model (or MockEndpoint for the offline arm).
Prove from the record alone: (a) which seat produced every attempt
(work attribution), (b) the seat stamp matches what setup bound,
(c) verify_root green, (d) a continuation preserves bindings or
refuses typed. The offline regression is the proof; one live attempt
is the demonstration (stochasticity rule).

### Rung S7 — packages  [after S3-S6; joins BEHAVIOR_MODES_PREPLAN]
A package = named preset bundling seat bindings + mode settings
(sampling, budgets, rule emphasis) + optional bundle ladder
(explore-seat generates → critical-seat judges via attached evidence).
Examples: "brainstorm" (cheap hot conjecturer + observe-only), "prove"
(strong coder seat, execution-heavy), "referee" (cold judge seat,
full criticism). Distribution shape: start as committed preset files +
ladder scripts (the Heddle packages/ pattern is the reference);
adoption = copy + explicit operator approval of the bindings
(installation is not authorization). Rung 6's conformance battery
applies to any module a package registers. This rung inherits the
epistemological guardrail from the modes pre-plan verbatim: seats
change how content is GENERATED, never what counts as EVIDENCE — no
package may let a generation seat's prose skip criticism.

## Order and cost

S1 (half a day, pure measurement) → S2 (a day of measured design, one
operator decision) → S3-S5 (one tranche each, the rung-3/4/5 shapes
rehearsed twice already) → S6 (one live A/B + its qualification
batteries) → S7 (its own program, scoped by then-current needs).
Frozen contact is confined to S2's decision; everything else is
reader-tolerant addition. Rungs are independently deliverable; the
ladder stops safely after any.

## What could kill it (named now, so S2 measures them)

- The manifest may bind provider identity too tightly for named
  profiles to stay out of it — then S2's option (b) territory, full
  requalification cost per home, operator call.
- Roles used inside QUALIFICATION itself must stay pinned to the seat
  being qualified, or the battery measures a chimera.
- Budget/steering signals (llm/budget.py, config_referee) may assume
  one model's token economics; per-seat budgets are S2 pricing, not an
  afterthought.
