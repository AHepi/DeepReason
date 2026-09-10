# Diagnosis: the registry stores one exact-match path per surface, and `_frozen_contacts` tests membership, so a surface the owning document spells as a DIRECTORY can only ever match the one file that was typed into it

## THE STOP, CLASSIFIED

There is no run root, no `root-no-log` run directory and no home: all three of
the stop report's source kinds are ABSENT. The failure is in an instrument
under `tools/`, which never opens a run. In place of section 4, the
instrument's own typed envelope, verbatim from
`proof/CENSUS_BEFORE.txt` (re-derived this phase on the pre-fix tree, and
identical to the run recorded at
`experiments/2026-09-10-defect-defended-trial-authority-census/proof/BLAST_RADIUS.txt`):

    $ python tools/blast_radius.py --files src/deepreason/verification/report.py
    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "disclosure_summary": "This change touches none of the five frozen surfaces.
                           1 test file(s) and 1 map document(s) assert on the
                           touched targets today."
    "frozen_surface_verdict": "CLEAR"

Exit class 0 — the instrument did not fail. It emitted a well-formed
`BLAST_RADIUS_RESULT_V1` and asserted, in typed fields and in words, the
opposite of what its owning document says. That is the defect: a wrong answer
delivered as a clean one.

Primary cause: `FROZEN_SURFACES` (`tools/blast_radius.py:110-132`) stores each
surface as a dict carrying exactly one `"path"` string, and `_frozen_contacts`
(`tools/blast_radius.py:195-207`) decides DIRECT contact by
`if entry["path"] in normed_files` — set membership, an exact string equality
test over the declared target files. Surface 3's owning document spells that
surface as two things, one of them a directory ("Replay-validation record
formats — `invariants.py`, `verification/`"), and the registry can hold only the
first, because a one-string-per-surface schema has nowhere to put the second and
an equality test could not match a directory against a file even if it did. So
the narrowing is structural, not a typo: the data shape and the comparison
operator each independently prevent surface 3 from being spelled the way its
document spells it. The comment above the registry asserts the list is
"verbatim from docs/map/INV-frozen-surfaces.md"; `docs/ERRATA.md` E88 already
records that this assertion is false, and states that until it is fixed the
document outranks the tool for any path under `src/deepreason/verification/`.

Evidence:

  - `proof/CENSUS_BEFORE.txt`, per-module census -> ALL TWELVE modules under
    `src/deepreason/verification/` return `frozen_surface_verdict: CLEAR`,
    including `report.py`, which took a granted contact on this very surface
    on 2026-09-10.
  - `proof/CENSUS_BEFORE.txt`, control run -> naming the five registry paths
    plus the frozen-adjacent path returns all six as `DIRECT` and the verdict
    as `CONTACT`. The computation, the tiering and the verdict scalar are
    sound; only the registry's contents are wrong. This is what rules out a
    fault in `_frozen_contacts`' logic.
  - `docs/map/INV-frozen-surfaces.md:72` -> the §3 heading, "Replay-validation
    record formats — `invariants.py`, `verification/`".
  - `docs/map/INV-frozen-surfaces.md:70` -> surface 2's own granted-contact
    check line ends `&& ! grep -rq "section-plan" src/deepreason/verification/`
    — the document treating `verification/` as a directory-scoped frozen
    surface in an executable check, not only in a heading.
  - CLAUDE.md, third-lane section -> "FIVE surfaces; they span seven paths,
    because surface 3 covers both `invariants.py` and `verification/`".
  - `docs/ERRATA.md` E88 -> the false "verbatim" comment, already recorded;
    cited, not re-recorded.

## Census of every other surface against its own document spelling

Run this phase, because the goal forbids widening only the surface the finding
names. Each row compares the registry entry to the owning document's heading
and to any path the section's own `check:` lines exercise.

| # | Document spells | Registry holds | Verdict |
|---|---|---|---|
| 1 | `capabilities/state.py` | `src/deepreason/capabilities/state.py` | matches |
| 2 | `harness.py` | `src/deepreason/harness.py` | matches |
| 3 | `invariants.py`, `verification/` | `src/deepreason/invariants.py` only | **NARROWER — the defect** |
| 4 | `run_manifest.py` | `src/deepreason/run_manifest.py` | matches |
| 5 | `qualification.py` | `src/deepreason/qualification.py` | matches |
| adj | `route_fingerprint` in `llm/firewall.py` | the whole file `src/deepreason/llm/firewall.py` | **WIDER, and deliberately left so** |

On the frozen-adjacent row, stated because the goal asked the question
directly: the registry is not narrower than its document, it is wider. The
document freezes one function's output format; the registry names the file that
holds it. For a DISCLOSURE gate that direction is the safe one — it
over-discloses, and a reader who is told to look sees the section that scopes
the freeze to `route_fingerprint`. Narrowing it to the function would move
`route_fingerprint` from the file registry into the symbol path, where contact
is only ever `SYMBOL_INDIRECT` and the tool's own honesty limits call it
"plausible, not confirmed" — a weaker disclosure for the same edit. Not
changed, and the reason is recorded so a later reader does not read the
mismatch as an oversight.

Implicated code:
  - `tools/blast_radius.py:110-132` — `FROZEN_SURFACES`, and the comment above it
  - `tools/blast_radius.py:195-207` — `_frozen_contacts`, the `in normed_files` test
  - `tools/blast_radius.py:681-712` — the self-test's fixture layout and Proof 1,
    which exercise only single-file surfaces and so cannot go red on this

Falsifiable prediction: on the pre-fix tree, a test asserting that
`--files src/deepreason/verification/report.py` yields
`frozen_surface_verdict == "CONTACT"` fails, and fails specifically with
`CLEAR` and an empty `frozen_surface_contacts` list — not with an error, not
with a `SYMBOL_INDIRECT` row. And a self-test case that declares a
directory-scoped surface in the fixture and names a file inside it fails the
same way. Both must go RED before the fix and GREEN after.

Ruled out: that `_frozen_contacts` mis-normalizes paths and drops a match it was
given. Checked by the control run above — every path actually present in the
registry returns `DIRECT`, and `src/deepreason/invariants.py` among them. The
computation returns exactly what the registry contains; nothing is lost between
the two.
