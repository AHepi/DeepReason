# Native one-shot vs DeepReason: three frontier models, one question

Date: 2026-07-28. Models: glm-5.2, kimi-k2.6, deepseek-v4-pro (Ollama
Cloud). Question (identical for all six answers):

> When two independently generated conclusions inside a deterministic
> reasoning system appear to agree, by what criteria should the system
> decide they are the same claim rather than distinct claims that merely
> overlap, and what does it risk by merging too eagerly or too
> reluctantly?

Native baseline: one shot, thinking on, 16k completion budget, no system
prompt. DeepReason: per-model isolated harness — setup, full production
qualification (concurrency 3, the account's concurrent-request cap),
one engaged public run (6 cycles / 100k tokens), grounded bridge.

## Outcomes

| | native | DeepReason |
|---|---|---|
| glm-5.2 | 29s, 6.8k chars, confident taxonomy ("four dimensions") | full tier (654s battery); run 569s; **conflicting_evidence** — four accepted formal artifacts with mutually incompatible identity criteria, typed conflict sections, merge-risk analysis marked conjecture |
| kimi-k2.6 | 36s, 6.2k chars (16k thinking), confident "hierarchy of sameness" | full tier (2446s battery); run 687s; **underdetermined** — a 12-way rivalry preserved, with a typed reason: no decisive facts admitted to adjudicate |
| deepseek-v4-pro | 40s, 5.5k chars, confident normalized-syntactic-first procedure | **refused the full engine.** Two independent qualification batteries (each with a bounded re-exercise of failing pairs) both failed: repeated `REPAIR_SCOPE_VIOLATION` on `scratch.cluster-guide.compact.v1` (plus `scratch.link.minimal.v1` validation failures on the second draw). Durably tiered shallow; the reduced-engine answer ran with an explicit disclaimer and no grounded-answer authority |

## What the difference actually is

**Content overlap is high; epistemic status is the difference.** The
criteria families the native answers propose (syntactic normalization,
mutual entailment, derivation-trace identity, counterfactual/operational
robustness) also appear inside the DeepReason runs — as *rival
artifacts*. What the native answers do not and cannot do is say which of
those survived criticism, which conflict, and whether the question is
actually settled. Each native answer resolves the tension by editorial
choice, presented with uniform confidence. The two full-tier DeepReason
answers both concluded — through different models — that the question is
*not settled*, and said so with typed resolutions (`conflicting_evidence`,
`underdetermined`), a claim ledger, and an auditable record of what was
proposed, attacked, and left standing.

**The harness discriminates between models; fluency does not.** The three
native answers are indistinguishable in confidence and polish. The
harness produced three different institutional outcomes: two models
earned full authority and produced grounded non-answers (the honest
result); one model failed a behavioral gate twice — a durable,
replayable finding about the model's contract discipline today (it
passed the same battery during the 2026-07-27 campaign; the regression
is on the provider side) — and was confined to a labeled reduced mode.
A reader of the native answers learns nothing about whether the
answering model can be trusted with the question; a reader of the
DeepReason record learns exactly that first.

**Cost, honestly.** Native: ~30–40 seconds. DeepReason: ~10–41 minutes
of one-time qualification per model (concurrent battery; was ~2 hours
before this session), plus ~10–12 minutes of reasoning and ~9 minutes of
bridge per question. The product's answer to "is it the same claim?" is
slower, but it is the only one of the six answers that knows — and
records — how sure it is.

## Harness findings surfaced by this comparison (all fixed and committed)

1. Typed budget-exhausted stops made every budget-bounded run
   uncomposable (`BRIDGE_STAGE_A_FAILED`); the replay guard now admits
   terminal-commitment-bound composition after resumable stops.
2. Bridged roots were never re-verifiable (post-horizon scratch
   bookkeeping unauthorized since the first bridge ever ran); the
   horizon whitelist now authorizes harness-actor scratch inside a
   commitment-bound bridge episode.
3. Fresh decision-4b evidence: a root whose only bridge episode failed
   is permanently bridge-dead (`start` returns the stale failed
   terminal); recovery semantics remain an owner decision. The dead
   glm root is preserved.
4. The re-exercise machinery worked as designed on real flakes: failing
   pairs drew fresh blocks, first draws preserved as evidence; a model
   failing two consecutive independent batteries is tiered shallow on
   demonstrated behavior, not one draw.

Raw records: `*-native.json`, per-model homes (`glm2/`, `kimi/`,
`deepseek/` — `glm/` is the preserved bridge-dead root), committed run
roots with logs, qualification reports, and bridge outputs.

## Expanded analysis (added after the run)

### The natives agree with each other — and can't know it

With the full texts side by side, the three native answers are close to
one another in inventory and in verdict. All three enumerate the same
criteria families (syntactic/canonical-form identity, extensional vs
intensional equivalence, mutual entailment, provenance/derivation
identity, contextual substitutability), all three name proof-path
collapse and retraction fragility as the eager-merge risk and
combinatorial bloat as the reluctant-merge risk, and all three close
with essentially the same architecture, stated as settled: merge to a
canonical claim node, keep multiple provenance edges (GLM: "canonical,
unified representation ... with multiple provenance paths"; Kimi: "the
node stores the content; the incoming edges store the derivations";
DeepSeek: "syntactic merging ... provenance tracking to keep
justifications distinct"). Three independently generated conclusions
that appear to agree — the question's own scenario — and nothing in any
of the three can say whether they are the same claim, three overlapping
claims, or rivals. Each model resolved the question by editorial fiat
and none flagged that the resolution was fiat.

### What the harness did with the same material

The harness runs contained the same conceptual inventory — as rival
artifacts that had to survive criticism. The native answers'
consensus architecture appears inside the runs as one rival among
several, and it did not survive as a settled conclusion, because
nothing in the bounded record adjudicated it against the alternatives.
GLM's run ended with four accepted formal artifacts proposing mutually
incompatible criteria (causal-trace isomorphism, counterfactual
robustness, equivalence-proof admission, mutual entailment) and
composed a typed conflict; Kimi's run ended with a twelve-way rivalry —
including tail positions no native answer volunteered (thermodynamic
stability of agreement under perturbation, Kolmogorov-auditability
trade-offs, structural-equation automorphism symmetry) — and a typed
reason for refusing to adjudicate. Where the native answers converge on
the conservative center, the harness funded the atypical tail and then
declined to pretend the center had won.

### The differences, named

1. **Where confidence comes from.** Native confidence is a property of
   the prose. Harness confidence is a property of the record: a section
   is rendered `observation` only when grounded in ledger entries of
   that class, `conjecture` when it survived but was never grounded,
   `conflict`/`unknown` when that is what the record holds. Every
   composed sentence carries its epistemic class and its ledger refs.
2. **The unit of output.** A native answer is one artifact with one
   implicit author-voice. A grounded answer is a resolution + typed
   sections + a claim ledger + a validation report, each
   content-addressed — "why do you say S2?" has a mechanical answer.
3. **Model discrimination.** The three native answers are
   indistinguishable in reliability signals. The harness gave the same
   three models different institutional outcomes, and DeepSeek's
   repeated repair-scope violations — invisible in its polished native
   answer — are now a durable, replayable report.
4. **Reproducibility.** The one-shots are unrepeatable samples. The
   harness answers are digest-bound: frozen question, manifest, and
   run identity, replayable end to end.
5. **Failure is a first-class object.** A native answer cannot fail;
   it can only be wrong fluently. The harness failed visibly twice in
   this campaign (both bridge defects), and both failures were
   diagnosed entirely from durable records — the same auditability the
   answers themselves get.
6. **What natives are better at.** Speed (30–40s vs ~20–60 min
   end-to-end), coverage, and pedagogy. The native answers are good
   tutorials. The grounded answers are findings. Different products:
   one tells you what is thought about the question, the other tells
   you what this bounded record can and cannot support.

### Honest limits

The two full-tier grounded answers say "unresolved" about a 6-cycle,
100k-token record — a statement about that bounded record, not an
eternal truth; more cycles or admitted evidence could adjudicate the
rivalry. And an archival loss: the kimi and glm2 run roots (full
ledgers and section texts) were reclaimed with the container before
being committed — a bare `runs/` gitignore pattern silently excluded
every per-home `<slug>/runs/` directory (now scoped to `/runs/`).
Resolutions, resolution reasons, section extracts, logs, qualification
records, and both DeepSeek battery reports survive in this directory
and in the session record.
