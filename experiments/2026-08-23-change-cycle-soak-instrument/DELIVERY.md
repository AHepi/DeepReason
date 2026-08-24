# DELIVERY — offline cycle soak instrument

R-by-R reconciliation against REQUEST.md. Every row cites the artifact or
pasted output that discharges it.

| R | requirement | disposition | evidence |
|---|---|---|---|
| R1 | the motivating record: four deaths, four typed causes | **verified, not assumed** | REQUEST.md R1 table quotes all four `run-status.json` records; all four are `state=failed`, `stop_reason=operational_failure`, at cycles 0–2 |
| R2 | drive the managed path to cycle 8+ on THIS config's shape | **done** | `scripts/cycle_soak.py`; `--cycles` defaults to 8 |
| R3 (S1) | script in `scripts/`, real config, parameterized, epoch-3 first, one run path, N cycles, typed terminal + `verify_root` + no `operational_failure`, reuse the smoke's stub | **done** | `CASES` with `epoch3` default and `reach-rich` second; config READ from the committed `run-config.yaml`; drives `TextRunApplicationService.start_manifest_run`; A1–A4; stub imported from `wheel_operational_smoke` — no second stub minted |
| R4 (S2) | four death shapes become assertions, failing by NAME | **done** | `SEAMS` tuple: each seam carries `reached_by` AND `fatal_messages`/`fatal_objects`; coverage table printed and written per run |
| R5 (S3) | no pytest gate; joins the wheel smokes; `AUDIT_BASELINES.md` entry; one line in `dr-drive-harness` preflight; same sentence in `CLAUDE.md` — same commit | **done** | `grep -rn cycle_soak tests/` empty; three doc edits in the same commit as the script |
| R6 (S4) | row a non-reproducible seam as not-coverable with the reason | **done, and exercised** | D1 rows `partial` by default with its reason; RESULTS.md additionally weakens the D2 and D3 green ticks rather than leaving them to read as full coverage |
| R7 | drive the adapter code, do not modify it; expect D4 red; mark expected-red rather than skip | **honoured** | `EXPECTED_RED` names D4; it is reported on every run, never skipped; exit 3 distinguishes it from a real regression; zero `src/` files changed |
| R8 | stop if adapter/transaction code needs editing | **triggered once, honoured** | the induced probe surfaced P1 in adapter/transaction territory; PARKED, not fixed, with a ready-to-send prompt |
| R9 | ring while iterating, full gate at boundary, docs_verify full, map in same commits, push every phase | **done** | see VALIDATION.md |
| R10 | deliver R-by-R with pasted proof and a closing line | **this file + the chat reply** | |
| R11 | setup | **done** | `pip install -e .` and test deps installed; `python -m pytest` used throughout |

## What was NOT done, and why

- **Exit 0 has never been observed.** The soak's recorded baseline is exit 0,
  but every deep run dies on D4, so the value is specified and not measured.
  RESULTS.md says so; it closes when the parallel window's fix lands.
- **D3's denial path is not exercised.** The runs set no finite token budget,
  so the authorization path is covered and the denial that follows it is not.
  `--token-budget` would reach it; not run for this segment.
- **D2's "with tuning" half is not exercised.** No logged controller adjusted
  `max_tokens` during these runs, so the soak proves the lease is checked, not
  that it survives tuning.
- **The `reach-rich` case was not run**, only defined.

## Deviations recorded

Both in REQUEST.md under "Recorded deviations": the branch
(`claude/cycle-soak-instrumentation-8e0vp7`, per this window's directive) and
the repository (`AHepi/DeepReason`, whose `main` head is the `5d9b995ce` the
request names — the window opened on `AHepi/Poietics`, where no anchor in the
request exists on any ref). Both were put to the operator and answered before
any work landed.
