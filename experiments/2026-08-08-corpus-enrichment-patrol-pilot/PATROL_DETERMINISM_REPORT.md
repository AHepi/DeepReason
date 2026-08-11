# Can the grounded extension be expanded deterministically for prose?

*Monitor report, 2026-08-09. Compiled at the operator's request from
the consistency-patrol window's committed work
(`experiments/2026-08-08-corpus-enrichment-patrol-pilot/`) and the
harness's own machinery. Every number is recomputable from committed
bytes; pointers are given for each.*

## What the patrol window actually did

1. **Phase 1 — corpus enrichment.** 10 live dual-mode-era runs on
   hard-tier questions, all committed, all replay-valid after the
   continue-to-clean recipe (RESULTS.md progress table).
2. **Phase 2 — the patrol.** All 9,277 same-problem pairs of accepted
   claims across 47 openable roots, one bounded LLM judgment each,
   raw responses preserved (`patrol_results.jsonl`): **1,941 candidate
   hits (20.9%)** — 25.2% on the enriched half vs 18.7% historical,
   at 1.5% parse-failure cost. The harness's own structural machinery
   flags none of this (attack-edge density stayed flat) — the patrol
   sees something the graph does not.
3. **The determinism correction (operator-forced, then ledgered).**
   The pilot's INPUTS are deterministic forever (append-only record;
   `verify_root` reproduces every claim byte-for-byte). Its FINDING
   step is not: each verdict was one temperature-0 model call, never
   repeated; temperature 0 reduces variance but guarantees nothing.
   The 1,941 hits are one non-deterministic pass over a fixed,
   reproducible pair set — a candidate list, not a stable set.
4. **The deterministic cross-check (operator-requested addendum).**
   Two embedders — one lexical/hashing (exactly deterministic), one
   neural/ONNX run locally, zero API calls — over all 9,277 pairs in
   ~3 minutes: hits cluster tighter and higher (semantic mean 0.895,
   stdev 0.043) than non-hits (0.845, stdev 0.080); the weakest hit
   still scored 0.706 — no hit is a weakly-related spurious pairing;
   and the non-deterministic judge's confidence correlates (r=0.399)
   with the deterministic similarity. A deterministic CORRELATE of
   the non-deterministic judgment — corroboration, not confirmation.

## The determinism question, decomposed — where "impossible" is right
## and where it is wrong

The grounded extension itself was never the problem: given the edges,
the label computation is already a pure deterministic fixpoint. The
whole question lives in **edge discovery for prose** — deciding that
two prose claims contradict. Three readings:

**Reading 1 — a sound, complete, deterministic contradiction decider
for arbitrary free prose: impossible, and the other LLMs are right.**
Deciding semantic contradiction of unrestricted natural language is
entailment-complete; no fixed endpoint-free procedure decides it
soundly and completely. This harness's own spec already encodes that
boundary ("the guarded rubric court for claims no program can
decide"). Anyone promising this is selling something.

**Reading 2 — deterministic adjudication for prose claims that carry
structure: possible, already partially built, and consistent with the
operator's own commitment doctrine.** "X passes P" vs "X fails P" is
a contradiction whatever the truth; detecting it needs only that the
claims exist in structured form (object, property, polarity). The
judgment can be paid ONCE, at write time, by the conjecturer itself —
dual-mode's exact pattern: prose stays free and unpenalized (R-g);
the criticizable surface is structured; everything downstream —
negation detection, joint execution, the grounded fixpoint — is a
pure function of committed bytes, endpoint-free forever. The
nondeterminism is confined to generation, which is where the
operator's own law says it belongs ("seats change how content is
GENERATED, never what counts as EVIDENCE").

**Reading 3 — a deterministic heuristic detector as an edge PROPOSER:
possible today, with measured error instead of soundness.** The
addendum's embedders are endpoint-free and replayable; a thresholded
similarity+opposition detector would be a deterministic function of
the record. It will have false positives and negatives — which is
acceptable for a PROPOSER (candidate attacks entering ordinary
criticism, where being wrong costs a refutation, not a corrupted
verdict) and unacceptable for a JUDGE. Determinism does not confer
correctness; it confers replayability and challengeability — the
same detector, the same bytes, the same flag, forever.

## What CP1-M settles (why it is the right next experiment for
## exactly this question)

- **S-formal measures Reading 2's coverage**: what fraction of real
  historical prose claims admit faithful structure extraction. High
  coverage → the write-time structured-claim road handles most of
  practice, and the deterministic prose extension is mostly
  achievable; low coverage → the judgment-only remainder dominates
  and Reading 1's boundary bites hard.
- **S-mech/dual-mode measures the executable frontier**: how much of
  the corpus can be adjudicated by running code — the strongest
  deterministic verdict there is.
- **The confirmed-hit set is the calibration asset**: any
  deterministic detector (Reading 3) can only have its real
  error rate measured against labeled ground truth. CP1-M's
  confirmed/refuted labels are that ground truth; the addendum's
  similarity scores are already computed for every pair, so the
  detector's ROC falls out of a join — no new calls.

## Bottom line

An entirely deterministic grounded extension for arbitrary free prose
is impossible in the strong sense — that part of the outside advice
holds. But the harness does not need the strong sense: structure paid
at write time makes prose deterministically adjudicable downstream;
execution adjudicates the computable frontier; and a deterministic
proposer with measured error can feed the criticism loop without ever
holding a gavel. How much of the record each regime covers is an
empirical question, and CP1-M is the experiment that answers it with
numbers instead of positions.
