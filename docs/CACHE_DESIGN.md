# Caching-Layer Design — What Survived Its Own Criticism

*2026-07-04. Result of an 18-cycle self-referential run (`--suite cache`,
spec injection on, 451k tokens): the harness worked the research question
that gates its own deferred feature — a deployable cache for providers
without prefix caching. Five rival designs survived criticism under the
`std-design` standard; full skeletons in
`experiments/results/cache_design_report.json`. This note distills what
we act on.*

## The surviving design space

1. **Exact pack fingerprint cache** (`ce1b3cfc`): SHA-256 of the rendered
   pack keys per-provider LRU shards. Simplest; correct by construction.
2. **Prompt-component DAG** (`c9931dd1`): stable components (system,
   problem, criteria, stance) hashed as a prefix chain; completions keyed
   by root hash, invalidation only on component change. A principled
   generalization of our stable-prefix pack ordering — the natural
   implementation target.
3. **Event-sourced completion log** (`18aa7c47`): append-only cache
   keyed (run_id, seq, input_hash) with epoch invalidation — closest fit
   to the harness's own log discipline.
4. **Delta reconciliation** (`890a7af4`): base pack + minimal edits,
   completions indexed by state fingerprint. Higher machinery cost.
5. **LSH semantic cache** (`346567fd`): route semantically-equivalent
   prompts to one completion. Survived, but its own forbidden cases name
   verdict leakage across targets and overhead exceeding a raw call —
   the riskiest branch; do not build first.

## Convergent forbidden cases = the test suite for the implementation

Independent designs converged on the same refuters, which makes them the
acceptance tests for whatever we build:

- **No cross-target leakage**: a hit must never serve a completion whose
  key came from a different target/school (fingerprint collision or
  semantic bucketing). → test: adversarial near-identical packs from two
  schools must miss.
- **Replay stays byte-for-byte**: cache entries must not survive into a
  replay/fork context where the log would have produced different bytes;
  epoch/config changes invalidate. → test: replay with cache enabled ==
  replay with cache disabled, always.
- **Hit-rate floor or it isn't worth it**: `ce1b`'s own falsifier —
  if measured pack variability makes fingerprints near-unique (<20%
  hits), the cache is a net negative. → measure cross-run pack overlap
  BEFORE building (this was the original research gate, now sharpened
  into a number).

## Epistemic boundary the run reaffirmed

Any cache serves **generator-side bytes only** (rendered packs,
completions for temperature-0 roles, embedding vectors). Two hard lines:

- Cached **verdicts** across non-equivalent targets remain forbidden —
  that is the battery-equivalence gate's exclusive jurisdiction.
- Caching **sampled** (temperature > 0) completions across contexts
  changes the exploration distribution — it would trade diversity for
  cost silently. Cache deterministic roles (judge) and renders; never
  the conjecturer's samples across different calls.

## Verdict on the deferred item

Build order when funded: (a) instrument pack-overlap measurement on
existing run logs → if overlap clears the `ce1b` floor, (b) implement
the exact-fingerprint cache with the component-DAG keying from `c9931dd1`
inside `llm/providers.py`/adapter seam, (c) ship with the three
convergent forbidden cases as tests. The LSH branch stays unbuilt unless
overlap measurement shows exact matching leaves large money on the table.

## Addendum (same day): the measurement happened, and it flipped the plan

`scripts/cachebench.py` replayed all 151 logged prompts from six run
directories — the real workload, byte-for-byte. Results
(`experiments/results/cachebench_report.json`):

- **cross-run exact hit rate: 1.99%** — far below `ce1b3cfc`'s own 20%
  floor. Its forbidden case obtained; it is now **refuted by a
  demonstrative warrant** carrying the benchmark trace.
- **same-run prefix reuse: 29%** (34% cross-run; conjecturer 30%, judge
  18%) — far below `c9931dd1`'s 90% claim. Also **refuted by
  measurement**. Stable-prefix ordering keeps the head cacheable, but the
  volatile tail (neighbourhood, target content) dominates prompt length.
- λ for the design domain rose 0.0 → 0.67: verdicts here are now
  grounded, not argued.

Standing after measurement: the **event-sourced completion log**
(`18aa7c47` — fits replay exactly, pays on re-runs/resumes rather than
fresh cycles), **delta reconciliation** (`890a7af4`), and the **LSH
semantic cache** (`346567fd`) — the "wild" branch survived its rivals
precisely because exact matching provably leaves the money on the table.
Its own forbidden cases (verdict leakage, overhead > raw call) are now
the next things to measure before building. Provider-side prefix caching
(free, automatic) remains worth keeping via pack ordering; a
harness-side exact/prefix cache is not worth building for this workload.
