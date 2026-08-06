# Delivered: seat census — Rung S1 of role-seat separation
Branch: `claude/seat-census-rung-s1-7gphj9` @ `d74cff79` (pushed, tree
clean)

## What changed

`experiments/2026-08-06-change-seat-census-s1/CENSUS.md` enumerates
every provider call site in the tree today: 43 through
`LLMAdapter.call` (or a subclass's `.call`) and 1 through
`cli/doctor.py`'s qualification battery, which renders and dispatches
on its own without ever calling `LLMAdapter.call`. A 44-row table
records, per site, the role rendered, the `template_role` (when used),
how its lease is selected (`select_lease` by default, or an explicit
caller-supplied `endpoint_lease` for school-routed and v6 sites), and
whether its presentation is frozen per-role today. Ten plan-named
modules that turned out to hold zero call sites of their own
(`workloads/website.py`, `workloads/code.py`, `workloads/formal.py`,
`workloads/text.py`, `workloads/simulation.py`, `qualification.py`,
`capabilities/simulation.py`, `capabilities/research.py`,
`scratch/conjecture.py`, `scratch/service.py`) are named as delegating
to the module that actually dispatches, each with its own evidence.

The central measured fact, found while building the table: every
canonical role is populated from the SAME single `ProviderProfileV1`-
derived endpoint at `deepreason setup` time
(`preparation.py`: `roles={role: dict(endpoint) for role in
V3_CANONICAL_ROLES}`). That one line, not any limit in `select_lease`,
is why no role's model/endpoint is frozen differently from any other's
today — `select_lease` itself already resolves a fully independent
`Route` (model, endpoint, family, reasoning, temperature, ...) per
`(role, seat)` pair, and v6 transactional runs already resolve
PRESENTATION profile (compact/standard/frontier, never provider/model
identity) per `(role, seat, endpoint_id)` via
`resolve_route_seat_base_profile`. This is documented as a permanent
concept in `docs/map/CON-seats.md` (added to `docs/map/INDEX.md`),
following the map's existing `SCHEMA.md` convention with 6 runnable
`check:` lines.

No file under `src/` or `tests/` was touched. `python
tools/docs_verify.py` (full mode, 823 checks across 52 documents) and
`--links` both report clean. The full project gate (`pytest tests/ -q
-n 4`) was also run per `dr-validate-change`'s standing procedure:
3339 passed, 7 skipped, 1 failed — proven pre-existing (this tranche's
diff never touches `src/` or `tests/`) and parked, not fixed, along
with two undeclared test/dev dependencies (`jsonschema`,
`pytest-xdist`) this container was missing — all three in
`PARKED.md` as ready-to-run entries for future tranches.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "MEASURE ONLY — no src/ change, no design." | done | `git diff --stat 7a6d1cdb..HEAD -- src/` empty (VALIDATION.md S4); S8 re-read found no S2 content |
| R2 | "Enumerate every provider call site and classify it by role and consumer" | done | CENSUS.md M0 sweep + M1 table, 44 sites (VALIDATION.md S1, S2) |
| R3 | "For each: which role it renders, which lease it selects, whether its profile is frozen per-role today" | done | CENSUS.md M1 table columns (VALIDATION.md S2) |
| R4 | "measure the lease/seat mechanism's current degrees of freedom — what select_lease can already vary" | done | CENSUS.md "select_lease degrees of freedom" section (VALIDATION.md S3) |
| R5 | "Every claim is a pasted command output." | done | 3/3 spot-checked byte-exact (VALIDATION.md S5, CHECKLIST.md step 12) |
| R6 | "Deliverable: a measured table... in the tranche + docs/map/CON-seats.md naming the seat concept" | done | CENSUS.md + docs/map/CON-seats.md, both committed (VALIDATION.md S1/S2/S6) |
| R7 | "docs/map/CON-seats.md with runnable checks" | done | 6 `check:` lines, `docs_verify --self-test: ok` (VALIDATION.md S6) |
| R8 | "docs_verify full mode 0 failed" | done | `docs_verify [full]: 52 documents, 823 checks... 0 failed` (VALIDATION.md S7) |
| R9 | "Stop after delivering S1... do not begin S2's design." | done | S8 re-read found zero S2 content; this document does not begin S2 |
| R10 | "Anything broken you find along the way is parked with a ready-to-run entry." | done | `PARKED.md`: P1 (jsonschema), P2 (pytest-xdist), P3 (continued-root double fingerprint stamp) |

Every requirement done; none deferred, none not-done.

## Assumptions the operator may override

A1 (Q1): the census enumerates every call site the live tree actually
has, not the plan's file-name sketch verbatim; a sketch-named module
with zero call sites of its own is noted as delegating, with its real
owning site cited.
A2 (Q2): the per-row "frozen-per-role" column stayed in the table even
though the mechanism-level answer is a uniform "No" for every ordinary
site — grounded per-row, not glossed over as a single blanket claim.
A3 (Q3): `docs/map/CON-seats.md` got an `INDEX.md` row and reuses the
two existing, already-real `DR-SEAM-llm-x-manifest`/
`DR-SEAM-llm-x-rules` seam references rather than inventing new ones;
`docs_verify` full mode (not `--links`) remained the one binding gate,
`--links` a free bonus.

## Parked (not done, not promised)

- **P1** — `jsonschema` is imported directly by
  `tests/test_schema_carries_every_prose_rule.py` but declared nowhere
  in `pyproject.toml`; a fresh container following the documented
  `pip install -e ".[dev]"` gate setup fails that test with
  `ModuleNotFoundError`. Fix shape: add it to the `dev` extra.
- **P2** — `pytest-xdist` (needed for the documented gate's `-n 4`) is
  likewise undeclared anywhere in `pyproject.toml`. Same fix shape,
  possibly the same commit as P1.
- **P3** — root `run-a518e33a75507207633f864ba6a864b1` (the testphase
  root `RESULTS.md` documents as continued via `deepreason continue
  --budget cycles=2`) now carries 2 `module_fingerprints` payloads in
  its log, where
  `tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
  asserts exactly 1 per stamped root
  (`ValueError: too many values to unpack`). Root-caused, not yet
  diagnosed which side is wrong (continuation re-stamping vs. the
  test's single-stamp assumption) — ready for
  `deepreason-orchestrator` to pick up via `dr-diagnose`.

None of these were fixed in this tranche; each has a reproduce command
and a fix-shape sketch in `PARKED.md` for whoever picks it up next.

This closes Rung S1 only. `docs/proposals/ROLE_SEAT_SEPARATION_PLAN.md`
names Rung S2 (seat binding design) as the next rung in the program —
it is not started, referenced for design, or scoped by this delivery.
