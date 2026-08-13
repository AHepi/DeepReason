# Parked — found during the single-run-path tranche, deliberately not done

One line of WHAT, then a ready-to-send prompt. The follow-up should cost
the operator a paste, not an authoring session.

## P1 — two `docs_verify --coverage` findings pre-date this tranche

WHAT: `python tools/docs_verify.py --coverage` reports 2 findings —
`SEAM-schools-x-scratch.md` does not name `src/deepreason/informal/trial.py`
as an enforcement site, and 16 seam documents carry no `Sweep:` header.
Neither names a document this tranche touched (only `SUB-application.md`
and `CON-run-identity.md` moved), so both pre-date it. Not fixed here:
validation may not edit the map, and fixing another seam's coverage
mid-tranche is scope creep.

READY-TO-SEND PROMPT:

```
Change tranche: close the two docs_verify --coverage findings. Route
through dr-change-orchestrator.

SETUP: git fetch origin main && git checkout -B claude/seam-coverage-<slug>
origin/main; pip install -e . --break-system-packages -q. Use
`python -m pytest`, never bare pytest.

AUTHORITY: `python tools/docs_verify.py --coverage` reports "6 seam(s)
swept, 16 without a Sweep: header, 2 finding(s)". Finding 1:
SEAM-schools-x-scratch.md does not name src/deepreason/informal/trial.py
as an enforcement site. Finding 2 is the 16 headerless seams, which the
tool itself annotates "add when next touched".

SCOPE: (1) Read docs/map/SCHEMA.md's Sweep: contract first. (2) Decide,
with evidence from the code, whether informal/trial.py genuinely enforces
the schools x scratch agreement or whether the coverage sweep is
over-reaching — the map's own falsification discipline says a finding can
be wrong about the document. (3) Fix whichever is wrong, with a check
that would fail if it regressed. (4) The 16 headerless seams: do NOT bulk-
add headers; the tool's own guidance is "add when next touched", so
either leave them and record that decision in VALIDATION.md, or pick the
ones whose agreement you can actually sweep and do those only.

GATE: docs_verify full + --audit + --links + --coverage. Baselines per
docs/AUDIT_BASELINES.md (3 CON-run-identity git-history failures on a
shallow clone). Map moves in the same commit as any code.
```

## P2 — `Verified-at:` stamps under-report on two map documents

WHAT: `SUB-application.md` (`98a5bc8f`) and `CON-run-identity.md`
(`bdc476e8`) kept their stamps through this tranche although every one of
their 44 checks was re-run and passes. `docs_verify --stale` reports 0
documents worth re-reading, so nothing is flagged; the stamps are stale-
but-honest rather than false. The previous two tranches to touch
`SUB-application.md` left it at `98a5bc8f` as well, so this is a habit
rather than a one-off.

READY-TO-SEND PROMPT:

```
Change tranche: make Verified-at stamps move when a document is
re-verified. Route through dr-change-orchestrator.

SETUP: git fetch origin main && git checkout -B claude/verified-at-<slug>
origin/main; pip install -e . --break-system-packages -q.

AUTHORITY: docs/map/SCHEMA.md says "Update Verified-at: to the commit you
are making. If you did not check the document's claims, do not advance the
stamp — a stale stamp is honest, a false one is not." In practice stamps
are not advancing: SUB-application.md has read 98a5bc8f across at least
three tranches that each re-ran its checks (2026-08-13 lifecycle parity,
2026-08-13 single-run-path unification, and the map-gate fix before them).

SCOPE: (1) Measure first — for every docs/map document, compare its
Verified-at against the last commit that touched it AND the last commit
that touched its Owns: files. Report the census before proposing
anything. (2) Decide whether the gap is a tooling gap (nothing computes
the right value at commit time) or a discipline gap. (3) If tooling: the
smallest fix is a docs_verify mode that PRINTS the stamp each passing
document should carry, so an executor can paste it — not an auto-editor,
which would advance stamps nobody checked. (4) Do not bulk-advance stamps
as part of this tranche; that is exactly the false-stamp failure SCHEMA.md
names.

GATE: docs_verify full + --audit + --stale. Baselines per
docs/AUDIT_BASELINES.md.
```

## Nothing else was parked

No defect was found in the code this tranche touched. The one full-gate
failure (`test_bronze_report.py::test_census_totals_internally_consistent`,
`assert 159 == 165`) is already parked with a diagnosis prompt in
`experiments/2026-08-09-change-judge-evidence-review/PARKED.md` P1 and is
not re-parked here.
