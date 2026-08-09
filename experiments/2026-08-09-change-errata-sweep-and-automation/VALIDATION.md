# Validation for: update the Errata (sweep + automation)

## Acceptance checks

S1: `grep -c "^\*\*E13" docs/ERRATA.md` -> 1 : PASS
S2: `grep -c "^\*\*E14" docs/ERRATA.md` -> 1 : PASS
S3: `grep -c "^\*\*E11" docs/ERRATA.md` -> 1 : PASS
S4: `grep -c "^\*\*E12" docs/ERRATA.md` -> 1 : PASS
S5: `grep -c "^\*\*E15" docs/ERRATA.md` -> 1 : PASS
S6: `grep -c "^\*\*E16" docs/ERRATA.md` -> 1 : PASS
S7: `grep -c "^\*\*E17" docs/ERRATA.md` -> 1 : PASS
S8: `grep -c "220-300\|220–300" docs/ERRATA.md` -> 0 (no entry written
    for the excluded S5 budget-headline candidate) : PASS
S9: `docs/ERRATA.md`, `.claude/skills/dr-deliver-change/SKILL.md`, and
    `.claude/skills/dr-verify-outcome/SKILL.md` all quote the same
    diagnosis paragraph's substance (checkpoint text derived from
    SPEC.md's "Diagnosis (R5)" section) : PASS
S10: `grep -ic "errata" .claude/skills/dr-deliver-change/SKILL.md` -> 9
     (>=3 required: procedure step 3c, DELIVERY.md template's Errata
     section, exit-criterion line) : PASS
S11: `grep -ic "errata" .claude/skills/dr-verify-outcome/SKILL.md` -> 6
     (>=2 required: closing-tranche bullet, VERIFY.md template line) :
     PASS

## Full gate

`python3 -m pytest tests/ -q -n 4` -> "1 failed, 3434 passed, 7 skipped
in 780.12s (0:13:00)" — the one failure,
`test_bronze_report.py::test_census_totals_internally_consistent`
(`assert 159 == 165`), is PRE-EXISTING, not caused by this tranche.
Proof (git-stash-equivalent, since this tranche's tree is fully
committed with nothing to stash): reproduced the identical assertion
(`159 == 165`) against a fresh, isolated `origin/main` checkout
(`git worktree add /tmp/dr-main-check2 origin/main --detach`) in a
throwaway venv holding no state from this session
(`python3 -m venv /tmp/dr-main-venv`), then removed both. This tranche
also changed zero files under `src/` or `tests/` — no code path this
tranche touches could produce a census-arithmetic mismatch. The failure
is already known and parked as D2's own
`experiments/2026-08-08-change-pipeline-design-d2/PARKED.md` item
P-D2-3 (dated 2026-08-08, five days before this tranche started), and
SPEC.md's "Out of scope" section named it explicitly as excluded from
this tranche's work. Per this skill's own rule ("a pre-existing failure
you can prove pre-dates the change... is recorded as such and does not
block, but goes to PARKED.md"): recorded here and cross-referenced in
this tranche's own PARKED.md (below). Verdict for this check: PASS
(non-regression proven), with the pre-existing failure disclosed, not
hidden.

Environment notes, neither caused by nor fixed as part of this
tranche's SCOPE (docs/ERRATA.md + two skill files), but required to get
an honest gate reading at all, so recorded for the next session: (1)
the bare `pytest` on `$PATH` resolves to an isolated `uv tool install`
environment missing `deepreason`/`jsonschema`/`pytest-xdist` from this
project's own venv — invoke `python3 -m pytest` instead; (2) `pytest`
and `jsonschema` were not present in the system Python's site-packages
at session start and were installed
(`pip install pytest pytest-xdist jsonschema --break-system-packages`);
(3) the container's git clone was shallow, failing 3
`CON-run-identity.md` checks that `git log` two historical run-
retirement commits by hash — fixed with `git fetch --unshallow origin`
(confirmed those 3 checks also fail on a fresh shallow `origin/main`
clone and pass once unshallowed, so this is a clone-depth artifact, not
a document error — no `ERRATA.md` entry warranted).

## Record-behavior preservation

n/a — this tranche touches no reader, validator, or writer of the
append-only record (`docs/ERRATA.md` and two `.claude/skills/*.md`
files only).

## Frozen-surface diff

    $ git diff --stat b5921b3ab00e69d148a133ff029990bb835142a2..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    (empty)

PASS — empty, as forecast in SPEC.md (this tranche touches no `src/`
file at all).

## Packaging surface

untouched — smoke not owed. This tranche changed no `pyproject.toml`,
CLI entry point, MCP server surface, or wheel-layout file.

## Map

docs_verify: 53 documents, 851 checks, 0 failed : PASS (required an
environment fix unrelated to this tranche's content — see Full gate
section's environment notes, item 3)
docs_verify --audit: 0 finding(s) : PASS
docs_verify --links: 0 dangling reference(s), 53 document(s) : PASS
docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0
finding(s) : PASS (the 16 without-header seams are pre-existing and
untouched by this tranche, which creates/edits no `docs/map/` document
at all)
docs_verify --stale: 33 document(s) worth re-reading — all 33 are
`docs/map/SUB-*.md`/`CON-*.md` documents listing commits from PRIOR,
already-delivered tranches (S1-S7, D1-D2, G1, L1, O1, rungs 4-7, etc.);
none names `docs/ERRATA.md` or a `.claude/skills/` file (neither is a
`docs/map/` document — this tranche is docs/skills-only, see
REQUEST.md's Map preflight and SPEC.md's frozen-surface forecast), and
none was made stale BY this tranche (this tranche created/changed zero
`docs/map/` files). Dismissed as out of scope for this tranche's
`Verified-at:` stamps; each is a candidate for whichever future tranche
next touches that subsystem, per the map's own maintenance rule ("the
map moves in the SAME COMMIT as the code" — there is no code here to
move it with).
new checks added by this change: none — this is a docs-ledger and
process-skill change, not new system behavior; SPEC.md's own rubric
pass records why (no `[DESIGN-AND-STOP]` shape, no new src/ behavior to
pin a check to).
record observables added vs sweep probes: none — no new field, record
type, or finding was added to the typed record.
wheel smoke: packaging surface untouched — smoke not owed.

## Requirement sweep

R1 (sweep every tranche since 2026-08-04): demonstrated by S1-S7
(seven confirmed entries E11-E17) plus the documented negative result
for the S5 budget-headline candidate (S8) — three independent research
sweeps covered all 25 named tranches (seat rungs S1-S6, D1/D2/D4, G1,
L1, O1/O2, the omnibus, the hard-set, and the 08-04/08-05 rung/
guardrail/investigation tranches; D3 confirmed not to exist).
R2 (every entry states claim/location/record/correction): demonstrated
by E11-E17's text in `docs/ERRATA.md` (each entry names the claiming
document + location, quotes the correcting record, and states where/
whether it stands corrected).
R3 (no errata for in-tranche revision supersessions): demonstrated by
S8's exclusion of the S5 budget-headline candidate (R21/R22, the
tranche's own stated amendment mechanism) and by SPEC.md's Out-of-scope
section declining to ledger any same-document revision found during
the sweep (S2/S3/S4's in-tranche corrections, D2's SPEC.md
self-corrections).
R4 (verify each named candidate against the record, don't copy blind):
demonstrated by S1/S2 (CLAUDE.md commits `1f6c24ab`/`7e8f42402`,
verified by direct `git show`), S7 (O1/O2, verified by direct file
reads of the cited line ranges), and S8 (the S5 candidate, verified and
correctly EXCLUDED rather than ledgered) — every candidate on the
operator's own list was independently re-verified against primary
source, not transcribed from a sub-agent's report unchecked.
R5 (diagnose in one paragraph why the ledger isn't automatic):
demonstrated by SPEC.md's "Diagnosis (R5)" section.
R6 (mandatory closing checkpoint, state-not-silence, in both skills):
demonstrated by S10/S11 — `dr-deliver-change/SKILL.md`'s new Procedure
step 3c + DELIVERY.md template's Errata section + exit criterion;
`dr-verify-outcome/SKILL.md`'s new closing bullet + VERIFY.md template
line.
R7 (checkpoint matches each skill's own existing state-not-silence
pattern): demonstrated by S10 explicitly citing 3b's "'No map change'
is a legitimate answer... say it rather than omitting the section" as
its own model, and S11 explicitly citing the existing "Residue
(honest): ... or 'none'" line as its model.
R8 (full gate + docs_verify full at the boundary): demonstrated by this
VALIDATION.md's Full gate and Map sections above.
R9 (deliver through validate/deliver, push each boundary): demonstrated
by every CHECKLIST.md [COMMIT] step's pasted push confirmation, and
this VALIDATION.md itself being the validate-phase artifact.
R10 (route through dr-change-orchestrator, ledger authority in
REQUEST.md): demonstrated by REQUEST.md's Verbatim section and this
tranche's phase sequence (capture -> spec -> plan -> execute ->
validate).

## Assumptions carried

A1 (Q1): `docs/ERRATA_EXECUTOR.md` is out of this tranche's scope — all
three sweep agents independently classified every confirmed finding as
`docs/ERRATA.md`-scoped; no material effect.
A2 (Q2): the R6 checkpoint's wording is reused near-verbatim in both
skills, substituting only the artifact name each skill closes with
(DELIVERY.md / VERIFY.md).

## Verdict: PASS
