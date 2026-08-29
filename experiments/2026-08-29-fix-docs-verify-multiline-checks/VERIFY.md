# VERIFY — against GOAL.md's four criteria

## R1 — an unparseable opener fails the run, never a skip: **PASS**

Mutation proof, a planted map directory holding one unclosed opener and
one sound check:

    docs_verify [full]: 1 documents, 1 checks, 4 workers
      FAIL INV-mutant.md:7: unparseable check: a column-0 `check: opener
      must close with a backtick at the end of the same line.
      Opener reads: '`check: python -c "'
    docs_verify: 1 failed
    exit code: 1

`--audit` reports the same opener. `--self-test` pins it in both
directions: an INDENTED example still parses to no check AND no error;
a column-0 opener that never closes parses to no check and exactly one
error — tested at end-of-file and mid-document.

Committed alone, before R2, exactly as GOAL.md required: R1 says "an
opener the grammar cannot read is loud" without saying what the grammar
is, so widening the grammar can only shrink the error set. There is no
longer a path through the parse loop that drops an opener.

## R2 — the 72 run as written: **PASS**

    docs/map/ parses:  1141 checks -> 1212 checks   (+70 committed, +1 new)
    unaccounted openers:   72      ->    0

No committed check text was rewritten. `SCHEMA.md` §Checks gained the
multi-line definition, one worked example, the totality rule and its
authoring price, in the same commit as the parser. `--self-test` covers
the multi-line form and prints the `--audit` lines that flag a
multi-line VACUOUS check and an unparseable opener:

      --audit over the self-test fixture:
        INV-selftest.md:21: unparseable check: a column-0 `check: opener …
        INV-selftest.md:17: vacuous check `true &&
                  true`
        docs_verify --audit: 2 finding(s)
    docs_verify --self-test: ok

The new `SCHEMA.md` check is falsifiable, proven by mutation: with
`_read_block` disabled the parser sees 0 multi-line checks and the check
exits 1 (`AssertionError: 0`). Tree restored byte-for-byte afterwards.

## R3 — every failure among the newly-executed tabled: **PASS**

FINDINGS.md carries the table: 66 of the 70 committed dark checks pass;
4 fail with the claim they defend and verbatim output (class b); 1 is
malformed beyond the grammar (class c) with its exact committed text; 4
pre-existing failures are separated out as not-this-tranche's. Five
ready-to-send prompts in PARKED.md. Nothing in `src/`, no committed
check text and no map document but `SCHEMA.md` was edited.

## R4 — the new baseline, with the old kept visible: **PASS**

`docs/AUDIT_BASELINES.md` now records 1212 checks over 69 documents, 6
failed on a full clone and 9 on a shallow one, itemised by class. The
superseded entry is kept struck-through with the reason it undercounted
by construction. The container's `python`/`pip` interpreter split is
recorded there too, with its measured cost (502 false failures).

## Gates

    python tools/docs_verify.py --self-test   ->  ok
    python tools/docs_verify.py --links       ->  0 dangling, 69 documents
    python tools/docs_verify.py --audit       ->  1 finding (the class-(c) malformed check)
    python -m pytest tests/ -q -n 4           ->  4412 passed, 6 skipped, 0 failed (12:03)

The full gate matches the recorded baseline (4412 passed, 0 failed)
exactly. No `tests/` file changed — the tool has no test file anywhere in
`tests/`, so its own `--self-test` is its gate, and this tranche extended
it rather than leaning on the suite.

## Frozen surfaces

Zero contact. The cone was `tools/docs_verify.py`, `docs/map/SCHEMA.md`,
`docs/AUDIT_BASELINES.md` and this tranche directory. None of the five
frozen surfaces, and no `src/` file, was opened. B1 and B2 REPORT on
frozen surfaces 3 and 5; they do not touch them.

## Verdict: PASS on all four.
