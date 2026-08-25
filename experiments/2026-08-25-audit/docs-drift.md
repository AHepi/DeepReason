# Dimension: docs drift (documentation vs code)

Primary instrument: the executable `check:` lines carried by every
load-bearing map claim. This worker runs the instrument, then censuses
what the instrument cannot see.

| id | target | gate | verdict | proof | disposition |
|---|---|---|---|---|---|
| DD1 | `docs_verify` full — 64 documents, 1069 checks, **3 failed** | pass | **baseline** | proof/docs-full.txt | baseline |
| DD2 | `docs_verify --audit` (toothless-check scan) — 0 findings | pass | baseline | proof/docs-audit.txt | baseline |
| DD3 | `docs_verify --links` — 0 dangling `DR-` references, 64 documents | pass | baseline | proof/docs-links.txt | baseline |
| DD4 | `docs_verify --stale` — **8 documents worth re-reading** | pass | **stale-stamp** | proof/docs-stale.txt | baseline (advisory) |
| DD5 | `docs/MINI_PLAN.md` Status line cites a missing evidence file | pass | **drifted** | proof/docs-claim-verification.txt | parked (already open as 2026-08-13 P4) |
| DD6 | `docs/ADMISSION_SPEC.md` Status "v1 IMPLEMENTED" | pass | covered | proof/docs-claim-verification.txt | baseline |
| DD7 | `docs/RESEARCH_BACKEND.md` Status "tranche 1 IMPLEMENTED" | pass | covered | proof/docs-claim-verification.txt | baseline |

## DD1 — the three failures are the recorded baseline, exactly

`AUDIT_BASELINES.md` says: "3 pre-existing failures, all
`CON-run-identity.md` git-history checks — they require an unshallowed
clone; on a full clone the expected value is 0 failed." All three
failures are `CON-run-identity.md:200`, `:202` and `:204`, and two of
them fail with `fatal: ambiguous argument '<sha>': unknown revision`.

Cause confirmed rather than assumed: `git rev-parse
--is-shallow-repository` → `true`, and `git rev-list --count HEAD` → 54.
This container holds a 54-commit shallow clone, so the history those
checks reach for is genuinely absent. **Baseline, not a finding.**

## DD1 scale delta against 2026-08-13

| | 2026-08-13 | 2026-08-25 | delta |
|---|---|---|---|
| documents | 53 | 64 | +11 |
| checks | 861 | 1069 | +208 |
| failed | 3 | 3 | unchanged |

The map grew by 11 documents and 208 executable checks with no new
failures. That is the map discipline working.

## DD4 — the stale list moved 0 → 8, and this is the one real delta

The prior audit recorded 0 stale stamps. Eight documents now carry a
`Verified-at:` stamp behind commits that touched files they own:

    CON-criticism-source.md      2 commits (Rung 6)
    CON-run-identity.md          1 commit  (Rung 6)
    CON-scheduler-ranking.md     1 commit  (Rung 8 steps 12-14)
    SEAM-calculus-x-rules.md     1 commit  (Rung 8 step 11)
    SEAM-evaluation-x-ontology.md 1 commit (Rung 8 steps 15-18)
    SEAM-llm-x-rules.md          1 commit  (Rung 6)
    SEAM-llm-x-scheduler.md      1 commit  (Rung 6)
    SEAM-scheduler-x-rules.md    1 commit  (Rung 8 steps 12-14)

Every one traces to the Rung 6 / Rung 7 / Rung 8 tranches of the past
four days. **Disposition `baseline`, per this worker's own outlet rule:
a stale stamp on a PASSING document is advisory, and re-stamping without
re-running the checks is the one forbidden move.** It is proof nobody has
re-read those documents, not proof they are wrong — all 1069 checks pass.

Related and already open: `experiments/2026-08-24-change-rung5-promotion-
criteria/PARKED.md` P4 parks stale `Verified-at:` stamps on eight map
documents. That park is one of the 60 open items the deletion tranche
must re-home, and it now has a second, independently measured instance.

## DD5 — the one genuine drift, and it was already known

`docs/MINI_PLAN.md`'s Status line reads "BUILT AND LIVE-VERIFIED — see
`mini/`" and cites `experiments/results/mini_smoke_report.json`. `mini/`
exists at repo root; **the cited evidence file does not exist.** This is
the finding the 2026-08-13 audit parked as its P4, unexecuted since.
Rowed again rather than re-parked separately.

**Count line: 7 findings tabled — 0 toothless-check, 0 dangling links,
8 stale-stamp (advisory, baseline), 1 drifted (already parked), 5 baseline.**
