# MiniReason — construction plan

*Original build status: BUILT AND LIVE-VERIFIED — see `mini/`. M0–M4 done;
the original M2 smoke PASS (meter==log, zero orbit windows,
novelty late/early 1.01 vs 0.846 baseline, parent ingest clean:
`experiments/results/mini_smoke_report.json`); all three judge seats
certified at 0.0 planted-flaw error
(`experiments/results/mini_seat_certification.json`).*
*The later shared-kernel compatibility refactor is locally verified, but its
live Gemma/frontier acceptance thresholds remain uncollected; see
`docs/SMALL_MODEL_COMPATIBILITY.md`.*
*Every inclusion/exclusion below cites a measurement from the parent
system's experiment record (see `experiments/results/INDEX_2026-07-05.md`,
`docs/BASIN_REPORT.md`). Nothing is kept on faith.*

## 1. Thesis

DeepReason's measured value lives in its **bookkeeping and gates**, not
(at strong-generator regimes) in its adversarial filtering. MiniReason keeps
a reduced scheduler and rule surface while importing the canonical Harness,
ontology, grounded adjudicator, anti-relapse guard, warrant plumbing, route
firewall, wire contracts, repair kernel, and persistence. Its roots are full
DeepReason roots from the first event, so a high-base-error workload can
graduate to the full scheduler without conversion.

## 2. Goals / non-goals

Goals:
- G1: every token on the log exactly once (meter == log, enforced).
- G2: byte-replayable runs; state is a pure function of the log.
- G3: no unsupervised waste: dedupe + orbit detection + rotation stop
  the two measured failure modes (repertoire exhaustion sampling,
  refuted-attractor orbiting at 4.3x token burn).
- G4: criticism that costs nothing: program checks compiled from each
  candidate's own falsifiability claims.
- G5: evaluation only through a calibrated instrument (naive pairwise
  judging measured unusable: 8/9 votes discarded to position bias).
- G6: one canonical root: MiniReason writes the parent's Event/object schemas
  through the parent's Harness, so full DeepReason opens it without migration.

Non-goals (all measured, none vibes):
- No 2-judge trial protocol, paraphrase screens, appellate machinery —
  no measured quality gain at low base error (A/B refuted twice).
- No embedding-based convergence detection — the embedding detector is
  scale-blind (within/cross-problem medians 0.645 vs 0.671); gate-rate
  replaces it outright (perfect separation on 15 roots).
- No complement directive — measured placebo (lowest echo 0.49x chance,
  zero novelty gain).
- No learned/self-calibrating controller — out of scope for mini.
- No duplicate adjudicator, status vocabulary, ontology, guard, or warrant
  implementation. Mini uses the parent's grounded/support labels, including
  attacks on validity nodes and reinstatement; only its scheduling surface is
  reduced.

## 3. Architecture

```
mini/
  minireason/
    __init__.py
    log.py        # M0  compatibility view over canonical Harness state/replay
    call.py       # M0  shared bounded repair + Mini spend accounting facade
    gate.py       # M1  process-only gate/orbit analytics (shared guard admits)
    analytics.py  # process-only text normalization for offline reports
    checks.py     # M1  canonical skeleton/commitment/program adapters
    rotate.py     # M2  stance rotation + problem turnover policy
    judge.py      # M3  the calibrated instrument (criterion forced choice)
    loop.py       # M2  driver: propose -> gate -> check -> rotate
  tests/
  README.md
```

The original line budget motivated the reduced feature surface; it is no
longer a source-size claim. Shared compatibility and replay adapters are kept
where they prevent Mini from becoming a second normative implementation.

### 3.1 `log.py` — M0
- `Event`, `LLMCall`, `BlobStore`, `ObjectStore`, and replay are the parent's
  implementations. Mini's `State` is a read-only dictionary-shaped projection
  of canonical Harness state, not a second materializer or status calculator.
- Append-only JSONL, strictly consecutive sequences, content-addressed blobs,
  grounded status, attack/support edges, and replay therefore have one code
  path in both engines.
- Why kept: the accounting layer caught three real bugs in the parent
  (invisible trial spend 85%, retry-exhausted spend 8.4%, mid-retry
  budget death delta=833).

### 3.2 `call.py` — M0
- One function: `call(endpoint, prompt, schema, meter) -> (obj, spend)`.
- The bounded repair state machine, transport mechanism selection, route lease,
  wire contract, and per-attempt trace come from shared DeepReason modules.
  Mini retains endpoint normalization and its hard `TokenMeter` facade.
- EVERY exit path carries spend: success returns it; SchemaError /
  EndpointError / BudgetExceeded all carry `.spend` for the caller to
  log (the parent's exception-spend family, ported verbatim).
- Hard `TokenMeter` with check-before-spend documented as approximate
  (the known overshoot semantics — document, don't pretend).

### 3.3 `gate.py` — M1
- Admission delegates to the parent's canonical hash/battery-equivalence
  anti-relapse guard. Mini constructs one canonical Artifact/Interface before
  that check and registers the same object; it carries no forked guard logic.
- Mini has no embedder, so its configured `NEAR_DUP_EPS=None` takes the shared
  guard's exact fallback: battery-check every refuted prior.
- Gate refusals are logged measures: `gate:<reason>` (parent format,
  so the orbit counter and parent tooling both read them).
- `orbit(events, window=20, floor=5) -> school | None` — the gate-rate
  detector. Justification: perfect separation across all 15 parent
  roots (healthy: 0 blocks ever; orbiting: 7-14 per window).

### 3.4 `checks.py` — M1
- `parse_skeleton(text)` — the parent's JSON skeleton contract
  (claim/mechanism/scope/forbidden/prose_notes).
- Model-authored forbidden cases use the parent's skeleton contract. Inline
  `predicate:` expressions are rejected at that boundary; known `program:`
  commitments compile through the parent's pure constructor and execute via
  `deepreason.programs`.
- Mini's frozen `rubric_policy=forbid` means a rubric-bearing candidate is
  process-logged and dropped before any commitment or artifact registration.
  The offline `judge.py` instrument is reporting only and does not turn that
  candidate into epistemic state.
- Why kept: in the basin arms, mechanical checks refuted candidates
  with zero judge tokens — free criticism is the only criticism that
  measured cost-positive at low base error.

### 3.5 `rotate.py` — M2
- Stance library (parent's 8) + rotation policy: rotate a stance when
  (a) the orbit detector names its school, or (b) stance age exceeds
  STANCE_DECAY conjectures. Default decay LOW (5) — fast rotation
  measured best on BOTH novelty (0.973 late/early vs 0.846 control)
  and school separation (0.690 vs 0.545).
- Problem turnover: when a problem's novelty budget is spent (K draws
  without a new distinct survivor, K default 8), spawn/advance to the
  next problem in the queue. Justification: turnover is the strongest
  anti-basin force measured (the only run whose novelty ROSE, 1.12).

### 3.6 `judge.py` — M3
- The validated instrument, ported: criterion-level forced choice
  (schema-enforced completeness), both presentation orders, verbosity
  penalty `min(0.3, 0.1*(ratio-1))`, degraded-control validity gate
  (>= +0.2 or the scoring run is void), per-order disagreement
  reported. Control gates measured +0.478/+0.909/+0.841 across three
  problems; zero abstentions in 72 calls.
- Offline tool, not in the loop: evaluation is a measurement you run
  ON a finished log, not a step that gates registration (§0 of the
  parent constitution, kept).

### 3.7 `loop.py` — M2
- The driver: `run(problem_queue, endpoint, budget)`:
  propose (VS_K candidates, stance-conditioned) -> gate -> checks ->
  log -> rotate-if-flagged -> next.
- Neighbourhood: keep it (8 exemplars) — it is mildly anti-basin for
  strong models (below-chance echo means the model uses it to avoid
  repeats) and harmless to blind runs; make it a knob like the parent.
- Stop conditions: budget, queue exhausted, or global novelty budget
  spent (all problems dry). Never loop a dry problem — that is the
  4.3x burn.

## 4. Milestones and verification

| id | deliverable | verification (all mechanical) |
|---|---|---|
| M0 | log.py + call.py | unit: replay determinism, meter==log under schema storms and budget death; canonical Harness reopens every generated root |
| M1 | gate.py + checks.py | fixture: replay `runs/basin/C-decay-off` events through `orbit()` -> fires at the same window; `runs/basin/A-control` -> never; skeleton checks refute a malformed corpus |
| M2 | rotate.py + loop.py | live smoke (~30k tokens): 2 problems x 20 cycles on the cheap provider; assert zero orbit windows, novelty late/early >= control-arm baseline, meter==log |
| M3 | judge.py | rerun the committed instrument report inputs -> byte-identical scores; control-pair gate passes on the committed pairs |
| M4 | README + graduation doc | a MiniReason log ingested by parent `Harness(root)` replays without violations (`invariants.verify_root` == []) |

Total build estimate: M0-M1 one sitting, M2-M3 a second, M4 half.
Live-token cost: ~30-40k (M2 smoke only). Everything else replays
committed logs as fixtures — the append-only design pays for itself
again here.

## 5. Graduation path (mini -> full)

The canonical root (G6) is the contract. A team outgrows the reduced engine
when:
- base error is measurably high (validate.py-style probe > ~0.15) —
  then the trial protocol has something to filter, or
- the workload needs research, informal trials, websites, capture control,
  long-horizon scheduling, or a normative cross-family judge ensemble.
Migration = point DeepReason at the mini's root. No data conversion.

## 6. Risks

- Mini supplies no embedder to the shared anti-relapse guard, so the guard
  battery-checks every refuted prior instead of using an embedding index to
  narrow the set. This preserves the canonical decision rule but costs more
  and can be coarse when the active battery is weak. Gate-rate/orbit analysis
  remains process-only and never substitutes a token-equivalence admission
  rule.
- The instrument's seat calibration is provider-specific; judge.py must
  ship with the planted-flaw battery (a trimmed judge_battery.py) so
  new deployments re-certify seats before trusting scores.
- Fast default rotation (decay 5) is measured on n=1 arm; M2's smoke
  doubles as its second measurement — if late/early degrades vs the
  parent control baseline, fall back to 10 and note it.
