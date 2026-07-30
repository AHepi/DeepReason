# Fix: compare a quote to the block's words, not to its line layout

Guarantee restored: a quoted citation verifies when, and only when, its
non-whitespace characters appear contiguously and in order in the cited
block's canonical text — the source author's line breaks and alignment
padding no longer decide whether a grounding is established.

## Change sites (exhaustive)

  - `src/deepreason/evidence/citations.py` (imports) — add `re`.
  - `src/deepreason/evidence/citations.py` (new module-level helper,
    ~10 lines) — `_WHITESPACE = re.compile(r"\s+")` and
    `_whitespace_folded(text)` returning `_WHITESPACE.sub(" ", text).strip()`,
    with a comment stating the constraint the code cannot show: admitted
    text carries the author's hard wrapping, a model reproduces running
    text, and layout is not part of the claim being checked.
  - `src/deepreason/evidence/citations.py:192` — replace the single
    containment test with: strict byte containment first; on failure,
    fold both sides and retry; only if both fail record
    `EVIDENCE_QUOTE_MISMATCH`. Carry which branch matched so the
    verified record can say so.
  - `src/deepreason/evidence/citations.py:207-219` — the
    `EVIDENCE_CITATION_VERIFIED` append gains a third `detail` wording
    for the folded case ("quote verified against the block's canonical
    text after folding whitespace; the admitted line breaks and
    alignment are not required to be reproduced").

`rules/conj.py` is NOT changed: the caller passes nothing new and the
Measure signal it records is the code, which is unchanged.

## The typed-code question, decided

Rejected: minting `EVIDENCE_QUOTE_REFLOWED` as a distinct code. A
reflowed quote is a verified citation, not a lesser kind of one — the
check exists to establish whether the model reproduced the source's
words, and layout is not part of that question. A distinct code would
also have to be threaded through `capabilities/research.py:71` and
`findings.py:190/194/200/532/535`, all outside this GOAL's scope, and
until it was, every folded match would be reported to the operator as a
FAILED citation — strictly worse than today.

The honest cost, stated: the ledger event carries only the code
(`rules/conj.py:2314`), so the record will not distinguish an exact
quote from a folded one as a verdict. This is acceptable because the
distinction remains **recoverable from the record at any time** — the
candidate's quote and the admitted source bytes are both immutable and
retained, which is exactly how this tranche's own diagnosis re-derived
all 15 field cases. Nothing is lost; it simply is not a second verdict.
`EvidenceCitationCheckV1.detail` still names the branch for any
in-process reader and for tests.

## Folding strength: all whitespace, not line breaks alone

Line-break folding alone recovers 13 of the field run's 15 quotes. The
2 it misses are indented math blocks where the source uses alignment
double-spaces the model collapsed
(`sum_k  U_k[...]  ==  T[...]` quoted as `sum_k U_k[...] == T[...]`).
Full folding recovers 15/15 and states one rule rather than two.

Strictness is preserved where it matters. Folding maps runs of
whitespace to one space; it never inserts whitespace where the source
had none, so `"foobar"` still fails against `"foo bar"` and `"foo bar"`
still fails against `"foobar"`. Every non-whitespace character must
still appear, contiguously and in order.

The one real widening, stated rather than discovered later: within a
single block, a quote may now span a blank line, joining text the source
separated into paragraphs (or a `section` block's heading to its body).
The joined text is still contiguous admitted text from the block the
citation names, so it remains a faithful quotation of that block; it is
recorded here because it is a genuine loosening, not because it is
believed harmful.

## Guard

A quote that folds to the empty string must NOT verify. `"" in anything`
is `True`, so the folded branch is gated on `folded_quote` being
non-empty. `EvidenceRefClaimV1.quote` has `min_length=1` but permits a
string of only whitespace, so this is reachable from the wire.

## Regression artifact

`experiments/2026-07-30-fix-citation-quote-check/repro_quote_reflow.py`
must invert:

    same text, newline->space : EVIDENCE_CITATION_VERIFIED   (was MISMATCH)
    fabricated (1976 -> 1979) : EVIDENCE_QUOTE_MISMATCH      (unchanged)
    honest reflowed quote and fabricated quote share one code: False

New conditions the permanent test must cover, beyond the repro:
  - quote crossing a hard newline, newline written as a space -> verified
  - quote crossing a newline plus list indentation (`\n   `) -> verified
  - quote collapsing an intra-line run of spaces -> verified
  - quote altering a non-whitespace character -> `EVIDENCE_QUOTE_MISMATCH`
  - quote deleting whitespace entirely (`"foobar"` for `"foo bar"`)
    -> `EVIDENCE_QUOTE_MISMATCH`
  - all-whitespace quote -> `EVIDENCE_QUOTE_MISMATCH`
  - exact byte quote -> still `EVIDENCE_CITATION_VERIFIED`, detail
    unchanged from today's wording
  - docstring names the motivating run
    ("Regression (tensorrank run-27b80f26bd398c718360e97e2a403593): ...")

## Existing tests at risk

  - `tests/test_evidence_citations.py::test_exact_quote_verifies_and_mismatch_is_a_typed_finding`
    (line 94) — **will invert; predicted here.** It asserts today that
    `canonical.replace(" ", "  ", 1)` yields `EVIDENCE_QUOTE_MISMATCH`.
    The local is named `reworded`, but the edit alters no non-whitespace
    character, so the fixture depended on exactly the defective
    behaviour. Minimal update: re-point that case at a genuinely
    reworded quote (alter a word) and keep the strict
    `EVIDENCE_QUOTE_MISMATCH` assertion there, so the test keeps testing
    what its name claims. The doubled-space case moves into the new
    regression test as a positive.
  - `tests/test_research_capability.py:421` — uses
    `canonical + " reworded"`, which adds a real word absent from the
    block. Unaffected; must keep passing unchanged.
  - `tests/test_amendment_epochs.py:288/308` — quote `"loop gain"` and
    `"Nyquist"`, both exact single-line substrings already verifying.
    Unaffected; must keep passing unchanged.

## Explicitly not changed

The admission path (`deepreason/admission.py`, block spans,
`text_sha256`). Normalising or re-wrapping at admission would change
block ids and dossier digests and invalidate every committed root —
wrong by definition. The comparison moves; the admitted bytes do not.

Also unchanged: `capabilities/research.py:71`. Its allowance tuning
counts verified citations, so folded matches will now count toward it.
That is the intended consequence flagged in DIAGNOSIS.md, and it is
correct — a verified citation is a verified citation — not a regression
to suppress.

Also unchanged: the unquoted-reference path (PARKED Q1), D2, and P4.

## Estimated diff

~30 changed lines in `src/deepreason/evidence/citations.py`,
~50 in `tests/test_evidence_citations.py`. 2 files, ~80 lines. Under the
150-line budget.

## Approval gate

GOAL.md classes this `defect`; diff estimate is 80 lines across 2 files;
no frozen surface is touched (`verify_root` reads none of this, and the
admitted bytes are untouched). Proceeds to `dr-implement-fix`.

---

## Amendment (during implementation): two documentation sites the plan missed

Implementation surfaced two docstrings that describe the old rule and
would be left asserting something the code no longer does. Recorded here
before the change, per the tranche rule against silent scope growth.

Added change sites:

  - `src/deepreason/evidence/citations.py` module docstring — says
    "every quote is byte-checked against the block's canonical text".
    Becomes a statement of the actual rule: checked against the
    canonical text with whitespace folded, every non-whitespace
    character still required.
  - `src/deepreason/llm/contracts.py:20-27`, `EvidenceRefClaimV1`
    docstring — says a quote "must reproduce a contiguous byte span of
    the block's canonical text exactly — the citation checker
    byte-verifies it". Becomes the true contract, and states positively
    that whitespace need not match while every other character must.

### Why the second one needed checking before it could be written

Pydantic promotes a model's class docstring to the JSON schema's
`description`, and that schema is serialised into the conjecturer's
context pack — so this docstring is prompt text the model reads, not
merely developer documentation. CLAUDE.md freezes anything that alters
qualification subject digests, which made this a potential stop.

Checked, and it is not one. `qualification_subject_payload`
(`src/deepreason/qualification.py:248-283`) closes over the provider
profile identity, the policy preset, the manifest behaviour, and a pair
inventory whose payload fields are
`contract_id, role, seat, endpoint_id, route_sha256, model_id,
model_revision, provider, family, output_mechanism`. No contract JSON
schema and no docstring text enters it. Corroborated against the
committed artifact: the tensor-rank run's
`production-contract-qualification.json` contains no `description` key
and none of the docstring's wording anywhere in its 65,975 bytes.

So the digest does not move, the qualification cache is not invalidated,
and no committed root is affected — their packs are already recorded in
their own blob stores. What does change is the prompt bytes of FUTURE
runs, which is intended: the contract the model is shown should be the
contract the harness enforces.

Revised estimated diff: ~40 lines in `citations.py`, ~8 in
`contracts.py`, ~90 in `tests/test_evidence_citations.py`. 3 files,
~138 lines. Still inside the 150-line budget.
