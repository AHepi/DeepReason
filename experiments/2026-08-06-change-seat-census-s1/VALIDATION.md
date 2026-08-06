# Validation for: seat census — Rung S1 of role-seat separation

## Acceptance checks

S1 (R2, R6): every call site enumerated.
```
$ grep -rn "\.call(" src/deepreason --include="*.py" | wc -l
43
$ grep -n "render_role_prompt\|EndpointLease(\|select_lease" src/deepreason/cli/doctor.py | wc -l
4
```
Matches CENSUS.md's M0 sweep exactly (spot-checked byte-exact in
CHECKLIST.md step 12). **PASS**

S2 (R3): one M-row per call site, no silent drop.
```
$ grep "^| M" experiments/2026-08-06-change-seat-census-s1/CENSUS.md | grep -v "^| M#" | wc -l
44
```
44 = 43 `.call(` hits (all promoted, 0 excluded) + 1 `doctor.py`
`render_role_prompt` dispatch (M1-M43, M44). **PASS**

S3 (R4): `select_lease` degrees of freedom measured from its own
source and both callers.
```
$ grep -n "^def select_lease" -A 4 src/deepreason/llm/firewall.py
def select_lease(
    leases: Mapping[str, tuple[EndpointLease, ...]], role: str, seat: int
) -> EndpointLease:
    try:
        lease = leases[role][seat]
```
`CENSUS.md`'s "select_lease degrees of freedom" section pastes
`Route`, `EndpointLease`, `leases_from_endpoints`,
`leases_from_manifest`, `select_lease` in full and derives the
variance statement from that text alone. **PASS**

S4 (R1): no `src/` file modified by this tranche.
```
$ git diff --stat 7a6d1cdb..HEAD -- src/
(no output)
```
**PASS**

S5 (R5): every claim backed by a pasted command. Spot-checked 3
CENSUS.md commands byte-exact against fresh output in CHECKLIST.md
step 12 (M0 raw sweep, `select_lease` source, `preparation.py:263-277`
mint-time fact) — all 3 exact matches. **PASS**

S6 (R7): `docs/map/CON-seats.md` follows the `SCHEMA.md` convention.
```
$ python tools/docs_verify.py --self-test
docs_verify --self-test: ok
```
File has doc-id comment, `Verified-at`/`Verify`/`Owns`/`Seams`/
`Seams-undocumented` headers, "What it is"/"Where it lives"/"The rules
it obeys"/"Traps" sections, 6 `` `check:` `` lines at column 0,
`docs/map/INDEX.md` row added. **PASS**

S7 (R8): `python tools/docs_verify.py` (full mode) 0 failed.
```
$ python tools/docs_verify.py
docs_verify [full]: 52 documents, 823 checks, 4 workers
docs_verify: 0 failed
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 52 document(s)
```
(Required installing this container's missing `dev` extras and one
undeclared test import first — recorded as P1/P2 in PARKED.md, not a
`CON-seats.md` defect: `CON-seats.md`'s own 6 checks were green on the
very first run, before either install.) **PASS**

S8 (R9): no Rung S2 design work performed.
```
$ grep -inE "should bind|recommend|SeatBinding|propose (a|the) (design|binding)" experiments/2026-08-06-change-seat-census-s1/CENSUS.md docs/map/CON-seats.md
(no output)
```
Manual re-read (CHECKLIST.md step 13) confirms both documents describe
only present-tense mechanism; `CON-seats.md`'s one forward-looking
sentence explicitly disclaims S2 scope. **PASS**

S9 (R10): every defect found is parked, not fixed.
`experiments/2026-08-06-change-seat-census-s1/PARKED.md` exists with
3 entries (P1 `jsonschema`, P2 `pytest-xdist`, P3 a continued root's
double module-fingerprint stamp — the last found during THIS
validation phase, not the census steps, and added here rather than
silently fixed). **PASS**

S10 (R2, C2): plan-named modules with zero call sites are noted as
delegating, not silently dropped.
```
$ grep -cE "^\| \`(workloads/(website|code|formal|text|simulation)\.py|qualification\.py|capabilities/(simulation|research)\.py|scratch/(conjecture|service)\.py)\`" experiments/2026-08-06-change-seat-census-s1/CENSUS.md
10
```
One row per named module confirmed zero-hit: `workloads/website.py`,
`workloads/code.py`, `workloads/formal.py`, `workloads/text.py`,
`workloads/simulation.py`, `qualification.py`,
`capabilities/simulation.py`, `capabilities/research.py`,
`scratch/conjecture.py`, `scratch/service.py`.
**PASS**

## Full gate

```
$ python -m pytest tests/ -q -n 4
1 failed, 3339 passed, 7 skipped in 588.03s (0:09:48)
FAILED tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after
```
This tranche made zero `src/` or `tests/` changes
(`git diff --stat 7a6d1cdb..HEAD -- src/ tests/` is empty both ways —
confirmed above and independently in CHECKLIST.md step 14), so the
failure provably pre-dates this tranche and is not caused by it. Root
cause identified (a continued root now carries 2 module-fingerprint
stamps where the test expects exactly 1) and recorded as PARKED.md
P3, with a ready-to-run diagnosis for `deepreason-orchestrator`, per
this skill's own rule 3 ("a pre-existing failure... is recorded as
such and does not block, but goes to PARKED.md"). **Gate: PASS
(pre-existing failure parked, not caused by this change)**

## Record-behavior preservation

n/a — this tranche touches no reader or validator of the append-only
record (`src/` untouched entirely). `verify_root` was not re-run
against any root; nothing in this change could affect it.

## Requirement sweep

R1 (process): demonstrated by S4 — zero `src/` diff since tranche
start, and no design/decision content (S8) landed.
R2 (behavior): demonstrated by S1/S2 — every call site across every
named consumer enumerated (44 promoted sites, 10 delegating modules
noted with evidence).
R3 (behavior): demonstrated by S2 — every M-row carries role rendered,
lease selection path, frozen-per-role status.
R4 (behavior): demonstrated by S3 — `select_lease` degrees of freedom
measured and stated.
R5 (process): demonstrated by S5 — every claim pasted-command backed;
3/3 spot-checked byte-exact.
R6 (artifact): demonstrated by S1/S2/S6 — CENSUS.md (measured table)
and `docs/map/CON-seats.md` (concept doc) both exist and are complete.
R7 (artifact): demonstrated by S6 — `docs/map/CON-seats.md` follows
`SCHEMA.md`'s convention with runnable checks.
R8 (process): demonstrated by S7 — `docs_verify` full mode, 0 failed.
R9 (process): demonstrated by S8 — no S2 design content found on
re-read.
R10 (process): demonstrated by S9 — PARKED.md exists with 3 concrete,
ready-to-run entries (P1, P2, P3), none fixed in this tranche.

Every R demonstrated by a PASS acceptance check above; none deferred.

## Assumptions carried

A1 (Q1): the census enumerates every actual call site found by
grepping the live tree, not the plan's naming sketch verbatim; modules
matching the sketch but holding zero call sites are noted as
delegating (CENSUS.md's "Delegating modules" table).
A2 (Q2): the table carries a per-row "frozen-per-role" column even
though the code-level answer is uniformly "No" (one `endpoint` copied
across `V3_CANONICAL_ROLES` at `preparation.py`'s mint time) — no row
was assumed away without its own evidence pointer.
A3 (Q3): `docs/map/CON-seats.md` got an `INDEX.md` row and reuses
existing `DR-SEAM-llm-x-manifest`/`DR-SEAM-llm-x-rules` seam
references; the tranche's binding acceptance gate remained
`docs_verify` full mode 0 failed exactly as R8 states, with `--links`
run as a free bonus (also 0 dangling).

## Verdict: PASS
