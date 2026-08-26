# W6 — the token-flow tables

Every number here is emitted by a committed instrument in this directory
and can be re-derived by running it. Nothing is hand-entered; the tables
are a rendering of the JSON, not a second source. Regenerate in order:

    python3 flow.py            # ~5 min: FLOW_CALLS.jsonl, FLOW_AGGREGATE.json,
                               #         METER_RECONCILIATION.json
    python3 pack_anatomy.py    # ~2 s:  PACK_ANATOMY.json, PACK_GROWTH.json,
                               #         PACK_SAMPLES.json
    python3 cross_arm.py       # ~10 s: CROSS_ARM.json
    python3 pc1_postmortem.py  # ~5 s:  PC1_POSTMORTEM.json

Scope: 54 committed run roots, 3 155 provider calls, **10 958 450 tokens**
— 7 467 145 prompt-side and 3 491 305 completion-side.

---

## T1 — Prompt-side vs completion-side, program-wide

| | tokens | share |
|---|---:|---:|
| prompt | 7 467 145 | **68.1 %** |
| completion | 3 491 305 | 31.9 % |

**Two tokens in three that DeepReason has ever bought were spent asking,
not answering.** This is the harness's overhead signature and every table
below is a decomposition of it.

## T2 — By purpose

Purpose is the call's `contract_id`, named, not judged.

| purpose | calls | tokens | share | prompt-side | mean/call |
|---|---:|---:|---:|---:|---:|
| generation | 1 219 | 7 093 809 | 64.7 % | 69.9 % | 5 819 |
| criticism | 1 418 | 2 863 877 | 26.1 % | 65.2 % | 2 020 |
| report | 48 | 504 116 | 4.6 % | 44.4 % | 10 502 |
| adjudication | 464 | 476 747 | 4.4 % | **84.8 %** | 1 028 |
| configuration | 6 | 19 901 | 0.2 % | 74.5 % | 3 317 |

Adjudication is the extreme: a judge ruling averages 1 113 tokens of which
**94.1 % is prompt**. A judge seat reads a great deal and says almost
nothing — 358 172 prompt tokens against 22 428 completion tokens over 342
rulings.

## T3 — By purpose detail

| contract | calls | tokens | prompt | completion | mean/call |
|---|---:|---:|---:|---:|---:|
| `conjecturer.turn.v6` | 816 | 5 679 006 | 4 017 868 | 1 661 138 | 6 960 |
| `batch-critic.v2` | 1 384 | 2 804 637 | 1 822 069 | 982 568 | 2 027 |
| `conjecturer.atomic-candidate.v1` | 373 | 1 328 116 | 911 733 | 416 383 | 3 561 |
| `judgeruling.direct.v1` | 342 | 380 600 | 358 172 | 22 428 | 1 113 |
| `bridge.ledger.v3` | 18 | 259 592 | 141 142 | 118 450 | 14 422 |
| `bridge.ledger-batch.v1` | 13 | 140 227 | 35 643 | 104 584 | 10 787 |
| `defender.direct.v1` | 122 | 96 147 | 46 071 | 50 076 | 788 |
| `bridge.composition.v2` | 12 | 92 483 | 38 927 | 53 556 | 7 707 |
| `variator.direct.v1` | 30 | 86 687 | 26 404 | 60 283 | 2 890 |
| `critic.atomic-target.v1` | 34 | 59 240 | 46 203 | 13 037 | 1 742 |
| `config-referee.v1` | 6 | 19 901 | 14 823 | 5 078 | 3 317 |
| `bridge.composition-batch.v1` | 5 | 11 814 | 8 090 | 3 724 | 2 363 |

## T4 — By call kind (the repair bill)

Call kind is the `work_prepared` lifecycle transition's `trigger_ref` — the
record's own marker, not `repair_scope` (see the caveat under T10).

| call kind | calls | tokens | share | prompt-side |
|---|---:|---:|---:|---:|
| first ask | 2 314 | 8 231 682 | 75.1 % | 65.9 % |
| **repair re-ask** | **456** | **1 382 831** | **12.6 %** | **80.7 %** |
| decomposition leg | 385 | 1 343 937 | 12.3 % | 69.2 % |

**One token in eight is a repair re-ask, and four in five of those are
prompt.** A repair sends the model its own rejected JSON back verbatim:
1 115 875 provider prompt tokens over 456 re-asks, of which 839 301
(estimated) are the returned rejected value and 194 383 the diagnostic
envelope. Two forms: 390 patch re-asks ("CURRENT JSON" + "DIAGNOSTIC
ENVELOPE", return one JSON-pointer operation) and 66 full-value re-asks
("INVALID JSON", return the whole corrected object).

## T5 — By outcome

Outcome is `workflow-work-terminal-v1.status`.

| outcome | calls | tokens | share |
|---|---:|---:|---:|
| admitted | 2 580 | 7 971 950 | 72.7 % |
| rejected into repair | 473 | 2 694 889 | **24.6 %** |
| invalid, discarded (`schema_exhausted`) | 101 | 289 335 | 2.6 % |
| no terminal record | 1 | 2 276 | 0.0 % |

**A quarter of every token ever spent went to a call whose output the
harness rejected.** Note this is not the same number as T4's repair bill:
T5 counts the tokens of the call that GOT rejected, T4 counts the tokens of
the re-ask that followed.

## T6 — What the tokens bought

The artifacts a call bought are the ones the log applies before the next
provider call. Self-checked: on the 465 conjecturer calls that carry an
explicit `conjecture-call:<seq>` backref, the window rule and the backref
name the same call 465 times and disagree 0 times.

| what it bought | calls | tokens | share |
|---|---:|---:|---:|
| an artifact that ended accepted | 1 415 | 5 582 650 | 50.9 % |
| **nothing — output rejected or discarded** | **574** | **2 984 885** | **27.2 %** |
| nothing in window — admitted, artifact-producing contract | 645 | 1 522 976 | 13.9 % |
| nothing — the contract produces no artifact | 521 | 867 939 | 7.9 % |

Read the last two rows carefully, because they are not waste:

- *nothing in window, artifact-producing* is almost entirely decomposition
  legs (291 calls, 1 044 545 tokens) and batch-critic passes (342 calls,
  462 502 tokens) whose work banks in a sibling leg or a later application.
- *the contract produces no artifact* is judge rulings (333 calls), defences
  (122), variations (30) and report passes — a ruling moves a status, it
  does not mint an artifact.
- "ended accepted" means the harness never refuted it. It does **not** mean
  the artifact was any good, and on P-C1 the two come apart completely: that
  root ends with 909 accepted artifacts, and **every one of its 132
  constructions is REFUTED** in the same replayed state. The accepted 909
  are criticisms, verdicts and ritual artifacts. See T11.

## T7 — Pack anatomy: where a prompt token goes

Split by contract AND prompt form, because a contract's packed calls and its
repair re-asks are different prompts and averaging them describes neither.
Sizes are the allocator's own `approximate_tokens`; the estimator runs about
0.90 of the provider's reported prompt count on `conjecturer.turn.v6`.

| contract, form | calls | mean est. prompt | preamble | **schema** | interstitial | pack sections |
|---|---:|---:|---:|---:|---:|---:|
| `conjecturer.turn.v6`, packed | 491 | 5 410 | 1.8 % | **70.2 %** | 0.3 % | 27.2 % |
| `batch-critic.v2`, flat | 1 286 | 1 321 | 8.4 % | 17.3 % | 74.3 % | — |
| `conjecturer.turn.v6`, repair | 325 | 2 975 | 2.5 % | — | 97.2 % | — |
| `conjecturer.atomic-candidate.v1`, packed | 351 | 2 166 | 2.2 % | 45.4 % | 3.1 % | 48.6 % |
| `judgeruling.direct.v1`, flat | 342 | 1 260 | 6.8 % | 9.0 % | 84.2 % | — |
| `bridge.ledger.v3`, flat | 12 | 10 521 | 1.9 % | 13.6 % | 84.5 % | — |
| `critic.atomic-target.v1`, packed | 34 | 1 247 | 3.4 % | 19.8 % | 2.8 % | 71.5 % |
| `defender.direct.v1`, flat | 122 | 459 | 15.0 % | 10.0 % | 75.1 % | — |

**On the harness's main generation contract, seven prompt tokens in ten are
the JSON Schema describing the form — not the problem, not the evidence, not
the prior candidates.** The fixed toll (preamble + schema) is 72.0 % of a
packed conjecture prompt.

`batch-critic.v2` is not on the pack IR (`render_batch_crit_pack` clips
aggregately), so it has no `## ` sections; its body is reported whole under
"interstitial" rather than being silently absent.

## T8 — Inside the pack body, by section kind

Over the 876 IR-packed prompts, 2 279 of the 3 155 calls having none.

| kind | appearances | est. tokens | share of packed body |
|---|---:|---:|---:|
| protocol | 885 | 332 106 | 29.6 % |
| frame (problem + criteria) | 1 752 | 223 892 | 19.9 % |
| evidence | 263 | 204 264 | 18.2 % |
| steering | 911 | 182 531 | 16.3 % |
| prior candidates | 635 | 180 038 | 16.0 % |

Largest single sections: `mandatory-interface` 229 041 (170 appearances,
mean 1 347), `scratch-advisory-context` 171 750 (271, mean 634),
`neighbourhood` 164 882 (558, mean 296), `citable-evidence-blocks` 152 653
(167, mean 914).

## T9 — Pack growth across cycles: there isn't any

Mean provider prompt tokens per packed `conjecturer.turn.v6` call, by cycle.

**P-C1 ARM H** (15 cycles):

| cycle | 1 | 2 | 3 | 5 | 6 | 7 | 9 | 10 | 11 | 13 | 14 | 15 | 16 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mean prompt | 6 155 | 6 204 | 4 810 | 6 277 | 6 257 | 4 865 | 6 286 | 6 286 | 4 898 | 6 286 | 6 286 | 4 898 | 6 282 |

**P-R1** (12 cycles):

| cycle | 1 | 3 | 4 | 5 | 7 | 8 | 9 | 11 | 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mean prompt | 8 381 | 7 736 | 8 384 | 6 923 | 8 350 | 6 870 | 8 352 | 8 351 | 6 918 |

The curve is FLAT. It oscillates between two values and never trends. The
model at cycle 15 is shown a pack the same size as the one it saw at cycle
1 — the pack budget caps it, so a long run does not accumulate context, it
re-pays for a bounded one. Earlier drafts of this table mixed repair
re-asks into the same cycle mean and produced dips that read as shrinkage;
splitting by prompt form removed them, and nothing shrank.

## T10 — The three token instruments do not agree

Each root states its provider spend three times: `run-status.json`
`token_spend`, `TOKEN_ACCOUNTING.json` `inquiry_provider_tokens`, and the
sum over `log.jsonl`. **27 of 54 roots disagree**, in two clean classes.

**Class A — 18 roots: `run-status.json` says zero.** Every root whose state
is `failed` or `running` carries `token_spend: 0` while the accounting and
the log agree exactly. P-C1 ARM H — a 702 789-token run — reads
`token_spend: 0`, and `deepreason results` prints that zero.

**Class B — 9 roots: the accounting undercounts the log**, by 428 624
tokens in total. In 8 of the 9 the residual is EXACTLY the report-purpose
(bridge) spend: the post-terminal ledger and composition passes run after
the budget is exhausted and land in no token counter, because
`token-accounting.v1` has `bridge_provider_calls` but **no bridge token
field at all**. Worst case `live_tri_2026-07-27/run-faa5feae…`: 138 396 of
330 396 tokens — 41.9 % of the run — spent composing the report and
accounted as zero. The ninth root
(`live_research_2026-07-29/narrow/run-7d87…`) has a residual of 37 132 that
is NOT the whole report pass: there, 9 of 12 bridge calls WERE folded into
`inquiry_provider_tokens` and 3 were not, so the counter is inconsistent
with itself as well as incomplete.

A third instrument caveat, found while building this window:
`attempt_trace.repair_scope` is populated on only **128** of the 456 repair
re-asks. It names the JSON pointer a repair was aimed at when one was
named; reading it as the repair marker undercounts the repair bill by 3.6x.

## T11 — Cross-arm: what one candidate cost each arm

P-C1, matched budget (`T_S/T_H = 1.009`, admissible per that tranche's
PREREG §4).

| | ARM H (harness) | ARM S (blind sampling) |
|---|---:|---:|
| tokens | 702 789 | 709 454 |
| prompt-side share | 79.8 % | 1.2 % |
| calls / samples | 292 | 54 |
| candidates attempted | 132 | 54 |
| checker-valid | 15 | 23 |
| above the registered 0.005 floor | **0** | 13 |
| survivors | **0** | — |
| harness's own status on the 132 constructions | **132 refuted, 0 accepted** | — |
| best score | 0.000 407 5 | 0.013 594 936 |
| **tokens per attempted candidate** | **5 324.2** | **13 138.0** |
| **tokens per valid candidate** | **46 852.6** | **30 845.8** |
| **tokens per above-floor candidate** | **undefined (0)** | 54 573.4 |

**The one number: 1.519.** At a matched budget the apparatus paid 1.52x
what blind sampling paid for one checker-confirmed construction.

**The number it hides:** cost per *valid* candidate flatters ARM H, because
"valid" means the checker confirmed the claim, not that the construction
was worth having. On the run's own registered floor ARM H's cost per useful
construction is not a large number — it is an undefined one.

**The prompt-side signature, in one comparison:** ARM S poses the same
instance in **163.9** prompt tokens. ARM H's mean generation prompt is
**3 959.5**. The harness pays **24.2x the prompt** to ask the same question.

## T12 — P-C1 ARM H line item: what the 702 789 bought

Cut by the problem each call was posed against, read from the rendered
prompt's own `PROBLEM` line and cross-checked against the run's three
problem objects.

| line item | calls | tokens | share |
|---|---:|---:|---:|
| the operator's seed question (`question-64b724c4…`) | 61 | 373 903 | **53.2 %** |
| `audit:ritual` — a problem the run spawned about its own critic | 203 | 289 676 | **41.2 %** |
| repair re-asks (carry no pack, so no problem line) | 28 | 39 210 | 5.6 % |

The 53.2 % spent on the operator's question bought 132 constructions, of
which the harness's own replayed state refutes **all 132**. Not one
construction in the run ends accepted.

`audit:ritual` ("audit the critic: adjudication-ritual flags sustained
§11.3") was spawned at log seq **345 of 3 200**, with provenance
`{"trigger": "audit-critic"}`; it then spawned `disc:audit:ritual`
("discriminate between 20 surviving rivals") at seq 603.

| | tokens | share on the seed question |
|---|---:|---:|
| before the spawn | 66 842 | **100.0 %** |
| after the spawn | 635 947 | **48.3 %** |

ARM S spent 100 % of its budget on the instance, by construction — it has
no mechanism for spawning a sub-problem.

ARM H's own purpose split: generation 104 calls / 517 838 tokens (73.7 %),
criticism 188 / 184 951 (26.3 %). Its outcome split: admitted 83.3 %,
rejected into repair 13.4 %, invalid-discarded 3.2 %.

## T13 — The two-call (split-budget) check

**Zero.** Across all 54 roots and 3 155 attempts, the number of attempts
carrying a non-empty `split_leg` is **0**.

The split fields (`split_leg`, `split_notice`, `split_max_tokens`) are
present on 717 attempts in the 5 newest roots — the roots written by code
that has the feature — and every one of them is empty. The only
split-related content in the whole record is a typed notice,
`split-budget:repair-authorization-is-single-leg`, on **96** repair
attempts: the split budget declining to split a repair authorisation.

So the shipped two-call fix has **no field measurement yet**: no committed
run has taken a split leg, and there is nothing to report about what an
extraction pass cost or recovered. That is the finding, and it is stated as
one rather than reported as a zero-cost success.
