# Results — the blast-radius gate's frozen-surface registry

## 2026-09-10 — the gate said CLEAR for a file inside a frozen surface

**What was observed.** `python tools/blast_radius.py --files
src/deepreason/verification/report.py` returned `frozen_surface_verdict: CLEAR`
and, in words, "This change touches none of the five frozen surfaces" — for a
module inside frozen surface 3. Not an error, not a crash: exit 0, well-formed
JSON, a clean wrong answer. All twelve modules under
`src/deepreason/verification/` behaved the same way
(`proof/CENSUS_BEFORE.txt`).

Found the day before by hand, during the defended-trial authority census, whose
own grant request had to disclose the gap the gate could not
(`experiments/2026-09-10-defect-defended-trial-authority-census/` PARKED.md P2;
`docs/ERRATA.md` E88).

**What was fixed.** The registry stored ONE exact-match path per surface, and
`_frozen_contacts` tested set membership. Surface 3's owning document names two
things, one of them a directory: "Replay-validation record formats —
`invariants.py`, `verification/`". A one-string schema had nowhere to put the
second, and an equality test could not have matched a directory against a file
even if it had — so the narrowing was structural, not a typo. Each entry now
carries a list of paths; a trailing `/` marks a directory scope matched on a
path boundary.

**What the record now shows.** All twelve modules under `verification/` report
`CONTACT` with a `DIRECT` row, while `scheduler/scheduler.py`, `rules/conj.py`
and `config.py` stay `CLEAR` — the widening is the surface, not the tree
(`proof/CENSUS_AFTER.txt` against `proof/CENSUS_BEFORE.txt`). Four regression
tests were run RED first (`proof/repro_red.txt`), two of them against the real
tree rather than a fixture, because a fixture-only registry test was green for
the entire life of this defect. The self-test case the goal required is
mutation-proved in both directions (`proof/MUTATION_PROOF.txt`). Full gate:
5231 passed, 6 skipped, 0 failed.

**The census the goal demanded, and its one surprise.** All six registry rows
were compared against their sections before anything was widened. Surfaces 1,
2, 4 and 5 matched exactly. The frozen-ADJACENT `route_fingerprint` row did
NOT match — but in the other direction: the registry names the whole file where
the document freezes one function's output format. It was left alone, and the
reason is now a comment above the entry rather than a silence: for a disclosure
gate, over-disclosing is the safe direction, and narrowing it to the symbol
would demote `DIRECT` contact to the `SYMBOL_INDIRECT` tier the tool's own
honesty limits call plausible rather than confirmed — a weaker disclosure for
the same edit.

## The residue — what remains unproven

**The fix makes one list right; it does not make the lists agree.** Three
hand-maintained lists name the five frozen surfaces: this registry, the
document's section headings, and the document's own `Owns:` header. The header
names FOUR paths for five surfaces, omitting `qualification.py` and
`verification/` — the same failure shape, found while auditing for exactly this
and parked rather than folded in (PARKED P1). Nothing goes red when the three
disagree. A sixth surface added to the document tomorrow and not to the
registry still reads CLEAR; the new checks would not catch it, and the module
docstring now says so in the tool's own voice.

**The tranche is over its diff budget on the record.** `tools/diff_budget.py`
returned `EXCEEDED` — 310 insertions against 150 — and it is recorded as a stop
at FIX.md Amendment 1 with three options priced, not argued away. 81 of those
lines are net new mechanism; the rest are test, map and ledger. Accepted does
not mean true, and over budget does not mean wrong: the operator rules.

**`docs_verify` is four rows above its baseline for reasons that predate this
tranche.** Ten failed where the baseline predicts five or six. Six match; four
are a delta, each probed individually and each shown independent of a diff that
touches no file under `src/` (PARKED P2). One of the four is worth naming here
because it is the kind of thing that gets mistaken for a code failure: a check
that TIMES OUT at `docs_verify`'s own 300-second ceiling and passes in 356
seconds when run alone. The claim is true; the check is too expensive. That has
a precedent to copy (`docs/ERRATA.md` E67).
