# Request: "the discharge-required criticism channel — criticism enters the writer's working context, and submission requires it discharged"

Captured: 2026-08-26 from the operator's tranche instruction (message 1, session
opening) and the operator's mid-turn amendment (message 2, arriving during map
preflight, before any artifact existed).

Tranche: `experiments/2026-08-26-change-f1-discharge-criticism-channel/`.
Branch: `claude/rebuild-discharge-criticism-channel-2b8z8i`.
Base: `origin/main` at `4760a32ef` (be9bcff54 confirmed ancestor).
Family: `dr-change-orchestrator`.

## Map preflight — resolved ids

Read in the prescribed order (`dr-drive-harness` §4): `docs/map/INDEX.md` →
`docs/map/INV-frozen-surfaces.md` → the seams → the subsystems.

| Id | Why it is in scope |
|---|---|
| `DR-SEAM-llm-x-rules` | the pack render sections meet the rule that dispatches them — C1's vehicle |
| `DR-SEAM-rules-x-workflow` | the submission path's transactional lifecycle — C2's boundary |
| `DR-SEAM-calculus-x-rules` | Rung 6's render machinery (`calculus/render.py` ↔ `rules/conj.py`), the declared vehicle for C1 |
| `DR-SEAM-adjudication-x-rules` | C3's law line: the boundary a discharge may never cross |
| `DR-CON-criticism-source` | `rules/crit.py` — where an open criticism is recorded (`_observe_case`, the `["scrutiny", target, critic]` Measure) |
| `DR-CON-conjecture-source` | `rules/conj.py` — the socket that proposes candidates; the submission precondition lands here |
| `DR-CON-packs-and-token-economy` | section allocation, `DISCLOSED_ON_DROP`, the non-droppable rule C1's persistence needs |
| `DR-CON-authority` | who may change a Status — C3's "never what counts as EVIDENCE" |
| `DR-CON-warrants-and-attacks` | the chain a REBUTTED discharge must enter as an ordinary criticism artifact |
| `DR-CON-conjecture-kinds` | the R-g formalism-optional guardrail, which R11 below restates for discharge kinds |
| `DR-SUB-llm` | `llm/packs.py`, `llm/wire.py` — pack sections and the submission's wire shape |
| `DR-SUB-rules` | `rules/conj.py`, `rules/crit.py` |
| `DR-SUB-adjudication` | labels; the mutation proof's target |
| `DR-INV-frozen-surfaces` | read BEFORE designing, per law |
| `DR-INV-signal-contract` | the FROZEN / VERSIONED / FREE pattern R12 binds this tranche to |

**No map id exists for a discharge channel.** That is this tranche's own
finding, recorded here rather than treated as a blocker: a new
`CON-discharge-channel.md` (or equivalent) is part of the work, per
`dr-drive-harness` §4 step 5.

## Verbatim

### Message 1 — the tranche instruction (session opening)

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if based elsewhere, ask the operator to attach it with push access
> and STOP until then.
>
> Change tranche F1 of the REBUILD program: the discharge-required
> criticism channel — criticism enters the writer's working context,
> and submission requires it discharged. Route through
> dr-change-orchestrator; the workflow's own stops apply.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor be9bcff54 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`,
> never bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY for REQUEST.md, operator verbatim (2026-08-26):
> "rebuild. These are massive issues that may explain why the
> results are terrible." The motivating evidence, cite it:
> W2's placebo-corrected coupling (zero or negative; 0 of 92
> coupled changes improved a score; NeglectRate 82-91%) —
> experiments/2026-08-26-run-anatomy-program/W2*/RESULTS.md — and
> the external protocol it points at:
> docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md Q5 — criticism entering
> a separable advice field gets neglected; criticism entering the
> solver's WORKING CONTEXT with discharge-required re-submission is
> the structure that coupled. Q5's warning is BINDING: do NOT build
> an acknowledgment requirement — ACK-required measurably HURT.
>
> THE CHANGE:
> C1 IN-CONTEXT CRITICISM: open criticisms on a problem render
>    INSIDE the conjecturer's working section of the pack (not a
>    sidebar section) — each as the claim, the cited span, and a
>    stable discharge handle. Rung 6's render machinery is the
>    vehicle; its persistence rule already applies (renders every
>    cycle until discharged, asserted at terminal).
> C2 DISCHARGE-REQUIRED SUBMISSION: a new candidate on a problem
>    with open criticisms must carry, per criticism handle, a typed
>    discharge: REVISED (what changed, where), REBUTTED (why the
>    criticism fails — itself attackable), or DEPARTURE-DECLARED
>    (the Rung 6 protocol; no penalty). A submission with
>    undischarged handles is returned ONCE with the open list (a
>    typed re-ask, not a repair grant), then accepted WITH a typed
>    undischarged disclosure — disclose, never die (the
>    all-configurations law at the submission boundary).
> C3 THE LAW LINE, stated in SPEC and pinned by test: discharge
>    constrains how content is GENERATED (a submission
>    precondition), never what counts as EVIDENCE — no discharge
>    field ever feeds a label, a warrant, or adjudication; a
>    REBUTTED discharge is just a criticism artifact entering the
>    ordinary graph. Mutation-prove the boundary (wire a discharge
>    into label computation in a scratch copy, RED, restore).
>    Formalism-optional also binds: discharge kinds carry no rank
>    or admission weight.
>
> GATE PROVES: the coupling instrument from W2 (reuse its committed
> operationalization R1) re-run on an OFFLINE stub-driven run with
> the channel on vs off — coupling must be measurably nonzero with
> the channel on where the stub's criticism names a mechanical
> respect; the disclosure road works; C3's mutation proof; no label
> differs between channel-on and channel-off runs on the same graph.
> Full gate 0 failed; docs_verify full; map moves in the same
> commits.
>
> CONCURRENCY: F2 (wire-contract handle menus) and F3 (config
> defaults + allocation policy) run in parallel. Your blast radius:
> pack render sections, the submission path, discharge records. If
> you need to edit wire-contract FIELD definitions (F2's) or
> Config defaults (F3's), STOP and say so. SIZE: if SPEC exceeds
> ~700 lines of plan, STOP and say what grew. Commit and push every
> phase boundary (retry 2s/4s/8s/16s).

### Message 2 — mid-turn amendment (arrived during map preflight)

> NEW OPERATOR LAW, ledgered on main 2026-08-26 (CLAUDE.md §Operator
> design laws — re-read it): "There needs to be a priority that
> enforces modularity. Customisation needs to be easy." Amend your
> REQUEST.md with it as a requirement and let SPEC.md answer it
> explicitly. What it means for this tranche:
>
> - Every knob, policy, and behavior your tranche introduces is
>   reachable as CONFIGURATION or a REGISTERED VERSIONED ARTIFACT —
>   if customizing it would require editing code, the design is
>   wrong; rework it before implementing.
> - Your new machinery sits behind a DECLARED INTERFACE on the
>   signal-contract pattern (frozen protocol / versioned artifact /
>   free parameters), and you ship an ARCHITECTURE TEST that goes
>   RED when a consumer bypasses the interface — a modularity claim
>   without a failable check is decoration.
> - At any design fork between a tighter coupling that is smaller
>   and a declared interface that is larger, the interface wins —
>   the operator has priced this and chosen.
>
> Binding it to your specific tranche:
> - F1: the discharge policy (kinds, the re-ask behavior, the
>   disclosure road) is a registered, config-selectable policy —
>   new discharge kinds enter by declaration, not by editing the
>   submission path.
> - F2: the menu renderer is an interface keyed by field kind —
>   a new reference-bearing field type gets a menu by registering,
>   not by touching the renderer; the one-authority legal-set
>   source is the interface's contract.
> - F3: you are closest to compliant already — the wander cap is a
>   policy artifact and the channels are config defaults; add the
>   architecture test that a channel toggle and a floor change are
>   pure configuration, and strike-or-emit the phantom signals so
>   the registry never lies about what is customizable.

### Message 3 — the grant (reply to SPEC.md's three batched questions)

> GRANTED, PROCEED, ONE TRANCHE — the three words, with the standard
> riders:
>
> Q1 GRANTED: the one-line versioned-source entry for
> DISCHARGE_POLICY in run_manifest.py. This is not an exception to
> the frozen surface — it is the documented recipe (a Config field
> is not done WITHOUT that line; the ENGAGED_CRITICISM_AUTHORITY
> trap is its ancestor). Riders, same as every prior grant: SPEC.md
> records "GRANTED 2026-08-26"; the digest before/after measurement
> (b9038b84... unchanged) is committed as pasted proof; the map's
> frozen-surface document gains the contact line in the SAME commit
> as the code; the line exists for EVERY schema version the
> serializer handles, not just the newest.
>
> Q2: read C6 as "F2's fields" — that reading is the intent. The
> boundary exists to prevent collision, not to freeze the wire
> layer; two optional fields of your own, in a different region,
> digest-byte-identical, hidden when the channel is off, is
> additive per-call machinery done properly. The composition note
> (discharges[].handle registering into F2's menu interface later)
> is exactly the modularity law working — record it in SPEC so F2's
> window or a successor finds it. The wire.py merge is the
> monitor's problem, not yours.
>
> Q3: one tranche, three commits, ~640 lines accepted. The ~140
> interface lines are the modularity law's own price, paid where
> the operator said to pay it (R15: the interface wins the fork).
> Rung 6's precedent stands. The diff-budget discipline still
> applies at your stated ceiling — a typed STOP if it grows beyond
> what SPEC now declares, not silent growth.
>
> And the honesty paragraph is accepted as scoped: F1 claims
> DELIVERY, not response — the offline gate proves the channel
> carries and the off-state cannot, RESULTS.md says a live model's
> responsiveness is P2's question, and the parked four-arm A/B
> remains the live proof. The upcoming P-C2 rematch will bear on it
> but does not replace P2's design. Proceed.


### Message 4 — the ceiling ruling (reply to step 10's R19 typed STOP)

> 900


### Message 5 — the second ceiling ruling (reply to the signal-contract STOP)

> raise approved. keep going


## Requirements

R1 (behavior): "open criticisms on a problem render INSIDE the conjecturer's
working section of the pack (not a sidebar section) — each as the claim, the
cited span, and a stable discharge handle."

R2 (behavior): "Rung 6's render machinery is the vehicle; its persistence rule
already applies (renders every cycle until discharged, asserted at terminal)."

R3 (behavior): "a new candidate on a problem with open criticisms must carry,
per criticism handle, a typed discharge: REVISED (what changed, where),
REBUTTED (why the criticism fails — itself attackable), or DEPARTURE-DECLARED
(the Rung 6 protocol; no penalty)."

R4 (behavior): "A submission with undischarged handles is returned ONCE with
the open list (a typed re-ask, not a repair grant), then accepted WITH a typed
undischarged disclosure — disclose, never die (the all-configurations law at
the submission boundary)."

R5 (artifact): "THE LAW LINE, stated in SPEC and pinned by test: discharge
constrains how content is GENERATED (a submission precondition), never what
counts as EVIDENCE — no discharge field ever feeds a label, a warrant, or
adjudication."

R6 (behavior): "a REBUTTED discharge is just a criticism artifact entering the
ordinary graph."

R7 (process): "Mutation-prove the boundary (wire a discharge into label
computation in a scratch copy, RED, restore)."

R8 (behavior): "Formalism-optional also binds: discharge kinds carry no rank
or admission weight."

R9 (process): "the coupling instrument from W2 (reuse its committed
operationalization R1) re-run on an OFFLINE stub-driven run with the channel on
vs off — coupling must be measurably nonzero with the channel on where the
stub's criticism names a mechanical respect."

R10 (process): "the disclosure road works; C3's mutation proof; no label
differs between channel-on and channel-off runs on the same graph. Full gate 0
failed; docs_verify full; map moves in the same commits."

R11 (behavior): "Q5's warning is BINDING: do NOT build an acknowledgment
requirement — ACK-required measurably HURT."

R12 (behavior, Amendment 1): "There needs to be a priority that enforces
modularity. Customisation needs to be easy." — bound to this tranche as:
"the discharge policy (kinds, the re-ask behavior, the disclosure road) is a
registered, config-selectable policy — new discharge kinds enter by
declaration, not by editing the submission path."

R13 (behavior, Amendment 1): "Every knob, policy, and behavior your tranche
introduces is reachable as CONFIGURATION or a REGISTERED VERSIONED ARTIFACT —
if customizing it would require editing code, the design is wrong; rework it
before implementing."

R14 (artifact, Amendment 1): "Your new machinery sits behind a DECLARED
INTERFACE on the signal-contract pattern (frozen protocol / versioned artifact
/ free parameters), and you ship an ARCHITECTURE TEST that goes RED when a
consumer bypasses the interface — a modularity claim without a failable check
is decoration."

R15 (process, Amendment 1): "At any design fork between a tighter coupling that
is smaller and a declared interface that is larger, the interface wins — the
operator has priced this and chosen."

R16 (process, Amendment 2): "GRANTED: the one-line versioned-source entry for
DISCHARGE_POLICY in run_manifest.py." With four riders, each a separate
obligation: (a) "SPEC.md records \"GRANTED 2026-08-26\""; (b) "the digest
before/after measurement (b9038b84... unchanged) is committed as pasted proof";
(c) "the map's frozen-surface document gains the contact line in the SAME
commit as the code"; (d) "the line exists for EVERY schema version the
serializer handles, not just the newest."

R17 (behavior, Amendment 2): "read C6 as \"F2's fields\" — that reading is the
intent." Resolves Q5/Q-OP-2: F1's two optional additive fields proceed.

R18 (artifact, Amendment 2): "The composition note (discharges[].handle
registering into F2's menu interface later) is exactly the modularity law
working — record it in SPEC so F2's window or a successor finds it."

R19 (process, Amendment 2): "one tranche, three commits, ~640 lines accepted …
The diff-budget discipline still applies at your stated ceiling — a typed STOP
if it grows beyond what SPEC now declares, not silent growth."

R20 (artifact, Amendment 2): "F1 claims DELIVERY, not response — the offline
gate proves the channel carries and the off-state cannot, RESULTS.md says a
live model's responsiveness is P2's question, and the parked four-arm A/B
remains the live proof."

R21 (process, Amendment 3): "900" — in answer to step 10's typed STOP, which
offered "(ii) Re-declare the ceiling at 900 and keep gating on it
(RECOMMENDED)", "(i) Trim to fit 640", and "(iii) Continue and disclose". The
operator chose (ii). The `src/` ceiling is **900**; `tools/diff_budget.py`
keeps gating on it at every `[COMMIT]` step, and R19's obligation is
UNCHANGED — a typed STOP if the tranche grows beyond 900, never a second
silent re-baseline.

R22 (process, Amendment 4): "raise approved. keep going" — in answer to the
second R19 STOP, raised when the SIGNAL CONTRACT (an operator design law of
2026-08-14) required three new `SignalDeclaration` entries and took `src/` to
943 against the 900 of R21. The ceiling is re-declared at **960**: the measured
943 plus a stated margin. R19's obligation is unchanged and now attaches to 960
— growth beyond it is a fresh typed STOP.


## Standing constraints

C1: "TARGET REPOSITORY: AHepi/DeepReason — verify before anything else" —
message 1. **Satisfied**: `origin` is `https://github.com/AHepi/DeepReason`,
verified before any other action.

C2: "Route through dr-change-orchestrator; the workflow's own stops apply." —
message 1.

C3: "Use `python -m pytest`, never bare pytest." — message 1.

C4: "Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator." —
message 1. **Satisfied** before this artifact was written.

C5: "Your blast radius: pack render sections, the submission path, discharge
records." — message 1.

C6: "If you need to edit wire-contract FIELD definitions (F2's) or Config
defaults (F3's), STOP and say so." — message 1.

C7: "SIZE: if SPEC exceeds ~700 lines of plan, STOP and say what grew." —
message 1.

C8: "Commit and push every phase boundary (retry 2s/4s/8s/16s)." — message 1.

C9: "F2 (wire-contract handle menus) and F3 (config defaults + allocation
policy) run in parallel." — message 1. Merge-surface hygiene binds: this
tranche must not gratuitously touch files F2/F3 own.

C10: The motivating evidence to cite: "W2's placebo-corrected coupling (zero or
negative; 0 of 92 coupled changes improved a score; NeglectRate 82-91%)" and
"docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md Q5". — message 1.
**Path correction, recorded rather than silently fixed:** message 1 cites
`experiments/2026-08-26-run-anatomy-program/W2*/RESULTS.md`. No `W2*`
subdirectory exists under `2026-08-26-run-anatomy-program/`; the W2 tranche is
its own sibling directory, `experiments/2026-08-26-run-anatomy-w2-criticism/`,
and that is the file cited throughout this tranche. The content is the one the
operator named (placebo-corrected coupling −12.7 / −1.9 / +5.9 / +0.0 pp;
0 of 32 + 0 of 60 = 0 of 92 coupled changes improved a score; NeglectRate
82.2% / 90.6%). Nothing about the instruction changes.

## Open questions (for dr-spec-change)

Q1: "INSIDE the conjecturer's working section of the pack (not a sidebar
section)" — the conjecturer pack has no section literally named "working";
which existing section (or new non-droppable section, and at what priority
relative to `problem`/`criteria`/`mandatory-interface`) counts as inside the
working section rather than a sidebar?

Q2: What makes a criticism "open" on the record — an `observe_only` scrutiny
Measure with no later discharge, an attack edge, or both? W2 establishes that
`observe_only` critic artifacts are the population that was never routed
anywhere.

Q3: What is the "stable discharge handle" keyed on, such that it survives
across cycles and across replay — the critic artifact id, a digest, or an
ordinal? R1 says "stable"; R2 says it must persist "every cycle until
discharged".

Q4: R3's discharge is per-candidate ("a new candidate ... must carry"), but R4's
re-ask is per-submission ("A submission with undischarged handles is returned
ONCE"). Does the ONCE count per turn, per problem, or per cycle?

Q5: R3 requires a typed discharge to arrive from the model. The conjecturer's
reply shape is a wire contract, and C6 reserves "wire-contract FIELD
definitions (F2's)". Is ADDING a new F1-owned field (as against editing an
existing F2-owned one) inside or outside C5's declared blast radius
("the submission path")?

Q6: R2 says the persistence rule is "asserted at terminal". Rung 6's terminal
assertion is over frame crisis sections. What is the terminal assertion for a
discharge handle — that every handle rendered at cycle N is either discharged
or still rendered at cycle N+1?

Q7: R9's "coupling must be measurably nonzero" — nonzero on which of W2's two
operationalizations, and against which placebo? W2 §residue item 1 rules R2
(prose-quote) inadmissible as a rate ("no discriminating power and must not be
quoted as a rate"), which leaves R1 (mechanical). The operator names "the
committed operationalization R1", consistent with that.

Q8: R12 says the policy is "config-selectable". A new `Config` field is
frozen-surface adjacent (`INV-frozen-surfaces` surfaces 4/5: every new
top-level `Config` field owes an explicit `_versioned_source_config_data` line
in `run_manifest.py`, per schema version, or every qualification subject digest
moves). C6 reserves "Config defaults (F3's)". Is a NEW F1-owned `Config` field
plus its versioned-source line inside this tranche, and is the frozen-surface
grant requested in SPEC.md per the standing discipline?

## Amendments

**Amendment 1 — 2026-08-26, mid-turn, before any artifact existed.**
Message 2 above, quoted verbatim in `## Verbatim`. Lands as R12, R13, R14, R15.
Supersedes nothing. Its own instruction — "Amend your REQUEST.md with it as a
requirement and let SPEC.md answer it explicitly" — makes SPEC.md's explicit
answer to R12–R15 a delivery obligation, reconciled in DELIVERY.md like any
other requirement.

**Amendment 2 — 2026-08-26, the grant.** Message 3 above, quoted verbatim in
`## Verbatim`. Lands as R16–R20. Resolves and CLOSES open questions Q5 (via
R17) and Q8 (via R16); SPEC.md's Q-OP-1, Q-OP-2 and Q-OP-3 are all answered.
Supersedes nothing. One clarification the operator added that is not a
requirement but is recorded so a later reader does not mistake it for silence:
"The upcoming P-C2 rematch will bear on it but does not replace P2's design" —
P2 stays parked as designed.

**Amendment 3 — 2026-08-26, the ceiling ruling.** Message 4 above, verbatim.
Lands as R21. Supersedes SPEC.md's declared `src/` ceiling of 640 with **900**;
supersedes nothing in R19, whose typed-STOP obligation now attaches to the new
number. Recorded because the operator's own words in Amendment 2 required it:
"a typed STOP if it grows beyond what SPEC now declares, not silent growth" —
the ruling is what makes 900 "what SPEC now declares", so the instrument stays
live rather than becoming a waiver.

**Amendment 4 — 2026-08-26, the second ceiling ruling.** Message 5 above,
verbatim. Lands as R22. Supersedes R21's 900 with **960**; supersedes nothing in
R19. The growth was not discretionary: `tests/test_signals.py::
test_every_emitted_signal_is_registered` refused the three Measures this channel
emits until each was DECLARED, which is the 2026-08-14 signal-registry law
working exactly as stated ("new setups add signals by declaration through this
typed channel"). The number is final rather than projected: the FULL gate was
run BEFORE the stop was raised (4225 passed, 6 skipped, 0 failed), so nothing
further forces a `src/` change.
