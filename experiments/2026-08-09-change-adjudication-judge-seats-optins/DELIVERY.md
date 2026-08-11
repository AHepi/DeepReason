# Delivered: adjudication / judge-seats / legacy-criticism / schools opt-ins
Branch: `claude/adjudication-judge-seats-optins-4nb7ov` @ `5ad698e27` (pushed,
tree clean before this commit)

## What changed

Four independent opt-ins were added, every one defaulting to today's
behavior byte-identical unless explicitly turned on. **Adjudication**
(`ADJUDICATION_STATUS_AUTHORITY_ENABLED`): whether a judge's ruling can
actually change a piece of work's status, versus only recording an opinion
(today's default). **Judge seats** (`JUDGE_SEATS_ENABLED` +
`JUDGE_SUMMONS_PER_CYCLE`/`JUDGE_SUMMONS_COOLDOWN`): judges never spend a
token unless explicitly enabled, with a config-based throttle and a
setup-time evidence warning about measured judge biases. **Legacy
criticism** (`LEGACY_CRITICISM_ENABLED`): a real, rebuilt v6 dispatch path
("Road E") that lets criticism run without any school grouping at all —
per your own later instruction, this became the *new default* partway
through this tranche. **Schools as opt-in seats**, split per your
correction into two fully independent CLI levers: `--school-seat` (a
school's idea-generation route) and `--criticism-seat` (a school's
criticism route) — using one never implies or requires the other. A fifth,
smaller piece: `signals_read.py`, a read-only summary that pulls existing
signals (recent config critiques, deferred work, token spend) into one
typed view, wired into the existing verification report.

One real regression was found and fixed during final validation: the new
legacy-criticism default was being wrongly flagged as a security problem
by a safety check that hadn't been told about the new dispatch shape —
found live via the installed-wheel operational smoke test, fixed, and
covered by two new regression tests (commit `b9638f3ff`).

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Adjudication: Opt in." | done | Part C; VALIDATION.md acceptance checks |
| R2 | "Judge seats: opt in." | done | Part D; `JUDGE_SEATS_ENABLED` defaults off |
| R3 | "Optional legacy criticism paths: opt in." | done | Part B/A; `LEGACY_CRITICISM_ENABLED` |
| R4 | "I need to know why they were disconnected" | done | SPEC.md §1(a)-(c), delivered pre-code |
| R5 | "schools need to be opt in seats as well" | done (superseded shape, see R27) | Part E |
| R6 | judge "dormant... summoned... doesn't need to be active" | done-with-deferral | dormant+starvable shipped (Part D); live standoff-summons wiring explicitly deferred, Amendment 5: "the standoff-summons wiring is its own later tranche, NOT this one" |
| R7 | "configuration machinery to starve the judge" — verify | done | SPEC.md §1(d) — established absent (research only) |
| R8 | "function that checks the config... sends a config recommendation" — verify | done | SPEC.md §1(d) — found LIVE (`config_referee`), no code needed |
| R9 | "if these functions... are dead... workflow needs a makeover" | done (conditional not triggered) | SPEC.md §1(d) split verdict — `config_referee` live, so the conditional's own terms were not met |
| R10 | "starving the judge... doable in config" | done | Part D throttle fields |
| R11 | "built in signals to detect active judges" — verify | done | SPEC.md Amendment-3 addendum finding (research only) |
| R12 | "single model two judge seats should be possible" | done | Part D2, `--blind-same-model-judges` |
| R13 | "trace the code for criticism before schools... switched back on" | done | Road E, Part A (Steps 1-15) |
| R14 | (task issuer's framing) static/mint-time gates only | done | honored throughout; no mid-run signal consumption added anywhere |
| R15 | signal abstraction, static form only | done | Part F, `signals_read.py` |
| R16 | `run_manifest.py` pop-line grant | done | VALIDATION.md Frozen surfaces — exactly the granted pop-lines |
| R17 | "grant is not transitive" | done | process constraint, honored |
| R18 | dr-execute-step then dr-validate-change, STOP after VALIDATION.md | done | this delivery follows a PASS VALIDATION.md |
| R19 | "a clean separation between school and criticism" | done | Part A, S13i self-sufficient dispatch |
| R20 | "they still need to interact" | done | school-routed path byte-identical throughout Part A |
| R21 | "separation... need to exist" (without weakening the scheduler boundary) | done | Step 13's AST check, re-affirmed by the full gate |
| R22 | "judge seat assignment needs to be without restriction... same model grading its own answer... should mint" | done | Part D2, content-blind same-model substitute |
| R23 | "Observe only should also be an optional config." | done | untouched; still the default authority path |
| R24 | blindness is the actual guarantee, not family/school diversity | done | S15/S16, pinned invariant test |
| R25 | "needs to be exposed to CLI... Otherwise it's not a setting" | done | `--blind-same-model-judges` on `deepreason config compile` |
| R26 | "Yes. School opt in. But for both criticism and conjecture." | superseded by R27 | see ERRATA.md E18 |
| R27 | "School and criticism should be separate... always separate from the conjectures" | done | Part E's two independent levers, `--school-seat`/`--criticism-seat` |
| R28 | "Legacy, not schools, should be default for criticism." | done | Part B2, default flip |

No R is `not-done`.

## Assumptions the operator may override

A1: The four (now five, after R27) opt-ins are independent `Config`
booleans, not one unified flag — smallest-reasonable reading of the
operator listing them as separate sentences; every later amendment
reinforced independence as the actual intent.

A2: "The two assignable seats" = `conjecture` + its `simulation` alias;
`coder`/`scratch` are dead weight (resolved from the record, Half 1(a)).

A3: "Legacy criticism paths" resolved to exactly one true
legacy-superseded pair (Road E's subject) — no second opt-in surface
needed beyond the adjudication flag and `LEGACY_CRITICISM_ENABLED`.

A4: The decision-sheet forks (§5.1, §5.4, §5.5) are resolved per the
operator's binding approval (Amendment 5) — Road A / Road A-with-Road-B /
Road B respectively.

## Map delta

changed: `CON-authority.md`, `CON-schools.md`, `CON-seats.md`,
`SEAM-adjudication-x-authority.md`, `SEAM-llm-x-rules.md`,
`SEAM-manifest-x-schools.md`, `SEAM-rules-x-workflow.md`,
`SEAM-scheduler-x-rules.md`, `SEAM-scheduler-x-workflow.md`,
`SUB-scheduler.md`, `SUB-verification.md`, `SUB-workflow.md`
created: none — no new subsystem/seam warranted its own document; the one
candidate (`signals_read.py`) is documented inside `SUB-verification.md`
instead (its only wired-in consumer today)
new checks: 4 (document count unchanged at 53; check count `851 → 855`
across this tranche's own progression, confirmed in `CHECKLIST.md`'s own
step proofs)
left stale: all 12 of the above (plus 30 more, stale from this same
tranche's earlier parts) have their `Verified-at:` stamps unbumped, though
every check in every one currently passes (`docs_verify` full: 855 checks,
0 failed) — dismissed with that reason in VALIDATION.md's Map section, per
this skill's own rule that validation may not edit the map documents it
validates. A single stamp-bump follow-up commit is recommended (zero
content risk) but not done here.

## Errata

Two entries added this delivery, `docs/ERRATA.md` **E18** and **E19**:
- E18: Amendment 10's "and" reading of the schools opt-in (R26,
  `config.py`'s original `SCHOOL_SEATS_ENABLED` comment) was recorded as
  confirmed, then found too coupled and corrected by Amendment 11 (R27).
- E19: `CHECKLIST.md`'s step-3 STOP priced Road A/Road B for the
  school-free criticism circuit; neither shipped — Amendment 7 (R19)
  directed a third shape instead. Already self-corrected in place in
  `CHECKLIST.md`; E19 is a pointer so a reader scanning ERRATA finds it
  without reading the whole file.

## Parked (not done, not promised)

Three findings from `PARKED.md`, none fixed here, each with a ready-to-send
next-tranche prompt:

1. **`test_bronze_report.py::test_census_totals_internally_consistent`
   fails** (`159 == 165`), confirmed pre-existing (reproduces identically
   against this tranche's true base commit in an isolated worktree).
   Next-tranche prompt: *"Diagnose and fix
   `test_bronze_report.py::test_census_totals_internally_consistent` —
   `scripts/bronze_census.py::build_census()`'s gate-measure accounting
   disagrees with itself (159 vs 165) over the committed
   `experiments/bronze_flat_2026-07-13/` roots. Confirmed pre-existing as
   of commit `81d08e5f0`; not caused by any later tranche."*

2. **`tools/root_sweep.py` hangs indefinitely** on
   `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03`
   — confirmed via `strace` to loop on repeated `ENOENT` object-path
   probes on an otherwise ordinary-sized root (508 log lines, 5.2MB).
   Next-tranche prompt: *"Profile `verify_root_report`/the content-
   addressed object-store lookup path against
   `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03`
   specifically — `tools/root_sweep.py` hangs indefinitely on this one
   root (killed after 1h37m at ~100% CPU, no progress). Likely a
   pathological linear type-guessing scan; may affect other roots with a
   similar content shape."*

3. **Transient MCP-thread test flakiness** (5 tests in `test_mcp_run.py`/
   `test_mcp_scratch_bridge.py`, `thread.join(timeout=5)` under parallel
   load) — not filed as a tracked defect, recorded only so a future
   session recognizes it instantly. No prompt offered; revisit only if it
   recurs reliably.

recommended next: **item 1** (the bronze-census failure) — it is the only
one of the three that is an actual FAILING test in the standing gate today,
so it is the one most likely to cause confusion for the next tranche that
runs the full suite and sees red.
