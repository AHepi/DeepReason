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
