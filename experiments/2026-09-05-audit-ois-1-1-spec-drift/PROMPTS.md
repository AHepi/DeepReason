# PARKED PROMPTS — one per DIFFERS / NOT REPRESENTED row

Read-only audit; nothing here is a change. Each block is paste-ready for an
executor window. Every prompt names the operator law it touches, so the cost
can be priced without reading the specification.

Base commit for every prompt: `c26c66de7266968157c61e269fb927c5e368d2c3`.
Evidence lives in `experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/`.

**None of the specification is adopted.** Each prompt asks the operator to
decide whether to close a measured distance, not to conform.

---

## P1 — row 1 · the dependency exemption has nine mint sites, not one

*Route:* `deepreason-orchestrator` (a defect tranche for this behaviour is
already commissioned — this prompt EXTENDS its scope, it does not restart it).
*Touches:* no frozen surface. `rules/crit.py`, `informal/trial.py`,
`rules/relatedness.py`, `rules/experiment.py`, `rules/vision.py` are all free.

```text
EXECUTOR WINDOW — DEFECT (scope extension): the dependency exemption is
nine mint sites wide.

Read CLAUDE.md in full. Load deepreason-orchestrator and dr-drive-harness.
Base on main at or after c26c66de72.

The behaviour is already diagnosed and reproduced:
experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/check01-repro.txt
shows a criticism whose essential premise is withdrawn keeps its target
refuted when the premise is a DEPENDENCE ref, and reinstates it when the
premise is an EVIDENCE ref on the validity node.

WHAT THIS WINDOW ADDS is the census the audit completed
(proof/check01-census.txt, check01-census2.txt, check01-mintsites.txt):
there are SIX argumentative warrant mint sites and 27 register_fail_warrant
call sites. Of all of them, exactly three ever put an EVIDENCE ref on a
validity node -- rules/act.py:178 (an evidence artifact), rules/warrants.py:164
(a derivation manifest), rules/vision.py:101 (recorded screenshots). None of
the three carries a premise the CRITIC declared. Four argumentative sites
(informal/trial.py:1066 and :1401, rules/relatedness.py:145,
rules/experiment.py:385) create their validity node with no interface at all,
so no premise can reach them by any route.

Fix every site, not the one the reproduction uses. The done-criterion is a
mutation-proven regression per site: withdraw the premise, the criticism
loses standing AND its target reinstates, in the same adjudication.

Operator laws in scope: none is violated by the fix itself. Do NOT add a
required field to any seat's form while doing it -- formalism-optional
(2026-08-08) forbids penalizing a criticism that declares no premises; a
criticism with an empty premise list must behave exactly as today.
```

---

## P2 — row 3 · the shipped default critic pack prints the status label

*Route:* `dr-change-orchestrator`.
*Touches:* no frozen surface. `llm/packs.py`, `llm/seat_plugins.py`,
`llm/seat_layouts.py`. Governed by `DR-INV-seat-section-plugins`.

```text
EXECUTOR WINDOW — CHANGE: stop the adjudicated status label reaching a seat.

Read CLAUDE.md in full. Load dr-change-orchestrator, dr-drive-harness and
pinker-write-for-readers. Base on main at or after c26c66de72.

Evidence (experiments/2026-09-05-audit-ois-1-1-spec-drift/):
- proof/check03-status-leak.txt: llm/packs.py:900 and
  llm/seat_plugins.py:619 both render f"- {x} [{status.value}]". The plugin
  at line 619 is dr.standing-attacks, priority 5 in CRITIC_LEGACY_LAYOUT --
  the SHIPPED DEFAULT for the critic seat.
- proof/check03-record.txt: rendering that default layout against the
  committed root experiments/2026-09-02-live-p-a2-corrected/run emits
  "- 045499e53e23... [accepted]: critic: pa1-scaling-law@v1 failed on ...".
- The record's second instance: the history arms of
  experiments/2026-09-03-change-provenance-history-channel/ put the word
  REFUTED into 33 conjecturer prompts in
  runs/home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e, and they went in
  under "## citable-evidence-blocks" -- as material the seat was invited to
  cite as evidence.

The operator law this violates is DeepReason's own, not a specification:
"Seats change how content is GENERATED, never what counts as EVIDENCE."
An adjudicated label in a seat's brief is the evidence side leaking into the
generation side.

What to decide and build: an attack shown to a critic needs to be
identifiable (so the critic does not repeat it) without carrying its
adjudicated status. Propose the smallest form that keeps the first and drops
the second. Then make it ENFORCED per the modularity law (2026-08-26): an
architecture test that goes red when any section renderer reads state.status,
so a future plugin cannot reintroduce it. dr.history.v1 stays registered and
off by default (the 2026-09-05 history ruling) -- this window does not remove
it, it makes its status vocabulary a declared exception or removes the
vocabulary from the header.
```

---

## P3 — row 4 · a criticism cannot say what it rests on

*Route:* `dr-change-orchestrator`. **Depends on P1** — build P1 first, or this
adds a field nothing consumes.
*Touches:* no frozen surface. `llm/contracts.py`, `llm/wire.py`, `rules/crit.py`.

```text
EXECUTOR WINDOW — CHANGE: give a criticism a way to name what it rests on.

Read CLAUDE.md in full. Load dr-change-orchestrator and dr-drive-harness.
Base on main at or after c26c66de72. Build AFTER the P1 defect tranche, or
this field will have no consumer.

Evidence: experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
check04-critic-contract.txt -- grep for premises_essential, essential_premise
and essential_uses over src/ returns nothing. ArgumentativeCriticOutput carries
case, counterexample, premise, premise_evidence and the successor question;
`premise` is documented in the code as a presupposition OF THE PROBLEM, not a
premise of the criticism. So the correct adjudication branch is unreachable
from the wire even where a mint site could register it.

Requirement: a criticism may name the artifacts its case essentially relies
on, and the mint sites register them on the criticism's validity node so that
withdrawing one disables the criticism and reinstates its target.

THE BINDING CONSTRAINT, and the reason this is a change and not a defect:
formalism-optional (2026-08-08, "do not make them repeat it again"). The field
is OPTIONAL and UNPENALIZED. A criticism that names nothing must rank, admit
and adjudicate exactly as it does today -- byte-identically where the record
allows. Model the field on `premise` and the successor question beside it,
both of which are already absent-legal. Do NOT import the configuration
document's R2, which would fail a call whose discriminator is empty; the
operator declined those rewrites for the default forms.
```

---

## P4 — rows 6 and 12/S17 · an imported contribution loses its place

*Route:* `dr-change-orchestrator` (a design question first, not a defect).
*Touches:* possibly frozen surface 2 (`harness.py`) if a new record kind is
needed to carry an original location. `imports.py` itself is free.

```text
EXECUTOR WINDOW — CHANGE (design first): what an imported contribution keeps.

Read CLAUDE.md in full. Load dr-change-orchestrator and dr-drive-harness.
Base on main at or after c26c66de72.

Evidence: experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
check12-hardening.txt (S17 block) and proof/check06-merge.txt.

Measured today: an imported artifact KEEPS its identity for free, because an
id is a hash of content, codec and interface. It does NOT keep its location or
its originating role. imports.py calls harness.create_artifact(...,
provenance=Provenance(role="import")) at nine sites, so the import becomes a
new event in the importing run's own sequence, after the merge, and the role
that produced it is overwritten.

Zero of the 86 committed roots have ever exercised this path, so there is no
live evidence either way and no migration cost.

The question for the operator, not for the executor to settle alone: is
overwriting the originating role a FEATURE? CLAUDE.md carries the standing
invariant "import-role admission records never count as survivors", which
reads as a deliberate reason for exactly this rewrite. If it is a feature,
this row closes as a documented difference and the tranche is a map edit, not
a code change. If the original role should survive alongside the import role,
propose the smallest carrier for it and price whether it needs a new record
kind -- which would touch frozen surface 2 and need the operator's verbatim
grant, in the shape of the 2026-09-04 section-plan contact.
```

---

## P5 — row 7 · there is no place on the record for someone's judgment

*Route:* `dr-change-orchestrator`. **Needs a frozen-surface grant.**
*Touches:* frozen surface 2 (`harness.py` event application), in the shape of
the granted 2026-09-04 section-plan contact.

```text
EXECUTOR WINDOW — CHANGE (needs an operator grant before any code): a record
kind for a situated judgment.

Read CLAUDE.md in full. Load dr-change-orchestrator and dr-drive-harness.
Base on main at or after c26c66de72. STOP at the SPEC phase and put the grant
request to the operator in their own words before any implementation step.

Evidence: experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
check07-maxima.txt. EpistemicState.status is dict[artifact-id -> one Status].
One label per artifact, COMPUTED by adjudication/ from the attack graph, never
SELECTED from competing records. Grep for "appraise" or "appraisal" over src/
returns two code comments and nothing else.

So DeepReason has no way for an identified inquirer -- the operator, a seat,
a later reviewer -- to put a reasoned judgment on the record as their own,
distinct from what the harness computed. Nor for two such judgments to
disagree without one of them being erased.

Why it matters here and not only in the abstract: the 2026-09-05 mini ruling
says a critic's objection inside mini "can't overturn anything" and that
mini's content is tested later on the full harness. An appraisal record is
exactly the shape that ruling needs -- a judgment on the record that changes
no status.

The frozen-surface ask, worded for the operator: one new record object kind,
registration and well-formedness only, fixed position, no verify_root change.
The same shape they granted on 2026-09-04 for workflow-context-section-plan-v1.
Do not write it verbally; write the request and its reason into the tranche's
SPEC.md first, as they instructed on 2026-08-21.
```

---

## P6 — row 8 · only one seat's brief is receipted

*Route:* `dr-change-orchestrator`.
*Touches:* no frozen surface. `llm/packs.py`, `rules/crit.py`,
`rules/experiment.py`, `workflow/transaction_service.py`. Governed by
`DR-INV-seat-section-sources`.

```text
EXECUTOR WINDOW — CHANGE: receipt every seat's brief, not just the
conjecturer's.

Read CLAUDE.md in full. Load dr-change-orchestrator and dr-drive-harness.
Base on main at or after c26c66de72.

Evidence: experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
check08-crossings.txt.

The receipt mechanism is real and good. A committed root carries per-section
disposition, plugin id, plugin version, parameters digest, source bytes and
rendered bytes:
experiments/2026-09-03-change-provenance-history-channel/runs/home-m1-r3/
runs/run-f23da86ddfd5ab820957221cfebe4b2e/objects/
workflow-context-section-plan-v1/

But rules/conj.py is the ONLY caller that emits one. The critic, experiment,
property and counterexample-retry briefs are built by render_batch_crit_pack,
render_crit_pack, render_experiment_pack, render_property_pack and
render_cx_retry_pack in llm/packs.py and receipt nothing. In the record: 5 of
86 committed roots carry section-plan receipts at all, and all five are
conjecturer-side.

Goal: what a seat was shown is answerable from the record for every seat, not
one. Route the remaining briefs through the layout/plugin path that already
receipts, rather than teaching each render_* function to emit a receipt of its
own -- the modularity law (2026-08-26) prefers the declared interface over the
smaller coupling, and this is precisely that fork.

The seat-is-a-shell law (2026-09-03) points the same way: the critic's brief
and form should be a registered pairing, so this tranche and that programme
are the same work seen from two sides. Check whether
experiments/2026-09-03-change-conjecturer-pluggable-interface/ already owns
part of it before starting.
```

---

## P7 — row 11 · a criticism resting on an open question still eliminates its target

*Route:* `deepreason-orchestrator` for F2; `dr-change-orchestrator` for F4.
Separate tranches — they have different costs.
*Touches:* `adjudication/` is not frozen, but F4 changes `verify_root`'s
epistemic-check report shape → **frozen surface 3**.

```text
EXECUTOR WINDOW — DEFECT: a criticism whose premise is UNRESOLVED still
refutes its target.

Read CLAUDE.md in full. Load deepreason-orchestrator and dr-drive-harness.
Base on main at or after c26c66de72.

Evidence: experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/check11-da1.txt,
fixture F2. Reproduce with
  python experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
         check11_da1_vs_harness.py

Set-up: A is a target. C is a criticism of A that essentially depends on
standard K. K and a rival standard M attack each other, so neither is
settled. DeepReason labels A REFUTED. The premise the criticism rests on is
an open question, and the target is eliminated anyway.

This is NOT the same defect as the DEPENDENCE-ref finding already
commissioned, and fixing that one does not fix this one. The cause is the
pass ORDER: adjudication/grounded.py labels the attack graph completely
before adjudication/support.py ever looks at the dependence DAG, so C's
attack has already landed by the time C is found unsupported. The reference
policy in docs/proposals/ois-1.1/verification/reference_kernel.py reaches ONE
fixed point over attacks and dependencies together and leaves A open.

Diagnose from the record first, as the family requires. Then price the two
roads honestly: (a) a joint fixed point, which changes the labels of every
artifact whose criticism has an unsettled premise, and (b) leaving it and
documenting it. Road (a) is the epistemology, not a refactor -- put the
priced fork to the operator before implementing either.

SEPARATE, SMALLER, AND DO NOT FOLD IT IN: fixture F4 in the same proof file
shows DeepReason has no UNKNOWN readiness at all -- an unattacked use whose
declared check is unavailable labels `accepted`. Adding one is a fifth status
value or a readiness field feeding the label, which changes verify_root's
epistemic-check report shape and therefore touches FROZEN SURFACE 3. That is
its own tranche and its own grant.
```

---

## P8 — row 12/S05 · the label never asks whether the body passed its own check

*Route:* `dr-change-orchestrator` (a design question).
*Touches:* `adjudication/` — see P7's frozen-surface note if a new status or
readiness value is proposed.

```text
EXECUTOR WINDOW — CHANGE (design first): should the status label consult an
artifact's own declared checks?

Read CLAUDE.md in full. Load dr-change-orchestrator and dr-drive-harness.
Base on main at or after c26c66de72.

Evidence: experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
check12-hardening.txt, S05 block. Reproduce with
  python experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
         check12_hardening.py

Measured: an artifact declares a commitment whose predicate FAILS on its own
content. No criticism has been minted yet. Registered attacks: none.
Adjudicated status: accepted.

adjudication/grounded.py reads the attack graph and nothing else. Whether an
artifact satisfied the checks it itself declared is invisible to the label
until some rule notices and mints a warrant. Between those two moments the
artifact is a survivor, and anything reading the state in that window --
a pack, the frontier, a report -- reads it as one.

Two honest readings, and the operator picks:
(a) It is fine. The rules do run, the window is short, and "no warrant, no
    edge, no REFUTED" (DR-CON-warrants-and-attacks) is the design: a label
    that could move without a registered, attackable warrant would be a
    hidden authority.
(b) It is a false-positive path. A declared machine check that failed is the
    cheapest, least arguable evidence there is, and letting it sit unread
    while the artifact counts as accepted is the "admitted therefore
    successful" move the record is supposed to make impossible.

Reading (a) is the stronger one on DeepReason's own terms and the executor
should say so. What the tranche should measure before anything is built:
across the committed roots, how long an artifact with a failing declared
check actually stays accepted, and whether any pack, frontier or report ever
read one in that window. Tokens are cheap and the agent is not -- measure it
from the record rather than arguing it.
```
