<!-- DR-SUB-evidence -->
Verified-at: 39566854
Verify: python -m pytest tests/test_evidence_citations.py tests/test_p4_citable_evidence.py -q
Owns: src/deepreason/evidence/citations.py, src/deepreason/evidence/dossier.py, src/deepreason/evidence/models.py, src/deepreason/evidence/render.py, src/deepreason/evidence/state.py
Seams: 
Seams-undocumented: evidence x rules, evidence x workflow, evidence x amendment

# Attached evidence — dossiers, admitted blocks, and byte-checked citations

## What it is

A run may be given source documents. This package is everything that happens to
them between "the operator handed us a file" and "the record says a candidate
quoted block `a1b2…` exactly": admission into content-addressed blocks, frozen
selection of what a prompt may show, model-facing rendering, and the
deterministic check of every citation a model claims.

The package's whole design turns on one refusal: **attachment is not support.**
A source in the dossier is untrusted data. Rendering it into a prompt does not
make it true, relevant, or in-scope, and no path here assigns a status. What it
produces are typed CHECKS and typed RECEIPTS, which criticism can then attack
like anything else.

## Entry points

| Caller wants | Calls | Lives in |
|---|---|---|
| to freeze what one call may show | `pack_dossier(...) -> DossierPackReceiptV1` | `dossier.py` |
| to make that receipt reachable | `commit_dossier_pack_receipt(harness, receipt)` | `dossier.py` |
| the prompt text for a bound dossier | `render_dossier_pack(...) -> str` | `render.py` |
| the citable-block legend AND what it actually showed | `citable_legend(blocks, blobs) -> CitableLegend \| None` | `render.py` |
| just that legend's text | `render_citable_blocks(blocks, blobs)` | `render.py` |
| to check what a model claimed | `check_candidate_citations(...) -> tuple[EvidenceCitationCheckV1, ...]` | `citations.py` |
| a block's exact admitted text | `canonical_block_text(block, source_bytes)` | `citations.py` |

`check: python -c "from deepreason.evidence import canonical_block_text, check_candidate_citations, citable_legend, commit_dossier_pack_receipt, pack_dossier, render_citable_blocks, render_dossier_pack" && grep -q "^def citable_legend(" src/deepreason/evidence/render.py && grep -q "^def check_candidate_citations(" src/deepreason/evidence/citations.py && grep -q "^def pack_dossier(" src/deepreason/evidence/dossier.py`

## State it owns

Nothing mutable. Every record here is content-addressed and frozen:

- `EvidenceDossierV1` / `V2` — the admitted sources and, from v2, the
  `AdmissionBlockV1` blocks. Bound to the root by `bind_run_input`.
- `AdmissionBlockV1` — one canonical unit. **Evidence-tier blocks are always
  SPAN blocks**: their text is the byte slice of the admitted source, never
  inlined, so the text a citation is checked against is recovered from
  content-addressed bytes rather than from a copy someone could edit.
  `extracted` blocks lack byte-span fidelity and are refused the evidence tier
  outright.
`check: python -c "
from deepreason.evidence.models import AdmissionBlockV1
import hashlib
body=b'x'; d=hashlib.sha256(body).hexdigest()
base=dict(schema='admission-block.v1', id=d, source_sha256=d, span_start=0, span_end=1, text_sha256=d)
try:
    AdmissionBlockV1.model_validate({**base, 'kind':'paragraph', 'tier':'evidence', 'text':'x'}); raise SystemExit('span block inlined its text')
except Exception as e:
    assert 'span blocks never do' in str(e), e
try:
    AdmissionBlockV1.model_validate({**base, 'kind':'extracted', 'tier':'evidence', 'text':'x'}); raise SystemExit('extracted entered the evidence tier')
except Exception as e:
    assert 'cannot enter' in str(e), e
"`
- `DossierPackReceiptV1` — which sources one call was allowed to show, why
  (`policy_digest`), and against which state fence. Selection is deterministic:
  literal token overlap, then under-exposure, then a seeded tie-break over the
  run input digest — no clock, no randomness.
- `EvidenceCitationCheckV1` — one durable outcome per claimed citation. Seven
  codes; `verified` is the property, not the absence of a failure.

## Invariants

- **Visibility never creates support.** The legend and the pack are
  presentation; the checker is the sole authority on what a citation
  establishes, and even a verified citation assigns no status.
- **A quote is compared to admitted bytes, twice.** Exact byte containment
  first; then whitespace-folded containment, so the source author's line
  wrapping cannot decide the verdict while every non-whitespace character must
  still appear contiguously and in order. The empty-fold guard is load-bearing:
  a whitespace-only quote folds to `""`, which is a sub-span of everything.
`check: python -m pytest tests/test_evidence_citations.py -q`
- **Presentation never fails a pack.** `citable_legend` silently drops a block
  whose bytes cannot be recovered. That is why it returns `shown` alongside
  `text` — see the trap below.
- Frozen surfaces: none of this package is frozen. The records it writes reach
  `DR-SUB-verification` through the run root, and the manifest policies that
  bound it (`AttachedEvidencePolicyV1`) live behind `DR-SUB-manifest`, which
  is.

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| change what a prompt may show per call | `dossier.py::pack_dossier` bounds | `tests/test_evidence_dossier.py` |
| change how a citation is resolved or checked | `citations.py::check_candidate_citations` | `tests/test_evidence_citations.py` |
| change what the citable legend renders | `render.py::citable_legend` | `tests/test_p4_citable_evidence.py` |
| change which blocks a call may cite | the CALLER (`rules/conj.py`), not this package | `tests/test_p4_citable_evidence.py` |
| add a citation failure code | `citations.py` `Literal[...]` + the module constant | `tests/test_evidence_citations.py` |

## Traps

- **`citable_legend` returns two fields because the receipt is built from the
  second one.** Rendering drops blocks — unrecoverable bytes, empty excerpt,
  past the cap — and drops them silently by design. A context-exposure receipt
  built from the block universe rather than from `shown` would claim the run
  exposed bytes it never rendered, which is a false record in the one place the
  system treats as evidence. P4 (`experiments/2026-08-16-change-p4-citable-
  evidence/`) added the second field for exactly this reason, and the caller in
  `rules/conj.py` filters `shown` a second time against the rendered pack,
  because section allocation can still compress the legend out after it was
  rendered.
`check: grep -q "class CitableLegend(NamedTuple):" src/deepreason/evidence/render.py && grep -q "shown: tuple" src/deepreason/evidence/render.py && grep -q 'if f"\[{block.id\[:16\]}\]" in pack' src/deepreason/rules/conj.py && python -m pytest tests/test_p4_citable_evidence.py::test_an_unrenderable_block_is_in_neither_the_text_nor_the_receipt -q`
- **The citable universe is the RUN's, not the seed problem's.** Before P4 the
  legend was gated on the problem being an amendment-epoch problem, so every
  derived problem reasoned about the run's evidence while unable to name one
  block the checker resolves. The gate is gone; the dossier is bound to the run
  input, and every problem in that run sees the same citable set.
`check: python -m pytest tests/test_p4_citable_evidence.py::test_a_derived_problem_sees_the_citable_block_ids -q`
- **A citation resolves by unique PREFIX, and ambiguity is a typed outcome, not
  a best match.** `EVIDENCE_REF_AMBIGUOUS` exists because a 12-hex prefix can
  match two blocks; silently taking the first would make a citation's meaning
  depend on dossier order.
`check: grep -q "EVIDENCE_REF_AMBIGUOUS" src/deepreason/evidence/citations.py && grep -q "if len(matched) > 1:" src/deepreason/evidence/citations.py`
- **Evidence is cumulative across amendment epochs.** A citation verified
  against the first dossier must verify identically after later ones are bound,
  which is why `check_candidate_citations` takes `dossiers` (the union) rather
  than one dossier. Passing a single dossier where a union was meant silently
  narrows what a candidate may cite.
`check: python -m pytest tests/test_amendment_epochs.py -q -k citation`
