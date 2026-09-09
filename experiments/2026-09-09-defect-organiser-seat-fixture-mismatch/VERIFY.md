# Verify: PASS

Date: 2026-09-09. Fix commit `0b10b2f2c`. Branch
`claude/organiser-seat-fixture-mismatch-12ttru`, based on `origin/main`
`d7c87473e`.

## The goal's success criterion, met

    $ python -m pytest tests/test_organiser_seat.py -q
    ............                                                             [100%]
    12 passed in 4.67s

    $ python -m pytest tests/ -q -n 4
    5169 passed, 6 skipped in 1204.93s (0:20:04)

Zero failed. The three tests that were red on `origin/main` are green, the
nine that were green stayed green, and nothing else in the suite moved.

## No assertion was weakened

Each of the three tests now compares against a committed record instead of a
typed copy, and each gained assertions rather than losing them:

| test | before | after |
|---|---|---|
| `..._byte_for_byte` | bytes vs. three literals | bytes vs. `ATTACHMENT.sha256` AND `CONVERSION.json`'s own per-file `sha256`, plus the manifest must name exactly the three attached files |
| `test_admission_mints_one_block_per_room_record` | three literal counts | per-file count vs. the converter's room-record count plus its one preamble, AND the same numbers in `proof/DRY_ATTACH.txt`, AND the dossier's total |
| `..._shows_the_whole_room_and_the_directive` | literal split, literal `+62` | split vs. the committed render proof, shown total vs. the proof AND the 32-block cap, withheld tied to `len(dossier.blocks) - len(shown)` before the notice string is built from it |

No `>=`, no `in` where an `==` stood, no `approx`, nothing deleted.

## Mutation proof — the new assertions can still fail

Four mutations, each applied to the tree, measured, and reverted
(`git status` clean afterwards; only the test file remained modified):

| mutation | result |
|---|---|
| `evidence/render.py:196` legend cap `32 -> 31` | 1 failed (`..._shows_the_whole_room...`) |
| `admission/parse.py:563` `blocks.extend(source_blocks[1:])` — one block per source dropped | 2 failed (admission and the brief) |
| `admission/parse.py:577` dossier no longer sorted by content id | 6 failed |
| one space appended to `attachment/03-objections.txt`, manifest untouched | 2 failed (the digest test and the brief) |

The first three are the properties the literals were there to guard — the cap,
one-block-per-paragraph, and hash ordering. The fourth is the property the
digest pins were there to guard. All four still bite.

## The map

`docs/map/INV-seat-section-plugins.md` — the document that owns the organiser
shell and carries `check: python -m pytest tests/test_organiser_seat.py -q` —
gains a `Traps` entry naming this incident, the commit that moved the
attachment (`8a579f1e6`), the amendment that designed the move, and the rule it
leaves: a data file inside `experiments/` that a test reads is a test input, so
a window that rewrites it owes `tests/` a run even when `src/` is
byte-untouched. No `Traps` entry was deleted. The document's `Verified-at:`
stamp is left where it was: this tranche changed no file the document `Owns:`,
and a stamp that claims more than the commit did is worse than a stale one.

## docs_verify — 7 failed, all seven pre-existing

    $ python tools/docs_verify.py
    docs_verify [full]: 82 documents, 1433 checks, 4 workers
    ... docs_verify: 7 failed

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 1 finding(s)      # SEAM-llm-x-rules.md:54, the
                                           # recorded baseline row (parked P3)
    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 82 document(s)

Every one of the seven was re-run with this tranche's change STASHED, at
`origin/main`'s exact state, and every one failed identically. None is in
`INV-seat-section-plugins.md`, and none reads `tests/` or the attachment.
By class: three are shallow-clone git-history rows in `CON-run-identity.md`
(`1637e808` and `f304fec1` are not revisions in this clone); `SEAM-llm-x-rules.md:54`
is the parked malformed check; `INV-frozen-surfaces.md:206` is the parked
rotted `transport_failure` census; `INV-frozen-surfaces.md:909` reads a branch
this clone has not fetched; `INV-frozen-surfaces.md:1274` points at a run root
that is not committed (`record_claims: … no run-status.json (not a run root)`).

`docs/AUDIT_BASELINES.md` records 5 or 6 on this container as of 2026-08-30/31.
The last two rows postdate that entry. The delta is a finding for another
tranche, not this one — PARKED P1 and P2.

**Procedural correction, recorded because the rule exists and I broke it.**
The first `docs_verify` run overlapped the full gate, which
`docs/AUDIT_BASELINES.md` and `dr-drive-harness` §5b forbid. It was re-run
serially on an idle box afterwards; both runs reported the same seven rows,
and the serial run is the one quoted above. The concurrent reading is not
admissible and is not used.

## No live run

The goal names no live proof and none is owed: the defect and the fix are both
offline, and the tranche touches no `src/` file. The organiser tranche's own
live arm is a separate matter, still unlaunched for want of a credential
(that tranche's RESULTS.md, third segment).

## Residue — what this does NOT prove

- It does not prove the attachment is the right room, or that the organiser
  arm will produce anything. It proves the tests read the attachment that is
  committed, whatever that attachment says.
- It does not close the class of defect. Other test files may read data under
  `experiments/`; this tranche looked at one file and did not census the rest
  (PARKED P3).
- The 32-block cap and the hash ordering remain what they were: PARKED P2 of
  the organiser tranche, untouched here.
