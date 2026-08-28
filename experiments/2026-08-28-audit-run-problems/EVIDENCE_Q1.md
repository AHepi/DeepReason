# Q1 evidence ledger — the critic-side citation channel

Read-only census over the four committed roots of the P-T1 technique run
(branch `claude/spec-to-code-technique-k5209o`, never modified).

## Roots

| root | state | stop_reason | cycles | token_spend |
|---|---|---|---|---|
| `failed-epoch0-run-19c2ff74…` | failed | operational_failure | 2 | **0** |
| `completed-epoch1-run-92e63dcb…` | completed | budget_exhausted | 12 | 413631 |
| `failed-epoch5-run-456885c5…` | failed | operational_failure | 2 | **0** |
| `run/` (= epoch 6, 456885c5…) | completed | budget_exhausted | 24 | 772482 |

Epochs 3 and 4 roots are not committed on that branch.

## Census 1 — citation Measure events in `log.jsonl`

| root | `evidence-citation:*` (conjecturer) | `premise-citation:*` (critic) |
|---|---|---|
| epoch 0 | 9 (all `EVIDENCE_CITATION_VERIFIED`) | **0** |
| epoch 1 | 8 (all `EVIDENCE_CITATION_VERIFIED`) | **0** |
| epoch 5 | 2 (all `EVIDENCE_CITATION_VERIFIED`) | **0** |
| epoch 6 | 1 VERIFIED + 1 `EVIDENCE_REF_UNKNOWN_BLOCK` | **0** |

The critic-side emitter is `rules/crit.py:1385-1392` (`premise-citation:{code}`).
Zero events in every root: **not an attempt that was rejected — never attempted.**

## Census 2 — LLM calls by role

| root | conjecturer | argumentative_critic |
|---|---|---|
| epoch 0 | 23 | 29 |
| epoch 1 | 45 | 15 |
| epoch 5 | 32 | 10 |
| epoch 6 | 41 | 44 |

## Census 3 — was the channel ever SHOWN to the critic?

Prompt blobs containing the invitation text `PREMISE INVITATION`:

| root | invitation blobs | critic calls | exposure |
|---|---|---|---|
| epoch 0 | **0** | 29 | 0 % |
| epoch 1 | **0** | 15 | 0 % |
| epoch 5 | 2 | 10 | 20 % |
| epoch 6 | 2 | 44 | **4.5 %** |

Epoch 6's two invitation blobs
(`blobs/98/98e3b56d…`, `blobs/20/20c3f7b6…`) DO carry the citable clause
(`premise_evidence` + `CITABLE EVIDENCE BLOCKS`), and both name the SEED
problem `question-9e8800977c3e1deaf5b034b93db38959`.

## Census 4 — was a premise ever filed?

No `premise` and no `attribution` object type exists under `objects/` in ANY
of the four roots. The critic declined both invitations it received.
