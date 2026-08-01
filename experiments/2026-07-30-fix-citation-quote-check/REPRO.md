# Reproduction

Form: unit-style fixture (part 1) + record replay (part 2), in one
offline script. No production code touched; no run root's contents
edited.

Artifact: `experiments/2026-07-30-fix-citation-quote-check/repro_quote_reflow.py`

    python3 experiments/2026-07-30-fix-citation-quote-check/repro_quote_reflow.py

Current output:

    PART 1 - fixture, one block, three quotes
      block spans 3 hard newline(s)
      exact bytes incl. newline : EVIDENCE_CITATION_VERIFIED
      same text, newline->space : EVIDENCE_QUOTE_MISMATCH
      fabricated (1976 -> 1979) : EVIDENCE_QUOTE_MISMATCH

    PART 2 - the committed root's own quotes (15 distinct)
      exact byte sub-span            : 0
      present only after reflow      : 15
      absent under any whitespace    : 0
      block unresolvable             : 0

    VERDICT
      honest reflowed quote and fabricated quote share one code: True (EVIDENCE_QUOTE_MISMATCH)
      field failure is the same mechanism: True

Confirms diagnosis: yes. Part 1 hits the prediction exactly — the same
text verifies with the source's newline in place and fails with that one
newline written as a space, so the verdict is decided by line layout.
Part 1's third line is the part that matters most: an honest reflowed
quote and a quote with a falsified date return the *identical* code, so
the check does not discriminate between them. Part 2 shows the fixture
is not a lookalike: all 15 distinct quotes from
`run-27b80f26bd398c718360e97e2a403593` fall in the reflow bucket, none
exact, none absent, none unresolvable.

Post-fix expectation:

    exact bytes incl. newline : EVIDENCE_CITATION_VERIFIED   (unchanged)
    same text, newline->space : EVIDENCE_CITATION_VERIFIED   (was MISMATCH)
    fabricated (1976 -> 1979) : EVIDENCE_QUOTE_MISMATCH      (unchanged)
    honest reflowed quote and fabricated quote share one code: False

Part 2 is a measurement of the committed record, not of the code under
test; its four numbers must not move, because the admitted bytes and the
recorded quotes are immutable. What changes after the fix is what the
checker would now *return* for those same 15 pairs.

## Collision the fix must handle, found while building this

`tests/test_evidence_citations.py::test_exact_quote_verifies_and_mismatch_is_a_typed_finding`
asserts today that `canonical.replace(" ", "  ", 1)` — a quote differing
from the admitted text ONLY by one doubled space — yields
`EVIDENCE_QUOTE_MISMATCH`. The variable is named `reworded`, but the edit
alters no non-whitespace character. Any fix that makes reflowed quotes
verify inverts this assertion.

Under CLAUDE.md a fixture that depended on defective behaviour may be
minimally updated only when the fix's design doc predicted it, so
FIX.md must name this test, state whether a doubled space is meant to
verify or to fail, and justify the answer. It is not a licence to relax
the assertion silently: the honest options are to re-point the test at a
genuinely reworded quote (changing non-whitespace characters) and keep a
strict-failure case there, or to argue that intra-line whitespace should
stay strict while only line-break folding is tolerated — which is a
narrower fix and a different implementation.
