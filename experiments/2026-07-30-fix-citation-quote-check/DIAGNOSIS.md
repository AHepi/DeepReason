# Diagnosis: the quote check tests line-layout agreement, not textual agreement

Primary cause: `check_candidate_citations` decides a citation with
`ref.quote.encode("utf-8") not in canonical.encode("utf-8")`
(`src/deepreason/evidence/citations.py:192`), where `canonical` is the
admitted source's own bytes — including its hard line breaks and its
list/code indentation. A model renders a quote as running text. The
comparison therefore succeeds only when the model's line layout happens
to coincide with the source author's, and it emits the same
`EVIDENCE_QUOTE_MISMATCH` for an exact quote that crosses a wrap as for
a fabricated one. Because `TENSOR_RANK_CHALLENGE.md` is wrapped at a
mean non-blank line length of 61.9 characters and 17 of its 26 admitted
blocks span at least one newline, essentially every quote long enough to
ground a claim crosses a break, and the channel returns a constant
verdict carrying no information about the thing it exists to establish.

Evidence:

  - `<root>/log.jsonl` — 42 events whose `inputs[0]` is
    `evidence-citation:EVIDENCE_QUOTE_MISMATCH` and 4 whose `inputs[0]`
    is `evidence-citation:EVIDENCE_CITATION_VERIFIED`. Every one names a
    block id present in `evidence-dossier.json`; none is
    `EVIDENCE_REF_UNKNOWN_BLOCK` or `EVIDENCE_REF_AMBIGUOUS`. Block
    `70df46c005c3` appears in 7 mismatches and all 4 verifications.
  - The 42 reduce to 15 distinct (block, quote) pairs recovered from
    `<root>/blobs/`. Re-checked against each block's canonical text:
    0 exact, 15 present after whitespace normalisation, 0 absent,
    0 unresolvable. Nine differ from the admitted bytes only at a hard
    newline; six differ by a newline plus list indentation (`\n   `) or
    by runs of spaces inside an indented code block.
  - `evidence-dossier.json` + `<root>/blobs/3d/3d01498879...` — the
    admitted source blob is byte-identical to
    `experiments/live_research_2026-07-29/tensorrank-dossier/TENSOR_RANK_CHALLENGE.md`
    on disk, its sha256 matches the declared `source_sha256`, and all 26
    of its blocks' `span_start:span_end` slices hash to their recorded
    `text_sha256`. The wrapping is the author's; the parser reproduced
    it faithfully.
  - `verify_root(<root>)` returns `violations: []` with 499 events, 42
    artifacts, 42 accepted — clean, in the presence of all 42 citation
    failures.
  - `src/deepreason/invariants.py` — its only `rule.value == "Measure"`
    handler is `validate_foreign_criticism_coverage`, keyed on
    `inputs[0] == "foreign-criticism-coverage.v1"`. No site in
    `invariants.py` reads an `evidence-citation:` signal or imports
    `check_candidate_citations`. Replay validation neither recomputes
    nor depends on citation outcomes.

Implicated code:
  - `src/deepreason/evidence/citations.py:192` (the comparison)
  - `src/deepreason/evidence/citations.py:60` (`canonical_block_text`,
    which correctly returns the admitted bytes and must keep doing so)
  - `src/deepreason/rules/conj.py:2303` (the single production caller)

Falsifiable prediction (what `dr-reproduce` must show):

    An offline dossier admitted from a document hard-wrapped at ~72
    columns, cited twice against the same block:
      - quote reproducing the block's bytes across the wrap, newline
        included  -> EVIDENCE_CITATION_VERIFIED
      - the identical text with that newline written as a single space
        -> EVIDENCE_QUOTE_MISMATCH
    If the second case verifies, this diagnosis is wrong.

Ruled out: **a parser or span defect.** If the admission path had
mangled the block boundaries, the quotes would fail for a reason no
comparison change could repair. It did not: the admitted blob equals the
on-disk file byte for byte, every block's span slice hashes to its
recorded `text_sha256`, and the 15 quotes land inside the blocks they
name. The divergence is entirely between the model's rendering and the
source's line layout.

## Consequence the fix must account for (not a second cause)

`src/deepreason/capabilities/research.py:71` tunes the research request
allowance by counting `evidence-citation:EVIDENCE_CITATION_VERIFIED`
events. Making reflowed quotes verify will therefore raise that
allowance on future runs. This is forward-looking behaviour only — no
committed root is re-derived — but `dr-propose-fix` must state it rather
than discover it.
