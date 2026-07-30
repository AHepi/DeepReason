# Goal: a quoted citation of a hard-wrapped admitted block can verify

Class: defect

Observed: in `run-27b80f26bd398c718360e97e2a403593` (committed under
`experiments/live_research_2026-07-29/openchallenge/runs/`), `log.jsonl`
carries 42 `EVIDENCE_QUOTE_MISMATCH` events and 4
`EVIDENCE_CITATION_VERIFIED`. The 42 reduce to 15 distinct
(block, quote) pairs; re-checking each against its cited block's
canonical text — the digest-verified `span_start:span_end` slice of the
admitted source — puts all 15 in the block they cite once whitespace is
normalised, with 0 absent and 0 unresolvable. The 4 that verified carry
no quote at all, so the checker never compared any text for them. The
run's byte-checked citation score is therefore 0 of 50 quoted citations
and 4 of 5 unquoted ones, and 7 quoted citations of block `70df46c005c3`
failed while 4 bare references to that same block passed.

Why this is classed `defect` and not `capability-gap`: the admission
contract's stated purpose is that a citation is *checkable* — verification
and failure are both recorded outcomes, never silence
(`src/deepreason/evidence/citations.py` module docstring). A check that
returns the same verdict for an honest quote of wrapped text and for a
fabricated one does not discriminate, so the recorded outcome carries no
information about the thing it exists to establish. The run's own
FINDINGS.md reports the 42 failures as "groundings NOT established",
which is true of a fabrication and equally true of an exact quote of a
line-wrapped paragraph. The operator has in any case explicitly ordered
this fixed, so the class does not gate implementation.

Success criterion (machine-decidable):

    pytest tests/test_evidence_citations.py -q
        passes, including a new regression test naming
        run-27b80f26bd398c718360e97e2a403593 in its docstring, in which
        (a) a quote of a hard-wrapped admitted block differing from the
            admitted bytes ONLY by the source's line breaks and its
            list/code indentation yields a check with .verified is True;
        (b) a quote absent from the block under any whitespace reading
            still yields EVIDENCE_QUOTE_MISMATCH;
        (c) a quote whose non-whitespace characters are altered
            (a reworded or fabricated quote) still yields
            EVIDENCE_QUOTE_MISMATCH.

    pytest tests/ -q -n 4
        0 failed.

    verify_root over every committed run root in experiments/
        verdicts byte-identical to those at commit 301885f0.

In scope:
  - src/deepreason/evidence/citations.py
  - tests/test_evidence_citations.py
  - src/deepreason/rules/conj.py (only if the single production caller
    at line 2303 must pass something new; no rule-logic changes)

NOT in scope: the admission parser and block spans
(`src/deepreason/evidence/` admission path). Re-wrapping or normalising
text AT ADMISSION would change `text_sha256`, block ids, and dossier
digests, and would invalidate every committed root — wrong by definition
under CLAUDE.md. The comparison moves; the admitted bytes do not.

Also NOT in scope: D2 (the sandboxed_python_v1 program contract missing
from the context pack) and P4 (TOKEN_ACCOUNTING.json miscounting
research as simulation). Both are recorded in PARKED.md.

Budget: <=150 changed lines, 1 commit, ~2 hours
Stop conditions inherited from orchestrator: yes

## Design question this goal deliberately leaves open

The criterion commits to the OUTCOME (a reflowed quote verifies) but not
to the MECHANISM. `dr-propose-fix` must choose among at least:
normalising both sides before comparison; keeping the strict byte check
and adding a second, distinct typed code for a whitespace-only
divergence; or anchoring the comparison on the block's canonical text
with a reflow-tolerant matcher that still reports the matched span.
Whether a whitespace-tolerant match should record
`EVIDENCE_CITATION_VERIFIED` or a distinct code is a fix-design
question. It is NOT open to normalise the admitted bytes instead.

## Rejected alternative, recorded

"Tell the model to quote exactly, including line breaks." Rejected as
the primary fix: it leaves the check unable to discriminate an honest
reflowed quote from a fabrication, moves the burden to prompt text that
every future dossier author must also honour, and does not repair the
already-recorded run. It may still be worth doing in addition; that
belongs to the D2 tranche, which is about what the pack tells the model.
