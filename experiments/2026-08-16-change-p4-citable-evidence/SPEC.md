# SPEC — P4, three-layer citable evidence

Discharges REQUEST.md M1–M7.

## Map preflight (resolved ids, read in this order)

| Id | Why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | read first; the change must not touch `harness.py` event application, manifest schemas, or anything moving a qualification subject digest |
| `DR-SEAM-rules-x-workflow` | **the load-bearing seam.** The exposure receipt is a workflow record produced by a rule; its "How to change it" fixes the order: record → service → replay → rule → **recovery** |
| `DR-SEAM-llm-x-rules` | the contract half: a new wire field is a contract change the rule must render and re-read |
| `DR-CON-packs-and-token-economy` | the citable legend is a pack SECTION and is byte-accounted like every other |
| `DR-CON-conjecture-source` | the conjecturer half of the render fix (M1) |
| `DR-CON-criticism-source` | the critic half (M6) — the seat that authors calculus claims |
| `DR-SUB-calculus` | the claim substrate whose interface must gain the evidence dependence (M5) |
| `DR-SUB-workflow` | `ContextNamespace`, `ContextPackPlanV1`, `ContextExposureReceiptV2` live here |

**Map gap, recorded rather than papered over:** `src/deepreason/evidence/` — the
dossier, the admission blocks, the citation checker — is covered by NO map
document. `SUB-bridge.md` owns `bridge/evidence_pack.py`, which is a different
thing (the grounded-application bridge's pack, not the run's dossier). This
tranche makes a load-bearing change inside that package, so it writes
`SUB-evidence.md` in the same commit as the code. That is the SCHEMA rule
applied to an uncovered package, not scope creep.

## What is actually broken (measured, not assumed)

Three separate facts, each confirmed by reading the tree, not by trusting the
advice's numbers:

1. `rules/conj.py:1349` renders the citable-block legend from
   `_union_blocks(bound_dossiers) if bound_dossier is not None else ()`.
   `bound_dossier` is set only when `addressed` — that is, only when the
   problem's id is an EPOCH problem id. Every derived problem therefore sees
   `consumed_research_blocks(harness)` and nothing else. This is exactly the
   advice's "subproblems received aliases rather than citable block IDs": the
   dossier reaches them as `SRC_nnn` source excerpts, and the block ids the §4
   checker resolves against are never shown.
2. The legend that IS rendered appears in **no** durable record. The v6
   exposure receipt (`ContextExposureReceiptV2`) carries source, simulation and
   scratch items; the citable blocks are in the prompt bytes and nowhere else.
   There is no typed record of which blocks a call could see.
3. `evidence/citations.py::check_candidate_citations` resolves a citation
   against the whole bound dossier. A model that names a block id it was never
   shown verifies identically to one that quotes what it read.

`EvidenceRefClaimV1.quote` being optional is the fourth fact, and the one R62
forbids fixing by mutation.

## Design

### Layer 1 — the blocks reach every problem, and the receipt records them (M1, M2)

- `workflow/transaction.py` gains `ContextNamespace.EVIDENCE = "evidence"` with
  alias prefix `EVD_`, and `ContextPackPlanV1.plan_kind` gains `"citable"`.
  A separate namespace rather than more `SRC_` aliases: the exposure receipt
  requires aliases AND object refs unique across every plan in one call, and —
  the substantive reason — `wire.py`'s semantic-retrieval contract lets a model
  REQUEST context by visible `SRC_###` alias. A citable block is not
  requestable context; it is already in the prompt. Putting it in the source
  namespace would invent a handle the model could ask for and the packer could
  not serve.
- `evidence/render.py::render_citable_blocks` currently returns text and
  silently drops blocks it could not render (unrecoverable bytes, empty
  excerpt, over the cap). Split the decision from the string:
  `citable_legend(blocks, blobs, ...) -> CitableLegend(text, shown)` where
  `shown` is exactly the blocks whose bytes are in `text`. `render_citable_
  blocks` stays as a thin wrapper (one existing caller, one test).
  **The receipt is built from `shown`, never from the input list** — a receipt
  claiming exposure of a block the packer dropped is a false record, and the
  drop is silent by design so that presentation never fails a pack.
- `rules/conj.py`: the legend's block universe becomes
  `_union_blocks(bound_dossiers) + consumed_research_blocks(harness)`
  unconditionally — the dossier is bound to the RUN, and a derived problem is
  reasoning about the same run's evidence. A `plan_kind="citable"` context plan
  is appended with one `VisibleContextItemV1` per shown block:
  `object_ref` = the full block id, `content_sha256` = the block's
  `text_sha256`, `planned_bytes` = the legend's rendered bytes on the first
  item and 0 on the rest (the batch-critic convention at `crit.py:405`, because
  the legend is one indivisible section).

### Layer 2 — a quoted subtype, old V1 unmutated (M3)

- `llm/contracts.py` gains `QuotedEvidenceRefV1`: same `block` pattern,
  `quote: str` **required**, `min_length=1`. `EvidenceRefClaimV1` is untouched —
  checked by a test that asserts its `quote` annotation still admits `None`.
- The calculus claim channel — the `premise` field the Rung 2 critic contracts
  carry — gains `premise_evidence: list[QuotedEvidenceRefV1]` (max 2) on
  `ArgumentativeCriticOutput` and `BatchCase`, and their `wire.py` mirrors.

**Assumption recorded (SPEC's own, per the scope contract):** the advice says
"require quotes for the new claim contracts". The smallest reading that does
not break the harness is *a citation carried by a calculus claim must be
quoted*, NOT *every calculus claim must cite*. The wider reading would make the
premise channel unusable in the configurations the standing laws protect — a
solo run with no dossier bound has nothing to quote, and an all-configs
compile may not refuse it. So `premise_evidence` is optional and empty is
legal; what is illegal is an unquoted entry, which the type makes
unrepresentable.

### Layer 3 — admission byte-checks against the recorded bytes (M4)

- `evidence/citations.py` gains one code, `EVIDENCE_REF_NOT_EXPOSED`, and one
  optional keyword `exposed_block_ids`. When supplied, a citation resolving to
  a block outside that set records `EVIDENCE_REF_NOT_EXPOSED` instead of
  `EVIDENCE_CITATION_VERIFIED`. When not supplied the behaviour is byte-identical
  to today — every existing caller keeps its semantics until it opts in.
- The conjecture admission path passes the set from the citable plan it just
  built. The set comes from the RECORD (the plan items), not from the local
  variable that rendered the legend: layers 1 and 3 must agree because they
  read the same receipt, not because the code was written on the same day.

### Layer 4 — the claim interface depends on the admitted evidence record (M5, M6)

- `rules/crit.py::_file_attribution`: when `premise_evidence` is present, each
  entry is checked with `check_candidate_citations` against the exposed set.
  Entries that verify become ONE `evidence-citation` artifact registered by the
  ordinary path; entries that do not are recorded as failed checks and
  contribute nothing (the standing rule: visibility never creates support, and
  neither does a claim of support).
- `calculus/claims.py::PremiseAttributionV1` gains
  `evidence_ref: str | None` — the artifact id of the admitted citation record.
- `calculus/compiler.py` compiles it as `RefRole.DEPENDENCE`, the second and
  last dependence in that body. The reason it is a dependence and not a
  mention, stated where the code cannot show it: if the evidence record falls,
  the attribution's support falls with it — which is the whole point of R62's
  fourth line. The premise itself stays a MENTION (law 9.4'); this changes
  nothing about the mention-law.
- The critic pack carries the citable legend **only when the premise invitation
  is present**, so this adds no bytes to ordinary criticism.
- `workflow/nonconjecture_recovery.py:730-740` asserts the critic's exposure is
  exactly the target aliases and every entry is `SOURCE`. Both assertions
  narrow to the SOURCE-namespace entries, so an evidence plan cannot make a
  resumed critic diverge. **This is the recovery half the seam document warns
  is forgotten** — it moves in the same step as the dispatch half.

## Order of work (forced by `DR-SEAM-rules-x-workflow` "How to change it")

Record → service → replay → rule → recovery. Concretely: transaction.py first,
then the render split, then conj.py, then citations.py, then the contracts,
then crit.py + calculus, then recovery. Steps in CHECKLIST.md follow this and
may not be reordered.

## Budget

Honest estimate, not an aspiration — the last three tranches all overran and
were disclosed rather than re-baselined:

| Area | Budget |
|---|---|
| production | 420 lines changed |
| tests | 340 |
| map documents | 260 (`SUB-evidence.md` is new) |

Overrun is disclosed in VALIDATION.md, never silently re-baselined.

## Out of scope, explicitly

- **A19 stays deferred.** M7 is a policy requirement discharged by NOT running
  a pilot; delivering M1–M6 unblocks it in principle and it still needs a
  credential.
- **P4b's prompt wording** ("optionally with a quote") for the OLD conjecturer
  contract stays parked, per the program's RECONCILIATION §2 P4 row. This
  tranche changes what the old contract's citations are CHECKED against
  (layer 3), never what its schema requires.
- The advice's `EvidenceRefClaimV1`-wide quote requirement is refused by R62
  itself and is not implemented.
- **RECONCILIATION's "P4 absorbed by Rung 5" row is superseded** by the
  operator's board sentence, which schedules P4 as its own tranche before Rung
  3b. Recorded in that file rather than silently diverged from.
