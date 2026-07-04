# DeepReason — What We Built, What Happened, and Why It Matters

*A guided tour of the project as of 2026-07-05. Written to be read start to
finish; every claim here is checkable against the repo and the run
directories.*

---

## 1. The idea in one paragraph

DeepReason is a machine that does **Popperian epistemology as bookkeeping**.
An LLM proposes ideas ("conjectures"); deterministic code decides what
survives — never the LLM. Ideas are only ever killed by *criticism with a
warrant*: a failed program check, a lost trial, a lost head-to-head ruling.
Nothing is ever deleted, no status is ever final, and every state the system
has ever been in can be reproduced byte-for-byte from an append-only event
log. The LLM is deliberately reduced to a single narrow job: a pure function
from a rendered "pack" of context to schema-validated JSON. All the
epistemology — who's accepted, who's refuted, who gets reinstated when a
test is discredited — lives in the harness.

The build spec (`docs/harness-spec-v1.3.md`) comes from a theory called the
*creativity calculus*; the code implements it section by section.

## 2. The theory, in the order you need it

**Artifacts are untyped.** Everything — a conjecture, a criticism, a piece
of evidence, a quality standard, even the rules themselves — is the same
kind of object: content (opaque bytes) plus an *interface*. There is no
`kind` field anywhere. What a thing *does* comes from its structure:

- carrying a **warrant** against a target creates an *attack edge*;
- declaring a **dependence ref** on a target creates a *support edge*;
- listing **commitments** ("if this check fails, I fail") is the artifact's
  declared attack surface.

**Adjudication is a two-pass graph computation** (Dung's grounded
semantics, then a support cascade). Unattacked things are accepted. If a
critic attacks a conjecture, the conjecture is refuted — unless something
attacks the *critic*, in which case the conjecture is reinstated
automatically. Reinstatement is a theorem of the graph, not a feature
someone codes. If your premise falls, you become `suspended_unsupported` —
orphaned, not false.

**Every attack needs a warrant, and every warrant carries a validity node
(ν)** — an ordinary, attackable artifact asserting "this test was sound and
relevant." This is the deep move: you can always appeal a conviction by
attacking the *test* rather than re-arguing the verdict. When a warrant's ν
falls, the verdict falls, and the original target comes back.

**Standards are case law.** In informal domains (history, aesthetics),
verdicts come from a judge LLM ruling under a registered *standard*
artifact. Every such ruling's ν cites its standard. Refute the standard and
*every verdict ever issued under it collapses at once*, reinstating every
target — the spec calls this the "parallel fifths" move (the rule against
parallel fifths was repealed; every piece condemned under it deserves
re-hearing). We watched this work live.

**Measures never adjudicate.** Diversity scores, novelty metrics,
hard-to-vary estimates — none of them may touch a status. They steer
*attention* only: what gets worked next, what gets rendered into packs,
what gets budget. This single invariant is enforced everywhere and is the
reason the system can't Goodhart itself into deleting ideas a metric
dislikes.

**Hard-to-vary (HV)** operationalizes Deutsch's criterion for good
explanations: a variator LLM makes k structural edits to an idea; if the
edits mostly still pass the idea's own checks, the idea was easy to vary
(bad — like the Persephone myth, where any god and any crime slot in and
"winter" is still explained). Low HV on a proposed *connection* between
ideas produces an ordinary refutation with a full trace — and even that
verdict carries an attackable ν.

**Schools** fight mode collapse. N parallel "conditioning regimes" (a
mechanist, a skeptic, ...) each see packs biased toward their own accepted
lineage, so conjecture diverges like island populations — but criticism
crosses school lines freely, and school membership can never influence
adjudication (it lives in provenance, which is never a warrant).
**Capture detection** watches two failure surfaces — a generator collapsing
into one idea, and a court ossifying into ritual — via replay programs over
the event log, and a fixed response ladder (fan-out, reseeding a school,
audit sweeps) reacts with hysteresis.

**λ (lambda)** is the fraction of recent verdicts grounded in *program or
observation* rather than LLM judgment. It's the system's tether to reality:
a closed loop of LLMs judging LLMs can drift arbitrarily while looking
internally consistent. The spec pre-registers an experiment (§11.8) to test
whether the tether actually matters. We ran a pilot of it — see §6.

## 3. What was built, phase by phase

All phases P0–P6 of the spec are implemented: **84 tests, all passing**,
across 14 commits on `claude/folders-files-layout-7ajf1d`.

| Phase | What it is | The acceptance proof |
|---|---|---|
| **P0** | The deterministic core: untyped schema, content-addressed storage, append-only event log, two-pass adjudicator, both closure rules | Reinstatement, standard-refutation cascade, and byte-for-byte replay all pass as unit tests |
| **P1** | The loop: Conjecture → Criticize → Adjudicate, with the Verbalized-Sampling conjecturer contract and the anti-relapse gate | A refuted idea resubmitted verbatim is blocked at the gate with a logged reason |
| **P2** | Scheduler, all 7 problem-spawning triggers, HV + reach measures, schools, capture detection, response ladder, λ instruments | An easy-to-vary relation is refuted by `hv-floor` and reinstated by attacking its ν; forced school convergence triggers a logged Reseed |
| **P3** | Merge: two divergent sessions union into one graph (CRDT-style, no conflicts possible) and re-adjudicate | A counter-attack authored in session B against a critic it never saw reinstates the common ancestor on merge |
| **P4** | Research: observation-valued commitments spawn research problems; evidence enters as an attackable artifact resting on a source-reliability node | Attacking the reliability node orphans the evidence and re-arms research |
| **P5** | The informal-domain protocol: skeletons with forbidden cases, standards, the trial guard, pairwise rulings, judge audits, holdout/reveal, the appellate docket | Six acceptance criteria, each with a dedicated test — including the audit that attacks a judge's ν and thereby reinstates the judged |
| **P6** | Hardening: the eval report (valid-JSON rate, attack validity, trial-guard survival, escape efficacy), token budgeting, live-run tooling | Used in anger below |

Two pieces deserve special mention because they did real work in the live
runs:

- **The trial guard** (spec §3): before any judge verdict becomes a
  warrant, it must survive four program-checked screens — the cited
  decisive point must literally appear in the trial exchange (*referential
  integrity*), the ruling must survive swapping presentation order, it must
  survive paraphrase, and a two-model judge ensemble must agree. A verdict
  that fails any screen is logged and discarded. Crucially this is enforced
  at *registration*: even hand-constructed rubric warrants without a
  conforming transcript are rejected by the harness itself.
- **The token meter**: a hard provider-wide ceiling checked *before* each
  call spends anything; exhaustion stops a run gracefully with consistent,
  replayable state.

## 4. The live runs: a story in seven acts

We ran the harness against **DeepSeek v4-pro** (with v4-flash as the second
judge seat). Every failure below was diagnosed *from the system's own
blobs and logs* — the audit trail is not decorative.

**Act 1 — Tides (success).** A physics-flavored problem with two cheap
program criteria. 17 calls, 100% schema-valid JSON, and the surviving
theory was genuinely good: a resonance/forcing account of tides whose
dependency chain included a self-generated *correction* about how
amphidromic points suppress a whole tidal constituent (the model's critic
pushed its conjecturer to a more precise account). One candidate — "the
tides are magic" — was refuted by program, no judge needed.

**Act 2 — Republic, first attempt (failure: truncation).** A history
problem requiring answers as JSON "skeletons" with falsifiable forbidden
cases. Every single γ-call failed. Diagnosis from the blob store: the model
was producing *exactly correct* output, truncated mid-JSON — every
completion hit my 1,600-token cost cap precisely (28,800 tokens ÷ 18 calls
= 1,600.0). My optimization had strangled the task. **Fixes:** roomier caps
for skeleton-bearing roles; endpoints now expose `finish_reason` so a
truncated response triggers a "respond more compactly" repair hint instead
of a blind (identically-truncating) retry; the contract also now accepts
skeleton content emitted as a JSON object rather than an embedded string.

**Act 3 — Republic, second attempt (failure: network).** One TLS connection
reset killed the whole run mid-cycle. The harness state survived perfectly
(the event log is the source of truth), which proved the persistence design
but exposed missing transport robustness. **Fix:** retries with exponential
backoff for transient errors; a permanently failed call now drops one cycle
with a logged diagnostic instead of crashing the run.

**Act 4 — Republic, third attempt (failure: the thinking judge).** The
conjecturer now worked (valid skeletons, first attempt), but every *trial*
died: v4-pro writes analysis prose before its JSON ruling, and the judge's
cap truncated it every time — the compression hint couldn't stop a model
from thinking out loud. **Fix:** DeepSeek's native JSON mode
(`response_format: json_object`), which suppresses the preface at the API
level, plus a realistic judge cap.

**Act 5 — Republic, fourth attempt (success, and the good stuff).**
23,817 tokens, and the P5 machinery worked end-to-end on live model output:

- Three prose-shaped answers **refuted by program** (`skeleton-wf`): if you
  forbid nothing, a 30-line Python function kills you — no judge involved.
- A **live pairwise ruling**: the judge, under mandatory order-swap,
  eliminated a speculative malaria-epidemiology account in favor of the
  Marian-reforms account, with the ruling honestly citing the loser's
  speculativeness.
- The **trial guard blocked a conviction**: one "fail" ruling cited a
  decisive point that didn't appear in the trial exchange — referential
  integrity check failed, no warrant registered. The court declined to
  convict on grounds it couldn't quote.
- Two sophisticated survivors, each with genuinely falsifiable forbidden
  cases — one of which ("a general with a loyal army voluntarily
  surrendering power") flirts with Sulla's abdication, i.e. the model
  planted a hook a future critic could use against it.

**Act 6 — Republic extension, 10 more cycles (success + a design bug
found).** The graph grew to 96 artifacts / 34 problems / 30 warrants; the
two strong survivors held. But the eval report's per-role valid-JSON rates
(critic 33%, variator 50%) exposed still-starved caps, and the problem
ledger exposed a real design bug: **successor problems inherited their
parent's *criteria* but not its *description***, so retry-packs never
contained the "answer as skeleton JSON" instruction — the model wrote
prose, the program refuted it, and the refutation spawned another
description-less successor. A correctness-preserving but self-defeating
cascade (27 successor problems). **Fix:** successors now embed the parent's
description.

**Act 7 — the λ pilot (one failure, then data).** First attempt: a
replicate burned 64k tokens producing *zero* conjectures — every response
was **empty**. Diagnosis: v4-pro is a reasoning model; on a
letter-counting task it spent the entire completion budget on internal
reasoning and never emitted the answer. (The empty string, content-addressed,
deduped to a single zero-byte blob — the storage layer inadvertently
compressing failure.) **Fix:** real headroom for reasoning. A related fix
found while building the oracle: Python's `eval` puts free names in
*globals*, so list comprehensions inside safe predicates couldn't see our
sandboxed names until the namespace was passed as globals rather than
locals.

## 5. What the λ experiment is and why it's pre-registered

Spec §11.8 asks the sharpest question in the project: **does grounding
verdicts in programs (λ high) actually produce better outcomes than a
closed loop of LLMs judging LLMs (λ = 0), or is that an
architecture-diagram fiction?**

Design: two arms differing in exactly one bit. Both get the same problem —
*compose an English sentence whose first 8 word-lengths encode
3.1415926* (e.g. "How I wish I could enumerate pi easily" = 3-1-4-1-5-9-2-6).
A program can verify this perfectly. In **λ_full** the verifier is
registered as an in-loop criterion; in **λ0** it is *withheld* — the loop
runs on argumentative criticism alone — and the verifier scores everything
only after the fact ("oracle-blind, oracle-scored"). Thresholds and a
falsifier were committed to the repo **before any run**
(`experiments/lambda_preregistration.yaml`), which is what makes the result
science rather than storytelling: we can't move the goalposts after seeing
the data.

## 6. The λ pilot results — and the honest reading

Pilot scale: 3 replicates × 10 cycles per arm (the pre-registration calls
for ≥5 × 30; the deviation is recorded in the output). 465,347 tokens.

**Topline, as pre-registered:** λ_full passed the oracle at 0.10 in every
replicate; λ0 at 0.10/0.30/0.35. Oracle gap = **−0.15**, below the
pre-registered +0.10 threshold → **the falsifier triggered.** Recorded
verbatim in `runs/lambda/lambda_report.json`, as the protocol demands.

**Post-hoc diagnosis (labelled as such):** the topline is an artifact of
two confounds, and the underlying data says something much simpler:

| | on the actual seed problem | on derivative side-problems |
|---|---|---|
| λ0 (all 3 replicates) | **2/2 pass** | 0–5 of 18 |
| λ_full (all 3 replicates) | **2/2 pass** | 0 of 18 |

1. **Ceiling effect.** v4-pro solved the mnemonic *immediately, in every
   replicate, in both arms* (verified by hand: "How I wish I could
   enumerate pi easily"). A task the generator never fails cannot show a
   dose-response to criticism. The oracle needs to be harder.
2. **Denominator dilution.** After cycle 1 the seed problem had survivors,
   so the scheduler's "unsolved problems first" rule spent the remaining
   nine cycles on derivative problems (discrimination → successor cascades)
   whose criteria were empty — 18 of every 20 conjectures never faced the
   oracle at all, and the pre-registered metric averaged over them. λ0's
   apparent "advantage" is noise in that off-task majority.

So the correct reading is: *the falsifier fired against the pilot's
metric, the pilot's metric was measuring the wrong denominator, and the
pre-registration discipline is exactly what let us say both things
cleanly.* This is the Popperian machine eating its own cooking: a verdict
was rendered, the verdict's *validity* was then attacked with evidence,
and the attack stands. A definitive run needs (a) a harder oracle with no
ceiling, (b) the metric conditioned on oracle-facing candidates or a
scheduler focus lock, (c) the pre-registered 5×30 scale — all cheap to do,
no goalposts moved.

### 6b. The v2 run — the definitive (near-complete) result

All three fixes were pre-registered as an amendment
(`experiments/lambda_preregistration_v2.yaml`, committed before any v2
run): an arbitrary word-length oracle `[4,2,9,3,7,5,8,2,6,10]` with no
famous mnemonic to recall, a scheduler focus lock eliminating side-problem
dilution, and a count metric — distinct verified passers per run — immune
to denominator games. Scale: 5 replicates × 30 cycles per arm; the run was
stopped at user request after **4 complete replicates per arm** (the
deviation is recorded in the verdict).

**Pre-registered verdict: the falsifier triggered again.** λ_full averaged
5.0 verified sentences per run vs λ0's 4.5 — a gap of 0.5, under the
pre-registered 1.0. In-loop grounding did not increase the *volume* of
verified output. Recorded in `experiments/results/lambda_v2_report.json`.

**What the distributions show** (the phenomenon the count metric wasn't
built to catch):

| | λ0 (closed loop) | λ_full (grounded) |
|---|---|---|
| verified per run | 7, 0, 2, 9 — erratic | 6, 7, 3, 4 — consistent |
| share of registered record correct | 33% | **79%** |
| worst replicate | 36 candidates, zero correct | 3 correct |
| anti-relapse gate blocks | 0 | 6–36 per run |

The closed loop is a gambler — one replicate produced nothing true across
30 cycles while its unanchored critic found nothing wrong. The grounded
loop never excelled and never failed: high floor, mostly-true record,
gate visibly working. Caveats both ways: v4-pro can count letters
internally (partially its own oracle here, compressing the gap), and the
count metric charges λ_full for candidates its own gate correctly
suppressed. Current best statement: **grounding as built does not make the
generator more productive — it makes the archive trustworthy and bounds
the failure modes.** A v3, if run, should use a precision-weighted primary
metric; that intention is on record before any v3 data exists. The full
narrative is in `docs/STATE_OF_THE_THEORY.md`.

## 7. Token spend vs. the 4M budget

| Run | Tokens | Outcome |
|---|---|---|
| Tides (unmetered — accounting built after) | ~40–80k est. | success |
| Republic 1 (truncation) | 44,380 | failed, diagnosed |
| Republic 2 (network) | 12,552 | failed, diagnosed |
| Republic 3 (JSON mode success) | 23,817 | success |
| Republic extension | 70,108 | success |
| λ pilot 1 (reasoning-empty, killed) | ~65–95k | failed, diagnosed |
| λ pilot 2 (complete) | 465,347 | complete data |
| λ v2 definitive (8 full runs + 2 partial, stopped) | ~1,700k | verdict recorded |
| **Total** | **≈ 2.4–2.5M** | |

**Roughly 1.5M of the 4M remains.** Every run after the first is
hard-capped by the token meter, which stops before spending when a ceiling
is reached.

## 8. What remains

1. ~~**The definitive λ run**~~ — **done** (see §6b): pre-registered v2,
   4/5 replicates per arm, falsifier verdict recorded. Open follow-up: a
   v3 with a precision-weighted primary metric and a task the model cannot
   self-verify.
2. **Longer informal runs** — enough cycles for the judge-audit sweeps
   (paraphrase invariance, planted-flaw calibration, bias probes) to fire
   against live rulings, and for a critic to find the Sulla counterexample.
3. **True cross-family judging** — both judge seats are DeepSeek models; the
   spec wants different model *families* (the config caveat is documented).
4. **Scheduler focus tuning** — the side-problem dilution in the pilot is
   the same "unsolved-first" rule that is elsewhere a virtue; it likely
   wants a configurable seed-problem share, the same way integration work
   is capped.
5. **A pull request** — the branch is 14 coherent commits; say the word.

## 9. Where everything lives

- Spec: `docs/harness-spec-v1.3.md` · Layout and phase table: `README.md`
- Core: `src/deepreason/harness.py` (registration/replay),
  `adjudication/` (the two-pass court), `programs.py` (test programs)
- Informal protocol: `src/deepreason/informal/` (trial, standards, audits,
  holdout, appellate)
- Capture control: `src/deepreason/capture/` (schools, detection, ladder)
- Live tooling: `scripts/live_run.py`, `scripts/lambda_live.py`,
  `src/deepreason/report.py`, `src/deepreason/llm/budget.py`
- Run data (replayable): `runs/republic/`, `runs/lambda/` +
  `runs/lambda/lambda_report.json` · Pre-registration:
  `experiments/lambda_preregistration.yaml`
- Every run replays: `Harness(root)` rebuilds any state byte-for-byte from
  its event log; `deepreason --root <run> report` re-derives every metric.
