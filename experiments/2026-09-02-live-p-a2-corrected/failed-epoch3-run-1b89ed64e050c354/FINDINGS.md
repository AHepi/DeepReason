# Findings

## Question

Consider asynchronous majority dynamics on a random 3-regular graph on n vertices: at each step one uniformly random vertex adopts the majority opinion of its three neighbors. Starting from a uniformly random two-coloring, as n grows, does the probability of reaching unanimous consensus tend to 1, to 0, or to a constant strictly between? Characterize the finite obstruction structures (locally stable mixed configurations) that prevent consensus, and give either a proof sketch or a falsifiable quantitative law for how their prevalence scales with n.

## Positions the record accepts

13 positions stand formally accepted. Where they answer the same question differently they are unresolved rivals: the record deliberately preserves the disagreement rather than merging it.

- As n grows, the probability of reaching unanimous consensus tends to a constant strictly between 0 and 1, not to 1 or 0. `[513b3472f223]`
- nu: verdict of pa1-scaling-law@v1 on 005ffbd5709079d789561c5aa152caea47e6dd20519451bd49b9a0bb214b2d25 is sound and relevant `[d9ae544b53a0]`
- critic: pa1-scaling-law@v1 failed on 005ffbd57090 `[d35a6dd7a77c]`
- nu: verdict of pa1-scaling-law@v1 on 363ee7a4329582bf8bb2833ce99ee3968491a6cc12b15b821a00956275589dd4 is sound and relevant `[a9b051224d44]`
- critic: pa1-scaling-law@v1 failed on 363ee7a43295 `[77102c4075db]`
- nu: verdict of pa1-limit-verdict@v1 on eb62c8ac2ca50c777de883ec5980764150d3716279fd4c7fe2f07a1fcc84f25a is sound and relevant `[954f89ea8d07]`
- critic: pa1-limit-verdict@v1 failed on eb62c8ac2ca5 `[647e1cbeee52]`
- On a random 3-regular graph with asynchronous majority dynamics from a uniform random two-coloring, the probability of reaching unanimous consensus as n grows tends to a constant strictly between 0 and 1 (bounded away from both 0 and 1). The obstruction structures are locally stable mixed configurations: colorings in which every vertex agrees with at least two of its three neighbors, so no vertex ever changes its opinion. In any minimal such mixed configuration the disagreeing edges form a matching (each vertex has exactly one neighbor of the opposite color and two of the same), i.e. the verte… `[a3002cb7e64f]`
- The probability of reaching unanimous consensus tends to 1 as n → ∞ (probability of consensus approaches 1, i.e. is 1 - o(1)): no locally stable mixed obstruction survives on a random 3-regular graph whp. Candidate obstructions are configurations where every vertex agrees with the majority of its three neighbors while the coloring stays mixed; but on a random 3-regular graph, which whp has large girth and is an expander, any such mixed configuration forces the disagreeing-edge structure to be a matching separating large monochromatic induced subgraphs, and random expanders have edge expansion … `[efcd6d295035]`
- Consensus probability as n grows tends to 0: the dynamics whp gets trapped in a locally stable mixed configuration, because such obstructions are abundant. The obstruction structures are frozen colorings where every vertex has at least two of its three neighbors of its own color; equivalently the disagreeing edges form a subgraph of maximum degree 1 on each side. The simplest and dominant gadget is a pair of adjacent disagreeing-edge endpoints forming an isolated cross-edge between two internally monochromatic induced subtrees. Quantitative law: the expected number of such absorbing mixed conf… `[79e3b803c1fd]`
- Falsifiable-law candidate (deliberately minimal-commitment): whatever the limiting consensus probability is, the decisive quantity is the density of locally stable mixed configurations, and it obeys a clean quantitative law — the expected number of vertices that end in a dissenting matched pair after dynamics stabilizes scales like Θ(n) with an explicit per-vertex constant ρ ≈ 0.05–0.15 (empirically measurable), so the probability that this expected count is zero (i.e. consensus) converges to a Poisson-type limit: probability of consensus → exp(-ρn) is ruled out; instead the count does not con… `[77cde74a5abb]`
- Counterexample-first structural claim: the correct obstruction characterization must include not only static fixed points but also period-2 orbits, and their inclusion flips the verdict to consensus probability tending to 0 on random 3-regular graphs. Asynchronous majority dynamics on 3-regular graphs is known (Goles–Olkiewicz style results) to eventually enter a cycle of period at most 2; a locally stable mixed configuration in the broad sense is either a frozen fixed point (each vertex agrees with at least two of its three neighbors) or a 2-cycle where a vertex with a tied neighborhood oscil… `[16a45afde6fd]`
- Atypical, decisive-experiment framing: the entire verdict question reduces to one measurable number — the probability p_n that a random 3-regular graph admits ANY locally stable mixed coloring reachable from a uniform start. Conjecture: p_n → p* with 0 < p* < 1, and the consensus probability equals 1 - p* + o(1), i.e. tends to a constant strictly between 0 and 1. Obstruction structure: a locally stable mixed configuration is a two-coloring in which no vertex is in the minority among its neighborhood; every vertex agrees with the majority of its three neighbors; the color classes then have the … `[344055628a4a]`

## Positions the record refuted

- As n grows, the probability of reaching unanimous consensus tends to 1 (whp). `[005ffbd57090]`
- As n grows, the probability of reaching unanimous consensus tends to 0. `[363ee7a43295]`
- The probability of consensus tends to a constant strictly between 0 and 1, with the constant controlled by the largest stable 2-core traps, not only short cycles. `[eb62c8ac2ca5]`

---
Every statement above is derived from the append-only run record; nothing was generated by a model for this report. Accepted does not mean true — it means the position survived recorded criticism so far, and the run remains continuable.
