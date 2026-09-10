# Verification

Verdict: **PASS (offline; no live proof owed)**

The goal's success criterion is four commands. All four are pasted below from
`proof/CRITERION.txt`, `proof/FULL_GATE.txt` and `proof/DOCS_VERIFY.txt`, run on
the committed tree.

## 1. The criterion command

    $ python tools/blast_radius.py --files src/deepreason/verification/report.py
    "frozen_surface_contacts": [
      {"surface": "replay-validation record formats (invariants.py, verification/)",
       "tier": "DIRECT",
       "target": "src/deepreason/verification/report.py",
       "detail": "target file is inside surface path src/deepreason/verification/"}
    ]
    "frozen_surface_verdict": "CONTACT"
    disclosure_summary: "This change touches 1 of the five frozen surfaces ..."

Before the fix the same command returned `[]`, `CLEAR`, and "This change touches
none of the five frozen surfaces" (`proof/CENSUS_BEFORE.txt`).

## 2. The self-test, with the case the goal requires

    $ python tools/blast_radius.py --self-test
    SELF-TEST PASS

The new Proof 1b declares a directory-scoped surface in the fixture and asserts
CONTACT on a file beneath it plus CLEAR on two near-misses; Proof 1c asserts
every registry path exists in the real tree. Mutation-proved in BOTH directions
(`proof/MUTATION_PROOF.txt`), which is what the goal asked for:

  - drop `verification/` from surface 3 -> self-test exit 1, `assert
    data["frozen_surface_verdict"] == "CONTACT"` fails with `CLEAR`; the test
    file goes to 5 failed.
  - loosen the directory match to a bare string prefix -> self-test exit 1 on
    the near-miss `verification_notes.py`, which the mutation wrongly flags as
    `DIRECT` contact; the test file goes to 2 failed.
  - restored -> `SELF-TEST PASS`, 27 passed.

## 3. The ring

    $ python -m pytest tests/test_blast_radius.py -q
    27 passed in 7.44s

The four tests that were RED before the fix (`proof/repro_red.txt`: 4 failed,
23 passed) are green, and the three companions that had to STAY green did:
the pre-existing exact-match pin, the two near-misses, and the real-tree CLEAR
on `scheduler/scheduler.py`.

## 4. The gate

    $ pytest tests/ -q -n 4
    5231 passed, 6 skipped in 1806.42s (0:30:06)

**0 failed.** No assertion was weakened and no fixture was updated: FIX.md
predicted none would need to be, and none did.

## 5. `docs_verify` — 10 failed, and none of them this tranche's

    $ python tools/docs_verify.py
    docs_verify: 10 failed

`docs/AUDIT_BASELINES.md` predicts 5 or 6 on a shallow clone, which this
container is (`git rev-parse --is-shallow-repository` -> `true`). Six rows
match the recorded baseline; four are a delta. Every one was probed
individually rather than waved through, and the probes are in this file's
sibling `PARKED.md` P2. The dispositions:

| where | class | probe |
|---|---|---|
| `SEAM-llm-x-rules.md:54` | baseline (malformed check) | listed in AUDIT_BASELINES |
| `CON-run-identity.md:211`, `:213`, `:215` | baseline (shallow clone) | `is-shallow-repository` -> `true` |
| `INV-frozen-surfaces.md:206` | baseline (`transport_failure` census, listed at `:181`; anchored by content per `docs/ERRATA.md` E67) | same command, same claim |
| `INV-frozen-surfaces.md:1175` | baseline, container-conditional | `git rev-parse --verify origin/claude/deepreason-p-s1-commitments-wowcib` -> "Needed a single revision" |
| `CON-successor-questions.md:305`, `SEAM-scratch-x-workflow.md:51` | **delta** — one rotted count, pinned in two documents | the census returns **51**, both checks assert 50 |
| `INV-frozen-surfaces.md:1569` | **delta** — missing evidence | the run root the check reads is not in this checkout (`ls` -> No such file) |
| `CON-run-identity.md:313` | **delta** — instrument cost, claim intact | TIMEOUT at the 300 s ceiling under load; run ALONE on a quiet box it **passes in 356 s**, 9 passed |

Shown, not asserted: `git diff <base> --name-only` lists **no file under
`src/`**. The two count checks census `.py` files under `src/deepreason`; the
record-claims check reads a run root; the timeout is the instrument's own
ceiling. Nothing among the ten reads `tools/blast_radius.py`, `docs/ERRATA.md`,
or any part of `docs/map/INV-frozen-surfaces.md` this tranche edited.

The three checks this tranche ADDED were run by their own commands and pass
(the G6 answer check, `--self-test`, and the Traps grep), as did the two
pre-existing checks that assert exact contact-row lists — `:326`
(`--files invariants.py` yields exactly one row) and `:471` (four files yield
exactly the `run_manifest.py` row). Those two are the ones a careless widening
would have broken, and they are unmoved.

Historical roots re-checked: **none, and none are owed.** This tranche changed
an instrument under `tools/` that reads the source tree, not a reader of the
append-only record. No `verify_root` output, no record format, no digest and no
committed root is touched by the diff.

Live attempt: **none, and none is owed.** GOAL.md demands no live proof; the
whole subject is a static analysis over the tree.

## Residue (honest)

  - **The diff budget says EXCEEDED and stands recorded as such.** 310
    insertions against the 150 ceiling, accounted per area at FIX.md
    Amendment 1 with three options priced. The recommendation there is to
    accept, on the ground that 81 lines are net new mechanism and the other 229
    are test, map and ledger — but that is a recommendation, and the operator
    has not ruled. Until they do, this tranche is over budget on the record.
  - **The five surfaces are still named by three hand-maintained lists, and
    only one of them is now checked.** This fix makes the blast-radius registry
    right and pins it with a check on the tool's ANSWER. The map document's own
    `Owns:` header still names four paths for five surfaces (missing
    `qualification.py` and `verification/`), and nothing goes red when the
    three lists disagree. PARKED P1 — the same failure SHAPE, a different
    consumer.
  - **`docs_verify` is four rows above its baseline** for reasons this tranche
    did not cause and did not fix. PARKED P2.
  - **What the new checks do NOT prove.** They prove the registry spells
    surface 3 correctly and that a directory scope matches on a path boundary.
    They do not prove the registry is COMPLETE against the document — that
    would need the registry derived from the document, which is exactly the
    parked P1 question. A sixth surface added to the document tomorrow, and not
    to the registry, still reads CLEAR and no check goes red. The honesty limit
    added to the module docstring says this in the tool's own voice rather than
    leaving it to be discovered.
  - **`Verified-at:` on `docs/map/INV-frozen-surfaces.md` was NOT advanced.**
    Its checks were re-run this tranche, but the stamp names a commit hash and
    the run happened on a working tree whose commit did not yet exist. A stale
    stamp is honest; a stamp naming a commit the checks were not run at is not.

Errata: **E89 added** (`docs/ERRATA.md`), recording where E88 was corrected.
E88 itself is not rewritten — that ledger's header forbids it ("Entries are
appended, never rewritten"). E88 was cited, not re-recorded, per the tranche
brief.
