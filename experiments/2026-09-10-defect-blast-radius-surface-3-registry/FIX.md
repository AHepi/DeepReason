# Fix: a registry entry carries every path its surface's document names, and a path ending in `/` is a directory scope

Guarantee restored: **`tools/blast_radius.py` spells each of the five frozen
surfaces with every path its owning document's own section names, so no file
inside a frozen surface can be reported CLEAR.**

## The shape decision, made before coding (the goal asked for it)

Two shapes were on the table, both named in the parked prompt: a path PREFIX
per entry, or a LIST of paths per entry. **Taken: a list, whose elements are
either an exact file path or a directory scope marked by a trailing `/`.**

Prefix alone was rejected on evidence, not taste. Surface 3 is not one prefix:
it is `invariants.py` AND `verification/`, a file and a directory that share no
useful prefix (`src/deepreason/` covers the whole package). A single-prefix
entry could only spell surface 3 by widening it to everything under
`src/deepreason/`, which trades a false CLEAR for a false CONTACT on 34
packages and destroys the verdict's meaning. A list also lets a later surface
gain a second path by adding a string, which is the modularity law's
"reachable as configuration, never by editing code" applied to a hand-
maintained registry as far as a `tools/` script can carry it.

The trailing `/` marks a directory rather than a separate `"kind"` field
because the marker is then IN the path, where a reader comparing the registry
to the document sees it — and `docs/map/INV-frozen-surfaces.md` §3 already
spells it exactly that way, `verification/`. The registry becomes copyable from
the heading, which is what the false "verbatim" comment claimed all along.

## Change sites (exhaustive)

  - `tools/blast_radius.py:110-140` — `FROZEN_SURFACES` and `FROZEN_ADJACENT`:
    each entry's `"path": "<str>"` becomes `"paths": [<str>, ...]`. Surface 3
    gains `"src/deepreason/verification/"`. No other surface's path set
    changes — the census in DIAGNOSIS.md checked all six rows and found only
    this one narrower than its document.
  - `tools/blast_radius.py:110` — the comment above the registry. It claims the
    list is "verbatim from docs/map/INV-frozen-surfaces.md" and is false
    (`docs/ERRATA.md` E88, cited not re-recorded). Replaced with what the list
    actually is: one entry per surface, carrying every path that surface's
    section names, hand-maintained, with the trailing-`/` convention stated.
  - `tools/blast_radius.py:195-221` — `_frozen_contacts`: one new
    `_surface_match` helper decides DIRECT contact per entry path — exact
    string equality for a file, `startswith` for a directory scope, which is
    boundary-safe precisely because the entry ends in `/`. The
    `SYMBOL_INDIRECT` half gains `_surface_files`, which expands a directory
    scope to the `.py` files beneath it in sorted order; one contact row per
    (surface, symbol) is still emitted, with `detail` naming the file(s) the
    symbol was found in, so the JSON row count does not inflate.
  - `tools/blast_radius.py`, module docstring "Honesty limits" — one bullet:
    the frozen-surface registry is hand-maintained like the entry-point
    registry beside it, and a surface path missing from it reads CLEAR.
  - `tools/blast_radius.py`, `_self_test()` — the fixture gains a
    directory-scoped stand-in (`src/deepreason/verification/report.py`) and two
    near-misses, and Proof 1 gains three assertions: CONTACT+DIRECT on the file
    inside the directory, and CLEAR on both near-misses. **This is the case the
    goal requires: it goes RED if a directory-scoped surface stops matching a
    file inside it, and RED the other way if the match loosens to a bare string
    prefix.**

## Map moves in the same commit

  - `docs/map/INV-frozen-surfaces.md`, the G6 subsection — one sentence stating
    that a surface spanning more than one path is spelled with all of them, and
    a new `check:` that goes red if the registry loses `verification/` or if
    the tool reports CLEAR for a path inside it.
  - `docs/map/INV-frozen-surfaces.md`, the "Granted contact, 2026-09-10" entry —
    its closing paragraph reads "Until it is fixed, this document outranks that
    tool for any path under `src/deepreason/verification/`". This fix falsifies
    that sentence; it gains a dated line saying so and naming this tranche. The
    paragraph's account of what the gate said at grant time is NOT edited — it
    records what that window was told, which stays true.
  - `docs/ERRATA.md` — a new appended entry E89. E88 says "Where corrected:
    NOWHERE YET, deliberately" and points at the parked prompt; that entry is
    not rewritten (the ledger's own rule, header lines 5-6), so the correction
    is recorded as its own dated entry citing E88.

## Regression artifact

The four RED tests from REPRO.md must invert, and three companions must stay
green (the exact-match pin, the two near-misses, and the real-tree CLEAR on
`scheduler/scheduler.py`). New conditions this fix must also be tested against,
beyond the reproduction:

  - `python tools/blast_radius.py --self-test` — the directory-scope case above.
  - A real-tree assertion that every path in the registry EXISTS, so a
    renamed surface file cannot silently empty an entry — the failure mode a
    list-shaped registry newly makes possible and the old one did not.

## Existing tests at risk

From `grep -rn "blast_radius" tests/`: three files reference the tool.

  - `tests/test_blast_radius.py::test_frozen_surface_clear_when_no_target_matches`
    — the pre-existing mutation companion pinning DIRECT contact to an EXACT
    match. **Must keep passing, unchanged.** It is the reason the directory
    marker is a trailing `/` and the match is not a bare substring test.
  - `tests/test_blast_radius.py::test_frozen_surface_direct_contact_on_target_file`
    and `::test_frozen_surface_symbol_indirect_contact_is_tier_tagged` — assert
    on `target`, `tier` and row shape for single-file surfaces. **Must keep
    passing, unchanged**: the fix must not alter what a single-file surface
    reports, which is the whole registry except surface 3.
  - `tests/test_wire_contract_id_map.py`, `tests/test_reference_menu.py` —
    reference the tool by PATH only (a menu row, a map cross-reference), never
    its registry. No fixture depends on the old shape.

No fixture is defect-dependent; nothing is updated to accommodate the fix.

## Explicitly not changed

  - **`src/deepreason/verification/` itself.** This tranche changes what the
    disclosure gate SAYS about frozen surface 3, never the surface. `tools/` is
    not a frozen surface, so no grant is required or requested.
  - **The frozen-adjacent `route_fingerprint` row.** DIAGNOSIS.md's census
    found it WIDER than its document, not narrower — the document freezes one
    function's output format, the registry names the file holding it. For a
    disclosure gate that direction over-discloses, and narrowing it to the
    symbol would demote contact from `DIRECT` to `SYMBOL_INDIRECT`, which the
    tool's own honesty limits call "plausible, not confirmed" — a weaker
    disclosure for the same edit. Left as it is, with the reason recorded so a
    later reader does not read the mismatch as an oversight.
  - **The `Owns:` header line of `docs/map/INV-frozen-surfaces.md`**, which
    lists four paths and omits both `qualification.py` and `verification/`.
    That is a different hand-maintained list with a different consumer
    (`docs_verify`'s ownership map, not this gate), and touching it here would
    widen the tranche past its one goal. PARKED.
  - **`tools/diff_budget.py`, `tools/docs_verify.py`, `tools/record_claims.py`.**
    Untouched; only the blast-radius gate carries a frozen-surface registry.

## Estimated diff

~85 lines across 2 code/doc files (`tools/blast_radius.py`,
`docs/map/INV-frozen-surfaces.md`) plus `docs/ERRATA.md`, on top of the ~70
test lines already committed in the reproduction phase. Well under 150.

## Approval gate

Class `defect` per GOAL.md; estimate under 150 lines; **no frozen surface is
touched** — `tools/` is outside all five, stated by the operator in this
tranche's brief and true of the change sites above. Proceeds to
`dr-implement-fix` without an operator grant.

---

## Amendment 1 — the diff budget gate says EXCEEDED, and this is the stop

Run before the commit, as `dr-implement-fix` step 8 requires
(`proof/DIFF_BUDGET.txt`, verbatim):

    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "9607fba6f",
     "areas": {"tools/blast_radius.py": 109,
               "docs/map/INV-frozen-surfaces.md": 63,
               "docs/ERRATA.md": 30,
               "tests/test_blast_radius.py": 108},
     "total_insertions": 310, "ceiling": 150, "verdict": "EXCEEDED"}

**The decision.** 310 insertions against a 150 ceiling, so the ceiling is
missed by more than double. Recorded here, before the commit, because the
recorded failure this gate exists to prevent is a diff going over quietly:
2026-08-05, 193 insertions against the same ceiling with no stop written
anywhere. The size is not the finding — the missing stop was.

**Where the estimate was wrong, per area.** My estimate said "~85 lines across
2 code/doc files plus `docs/ERRATA.md`, on top of the ~70 test lines already
committed", i.e. it under-counted three ways at once:

  - `tools/blast_radius.py` 109 against ~50 assumed. Changing an entry's shape
    from `"path": <str>` to `"paths": [<str>]` rewrites all six entries, and
    `git` counts a rewritten line as an insertion plus a deletion. 28 of those
    109 have a matching deletion; the true new-code figure is 81.
  - `docs/ERRATA.md` 30 against ~15 assumed. The ledger's own rule forbids
    rewriting E88, so the correction is a full new entry rather than three
    words changed in place.
  - `tests/` 108 against the ~70 I had already committed and stopped counting.
    Two real-tree tests and a six-line fixture addition landed after that count
    was written.

**Priced options.**

  A. **Accept the diff as it stands.** Cost: the tranche closes over budget on
     the record, and this amendment is what a later reader finds. Buys: the
     evidence stays whole — four regression tests, two of them against the real
     tree (the only kind that could have caught this defect), the self-test case
     the goal explicitly requires, and a ledger entry that does not lie about
     where E88 was corrected.
  B. **Trim to fit 150.** The only areas with slack are prose: the map's inline
     check block (~18 lines) and E89 (~30). Cutting both to the bone recovers
     roughly 35 and still lands near 275. Reaching 150 means deleting either
     the real-tree tests or the errata entry. Cost: the instrument goes back to
     being pinned only by fixture tests — which is precisely how this defect
     survived from the gate's construction to 2026-09-10, since a fixture
     registry was green throughout.
  C. **Split into two tranches** — mechanism now, record and map next. Cost:
     violates the map rule this repo states in the imperative ("the map moves
     in the SAME COMMIT as the code — a separate 'update docs' commit is the
     commit that gets dropped") to satisfy a line count.

**Recommendation: A, and the ceiling was the wrong instrument here.** The 150
ceiling guards against a fix quietly becoming a redesign. This one did not: the
mechanism is 81 net new lines in one file, one helper and one comparison, and
the census in DIAGNOSIS.md checked all six registry rows so no surface was
widened beyond the one the finding names. The other 229 lines are test, map and
ledger — the three things this repo's rules require to move WITH a fix, and the
three the ceiling counts as if they were risk. Recorded as EXCEEDED rather than
argued away; the operator decides whether to trim.
