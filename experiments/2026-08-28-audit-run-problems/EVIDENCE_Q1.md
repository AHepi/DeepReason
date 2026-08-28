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

CORRECTED 2026-08-28 (the first reading of this census was wrong: attributions
are stored as ordinary artifacts, not under an `objects/<schema>/` directory,
so a directory listing missed them). Measured with
`premises.standing_attributions`:

| root | standing attributions |
|---|---|
| epoch 0 | 0 |
| epoch 1 | 0 |
| epoch 5 | 0 |
| **epoch 6** | **1** |

Epoch 6's pair — `09cff5b9abfa…` (attribution) and `b38afbf002e6…` (premise),
both `ProvenanceRole.CRITIC`, both `ACCEPTED`, on the seed problem — means the
critic ACCEPTED the invitation and filed a premise. It filed no
`premise_evidence` with it, so `_check_premise_citations` returned at its
`if not refs` guard (`crit.py:1369-1370`) and recorded nothing.

## Census 5 — the anti-E28 receipt disagrees with the record

`scheduler.py:2065-2072` emits `premise.work-invited.v1` so that "a mechanism
nobody triggers" is visible. It recorded **0 in all four roots**, including
epoch 6 where the invitation demonstrably reached two critic prompts
(blobs referenced at seq 141 and 180) and produced a standing attribution.

The receipt samples `premise_work_invited(selected_problem)` at cycle START;
the pack computes the invitation per criticism TARGET mid-cycle
(`crit.py:1477`, `:1641`). In epoch 6 both events fell inside cycle 0 — the
refuted count crossed `PREMISE_INVITE_AFTER = 2` after selection, and the
attribution filed during the same cycle then made the predicate False
(`premises.py:638-639`) before the next selection boundary. So the receipt's
window was never open when it was read.

A reader asking the record "did the premise channel ever fire?" gets **no**,
and the answer is **yes**.
