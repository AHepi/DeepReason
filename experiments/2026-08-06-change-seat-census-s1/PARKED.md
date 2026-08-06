# Parked — found during Rung S1 (seat census), not fixed

Per this tranche's R10: anything broken noticed while reading call
sites is recorded here, never fixed in a MEASURE-ONLY tranche. Each
entry is meant to be handed to `deepreason-orchestrator` / `dr-set-goal`
directly.

## P1 — `jsonschema` is an undeclared test dependency

**Where found:** step 9, running `python tools/docs_verify.py` (full
mode) for the first time in this container.

**What's broken:** `tests/test_schema_carries_every_prose_rule.py`
imports `jsonschema` directly (`import jsonschema` inside
`test_alias_bearing_fields_name_their_legal_values_in_the_schema`), but
`jsonschema` appears nowhere in `pyproject.toml` — not in
`dependencies`, not in `[project.optional-dependencies].dev`, not in
any other extra. A fresh container that runs
`pip install -e ".[dev]" --break-system-packages` (the declared dev
install) still fails this test with
`ModuleNotFoundError: No module named 'jsonschema'`, because the
package was never listed anywhere pip would see it.

**Reproduce:**
```
pip install -e ".[dev]" --break-system-packages -q
python -m pytest tests/test_schema_carries_every_prose_rule.py::test_alias_bearing_fields_name_their_legal_values_in_the_schema -q
# ModuleNotFoundError: No module named 'jsonschema'
```

**Ready-to-run fix shape (not performed here):** add `jsonschema` to
`pyproject.toml`'s `[project.optional-dependencies].dev` list (it sits
next to `pytest>=8.0` and `ruff>=0.4`), one line, no `src/` change.
`dr-set-goal` can scope this directly: "the dev extra is missing a
dependency a committed test imports, causing that test — and every
`docs/map/` check that runs it — to fail on any fresh container that
follows the documented install path."

**Not fixed here because:** this tranche is MEASURE ONLY (R1: no
`src/` change; this is a `pyproject.toml`/dependency-declaration
change, out of scope by the same "no code changes" spirit even though
it is not literally under `src/`) and the census's own acceptance
(docs_verify 0 failed) only required the package to be INSTALLED in
this session, which was done as an environment-completion step (see
CHECKLIST.md step 9), not a repository change.

## No other defects surfaced

Reading all 44 call sites, `select_lease`, `EndpointLease`, `Route`,
`ProviderProfileV1`, `preparation.py`'s role-copy mechanism, and
`cli/doctor.py`'s qualification battery (CENSUS.md, `docs/map/
CON-seats.md`) turned up one genuine mechanism worth flagging as a
design nuance — the v6 per-`(role, seat, endpoint_id)` presentation
resolution already reached by `resolve_route_seat_base_profile` — but
that is a measured FACT for Rung S2 to spend, not a defect; it is
recorded in `CON-seats.md`'s "Traps" section and the M42/M44 table
rows, not here.
