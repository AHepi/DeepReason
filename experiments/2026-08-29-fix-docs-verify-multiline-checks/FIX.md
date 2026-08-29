# FIX — a total grammar, and no silent branch

Designed against the measured shapes of the 72 (DIAGNOSIS.md
"Shape of the 72"), before the code was written.

## R1 — the silent branch closes (its own commit, first)

`parse_text` grows the `else` it never had. `_CHECK` keeps deciding
what RUNS; a new `_CHECK_OPEN` decides what must be ACCOUNTED FOR. Any
column-0 `` `check: `` the running grammar cannot read is appended to
`Doc.errors`, and:

- `cmd_run` turns every `Doc.errors` entry into a FAIL line and a
  non-zero exit, before a single check is dispatched;
- `cmd_audit` reports them as findings — a check that cannot RUN is the
  limit case of the thing `--audit` exists to catch, a check that
  cannot FAIL;
- `--self-test` pins both directions: an indented example still parses
  to nothing at all (no check, no error), an unclosed column-0 opener
  parses to no check and exactly one error.

R1 is designed to hold whatever R2 decides. It says "an opener the
grammar cannot read is loud"; it does not say what the grammar is.
Widening the grammar in R2 shrinks the error set; it cannot re-open the
silent branch, because there is no longer a path through the loop that
drops an opener.

Cost, stated plainly: between R1 and R2 the real map is RED with 72
errors. That is the honest state of the tree — those 72 checks have
never run — and R2 lands next.

## R2 — the multi-line form

    A column-0 `check: opener begins a check block.
      - If the line ends with a backtick, the block is that line.
      - Otherwise the block continues, and closes at the first later
        line whose right-stripped text ends with a backtick.
      - An opener that reaches EOF, or another column-0 opener, without
        closing is an ERROR (R1).

The command is the block's text with the opening `` `check: `` and the
closing backtick removed, newlines PRESERVED — the 70 committed blocks
are `python -c "..."` bodies whose statements are newline-separated, so
joining them onto one line would change what they mean. `subprocess.run
(..., shell=True)` takes a multi-line string directly.

**The grammar is TOTAL, deliberately.** There is no third disposition:
a column-0 opener is a check or an error, never prose. Two consequences,
both measured against the committed tree rather than assumed:

1. `SCHEMA.md:159` — a sentence that quotes `` `check: test -f
   src/deepreason/harness.py` `` as an example of a check that cannot
   fail, and that a line wrap happened to push to column 0. Rewrapped
   in the same commit so no line begins with an opener. This is the
   price of totality and it is one line.
2. `SEAM-llm-x-rules.md:54` — a real malformed check, and totality is
   what finds it. Not repaired here (out of cone); reported as R3
   class (c).

A "closed span followed by prose" carve-out was considered and
REJECTED. It would silently ignore `` `check: foo` bar `` at column 0,
which is precisely the silence this tranche exists to remove: the whole
value of R1 is that the parser has no disposition that discards an
opener without saying so.

`_fingerprint` needs no change — `_PATHISH` already scans the whole
command string, so a multi-line command's paths are found the same way.
Failure and slow-check output render continuation lines indented, so a
13-line check does not shred the report.

`--audit` needs no change beyond R1's: `_VACUOUS` anchors at `^\s*` of
the joined command, so a multi-line block whose first statement is
`true` is flagged exactly as a single-line one is. Pinned by a new
`--self-test` case rather than trusted.

## What this fix does NOT do

It does not rewrite the 72 across 27 documents. Four fix windows are in
flight and each will add checks to map documents; a 27-document reflow
would collide with all of them. The tool learns the shape the documents
already have.

It repairs no claim and no `src/` file. R3 measures; it does not mend.
