# SPEC — close-out prune of `experiments/`

Traces to `REQUEST.md` R1-R6.

## Map preflight (dr-drive-harness §4)

Resolved ids: **none**. This tranche touches no package under
`src/deepreason/`, so no `DR-SUB-`/`DR-CON-`/`DR-SEAM-` id covers it.
That is a fact about the change, not a gap in the map: the map describes
`src/deepreason/`, and this change edits only `experiments/`.

`docs/map/INV-frozen-surfaces.md` read before designing. **No frozen
surface is touched.** The five surfaces are code and format surfaces
(`capabilities/state.py` digests, `harness.py` event application,
`invariants.py` + `verification/`, `run_manifest.py` schemas,
`qualification.py` subjects). Deleting an experiment directory touches
none of them.

One frozen-surfaces-adjacent fact, checked explicitly:
`INV-frozen-surfaces.md:406` cites
`experiments/2026-08-03-change-rung2-engaged-criticism-switch/`. That
directory is rowed **KEEP** (Q-E1), and is not on the delete list.

## What changes

| # | change | requirement |
|---|---|---|
| S1 | new file `experiments/OPEN_PARKS.md` | R2 |
| S2 | 18 EXTRACT-THEN-PRUNE directories removed | R1, R3 |
| S3 | 52 PRUNE directories removed | R3 |

Nothing under `src/`, `tests/`, `tools/`, `scripts/`, `docs/` changes.
No `.claude/skills/` file changes.

## Safety property, verified BEFORE any deletion

**Not one of the 70 directories on the delete list is referenced from
`tests/`, `src/`, `scripts/`, `tools/` or `docs/map/`.** Re-derived at
tranche open, independently of the census that produced the list:

    while read -r d; do grep -rIn --exclude-dir=.git -e "$(basename $d)" \
      tests/ src/ scripts/ tools/ docs/map/ ; done < delete.txt
    -> 0 directories with any hit

This is the property that makes R5's two gates predictable rather than
hopeful. Proof: `proof/safety-recheck.txt`.

## A known consequence, priced not prevented (A2)

**26 of the 70 are cited from `docs/` prose** — chiefly `docs/ERRATA.md`
and `docs/ERRATA_EXECUTOR.md`, plus three handovers,
`docs/HIDDEN_LEGACY_INVENTORY.md`, `docs/proposals/DETERMINISTIC_GATES_PREPLAN.md`,
`docs/AUTONOMOUS_SIMULATION_MIGRATION.md`, `docs/INDEX.md`, and
`docs/harness-spec-v1.7-amendment.md`.

This is NOT a census miss. The operator's Q-E1 scoped the reference grep
to `tests/`, `src/`, `scripts/`, `tools/`, `docs/map/` — `docs/` prose was
deliberately outside it, because `docs/` narrative is itself the target of
the separate docs census. The audit reported the same class of cost for
citations inside `experiments/` (105 pairs) and the operator approved on
that basis.

No instrument reads these citations: `docs_verify` checks map `check:`
lines and `DR-` links, not prose paths into `experiments/`. Both R5 gates
therefore stay green. The cost is that a reader following one of these
citations needs `git show` rather than `ls`.

Two of the 26 sit in documents that are normative or navigational rather
than narrative, and are called out so they are not lost in the count:

- `docs/harness-spec-v1.7-amendment.md:12` cites
  `experiments/2026-08-11-spec-drift-measurement/DRIFT_TABLE.md` as
  evidence for a spec claim. The spec series is append-only; the citation
  is not edited by this tranche.
- `docs/INDEX.md:4` and `:149` cite the same directory. `INDEX.md` is the
  navigation layer and is rowed KEEP.

**Disposition: PARKED, not fixed here.** Repairing `docs/` citations is
the docs-prune tranche's job (P5), which already carries an explicit
requirement to fix `INDEX.md` links in the same commit. Fixing them here
would widen this tranche into P5, which the operator did not approve.
Parked as this tranche's P1 with the full 26-row list.

R2's sha requirement is what discharges "nothing is lost": every deleted
directory's content is one `git show <sha>` away, and the sha is recorded.

## Acceptance checks

| check | requirement | how proven |
|---|---|---|
| AC1 | `experiments/OPEN_PARKS.md` exists and carries every open item from all 18 EXTRACT directories, verbatim | R2 | item count matches the audit's 60; each row carries tranche + sha |
| AC2 | no open park text is summarized or truncated | R2 | extraction is a byte copy of the source region; a diff of extracted-vs-source text is empty |
| AC3 | exactly 70 directories removed; exactly 82 remain | R3, R4 | `ls -d experiments/*/` count before and after |
| AC4 | every one of the 82 KEEP rows still present | R4 | set comparison against `experiments-census.md` |
| AC5 | `python tools/docs_verify.py` FULL: no non-baseline failure | R5 | 3 `CON-run-identity` git-history failures only (shallow clone) |
| AC6 | `python -m pytest tests/ -q -n 4`: 0 failed | R5 | 4162 passed, 6 skipped |
| AC7 | nothing changed outside `experiments/` | R3 | `git status --porcelain -- src/ tests/ docs/ tools/ scripts/ .claude/` empty |
| AC8 | P5 untouched | scope boundary | the 13 docs PRUNE-CANDIDATE files all still present |

## Diff budget

One new file (`OPEN_PARKS.md`), 70 directory removals, one tranche
directory. No source file modified. A diff touching any file under `src/`
or `tests/` is out of budget and a stop condition.
