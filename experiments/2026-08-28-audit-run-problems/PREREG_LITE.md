# PREREG-LITE — the one live probe this audit runs

**Frozen 2026-08-28, before any provider call and before the credential is
placed on disk.** Registered here so the reading cannot be chosen afterwards.

## Why only one probe

Q2, Q3, Q4 and Q5 were settled from the committed record and from offline
re-derivation; nothing they leave open would be moved by a provider call. Q1's
STRUCTURAL half is settled too — 93 of the 98 critic dispatches across the four
committed roots were never shown the byte-checked citation channel at all
(`probes/q1_prompt_surface.json`). What the record cannot settle is the
BEHAVIOURAL half, and it cannot because the sample is five:

| dispatch | invitation shown | `premise` returned | `premise_evidence` returned |
|---|---|---|---|
| epoch 5 seq 167 | yes | null | null |
| epoch 5 seq 204 | yes | null | null |
| epoch 5 seq 340 | yes | null | null |
| epoch 6 seq 141 | yes | (no case carried the fields) | — |
| epoch 6 seq 180 | yes | **substantive text** | **null** |

One dispatch in six epochs both engaged the invitation and declined the
citation. n = 1 cannot separate "the seat will not cite" from "this prompt does
not get it cited".

## Hypothesis

H0 — MODEL BEHAVIOUR. Shown the invitation and the citable-block legend, the
critic seat fills `premise` and leaves `premise_evidence` null, and continues to
do so when shown a worked example of filling it.

H1 — PROMPT SURFACE. The seat will fill `premise_evidence` when the prompt
carries one minimal exemplar of a filled entry, and does not otherwise.

## Design

Two arms against the same model, same endpoint, same wire schema.

- **Arm A (control).** The verbatim prompt bytes of epoch 6 seq 180, read from
  that root's own blob `98e3b56dcb33397f31a9573ddc099964086cdc0b5ed18f8859c240a1bb3027f6`.
  Not a reconstruction — the bytes the run actually sent.
- **Arm B (treatment).** Arm A's bytes plus one appended exemplar showing a
  single filled `premise_evidence` entry, using a block id drawn from the
  prompt's own CITABLE EVIDENCE BLOCKS list and a quote taken verbatim from
  that block's rendered preview. Nothing else changes.

Model `kimi-k3`, `reasoning: "low"`, `response_format: json_object`, exactly as
`run-manifest.json` `roles.argumentative_critic` binds it.

**N = 8 per arm, 16 calls total.** Cap: **100 000 tokens** across the whole
probe (epoch 6 seq 180 cost 4 967 tokens, so 16 calls budgets to ~80 000). If
the probe would exceed the cap it stops and reports the partial count as
partial.

## The measure

For each response, parse the JSON and count a HIT when any case object carries
`premise_evidence` that is a non-empty list. Nothing else is counted; prose
about the record is not a citation, which is the same rule M2 itself applies.

## What settles it, decided now

| result | verdict |
|---|---|
| A ≤ 1/8 and B ≥ 5/8 | **PROMPT SURFACE.** The channel works and the shipped prompt does not elicit it. |
| A ≤ 1/8 and B ≤ 2/8 | **MODEL BEHAVIOUR.** The seat declines the citation half even when shown how. |
| A ≥ 4/8 | The epoch-6 observation was not representative; M2's critic-side zero rests on the invitation gate alone. |
| anything else | **UNDETERMINED**, reported as such, with the counts. |

## What this probe CANNOT do, registered in advance

It cannot move the structural finding. Whatever the seat does when shown the
channel, it was not shown the channel on 93 of 98 dispatches, and on the two
epoch-6 dispatches where it was, the gate latched shut the moment an
attribution was filed (`premises.py:638`). A prompt-surface verdict would make
the channel worth opening; it would not mean the channel was open.

It is also one prompt, one target, one model. A negative arm B is evidence
about this prompt, not about every prompt that could be written.

## Raw preservation

Every request and response is written verbatim under `probes/live/`, with the
token count per call. The credential is never committed and never written
inside the repository.
