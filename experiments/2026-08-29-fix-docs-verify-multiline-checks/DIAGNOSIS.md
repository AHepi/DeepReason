# DIAGNOSIS — one regex, one line, 72 dark checks

## Primary cause

`tools/docs_verify.py:47`:

```python
_CHECK = re.compile(r"^`check:\s*(?P<cmd>.+?)`\s*$")
```

`.+?` cannot span a newline, and the pattern anchors the CLOSING
backtick with `` ` \s*$ `` on the SAME line as the opener. `parse_text`
(`tools/docs_verify.py:66-78`) walks the document one line at a time
and appends a check only when this pattern matches. There is no `else`.
A column-0 `` `check: `` opener whose closing backtick is on a later
line therefore falls through every branch of the loop and is DISCARDED
WITHOUT A RECORD — not skipped-with-a-note, not counted, not reported.

`cmd_audit` (`--audit`) iterates `doc.checks`, the same already-filtered
list, so the instrument built to find checks that cannot fail cannot
see checks that never run. `cmd_run`'s printed total (`{total} checks`)
is likewise a count of what parsed, and has been read as a count of
what the map carries.

## Census (cited, re-derived once to confirm)

72 column-0 `check:` openers with no same-line closing backtick, across
27 of the map's documents. Matches the monitor's count exactly.

| n | document |
|---|---|
| 10 | `INV-frozen-surfaces.md` |
| 8 | `INV-axiom-basis.md` |
| 7 | `INV-render-layout.md` |
| 6 | `SUB-calculus.md` |
| 5 | `INV-evidence-channels.md` |
| 4 | `CON-scheduler-ranking.md` |
| 3 | `INV-signal-contract.md`, `SEAM-evaluation-x-rules.md`, `SEAM-llm-x-verification.md` |
| 2 | `CON-packs-and-token-economy.md`, `CON-problem-layer-lifecycle.md`, `SEAM-llm-x-rules.md`, `SUB-ontology.md`, `SUB-verification.md` |
| 1 | `CON-authority.md`, `CON-criticism-source.md`, `CON-discharge-channel.md`, `CON-seats.md`, `CON-standing-and-background.md`, `REC-revise-allocation-policy.md`, `SCHEMA.md`, `SEAM-llm-x-scheduler.md`, `SUB-capabilities.md`, `SUB-evidence.md`, `SUB-manifest.md`, `SUB-periphery.md`, `SUB-scheduler.md` |

The concentration is the finding, not a detail: the heaviest offenders
are the INV- documents — the invariants and frozen surfaces — because a
claim strong enough to need a frozen surface is usually defended by a
multi-statement `python -c` block, which is exactly the shape the
parser cannot read. The map's strongest claims were its darkest.

## Shape of the 72, measured before designing the grammar

Scanning forward from each opener to the first line whose right-stripped
text ends with a backtick, stopping at the next opener:

- **70 close cleanly.** Block spans run 3-13 lines (mode 6).
- **2 do not**, and they are different from each other:
  - `SCHEMA.md:159` — PROSE. A sentence quoting `` `check: test -f
    src/deepreason/harness.py` `` as an example of a check that cannot
    fail, which happens to begin at column 0 after a line wrap. In this
    tranche's cone; rewrapped so no line begins with an opener.
  - `SEAM-llm-x-rules.md:54` — a REAL MALFORMED CHECK. A single-line
    check lost its closing backtick, and the prose paragraph that
    followed it was absorbed into the same line: the text runs
    `... = "41" What does not cross is every transport primitive — no`
    and continues into prose. Not in this tranche's cone. Reported as
    R3 class (c), parked, not repaired.

## Why this is a defect and not a limitation

`SCHEMA.md` states the map's epistemology: documents are "authenticated
by RE-DERIVATION, not by signature", because re-derivation "proves the
sentence is still true, which is the property that actually decays." A
check that is never executed authenticates nothing while looking, in the
document, exactly like one that is. The 72 are worse than absent checks:
`SCHEMA.md` itself names that failure mode — "worse than no check,
because they buy the claim false credibility."

## Secondary cause, and the half that must be fixed first

Teaching the parser the multi-line form (R2) closes today's 72. It does
not close the CLASS. As long as an unparseable opener falls through
silently, the next malformed check is dark again and nothing announces
it. R1 is therefore the load-bearing half and lands first, alone: every
column-0 opener the grammar cannot parse becomes a loud ERROR that
fails the run.
