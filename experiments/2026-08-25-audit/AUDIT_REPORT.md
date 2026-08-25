# AUDIT_REPORT — 2026-08-25 post-program close-out audit

Date: 2026-08-25 (UTC). Model: `claude-opus-5`.
HEAD: `853bf705cca96e97c22d193df5b1889511bd92c4`.
Baselines: `docs/AUDIT_BASELINES.md` @ `eac1b17b527ec6dfe4992b7a3d9cc81ba03610d8`.
Comparison copy: `experiments/2026-08-13-audit/`.

**Read-only.** This audit deleted nothing and changed nothing outside its
own tranche directory. Every finding leaves as a ready-to-send prompt in
`PARKED.md`.

## The three numbers the close-out asked for

| number | value |
|---|---|
| experiment directories leaving the tree, of the total | **70 of 152** (52 PRUNE + 18 EXTRACT-THEN-PRUNE) |
| docs files rowed PRUNE-CANDIDATE, of the total | **13 of 131** |
| open parks that must be re-homed before any deletion runs | **60** |

## Two things that are NOT true, stated first

**Nothing is broken.** Every instrument that ran came back at its recorded
baseline. The full test gate is green at 4162 passed, 6 skipped, 0 failed.

**The 70 prunable directories are not 70 lost records.** Git history keeps
every byte; each census row cites what it is and where it lives. Pruning
moves them out of the working tree, not out of the repository.

## PART 1 — the five standard dimensions

| dimension | result | artifact |
|---|---|---|
| broken | 5 instruments at baseline, 0 broken, 0 flaky; 1 could not run | `broken.md` |
| dead | 2947 symbols, 15 `candidate-dead` — identical to 2026-08-13 | `dead.md` |
| docs-drift | at baseline; one advisory delta (stale 0 → 8) | `docs-drift.md` |
| spec-drift | 4 orphans still open; +40 spec-silent surface items | `spec-drift.md` |
| goal-trace | 8 laws, 7 enforced, 1 process-law, 0 unenforced | `goal-trace.md` |

### The three highest-consequence findings, in plain language

**1. Two skills still order you to run an instrument the operator
retired.** `dr-drive-harness` and `dr-spec-change` both still name the
root sweep (`tools/root_sweep.py`) as an instrument that "proves you
broke nothing". The operator retired it on 2026-08-22 — "it just wastes
time" — and CLAUDE.md now forbids any tranche, gate, audit or grant from
requiring it. `dr-audit-broken` and `AUDIT_BASELINES.md` both carry the
retirement correctly, so the contradiction is confined to those two
files. What this does NOT mean: no verdict anywhere is wrong because of
it. What it does mean: an agent that reads the driving manual and obeys
it literally — which is exactly what that manual asks for — will spend
time on a retired instrument. Parked as **P1**.

**2. The 2026-08-13 audit's spec prompts were never picked up.** Four
spec-orphan terms (P6–P9) and the `MINI_PLAN.md` evidence-file drift
(P4) are re-measured here as completely unchanged. This is not new
breakage; it is the previous audit's output sitting untouched. Parked as
**P2** and rowed as `docs-drift` DD5.

**3. The spec is falling behind the code, and the rate is measurable.**
243 of 313 shipped surface items (78%) are now spec-silent, against 203
of 272 (75%) in August. Every one of the 40 items added since then
shipped without a spec amendment — the *covered* counts did not move at
all. Parked as **P3**, scoped deliberately to the 40-item delta rather
than the 243-item backlog, because a tranche aimed at the backlog would
never ship.

### What improved since 2026-08-13

- **L2 and L5 moved from `partially-enforced` to `enforced`.** Both had
  a mechanism but no test pinning it. Both now have one, and
  `tests/test_seats_evidence_law.py` cites the prior audit's own
  `goal-trace.md` row L2 in its docstring — the audit family closed its
  own loop.
- **Three new operator design laws** (L6 operations-parity, L7
  old-runs-owe-nothing, L8 signal-registry-as-contract) are traced for
  the first time, and all three are enforced with mechanism and test.
- **The map grew 11 documents and 208 executable checks with no new
  failures.**

## PART 2 and PART 3 — the censuses

Full tables: `experiments-census.md` (152 rows), `docs-census.md` (131
rows). Both are machine-readable, one row per artifact, stable columns —
they double as the index the repo has been missing.

### One methodology correction worth stating plainly

My first pass measured 74 of 76 CLI flags as spec-silent, against the
prior audit's 34. That would have read as a catastrophic regression. It
was my matching rule: the earlier audit matched the flag *stem*
(`cycles`), not the literal `--cycles`, and never said so. Re-run under
its rule the number is 34 — its figure reproduced exactly. The
reconciliation is in `proof/spec-method.txt` so the number is
re-derivable either way. No drift occurred.

### A cost of pruning that neither gate can see

**105 prose citations inside KEEP-rowed tranches point at PRUNE-rowed
directories** (`proof/census-citation-cost.txt`). Neither `docs_verify`
nor pytest reads narrative prose, so both gates stay green after the
prune — which is exactly why it needs saying out loud rather than being
left for an instrument to catch. Git history keeps every target, so
nothing becomes unrecoverable; the cost is that a reader following a
citation in a surviving tranche's RESULTS.md will need `git show`
instead of `ls`. Priced here for the operator, not treated as a blocker.

### Why the KEEP rows are not a matter of taste

25 executable `check:` lines across 12 map documents run against
committed run roots inside `experiments/`. Two were re-derived live
during this audit (`proof/census-keep-is-load-bearing.txt`): the
assertion that one root contains exactly 1083 files, and that it
materializes exactly 42 artifacts. Both hold. Delete the wrong directory
and `docs_verify` goes red the next time it runs.

### A replication worth more than either census alone

The dead-code pass reproduced the 2026-08-13 audit's 15 unreferenced
symbols **exactly — same fifteen, no additions, no removals** — using a
different implementation (one token index over the whole tree, versus a
ripgrep per symbol), run by a different model, twelve days and roughly a
thousand tests later. Two things follow, and they point opposite ways:
the prior audit's P2 prompt was never executed, *and* the list is now
independently corroborated rather than merely repeated.

It also shows what `candidate-dead` is not. `_document_excerpt`
(`llm/packs.py`) is on the list and should **not** be deleted:
`experiments/2026-08-01-change-prose-can-refute/PARKED.md` records that
it was "deliberately kept rather than deleted, because it is the right
tool for this path if the operator wants R3 extended to it." A mechanical
scan cannot tell "nobody calls this" from "nobody calls this yet, on
purpose, and the reason is written down elsewhere." One of the fifteen
has such a reason on record; the other fourteen have not been checked
for one.

### One instrument is dark, and it is the one that watches the outside world

`treadle doctor` could not run: the vendored virtualenv is gone (a
container rollback, which the baseline explicitly anticipates) and there
is no credential to run it with. It is rowed **no evidence** rather than
`baseline` — an instrument that could not run has said nothing in either
direction, and recording a green it never gave would be the one dishonesty
this family cannot afford.

Why it matters beyond bookkeeping: the baseline says a `WARN model tag …
NOT on endpoint` line "is always a finding: hosted checkpoints are retired
without notice, and that line is how this repo learns." If a hosted model
the treadle lane depends on were retired today, nothing here would notice.
Parked as **P6**.

## The picture AFTER the prune — approve this, not the rows

### `experiments/`: 152 directories → 82, plus one new file

Every surviving directory survives for a reason a machine can re-check:

| what keeps it | directories |
|---|---|
| a test opens it as a fixture, or names it as a regression's motivating run | 33 |
| a `docs/map` `check:` line executes against it, or a `Traps` entry names it | 27 |
| `src/`, `scripts/` or `tools/` reads it | 19 |
| CLAUDE.md, `AUDIT_BASELINES.md` or a skill names it by path | 3 |

That is the whole justification set. There is no "kept because it seemed
important" bucket, and there is no "deleted because nobody liked it"
bucket either.

**The new file is `experiments/OPEN_PARKS.md`** — the registry stage 1 of
the deletion tranche creates. Today, 60 deliberately-deferred work items
are scattered across 18 directories that are otherwise ready to go, and
the only way to find them is to know which tranche parked them. After the
prune they are one file, each row naming its originating tranche and the
sha where its full text lives. **This is the single largest structural
improvement in the whole close-out**, and it is worth more than the disk
the prune reclaims: it converts a deletion into a consolidation.

What `experiments/` becomes: 82 directories that instruments actually
touch, plus one index of everything the project decided not to do yet.

### `docs/`: 131 files → 118, in three clearly separated tiers

| tier | files | what it is |
|---|---|---|
| `docs/map/` | 64 | the code map. Self-authenticating — 1069 executable checks. Untouched. |
| living authority + referenced | 40 | the spec series and its amendments, the theory stack, ERRATA, AUDIT_BASELINES, the monitor handover, the research notes with open consumers, the navigation index |
| KEEP-UNTIL-ABSORBED | 14 | nothing absorbed these yet, so deleting them loses the only working-tree copy |

13 files leave: 4 superseded handovers, 2 research notes whose every
consumption point landed, `POIETIC_CALCULUS_v0.1` (superseded by the
FORMALIZED twin), `RUNTIME_IMPORTS` (documents a website subsystem the
tree no longer has), and 5 implemented or abandoned proposals.

**The operator's actual complaint — "a lot of data with no structure" —
is only half-answered by deleting 13 files.** The other half is the 14
KEEP-UNTIL-ABSORBED files. What a one-page absorption would need, named
so the next tranche can be scoped without re-deriving it:

1. **One `docs/REPORTS_DIGEST.md`**, absorbing the three dated one-time
   reports (`AUTONOMICS_REPORT` 2026-07-05, `STRESS_INSIGHTS`
   2026-07-04, `CAN_LLMS_EXPLORE`) into one page: per report, the
   question it asked, the number it produced, and whether that number
   still holds. Then those three can go. **Not `MINI_STRESS_REPORT.md`**,
   which looks like the same kind of document and is not:
   `SEAM-adjudication-x-rules.md:247` and `CON-warrants-and-attacks.md:253`
   both cite its §F4 as *evidence*, so it is rowed KEEP and absorbing it
   would break two map citations.
2. **One `docs/GUIDES.md` or a `docs/guides/` folder** for the five
   operator/migration guides that hang off living spec amendments
   (`SCRATCHPAD_GROUNDED_BRIDGE` → v1.4, `JOLT_CONTROL_PLANE_MIGRATION`
   → v1.5, `TRANCHE_A_AUTONOMOUS_SIMULATION` and
   `AUTONOMOUS_SIMULATION_MIGRATION` → v5, `RUN_PLAN_TEMPLATE` +
   `SELF_IMPROVEMENT` → `AGENT.md`). These are not reports and should
   not be pruned; they are just filed in the wrong place.
3. **A successor to `STATE_OF_THE_PROGRAM_2026-08-14`.** The close-out
   brief makes that file prunable *once its successor exists*. No
   successor exists on main, so it is currently the newest briefing the
   project has. Writing the 2026-08-25 successor is what unlocks it.
4. **Two status pages need a fact-check before absorption, not after:**
   `MINI_PLAN.md` (cites a missing evidence file — audit P4, still open)
   and `SMALL_MODEL_COMPATIBILITY.md` (names a kernel identifier absent
   from code — audit P5, still open). Absorbing a page whose claims are
   already known-wrong just moves the error.

### What does not change

`docs/map/` is untouched — all 64 documents, all 1069 checks. The five
frozen surfaces are untouched. No committed run root is edited. No
`ERRATA.md` entry is ever deleted: errata are append-only forever, and
an entry recording that a claim was found wrong stays true whether or
not the document it corrects survives.

## Close gates (audit-family standard)

All three pass. Full output: `proof/close-gates.txt`, `proof/close-gates-4.txt`.

**PRECEDENCE 1 — committed run roots are read, never written.**

    $ git status --porcelain -- experiments/ | grep -v 2026-08-25-audit
    (empty)

Two committed roots were opened during this audit to re-derive map
checks; both were opened `read_only=True`, and the empty status above is
the proof nothing was written back.

**PRECEDENCE 3 — nothing modified outside the tranche directory.**
`git status --porcelain` and `git diff --stat HEAD` name only files under
`experiments/2026-08-25-audit/`. Three activation plants edited tracked
files (`tests/test_error_catalog.py`,
`docs/map/SEAM-harness-x-verification.md`); each was restored with
`git checkout --` and its clean status pasted into its proof file.

**PRECEDENCE 4 — every verdict row cites a proof file that exists.**
44 LEDGER finding rows, 44 proof files, **0 missing**. Three rows cite a
census table rather than a `proof/` file (`experiments-census.md`,
`docs-census.md`); both exist and are the proof for those rows.

## Instruments run, and what each said

| instrument | ran | result |
|---|---|---|
| `pytest tests/ -q -n 4` | yes | 4162 passed, 6 skipped, 0 failed |
| `docs_verify` (full) | yes | 64 docs, 1069 checks, 3 failed (baseline) |
| `docs_verify --audit` | yes | 0 findings |
| `docs_verify --links` | yes | 0 dangling |
| `docs_verify --stale` | yes | 8 documents (was 0) |
| `wheel_smoke.py` | yes | exit 0 |
| `wheel_operational_smoke.py` | yes | exit 0, all stages |
| dead-code census | yes | 2947 symbols, 15 candidate-dead |
| root sweep | **no — retired** | marker written |
| `treadle doctor` | **no — not runnable** | no evidence; parked P6 |
| `cycle_soak.py` | **no — pre-launch only** | not applicable to a read-only audit |

## Parked prompts

`PARKED.md` carries **seven** ready-to-send prompts. Your cost per item
is one paste.

| | prompt | route |
|---|---|---|
| P1 | two skills still require the retired root sweep | `dr-change-orchestrator` |
| P2 | the four unexecuted 2026-08-13 spec-orphans | `dr-change-orchestrator` |
| P3 | a v1.8 amendment for the 40 new spec-silent surface items | `dr-change-orchestrator` |
| **P4** | **the experiments deletion tranche — extract 60 parks, then delete 70 directories** | `dr-change-orchestrator` |
| **P5** | **the docs prune tranche — 13 files** | `dr-change-orchestrator` |
| P6 | restore and run `treadle doctor` | `dr-change-orchestrator` |
| P7 | CLAUDE.md's stale "~3100 passed" gate expectation | `dr-change-orchestrator` |

Not parked, deliberately: the 15 `candidate-dead` symbols. The
2026-08-13 audit already parked them as its P2 and that prompt is still
valid and still unexecuted — re-parking it would just create a second
copy of the same work item. This audit corroborates it instead, and
adds the `_document_excerpt` caveat above to it.
