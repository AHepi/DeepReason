# Request: isolated-LLM probe wiring audit, then an apparatus spec (amended from "research source" framing)
Captured: 2026-08-09 from the task-description message and one mid-turn
amendment message sent by the operator during Phase A execution.

## Map preflight (recorded before routing)

- `DR-SUB-capabilities` (`src/deepreason/capabilities/`) — the research
  capability lifecycle (`capabilities/research.py`), whose grant/execute/
  consume machinery and frozen `state.py` digesting are the base this
  work extends or reuses.
- `DR-SEAM-capabilities-x-rules` — the only documented seam this package
  has: a capability proposal is filed only from inside a conjecture turn,
  as semantic intent the model authored, never as an operational
  parameter. Governs any new conjecturer-side or critic-side probe path.
- `DR-INV-frozen-surfaces` — read before designing (see below); surfaces
  1 (`capabilities/state.py` digests/apply), 2 (`harness.py` event
  application), 3 (replay-validation formats), 4 (manifest schemas AND
  validators), 5 (qualification subject digests) all bound on any change
  that touches the capability lifecycle or manifest.
- `DR-CON-conjecture-kinds` — the dual-mode (formal/informal) candidate
  precedent the amendment names as the template for a probe-checkable
  commitment shape, and the seat of the R-g guardrail (formalism is an
  option, never an obligation).
- `DR-CON-seats` — `select_lease`, `EndpointLease`, one-profile-per-run
  minting; governs how a probe would acquire a model endpoint distinct
  from a run's seated provider.
- `DR-SUB-scratch` — declared `advisory_non_grounding`; governs the
  scratchpad access point the amendment names for conjecturer-side probe
  exploration.
- Undocumented-but-relevant seam pairs per `INDEX.md`'s matrix:
  capabilities x rules (documented above), capabilities x scheduler
  (documented in `DR-SUB-capabilities` itself: research executes inside
  the conjecture turn, never scheduler-dispatched), capabilities x
  llm/workflow (candidate pairs, not yet analyzed — may need first-time
  documentation if the probe apparatus is judged to touch them).

## Verbatim — original task description

> Is the ability for endpoints to query the output of isolated LLMs for
> research purposes still wired? ... First, check the wiring and ensure
> its secure. Then check where it can be accessed from. Third, we have
> to decide whether it's access points are worth expanding.

> Phase A — WIRING AUDIT (measure, paste evidence): reconcile
> docs/RESEARCH_BACKEND.md's "tranche 2 gated" claim against the tree
> (capabilities/research.py's controller lifecycle,
> V6_RESEARCH_UNAVAILABLE — what is actually reachable in a live managed
> run today, proven by the committed live_research_2026-07-29 roots and
> the enrichment corpus's research records); enumerate every access point
> (docket/submit_evidence seam, ladder-level run_research, in-run
> capability channel if live) and each one's containment properties; if
> the doc is stale, that's an ERRATA entry per the new checkpoint rule.

## Verbatim — amendment (supersedes the "research source" framing for Phase B)

> Amendment to your capture — the operator corrects the design intent,
> ledger these words verbatim, superseding the "research source" framing:
> "I want the harness to figure out how to run without having to keep
> review only mode on for solo runs. I was also intending on the isolated
> LLM functioning as way for conjecturers to test their theories about the
> limits of LLMs. Preferably reachable from scratch pad, as well as
> critics. It would help with broadening the attack surface of
> conjectures."

> Phase B's SPEC now designs the LLM-probe channel: an isolated-model
> APPARATUS, not a source — (1) a typed probe protocol (model allowlist
> frozen like the domain allowlist, prompt + sampling params recorded,
> budgets requests-denominated, receipts with digests — the fetch-receipt
> replay precedent applies: probes are attested observations, never
> re-executed at replay); (2) TWO access points, priced separately against
> the seam docs: the scratchpad (conjecturer-side exploration — advisory
> tier, per the spec's own law that scratch can never establish grounding)
> and the criticism path (critic-side counterexample probes — where a
> probe result becomes execution-grade evidence against a conjecture
> ABOUT LLM behavior, the attack-surface broadening the operator names);
> (3) the commitment shape: how a conjecture about LLM limits declares a
> probe-checkable commitment (the dual-mode candidate-checker precedent is
> the template), making this domain mechanically adjudicable in SOLO runs
> with no judge anywhere — cite the solo law, the seats/evidence
> guardrail, R-g, and the judge-review §8 as binding constraints; (4)
> stochasticity honesty: probes are sampled behavior, not pure functions —
> specify how many samples ground a claim, how variance is recorded, and
> what a probe can NEVER do (rule on prose quality). Frozen-surface
> forecast from scratch; decision sheet priced; STOP after SPEC.md.

## Requirements

R1 (process): "First, check the wiring and ensure its secure." — Phase A
wiring audit of the existing research-capability channel: reconcile
`docs/RESEARCH_BACKEND.md` against the tree, with pasted evidence.

R2 (process): "Then check where it can be accessed from." — enumerate
every access point to the existing wiring and each one's containment
properties.

R3 (process): "Third, we have to decide whether it's access points are
worth expanding." — Phase B, superseded in shape by the amendment below;
originally framed as a decision sheet on expanding access to
LLM-as-research-source, now reframed per the amendment as designing a
probe APPARATUS.

R4 (artifact, superseding R3's original framing — "supersedes the
'research source' framing"): design a typed probe protocol for querying
isolated model endpoints — model allowlist frozen like the domain
allowlist, prompt + sampling params recorded, requests-denominated
budget, receipts with content digests, "the fetch-receipt replay
precedent applies: probes are attested observations, never re-executed
at replay."

R5 (artifact): design exactly two access points, priced separately
against the seam docs — "the scratchpad (conjecturer-side exploration —
advisory tier, per the spec's own law that scratch can never establish
grounding) and the criticism path (critic-side counterexample probes —
where a probe result becomes execution-grade evidence against a
conjecture ABOUT LLM behavior, the attack-surface broadening the
operator names)."

R6 (artifact): design the commitment shape — "how a conjecture about LLM
limits declares a probe-checkable commitment (the dual-mode
candidate-checker precedent is the template), making this domain
mechanically adjudicable in SOLO runs with no judge anywhere" — citing
the solo law, the seats/evidence guardrail, R-g, and judge-review §8 as
binding constraints.

R7 (artifact): "stochasticity honesty: probes are sampled behavior, not
pure functions — specify how many samples ground a claim, how variance is
recorded, and what a probe can NEVER do (rule on prose quality)."

R8 (artifact): "Frozen-surface forecast from scratch" as part of SPEC.md.

R9 (artifact): "decision sheet priced" as part of SPEC.md.

R10 (process): "if the doc is stale, that's an ERRATA entry per the new
checkpoint rule" — if Phase A finds `docs/RESEARCH_BACKEND.md` stale
against the tree, file a `docs/ERRATA.md` entry.

R11 (process): "Commit and push each phase" — commit+push after Phase A
and after Phase B.

R12 (process): "STOP after SPEC.md." — no `dr-plan-steps`/execution in
this tranche; SPEC.md is the deliverable and the tranche ends there
pending operator approval.

## Design-intent context (not a numbered obligation, but binds
## interpretation of R4–R7 in dr-spec-change)

> "I want the harness to figure out how to run without having to keep
> review only mode on for solo runs."

This names the motivating problem the probe apparatus must solve: a solo
run (no judge seats, per the operator's standing solo law in CLAUDE.md)
currently cannot let prose-stage conjectures about LLM behavior become
execution-grade without either a judge or "review only mode." The probe
apparatus is the mechanically-adjudicable alternative for this one
domain (claims about LLM behavior), not a general judge replacement.

> "I was also intending on the isolated LLM functioning as way for
> conjecturers to test their theories about the limits of LLMs."

Conjecturer-side use is exploratory/theory-testing, routed through
scratch (advisory, non-grounding) per R5.

> "Preferably reachable from scratch pad, as well as critics."

Both access points are required, not optional design alternatives.

> "It would help with broadening the attack surface of conjectures."

The critic-side probe path is the one that can change execution-grade
status — "broadening the attack surface" names criticism's role of
attacking conjectures, matching the operator's own R-g
formalism-is-never-an-obligation vocabulary (a probe-checkable commitment
is a new attackable surface alongside formal execution).

## Standing constraints

C1: "STOP after SPEC.md." — no execution phase in this tranche.
C2 (CLAUDE.md, Operator design laws — cited by the amendment itself):
the solo law ("A solo run with everything on must be an option"), the
seats/evidence guardrail ("Seats change how content is GENERATED, never
what counts as EVIDENCE"), R-g (formalism is an option, never an
obligation — see `DUAL_MODE_CONJECTURE_PREPLAN.md`), and judge-review §8
(`experiments/2026-08-09-change-judge-evidence-review/REVIEW.md`).
C3 (CLAUDE.md, frozen surfaces): `capabilities/state.py`, `harness.py`,
replay-validation formats, manifest schemas AND validators, qualification
subject digests — any of these touched by the spec must be forecast, not
silently assumed changeable.
C4 (CLAUDE.md, explain-to-operator): every message to the operator —
intermediary and final — follows the binding communication discipline
(worry first, gloss terms, one closing analogy on the final message).

## Open questions (for dr-spec-change)

Q1: Is the isolated-model endpoint for probes the SAME provider/model
pool the run's own seats draw from (risk: seat/evidence conflation) or a
disjoint pool (needs its own allowlist entity)? The amendment says
"isolated LLM," suggesting disjoint, but the exact provisioning
mechanism (new `Config` field? new policy? reuse of `CON-seats`
`select_lease`?) is not stated by the operator's words and is SPEC's to
decide, recording the assumption.
Q2: Whether the probe apparatus is scoped to THIS tranche as SPEC-only
(per R12, yes — no implementation now) is settled; what is open is
whether Phase A's audit surfaces an existing partial mechanism SPEC
should reuse vs. one that must be superseded outright. Resolved by
Phase A's evidence, not asked.

## Amendments

(none yet — the mid-turn message above is captured as the operative
Phase B framing in this same initial REQUEST.md, since it arrived before
Phase A's wiring-audit work began and no artifact yet existed to amend)
