# Pre-plan: grounded-extension overlays — catching what the acceptance pass cannot see

Status: PROPOSED. Written 2026-08-08 by the monitor session on the
operator's instruction ("Can we extend Dung's grounded extension? Can
you think of any ways to do it to catch more inconsistencies in
another pass? ... Let's move to this next.").

## The baseline and its three blind spots

Acceptance is the GROUNDED extension of the attack graph (artifacts as
nodes, recorded refutation warrants as attack edges): accept what is
defensible from unattacked ground, iterate to the least fixed point.
Maximally skeptical — the right OFFICIAL semantics, and this plan
never changes it (a semantics change would flip committed roots:
wrong by definition). The blind spots, each inviting a SECOND PASS
that is additive only:

1. **Missing edges.** Conflict-freeness holds only over RECORDED
   attacks; two accepted artifacts that contradict each other stay
   jointly accepted forever if no one minted the edge.
2. **Silent cycles.** Mutual and odd attack cycles land "undecided"
   with no signal distinguishing live controversy from noise.
3. **Meaning-blindness.** The graph never executes anything; two
   formally-backed artifacts can pass their own checks while their
   checkers are JOINTLY unsatisfiable on overlapping input domains.

Epistemology guardrails, standing: a second pass may MINT candidate
attack edges (which enter the ordinary criticism loop) or emit typed
ADVISORY reports (attention routing) — it may never relabel, never
bypass criticism, and per R-g/operator law must be kind-blind in
anything that touches rank or exposure.

## Rung O1 — offline retrodiction  [MEASURE ONLY, no src/ change]

Before building anything live: compute, over EVERY committed root's
final state, what each overlay WOULD have caught. Read-only analysis
scripts in the tranche directory (promotion to `tools/` only if the
numbers earn it), no LLM calls, no provider, no new records:

- **O1a — semantics diff.** Grounded vs preferred extensions; report
  every artifact skeptically-accepted-under-preferred but blocked from
  grounded, and every attack-graph SCC (cycle cluster) containing an
  undecided artifact: the controversy inventory, per root.
- **O1b — joint-execution probe.** For every PAIR of accepted
  formally-backed artifacts within one root whose executable
  commitments declare overlapping admissible input domains: fuzz for
  inputs where both checkers can be satisfied; report pairs where the
  conjunction looks unsatisfiable (bounded budget, typed
  INCONCLUSIVE when the budget dies — never claim more than the
  probe shows).
- **O1c — floating foundations.** Dependence-graph SCCs of accepted
  artifacts with no support path from ground (evidence/admission):
  self-supporting clusters, per root.
- **O1d — load-bearing warrants.** For each accepted artifact, the
  minimum set of warrants whose invalidation flips its label
  (single-warrant sensitivity first; report the distribution — how
  much acceptance rests on one edge).

Deliverable: analysis scripts + a measured report (counts per root
per overlay, with the specific artifact ids so spot-checks are one
command) + RESULTS.md honest-ledger segment including the residue —
what offline analysis structurally cannot see (missing edges needing
semantic judgment, i.e. the LLM consistency patrol, which is
inherently live and deliberately NOT in this rung). Accept: every
number recomputable from committed bytes; zero `src/`/`tests/`/
`tools/` diff; full gate untouched (run once at the boundary to
prove it — expect the program's new baseline: 0 failed, no
exceptions); docs_verify green if any map doc gains the concept.

## Rung O2 — decided by O1's numbers  [DESIGN-AND-STOP]

Whichever overlay(s) O1 shows non-trivial catches for, design the
live counterpart with the guardrails above (candidate-attack minting
through the ordinary loop; advisory typed reports; kind-blind). If
O1's counts are ~zero across the board, O2 is a one-paragraph
closure recording that the graph closure is healthy — a negative
result recorded as one, per house law. The LLM consistency patrol
(blind spot 1's full remedy) is priced here, not before: its cost
shape (pair selection, batching, budget) should be chosen against
O1a/O1b's actual cluster sizes.

## What could kill it

- **Preferred-extension computation cost** — worst case exponential;
  the attack graphs per root are small (hundreds of artifacts), and
  O1a must PASTE per-root node/edge counts before computing, stopping
  with a typed TOO-LARGE rather than hanging.
- **Joint-domain inference (O1b)** — deciding two checkers share an
  input domain may itself need judgment; O1b restricts to pairs with
  machine-comparable input gates and reports the excluded remainder
  honestly rather than guessing.
- **Overlay drift** — an advisory report nobody consumes rots; O2
  must name the consumer (scheduler attention, criticism budget, or
  operator report) before any live build.
