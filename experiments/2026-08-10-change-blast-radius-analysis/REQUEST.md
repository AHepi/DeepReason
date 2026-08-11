# Request: automatic blast radius analysis in the skills workflow

Captured: 2026-08-10, executor session, from the task-assignment message
opening this session.

## Verbatim

> Setup FIRST: git fetch origin main && git checkout -B claude/<your-branch-name> origin/main, verify git merge-base --is-ancestor 25686797 HEAD succeeds, preflight (which deepreason || pip install -e . --break-system-packages -q; pip install pytest pytest-xdist jsonschema --break-system-packages -q). THEN read CLAUDE.md (all Operator design laws bind), .claude/skills/dr-explain-to-operator/SKILL.md (Read tool, follow for every message), .claude/skills/README.md, and docs/ERRATA_EXECUTOR.md's 2026-08-09 entry — it is this tranche's origin incident.
>
> Route through dr-change-orchestrator from dr-capture-request; SPEC-AND-STOP, no code this window. The operator's verbatim words, the authority to ledger:
>
> I'm thinking of putting an automatic blast radius analysis in skills workflow. These drastic changes in code that hid legacy architecture was my fault. I authorised changes without fully understanding the implications. This frozen surface issue was also my fault since I wasn't aware of the potential scope creep.
>
> The capture must state the design's premise explicitly: the operator's self-assessment is ledgered as context, and the system's share is the design target — authorization requests that do not compute and present their own implication surface are the defect; the operator cannot be the blast-radius calculator for a 125k-line codebase. Three deliverable parts:
>
> Part 1 — census of existing practice and its failure cases. What blast-radius discipline exists today (the SPEC-phase blast-radius-census convention, tools/diff_budget.py and its skill checkpoints from the G1 tranche, the deterministic-gates pre-plan's G4/G5 designs, the errata checkpoint pattern in the closing skills) — and, from the record, every case where an AUTHORIZED change hid or disconnected architecture without the grant saying so: the frozen-surface incident (the errata entry), the legacy-criticism weld (one missing v6 contract silently made schools mandatory for criticism — the opt-in tranche's Road E finding), the dead circuits the liveness censuses found (property_designer, bias_probes, the judge machinery gaps), and any others a sweep of PARKED/ERRATA entries surfaces. For each: what was authorized, what the authorization request failed to disclose, and what a blast-radius computation at grant time WOULD have shown. This is the evidence base proving where the checkpoint belongs.
>
> Part 2 — the automatic blast-radius design. A deterministic tool (the gates pre-plan's shape rules bind: versioned typed result, exit classes, mutation-proven, map check: line) that, given a proposed change's declared target symbols/files, computes: frozen-surface contacts (all five, plus the frozen-adjacent list), reachability changes (dispatch paths that would become dead or newly-live — the property_designer/legacy-criticism failure class), consumers of every touched symbol (tests, map checks, qualification digests, wheel-smoke pins), and the disclosure summary in operator terms. Then the skill checkpoints, each mandatory and state-not-silence like the errata checkpoint: at dr-spec-change (the census section becomes tool-backed, pasted result required); at grant-request time — the load-bearing one: any frozen-surface or scope grant request presented to the operator MUST embed the tool's computed contact list, so the words they give are words over a disclosed surface, never an inferred one; at dr-execute-step commits (actual-touch drift vs specced radius; drift = STOP, the same shape as diff_budget's EXCEEDED). R-g and the solo law bind anything the tool weights or reports.
>
> Part 3 — the hidden-legacy inventory. Consolidate Part 1's cases plus a targeted sweep into one honest inventory document: every piece of designed architecture currently disconnected/buried by later authorized changes, each with its disconnection commit or mechanism where traceable, so the operator can decide re-connection priorities from a single page instead of archaeology-per-incident.
>
> Frozen-surface forecast from scratch (expect none — tools/ and skills only; any src/ contact is a STOP). Decision sheet priced with recommendations. Commit and push REQUEST.md and SPEC.md, then STOP for operator words.

## Design premise (stated explicitly, per the task-assignment message's own instruction)

The task-assignment message requires this premise to be ledgered, not
interpreted: the operator's self-assessment quoted below is captured as
CONTEXT for why this tranche exists, not as a requirement to satisfy by
making the operator more careful. The requirement the system must meet is
the opposite move — an authorization request is defective if it does not
itself compute and present the implication surface (frozen-surface
contacts, dead/newly-live dispatch paths, consumers) it is asking the
operator to approve. The operator is not expected to be, and this design
must not require them to act as, the blast-radius calculator for a
125,000-line codebase (per CLAUDE.md's own line count). This premise binds
Part 2's design and both grant-request checkpoints.

## Operator self-assessment (ledgered verbatim as context, per the premise above)

> These drastic changes in code that hid legacy architecture was my
> fault. I authorised changes without fully understanding the
> implications. This frozen surface issue was also my fault since I
> wasn't aware of the potential scope creep.

## Requirements

R1 (artifact): "I'm thinking of putting an automatic blast radius
analysis in skills workflow." — the headline request: an automatic
blast-radius analysis, integrated into the skills workflow (the
`.claude/skills/` change and diagnosis families), not a one-off report.

R2 (process): "The capture must state the design's premise explicitly:
the operator's self-assessment is ledgered as context, and the system's
share is the design target — authorization requests that do not compute
and present their own implication surface are the defect; the operator
cannot be the blast-radius calculator for a 125k-line codebase." —
binding statement of what the design must optimize for; see "Design
premise" above.

R3 (artifact): "Part 1 — census of existing practice and its failure
cases." Must cover, verbatim-named: "the SPEC-phase blast-radius-census
convention, tools/diff_budget.py and its skill checkpoints from the G1
tranche, the deterministic-gates pre-plan's G4/G5 designs, the errata
checkpoint pattern in the closing skills"; and, "from the record, every
case where an AUTHORIZED change hid or disconnected architecture without
the grant saying so": "the frozen-surface incident (the errata entry),
the legacy-criticism weld (one missing v6 contract silently made schools
mandatory for criticism — the opt-in tranche's Road E finding), the dead
circuits the liveness censuses found (property_designer, bias_probes, the
judge machinery gaps), and any others a sweep of PARKED/ERRATA entries
surfaces." For each case: "what was authorized, what the authorization
request failed to disclose, and what a blast-radius computation at grant
time WOULD have shown." Named purpose: "the evidence base proving where
the checkpoint belongs."

R4 (artifact): "Part 2 — the automatic blast-radius design." Must be "A
deterministic tool (the gates pre-plan's shape rules bind: versioned
typed result, exit classes, mutation-proven, map check: line) that,
given a proposed change's declared target symbols/files, computes:
frozen-surface contacts (all five, plus the frozen-adjacent list),
reachability changes (dispatch paths that would become dead or
newly-live — the property_designer/legacy-criticism failure class),
consumers of every touched symbol (tests, map checks, qualification
digests, wheel-smoke pins), and the disclosure summary in operator
terms." Then "the skill checkpoints, each mandatory and state-not-silence
like the errata checkpoint": three named checkpoint sites — "at
dr-spec-change (the census section becomes tool-backed, pasted result
required)"; "at grant-request time — the load-bearing one: any
frozen-surface or scope grant request presented to the operator MUST
embed the tool's computed contact list, so the words they give are words
over a disclosed surface, never an inferred one"; "at dr-execute-step
commits (actual-touch drift vs specced radius; drift = STOP, the same
shape as diff_budget's EXCEEDED)." Binding constraint: "R-g and the solo
law bind anything the tool weights or reports."

R5 (artifact): "Part 3 — the hidden-legacy inventory. Consolidate Part
1's cases plus a targeted sweep into one honest inventory document:
every piece of designed architecture currently disconnected/buried by
later authorized changes, each with its disconnection commit or
mechanism where traceable, so the operator can decide re-connection
priorities from a single page instead of archaeology-per-incident."

## Standing constraints

C1: "Setup FIRST: git fetch origin main && git checkout -B
claude/<your-branch-name> origin/main, verify git merge-base
--is-ancestor 25686797 HEAD succeeds, preflight (which deepreason || pip
install -e . --break-system-packages -q; pip install pytest
pytest-xdist jsonschema --break-system-packages -q)." — session preflight,
completed before this document.

C2: "THEN read CLAUDE.md (all Operator design laws bind),
.claude/skills/dr-explain-to-operator/SKILL.md (Read tool, follow for
every message), .claude/skills/README.md, and docs/ERRATA_EXECUTOR.md's
2026-08-09 entry — it is this tranche's origin incident." — completed
before this document; the 2026-08-09 entry (surface 3 modified with
Amendments reading "(none yet)") is this tranche's origin incident and is
the primary evidence item for Part 1's checkpoint-placement case.

C3: "Route through dr-change-orchestrator from dr-capture-request;
SPEC-AND-STOP, no code this window." — this tranche stops after SPEC.md;
no CHECKLIST.md, no dr-execute-step, no code or skill-file edits this
window.

C4: "Frozen-surface forecast from scratch (expect none — tools/ and
skills only; any src/ contact is a STOP)." — the census in SPEC.md must
re-derive the frozen-surface forecast against `INV-frozen-surfaces.md`
rather than assume the operator's "expect none"; any `src/` contact found
is a STOP, not a proceed-with-note.

C5: "Decision sheet priced with recommendations." — SPEC.md (or an
attached decision sheet) must present forks in cost/benefit terms with an
explicit recommendation, not just options.

C6: "Commit and push REQUEST.md and SPEC.md, then STOP for operator
words." — the tranche's exit action.

C7 (from CLAUDE.md, standing): "All Operator design laws bind" —
R-g (formalism is never an obligation and never a penalty), the
seats/packages guardrail (no seat may let prose skip criticism), the
solo law (sole-model operation may never be structurally locked out of
any harness capability, including status-changing criticism; judge
seats are suspect-by-default), and "tokens are cheap; the agent is not"
(prefer live/API evidence over hand-built machinery) all bind Part 2's
design, per R4's explicit callout of "R-g and the solo law."

## Open questions (for dr-spec-change)

Q1: "Any others a sweep of PARKED/ERRATA entries surfaces" (R3) is
open-ended — dr-spec-change must bound how many tranches/PARKED.md files
the sweep covers and state that bound explicitly, since "every" is not
literally achievable for a 125k-line, many-tranche record without a
declared search method.

Q2: R4 names the tool's four computations and three checkpoints but does
not specify the CLI invocation shape, the map document(s) that gain
`check:` lines, or which existing skill files (dr-spec-change,
dr-capture-request/grant-request path, dr-execute-step) receive the
amendment text — dr-spec-change must decide and record these as
assumptions.

Q3: "Declared target symbols/files" (R4) as the tool's input does not
say who declares them or at what granularity (function-level, file-level,
or both) — dr-spec-change must fix this.

Q4: R5's "one honest inventory document" does not name a filename or
location (tranche-local vs. repo-wide docs/ location) — dr-spec-change
must decide and record the choice as an assumption, consistent with
CLAUDE.md's convention that tranche narrative lives under
`experiments/<tranche>/`.

Q5: The verbatim request does not state whether Part 2's tool is
IMPLEMENTED this tranche or only DESIGNED — SPEC-AND-STOP (C3) resolves
this: design only, no code, this window. dr-spec-change must state this
explicitly rather than leave it inferred from C3 alone, since Part 2's
prose ("A deterministic tool ... that ... computes") reads like a
finished-tool description.

## Amendments

**Amendment 1** (2026-08-10, operator, in response to SPEC.md's Decision
sheet): "Go"

R6 (process): the operator's one-word reply to a message that (a)
summarized SPEC.md's five forks (F1-F5) each with a stated
recommendation, and (b) explicitly asked "say 'go ahead' and I'll build
it, or redirect any of the five." Read per `dr-ask-the-right-question`
section 2's own table ("'Do it' / 'go ahead' after you stated a plan" →
"approval of EXACTLY that plan," not "a new vague instruction; license
to widen"): approval of SPEC.md's Decision sheet exactly as recommended
— Fork F1 Road B (AST-based reachability), Fork F2 Road A (amend
`DETERMINISTIC_GATES_PREPLAN.md` as Rung G6), Fork F3 Road A (Checkpoint
2 bounded to `dr-spec-change` + `dr-ask-the-right-question`), Fork F4
Road B (promote `HIDDEN_LEGACY_INVENTORY.md` to a `docs/`-level standing
reference), Fork F5 Road B (no re-connection ranking/recommendation
engine). Authorizes `dr-plan-steps` to proceed from SPEC.md as amended.
No frozen surface is touched by this amendment or by SPEC.md's own
forecast (checked, none) — this is a process authorization, not a
frozen-surface grant, so no separate frozen-surface wording is required
of it.
