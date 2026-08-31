# docs_verify at the integration boundary — every failure disposed

FULL mode, not `--fast`, run ALONE on an idle 4-CPU box (never concurrently
with the pytest gate — both fan out workers and the contention manufactures
failures).

## Run 1 — `10 failed`, against a recorded baseline of 5 or 6

`docs_verify [full]: 71 documents, 1290 checks, 4 workers` → **10 failed.**

The corpus is bigger than the baseline's (`1250 checks over 70 documents`,
`docs/AUDIT_BASELINES.md`) because lane B's `CON-successor-questions.md` is the
71st document and this integration added checks to it and to four others.

**FIVE were baseline**, and this container reports
`git rev-parse --is-shallow-repository` → `true`, which is what puts the three
`CON-run-identity.md` rows on the list:

| row | class | disposition |
|---|---|---|
| `SEAM-llm-x-rules.md:54` | check malformed (a lost backtick) | baseline, parked P3 |
| `INV-frozen-surfaces.md:181` | claim rotted (the `transport_failure` census) | baseline, parked P-D3 |
| `CON-run-identity.md:211`, `:213`, `:215` | git-history checks on a shallow clone | baseline; all three pass after `--unshallow` |

`SUB-application.md:421`, the CONTAINER-CONDITIONAL timing row the baseline
allows, did **not** trip in either run.

**FIVE were a delta, i.e. findings.** Four were caused by this integration and
are REPAIRED below; the fifth is a tripwire working correctly and is explained
rather than repaired.

### Finding 1 — `INV-frozen-surfaces.md:1026`: a count pin, dated by its count

The check asserted `len(pins) == 2`, where `pins` is every check in that file
containing the live qualification subject digest. The Q1 grant block added a
THIRD pin **of the same live value** — an exactly-correct addition — and turned
it red.

This is `docs/ERRATA.md` E65's own lesson landing on the same day it was
written: an entry that asserts a COUNT is dated by the count. Repaired by
asserting the two PROPERTIES the surrounding paragraph actually states, neither
of which rots when a grant adds a pin:

- the value is pinned **at least twice** (a positive anchor, so the check
  cannot pass by there being no pins at all), and
- the documented PREDECESSOR digest `b9038b84…` survives in **no** check in
  the file — which is rule one of that Traps entry (*"when a granted contact
  moves a digest, grep THIS FILE for the old value"*) encoded, and the clause
  that would have caught the two-day staleness the entry records.

The predecessor is spelled in two halves inside the check, and that is not
cosmetic: written whole, the check's own text contains it and the scan matches
ITSELF. The first version of this repair failed exactly that way, in one run,
and is recorded here rather than quietly re-written.

### Findings 2, 3, 4 — three word-mention censuses moved by ONE new file

`SEAM-harness-x-workflow.md:43` (`harness` + `workflow`, `-eq 59`),
`SEAM-scratch-x-workflow.md:44` (`scratch` + `workflow`, `-eq 48`) and
`CON-successor-questions.md:305`, which embeds both counts.

Cause: `src/deepreason/aftercycle.py`, the new hook point, NAMES the six
deciding packages — `workflow` and `workflows` among them — in a docstring
explaining why the scheduler may not name the successor channel. It imports
nothing from either side. So one file joined three censuses **without adding a
single dependency**, which is worth stating because the clauses beside these
counts measure edges from the import graph while the counts themselves measure
word mentions.

Repaired by updating the counts in the same commit as the code (59→60, 48→49),
and by saying in each document's prose that the newest member is a PROSE
mention with no edge — so the number is not read as coupling that is not there.

Not writing around the check: rewording the docstring to dodge the word would
have made the census pass while the file still mentioned the concept, which is
the worse of the two.

**A pre-existing disagreement found on the way, and NOT caused by this
tranche:** `SEAM-scratch-x-workflow.md`'s prose said *"Forty-seven files"*
while its own check on the next line asserted **48**. Corrected to 49 with the
disagreement stated, rather than silently harmonised.

### Finding 5 — `INV-frozen-surfaces.md:297`: the tripwire is RIGHT, and stays red

```
! git diff --name-only origin/main...HEAD | grep -qE "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"
```

It fails because this branch **does** change `run_manifest.py` — the Q1 granted
contact. That is the check doing its job, not a defect in it, and it must NOT
be weakened: a tripwire that a grant can switch off protects nothing.

Three things make this dispositive rather than convenient:

1. The contact is **granted, in writing, before the edit** — `FIX.md` at
   `907d260b9`, with `blast_radius.py`'s own CONTACT verdict pasted and every
   row disposed — and recorded as the sixth granted contact in the same
   document the tripwire lives in.
2. What the tripwire exists to prevent did **not** happen: the qualification
   subject digest and all six `source_config_hash` values are byte-identical
   (`q1_grant_measurements.txt`), so no home owes a battery and no committed
   root moves.
3. It is **branch-relative and self-clearing**. The check compares
   `origin/main...HEAD`; once this branch is on `main`, the diff is empty and
   the check is green with no edit at all. Any tranche taking a granted
   surface-4 contact sees this row red on its own branch — the five prior
   grants did too, and were green by the time anyone ran the sweep against
   `main`.

**Recorded as an expected, explained failure of an integration branch, not as a
baseline entry.** It does not belong in `docs/AUDIT_BASELINES.md`, because on
`main` it passes.

## Run 2 — after the four repairs

See `docs_verify_run2.txt`, appended below by the same command.
