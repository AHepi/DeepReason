<!-- honest ledger; every number here is produced by analyze.py from the
     committed case tables. Residue is stated at the end, not smoothed. -->
# RESULTS — grounded-extension flip rate under attack-edge error

Date: 2026-08-22 · Branch `claude/grounded-flip-rate-measure-x36e1w` ·
Base `d9b8ef2c2` · Read-only tranche (no `src/`, no `tests/`, no run root
touched)

Answers `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` open item 2:
*empirical grounded-label flip rate vs. attack-edge error rate*, marked
`[UNKNOWN] — nobody has run it`.

Design pre-registered in `GOAL.md` before any battery ran. Everything below
is arithmetic over `results.json`, which `analyze.py` builds from
`battery_a_cases.csv.gz`, `battery_b_cells.json` and
`battery_c_relevance.json`.

---

## 0. Headline

**On this harness's own 96 committed argument graphs, the grounded extension
is not the fragile part. The support cascade underneath it is.**

One spurious attack edge changes the *grounded labelling* of 0.99 arguments
on average and never more than 2. The same edge changes DeepReason's
*reported status* of 2.09 arguments on average, up to 84 — and 52.6 % of
those changes lie strictly outside the attack cone that Dung directionality
bounds. The amplifier is `dep`, not `att`.

Three numbers carry the Rung 8 decision:

| | value |
|---|---|
| single spurious edge flips **zero** labels (stability mass) | **2.29 %** |
| single spurious edge flips zero labels **of the seed question** | **96.15 %** |
| flips that escape the Dung attack cone | **52.6 %** of all flips |

---

## 1. The corpus, and what it is not

`inventory.py` → `inventory.json`; `cache_graphs.py` → `graphs.json`.

- 107 committed roots carry a `log.jsonl`. **96 open under the current
  version.** 11 refuse with `UnsupportedRunManifestVersionError` and are
  excluded by name in `inventory.json` — lawful under the 2026-08-14 operator
  law (old roots owe the future nothing).
- **6 370 artifacts** (min 4, median 53, max 304); **5 165 `dep` edges**.
- **60 `att` edges in the entire corpus. 76 of 96 roots have `att = ∅`.**
- Baseline labels: 6 309 `accepted`, 60 `refuted`, 1 `suspended_unsupported`,
  0 `suspended`.
- 60 edges ↔ 60 `refuted` nodes: **no node is attacked twice and no attacker
  is itself attacked.** Every attack relation in the corpus is a **depth-1
  matching** — no directed cycle, no self-attack, no defence chain longer
  than one hop anywhere in 6 370 arguments.

That last fact is the corpus's dominant property and it must be read before
any number below. The literature's amplifying structures for grounded
semantics — long defence chains, odd-length attack cycles — **do not exist
here**. `cache_graphs.py` asserts per root that labels re-derived from the
cached relations equal `h.state.status`, so the cache is a faithful stand-in
for the run; that assertion passed on all 96.

**Why the graphs are this sparse** is `DR-SEAM-adjudication-x-rules`: an
attack edge exists only where criticism minted a *warrant*, and a rule's
entire power over status is the right to attach warrant/target/validity-node.
Criticism that produced prose but no warrant produces no edge. This is the
same condition `verification/report.py`'s adjudication-blindness detector
fires on, now visible at corpus scale (parked, §7).

## 2. Measured code path

    from deepreason.adjudication.grounded import label0      # pass 1, Dung
    from deepreason.adjudication.support  import final_labels # pass 2
    labels = final_labels(label0(nodes, att), dep)

Exactly `Harness._adjudicate`'s two passes with `att` substituted. Not a
reimplementation — a reimplementation would measure itself.

**Modelling assumption, registered:** `build_att` is *not* re-run. The
perturbation models error in the extracted attack RELATION, which is the
level Q10 measures Attack-F1 at. Errors introduced further upstream — at the
warrant, before `build_att`'s closure rules lift them onto every carrier —
are NOT measured here and could have a larger radius (§7, parked).

Throughout, a **pass-1 flip** is a change in the grounded labelling itself; a
**pass-2 flip** is a node whose `Status` moved while its grounded label did
not — the support cascade.

## 3. Battery A — single edge, exhaustive

645 624 cases, no sampling, 151 s: every one of the 60 possible deletions and
every one of the 645 564 possible additions of an ordered non-self pair.

### 3.1 Deletion — a missed attack edge (Q10's dominant error direction)

| | |
|---|---|
| cases | 60 (exhaustive) |
| stability mass (zero flips) | **0 %** |
| blast radius | mean 1.017, median 1, p99 2, **max 2** |
| pass-1 flips | exactly 1 in every case |
| pass-2 flips | 1 across all 60 cases |

Transitions: `refuted→accepted` 58, `refuted→suspended_unsupported` 2,
`suspended_unsupported→accepted` 1.

Deleting an edge is never inert and never wide. It reinstates its own target
and, once in sixty, one dependent. **A false-negative extractor on this
corpus loses exactly the finding it missed — no more.** That is the mild
direction, and it is the direction Q10 says LLM extractors err in most.

### 3.2 Addition — a spurious attack edge

| | whole verdict | pass 1 only (Dung) | pass 2 only (cascade) |
|---|---|---|---|
| cases | 645 564 | 645 564 | 645 564 |
| stability mass | **2.29 %** (14 784) | 2.29 % | 90.38 % |
| mean | 2.086 | **0.988** | 1.098 |
| median | 1 | 1 | 0 |
| p90 | 2 | 1 | 0 |
| p95 | 7 | 1 | 6 |
| p99 | 24 | **2** | 23 |
| p99.9 | 73 | 2 | 72 |
| **max** | **84** | **2** | **83** |

Transitions (1 346 492 flips):

| transition | count |
|---|---|
| `accepted → suspended_unsupported` | 708 188 |
| `accepted → refuted` | 630 433 |
| `refuted → accepted` (reinstatement) | 7 145 |
| `suspended_unsupported → accepted` | 287 |
| `suspended_unsupported → refuted` | 287 |
| `accepted → suspended` | 60 |
| `refuted → suspended` | 60 |
| `refuted → suspended_unsupported` | 32 |

Read the first two rows against each other: **more status changes come from
the support cascade than from the attack itself.** The 60 + 60 `→suspended`
flips are precisely the 60 cases where the spurious edge is the reciprocal of
an existing one, creating the corpus's only two-cycles.

### 3.3 Per root

Median root: 1.273 flips per spurious edge. 20 of 96 roots have a maximum
blast radius of exactly 1 — a spurious edge there can never do more than
refute its own target. **33 of 96 roots contain at least one edge that flips
≥ 10 labels.**

| root | n | att | dep | mean flips | max |
|---|---|---|---|---|---|
| `live_research_2026-07-29/selfstudy/.../completed-epoch3-run-9175f0ec…` | 79 | 0 | 249 | 4.165 | 49 |
| `live_research_2026-07-29/selfstudy/.../failed-epoch2-run-9175f0ec…` | 53 | 0 | 158 | 4.038 | 25 |
| `2026-08-12-live-grounded-extension-expansion/run` | 304 | 16 | 807 | 3.874 | **84** |
| `2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/live_run_v7` | 27 | 0 | 39 | 3.259 | 15 |
| `bronze_flat_2026-07-13/deepseek-v4-pro` | 34 | 11 | 0 | 0.693 | 2 |

The last row is the control that makes the pattern unmistakable: 11 attack
edges and **zero** `dep` edges — the most attack-dense root in the corpus is
also the *least* fragile one. Fragility tracks `dep`, not `att`.

## 4. Directionality — the Q3 `[INFERRED]` claim, tested

The note infers from Baroni & Giacomin that a single edge error's blast radius
is bounded to the perturbed edge's downstream cone. Measured over all
645 624 cases, distances taken from the perturbed edge's head:

| | count |
|---|---|
| pass-1 flips outside the **att** cone | **0** |
| pass-2 flips inside the **att** cone | **0** |
| flips outside the **full** cone (att ∪ reversed `dep`) | **0** |
| max distance, att cone | 1 |
| max distance, full cone | 2 |

The partition is exact, not approximate. So:

**Confirmed** for the grounded labelling. Directionality holds on real graphs
with no exceptions in 645 624 trials, and it holds *tightly*: no pass-1 flip
was ever more than one hop from the perturbed edge.

**Refuted for DeepReason's actual verdict.** 708 475 flips — 52.6 % of all of
them, in 62 083 cases (9.62 % of additions) — lie outside the Dung cone
entirely. They are not a violation of Baroni & Giacomin; they are outside its
scope. Pass 2 walks the `dep` DAG, and a support relation is not an attack
relation, so no argumentation-semantics directionality theorem covers it.

**This is the finding with the most consequence for Rung 8.** An
uncertain-edge layer built on IAF relevance reasons about the attack graph.
On this corpus that is the well-behaved half of the computation. Adding it
without also modelling `dep` would certify the half that was not in danger.

## 5. Structure — what makes an edge dangerous

Two features, and only two, explain nearly all the variance.

**(a) The tail must bite.** An attack from a node that is not itself in the
grounded extension does nothing.

| baseline status of tail `x` | cases | zero-flip share | mean flips |
|---|---|---|---|
| `accepted` | 637 594 | 1.12 % | 2.110 |
| `refuted` | 7 667 | **99.22 %** | 0.016 |
| `suspended_unsupported` | 303 | 5.28 % | 4.099 |

**(b) The head's support cone sets the radius.**

| `dep` cone below head `y` | cases | mean flips | max |
|---|---|---|---|
| 0 | 582 438 | 0.990 | 3 |
| 1–2 | 9 565 | 2.142 | 3 |
| 3–5 | 17 990 | 5.463 | 6 |
| 6–10 | 16 021 | 7.441 | 11 |
| 11–25 | 13 148 | 20.357 | 25 |
| ≥ 26 | 6 402 | **41.300** | **84** |

Pearson r(dep-cone, flips) = **0.9771** over all additions, **0.9975**
restricted to accepted tails. And the relationship is a closed form, not a
trend:

> **`n_flips = 1 + |dep-cone(y)|`** whenever `x` is `accepted` and `y` has no
> outgoing attack — **exact in 96.44 %** of the 630 433 cases meeting that
> precondition.

**Defence-chain length and cycle membership explain nothing**, because the
corpus has neither: the head's defence-chain length is 0 in 637 957 cases and
1 in 7 607, never more; no root's attack relation contains a cycle. The
prereg predicted this and predicted that pass-2 reach would dominate. Both
confirmed. **The literature's amplifying structures are absent and a
different one — support fan-out — took their place.**

**A dangerous edge on these graphs is: any accepted argument, pointed at a
premise that many conclusions rest on.** Nothing about the attack relation's
shape is involved.

## 6. Battery B — error-rate curves

524 cells × 200 seeded reps = 104 800 recomputes, 7 s. Seeds derive from root
id and cell coordinates via blake2b; the battery replays byte-identically.
Flip fraction is labels flipped ÷ artifacts, node-weighted across roots.

**B-add** — `k = max(1, round(ρ·n))` spurious edges, one per 100/50/20/10
arguments, all 96 roots:

| ρ | mean edges added | corpus flip fraction | median root | worst root |
|---|---|---|---|---|
| 0.01 | 1.04 | **2.49 %** | 2.58 % | 62.0 % |
| 0.02 | 1.55 | 3.97 % | 3.63 % | 63.3 % |
| 0.05 | 3.39 | 8.24 % | 6.30 % | 67.1 % |
| 0.10 | 6.67 | 14.44 % | 11.15 % | 74.1 % |

**B-del** — each true edge dropped with probability ρ (ρ = 0.65 is Q10's
recall complement at Attack-F1 ≈ 0.4), the 20 roots with `att ≠ ∅`:

| ρ | mean edges deleted | corpus flip fraction | median root | reps flipping nothing |
|---|---|---|---|---|
| 0.10 | 0.29 | **0.29 %** | 0.11 % | 3 135/4 000 |
| 0.25 | 0.75 | 0.74 % | 0.31 % | 2 325/4 000 |
| 0.50 | 1.52 | 1.50 % | 0.62 % | 1 348/4 000 |
| **0.65** | 1.95 | **1.91 %** | 0.84 % | 929/4 000 |

**B-mix** and the matched comparison, all three arms on the same 20 roots:

| ρ | B-del | B-add | B-mix |
|---|---|---|---|
| 0.10 | 0.29 % | 16.82 % | 16.81 % |
| 0.25 | 0.74 % | — | 31.01 % |
| 0.50 | 1.50 % | — | 43.94 % |

B-mix and B-add coincide at ρ = 0.10 to two decimal places. **Deletion
contributes essentially nothing to the mixed error rate.** The whole curve is
the addition arm.

The single most important row is B-del at ρ = 0.65: at the miss rate the
literature actually reports for LLM attack-edge extraction, **1.91 %** of
labels move, and 23 % of individual draws move nothing at all. Missing edges
— the error direction Q10 says dominates — is close to harmless here.

The worst-root column is inflated by small roots: at ρ = 0.01 the worst is a
4-artifact root where one flip is 25 % of the graph. The node-weighted corpus
column is the honest aggregate.

## 7. Battery C — IAF relevance, measured

The Rung 8 proposal's certificate is not "the graph is stable"; it is
**"of N uncertain edges, k are relevant"** — relevant *to a target set of
arguments whose status you care about*. Battery C re-runs the exhaustive
sweep and asks, per case, whether any member of a target set flipped.

| target set | direction | relevant share | roots where k = 0 |
|---|---|---|---|
| all artifacts | addition | **97.71 %** | 0 / 96 |
| all artifacts | deletion | 100 % | 0 / 20 |
| **seed question** | **addition** | **3.85 %** | 0 / 96 |
| **seed question** | **deletion** | **16.67 %** | **18 / 20** |
| critic artifacts | addition | 35.57 % | 6 / 96 |
| critic artifacts | deletion | 0 % | **20 / 20** |
| baseline-refuted artifacts | addition | 1.12 % | 76 / 96 |
| baseline-refuted artifacts | deletion | 100 % | 0 / 20 |

Not one of the 6 370 artifacts is invulnerable to every single-edge error.

**The target set decides whether the certificate is worth anything.**

- Whole-graph: 97.71 % of candidate edges are relevant, and **no root in the
  corpus would ever produce k = 0.** A whole-graph stability certificate is
  a certificate that never fires.
- Seed question: **96.15 % of candidate spurious edges are irrelevant**, and
  the seed's status survives *any* deletion of a true edge on 18 of 20 roots.
  A seed-targeted certificate carries real information and would usually be
  favourable.
- Criticism verdicts: **no deletion, anywhere, changes a critic artifact's
  status** — 20 of 20 roots read k = 0.

## 7b. Deviations from the pre-registration

Recorded because a prereg that quietly grows is not a prereg.

- **Battery C was not registered.** `GOAL.md` registers batteries A and B
  only. Battery C was added after reading A's directionality result, because
  the whole-graph flip rate turned out not to be the quantity the Rung 8
  certificate is written in. It is a *new exhaustive sweep over the same
  registered case space* — no new perturbation, no sampling, no seed, no
  discretion — so it cannot have been tuned to a result, but it is
  exploratory rather than confirmatory and §9's target-set argument should be
  read as such.
- **`cache_graphs.py` was extended** after registration to cache provenance
  roles, which Battery C's target sets need. The cached relations, node order
  and baselines are unchanged, and the per-root assertion that re-derived
  labels equal `h.state.status` still passes on all 96. Batteries A and B were
  re-run from the extended cache; every number in §3–§6 is unchanged.
- **Nothing registered was dropped.** Both directions, all three rate arms,
  and all four structure features ran as written, including the two —
  defence-chain length and cycle membership — that turned out to explain
  nothing.
- **The stopping rule did not fire.** Battery A took 156 s against a 45-minute
  budget, so the exhaustive sweep ran whole and no sampling rule was used.

## 8. Residue — what this does not show

- **The attack relations are depth-1 matchings.** No result here says
  anything about grounded semantics on graphs with defence chains or odd
  cycles. Where the literature locates the danger, this corpus is empty. The
  measurement is of *these* graphs.
- **The addition candidate space is all ordered pairs**, uniform. A real
  extractor proposes edges only between argumentatively related components.
  2.29 % stability mass and 97.71 % relevance are over a uniform pair space
  and are therefore *not* the rates a deployed extractor would produce. The
  direction of the bias is not established: the realistic subset is enriched
  for related pairs, which could be either more or less dep-connected.
- **`build_att` is not re-run** (§2). Warrant-level errors that propagate
  through validity-node closure and case-law closure onto every carrier are
  unmeasured, and closure could widen the radius.
- **Deletion rests on 60 cases.** Exhaustive, but 60 is 60. The
  deletion-direction conclusions are the thinnest in this report.
- **One harness, one provider family, one question set.** Nothing here
  generalizes to argument graphs mined from essays, which is the setting
  Q10's F1 was measured in.
- **Flip ≠ error.** A flipped label is a changed verdict, not a wrong one.
  This measures sensitivity to perturbation, not accuracy against truth. No
  ground-truth attack relation exists for these graphs and none is claimed.
- Accepted does not mean true. These are the record's numbers, not the
  world's.

## 9. For the Rung 8 decision — recommendation, not decision

**Necessary-only-for-certain-structures, and not the structures the research
note predicted.**

The case for an IAF layer as written in "The one item to act on first" is
that grounded semantics is the worst-behaved semantics under edge
uncertainty. On this corpus that case does not survive contact: the grounded
labelling moves 0.99 arguments per spurious edge and never more than two, the
directionality bound holds exactly and tightly, and the error direction the
extractor literature says dominates — missed edges — moves 1.91 % of labels
at a 65 % miss rate. Buying an uncertain-edge layer to protect the grounded
extension would be buying insurance on the component that is already
stable.

What is *not* stable is the support cascade beneath it. One spurious edge
into a well-supported premise moves up to 84 statuses, 52.6 % of all label
changes lie outside the cone any argumentation-semantics stability result
can reason about, and the blast radius is `1 + |dep-cone(head)|` to four
significant figures. That exposure is real, it is large, and an IAF layer
over `att` alone does not touch it.

Three roads, priced:

1. **Uncertain-edge layer over `att` only, as proposed.** Buys a certificate
   that on this corpus reads k > 0 for every root and 97.71 % of candidate
   edges — it never certifies anything — and leaves 52.6 % of the exposure
   outside its scope. Not recommended on this evidence.
2. **Target-set relevance, cheap version.** Keep crisp adjudication; add a
   diagnostic that reports relevance *for the seed question* rather than for
   the whole graph. On these numbers it would report "96 % of possible edge
   errors cannot change this verdict" and would read k = 0 for deletions on
   18 of 20 roots. This is a real certificate, it is arithmetic over the two
   relations the harness already has, and Battery C is a working prototype
   of it. **Recommended as the first rung.**
3. **Extend uncertainty to `dep`, not just `att`.** The measured exposure is
   here. It is also the larger and less charted piece of work — Dung's
   framework does not model support, so the IAF machinery does not port
   over unchanged. Worth scoping only after (2) shows what the seed-targeted
   numbers look like on new runs with denser attack relations.

One caution attached to all three: 76 of 96 roots have an empty attack
relation. Any Rung 8 design validated only on this corpus is validated on
graphs that barely have the structure it reasons about. The measurement
that would change these conclusions is a corpus of runs whose criticism
actually mints warrants — that is a live-run question, not an offline one.

---

### Artifacts

| file | what |
|---|---|
| `GOAL.md` | goal + pre-registration (written before any battery) |
| `inventory.py` / `inventory.json` | which roots open under the current version |
| `cache_graphs.py` / `graphs.json` | one replay per root; the cached graphs |
| `perturb.py` | shared machinery; both reachability cones |
| `battery_a.py` / `battery_a_cases.csv.gz` / `_detail.json` / `_roots.json` | 645 624 exhaustive single-edge cases |
| `battery_b.py` / `battery_b_cells.json` | 524 rate cells × 200 seeded reps |
| `battery_c.py` / `battery_c_relevance.json` | IAF relevance by target set |
| `analyze.py` / `results.json` | every number in this document |
| `PARKED.md` | what was noticed and not acted on |

Reproduce: `python cache_graphs.py && python battery_a.py && python
battery_b.py && python battery_c.py && python analyze.py` (~9 min).
