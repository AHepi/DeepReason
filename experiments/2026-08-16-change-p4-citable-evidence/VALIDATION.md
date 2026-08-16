# VALIDATION — P4

Verdict: **PASS on M1–M6. M7 is a policy requirement discharged by not running
a pilot, and A19 stays deferred.**

Instruments:

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **3682 passed, 7 skipped, 0 failed** (977 s), run idle |
| `python tools/docs_verify.py` (full) | 60 documents, 916 checks, **3 failed — all `CON-run-identity`**, the recorded shallow-clone baseline |
| `python tools/docs_verify.py --links` | 0 dangling references, 60 documents |
| `python scripts/wheel_smoke.py` | passed — entry points, MCP tool set and schema shas unchanged |
| `python tools/diff_budget.py HEAD --paths src/ tests/ docs/map/` | src 541 / 420, tests 774 / 340, map 184 / 260 — **EXCEEDED on two areas, disclosed below** |

## Acceptance checks

| # | Check | Verdict | Evidence |
|---|---|---|---|
| A1 | The evidence namespace owns `EVD_`, and no other namespace may borrow it; `citable` is a declarable plan kind | PASS | `test_the_evidence_namespace_owns_its_own_alias_prefix`, `test_a_citable_plan_is_a_declarable_plan_kind` |
| A2 | The legend reports exactly the blocks whose bytes it rendered; an unrenderable block is in neither text nor receipt | PASS | `test_the_legend_reports_exactly_the_blocks_whose_bytes_it_rendered`, `test_an_unrenderable_block_is_in_neither_the_text_nor_the_receipt` |
| A3 | A DERIVED problem's conjecturer prompt carries the citable block ids | PASS, **mutation-checked** | `test_a_derived_problem_sees_the_citable_block_ids`; restoring the `bound_dossier is not None` gate fails it |
| A4 | The call's exposure receipt names one evidence item per shown block, with the block's own `text_sha256`, and nothing the prompt did not carry | PASS, **mutation-checked** | `test_the_exposure_receipt_records_the_blocks_the_prompt_carried` |
| A5 | A citation to a real, admitted block that was not exposed to THIS call records `EVIDENCE_REF_NOT_EXPOSED`; an empty exposure set is not the same as no binding | PASS | `test_a_block_that_was_not_exposed_to_this_call_does_not_verify`, `test_an_empty_exposure_set_is_not_the_same_as_no_binding` |
| A6 | With the keyword omitted, every existing outcome is unchanged | PASS | `test_omitting_the_exposure_binding_changes_no_outcome` |
| A7 | `QuotedEvidenceRefV1` cannot be built without its quote; `EvidenceRefClaimV1` still admits `quote=None` | PASS | `test_the_quoted_subtype_cannot_be_built_without_its_quote` |
| A8 | The critic contracts carry `premise_evidence` and keep their `contract_id` values | PASS | `test_the_critic_contracts_carry_quoted_evidence_and_keep_their_ids`; wheel smoke green on the MCP schema shas |
| A9 | A verified quote makes the attribution DEPEND on the citation record | PASS | `test_a_verified_quote_makes_the_attribution_depend_on_the_citation` — through the real Scheduler loop, no hand-built receipt |
| A10 | An unverified quote grounds nothing, is recorded, and does not cost the premise its filing | PASS | `test_a_quote_that_is_not_in_the_bytes_grounds_nothing` |
| A11 | The premise ref is still MENTION | PASS | same test as A9 — asserted on the same attribution |
| A12 | A resumed critic whose call exposed evidence recovers identically | PASS, **mutation-checked** | `test_a_resumed_critic_tolerates_an_evidence_exposure_entry`; widening `exposed` back to every namespace raises `NonConjectureRecoveryAuthorityError` |
| A13 | ONE offline loop in which a derived problem's conjecturer sees the legend AND a premise attribution is filed with a byte-checked quote | **PARTIAL — the two halves are proven, the combination is not** | See "What was not proven" |

## Hard constraints, checked rather than asserted

| Constraint | How it holds |
|---|---|
| No new LLM role | Two optional fields on existing contracts and one optional pack section. `contract_id` values unchanged (A8), so no qualification subject digest moves. |
| Frozen surfaces untouched | No event type added: the citable exposure rides the EXISTING `ContextExposureReceiptV2` through the existing `WORK_ISSUED` append. `harness.py` event application, `capabilities/state.py`, `invariants.py` and `run_manifest.py` are untouched by this diff. |
| All configurations compile | Nothing here can refuse a config. A run with no dossier renders no legend, declares no citable plan, and passes `None` for the exposure binding — which is byte-identical to the pre-P4 path (A6). |
| Solo runs reach everything | The channel needs one critic seat and one dossier; no ensemble, no judge, no second family. |
| Nothing weights an outcome on citation | A verified citation adds a DEPENDENCE edge to the ATTRIBUTION and nothing else. No rank, admission, acceptance or status reads `premise_evidence`; an unverified citation still leaves the premise filed (A10). |
| Attention only where Rung 2 said so | Unchanged: this tranche registers no warrant and assigns no status. |
| No cross-version proof owed | None attempted (2026-08-14 law). |

## Two failures the first gate found, and what they were

Recorded because both were real and one changed the design:

1. **`test_signals.py` — an undeclared signal.** `premise-citation:` was emitted
   before it was declared. Fixed the way `DR-REC-add-signal` says: a
   `SignalDeclaration` with a real unit (`event`) and staleness (`permanent`),
   through a new `_DECLARED_PREFIXES` tuple, because `_PREFIX_MEANINGS` is the
   pre-contract migration pool and every entry in it carries `unspecified` —
   which a new signal may not use. The migration census is unchanged at 89.
2. **`test_l1_continue_resumable_crash.py` — a committed fixture stopped
   replaying.** `premise_evidence` defaulted to `[]`, which survives
   `exclude_none`, so every batch-critic admission digest moved and a 2026-08-08
   root's recovery refused. The 2026-08-14 law says old roots are owed nothing,
   so this was NOT an obligation — but the field's two siblings on the same
   contract (`premise`, `counterexample`) are both `| None = None`, and matching
   them is the more consistent shape anyway. Digest stability came free with the
   consistency, so the regression test was kept rather than retired.

A third instrument reading was discarded rather than reported: the second gate
run showed 4 MCP failures, all thread-timing, because docs_verify was running
concurrently. Re-run idle they pass, and the gate figure above is from a run
with nothing else on the machine.

## Two map claims this change falsified, and one it obeyed

- `CON-packs-and-token-economy` pinned `render_crit_pack` at 10 pack sections
  and `SEAM-rules-x-workflow` pinned 32 workflow imports across the two rules
  modules; both counts moved and both were updated in this commit.
- `SEAM-capabilities-x-rules` holds that exactly ONE rules module reaches the
  capabilities package. The first draft of `_citable_blocks` imported
  `consumed_research_blocks` into `crit.py` and broke it. The check was NOT
  updated: the boundary was obeyed instead, and the critic's citable universe is
  bound-dossier blocks only. That is a real capability loss, stated in
  DELIVERY.md rather than absorbed silently.

## What was not proven

- **A13's combination.** A3/A4 prove the derived-problem legend and its receipt
  through the real `conj` under a v6 manifest; A9/A10 prove the quoted-citation
  filing through the real `Scheduler` loop. No single offline run does both,
  because the premise loop fixture runs without a run manifest (so it has no
  exposure receipt) and the v6 conjecture fixture drives one call rather than a
  scheduler. Building the combined fixture is a scheduler-level v6 run with a
  bound dossier, a derived problem AND a standing invitation; it is worth doing
  when A19 is unblocked, and it is not done here. **Consequence, stated
  plainly: the two halves are each proven against the record, and their
  composition rests on reading the code rather than on a test.**
- **The exposure binding is not exercised on the criticism path end to end.**
  `_exposed_block_ids_for_call` matches an exposure receipt to a provider call
  by prompt digest, and A12 proves the recovery half accepts evidence entries,
  but no test drives a v6 critic call that both showed blocks and cited one.
  The same combined fixture would cover it.
- **A19 remains unexercised**, now for one reason instead of two: P4 has landed,
  so only the credential is missing. R62's policy block is discharged.

## Budget

**EXCEEDED and disclosed, not re-baselined.**

| Area | Budget | Measured | Over |
|---|---|---|---|
| production | 420 | 541 | +121 |
| tests | 340 | 774 | +434 |
| map documents | 260 | 184 | — |

The test overrun is the honest number and the estimate was simply wrong: four
of the acceptance checks drive real fixtures (a bound dossier and a v6 manifest
for A3/A4, the siren loop for A9/A10, a durable criticism transaction for A12),
and fixture construction is most of the file. The production overrun is the
recovery half plus the critic-side legend, both of which the SPEC named and
neither of which was priced.
