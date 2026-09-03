# Request: "using it as another type of scratchpad … a small SQL type language that another conjecturer or critic could search through"

Captured: 2026-09-03, from the executor-window instruction for this tranche,
which carries the operator's words verbatim and marks the monitor's reading
as separate. Phase 1 of a multi-phase change tranche.

Tranche: `experiments/2026-09-03-change-provenance-history-channel/`
Branch: `claude/executor-window-phase-1-s5ex6w`
Base: `2d84a86cd` (main).

---

## Map preflight (resolved before any design; every later phase starts here)

Resolved from `docs/map/INDEX.md`. Read in the mandated order — seams before
subsystems, `INV-frozen-surfaces.md` before designing anything.

**Frozen-surface authority (read first, always):**

- `DR-INV-frozen-surfaces` — the five surfaces, spanning seven paths.
  Forecast contacts for this tranche are recorded in the window instruction
  and re-stated under C7 below.

**Seams (read before either side):**

- `DR-SEAM-rules-x-scratch` — the conjecture/criticism sockets against the
  scratchpad. The operator's framing is "another type of scratchpad", so
  this seam is the primary one.
- `DR-SEAM-rules-x-workflow` — coupling 37, the highest in the tree. The
  context-expansion request path and the exposure receipt both live across
  it.
- `DR-SEAM-llm-x-rules` — pack rendering into a seat call.
- `DR-SEAM-scratch-x-workflow` — a scratch destination under transactional
  dispatch.
- `DR-SEAM-llm-x-manifest` — engaged only if the exposure policy is stamped
  into the manifest (a forecast frozen contact, C7).
- `DR-SEAM-llm-x-verification`, `DR-SEAM-harness-x-verification` — engaged
  only if a new typed record shape is proposed (a forecast frozen contact,
  C7).

**Concepts:**

- `DR-CON-conjecture-source` — `rules/conj.py`, the socket that proposes
  candidate artifacts; owner of the context-expansion request mechanism.
- `DR-CON-criticism-source` — `rules/crit.py`, the socket that attacks a
  target. R7's "criticism without fully understanding the reasoning" lands
  here.
- `DR-CON-packs-and-token-economy` — prompt construction, section
  allocation, budgets. M2's subject.
- `DR-CON-discharge-channel` — criticism in the writer's working context and
  what it takes to discharge it. The rebuttal/discharge history M3 exposes
  is this channel's record.
- `DR-CON-successor-questions` — the P9 plugin shape: a versioned,
  registered routing destination, off-by-default gate. The channel registry
  proposed under R2/R3 is asked to follow this shape.
- `DR-CON-seats` — `select_lease`, `EndpointLease`. "Per-seat" in the
  exposure policy means per SEAT INSTANCE, per the signal-contract law.
- `DR-CON-scheduler-ranking` — the seed question's rank-tie guarantee, cited
  because M1/M3 measure per problem and must not confound across problems.

**Subsystems:**

- `DR-SUB-scratch` — the imaginative workshop, declared
  `advisory_non_grounding`. The mini episode log is proposed as a registered
  destination here.
- `DR-SUB-rules` — conjecture, criticism, warrants, spawn, guards.
- `DR-SUB-workflow` — the v6 transactional work lifecycle; owner of
  `ContextExposureReceiptV2` / `workflow-context-exposure-v2`.
- `DR-SUB-llm` — adapter, packs, wire contracts, profiles.
- `DR-SUB-verification`, `DR-SUB-manifest` — **frozen**; touched only under
  a forecast, priced grant (C7).

**Invariants and recipes:**

- `DR-INV-render-layout` — where a rendered prompt puts what it carries.
  A new pack section must be placed by this policy, not ad hoc.
- `DR-INV-signal-contract` — the FROZEN / VERSIONED / FREE layering the
  channel registry is asked to follow.
- `DR-INV-evidence-channels` — the outside-reaching channels and the one
  field that turns any of them off; the exposure policy must not be confused
  with it.
- `DR-REC-change-a-seam` — the worked recipe for the seam changes above.

**Map gaps found at preflight (a finding, not a blocker):** there is no
`SEAM-rules-x-verification` and no `CON-provenance` document. If this tranche
proceeds to implementation, writing the covering document becomes part of it,
per `dr-drive-harness` §4.5.

**Two mechanisms the design leans on — confirmed present in the tree at base,
not assumed:**

- context-expansion requests: `src/deepreason/run_manifest.py:576`
  (`max_context_expansion_requests: int = Field(ge=0, le=8)`),
  `src/deepreason/rules/conj.py:344,2360,2373,2950`,
  `src/deepreason/v6_policy.py:79,129`.
- exposure receipts: `ContextExposureReceiptV2` registered as
  `workflow-context-exposure-v2` at `src/deepreason/harness.py:1071`,
  `src/deepreason/storage/objects.py:167`,
  `src/deepreason/workflow/replay.py:86,2419,2430`.

---

## Verbatim — the operator, 2026-09-03

Message 1 (the substantive suggestion):

> "I was actually thinking of something different. I was thinking of
>  using it as another type of scratchpad. Mini produces its own log. I
>  wanted to test a small SQL type language that another conjecturer or
>  critic could search through to get an idea of how a conjecture and
>  commitment battery were arrived at. And now that I think about it, a
>  conjecturer might find it helpful in building a commitment interface
>  after a mini run. What I realised is that conjectures themselves
>  usually have a long history, and understanding that history might help
>  LLMs craft better conjectures. the problem right now is the basin
>  attractor issue again. Solvable though.
>  The other thing I realised is that I've been modifying DeepReason
>  without testing the limits of context. I also realised that criticism
>  without fully understanding the reasoning behind a conjecture might
>  help sharpen critiques."

Message 2 (the follow-up, immediately after):

> "Is that with mini running in each conjecture run? Or are you thinking
>  something else? Either way, it's a good start so next prompt please"

Earlier, on the model-profile branch — quoted in
`experiments/2026-09-02-episode-config/CONFIG.md` and in
`experimental_mini_generator.py` on branch
`claude/model-profile-registry-opkgal`:

> "Mark this new configuration down as 'episode config'. An episode runs in
>  each mini run."

> "Mini is generator, playing the same role as thinking on even though
>  thinking must be off."

---

## Requirements

Every requirement carries the operator's own words. Where a requirement is
narrower than the quote, the quote is reproduced whole and the narrowing is
left to SPEC.md, where it is reviewable.

**R1 (behavior) — provenance history is a scratchpad-kind channel.**
> "I was actually thinking of something different. I was thinking of using
>  it as another type of scratchpad."

**R2 (behavior) — the mini episode log is one of the things in it.**
> "Mini produces its own log."

**R3 (behavior) — a small query language over that material, searchable by
another seat.**
> "I wanted to test a small SQL type language that another conjecturer or
>  critic could search through"

**R4 (behavior) — what the query is FOR: how a conjecture and a commitment
battery were arrived at.**
> "to get an idea of how a conjecture and commitment battery were arrived
>  at."

**R5 (behavior) — a conjecturer building a commitment interface after a mini
run is a named beneficiary.**
> "And now that I think about it, a conjecturer might find it helpful in
>  building a commitment interface after a mini run."

**R6 (behavior) — the motivating premise: conjectures have long histories,
and exposing that history is hypothesised to improve conjectures.**
> "What I realised is that conjectures themselves usually have a long
>  history, and understanding that history might help LLMs craft better
>  conjectures."

**R7 (behavior) — the counter-hypothesis the operator states in the same
breath: criticism WITHOUT the reasoning may sharpen critiques.**
> "I also realised that criticism without fully understanding the reasoning
>  behind a conjecture might help sharpen critiques."

Note, recorded here because it is a property of the operator's own words and
not an interpretation: R6 and R7 point in opposite directions — more history
for conjecturers, possibly less for critics. The operator states both without
resolving them. Which one binds which seat is Q1.

**R8 (constraint-on-design) — the basin attractor problem is named as the
present obstacle, and as solvable.**
> "the problem right now is the basin attractor issue again. Solvable
>  though."

**R9 (process/behavior) — the limits of context have not been tested, and
that is stated as a gap in how DeepReason has been modified.**
> "The other thing I realised is that I've been modifying DeepReason without
>  testing the limits of context."

**R10 (artifact) — "episode config" is the recorded name, and an episode runs
in each mini run.**
> "Mark this new configuration down as 'episode config'. An episode runs in
>  each mini run."

**R11 (behavior) — mini's role is GENERATOR, occupying the seat that
thinking-on would occupy, with thinking off.**
> "Mini is generator, playing the same role as thinking on even though
>  thinking must be off."

**R12 (process) — the operator asked for the next prompt and called the
direction a good start; the work continues rather than stopping for approval
of the direction itself.**
> "Either way, it's a good start so next prompt please"

---

## Standing constraints

Constraints C1–C6 are the operator's standing laws from CLAUDE.md; C7–C13 are
the window instruction that scopes THIS phase. Both bind; only C1–C6 are the
operator's own words.

**C1** (operator law, 2026-08-28, verbatim in CLAUDE.md):
> "My intention was that configuration of seats need to be able to turn gates
>  on and off at will. Meaning no limits to what model you place where. …
>  Gates are always optional: with warnings."

Binds R3/R7: whichever seat sees whichever channel must be switchable per
run, and switching one off emits a typed warning, never a refusal and never
silence.

**C2** (operator law, 2026-08-29, P9, verbatim in CLAUDE.md):
> "The scratch pad option must function like a plugin that allows for
>  movement elsewhere as well. Again, the modularity thing and Max config
>  thing."

Binds R1/R2: the destination is a versioned, registered routing point.

**C3** (operator law, 2026-08-26, verbatim in CLAUDE.md):
> "There needs to be a priority that enforces modularity. Customisation needs
>  to be easy."

**C4** (operator law, 2026-08-08, verbatim in CLAUDE.md):
> "Ollama API tokens are cheap, you are not. Running endless API experiments
>  is preferred if it means you do less work. Creating evidence from live
>  runs is preferred if it means less work."

Binds the whole of Phase 1: the three measurements precede the design.

**C5** (operator law, 2026-08-12, verbatim in CLAUDE.md):
> "All configurations should be allowed."

**C6** (operator law, 2026-08-13, verbatim in CLAUDE.md):
> "The flags and operations available to the newer reason runs should be
>  available to all configurations."

**C7** (window instruction — frozen surfaces, forecast not discovered):
> "a new typed event or object kind that replay validation must recognise is
>  surface 3 (verification/) contact → PRICED STOP; prefer existing
>  exposure-receipt and context-request shapes. run_manifest.py (4) if the
>  exposure policy is stamped into the manifest → PRICED STOP with the digest
>  price measured the compile-gap way. Nothing else expected. Committed roots
>  read-only."

**C8** (window instruction — phase boundary):
> "This phase ends at an APPROVED SPEC and PLAN: no production code is
>  written in this phase."

**C9** (window instruction — out of scope):
> "implementing the feature (Phase 2, after the operator approves SPEC.md and
>  CHECKLIST.md); the frontier, hv, transport, F4 tranches; merging anything
>  from the model-profile experiment branch."

**C10** (window instruction — measurement comparability):
> "Use the mini window's baseline model for comparability (qwen3.5:397b,
>  reasoning none, per its committed profile), the same seed question as
>  experiments/2026-09-02-full-harness-diversity/QUESTION.txt, and the
>  blind-judging protocol already committed at
>  experiments/2026-09-02-episode-config/JUDGING_PREREG.md … copy it, cite
>  it."

**C11** (window instruction — the D5 confound, a correction to prior work):
> "Diversity is measured PER PROBLEM (seed-question candidates only) — the
>  pooled D5 on that branch carries an unexamined cross-problem confound; do
>  not repeat it."

**C12** (window instruction — budget and credentials):
> "Budget ~3 M tokens across all three; one API key asked for at the launch
>  step, gitignored, never committed. Each measurement gets RESULTS.md with
>  the honest residue; an inconclusive result is recorded as one."

**C13** (window instruction — stop conditions):
> "the SPEC itself (this phase ends there); any M-result that contradicts the
>  monitor's reading above; any frozen contact; the default exposure for
>  critics if M3 is inconclusive."

---

## The monitor's reading (NOT the operator's words — kept separate by
## instruction, and reproduced verbatim so SPEC.md can be checked against it)

The window instruction states this as the monitor's reading, explicitly not
the operator's. It is recorded here because C13 makes it falsifiable: an
M-result that contradicts it is a stop condition.

> 1. A conjecture's history already exists on the record, typed: prompts,
>    episode pools, attacks, rebuttals/discharges, check verdicts,
>    revisions. What no seat can do is ASK. The feature is a QUERY SURFACE
>    over provenance, reachable through the existing context-request
>    mechanism (rules/conj.py, max_context_expansion_requests), with mini's
>    episode log as one registered channel among several.
> 2. "SQL type language" is realised as a CLOSED, VERSIONED vocabulary of
>    typed queries with bounded answers — lineage(X), attacks(X),
>    discharges(X), verdict_history(X), siblings(problem), episode_pool(X)
>    — never a free query string executed against a store. A model-
>    authored query that becomes code is the treadle rule's forbidden
>    shape. Deterministic, replayable, recorded as exposure receipts (the
>    workflow-context-exposure-v2 family already exists).
> 3. Which seat may see which channel is a PER-SEAT EXPOSURE POLICY,
>    configuration per run, typed disclosure when a channel is off. The
>    operator's hypothesis "criticism without the reasoning sharpens
>    critiques" is the CURRENT critic behaviour (critics see the target
>    whole, no history, no rebuttals) and must stay available as the
>    default; the known cost — re-raising answered objections — is met by
>    harness-side filtering of already-rebutted cases or by judge-side
>    exposure, not by informing the critic. Settle which by measurement.
> 4. Basin pull is met by SHAPING exposure: refuted lineages and failed
>    attacks are anti-attractor information; the winning lineage is
>    shown only on request. Measure it, do not assume it.
> 5. Episodes are orthogonal: a per-run switch (configuration, not the
>    env vars on the experiment branch). History works with them on or off.

---

## Pre-registered measurements (window instruction, verbatim)

These are obligations of THIS phase, ahead of SPEC.md. Reproduced verbatim so
that no later artifact can quietly re-scope them.

> M1 HISTORY ON/OFF for conjecturers: arm H0 = shipped pack; arm H1 = pack
>    plus a prototype history section rendered OFFLINE from the record
>    (refuted lineages + failed attacks on the problem's artifacts, capped;
>    no code in src/ — a script under the tranche directory that renders
>    the section and injects it via the existing scratch channel or a
>    pre-built pack file). 4 cycles each. Measure: per-problem D5, near-
>    duplicate rate, hv where measurable, blind-judged quality, tokens
>    per admitted artifact. Prediction registered before launch.
> M2 PACK BUDGET SWEEP: PACK_TOKEN_BUDGET at 2500 (shipped) / 6000 / 12000
>    / 24000, same seats, 2 cycles each. Measure blind-judged quality and
>    tokens per admitted artifact; record separately the share of each
>    prompt that is the JSON schema (P-A1: ~19k of 30k chars). This is
>    the "limits of context" the operator named; the schema-every-call
>    cost is a finding for SPEC.md, not a fix here.
> M3 CRITIC BLIND vs INFORMED: arm C0 = shipped critic pack; arm C1 =
>    critic pack plus the target's rebuttal/discharge history (offline
>    render, as M1). Measure: blind-judged case sharpness, rate of re-
>    raised already-rebutted objections, rate of cases the defender
>    sustains. Prediction registered before launch.

M1 answers R6 (does history help conjecturers). M3 answers R7 (does blindness
sharpen criticism). M2 answers R9 (the untested limits of context).

---

## What SPEC.md must state (window instruction, verbatim)

> the closed query vocabulary and its answer bounds; the channel registry
> (record-derived channels + mini episode log as a registered scratch
> destination per the P9 plugin shape); the per-seat exposure policy schema
> and its defaults (critic blind by default unless M3 says otherwise); how a
> query result is recorded (exposure receipt) and how it is bounded against
> the pack budget; the anti-attractor shaping rule; and the episode switch as
> configuration.

---

## Open questions (for dr-spec-change — NOT answered here)

**Q1.** R6 and R7 pull in opposite directions: history helps conjecturers,
blindness may sharpen critics. Does the exposure policy therefore default
asymmetrically (conjecturer informed, critic blind), and is that a default or
a law? M1 and M3 are the deciding instruments; C13 makes an inconclusive M3 a
stop.

**Q2.** R4 says "how a conjecture **and commitment battery** were arrived at."
"Commitment battery" is not a term the map or the code uses. Whether it names
the `Commitment` set attached to an artifact, the evaluation battery, or
something else is undetermined by the words. Resolve from the record and the
map before asking.

**Q3.** R5's "building a commitment interface after a mini run" — whether
"interface" here is the ontology's `Interface` type or the informal sense of
a hand-off surface is undetermined by the words.

**Q4.** R3 says "another conjecturer or critic could search through". Whether
the QUERY is issued by the seat mid-call (a context-expansion request, which
already exists) or rendered into the pack unasked is undetermined; the
monitor's reading picks the former. M1's H1 arm deliberately tests the LATTER
shape offline, so the two are not the same thing and SPEC.md must say which
it specifies.

**Q5.** R8 names the basin attractor problem as the obstacle but not the
remedy. The monitor's reading proposes anti-attractor shaping (refuted
lineages and failed attacks, winner on request only). M1 is the instrument;
whether it can decide the question at 4 cycles is itself uncertain.

**Q6.** R2's "Mini produces its own log" — on the model-profile branch that
log is `DEEPREASON_MINI_GENERATOR_TRACE`, a JSONL trace "self-metered outside
the harness's accounting" (`CONFIG.md`). Whether the registered channel reads
that trace shape, or requires the episode pool to become a first-class record
object, is undetermined and bears directly on C7's frozen-surface forecast.

**Q7.** R10/R11 arrived on a branch this tranche may not merge (C9). Whether
"episode config" is re-specified here as configuration, or deferred to the
phase that lands the mini generator, is undetermined.

---

## Amendments

(append-only; later operator messages land here as R13… or "R2a supersedes
R2", each with its verbatim quote)

---

### Amendment 1 — 2026-09-03, answering the Phase 1 stop

The monitor stopped and asked for exactly two things: an API key to run
M1/M2/M3, and a frozen-surface grant for the per-seat exposure policy as
`Config` fields under the documented digest-preserving recipe. The stop closed
with the monitor's own statement of what would follow: *"A 'yes' and a key is
enough; I'll run the measurements and bring you SPEC.md."*

The operator replied with a credential and then, verbatim:

> "make the changes and push. But never merge with main."

**The credential is NOT reproduced here.** REQUEST.md is a committed file and
this ledger's verbatim rule is not a licence to commit a secret. The key was
written to `experiments/2026-09-03-change-provenance-history-channel/env`,
which `git check-ignore` confirms is ignored by `.gitignore:50`
(`experiments/**/env`, the line this tranche added in its first commit), mode
600, and which `git status` does not see. This redaction is recorded rather
than performed silently, because a reader comparing the operator's message to
this file must be able to see that something was deliberately withheld and
why.

**R13 (process) — the new standing instruction, verbatim:**
> "But never merge with main."

Recorded as **C14** below rather than as a requirement about the feature: it
binds how this tranche is delivered, not what it builds.

**R14 (process) — the approval, verbatim:**
> "make the changes and push."

**How R14 is read, and the reading is stated here so it can be overruled
cheaply.** Under `dr-ask-the-right-question`'s operator-reading table, "do it"
after a stated plan is *approval of EXACTLY that plan* — never a licence to
widen. The plan stated in the stop was: run the three measurements, then bring
SPEC.md. So R14 authorises:

1. the frozen-surface grant that was asked for — two `Config` fields plus two
   `data.pop` lines in `_versioned_source_config_data`, insertions-only and
   digest-preserving, measured at `PRICE_EXPOSURE_POLICY.txt` (E1 moves the
   hash at all six schema versions without the pop; E2 is byte-identical with
   it). Recorded as **G1** below;
2. running M1, M2 and M3 against the pre-registered arms in `PREREG.md`;
3. writing SPEC.md and CHECKLIST.md and pushing them.

It does **not** authorise writing the feature's production code in this phase.
C8 (the window instruction) ends Phase 1 at an approved SPEC and PLAN, and C9
puts implementation in Phase 2 "after the operator approves SPEC.md and
CHECKLIST.md". Nothing in R14 mentions the spec, the checklist or the phase
boundary, and the sentence it answers said the deliverable would be SPEC.md.
Reading "make the changes" as "implement the feature now" would therefore
overturn two written constraints on the strength of three words that already
have a narrower reading fitting the exchange exactly. If the operator meant
the wider one, one word restores it and the grant G1 is already in hand.

**G1 — frozen-surface grant, GRANTED 2026-09-03 (surface 4, `run_manifest.py`).**
Scope: the per-seat exposure policy reaches a run as `Config` fields, popped in
`_versioned_source_config_data` so they never enter `engine_config_json`. This
is the recipe granted twice before on this surface — 2026-08-23 split-budget
knobs, 2026-08-26 F3 knobs — and its price was measured before the grant was
requested rather than after. The grant is for the SHAPE; the exact field names
and count are SPEC.md's to fix, and any departure from insertions-only or from
digest preservation is a fresh stop, not covered here.

**C14 (standing, this tranche and its successors) — verbatim:**
> "never merge with main"

Operational reading: work stays on `claude/executor-window-phase-1-s5ex6w`;
no merge of `main` into this branch and no merge of this branch into `main`.
This is compatible with, and stricter than, C9's existing prohibition on
merging the model-profile experiment branch. Rebasing, fast-forwarding and
cherry-picking are all forms of taking `main` into this branch and are treated
as covered by the same instruction; if a base move is ever needed it is a
question for the operator, not a judgement call.

