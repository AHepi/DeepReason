# Request: make the critic seat's byte-checked citation channel reachable often enough to be measurable, and stop it latching permanently shut on the first premise filed

Captured: 2026-08-28, from the monitor's dispatch of the operator-approved
P11 prompt (`experiments/2026-08-28-audit-run-problems/PARKED.md` §P11),
plus the operator's own standing 2026-08-28 law recorded in CLAUDE.md.

## Verbatim

**(a) The operator's approval of the program, relayed in the dispatch:**

> Operator, 2026-08-28, approving the program: criticism must be able to bite
> what generation produces; the audit (F-B) established the critic's
> byte-checked citation channel was structurally closed on 93 of 98 dispatches
> and latches shut permanently after one use — M2 was unmeetable, not unmet.

**(b) The ready-to-send prompt, verbatim from `PARKED.md` §P11** (the
authority for scope; quoted in full, untrimmed):

> ```
> Route: dr-change-orchestrator (a design change, not a defect -- nothing is
> broken; a channel is gated so tightly it cannot be exercised). Sequence AFTER
> P10: the criticism authority this run executed under was not the one its config
> named, and that must be settled before anyone tunes a criticism channel.
>
> Goal, one sentence: make the critic seat's byte-checked citation channel
> reachable often enough to be measurable, and stop it latching permanently shut
> on the first premise filed.
>
> Evidence, all committed:
>   experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-B
>   experiments/2026-08-28-audit-run-problems/probes/q1_prompt_surface.json
>       -> 98 critic dispatches, 5 shown the invitation, 5 shown the legend
>   experiments/2026-08-28-audit-run-problems/probes/q1_invite_gate.py output
>       -> max REFUTED on one problem: 1, 1, 3, 6 across the four roots
>   experiments/2026-08-28-audit-run-problems/probes/q1_invited_replies.json
>       -> what the seat returned on each of the 5
>   experiments/2026-08-28-audit-run-problems/probes/live/SUMMARY.json
>       -> the registered live probe: 0/8 control, 0/8 exemplar
>   experiments/2026-08-28-audit-run-problems/PREREG_LITE.md
>       -> frozen before the probe ran, including what it CANNOT establish
>
> Code:
>   src/deepreason/premises.py:625-645 premise_work_invited -- the gate
>   src/deepreason/premises.py:68     PREMISE_INVITE_AFTER = 2
>   src/deepreason/premises.py:638    the latch: any standing attribution closes
>                                     the problem to further invitations forever
>   src/deepreason/rules/crit.py:1268 _premise_invited_problem
>   src/deepreason/rules/crit.py:1368 _check_premise_citations -- the ONLY
>                                     producer of the premise-citation Measure,
>                                     and it records NOTHING when refs is empty
>   src/deepreason/rules/crit.py:1401 _file_attribution -- returns None uninvited
>   src/deepreason/rules/crit.py:1283 _citable_blocks -- the legend, rendered
>                                     only under the invitation
>
> Read DR-CON-criticism-source and DR-SEAM-scheduler-x-rules before designing,
> and DR-INV-frozen-surfaces first.
>
> Three questions to answer explicitly, in this order:
>
> (1) THE LATCH. premises.py:638 closes a problem to further invitations the
> moment one attribution stands. On the evidence that is the binding constraint,
> not the threshold: the run proved its own question malformed 593 events after
> the channel closed. Should the gate reopen -- on a new refutation, on a new
> attribution being refuted, on nothing at all? Say why, and price the cost of
> re-asking (each invitation is a rendered legend in a critic pack).
>
> (2) THE EMPTY-REFS SILENCE. crit.py:1368 returns () without a Measure when
> premise_evidence is empty, so the record cannot distinguish "the seat was
> invited and declined" from "the seat was never invited". Both read as zero.
> The invited-and-declined case is real evidence about a seat and should be
> typed. This is cheap and is probably worth doing even if nothing else here is.
>
> (3) THE UNINVITED SCHEMA FIELD. On 93 of 98 dispatches premise_evidence sits in
> the wire contract with no legend and no legal value. RUN_ANATOMY_SYNTHESIS
> section 2.5 measured what models do with a required field they cannot satisfy
> (255 of 257 fabricated); this field is nullable so they nulled it instead,
> which is the good outcome. Decide whether the field should be ABSENT from the
> contract when the invitation is absent, rather than present-and-unfillable.
>
> Do NOT lower PREMISE_INVITE_AFTER as the whole fix. A threshold change without
> (1) still gives one invitation per problem per run, and this audit's evidence
> is that one is not enough to catch a criticism that arrives late.
>
> Do NOT treat the live probe as showing the seat "will not cite". A null premise
> is legal when the seat sees no malformed presupposition, and the probe cannot
> separate that from refusal -- PREREG_LITE.md says so in advance. If you want
> that separated, the audit's residue item 2 names the experiment: the same
> replay with a deliberately malformed presupposition planted in the problem
> text, ~40k tokens, where a correct seat MUST fill premise.
>
> End state: a problem can invite premise work more than once under a stated
> rule; an invited-and-declined dispatch is typed on the record; a regression
> test drives a run where the channel opens after a late refutation; full gate
> 0 failed; map moved in the same commit.
> ```

**(c) The monitor's dispatch amendments to (b), verbatim:**

> The sequencing note in the brief ("after P10") is OVERRULED by the monitor
> for concurrency: your cone and P10's are disjoint, and your three design
> questions do not depend on P10's outcome. Note in SPEC.md that any live
> re-measurement of M2 waits until both tranches are merged.

> (The optional planted-presupposition probe the brief mentions is NOT authorized
> in this window — park it.)

> FROZEN-SURFACE FORECAST: none — your cone is premises.py, rules/crit.py,
> tests, map documents (read DR-CON-criticism-source and
> DR-SEAM-scheduler-x-rules before designing, DR-INV-frozen-surfaces first).
> If any frozen surface or committed digest pin turns out to move, STOP and
> report. Mind the seats law while designing: the channel changes how
> criticism is GENERATED and checked; nothing here may let critic prose skip
> criticism or change what counts as evidence.

> PARALLEL WINDOWS — MUTUAL STOP LINES: a render-layout tranche owns
> llm/layout.py, llm/packs.py, llm/roles.py, informal/trial.py and its
> fixtures; a manifest tranche owns run_manifest.py and preparation.py. Do not
> touch either cone or their tranche directories. The technique branch is
> read-only evidence. ERRATA numbering collisions likely at merge — mint from
> the tail and note it.

> KNOWN CURRENT STATE: main = 2a5e984c8; gate baseline 4374 passed 0 failed;
> docs_verify baseline 3 shallow-clone + 1 pre-existing falsified census — a
> delta beyond four is a finding. Root sweep RETIRED. Never work around a
> REFUSED_* or typed stop.

> GATE: ring while iterating, full gate at the boundary (0 failed only),
> docs_verify full, mutation-proven regression tests (RED then GREEN, output
> committed) including the brief's named one — a run where the channel opens
> after a late refutation; map moves in the same commits; commit and push
> every phase boundary (retry 2s/4s/8s/16s).

> DELIVERY: per the brief's end state, R-by-R with pasted proof.

**(d) The operator's standing 2026-08-28 law that binds this design
(CLAUDE.md, operator's words verbatim):**

> "My intention was that configuration of seats need to be able to turn
> gates on and off at will. Meaning no limits to what model you place
> where. It also means that when and if I decide to replace schools with
> something different, those flags don't gate seat configuration paths.
> Gates are always optional: with warnings. Although behaviour path
> should be deterministic, yet also configurable. Do I want to
> prioritise brainstorming and idea generation first before subjecting
> the content to rigorous criticism and elimination -- the difference
> between strict narrowing and interesting options for a user to choose.
> Do I want to pick and argument apart and poke holes wherever possible
> and not necessarily create novel ideas. This isn't an exhaustive list,
> it's just two examples. That's why I made DeepReason modular, so these
> types of modes could be generated: Analysis mode, daydream mode,
> critic model, novel exploration mode; whatever."

## Requirements

R1 (behavior): "a problem can invite premise work more than once under a stated
rule" — the latch at `premises.py:638` must no longer close a problem to
further invitations permanently.

R2 (artifact): "(1) THE LATCH. ... Should the gate reopen -- on a new
refutation, on a new attribution being refuted, on nothing at all? Say why, and
price the cost of re-asking (each invitation is a rendered legend in a critic
pack)." — answered explicitly, in writing, first of the three.

R3 (behavior + artifact): "(2) THE EMPTY-REFS SILENCE. ... The invited-and-declined
case is real evidence about a seat and should be typed." — "an
invited-and-declined dispatch is typed on the record"; and the brief's claim
that this "is probably worth doing even if nothing else here is" must be
agreed with or refuted in writing.

R4 (artifact): "(3) THE UNINVITED SCHEMA FIELD. ... Decide whether the field
should be ABSENT from the contract when the invitation is absent, rather than
present-and-unfillable." — a written decision, answered third.

R5 (behavior/artifact): "a regression test drives a run where the channel opens
after a late refutation" — mutation-proven, RED then GREEN, output committed.

R6 (process): "full gate 0 failed; map moved in the same commit."

R7 (process): "Note in SPEC.md that any live re-measurement of M2 waits until
both tranches are merged."

R8 (process): "the optional planted-presupposition probe the brief mentions is
NOT authorized in this window — park it."

R9 (process): "DELIVERY: per the brief's end state, R-by-R with pasted proof."

## Standing constraints

C1: "Do NOT lower PREMISE_INVITE_AFTER as the whole fix. A threshold change
without (1) still gives one invitation per problem per run, and this audit's
evidence is that one is not enough to catch a criticism that arrives late."
— §P11, prohibition 1.

C2: "Do NOT treat the live probe as showing the seat 'will not cite'. A null
premise is legal when the seat sees no malformed presupposition, and the probe
cannot separate that from refusal" — §P11, prohibition 2.

C3: "FROZEN-SURFACE FORECAST: none ... If any frozen surface or committed
digest pin turns out to move, STOP and report." — dispatch. The five frozen
surfaces of `DR-INV-frozen-surfaces` (seven paths: `capabilities/state.py`,
`harness.py`, `invariants.py`, `verification/`, `run_manifest.py`,
`qualification.py`, plus frozen-adjacent `route_fingerprint` in
`llm/firewall.py`).

C4: "PARALLEL WINDOWS — MUTUAL STOP LINES: a render-layout tranche owns
llm/layout.py, llm/packs.py, llm/roles.py, informal/trial.py and its
fixtures; a manifest tranche owns run_manifest.py and preparation.py. Do not
touch either cone or their tranche directories."

C5: "Mind the seats law while designing: the channel changes how criticism is
GENERATED and checked; nothing here may let critic prose skip criticism or
change what counts as evidence." — dispatch, invoking the operator's
generation-vs-evidence guardrail.

C6: "ERRATA numbering collisions likely at merge — mint from the tail and note
it."

C7: "gate baseline 4374 passed 0 failed; docs_verify baseline 3 shallow-clone +
1 pre-existing falsified census — a delta beyond four is a finding."

C8: "Never work around a REFUSED_* or typed stop." — dispatch.

C9 (operator law, CLAUDE.md 2026-08-28): "Gates are always optional: with
warnings. Although behaviour path should be deterministic, yet also
configurable." Any gate this tranche touches must remain switchable per run
and deterministic given a configuration.

## Map preflight — resolved ids

Read in the mandated order before any design:

- `DR-INV-frozen-surfaces` — read FIRST. Forecast: no contact. The cone
  (`premises.py`, `rules/crit.py`, `llm/contracts.py`, `llm/wire.py`, tests,
  map documents) intersects none of the five surfaces' seven paths.
- `DR-SEAM-scheduler-x-rules` — read BEFORE either side. Owns
  `scheduler/scheduler.py`, `rules/conj.py`, `rules/crit.py`,
  `rules/spawn.py`. Row 58 is the load-bearing one: "the scheduler consults
  the premise layer and moves no label; the INVITATION itself is computed
  inside `rules/crit.py`, because `_arg_crit`'s call is keyword-free".
- `DR-CON-criticism-source` — owns `rules/crit.py`. Its "Where to change
  what" table routes "What a filed premise may cite, and how the citation is
  checked" to `_file_attribution` / `_check_premise_citations`, test
  `tests/test_p4_citable_evidence.py`.
- `DR-SUB-premises` (if it exists) / `DR-SUB-evidence` — the checker itself.
- `DR-INV-evidence-channels` — what counts as evidence (C5's guardrail).
- `DR-CON-authority` — the authority vocabulary this socket resolves.

## Open questions (for dr-spec-change)

Q1: Which reopen rule? (R2 — the brief names three candidate answers and
demands a priced justification, not a free choice.)
Q2: Does the invited-and-declined Measure go on the citation-Measure channel
(`premise-citation:<CODE>`) or a separate one, given C5 (nothing here may
change what counts as evidence)?
Q3: Does removing `premise_evidence` from the uninvited contract move any
committed digest pin (contract id, qualification subject, wheel-smoke schema
sha)? C3 makes this a STOP condition if it does.
Q4: Is `PREMISE_INVITE_AFTER` reachable as configuration under the modularity
law, given `premises.py:68`'s recorded reason for it being a module constant
(a Config field would need a line in frozen `run_manifest.py`)?

## Amendments

(append-only)
