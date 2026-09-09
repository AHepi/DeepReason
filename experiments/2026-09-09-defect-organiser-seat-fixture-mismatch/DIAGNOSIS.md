# Diagnosis: the tests pin bytes the attachment's own manifest no longer carries

Date: 2026-09-09. Primary cause, one sentence:
**`tests/test_organiser_seat.py` carries three sets of hand-copied literals
describing the committed attachment — its three sha256 digests, its per-file
block counts, and its rendered legend split — and the organiser tranche's
SECOND launch window rewrote the attachment on 2026-09-06 (commit `8a579f1e6`)
without moving those literals, because that window's own scope rule forbade it
from touching `tests/`.**

## The evidence, in the order it decides the question

### 1. The three failures, reproduced

`python -m pytest tests/test_organiser_seat.py -q` on this branch's base
(`origin/main` `d7c87473e`): `3 failed, 9 passed in 5.52s`.

| test | pinned | measured |
|---|---|---|
| `test_the_fixture_is_the_committed_attachment_byte_for_byte` | `PINNED["01-conjectures.txt"] = feb1dc48…` | `3e41fbaf…` |
| `test_admission_mints_one_block_per_room_record` | 12 / 46 / 36 blocks | 13 / 47 / 37 |
| `test_the_organiser_brief_shows_the_whole_room_and_the_directive` | legend 7 / 13 / 12, withheld `+62` | 4 / 17 / 11, withheld `+65` |

### 2. The attachment's own manifest agrees with the measurement, not the test

`experiments/2026-09-06-change-writers-room-organiser-testing/attachment/ATTACHMENT.sha256`
holds `3e41fbaf… 01-conjectures.txt`, `27f092c1… 02-proposals.txt`,
`8fde979b… 03-objections.txt`, and `sha256sum -c` on the committed files
passes. `attachment/CONVERSION.json` records `records` 12 / 46 / 36 per file
and a `preamble` entry per file. `proof/DRY_ATTACH.txt` — the tranche's own
committed admission proof — records `sources 3 blocks 97 refusals 0`,
`blocks_by_file` 13 / 47 / 37, `legend_shown_by_file` 4 / 17 / 11 and
`legend_withheld 65`. Every number the test rejects is a number the attachment
publishes about itself.

### 3. The rewrite was deliberate, predicted in writing, and entitled

`git log --oneline -- .../attachment/` shows exactly two commits: `9554abfe4`
(the converter and the attachment it wrote) and `8a579f1e6` (the second launch
window). `8a579f1e6`'s message states the change and its consequence before
any live call: "94 room records verbatim, plus three preambles, so admission
mints 97 blocks and the legend's hash-ordered 32 is redrawn to 4 conjectures /
17 proposals / 11 objections."

SPEC Amendment 4 of that tranche designs it (R39, R40, A16) and states the
same consequence under "Measured consequence, disclosed before the launch":
"4 conjectures / 17 proposals / 11 objections, against 7 / 13 / 12 before".
RESULTS.md's third segment §2 reports it as measured. So the moved bytes are
not damage — they are the change that window shipped.

### 4. Why the tests were not moved with them

The same window's scope rule, in its own commit message and in S39's
acceptance check: "`git diff --stat <window base>..HEAD -- src tests mini
docs` empty" — `tests/` was explicitly frozen for that window, on the ground
that no `src/` file moved and "no gate is owed". The gate WAS owed, because
`tests/test_organiser_seat.py` reads the attachment as its fixture. Nothing
in the tranche noticed that a data file inside `experiments/` is an input to
a test under `tests/`.

## The cause, stated so a fix can be aimed at it

The defect is not in the attachment and not in `src/`. It is that the test
file asserts against COPIES of the attachment's properties instead of reading
the attachment's own published record of them. A copy of a fact about a file
that the file itself publishes will drift the first time the file moves, and
the drift is silent until a gate runs.

`docs/map/INV-seat-section-plugins.md` — the map document owning the organiser
shell — carries `check: python -m pytest tests/test_organiser_seat.py -q`, so
that document's verification is red for the same reason.

## Ruled out

- **Not a defect in `src/`.** The three failures are all literal comparisons
  in the test file; `9 passed` includes every assertion about the shell, the
  layouts, the wording, admission, citation measures and status.
- **Not a defect in the attachment.** `sha256sum -c ATTACHMENT.sha256` passes
  on the committed bytes, and `CONVERSION.json` reports `verbatim 94/94`.
- **Not a reader/version problem.** The retired epoch-1 attachment bytes are
  not committed anywhere in the tree (`runs/armR-epoch1/` holds logs and JSON
  results only), so the old digests name bytes that no longer exist in the
  working tree at all — only in git history at `9554abfe4`.
