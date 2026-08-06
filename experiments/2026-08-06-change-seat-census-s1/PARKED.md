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

## P2 — `pytest-xdist` is an undeclared dependency of the documented gate

**Where found:** `dr-validate-change` phase, running the project's own
documented gate command (CLAUDE.md: `pytest tests/ -q -n 4`).

**What's broken:** `-n 4` requires `pytest-xdist`, which — like P1's
`jsonschema` — appears nowhere in `pyproject.toml` (`dependencies`,
`[project.optional-dependencies].dev`, or any other extra). A fresh
container that runs the documented `pip install -e ".[dev]"` gate
setup cannot run the documented gate command at all:
```
$ python -m pytest tests/ -q -n 4
ERROR: usage: python -m pytest [options] [file_or_dir] [file_or_dir] [...]
python -m pytest: error: unrecognized arguments: -n 4
```

**Ready-to-run fix shape:** add `pytest-xdist` to `pyproject.toml`'s
`[project.optional-dependencies].dev` alongside `pytest>=8.0` (same
fix shape as P1; likely worth one requirement/commit covering both).

**Not fixed here:** same reasoning as P1 — out of this MEASURE-ONLY
tranche's scope; installed into this session only
(`pip install pytest-xdist --break-system-packages`) to run the gate.

## P3 — a continued root now carries 2 module-fingerprint stamps; the regression test assumed exactly 1

**Where found:** `dr-validate-change` phase, full gate run
(`pytest tests/ -q -n 4`), pre-existing failure — this tranche made
zero `src/`/`tests/` changes (confirmed: `git diff --stat
7a6d1cdb..HEAD -- src/ tests/` is empty), so the failure predates and
is unrelated to the census.

**What's broken:**
`tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
does `(payload,) = recorded_module_fingerprints(harness)` for every
stamped root, asserting exactly one module-fingerprint payload per
root. Root `experiments/2026-08-05-testphase-live-validation/
home-testphase/runs/run-a518e33a75507207633f864ba6a864b1` — the one
`experiments/2026-08-05-testphase-live-validation/RESULTS.md`
documents as continued via `deepreason continue --budget cycles=2`
(2026-08-06 segment, point 5) — now carries 2:
```
$ python3 -c "
from tests.test_module_fingerprints import _sweep_committed_roots
from deepreason.harness import Harness
from deepreason.module_events import recorded_module_fingerprints
unstamped, stamped, _ = _sweep_committed_roots()
for root in stamped:
    payloads = recorded_module_fingerprints(Harness(root, read_only=True))
    if len(payloads) != 1:
        print(root, len(payloads))
"
experiments/2026-08-05-testphase-live-validation/home-testphase/runs/run-a518e33a75507207633f864ba6a864b1 2
```
Reproduce the test failure directly:
```
python -m pytest tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after -q
# ValueError: too many values to unpack (expected 1)
```

**Ready-to-run fix shape (not diagnosed further here — MEASURE-ONLY
scope and out of this rung's call-site focus):** either (a) the
continuation path re-emits a `module_fingerprints` stamp it should
only emit once per run (a `src/` fix, likely in the continuation/
resume path near rung 4's stamping logic), or (b) the test's "exactly
one" assumption is wrong for a continued run and should tolerate N>=1
appearances / assert the LAST one (a `tests/` fix) — `dr-diagnose`
should determine which before `dr-propose-fix` picks a side. This is
exactly the shape `deepreason-orchestrator`'s workflow exists for.

**Not fixed here:** out of this MEASURE-ONLY tranche's scope (R1); it
is also a genuine append-only-record/stamping question, not a
call-site question, so belongs to `deepreason-orchestrator`, not a
future seat rung.

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
