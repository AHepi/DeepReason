# CP1-M — hit stratification + dual-mode retrodiction: PRE-REGISTRATION

Frozen before any Phase call that spends a live provider token. House
pattern per `experiments/*/prereg.yaml` / `.../PREREG.md` precedent
(corpus-enrichment-patrol-pilot). Deviations from this file are reported
in `RESULTS.md`, deviation-by-deviation, never silently absorbed.

Two questions this tranche answers, over the 1,941 candidate
contradictions the consistency-patrol pilot found (`docs/map/DR-...`
below is the map preflight; the patrol pilot itself is
`experiments/2026-08-08-corpus-enrichment-patrol-pilot/`):

1. **Are the patrol's 1,941 candidates real contradictions?** — a master
   table, per stratum, of population / confirmed rate / method / evidence
   strength, and one headline number: of 1,941, how many CONFIRMED and at
   what strength.
2. **Can the dual-mode candidate-checker channel work in practice**,
   despite being unreachable by any LIVE run today (P-CEPP-1)? — offline
   authoring + compile + sandbox-execution of real checkers against real
   historical claims, by model, with a recommendation on whether fixing
   P-CEPP-1's wiring is worth it. (P-CEPP-1 itself is NOT fixed here —
   `src/`/`tests`/`tools/` stay byte-untouched, per task scope.)

## Map preflight

| id | covers | why it's read here |
|---|---|---|
| `DR-INV-frozen-surfaces` | the 5 surfaces no tranche may touch | this tranche is `src/`-byte-untouched by its own scope anyway; this confirms the dual-mode read path (`programs.py`, `oracle.py`) is not itself one of the five |
| `DR-SUB-evaluation` | programs, oracles, measures — where formal meets informal | `candidate_checker` is a `program:` eval kind; this is its owning subsystem |
| `DR-SUB-capabilities` | simulation/research lifecycles, **frozen state digests** | not touched — this tranche never mints a capability proposal |
| `DR-CON-conjecture-kinds` | formal vs informal, R-g guardrail | binds this tranche's stratification design: no stratum may be treated as a *better kind* of conjecture, only a different *evidence method* |
| `DR-SUB-manifest` | RunManifest schema, qualification, **frozen** | confirms `ContractVersionPolicyV3`/`_compile_contract_schema_repair_policy` are read-only reconnaissance targets for the P-CEPP-1 re-verification below, never edited |
| `DR-SUB-verification` | `verify_root`, replay validation, **frozen** | this tranche never writes into any root, so no root's `verify_root` result can change; noted for completeness, not exercised |

`INV-frozen-surfaces.md`'s five surfaces (capability state digests,
`harness.py` event application, replay-validation record formats,
qualification-subject digests, the append-only record itself) are
untouched by every phase this tranche plans. Confirmed by design, not
merely by intention: no phase below writes to any `src/`, `tests/`, or
`tools/` file, and no phase writes into any existing committed root
(new candidate-checker executions run in the oracle sandbox, in-memory,
never appended to a root's `log.jsonl`).

## P-CEPP-1 re-verification against the current tree (before relying on it)

`experiments/2026-08-08-corpus-enrichment-patrol-pilot/PARKED.md`'s
P-CEPP-1 entry was re-checked line-by-line against this tranche's own
checkout (commit `781ad6811`, same tree this branch forked from) rather
than trusted verbatim:

- `ContractVersionPolicyV3.conjecturer_turn_contract`
  (`src/deepreason/run_manifest.py:658`) — confirmed: `Literal
  ["conjecturer.turn.v6", "conjecturer.turn.v7"]`, default v6. v7 IS a
  legal value to construct.
- `_compile_contract_schema_repair_policy`
  (`src/deepreason/run_manifest.py:2473`), its `ceilings` dict
  (`src/deepreason/run_manifest.py:2491`) — confirmed: hardcodes
  `"conjecturer.turn.v6": conjecture_ceiling` only. No v7 key, no config
  field, no CLI flag adds one.
- `src/deepreason/run_manifest.py:1999` — confirmed: the behavioral
  route-seat compiler raises
  `RunManifestError("V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED", ...,
  "/contract_schema_repair_policy/grants")` whenever a contract id in
  a route's assignments has no matching grant — which v7 never does,
  because line 2491 never emits one.

**Verdict: P-CEPP-1's unreachability claim holds, byte-identical line
numbers, on this tranche's own checkout.** Every manifest built with
`conjecturer_turn_contract="conjecturer.turn.v7"` is refused before a
run can start. This tranche's entire dual-mode program (S-mech below)
therefore runs the checker-authoring + compile + sandbox-execution path
**offline against the D2/D3-delivered code path directly** —
`deepreason.oracle.candidate_checker_commitment` /
`deepreason.oracle.run_from_full_spec` / `deepreason.programs.evaluate`
with `eval="program:candidate_checker"` — never through a live harness
run (which the v7 gate forbids). This is not a workaround invented here;
it is the same code path `tests/test_oracle.py`'s dual-mode section
(`test_candidate_checker_reads_source_from_budget_not_content` through
`test_run_from_full_spec_overruns_on_malformed_spec`, lines 190-289)
already exercises with hand-written checkers. This tranche exercises it
with MODEL-AUTHORED checkers against REAL historical claims instead.

**The real dual-mode contract shape** (confirmed by reading
`src/deepreason/oracle.py` and `src/deepreason/programs.py` directly,
not inferred from prose):

```
candidate_checker_commitment(source: str, entry: str, tests: list, step_limit=...) -> Commitment
  # id = f"candidate-checker@{digest(spec)}"
  # eval = "program:candidate_checker"
  # budget.extra["spec"] = json.dumps({"source", "entry", "tests", "step_limit"})

run_from_full_spec(budget) -> (verdict, detail)
  # verdict in {"pass", "fail", "overrun"} (PASS/FAIL/OVERRUN from oracle.py)
  # loads {source, entry, tests, step_limit} from budget.extra["spec"]
  # OVERRUN if any of source/entry/tests missing (malformed spec, not a
  #   candidate failure)
  # otherwise: run(source, entry, tests, step_limit) — sandboxed
  #   subprocess, calls source's `entry` function against each test's
  #   {"in": [...], "out": ...}, PASS iff every case matches exactly
```

Two structural facts bind the checker-authoring contract below:
- The checker's `source` is **never** the claim's own prose — dual-mode's
  own Amendment 1 forbids a conjecture from ever being full code. The
  claim stays prose; the checker is a *separate* artifact the encoder
  authors, testing what the claim asserts.
- `run_from_full_spec` OVERRUNs (not FAILs) on a malformed spec —
  missing `source`/`entry`/`tests`. This tranche's authoring-success /
  compile-pass / execution-rate measures (below) treat OVERRUN as its
  own outcome, never folded into "fails the claim."

## Strata (all 1,941 hits, plus 150 sampled non-hit controls)

**Assignment is a single priority-ordered partition** — each hit is
tested against the strata in the order below and assigned to the FIRST
one it qualifies for. This is the order the task instruction itself
lists them in (S-mech, S-truth, S-formal, "S-judgment — the remainder"),
adopted here as the assignment rule rather than invented independently
— recorded as an assumption, not silently absorbed, since the task text
does not use the word "priority" explicitly.

No stratum assignment reflects or affects a claim's or checker's
*formal-vs-informal KIND* in the harness sense (`DR-CON-conjecture-kinds`,
R-g) — these are candidate ARTIFACTS from historical runs, being
RETRODICTIVELY checked by this tranche's own methods; the stratum a hit
lands in is a property of what kind of EVIDENCE is available for it, not
a judgment about the conjecture's own admission, rank, or protection
inside the run that produced it (Formalism-is-an-option law, CLAUDE.md).

### S-mech / dual-mode

**Eligibility**: either claim's content is executable/countable — a
claim asserting a value that a short, deterministic program could
compute and compare (a rule-CA property, a count, a tour length, an
arithmetic total, a pass/fail against a numeric criterion, etc.).

**Method**: an encoder-role model authors a `candidate_checker` (source,
entry, tests) through the REAL contract shape above — one call per
CLAIM (not per pair; a pair contributes up to two independent checkers,
one per claim, each tested against BOTH claims in the pair). Split
evenly by model and by key (below). Compiled and validated through the
actual code path OFFLINE
(`deepreason.programs.evaluate`/`deepreason.oracle.run_from_full_spec`),
executed in the sandbox (`deepreason.oracle.run`, the same isolated
worker `exec_oracle`/`property_oracle` use — AST-guarded, whitelisted,
step-bounded).

**Processing order within S-mech**: Rule-184-family hits first (43 hits
whose patrol `reason` field mentions "Rule 184", case-insensitive —
the pilot's own chunk-1 exemplars, `2026-08-02-stress-triplet/home-orbit`).

**Measures, per model** (glm-5.2 vs the coder-seat model, `gemma4:31b`,
matching the patrol pilot's own two-model precedent):
- authoring-success rate (the encoder call returns a well-formed
  `{source, entry, tests}` triple, parseable and non-empty)
- compile-pass rate (of authored, `run_from_full_spec` does not OVERRUN
  — source/entry both present and the source compiles under the oracle
  sandbox's AST guard)
- execution rate (of compile-pass, the sandboxed run completes to a
  PASS or FAIL verdict rather than a step-limit/sandbox abort)

**Measures, per pair** (once each claim in the pair has its own
checker, each checker run against BOTH claims — 2 checkers × 2 claims =
4 executions per fully-resolved pair):
- checker(A) passes claim A AND checker(A) fails claim B, or the
  symmetric case for checker(B) → **CONFIRMED contradiction, with
  polarity** (which claim the executable evidence sides with)
- both checkers pass both claims, or both checkers fail both claims →
  recorded honestly as **discriminating-power evidence** (the checker
  could not distinguish the two claims) — never silently dropped, never
  counted as a non-hit
- a pair where only one claim produced a usable checker (the other's
  encoder call OVERRAN, failed to author, or failed to compile) is
  scored on the ONE checker alone (pass/fail against both claims is
  still meaningful) and flagged `single_checker` in the master table's
  method column

### S-truth

**Eligibility** (evaluated only on hits S-mech did not already claim):
the pair's `problem_id` resolves to a source question carrying an
explicit ground-truth answer — concretely, the `accept` field pattern
used by `experiments/validation_questions*.json` (confirmed present:
every one of Phase 1's 10 base/hard/hard2 questions ships an `accept`
list, e.g. `q01: {"accept": ["6"]}`). Provisional population before
S-mech carve-out: up to 808 hits sit in the 10 Phase-1 enriched roots
(exactly the patrol's own "enriched half" count); the S-mech-first
carve-out and any historical-half question sources found to carry an
equivalent explicit-answer pattern are resolved during execution, not
assumed here.

**Method**: no model call needed for the ground-truth comparison itself
— parse each claim's asserted value (regex/number extraction against
the known `accept` value first; a bounded single model-extraction call
as fallback for claims where the value isn't a bare literal, itself
subject to the stability control below) and compare directly to
`accept`. A claim matching `accept` is TRUE; a claim contradicting it is
FALSE. Two claims where at least one is FALSE against ground truth are
**CONFIRMED contradiction, with polarity** (the FALSE claim is the one
refuted). Two claims both TRUE against ground truth cannot be a genuine
contradiction under this stratum's own method — recorded as
`ground_truth_agrees` (a MEASUREMENT of the patrol's classifier missing
here, not silently dropped) and routed to S-formal/S-judgment for a
second read rather than left unexamined.

### S-formal

**Eligibility**: pairs not claimed by S-mech or S-truth whose two claims
have a clean **(object, property, polarity)** shape — a shared subject,
a shared property, and opposite asserted values for it.

**Method**: structured extraction — one model call per claim, extracting
`{object, property, value}` — then MECHANICAL (non-model) negation
detection: same object + same property + incompatible values ⇒
**CONFIRMED contradiction, with polarity determined only if ground truth
or an S-mech-style check is separately available** (S-formal alone
proves inconsistency, not which side is right, unless chained into
S-truth/S-mech); same object + same property + compatible or
non-overlapping values ⇒ NOT a same-property contradiction under this
method (routed to S-judgment). **Extraction validated on a 50-hit pasted
sample** before running the full stratum — a human-in-the-loop (this
session, reading the raw extraction JSON against the raw claim text
side-by-side) check that the extraction schema captures the pair's
actual shape, run once before spending the stratum's full call budget,
not repeated per pair.

### S-judgment

**Eligibility**: the remainder — every hit not claimed by S-mech,
S-truth, or S-formal.

**Method**: adversarial battery — order-swap (A/B claim order reversed,
re-asked), skeptic framing (a prompt variant explicitly instructed to
argue AGAINST finding a contradiction unless compelled), and the
stability control itself (×2 identical repeats, see below) — run
**independently by both keys' models** (glm-5.2 and the coder-seat
model). **Convergence is the number reported**: of the up-to-6 readings
per pair (2 models × 3 battery variants, or fewer where a variant
overruns), what fraction agree with the ORIGINAL patrol verdict
(contradiction=true). A pair is **CONFIRMED** only if convergence meets
a pre-registered threshold — **≥4 of 6 available readings agree**,
recorded per-pair so a reader can re-derive the threshold choice's
effect; a pair below threshold is recorded as `not confirmed by
adversarial convergence`, never silently dropped from the master table.

### 150 non-hit controls

Sampled from `patrol_results.jsonl`'s 7,336 `is_hit=false, error=null`
rows, deterministic seed `sha256("cp1m-control-sample-v1")[:8]` (big-
endian int) via `random.Random(seed).sample(range(7336), 150)` —
reproducible from this file's own bytes, no wall-clock/random-module
call outside this pinned seed. Already drawn and committed at
`controls_150.jsonl` (150 rows, claim text resolved offline via the
SAME `Harness(root, read_only=True)` +
`deepreason.programs.content_text` loader `phase2_patrol.py` used — 0
unresolved). **Purpose**: run the SAME per-stratum method the pair's
content would route to (using the identical priority order above) and
report the FALSE-NEGATIVE rate this pilot's original 0.6-confidence
threshold produced — i.e., how many of the 150 non-hits would this
tranche's stronger methods have flagged as contradictions anyway. This
is the only number in this tranche that speaks to the patrol's
threshold choice itself, not just its positive hits.

## Offline first-pass sizing (heuristic, NOT the final stratum
## assignment — recorded so the operator can see population shape
## before any live call, per this tranche's own pre-registration rule)

Computed via `scripts/offline_stratify.py`… (see `RESULTS.md`'s first
segment for the exact numbers and the heuristic's definition — a
keyword/regex proxy for "executable/countable," explicitly named as
provisional). This pass made ZERO live calls: it only opened committed
roots read-only and matched text patterns.

## Checker-authoring contract (S-mech)

One encoder-role call per claim needing a checker. Frozen prompt shape
(the SAME text for every claim, differing only in the substituted
claim text and, where available, its problem statement):

```
You are given a claim asserted within a solved reasoning problem.
Write a short Python function that MECHANICALLY CHECKS whether a
given answer is consistent with this specific claim -- not whether
the claim is correct in general, just whether a candidate answer
matches what this claim asserts.

Problem: {problem_text_if_known}
Claim: {claim_text}

Respond with EXACTLY one JSON object and nothing else:
{{"source": "def check(answer):\n    ...\n    return True or False",
  "entry": "check",
  "tests": [{{"in": [<one or more self-consistent example answers your
             own check() should return True for>], "out": true}}]}}

Your `check` function takes ONE argument (the answer/value under
test) and returns True if it satisfies what the claim asserts, False
otherwise. Keep it under 40 lines, pure Python, no imports beyond the
standard library math/itertools if strictly needed.
```

`entry` is fixed to `"check"` by contract, matching `run_from_full_spec`'s
`entry` field. `tests` supplied by the model are used as the
checker's OWN self-consistency cases (an author who cannot write a test
their own checker passes is itself an authoring-success signal, folded
into the authoring-success measure); this tranche's OWN pass/fail
verdict on the actual claim pair comes from re-invoking the compiled
`check(answer)` against a value extracted from each claim (or, for
non-numeric claims, a small enumerated set of candidate answers derived
from the claim text) — the model's self-tests validate the checker
compiles and runs; they do not decide the pair's contradiction verdict.

**Split**: two provider models (glm-5.2, the primary model this repo
runs everywhere; and the coder-seat model, `gemma4:31b` — CLAUDE.md /
patrol precedent for the "encoder role" binding), evenly across the two
operator API keys (each key ≤3 concurrent calls — env discipline below).
"Split evenly" = alternate claim-checker authoring calls between the two
models in problem_id order, so no model gets systematically the easier
or harder half of the corpus by chance ordering.

## Confirmation criteria — summary table

| Stratum | CONFIRMED when | Discriminating-power / residue outcome |
|---|---|---|
| S-mech | one checker passes its own claim and fails the partner claim | both-pass or both-fail → discriminating-power evidence, never dropped |
| S-truth | at least one claim's asserted value contradicts the `accept` ground truth | both agree with ground truth → `ground_truth_agrees`, routed onward |
| S-formal | same (object, property), incompatible values, chained to S-mech/S-truth for polarity where available | non-overlapping/compatible values → routed to S-judgment |
| S-judgment | ≥4 of ≤6 adversarial-battery readings (both models × 3 variants) agree with the original patrol verdict | below threshold → `not confirmed by adversarial convergence` |

Every outcome above is a row in the master table — CONFIRMED,
discriminating-power, ground-truth-agrees, and not-confirmed are ALL
reported; none is silently excluded from the 1,941 denominator.

## Stability control (binding on every model-judgment step)

Searched `experiments/2026-08-08-corpus-enrichment-patrol-pilot/RESULTS.md`
for a section literally titled a "non-determinism correction" before
writing this rule, per this repo's own record-first discipline — none
exists under that name. The closest recorded fact is the Phase 3 overlay
non-reproducibility note ("a fresh `run_all_overlays.py` re-run is not
byte-reproducible... Python's hash-randomized `set()` iteration order...
never in content" — RESULTS.md, "Pre-registration and setup" segment),
which is about JSON-list ORDERING, not model judgment. The task
instruction's binding requirement is honored on its own terms regardless
of whether the literal section exists, because it is independently
justified by CLAUDE.md's own capability-channel stochasticity doctrine
("Capability-channel use... is STOCHASTIC across identical runs") and by
this pilot's own Phase 2 method (temperature=0.0 is not a determinism
guarantee for a hosted API — server-side batching/routing can still
vary a response run-to-run):

- **Every model-judgment step** (S-mech's checker authoring, S-truth's
  fallback extraction call, S-formal's extraction call, every
  S-judgment battery variant) draws a **sampled repeat pass**: for a
  fixed 10% sample of that step's calls (deterministic selection, same
  seeding convention as the control sample), the IDENTICAL call is
  issued a second time and the two outputs compared. The **flip rate**
  (fraction of the sampled repeats whose verdict/extraction differs
  between the two identical calls) is reported per step in the master
  table's method column.
- **Every deterministic step says so explicitly** in the master table
  (S-truth's direct `accept`-value comparison, S-formal's mechanical
  negation check, S-mech's sandboxed execution once a checker compiles)
  — labeled `deterministic, no repeat pass` rather than silently
  omitting a flip-rate column entry.
- A flip on the REPEAT pass does not itself change a pair's recorded
  verdict (the original call's outcome stands, per the task's own
  measures); it is evidence about the STEP's reliability, reported
  alongside the confirmed-rate numbers so the operator can weigh
  confidence, not folded into the confirmed count itself.

## Failure budget: 10 (S6-style)

Same discipline as the patrol pilot's own Phase 1 ledger and S6's
precedent: diagnose from the typed record and blobs BEFORE any remedy;
retire a dead/discarded attempt with a committed `git mv` first, never
edit a committed root in place (not applicable here in the strict sense
— this tranche writes no new harness roots — but the SAME discipline
applies to any corrupted/truncated JSONL output file this tranche
produces: retired, not hand-patched). Spend is ledgered in `RESULTS.md`
as it happens, same format as the patrol pilot's failure ledger.

## Environment / credential discipline

Two operator API keys, ≤3 concurrent calls per key, `env` file(s)
gitignored (`git check-ignore` verified before use), `chmod 600`, never
committed. **Status at pre-registration time: NEITHER key is present in
this container.** `experiments/live_research_2026-07-29/env` (the
CLAUDE.md-documented convention) does not exist on disk, no
`OLLAMA_API_KEY`-shaped variable is set in the environment, and no
handover document in this session's context carries key material. Per
CLAUDE.md ("recreate it from the operator's handover if missing") this
is an operator-authority gap, not something inferable from the record —
flagged here, before any Phase spends a live call, rather than guessed
at or fabricated.

## Deliverables (unchanged from task instruction, restated for the
## record)

1. Master table: per stratum — population, confirmed rate, method,
   spot-check pointers.
2. Headline: of 1,941 candidates, how many CONFIRMED and at what
   evidence strength.
3. Dual-mode verdict: can models author working checkers for real
   historical claims, rates by model, recommendation on whether fixing
   P-CEPP-1's wiring is worth it (decision is the operator's).
4. Artifact-type breakdown; depth-0/depth-k first count (CP3/CP4 seeds).
5. Honest residue.

Commit and push at every phase boundary (this document is the first).
Stop when the master table is pushed.
