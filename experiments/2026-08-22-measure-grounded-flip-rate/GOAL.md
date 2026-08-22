<!-- tranche: measurement, read-only on src/ and tests/ -->
# GOAL — how fragile is the grounded extension to attack-edge errors?

Date: 2026-08-22
Branch: `claude/grounded-flip-rate-measure-x36e1w`
Base: `d9b8ef2c2`
Family: `deepreason-orchestrator` (measurement tranche — no defect, no fix)

## Map preflight

| id | why it is in scope |
|---|---|
| `DR-SUB-adjudication` | owns the entirety of status semantics: `build_att`, `build_dep`, `grounded_extension`, `label0`, `final_labels`. The measured code path. |
| `DR-SEAM-adjudication-x-rules` | read for context: a rule's whole power over status is the right to mint warrant/target/validity-node. It explains WHY `att` is as sparse as §"Corpus facts" reports. |
| `DR-SEAM-adjudication-x-authority` | read for context: authority gates warrant minting upstream, so a missing edge is an upstream refusal, not an adjudication choice. |
| `DR-INV-frozen-surfaces` | read before designing. Nothing in this tranche writes to a root, a record format, or a digest. |

## The question

`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q3 records `[UNKNOWN]`: nobody
has measured the empirical label-flip rate of grounded semantics against an
attack-edge error rate, on any corpus (open item 2). Q10 supplies the error
rate that would be fed in — Attack-edge extraction runs at F1 ≈ 0.33–0.43
under gold component boundaries. "The one item to act on first" argues the two
compose badly and proposes an uncertain-edge (IAF) layer at Rung 8.

This harness owns 96 committed current-version argument graphs. The
measurement is offline arithmetic over them.

## Success criterion (falsifiable)

The tranche succeeds if `RESULTS.md` reports, from committed JSON:

1. the single-edge flip-rate table (per root and aggregate) for BOTH error
   directions;
2. the blast-radius distribution — median and tail labels flipped per single
   edge error, and the **stability mass**: the share of single-edge errors
   that flip zero labels;
3. the structural characterization of a dangerous edge on these graphs;
4. the directionality check — whether any flip ever escapes the perturbed
   edge's downstream attack cone;
5. one closing paragraph recommending (not deciding) for or against the
   Rung 8 uncertain-edge layer.

It FAILS if any number is reported without the JSON that produced it, or if
the corpus's own properties are smoothed over to make the curves look
better-behaved than they are.

## Scope contract

- **READ-ONLY on `src/` and `tests/`.** `git diff --stat origin/main` must show
  changes only under `experiments/2026-08-22-measure-grounded-flip-rate/`.
- No committed run root is modified; no record is written. All perturbation is
  on in-memory copies (deterministic-identity law).
- Any defect noticed is PARKED in `PARKED.md` with a ready-to-send prompt.
  Nothing is fixed here.
- A concurrent window owns `measures/reach.py`. No file is shared.

---

# PREREG — registered before any battery was run

Registered after the corpus inventory (`inventory.py` → `inventory.json`) and
the graph cache (`cache_graphs.py` → `graphs.json`), and before any
perturbation battery. The inventory and cache are descriptive, not tests: they
establish the denominators the batteries below are sized against, and those
denominators are stated here so no later choice can be tuned to a result.

## Corpus facts fixed at registration time

Established by `inventory.py` / `cache_graphs.py`, both committed:

- 107 committed roots carry a `log.jsonl`. **96 open under the current
  version**; 11 refuse with `UnsupportedRunManifestVersionError` and are
  excluded, named in `inventory.json`. (Exclusion is lawful under the
  2026-08-14 operator law: old roots owe the future nothing.)
- 6 370 artifacts across the 96 roots (min 4, median 53, max 304).
- **60 attack edges in the entire corpus.** 76 of 96 roots have `att = ∅`.
- Baseline labels: 6 309 `accepted`, 60 `refuted`, 1 `suspended_unsupported`,
  0 `suspended`.
- 60 edges ↔ 60 `refuted` nodes: **no node is attacked twice and no attacker
  is itself attacked.** Every attack relation in the corpus is a depth-1
  matching. No directed cycle, no self-attack.
- Replay cost: 233 s to open all 96 roots once (39.5 s of it the one
  12 991-line root). Paid ONCE; `graphs.json` carries the graphs thereafter.

`cache_graphs.py` asserts, per root, that labels re-derived from the cached
`att`/`dep` equal `h.state.status`. If that assertion fails the cache is not a
faithful stand-in and the measurement is void.

## Measured code path

The committed functions, not a reimplementation:

    from deepreason.adjudication.grounded import label0
    from deepreason.adjudication.support import final_labels
    labels = final_labels(label0(nodes, att), dep)

This is exactly `Harness._adjudicate`'s pass 1 + pass 2 with `att` substituted.
`build_att`/`build_dep` are NOT re-run: the perturbation being modelled is
error in the extracted attack RELATION, which is what Q10 measures F1 on, so
the relation is perturbed directly at the point adjudication consumes it.
Recorded as a modelling assumption, not a finding.

## Battery A — single-edge, EXHAUSTIVE (no sampling)

Sized at registration: 60 deletion cases and 645 624 addition cases across the
corpus, at 0.08–1.33 ms per recompute. **Both directions run exhaustively**;
no sampling rule is needed and none is used, so there is no seed to derive.

- **A-del**: for every existing edge `e ∈ att`, recompute on `att \ {e}`.
- **A-add**: for every ordered pair `(x, y)`, `x ≠ y`, `(x,y) ∉ att`,
  recompute on `att ∪ {(x,y)}`. Self-attacks are excluded — the corpus has
  none, and "a attacks a" is not an extractor error shape.

Per case record: the perturbed edge, the number of flipped labels, and for
each flipped node its id, before/after label, and its shortest-path distance
from the perturbed edge's HEAD in the union graph `att ∪ att'` (head distance
0). A flip at unreachable distance = `null` is a **directionality violation**
and is counted separately.

## Battery B — error-rate curves

Rates need a denominator, and the corpus makes the obvious one degenerate:
10 % of 0 edges is 0. Three arms are registered, each with its denominator
stated, and all three are reported whatever they show.

- **B-del** (deletion rate over true edges): delete each edge independently
  with probability ρ ∈ {0.10, 0.25, 0.50, 0.65}. ρ = 0.65 is Q10's recall
  complement at Attack-F1 ≈ 0.4. Applies to the 20 roots with `att ≠ ∅`.
- **B-add** (spurious-edge load per argument): add `k = max(1, round(ρ·n))`
  uniformly-sampled non-self, non-existing edges, ρ ∈ {0.01, 0.02, 0.05,
  0.10} — one spurious edge per 100 / 50 / 20 / 10 arguments. Applies to all
  96 roots.
- **B-mix** (both at once, matched ρ): B-del and B-add applied together at the
  same ρ ∈ {0.10, 0.25, 0.50}. Applies to the 20 roots with `att ≠ ∅`.

R = 200 repetitions per (root, arm, ρ) cell.

**Seed derivation — no wall-clock randomness.** For every cell,

    seed = int.from_bytes(blake2b(f"{root}|{arm}|{rho}|{rep}".encode(),
                                  digest_size=8).digest(), "big")
    rng  = random.Random(seed)

so the whole measurement replays byte-identically from `graphs.json`.

## Structure attribution

Registered in advance, so a null result cannot be re-described as a finding:

- **defence-chain length** — for each node, the longest directed `att` path
  ending at it. The corpus fact above predicts 1 everywhere; the battery
  measures it rather than assuming it.
- **cycle membership** of each endpoint of a perturbed edge.
- **in/out-degree** of each endpoint in the baseline graph.
- **dep fan-out** below the perturbed edge's head — pass 2 is the other way a
  single edge reaches many labels, and it is the one the Q3 note does not
  model.

Prediction registered: because every baseline attack relation is a depth-1
matching, single-edge ADDITION flips will be dominated by pass 2 (support
cascade) reach, not by pass 1 reinstatement chains. If that is what the
numbers show, it is a prediction confirmed; if not, it is recorded as a miss.

## Stopping rule

Exhaustive batteries run to completion. If Battery A exceeds 45 minutes
wall-clock, the excess is reported as a cost, roots are stratified by node
count and sampled with the seed rule above, and the truncation is stated in
`RESULTS.md`. **No silent caps.**
