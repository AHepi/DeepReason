# Census: existing blast-radius discipline and its failure cases

Traces: R3. Cited by M-number from `SPEC.md`, per the D1/D2 pipeline
tranches' own precedent (`experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md`
cited by `experiments/2026-08-08-change-pipeline-design-d2/SPEC.md`).

This document answers one question: what blast-radius discipline already
exists in DeepReason, and every recorded case where it did not stop an
authorized change from hiding or disconnecting architecture without the
authorization request saying so. It is the evidence base for Part 2's
design — where the automatic checkpoint belongs is decided from what is
listed here, not asserted.

## Part A — existing blast-radius discipline

### A1. The SPEC-phase "blast-radius census" convention (manual, prose)

`.claude/skills/dr-spec-change/SKILL.md` step 4, "Blast-radius census —
mandatory, pasted, BEFORE any fixture-drift prediction":

> For every symbol and file the spec changes, grep what already asserts
> on it: `grep -rn "<symbol>" tests/ docs/map/`. Paste the hit list (or
> "no hits") into SPEC.md's "Blast-radius census" section and classify
> EVERY hit: EXPECTED TO MOVE (the design predicts it) or MUST NOT MOVE.

This is entirely a HAND-RUN discipline: the author of SPEC.md chooses
which symbols to grep, runs the grep, and classifies the hits by
judgment. Nothing mechanizes the choice of which symbols to check, and
nothing catches an author who forgets to grep a symbol they touch.

Sixteen `SPEC.md` files across the tranche history contain a completed
"## Blast-radius census" section. Two representative examples:

```
experiments/2026-08-08-change-rung-g1-actual-diff-budget/SPEC.md:
`grep -rn "diff_budget" tests/ docs/map/ .claude/skills/` -> no hits
(new symbol; the new test file and map subsection introduce the only
references).
`grep -rn "INV-frozen-surfaces" tests/ docs/map/` -> 18 hits, all
`DR-INV-frozen-surfaces` cross-links from other map documents -> MUST
NOT MOVE, and none do.

experiments/2026-08-08-change-load-dials-d4/SPEC.md:
$ grep -rl "schema_version == 6\|schema_version=6" tests/ | wc -l
40
-> classified EXPECTED TO MOVE (with reasoning); a second grep over
canonical-hash symbols classified MUST NOT MOVE for existing pinned
hashes, EXPECTED TO MOVE only for genuinely new goldens.
```

The convention works when applied — but it depends entirely on the
author choosing the right symbol set. Nothing computes "what symbols did
this change actually touch" or "what surfaces does this file belong to"
on the author's behalf.

### A2. The frozen-surface contact forecast convention (manual, prose)

Same skill, step 3: "Diff the planned target files against
`docs/map/INV-frozen-surfaces.md`'s surface list and record the verdict
... ANY plausible contact stops the tranche HERE." This step is also
hand-run: the author reads the five-surface list and compares it by eye
against their own planned target files. `INV-frozen-surfaces.md` itself
is a plain-prose enumeration with `check:` lines that verify the
document's OWN claims about the code (e.g. `grep -q "class Harness"
src/deepreason/harness.py`) — it has no mechanism that checks a
PROPOSED change's target list against itself. The check exists to keep
the document honest, not to compute contact for a new tranche.

### A3. `tools/diff_budget.py` — the one mechanized gate that exists today

`tools/diff_budget.py` (229 lines) computes actual cumulative
`git diff --numstat` insertions against a ledgered ceiling, emitting
`DIFF_BUDGET_RESULT_V1`:

```json
{"result_type": "DIFF_BUDGET_RESULT_V1", "base": "...", "against": "...",
 "areas": {"<path>": N, "total": N}, "total_insertions": N,
 "ceiling": N, "verdict": "WITHIN" | "EXCEEDED" | "NO_CEILING"}
```

Exit classes: `0` result emitted (regardless of verdict), `2` invalid
invocation, `3` evidence unavailable (bad ref / not a git tree). Has a
built-in `--self-test` fixture harness. Wired into two skill checkpoints:

- `dr-spec-change` step 6: the Budget section's headline number must be
  the computed sum of its itemization, pasted, "never restated by hand."
- `dr-execute-step` step 6: runs at every `[COMMIT]` step; `EXCEEDED` is
  a STOP in the standard priced-options format, never a footnote.

This is the ONLY one of the five dimensions this tranche cares about
(line-count budget) that is fully mechanized end to end: typed result,
two named checkpoints, mutation-tested. It measures how MUCH changed. It
has no opinion on WHAT changed, which surfaces it touched, or who
depends on it — that gap is exactly what Parts 1-2 of this tranche are
about.

### A4. The deterministic-gates pre-plan (`docs/proposals/DETERMINISTIC_GATES_PREPLAN.md`)

Status: PROPOSED, five rungs, shape rules bind all of them:

> Gates live in `tools/`, never `src/`... Every gate consumes explicit
> inputs and emits a versioned typed result (`*_RESULT_V1` JSON): stable
> exit classes distinguish "result emitted" / "invalid invocation" /
> "evidence unavailable"; semantic verdicts live INSIDE the result...
> Each gate ships with its own mutation proof... and a `check:` line in
> the relevant map document... The ledger above is closed at five; a
> sixth gate requires its own recorded-failure citation and an operator
> word, same as a frozen surface.

Ladder status as of this tranche: **G1 (diff budget) is the only rung
actually built** — confirmed by `tools/diff_budget.py` existing and
being wired into two skills (A3 above). G2 (mutation attestation), G3
(evidence-population manifest), G4 (final-tree evidence gate), G5
(premise-currency preflight) are all still PROPOSED; none of their tools
(`tools/mutation_attest.py`, `tools/census_manifest.py`,
`tools/delivery_evidence.py`, `tools/premise_currency.py`) exist in the
tree.

**G4 and G5, checked specifically against this tranche's need (they do
not fill it):**

- G4 ("final-tree evidence gate") re-verifies that OWED INSTRUMENTS
  (gate runs, docs_verify, sweeps, the frozen-surface diff) were
  captured at the delivery commit and are not stale relative to later
  commits. It is a TEMPORAL check — was this evidence captured at the
  right commit — not a spatial/dependency one. It explicitly lists
  "frozen-surface diff" as one of the instruments it re-verifies for
  staleness, but computing that diff's CONTENT is not its job.
- G5 ("premise-currency preflight") verifies that a cited premise
  (a named symbol, failing test, or file:line anchor a tranche is BUILT
  ON) still holds at current head — CURRENT / MOVED / REFUTED /
  UNVERIFIABLE. It answers "does my starting assumption still exist,"
  not "what does my proposed change put at risk."

Neither G4 nor G5 is a frozen-surface-contact detector, a
reachability/dead-code analyzer, or a consumer/dependent finder. The
pre-plan's own "Parked" section names three other deferred ideas (skill
forward-testing, instrument-stage runner, check-registration audit) —
a mechanized blast-radius tool is not among them; it has no existing
home in this pre-plan and would be a genuinely new, sixth rung, which
the pre-plan's own rule requires "its own recorded-failure citation and
an operator word" to add. This tranche's origin incident
(`docs/ERRATA_EXECUTOR.md`'s 2026-08-09 entry) and this REQUEST.md are
exactly that citation and that word.

### A5. The errata "state-not-silence" checkpoint pattern

Three closing-skill checkpoints share one shape: an explicit, written
verdict is mandatory even when the answer is "nothing to report" —
silence is never an acceptable substitute for a stated "none."

- `dr-validate-change` step 4a2: "Frozen-surface diff — paste it, empty
  or explained... Empty output is the expected result and is pasted as
  proof. Non-empty output is a FAIL unless REQUEST.md quotes the
  operator approving that exact surface."
- `dr-deliver-change` step 3c: "Errata check — mandatory, before
  DELIVERY.md is committed... If no [correction found], state 'errata:
  none' explicitly in DELIVERY.md's Errata section — state it, do not
  omit the section."
- `dr-deliver-change` step 3b (the map-delta sibling): "'No map change'
  is a legitimate answer for a tranche that changed no behaviour — say
  it rather than omitting the section, so its absence is never
  ambiguous."

This is the precedent Part 2's checkpoints are modeled on: a checkpoint
that can return "clear" is legitimate; a checkpoint that can be SKIPPED
is not.

### A6. `docs/map/INV-frozen-surfaces.md` and the `check:` line convention

The five frozen surfaces, verbatim, each with its own `check:` line
(`docs/map/INV-frozen-surfaces.md`):

1. `capabilities/state.py` — digests and event application.
   `check: grep -q "def " src/deepreason/capabilities/state.py`
2. `harness.py` — event application and well-formedness.
   `check: grep -q "class Harness" src/deepreason/harness.py`
3. Replay-validation record formats — `invariants.py`, `verification/`.
   `check: grep -q "def verify_root" src/deepreason/invariants.py`
4. Manifest schemas AND their validators — `run_manifest.py`. Two
   checks (one per the "reading a model and not its validator" trap).
5. Anything altering qualification subject digests — `qualification.py`.
   `check: grep -q "def qualification_subject_payload" src/deepreason/qualification.py`

Frozen-adjacent (one entry, found by falsification): `route_fingerprint`
in `llm/firewall.py` — "the v6 behavioral gate compares stored route
digests against `route_fingerprint(route)`'s exact serialization... Treat
its output format as frozen."

`docs/map/SCHEMA.md`'s `check:` convention: a claim sentence followed,
at column 0, by a line beginning `check: <shell command>`; exit 0 means
the claim holds. Column 0 is what lets a document quote an EXAMPLE check
inside an indented block without `tools/docs_verify.py` executing it.
`docs_verify.py` has four modes: plain (every check), `--audit` (flags
vacuous/unfailable checks), `--links` (every `DR-` cross-reference
resolves), `--stale` (advisory, lists documents whose `Owns:` files
changed since `Verified-at`).

**Load-bearing gap for Part 2:** `INV-frozen-surfaces.md` does not itself
contain a Traps entry for the 2026-08-09 incident (surface 3) — that
incident lives only in `docs/ERRATA_EXECUTOR.md`. The document's own
Traps-entry convention ("never deleted, only rewritten to say when it
was fixed") has not yet been applied to this tranche's own origin
incident.

## Part B — failure cases: authorized changes that hid or disconnected architecture without the grant saying so

Each case states (a) what was authorized, verbatim where the record
allows it, (b) what the authorization failed to disclose, (c) what a
blast-radius computation at grant time would have shown.

### B1. The frozen-surface stop that did not hold (2026-08-09)

Already fully ledgered in `docs/ERRATA_EXECUTOR.md`'s final entry — this
tranche's own origin incident, read in full at session preflight.

- (a) Authorized: "fix dual seat wiring and test with a short live run"
  (the operator's five words, read as scope covering `run_manifest.py`,
  the surface REQUEST.md's C1 named explicitly).
- (b) Undisclosed: the same fix also widened `invariants.py` (surface 3,
  "Replay-validation record formats") to accept a new contract version
  id, committed (`d5f47101a`) with REQUEST.md's own Amendments section
  still reading "(none yet)." The SPEC.md census for that tranche had
  correctly IDENTIFIED surface 3 as plausible contact and said so in
  writing — the STOP that the identification should have triggered did
  not happen.
- (c) A blast-radius computation at grant time would have shown: surface
  3 contact, PRESENT, unauthorized — the same fact the tranche's own
  SPEC.md already stated in prose. The gap was not detection (the census
  correctly found it); the gap was that the finding did not force a stop
  before the commit landed. This is the single strongest argument for
  Part 2's third checkpoint (drift vs. specced radius, enforced
  mechanically at `dr-execute-step` commit time, not left to the
  author's own memory of what SPEC.md said three steps earlier).

### B2. The legacy-criticism weld, layer 1 — escape hatches promised, then discarded (2026-07-14)

Commit `83509657`, message "Make informal text adjudication advisory by
default": "advisory by default" and "Direct helper status modes and
legacy v1 routes remain explicit compatibility escape hatches."

- (a) Authorized: a DEFAULT, with named escape hatches remaining.
- (b) Undisclosed: `authority.py::trial_authority_for` computed a `mode`
  value and then discarded it, hard-returning `OBSERVE_ONLY`
  unconditionally for every text workload — the escape hatches the
  commit message promised did not exist in the code it described.
  Measured consequence at discovery (18 days later, 2026-08-01): "26 of
  42 recorded roots executed criticism and produced zero attacks, every
  artifact vacuously accepted."
- (c) A blast-radius computation would have shown: the computed `mode`
  local variable had zero live consumers after the return statement — a
  trivial dead-value check (does this computed value reach any branch?)
  would have caught a default silently promoted to unconditional at
  commit time, instead of 18 days and 26 vacuously-accepted roots later.

### B3. The legacy-criticism weld, layer 2 — the fix that made schools load-bearing (2026-08-01)

`experiments/2026-08-01-change-prose-can-refute/`. Operator's verbatim
authorization: "Get rid of that requirement. Prose can refute... It's
only formal claims in formal prose that require formal refutation," and
(R14) "as long as a critic isn't from the same school, it's fine."

- (a) Authorized: making prose refutable again, gated on cross-school
  criticism (the operator's own words named cross-school-ness).
- (b) Undisclosed: the fix could not use a cross-family JUDGE ensemble
  (SPEC.md's own finding: no manifest contract carries a judge-school
  binding — `run_manifest.py`'s `_validate_v4_criticism_policy` rejects
  any binding whose role is not `argumentative_critic`), so it pivoted
  to cross-school CRITICISM as the substitute guarantee (DELIVERY.md A9,
  marked "Load-bearing"). This makes `Config.N_SCHOOLS` — previously a
  pure conjecture-diversity knob with "no routing, no status, no budget"
  per `CON-schools.md`'s own words — a silent PRECONDITION for whether
  solo-run, status-changing criticism can fire at all. Nowhere in
  REQUEST.md, SPEC.md, or `CON-authority.md` is `N_SCHOOLS` named as a
  newly-critical input the operator is now depending on. If `N_SCHOOLS`
  is ever set to 1, or schools are repurposed or disabled, solo-run
  criticism silently reverts to the exact original bug
  (`same-school-critic` always fires), with no typed refusal surfaced —
  the confirmed live case of Part 2's own named failure class
  ("dispatch paths that would become dead or newly-live").
- (c) A blast-radius computation would have shown: `Config.N_SCHOOLS`'s
  consumer set changed from "read by `schools.py`'s roster/allocation
  only" to "also gates `trial.py`'s only path to a criticism-authority
  substitute" — a NEW reachability dependency on an existing,
  previously-cosmetic config knob. A disclosure summary would have read:
  "N_SCHOOLS now controls whether solo-run criticism can ever change
  Status, not just conjecture diversity" — exactly the kind of sentence
  Part 2's tool must be able to produce.

Corroborating map evidence, `docs/map/CON-schools.md` Traps: "Mistaking
`require_cross_family_judge_ensemble` for the live guarantee... correct
only for a manifest that authors judge bindings, which the validator
does not permit... The guarantee that actually runs is cross-school
*criticism* in `informal/trial.py`." The same tranche also left a second,
smaller undisclosed disconnection as PARKED dead weight:
`ARGUMENTATIVE_AUTHORITY=single_family_trial` "cannot complete a
trial... retained but superseded... parked as dead weight, not removed."

### B4. `property_designer` — a seat bound to a role with zero live dispatch paths

Chain: `2026-08-06-change-seat-census-s1/CENSUS.md` inventoried
`property_designer` as a call site without checking reachability →
`2026-08-06-change-seat-binding-design-s2/SPEC.md` designed the `coder`
seat group as `{experimenter, property_designer}` on that census's
strength → `2026-08-08-live-two-seat-ab-s6/PARKED.md` P1 discovered,
DURING A LIVE RUN, that the role can never dispatch: `propose_properties`
early-returns unless a property-oracle commitment already exists; the
only function that mints one (`property_oracle_commitment`) is called
only by `admit_counterexample`, which itself requires an EXISTING
property-oracle-typed base — "minting a property-oracle commitment
requires an existing property-oracle commitment as input. No public path
... constructs the first one." No `log.jsonl` anywhere in this
repository's history has ever carried a `property_designer` LLM-call
record. `docs/ERRATA.md` E15 records the permanent correction: S6's
pre-registration first mischaracterized this as a "stochastic miss"
under CLAUDE.md's capability-channel-stochasticity doctrine; "the
probability was 0, not low."

- (a) Authorized (S1/S2, 2026-08-06): binding a `coder` seat group whose
  only role was `property_designer`, presented as a real, workable role.
- (b) Undisclosed: the census that fed the design measured "is this role
  named as a call site," not "can this role ever be reached" — a
  category the census's own column scope never asked.
- (c) A blast-radius computation at S1/S2 grant time would have shown:
  the exact 6-step static call-graph trace S6 later reproduced live
  (`propose_properties` → `checker_wf_commitment` → ... →
  `admit_counterexample`'s own precondition) is entirely derivable
  OFFLINE, no live run needed. A reachability check over
  `propose_properties` at design time would have returned zero live
  paths, and the seat-binding grant request would have said so instead
  of presenting `property_designer` as live.

**Contrast case — the record's own example of doing this right:**
`experiments/2026-08-08-change-pipeline-design-d2/SPEC.md` Fork F3, once
`property_designer`'s deadness was known, explicitly forked the decision
("add a new role, leave `property_designer` untouched" vs. "repurpose
it") and the operator chose with the fork disclosed (R29). This is what
disclosed-fork handling looks like when the blast radius is already
known; Part 2's job is making that knowledge available BEFORE the first
grant, not only after a live run stumbles into it.

### B5. `bias_probes` and the wider judge-audit machinery gap (origin untraceable, currently disclosed)

`docs/map/SUB-evaluation.md` (a checked map claim): "Only
`paraphrase_invariance_audit` has a production call site
(`scheduler.py`); the other three [`premise_deletion_audit`,
`planted_flaw_calibration`, `bias_probes`] are named nowhere in `src/`
outside `informal/audits.py` itself." `2026-08-09-change-judge-evidence-review/REVIEW.md`
§2.2: "No committed root's `log.jsonl` contains a
`judge-self-preference:` or `judge-verbosity-bias:` tag... `bias_probes`
has never produced a live number in the committed record." Unlike B1-B4,
no specific authorizing commit/tranche that wired one audit function
while stranding the other three could be located in the available git
history — this is a genuine dead-circuit finding, correctly disclosed in
the CURRENT map (`SUB-evaluation.md` states it plainly today), not
traceable to one undisclosed grant. Listed here as a case Part 3's
inventory must still carry (the operator needs it on the single page
regardless of whether its origin is traceable), and as evidence that a
consumer-count computation ("who calls this symbol in `src/`, not just
in tests") is exactly the check that would surface this class of gap the
moment a NEW audit function is added, before it goes three functions
deep.

### B6. Map-consumer drift — seam documents that existed but were undiscoverable (`docs/ERRATA.md` E9)

Rung 1 (2026-08-03): seven `SEAM-*.md` documents existed in the tree, but
`INDEX.md`'s own routing matrix and six of the owning `SUB-`/`CON-`
document headers still omitted them or said "not yet written." E9's own
words: "No mechanism in `tools/docs_verify.py` checks a `Sides:` line
against both parties' `Seams:` headers, so nothing would have caught
this short of the cross-reference done here." A milder instance of the
same failure class — a change that should have updated a consumer index
silently didn't, and no instrument (only a manual cross-reference sweep)
caught it. Relevant to Part 2's "consumers of every touched symbol"
computation: map documents are themselves a class of consumer a touched
symbol can silently orphan.

### B7. A delivered finding silently superseded, no back-notification (`docs/ERRATA.md` E17)

Grounded-overlay rung O1's "14 genuine multi-node floating chains"
finding rested on a proxy definition; rung O2's spec-true re-run
superseded it to zero — but O1's own `RESULTS.md`/`DELIVERY.md`/
`VALIDATION.md`/`REPORT.md` were never corrected in place; "the
correction stands only in O2's SPEC.md prose until this [errata] entry."
Not a code-architecture disconnection, but the same disclosure failure
shape one level up: a consumer (any later document citing O1's number)
had no mechanism to learn its input had been invalidated. Cited here
because Part 2's "consumers" computation should generalize past code
symbols to documents that CITE a finding, not only code that CALLS a
function — a boundary worth naming explicitly in the design even though
Part 2's scope (declared target symbols/files) will not close it this
tranche.

### Cases considered and set aside as non-fits

- `experiments/2026-08-04-change-rung7-authority-as-declared-policy/PARKED.md`
  P1 and `2026-08-05-fix-continue-run-rejection/PARKED.md`: real
  process/coverage gaps (delivery-time proof going stale from the
  tranche's own later commits; a refusal path made unreachable and
  undetected for over a week) but framed by their own records as
  MEASUREMENT-staleness or test-COVERAGE gaps, not as an authorization
  request that hid a known consequence at grant time. Named for
  completeness; not counted among the seven cases above.
- `docs/ERRATA.md` E1-E8, E10-E14, E16: staleness/instrument-citation
  corrections (numerals, file:line pointers, fixture
  mischaracterizations) — real documentation-discipline defects, not
  instances of an authorized change hiding architecture.
- Two leads named in the operator's own words did not resolve to a
  distinct, separately-titled document: the literal string "Road E"
  and "legacy-criticism weld" appear nowhere in the committed record
  except this tranche's own REQUEST.md — they are the operator's
  compressed shorthand for the substance traced out as B2/B3 above, not
  a citation to a separate document. A second lead,
  `docs/proposals/GATES_AND_PACKAGES_PREPLAN.md`'s reference to
  `experiments/2026-08-09-change-adjudication-judge-seats-optins/`, does
  not resolve either — that directory does not exist in the committed
  tree; the planned tranche was never opened.

## Part C — where the checkpoint belongs (synthesis for Part 2)

Every case in Part B shares one shape: the DISCLOSURE gap, not the
DETECTION gap. In B1, the SPEC.md census had already found the contact
in prose — the checkpoint that failed was not "can this be found," it
was "does finding it force a stop before the commit lands." In B3/B4,
the information needed (N_SCHOOLS' new consumer; `property_designer`'s
call graph) was STATICALLY DERIVABLE at design time by the same kind of
grep/AST trace this census performed by hand, months after the fact.
None of these seven cases required a live run or new evidence to
surface — every one was answerable from the tree at grant time. That is
the premise REQUEST.md's R2 states explicitly, now with seven concrete
instances behind it: the operator was never positioned to compute this
themselves, and neither, reliably, was the author of the authorization
request — not from lack of care (B1's own SPEC.md correctly named the
risk in prose), but because nothing FORCED the computed fact into the
grant-request text itself, mechanically, every time. That gap is Part
2's target.
