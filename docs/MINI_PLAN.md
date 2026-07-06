# MiniReason — construction plan

*Branch: `claude/mini-harness`. Status: BUILT AND LIVE-VERIFIED — see
`mini/`. M0–M4 done; M2 smoke PASS (meter==log, zero orbit windows,
novelty late/early 1.01 vs 0.846 baseline, parent ingest clean:
`experiments/results/mini_smoke_report.json`); all three judge seats
certified at 0.0 planted-flaw error
(`experiments/results/mini_seat_certification.json`).*
*Every inclusion/exclusion below cites a measurement from the parent
system's experiment record (see `experiments/results/INDEX_2026-07-05.md`,
`docs/BASIN_REPORT.md`). Nothing is kept on faith.*

## 1. Thesis

DeepReason's measured value lives in its **bookkeeping and gates**, not
(at strong-generator regimes) in its adversarial filtering. A ~800-line
harness that keeps the five components that earned their keep — and
nothing else — should deliver essentially all demonstrated value at a
fraction of the complexity and token cost, and remain log-compatible so
a run can graduate to the full system if the high-base-error regime
(where criticism should pay) is ever reached.

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
- G6: log subset-compatible with the parent (an event stream MiniReason
  writes is ingestible by DeepReason's replay).

Non-goals (all measured, none vibes):
- No 2-judge trial protocol, paraphrase screens, appellate machinery —
  no measured quality gain at low base error (A/B refuted twice).
- No embedding-based convergence detection — the embedding detector is
  scale-blind (within/cross-problem medians 0.645 vs 0.671); gate-rate
  replaces it outright (perfect separation on 15 roots).
- No complement directive — measured placebo (lowest echo 0.49x chance,
  zero novelty gain).
- No learned/self-calibrating controller — out of scope for mini.
- No Dung adjudication graph in v0 — status is {live, blocked,
  refuted-by-check}; reinstatement semantics are the first thing to
  graduate INTO the parent for, not to reimplement.

## 3. Architecture

```
mini/
  minireason/
    __init__.py
    log.py        # M0  append-only events + content-addressed blobs
    call.py       # M0  schema-validated pure LLM calls + spend accounting
    gate.py       # M1  dedupe + battery-equivalence vs refuted + orbit counter
    checks.py     # M1  skeleton parse + program evals from forbidden cases
    rotate.py     # M2  stance rotation + problem turnover policy
    judge.py      # M3  the calibrated instrument (criterion forced choice)
    loop.py       # M2  driver: propose -> gate -> check -> rotate
  tests/
  README.md
```

Line budget: ~800 source lines total. If a module wants to exceed its
budget below, the addition must cite a measurement or get cut.

### 3.1 `log.py` (~120 lines) — M0
- `Event`: `{seq, rule, inputs, outputs, llm: {role, model, tokens,
  prompt_ref, raw_ref, attempts} | None}` — a strict subset of the
  parent's event shape (G6).
- Append-only JSONL, fsync on write, strictly consecutive seqs;
  content-addressed blob store for prompts/raws (sha256 files).
- `replay(root) -> State` and the invariant: two replays byte-equal.
- Why kept: the accounting layer caught three real bugs in the parent
  (invisible trial spend 85%, retry-exhausted spend 8.4%, mid-retry
  budget death delta=833).

### 3.2 `call.py` (~150 lines) — M0
- One function: `call(endpoint, prompt, schema, meter) -> (obj, spend)`.
- Repair loop (error fed back, bounded retries), length-truncation
  compression hint, `_usage_tokens` normalization (partial provider
  usage blocks must not count as zero — parent bug).
- EVERY exit path carries spend: success returns it; SchemaError /
  EndpointError / BudgetExceeded all carry `.spend` for the caller to
  log (the parent's exception-spend family, ported verbatim).
- Hard `TokenMeter` with check-before-spend documented as approximate
  (the known overshoot semantics — document, don't pretend).

### 3.3 `gate.py` (~80 lines) — M1
- Content-address dedupe (exact) + battery-equivalence vs refuted
  candidates (normalized-content match; NO embeddings in v0).
- Gate refusals are logged measures: `gate:<reason>` (parent format,
  so the orbit counter and parent tooling both read them).
- `orbit(events, window=20, floor=5) -> school | None` — the gate-rate
  detector. Justification: perfect separation across all 15 parent
  roots (healthy: 0 blocks ever; orbiting: 7-14 per window).

### 3.4 `checks.py` (~100 lines) — M1
- `parse_skeleton(text)` — the parent's JSON skeleton contract
  (claim/mechanism/scope/forbidden/prose_notes).
- Compile forbidden cases with `predicate:`/`program:` evals into
  runnable checks; a failed check refutes (the only refutation source
  in v0). Rubric-eval forbidden cases are carried but NOT judged in
  the loop (that's the instrument's job, offline).
- Why kept: in the basin arms, mechanical checks refuted candidates
  with zero judge tokens — free criticism is the only criticism that
  measured cost-positive at low base error.

### 3.5 `rotate.py` (~80 lines) — M2
- Stance library (parent's 8) + rotation policy: rotate a stance when
  (a) the orbit detector names its school, or (b) stance age exceeds
  STANCE_DECAY conjectures. Default decay LOW (5) — fast rotation
  measured best on BOTH novelty (0.973 late/early vs 0.846 control)
  and school separation (0.690 vs 0.545).
- Problem turnover: when a problem's novelty budget is spent (K draws
  without a new distinct survivor, K default 8), spawn/advance to the
  next problem in the queue. Justification: turnover is the strongest
  anti-basin force measured (the only run whose novelty ROSE, 1.12).

### 3.6 `judge.py` (~120 lines) — M3
- The validated instrument, ported: criterion-level forced choice
  (schema-enforced completeness), both presentation orders, verbosity
  penalty `min(0.3, 0.1*(ratio-1))`, degraded-control validity gate
  (>= +0.2 or the scoring run is void), per-order disagreement
  reported. Control gates measured +0.478/+0.909/+0.841 across three
  problems; zero abstentions in 72 calls.
- Offline tool, not in the loop: evaluation is a measurement you run
  ON a finished log, not a step that gates registration (§0 of the
  parent constitution, kept).

### 3.7 `loop.py` (~100 lines) — M2
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
| M0 | log.py + call.py | unit: replay determinism, meter==log under schema storms and budget death (port the parent's chaos tests); fixture: parse 2 committed parent roots with the subset reader |
| M1 | gate.py + checks.py | fixture: replay `runs/basin/C-decay-off` events through `orbit()` -> fires at the same window; `runs/basin/A-control` -> never; skeleton checks refute a malformed corpus |
| M2 | rotate.py + loop.py | live smoke (~30k tokens): 2 problems x 20 cycles on the cheap provider; assert zero orbit windows, novelty late/early >= control-arm baseline, meter==log |
| M3 | judge.py | rerun the committed instrument report inputs -> byte-identical scores; control-pair gate passes on the committed pairs |
| M4 | README + graduation doc | a MiniReason log ingested by parent `Harness(root)` replays without violations (`invariants.verify_root` == []) |

Total build estimate: M0-M1 one sitting, M2-M3 a second, M4 half.
Live-token cost: ~30-40k (M2 smoke only). Everything else replays
committed logs as fixtures — the append-only design pays for itself
again here.

## 5. Graduation path (mini -> full)

The log subset (G6) is the contract. A team outgrows the mini when:
- base error is measurably high (validate.py-style probe > ~0.15) —
  then the trial protocol has something to filter, or
- reinstatement semantics matter (attacks on attacks), or
- multi-family judge ensembles are required by policy.
Migration = point DeepReason at the mini's root. No data conversion.

## 6. Risks

- Battery-equivalence without embeddings may under-block paraphrase
  orbiting (parent uses `~=_B` with embedder support). Mitigation:
  normalized-token-set equivalence first; if M2 smoke shows orbiting
  slipping the gate, add the parent's equivalence check behind a flag.
- The instrument's seat calibration is provider-specific; judge.py must
  ship with the planted-flaw battery (a trimmed judge_battery.py) so
  new deployments re-certify seats before trusting scores.
- Fast default rotation (decay 5) is measured on n=1 arm; M2's smoke
  doubles as its second measurement — if late/early degrades vs the
  parent control baseline, fall back to 10 and note it.
