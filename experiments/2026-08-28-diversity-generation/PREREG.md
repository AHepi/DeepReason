# PREREG — DIVERSITY OF GENERATION: stratification vs verbalized sampling

**Frozen 2026-08-28, before any provider call.** This file is committed and
pushed before the operator's key is used. The git log is the proof: every
raw response under `raw/` postdates this commit, and `driver.log`'s first
line records the commit sha this file was frozen at.

Nothing in §1–§11 may be edited after the first provider call. If a design
decision turns out to be wrong, that is recorded in RESULTS.md as a
finding, or APPENDED here as a dated appendix — never repaired in place.

---

## §1 — Authority, and what this experiment is for

Operator, 2026-08-28, approving the staged plan:

> "Ok. Do it."

And, governing method:

> "tokens are cheap. You are not. So any experiments with token spend that
> can settle things is preferred."

Design input: `docs/RESEARCH_TEMPERATURE_VS_VS_2026-08-28.md`, an external
research note committed verbatim. It is **NEVER evidence**. Its §5 decision
table grades the verbalized-sampling rows **C** — authors' own results, no
independent replication — and its §6 names the gap explicitly:

> "**No VS evaluation on hypothesis or conjecture generation.** Nearest
> proxy is synthetic math-problem generation."
>
> "**The experiment nobody has run.** Matched-budget comparison on
> scientific conjecture generation: temperature sweep vs VS vs
> stratification, semantic distinctness measured with an embedding metric
> *and* a domain-expert or criticism-stage pass rate, on a reasoning model
> with thinking off."

This experiment runs the first half of that: the embedding-metric half, on
conjecture generation, on glm-5.2 with thinking off. It exists to replace
the note's grade-C rows with our own measurement, not to confirm them.

**It settles DISTINCTNESS only.** See §9.

## §2 — What this experiment is NOT, and its write cone

- **No harness changes.** No file under `src/`, `tests/` or `docs/` is
  touched. At delivery, `git diff --stat origin/main -- src tests docs`
  must be empty; the delivery check is recorded in RESULTS.md.
- **No managed harness run.** This is a standalone API experiment calling
  the provider directly, so no soak is owed
  (`scripts/cycle_soak.py` gates ladder launches, and no ladder launches).
- **Write cone:** `experiments/2026-08-28-diversity-generation/` only.
  Two other windows may be running (a read-only audit under
  `experiments/2026-08-28-audit-run-problems/`, and a change tranche on the
  prompt-render surface). Neither territory is written here. The technique
  branch `claude/spec-to-code-technique-k5209o` is read READ-ONLY, for the
  Q1 bytes in §3, and never modified.

## §3 — The three questions (frozen bytes)

Three questions, so the result is not a fact about one prompt. All three
are stated here in full, before any call, and are frozen in
`driver.py::QUESTIONS`; the driver asserts each question's sha256 against
the value tabled below and exits non-zero on any drift.

### Q1 — `technique` (the P-T1 seed question)

Source: `experiments/2026-08-27-change-technique-run/PREREG.md` §1 on
branch `claude/spec-to-code-technique-k5209o`, read read-only.

> What is the best technique for turning an abstract specification into
> executable code — such that the result actually holds its commitments?

**Registered exclusion.** The P-T1 question carries a second sentence,
"Ground every claim in the attached record of one fully-instrumented
attempt." It is excluded here, and the exclusion is registered BEFORE any
call: this experiment attaches no record, so retaining that sentence would
instruct the model to ground claims in a document it cannot see. What is
retained is the question proper, byte-for-byte.

### Q2 — `geometry` (the P-C1/P-C2 construction subject)

Source: `experiments/2026-08-25-change-constructive-frontier/question.py`
(`QUESTION`, sha256 of the file
`7659a81ac9bbbf2cd979cd7e9994b5280acdd1e36845794ea7d1c58805bb9ea4`),
the instance reused unchanged by the P-C2 rematch.

> Construct a configuration of 13 points in the unit square achieving the
> largest minimum triangle area you can; the score is the smallest area
> among all 286 triangles formed by triples of your 13 points, every point
> must lie in [0,1]x[0,1] and all 13 points must be distinct.

**Registered exclusion, and why.** The committed string continues with a
wire-format contract — "State the construction in exactly this form, one
point per line: a line \"POINT x y\" ... then a final line \"CLAIM v\"" —
which exists so a checker can adjudicate a candidate configuration. It is
excluded here for a reason registered before any call: that contract is an
output format incompatible with all four arms' own output contracts (§5),
so retaining it would make M3 (yield) a measurement of format collision
rather than of the arms. The geometric subject — the instance, the
objective, and the constraints — is retained verbatim. What this
experiment asks for is a **conjecture about how to attack the instance**,
not a scored configuration; a scored configuration is what P-C2 measures
and is out of scope here (§9).

### Q3 — `decay` (fresh, written here)

Written in this file, not taken from the record, and of comparable
open-endedness to Q1 and Q2:

> Why do long-running software systems become harder to change over time,
> even when every individual change was reviewed, tested, and locally
> correct?

### §3.4 — Frozen digests

The three strings live in `questions.py`, which imports nothing, so the
driver and the analyser read the same bytes rather than each keeping a
copy. `freeze_questions.py` wrote their sha256 digests to
`question_digests.json` at freeze; the driver recomputes them at startup
and exits non-zero on any mismatch.

| key | sha256 of the frozen question string |
|---|---|
| `technique` | `ec18e174eef61c8851f06bb78d48805bcecc0c42a131ebc5b1c7ec2a0c7caed2` |
| `geometry` | `938411430006153e48e9aec2d5f0f8843e162a15f2b438847cc8349c5f7e6167` |
| `decay` | `875059b0cc2e11dec8b71862336f19a6357cc04eb31bb3e5c435c68fa2c8598a` |

## §4 — Provider, sampling configuration, and what is NOT swept

Single provider profile, the one the committed record uses for glm-5.2:

| field | value | source |
|---|---|---|
| endpoint | `https://ollama.com/v1` | the committed record's Ollama Cloud profile |
| model | `glm-5.2` | as above |
| thinking | **off** — `reasoning_effort: "none"` | `llm/providers.py::_ollama_reasoning`; `reasoning_disabled()` records that unset is NOT off |
| temperature | **0.9** | research note §5 row 2 safe band 0.7–1.0, top of band |
| top_p | **0.95** | research note §5 row 11 |
| seed | **not sent** | repetitions must be independent |

**Thinking is off in every arm.** Research note row 12 (grade B): CoT
suppression leaves answer-level diversity unchanged, so OFF is both the
cheap and the controlled choice. It is a constant, not a variable.

**Temperature is RECORDED, NOT SWEPT.** Rows 1–3 are grade A — multiple
independent groups — that temperature is not a diversity lever. Spending
this experiment's budget re-measuring a grade-A finding would buy nothing;
the budget goes to repetitions of the contrast that is grade C.

**Registered exclusion: no divergence clause.** Research note §5 row 6
recommends appending a population-referential divergence instruction
("stand out from other responses that might be generated for this same
task"). It is used in NO arm. It is a fifth factor; including it in some
arms and not others would confound the 2×2 in §5, and including it in all
four would leave its own effect unmeasured either way. Registered here so
its absence is a decision, not an oversight.

If the preflight in §8 finds the endpoint or model unreachable, that is
recorded as a dated appendix to this file and in RESULTS.md — never by
editing the table above.

## §5 — The four arms: a 2×2, matched candidate count and capped budget

Two factors, fully crossed: **{direct, verbalized-sampling} × {unstratified,
stratified}**. Every arm produces a **target of 60 candidates** per cell, so
M1 is not merely a count of how many candidates an arm emitted.

| arm | stratified | elicitation | call shape | candidates |
|---|---|---|---|---|
| **A DIRECT** | no | one candidate per call | 60 independent calls | 60 |
| **B STRATIFICATION** | yes | one candidate per call | 1 planning call + 6 directions × 10 calls | 60 |
| **C VERBALIZED SAMPLING** | no | k=10 per call | 6 independent VS calls | 60 |
| **D COMBINED** | yes | k=10 per call | 1 planning call + 6 directions × 1 VS call | 60 |

A→B and C→D isolate stratification. A→C and B→D isolate verbalized
sampling. D is the research note's "concrete starting configuration".

**Every call is single-turn and stateless.** No call carries any history.
The planning call for B and D runs on a **fresh context per question per
repetition**, and is never seeded with any arm's outputs; B's and D's
planning calls are made **separately** (each arm-cell mints its own), so
the two arms do not share a direction list.

### The prompts, verbatim

All arms share this system prompt:

```
You are proposing scientific conjectures. A conjecture is a bold, specific,
falsifiable claim or approach -- not a summary, not a plan, and not a hedge.
Write plainly.
```

**A — direct** (one call, repeated 60×):

```
{QUESTION}

Propose ONE conjecture in response.
Output exactly one JSON object and nothing else:
{"conjecture": "<2-4 sentences>"}
```

**Planning call** (B and D, once per arm-cell):

```
{QUESTION}

Name 6 genuinely different directions an answer to this could take --
different in mechanism, level of description, measurement, scope, formal
apparatus, or failure mode. Do not answer the question itself.
Output exactly one JSON object and nothing else:
{"directions": ["<one short phrase>", "<...>", "<...>", "<...>", "<...>", "<...>"]}
```

**B — stratified direct** (one call, repeated 10× per direction):

```
{QUESTION}

Stay within this direction: {DIRECTION}

Propose ONE conjecture in response, within that direction.
Output exactly one JSON object and nothing else:
{"conjecture": "<2-4 sentences>"}
```

**C — verbalized sampling** (one call, repeated 6×):

```
{QUESTION}

Generate 10 candidate conjectures in response, sampled from the full
distribution of responses you could give to this prompt. For each, give the
conjecture and your estimated probability that it is the response you would
give to this prompt. Every candidate's probability must be below 0.10.
Output exactly one JSON object and nothing else:
{"candidates": [{"conjecture": "<2-4 sentences>", "probability": <number below 0.10>}, ... 10 items]}
```

**D — stratified verbalized sampling** (one call per direction, 6×):

```
{QUESTION}

Stay within this direction: {DIRECTION}

Generate 10 candidate conjectures within that direction, sampled from the
full distribution of responses you could give. For each, give the
conjecture and your estimated probability that it is the response you would
give to this prompt. Every candidate's probability must be below 0.10.
Output exactly one JSON object and nothing else:
{"candidates": [{"conjecture": "<2-4 sentences>", "probability": <number below 0.10>}, ... 10 items]}
```

The probability threshold is 0.10 per research note §5 row 8 (coverage
peaks at p=0.1; below 0.01 outputs go empty). **k = 10** per row 7.
**6 directions** per row 5's "5+", and because 6 divides 60 evenly.

### Budget

- **Cap: 40,000 tokens per arm per question per repetition** (prompt +
  completion, as reported by the provider's own `usage` field). A cell that
  reaches the cap stops issuing calls and records `budget_truncated: true`.
- **Repetitions: 3** independent runs of every arm × question cell.
- Cells: 4 arms × 3 questions × 3 reps = **36**. Envelope ceiling
  36 × 40,000 = **1,440,000 tokens**. Expected spend is well under it,
  because the caps are ceilings; actual spend per arm is reported beside
  the verdict table, which is itself a measurement (research note §5 row 7
  claims ~1.1× cost for VS — this experiment measures the real ratio).
- `max_tokens`: 400 for a single-candidate call, 800 for a planning call,
  3000 for a k=10 VS call.
- Concurrency 8. Calls are independent and stateless, so concurrency
  cannot affect the measurement.

## §6 — Outcome measures (frozen before any call)

Every candidate gets a deterministic id
`{arm}-{question}-r{rep}-c{call_index:03d}-i{item_index:02d}`.
Metrics are computed by `analyse.py` from `raw/` alone, so they are
recomputable from the committed raw responses.

**Embedder.** `deepreason.llm.embedder.NeuralEmbedder`, the package
default `nomic-ai/nomic-embed-text-v1.5`, raw text, no task prefix — the
same way the harness uses it. Fingerprint recorded on every artifact, and
frozen here:

```
model:    nomic-ai/nomic-embed-text-v1.5
version:  fastembed-0.8.0+onnxruntime-1.29.0
sentinel: d6e3599ce0377000
```

Thresholds are valid only for a matching fingerprint. A run under a
different fingerprint is a different measurement and says so.

### M1 — distinct-idea count per cell

Embed every valid candidate. Similarity = cosine. **Cluster by
single-linkage agglomerative merging: two candidates join the same cluster
iff their cosine similarity ≥ τ, transitively.** Single linkage is
order-independent, so M1 is a function of the candidate set alone.
**M1 = the number of clusters.** Maximum 60, minimum 1.

**τ is frozen at τ\* = 0.7454**, and it was calibrated OFFLINE, before the
key was used, by `calibrate_threshold.py` — no provider call, no network,
committed with its output `calibration.json`. Two labelled classes of 200
pairs each, built deterministically (seed 20260828) from the 40 committed
`docs/*.md` documents:

| class | construction | median cosine | p10 | p90 |
|---|---|---|---|---|
| hard negative (different idea, **same document** — shared jargon, shared topic) | two different paragraphs of one document | 0.6233 | 0.5564 | 0.7186 |
| same-idea | a paragraph vs a 60% sentence-subsample of itself | 0.9186 | 0.8111 | 0.9709 |

τ\* is the cut maximizing Youden's J: **J = 0.94** (TPR 0.97, FPR 0.03).
The classes separate cleanly under this embedder — which is NOT a given:
the E0.1 record
(`experiments/results/e01_embedder_recalibration_report.json`) recorded
`separable.near_dup_gate = False` for bge-small on this repo's artifacts.
Honest limit, registered: the same-idea class is a sentence-subsample, a
LOWER BOUND on same-idea similarity, not a paraphrase. Real paraphrase
pairs would require a generator, and generating them with the model under
test would contaminate the threshold with the model being measured.

**Sensitivity, registered, not chosen post hoc.** M1 is reported at
τ\* and at **τ\* ± 0.05 = {0.6954, 0.7954}** (one threshold step), and the
full curve over **τ ∈ {0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90}** is
reported as a figure-table. A hypothesis in §7 counts as SUPPORTED only if
its ordering holds at all three of τ\*, τ\*−0.05 and τ\*+0.05.

### M2 — mean pairwise embedding distance per cell

Mean of `1 − cosine` over all C(n,2) pairs of valid candidates in the cell.
Threshold-free, so it cannot be moved by any choice of τ.

### M3 — yield per cell

Counted, never repaired:

| code | definition |
|---|---|
| `parse_failure` | the response is not a JSON object of the required shape |
| `empty_candidate` | a conjecture string under 20 characters after stripping |
| `off_format_count` | a VS call returning other than exactly 10 items |
| `off_format_probability` | a VS item with a missing, non-numeric, or ≥ 0.10 probability |
| `transport_error` | HTTP/timeout failure after the one permitted retry |

**One retry per call, on transport error ONLY.** A parse failure is never
retried and never repaired — it IS the measurement. There is **no top-up**:
a cell that loses candidates to failure keeps its smaller n, because
topping up would hide M3 inside M1.

Because failures make cell sizes unequal, M1 is reported twice:
**M1@60** (all valid candidates in the cell) and **M1@Nmin**, where Nmin is
the smallest valid-candidate count across all 36 cells and the subsample is
the first Nmin candidates by candidate-id ascending. **Hypotheses are
adjudicated on M1@Nmin**; M1@60 is reported beside it.

### BINDING — the probability numbers are never a metric

The model's self-reported probability values are recorded raw in `raw/` and
**NEVER enter any metric, rank, filter, ordering, or weight.** They are a
steering device that changes what "typical" refers to, not a signal:
the research note's §6 closing warning states the numbers are fabricated by
construction, and this is the companion of the standing law that seats
change how content is GENERATED, never what counts as EVIDENCE. The only
use made of a probability field anywhere in this experiment is the M3
contract check `off_format_probability` above — a check on whether the
model obeyed the output format, not a reading of the number's value.
`analyse.py` carries an assertion enforcing this, and RESULTS.md records it.

## §7 — Hypotheses, and what refutes each

Primary statistic per arm per question: the **mean M1@Nmin over the 3
repetitions**. Comparisons are per-question, and a hypothesis must hold
across questions, not on their pooled average.

**Effect-size floor, registered:** a difference under **3 clusters** (5% of
60) is reported as *no detected difference*, never as a win.

| | claim | SUPPORTED iff | REFUTED iff |
|---|---|---|---|
| **H1** | B > A on M1 — the independent-evidence claim (note §5 row 5, grade B) | B exceeds A by ≥ 3 clusters on all 3 questions, at all three τ | A ≥ B on ≥ 2 of 3 questions at τ\* |
| **H2** | C > A on M1 — the authors-only claim under test (row 7, grade C) | C exceeds A by ≥ 3 clusters on all 3 questions, at all three τ | A ≥ C on ≥ 2 of 3 questions at τ\* |
| **H3** | D ≥ B and D ≥ C | D is within 3 clusters of, or above, both B and C on all 3 questions | D falls short of B by > 3 clusters, or short of C by > 3 clusters, on ≥ 2 of 3 questions |
| **H4** | C's gain does not come with M3 degradation | C's invalid-candidate rate exceeds A's by ≤ 5 percentage points | C's invalid rate exceeds A's by > 5 percentage points |

Anything that is neither SUPPORTED nor REFUTED is recorded **INCONCLUSIVE**
and stays inconclusive; the honest ledger does not promote it.

**Registered statistical limit.** Three repetitions per cell cannot support
inferential statistics, and none is claimed. The decision rules above are
the whole adjudication. Repetition-level spread is reported (min/median/max
per cell) so a reader can see whether a stated difference is larger than
the noise it sits in.

## §8 — Order of operations

1. This file, `calibrate_threshold.py`, `calibration.json`,
   `freeze_questions.py`, `question_digests.json` and `driver.py` are
   committed and pushed. **The key is not used before this push.**
2. Preflight: ONE call to the endpoint confirming reachability, model id,
   and that `reasoning_effort: "none"` returns an empty reasoning payload.
   Recorded in `preflight.json`. A deviation from §4 is appended here as a
   dated appendix, never edited in.
3. The driver runs. Every raw response is written to `raw/` verbatim —
   the complete provider JSON, including `usage` and any reasoning field —
   before any parsing. Raw responses are committed as they land.
4. `analyse.py` computes M1/M2/M3 from `raw/` alone.
5. RESULTS.md.

## §9 — What this experiment does NOT measure

**Survival under criticism is NOT measured here.** Whether a more distinct
population of conjectures is a BETTER one — whether the extra ideas survive
the harness's criticism stage — is a separate, in-harness leg and is
registered as out of scope. This experiment settles **distinctness only**.
No claim about conjecture quality, correctness, or value may be drawn from
its numbers, and RESULTS.md will say so in its own residue section.

Also not measured: temperature (recorded constant, §4), the divergence
clause (registered exclusion, §4), k-scaling, the probability threshold
curve, min-p (not exposed by this endpoint), and any model other than
glm-5.2.

## §10 — Falsifiable prediction about the experiment itself

Registered so the instrument can fail visibly: if the four arms' M1@Nmin
values all fall within 3 clusters of each other at τ\*, this instrument
detected nothing, and that is the finding — recorded as such, not rescued
by moving τ, changing the metric, or adding arms.

## §11 — Delivery obligations

- `git diff --stat origin/main -- src tests docs` empty, recorded.
- Raw responses committed verbatim; metrics recomputable from them alone.
- RESULTS.md leads with the per-hypothesis verdict table (arm × question ×
  repetition; M1/M2/M3) and token spend per arm beside it, then the honest
  residue: "more distinct" does not mean "better".
- If an arm wins clearly, ONE parked, ready-to-send prompt for the
  follow-on (wiring the winning generation shape in as configuration, per
  the modularity law, plus the in-harness survival-under-criticism leg).
  **Parked, not built.**

---

## Appendix A — 2026-08-28: repetitions extended from 3 to 9

**Appended, not edited in place**, per this file's own preamble. Registered
BEFORE any metric was computed: the git history is the proof — this appendix
is committed while `metrics.json` does not yet exist, and `analyse.py` had
never been run at the time of the commit that introduces it. `driver.log`
records the 36 registered cells finishing at 2026-08-28T15:46:30Z with
369,746 tokens spent; nothing in `raw/` had been read.

**Authority.** Operator, 2026-08-28, verbatim:

> "Tokens are cheap. use as many as you need"

**What changes, and only this.** §5's `Repetitions: 3` becomes
**Repetitions: 9** (reps 4–9 are added; reps 1–3 stand unchanged and are
re-used, not re-run). Cells become 4 arms × 3 questions × 9 reps = **108**.

**What does NOT change.** Everything else is untouched, and this is the
point of appending rather than editing:

- §7's four hypotheses, their SUPPORTED/REFUTED rules, and the 3-cluster
  effect-size floor are IDENTICAL. Only the number of repetitions the
  per-question mean is taken over increases.
- §6's metrics, τ\* = 0.7454, the τ grid, the M3 codes, the no-top-up rule,
  and the binding rule on probability values are IDENTICAL.
- §4's sampling configuration and §3's question bytes are IDENTICAL.
- §10's null-result condition is IDENTICAL.

**Why.** §7 registered a limit honestly — "three repetitions per cell cannot
support inferential statistics, and none is claimed". The operator's message
removes the constraint that made that limit necessary. Nine repetitions per
cell is still not a licence to run inferential tests that were not
registered, and none is added; what it buys is that a stated difference can
be read against nine samples of its own noise instead of three.

**Envelope.** The registered ceiling of 1,440,000 tokens (§5) is
UNCHANGED. Measured spend at 3 reps was 369,746 tokens, so 9 reps projects
to ≈1,109,000 — inside the ceiling already registered. No new envelope is
requested and none is granted here.

**Honest note on ordering.** Extending repetitions after seeing results
would be a design change bought with knowledge of the answer. That is why
this is registered blind, and why the ordering claim above is stated as
something a reader can check in the commit graph rather than something they
must take on trust.
