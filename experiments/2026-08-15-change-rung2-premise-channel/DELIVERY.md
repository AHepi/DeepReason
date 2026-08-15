# DELIVERY — Rung 2 step 2 (the premise channel, wired)

Branch `claude/calculus-rung2-step2-premise-pes36e`, based on
`claude/calculus-reconciliation-v2-qqghvn` (which carries Rungs 1, 1b-i and
Rung 2 step 1, all unmerged), with `main` merged in for the two calculus
authorities. Six commits:

| Commit | What |
|---|---|
| `e7bacbb0` | ledger Amendment 1 verbatim + the step-2 design; no code |
| `282e1acd` | the wiring (M12–M20) — gate 3635/0 |
| `a476c564` | the second demarcation check for prose (M21) — gate 3640/0 |
| `32154dc1` | validation and delivery record |
| `da8e79fa` | Riders 2 and 3 absorbed into the v2 program |
| *(this)* | the demarcation criterion RE-FOUNDED on Formalization §12.2 — gate 3640/0 |

## Requirement-by-requirement reconciliation

| # | Requirement (operator's words, condensed) | State | Where |
|---|---|---|---|
| M12 | Rent battery: a demarcation criterion pinned onto premise artifacts requiring a SUBSTANTIVE commitment; reuse `_substantive`; structural checks must NOT satisfy it; build the `crit` half of `active()` | **DELIVERED, then SUPERSEDED by R54** | The battery is pinned onto premise artifacts and structural checks still cannot satisfy it — but §12.2 relocates the substantive test from `crit` to `load`, so `crit` no longer uses `_substantive` and `active()` is now `demarcated()`. The REQUIREMENT is met; the MECHANISM the operator named is not the one in the tree, on the operator's own later instruction. `measures/demarcation.py`, `premises.py::premise_rent_sweep`; walked in `RECONCILIATION.md` S-1 |
| M13 | Wiring: critic pack invitation; scheduler consults `premise_work_invited`, deprioritises `premise_orphaned`, skips `retired_problems`. ATTENTION ONLY | **DONE** | `llm/packs.py::premise_invitation_note`; `rules/crit.py::_premise_invited_problem`, `_file_attribution`; `scheduler.py::_select_problem`, `step` |
| M14 | Three detection signals declared through the Rung 1b-i contract; no `unspecified` | **DONE** | `signals.py::_DECLARED`; `measures/attention.py`; `premises.py::independence_resolution_rate` |
| M15 | NO new LLM role | **HELD** | one optional field on existing contracts; `variator` is an existing seat |
| M16 | The producer fires in an offline run of the ACTUAL loop | **DONE** | `tests/test_premise_channel_loop.py::test_the_producer_fires_in_the_real_loop` |
| M17 | A premise falls by DEMARCATION with no hand-written refutation | **DONE** | `test_a_premise_falls_by_demarcation_with_no_written_refutation` |
| M18 | A marked problem is deprioritised, a retired one is not selected | **DONE** | `test_a_marked_problem_yields_to_unmarked_work`, `test_a_retired_problem_is_not_selected`, both selection modes |
| M19 | ONE guarded live run, judged on typed outcomes; a MISS is inconclusive but recorded | **BLOCKED — not attempted** | no credential in this container (below) |
| M20 | NOT OWED: any cross-version proof | **HONOURED** | none attempted; no old-root sweep run as a gate obligation |
| M21 | A second check for prose | **DONE, then RE-FOUNDED** | `measures/demarcation.py::load`/`demarcated` (§12.2), `measures/hv.py::VariationSampler`, `scheduler.py::_premise_rent_step`. The second reading survives the supersession; what changed is that `crit` became the weak test and `load` carries the substantive work |
| R54 | The three calculus documents supersede previous decisions | **APPLIED, retroactively, to shipped code** | `measures/demarcation.py` re-founded on §12.2/§12.1; the full walk of every previous decision is in the program's `RECONCILIATION.md` §2N |

## The one thing not delivered, and why

**UPDATED 2026-08-15 by RIDER 5 (R62): the live run is now DEFERRED BY POLICY,
not only blocked by a missing credential — and the policy is the better
reason.** The external implementation advice requires that no live pilot judge
premise extraction before P4's citable-evidence flow lands, and A19 is exactly
such a pilot. Without P4, a live miss would be uninterpretable: nobody could
tell a critic that DECLINED the invitation from one that never had the evidence
to take it up. So the operator should NOT be asked for a key to run this yet.
The credential paragraph below stands as the record of the original block and
of what closing A19 will need when P4 has landed.

**M19 / A19 — the guarded live run — was never attempted.** `experiments/*/env`
does not exist in this container and `OLLAMA_API_KEY` is unset, so no ladder
can reach a provider. This is not the "live MISS is inconclusive" case the
operator pre-authorised: a miss requires a run that happened and produced no
attribution. Nothing ran.

What is needed to close it: the `OLLAMA_API_KEY`, written to
`experiments/<ladder>/env` (gitignored, never committed). Then one ladder run
judged on typed outcomes only — run state, `stop_reason`, `verify_root`, and a
search of the record for `premise.work-invited.v1` /
`premise.attribution-filed.v1`. Budget the qualification battery (~14 minutes,
~1160 calls) if the home or provider profile is new.

Two facts worth carrying into that run, because they shape what a miss means:

1. The invitation only appears once a problem has accumulated two refuted
   candidates and no standing attribution — so a short run, or one whose
   candidates all survive, will never offer it. A miss under those conditions
   says nothing about the channel.
2. `load` — the second demarcation reading — needs the `variator` seat. A live
   configuration without it will file attributions and fell no premises,
   recording `premise.rent-undecided.v1` with reason `no-variator`, which is a
   correct outcome to observe rather than a failure.

## Known residue

Carried verbatim from VALIDATION.md: `load` is a sample and not a proof (ν says
so, and the sampled variants are logged); §12.2's empirical-scope clause is owed
and not met (S-5); D-8 — a premise contentful and wrong by argument alone — remains
unanswered and needs argumentative status authority no solo configuration has;
and the diff budget was EXCEEDED (production 458/320, tests 352/300) and is
recorded as a miss rather than re-baselined.
