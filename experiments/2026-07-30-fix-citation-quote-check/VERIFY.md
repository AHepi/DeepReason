# Verification

## Criterion 1 — the regression test

    $ pytest tests/test_evidence_citations.py -q
    ...........                                                    [100%]
    11 passed in 0.24s

    $ pytest tests/test_evidence_citations.py::test_quote_is_checked_against_the_blocks_words_not_its_line_layout -v
    PASSED

Its docstring names `run-27b80f26bd398c718360e97e2a403593`. It covers
(a) a hard newline written as a space, a newline plus list indentation,
and a collapsed intra-line run of spaces — all verified; (b) a quote
absent under any whitespace reading (`"\n"` deleted, joining words the
source separated) and an all-whitespace quote — both
`EVIDENCE_QUOTE_MISMATCH`; (c) a quote with a non-whitespace character
altered (`1976` -> `1979`) — `EVIDENCE_QUOTE_MISMATCH`.

## Criterion 2 — the full gate

    $ pytest tests/ -q -n 4
    3168 passed, 7 skipped in 490.99s (0:08:10)

Run exclusively, no concurrent gate (PARKED P3).

## Criterion 3 — historical roots

`verify_root` over all 16 committed run roots, diffed against the
pre-change baseline captured at `301885f0`: **byte-identical**.

Remaining violations, listed by class rather than summarised away — all
pre-existing, none introduced, none masked:

    run-7d8723fbe8626c71db880826c244d332              foreign-criticism
    run-d17935a4bf5ffa67c7f6e67b9a637a00              foreign-criticism
    run-e542c3c1fc266943e0260c5aa8d7c107              foreign-criticism
    completed-epoch2-run-9e9812feefa792179d490db7734825b5  foreign-criticism
    completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a  foreign-criticism
    failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a     run-input
    failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a     terminal-authority

(23 foreign-criticism, 1 run-input, 1 terminal-authority — the same
counts as before the change.) The tensor-rank root itself remains clean.

## Reproduction inverted

    exact bytes incl. newline : EVIDENCE_CITATION_VERIFIED
    same text, newline->space : EVIDENCE_CITATION_VERIFIED   (was MISMATCH)
    fabricated (1976 -> 1979) : EVIDENCE_QUOTE_MISMATCH
    honest reflowed quote and fabricated quote share one code: False

Part 2's measurement of the committed record is unmoved (0 exact, 15
reflow, 0 absent, 0 unresolvable), as it must be — those bytes are
immutable.

## Counterfactual replay of the field failure

The field run's 15 recorded (block, quote) pairs, put through the fixed
checker against that run's own dossier and blob store:

    15  EVIDENCE_CITATION_VERIFIED

All 42 recorded failures were the same 15 claims re-checked across
cycles. This is a counterfactual, not a repair of the record: the root's
`log.jsonl` still carries its 42 `EVIDENCE_QUOTE_MISMATCH` events and
always will — the log is append-only and was not touched.

Live attempt: none. GOAL.md did not demand live proof, and a live run now
would confound this fix with D2, which is still unfixed.

## Verdict: PASS (offline)

## Residue, stated honestly

**No live run has exercised this.** The proof is an offline fixture plus
a replay of the committed record's own quotes. Whether glm-5.2 actually
produces verified groundings against a hard-wrapped dossier in a fresh
run is UNPROVEN here. What is proven is narrower and worth stating
exactly: the check no longer returns the same verdict for an honest
reflowed quote and a fabricated one, and the 15 claims that the field run
rejected would now be accepted.

**The wire contract still describes the old rule.** FIX.md was amended
mid-implementation to fix `EvidenceRefClaimV1`'s docstring, then the
amendment was RETRACTED when the gate returned `4 failed, 3164 passed`.
Pydantic promotes that docstring into the JSON schema `description`,
which is serialised into the conjecturer's context pack, and the pack's
bytes sit inside committed provenance digests —
`test_semantic_freedom_constitution`'s
`tokens_per_admitted_useful_candidate` baseline (842.0 measured vs 784.5
committed) and `test_incident_wave_a_v2_fixtures`'
`generated_root_sha256` (`a8ea8a62891a...` vs `d887b4494a5d...`).
Isolated rather than guessed: all four failures pass on a clean tree and
pass again with only `contracts.py` reverted.

So the model is still told a quote must reproduce a byte span "exactly".
That is stricter than the harness now enforces, so it costs nothing in
correctness — a model that obeys it verifies. It is documentation debt,
parked as D1a for the D2 tranche, which is about pack text and must price
the frozen-digest regeneration deliberately.

**The earlier frozen-surface check was too narrow, and that is the
transferable lesson.** Asking whether the qualification subject digest
carries contract schema text was the right question; it does not. But
generalising that one answer to "the digest does not move" was wrong. The
pack's bytes are load-bearing in more places than the qualification
subject, and only the full gate found them.

**Not addressed, by design:** an unquoted citation is still recorded as
"byte-verified" in FINDINGS.md (PARKED Q1); D2 (the sandbox program
contract); P4 (TOKEN_ACCOUNTING.json miscounting research as simulation).
