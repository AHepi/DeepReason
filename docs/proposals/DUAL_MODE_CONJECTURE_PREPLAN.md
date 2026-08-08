# Pre-plan: dual-mode conjecture (informal + formal) and the load dials

Status: PROPOSED — takes priority per the operator's own rule below.
Written 2026-08-08 by the monitor session. Absorbs
`CODER_AS_TOOL_PREPLAN.md` (its delegation seam becomes this program's
formal-submission mechanism). Authority is the operator's words,
verbatim:

> As long as this doesn't kill informal conjecture and criticism and
> there is an option to submit both in the official epistemology
> loop. And that there's a signal that can verify which kind of
> conjecture is being committed and a mechanism that submits the
> correct type of form so that the critic can't become too zealous
> and harsh when it's uncalled for.
>
> Actually, I just realised the conjecturer also needs the option to
> submit both without disincentivising formal submissions when it
> implies. If this setup doesn't exist, this takes priority. And then
> engineering a mechanism that can turn the dials up and down on:
> conjecture vs criticism load, scratchpad load, simulation load and
> coding load. Meaning which gets priority and by how much. The
> architecture has started, but it needs more engineering.

Requirements, numbered from those words:

- R-a: informal conjecture and criticism survive untouched — the
  default loop is not weakened or gated.
- R-b: the conjecturer has the OPTION to submit a conjecture in both
  forms — informal claim and formal (executable/machine-checkable)
  encoding — into the official epistemology loop.
- R-c: a verifiable, typed signal says which kind each committed
  conjecture is.
- R-d: criticism arrives on the form matched to the kind — an
  informal conjecture is never attacked with formal-grade demands
  ("too zealous and harsh when it's uncalled for"), and a formal one
  gets mechanical recourse first.
- R-e: submitting formally is never disincentivised when the
  conjecture implies a testable form.
- R-f: a load-dial mechanism — operator-settable priority and share
  for conjecture vs criticism load, scratchpad load, simulation load,
  and coding load.

## What exists today (verified against the tree, 2026-08-08)

- **Informal loop: healthy (R-a's baseline).** Prose conjecture →
  argued criticism governed by `config.ARGUMENTATIVE_AUTHORITY`
  (`observe_only` records scrutiny; `trial_required` routes through
  the defended cross-family trial — critic drafts, defender answers,
  judge rules a narrow question, program checks screen the ruling; "no
  configuration may grant a self-certifying prose warrant",
  `rules/crit.py` header). The anti-zealotry machinery for VERDICTS
  exists; what R-d adds is form-matching at attack time, not a new
  guard at verdict time.
- **The kind signal exists structurally but not as a submission-time
  option.** An artifact whose interface carries program-eval'd
  commitments IS formal (crit_program runs it mechanically); one
  without is informal (crit_argumentative under authority modes). The
  distinction is real and typed — but only capability channels and
  internal experiment harnesses ever attach executable commitments.
- **The live conjecturer cannot submit formal at all (R-b fails
  today).** `ConjectureCandidate` (`llm/contracts.py:35`) has
  `content`, `typicality`, `refs`, `evidence_refs` — no commitment
  channel of any kind. The S1 census (M18/M19) confirms all
  executable authoring on the live path is the conjecturer's own
  prose-channel output via the stochastic capability channel; the one
  coding role is unreachable (S6 PARKED P1).
- **The disincentive is concrete (R-e fails today).** A violated
  property on an execution-backed artifact registers a DEMONSTRATIVE
  fail warrant against THE ARTIFACT (`rules/crit.py:805-812`) — the
  idea dies with its encoding. Both cycle-0 run deaths (turmite,
  jolt) were encoding failures by a reasoning model. Today, going
  formal buys refutation-by-typo risk with no offsetting mechanism;
  any rational conjecturer stays informal.
- **The dials exist as scattered knobs (R-f's "architecture has
  started").** `PROP_PROPOSE_PERIOD`, `FUZZ_N`, `PACK_TOKEN_BUDGET`,
  per-capability budgets (simulation/research request ceilings), the
  V6 policy preset's fixed cycle/token ceilings, `criticism_policy`
  coverage minima, scratch attention budgets — real levers, no
  unified surface, no priority semantics, no operator-facing
  "which gets more and by how much".

## The design seed (D2 decides, with measurements; recorded here so
## the intent is not re-derived)

**Twin artifacts.** A dual submission is TWO linked artifacts: the
informal claim (prose, criticized under the informal rules as today)
and its formal encoding (carrying the executable commitment,
criticized mechanically). The link is typed and directional
("encodes"). A DEMONSTRATIVE refutation of the ENCODING kills the
encoding only: the claim reverts to informal standing with a typed
mark ("formal twin refuted at encoding — repairable"), and the repair
path (re-encoding) is exactly where the coder seat serves as the
tool — a coding-strong model re-authors the encoding without touching
the claim. Refutation of the CLAIM through its encoding requires the
encoding to be conceded faithful (or to survive its own criticism),
so a formal submission's downside is bounded at "lost encoding, kept
claim" while its upside remains demonstrative support. That is the
non-disincentive mechanism R-e requires, and it is the reason
coder-as-tool is absorbed here rather than standing alone: delegated
authoring is what makes the formal channel cheap enough to use.

**Kind-matched criticism (R-d).** The critic pack renders the target's
kind from its commitments (the R-c signal); the critic's own contract
form follows: counterexample channel only against execution-backed
targets (already true), argued-case-only against informal targets
(already governed), and — new — an informal target's pack never
demands executable grounds, while a formal target's mechanical
verdicts come before any argued case is mounted.

## The ladder

### Rung D1 — pipeline census  [MEASURE ONLY, no code]
Absorbs coder-as-tool T1. Enumerate: every path by which an artifact
acquires an executable commitment today (capability channel,
lambda_run, the dead property path); the exact criticism dispatch per
kind (crit_program vs crit_argumentative selection logic, pack
rendering — what the critic SEES about a target's kind); the
refutation semantics per kind (what dies when a property fails, what
the trial can and cannot do to prose); the full inventory of load
knobs (name, location, unit, current default, mint-time vs
label-time). Historical: encoding-failure evidence from committed
roots (cycle-0 blobs; capability-channel validation failures).
Deliverable: measured table + `docs/map/CON-conjecture-kinds.md`.
Accept: every claim carries a pasted command; docs_verify green.

### Rung D2 — dual-mode design  [DESIGN-AND-STOP]
The twin-artifact shape, the submission-time option (the
`ConjectureCandidate` contract gains an OPTIONAL formal-encoding
channel — absence means today's behavior byte-identically, R-a), the
typed kind signal and link (R-c), kind-matched packs and contract
forms (R-d), the bounded-downside refutation semantics (R-e), and the
coder-seat delegation as the encoding author when bound (the absorbed
T2). Every decision priced from D1's measurements. Frozen-surface
forecast expected non-trivial: contract changes touch the wire/pack
surface (qualification subject digests — surface 5) and new typed
records touch event schemas; every contact named, none assumed,
operator words before D3. STOP.

### Rung D3 — implement dual-mode  [EXECUTE, after D2 approval]
Reader-before-writer for every new typed record; contract fence;
writer last; sweep probe separate; default path byte-identical when
the option is unused; full gate; map in the same commit. The offline
regression must include: informal-only run unchanged (byte-level),
dual submission criticized on both tracks, encoding refutation
leaving the claim standing with the typed mark, coder-seat
re-authoring when bound.

### Rung D4 — the load dials  [DESIGN-AND-STOP, then EXECUTE]
One typed load-mix policy: weights/priorities for {conjecture,
criticism, scratchpad, simulation, coding} — which gets budget and
scheduling priority, and by how much. Frozen at mint time into the
manifest (the rung-7 placement law: a continuation continues under
the mix it was minted with), surfaced as named presets
(BEHAVIOR_MODES_PREPLAN's modes; S7's packages consume these later).
D1's knob inventory decides what the weights actually drive (rank
re-weighting, per-role call ceilings, capability grant budgets,
scratch attention share). Scheduler selection policy is
operator-approval territory: SPEC stops for words before code.
Accept for the eventual fix: two runs differing only in the mix show
the predicted call-share shift from typed attempt records; a
no-mix-specified run is byte-identical to today.

### Rung D5 — live demonstration + research data  [LIVE A/B]
Absorbs T4. Abstract-strong conjecturer + coding-strong coder seat,
dual-mode on: measure formal-submission rate, encoding survival rate,
claim survival after encoding refutation, and the load-mix compliance
— from typed outcomes only. Feeds the criticism-symmetry program's
roster logic and the operator's model-role fit thesis alongside S6's
throughput signal.

## Priority and sequencing

Per the operator: this program takes priority. L1 (the continue-crash
fix from RECORD_LIFECYCLE_DEFECT_PLAN.md) remains the one item that
runs BEFORE/alongside D1 — it is small, fixture-ready, and every live
rung here depends on `continue` being trustworthy. Then D1 → D2
(STOP) → D3 → D4 (STOP, then execute) → D5. L3 (seat bindings in run
identity) slots into any gap; S4b and the criticism-symmetry program
queue behind D5 and consume its data.
