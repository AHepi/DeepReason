# RESULTS — docs_verify multi-line checks

## 2026-08-29 — the map's 72 dark checks, executed

**What the record shows.** `tools/docs_verify.py` required a check's
opening and closing backtick on the same line, and its parse loop had no
`else`: a column-0 `` `check: `` opener it could not read was discarded
with no output. 72 such openers stood across 27 map documents,
concentrated in the INV- documents (`INV-frozen-surfaces.md` 10,
`INV-axiom-basis.md` 8, `INV-render-layout.md` 7) because a claim strong
enough to need an invariant is usually defended by a multi-statement
`python -c` block — exactly the shape a one-line regex cannot hold. The
map's strongest claims were its darkest.

Two commits. The first closes the silence: any opener the grammar cannot
read is a loud `unparseable check` failure. The second teaches the
grammar the multi-line form, so the 70 well-formed dark checks run AS
WRITTEN, with newlines preserved. The grammar is deliberately TOTAL — at
column 0, `check:` opens a check or an error, never prose — because the
prose carve-out that reads better is the same carve-out that produced
this defect. Its price was one wrapped sentence in `SCHEMA.md`; its
benefit was finding a real malformed check nothing else could see.

**The first honest count.** 1141 checks became 1212, and 72 unaccounted
openers became 0. On a full clone: 6 failed. **66 of the 70 checks that
had never once run PASS** — including 8 of 10 in `INV-frozen-surfaces.md`
and all of `INV-axiom-basis.md`, `INV-render-layout.md`, `SUB-calculus.md`
and `INV-evidence-channels.md`. The unproven claims were, in the main,
true.

Four had rotted, and the sharpest is B1: `invariants.py:21` carries a
module-level `from deepreason.llm.firewall import route_fingerprint`,
while `SEAM-llm-x-verification.md` states there is "no import in either
direction". Frozen surface 3 importing the frozen-adjacent symbol, denied
by the document that governs the pair. B2 is a stale qualification-digest
pin that disagrees with the SAME document's other pin of the same
expression — neither could contradict the other while both were dark. B3
and B4 are checks that cannot reach their claims. C1 is a check whose
closing backtick was lost, merging it with the paragraph after it; the
document's own prose says that check exists because its count had already
drifted once, so the drift it was written to stop is the drift it has
been unable to stop since.

**The residue — what remains unproven.** That the 66 newly-green checks
were green all along: they were dark, and a claim that rotted and was
repaired by an unrelated change looks identical from here. The record
starts today. That the map is sound: nine in ten prose lines in these
documents carry no check at all, by design (`SCHEMA.md`), and this
instrument has never been able to see them. And which of B2's three
digest values is historically correct — this tranche shows only that the
pin at `:657` disagrees with the tree and with `:533`.

Accepted does not mean true. What is established is narrower and worth
stating exactly: as of 2026-08-29, 1206 of the map's 1212 executable
claims re-derive against the tree, 5 do not, and no claim can again carry
a check that has never run without the instrument saying so.

Findings: FINDINGS.md. Prompts for the five: PARKED.md. Proof: VERIFY.md.
