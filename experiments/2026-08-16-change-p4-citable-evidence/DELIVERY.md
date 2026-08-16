# DELIVERY — P4, three-layer citable evidence

Branch `claude/calculus-rung2-step2-premise-pes36e`. The tranche the operator's
board put after Rung 3c and before any live judgment.

## Requirement-by-requirement

| # | Requirement | State | Where |
|---|---|---|---|
| M1 | Full citable block ids and bytes reach **every** problem's conjecturer context | **DONE** | `rules/conj.py` — the legend's universe is `_union_blocks(bound_dossiers) + consumed_research_blocks(harness)`, unconditional. The `bound_dossier is not None` gate (epoch problems only) is gone. Mutation-checked by `test_a_derived_problem_sees_the_citable_block_ids` |
| M2 | Those bytes appear in the **recorded context-exposure receipt** | **DONE** | `ContextNamespace.EVIDENCE` + `plan_kind="citable"` in `workflow/transaction.py`; the plan is built in `rules/conj.py` from `CitableLegend.shown`, filtered again against the rendered pack. No new event type — it rides the existing `WORK_ISSUED` append |
| M3 | A quoted-evidence **subtype**; `EvidenceRefClaimV1` unmutated | **DONE** | `llm/contracts.py::QuotedEvidenceRefV1` (`quote` required), `premise_evidence` on `ArgumentativeCriticOutput` and `BatchCase`, mirrored in `llm/wire.py`. `EvidenceRefClaimV1.quote` still admits `None`, pinned by a test |
| M4 | Admission **byte-checks against those same recorded bytes** | **DONE** | `evidence/citations.py` — `EVIDENCE_REF_NOT_EXPOSED` and the `exposed_block_ids` binding; `rules/conj.py` reads the set from the exposure RECEIPT, `rules/crit.py` matches the receipt to the call by prompt digest |
| M5 | The claim **interface DEPENDS on the admitted evidence record** | **DONE** | `premises.py::file_premise(citation_ref=...)` adds the DEPENDENCE; `calculus/claims.py::PremiseAttributionV1.citation_ref` + `calculus/compiler.py` do the same in the substrate. The premise stays a MENTION |
| M6 | The critic channel can SEE the citable universe | **DONE** | `llm/packs.py` — both critic renderers take `citable_evidence_context`, rendered only under a standing premise invitation; `rules/crit.py` exposes the blocks in a `citable` plan and `workflow/nonconjecture_recovery.py` accepts them on resume |
| M7 | No live pilot before this lands; A19 unblocks on M1–M6 **and** a credential | **HONOURED** | No pilot attempted. R62's policy block is now discharged; the credential block is not |

## What the change actually does, in one paragraph

Before, a citation was a claim about a block id, checked against every block in
the run's dossier — so a model that guessed a real id verified exactly like one
that read the passage, and derived problems could not see any ids at all. Now
the run records which blocks each call was shown, in that call's own exposure
receipt; the checker resolves a citation against THAT set; and a premise
attribution that cites verified evidence carries a dependence edge onto the
citation record, so attacking the evidence reaches the attribution.

## Deliberate limits, each with its reason

- **The critic's citable universe is bound-dossier blocks only.** Including
  consumed research fetches would make `crit.py` the second rules module to
  import the capabilities package, and `DR-SEAM-capabilities-x-rules` holds
  that `conj` is the only one. The conjecturer keeps research blocks; the
  premise channel does not. Recorded here rather than discovered later.
- **`premise_evidence` is optional and absent by default**, matching `premise`
  and `counterexample` beside it. The wider reading of the advice — every
  calculus claim must cite — would refuse the configurations the standing laws
  protect (a solo run with no dossier). What the type forbids is an UNQUOTED
  entry, which is the half R62 actually names.
- **A19 is still not run.** M7 is discharged; the credential is not.

## Residue

Carried from VALIDATION.md: A13's combined loop (a derived problem's legend AND
a quoted premise citation in ONE offline run) is **not** proven — the two halves
are, separately, each through a real loop. The criticism-side exposure binding
is likewise proven in its parts rather than end to end. And the diff budget was
EXCEEDED on production (504/420) and badly on tests (774/340), disclosed rather
than re-baselined.
