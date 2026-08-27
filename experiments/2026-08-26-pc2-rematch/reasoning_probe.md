# PROBE — the two arms do not run the same model configuration

Two calls to the SAME endpoint with the SAME frozen question bytes,
differing in exactly one field: the one `arm_s.py` omits and the harness
sets. Run 2026-08-26, against the live provider.

| | ARM S2's shape (no reasoning field) | ARM H2's shape (`reasoning_effort: "none"`) |
|---|---|---|
| completion tokens | **9 712** | **177** |
| visible content | 326 chars | 326 chars |
| reasoning payload | **24 409 chars** | **0 chars** |
| message keys | `content`, **`reasoning`**, `role` | `content`, `role` |

**55x the completion tokens for the identical visible answer.** The harness
runs glm-5.2 with THINKING DISABLED; the sampler runs it with THINKING ON.

This is not news to the codebase, which measured it and wrote it down in
`llm/providers.py::reasoning_disabled`:

> Unset is NOT off. A profile carrying `None` sends no reasoning field, and a
> reasoning model then thinks by default — measured on glm-5.2 via Ollama
> Cloud, where an unset knob returned a populated reasoning payload and
> "none" returned an empty one.

`_ollama_reasoning` passes the value straight through as `reasoning_effort`,
and its own comment names this as "what makes `reasoning: none` actually
disable thinking on Ollama (the dominant cost lever)".

## Corroborated by both arms' own token splits

| | calls | prompt/call | completion/call | completion share |
|---|---|---|---|---|
| ARM H2 | 135 | 6 410 | **2 427** | 27.5 % |
| ARM S2 | 9 completed | 167 | **11 276** | 98.5 % |

ARM S2's visible answer is ~100 tokens. The other ~11 000 are hidden
reasoning. ARM H2 spends 72.5 % of its budget on PROMPTS, because it carries
packs.

## Why this matters to the matched-budget rule

PREREG §5 matches TOTAL tokens. Under that rule the sampler converts almost
every token into thinking, while the harness converts most of its tokens
into prompt text and is forbidden to think at all. So "matched budget" gives
the baseline roughly 4.6x more thinking per token spent, on top of being
allowed to think in the first place.

## Scope: this confound is INHERITED, and it is P-C1's too

`reasoning: "none"` comes from P-C1's `run-config.yaml`, unchanged — P-C2
was required to differ from it in exactly one field and does. `arm_s.py` has
never sent a reasoning parameter. So **P-C1's committed 33x result carries
the same confound**, and so does anything derived from it.

## What it does NOT do

It does not soften the registered verdict. PREREG §6 says value is claimed
iff `best_H2 > best_S2`, and that is reported as registered. What the
confound changes is what the number MEANS: the tranche compares a harness
with the model's reasoning switched OFF against a sampler with it switched
ON. It does not isolate the harness, and no P-C result should be read as if
it did until this is settled.

---

## PROBE 2 — the model's hard output ceiling, 2026-08-26

Asked whether the endpoint would accept a larger completion cap, before
changing anything. It refuses, and names the limit:

    max_tokens=200000  REFUSED  HTTP 400:
      "max_tokens (200000) exceeds model's maximum output tokens (131072)
       for model glm-5.2"

**glm-5.2's maximum output is 131 072 tokens** — the same number as the
context window this tranche's config already declared, which is therefore a
real limit rather than a guess inherited from P-C1.

What that bounds:

- ARM H3's `max_tokens: 100000` (Amendment 1) sits at **76 % of everything
  the model can ever emit**. The remaining headroom is ~31 000 tokens, not
  the 100 000 a naive doubling would assume.
- The retired 32 768 attempt was at **25 %** of the ceiling, which is why
  reasoning alone filled it.
- No further cap increase can buy much. If ARM H3 fails again at 100 000 for
  a length-related reason, the answer is NOT a bigger cap — the road is
  nearly out — and the diagnosis has to go elsewhere.

Recorded because the two retired attempts were both sizing failures, and
this is the measurement that says how much sizing room was ever available.
