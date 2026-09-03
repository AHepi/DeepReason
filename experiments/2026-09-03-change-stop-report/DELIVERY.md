# Delivered: the stop report — the harness writes the first failure report

Branch: `claude/executor-stop-report-paiagc` (pushed, tree clean)

## What changed

The harness now writes the first account of any failure itself, from the
record, and the diagnosis workflow will not proceed without it.

`deepreason stop-report <run-root-or-home>` is a new read-only command. It
prints, in Markdown or JSON: what actually ran per seat (model, profile,
the reasoning knob as sent, caps, timeouts, split protocol, every gate as
compiled with the six fields the manifest does not carry marked as
restored from notices); what the pre-run qualification check already knew,
per seat × form; provider health per seat with faults by kind and the
provider's own 429 text; **the stop classified into four boxes —
CONFIGURATION, ENVIRONMENT, MODEL, HARNESS — ranked by evidence, each
saying what supports it and what rules it out**; and whether `continue` or
`amend` would be accepted today. It asserts no defect, and HARNESS is
claimable only when the other three are ruled out with cited evidence.

New code: `src/deepreason/application/stop_report.py` (all logic; the CLI
is thin dispatch, because clients may not construct a `Harness`),
`tests/test_stop_report.py` (18 tests including one fixture per box), and
the subcommand in `src/deepreason/cli/main.py`. `deepreason results` is
untouched.

`.claude/skills/dr-diagnose/SKILL.md` now opens with "Step 1 — run the
stop report", requires its section 4 pasted verbatim at the top of
DIAGNOSIS.md, gates on `grep -q "THE STOP, CLASSIFIED" DIAGNOSIS.md`, and
carries an outlet for each prohibition. `dr-drive-harness` §5 lists the
report as the first instrument to reach for.

`docs/map/CON-configuration-stages.md` is the one-page answer to "how does
configuration work": the four stages a setting passes through — your file,
the compiled manifest, run-time restoration from notices, what the seat
receives — each with the command that reveals it, and seven traps stated
flatly.

**Proven against your own recorded failures.** The report was run over
eight failures across three branches, alongside the classifier it replaces
(read the settings, blame the seat the stop message names): **shipped 8/8
correct, naive 1/8, 7 misfiled.** The naive reader blames the MODEL on
P-A1 — the exact window you caught — whose `conjecturer#0` had passed
`conjecturer.turn.v6` 20/20 first-pass with 0 repairs.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | one command, read-only, deterministic, Markdown + JSON | done | `72046a17b4`, VALIDATION S1/S2/S11 |
| R2 | every line from the record; YAML only for a diff | done | `72046a17b4`, VALIDATION S3 |
| R3 | §1 WHAT ACTUALLY RAN, per seat + gates + embedder | done | VALIDATION S4 — 6 gates, `omitted → provider default`, embedder named |
| R4 | §2 PRE-RUN CHECK, per seat × form, cached digest named | done | VALIDATION S5 |
| R5 | §3 PROVIDER HEALTH, faults, 429 with provider message | done | VALIDATION S6 |
| R6 | §4 four boxes with typed evidence | done | VALIDATION S7 |
| R7 | CONFIGURATION box and its four probes | done | VALIDATION S9 |
| R8 | ENVIRONMENT box | done | VALIDATION S6; regression P-A2 epoch 2, phase-1 429 |
| R9 | MODEL box; **say so if the seat passed 20/20** | done | VALIDATION S8 |
| R10 | HARNESS box, only when the others are ruled out | done | VALIDATION S7; regression P-A2 epoch 3 |
| R11 | never assert a defect; rank and say what is ruled out | done | `test_report_never_asserts_a_defect` |
| R12 | §5 CONTINUABILITY | done | VALIDATION S10 |
| R13 | amend dr-diagnose and dr-drive-harness | done | `d23eb93b69`, VALIDATION S13/S14 |
| R14 | cite a report line, or stop | done | the GATE + outlet table, VALIDATION S13 |
| R15 | follow authoring-skills; quote the incident | done-with-assumption **A7** | rule + GATE in the skill; your words in `docs/ERRATA_EXECUTOR.md` X12 |
| R16 | a CON- page with re-runnable checks | done | `d23eb93b69`, VALIDATION S15 |
| R17 | the traps stated flatly | done | all seven, VALIDATION S16 |
| R18 | run against the named roots, right box, evidence quoted | done-with-assumption **A8** | 8/8; three of the six named roots do not exist — see below |
| R19 | show a naive version RED, the shipped one GREEN | done | `1a47f85fc2` — NAIVE 1/8, SHIPPED 8/8 |
| R20 | a unit fixture per box | done | `b39b395b2f`, VALIDATION S19 |
| R21 | update wheel-smoke pins in the same commit | done | `e158121de2` — no pin moved; verified by running |
| R22 | full gate 0 failed; baselines recorded not stopped on | done | **4707 passed, 6 skipped, 0 failed** |
| R23 | the map moves in the SAME commit | done | `d23eb93b69` carries code and map together |
| R24 | DELIVERY.md reconciles requirement by requirement | done | this table |
| R25 | no tracked file carries a credential | done | scanned before the first commit; zero hits |
| R26 | a new subcommand, not a flag on `results` (Amendment 1) | done | `ff77e805e8` |
| R27 | rootless mode in scope (Amendment 1) | done | three source kinds; VALIDATION S12 |
| R28 | one tranche, two commit groups (Amendment 1) | done | Group A steps 1-15, Group B 16-20 |
| R29 | ceiling raised to 2100 (Amendment 2) | done | diff_budget 1905 WITHIN |

No `not-done` rows. No `deferred` rows.

## Assumptions the operator may override

- **A1** No new record kind was needed — every section reads fields that
  already exist, so no frozen surface was touched.
- **A2** Nothing writes into a root — proven, not promised.
- **A3** Report logic in `application/`, CLI thin. Forced by an existing
  architecture test.
- **A4** The report reads the STORED `verify_root` verdict by default and
  re-derives only on `--verify`, mirroring `deepreason results`.
- **A5** "Deterministic" means byte-identical output for the same root and
  flags; the report carries no timestamp of its own.
- **A6** The instruction said "39 RemoteDisconnected"; the instrument
  counts **41**, on one endpoint as stated. Bound at the measured number.
- **A7** The instruction said to quote the incident in the skill;
  `authoring-skills` W5 forbids incident stories in instructions and names
  ERRATA as where history lives. Split rather than decided: the rule and
  its GATE are in the skill, your verbatim words are in
  `docs/ERRATA_EXECUTOR.md` X12.
- **A8** Three of the six roots named for the regression produced **no run
  root at all** (they died during qualification), and a fourth is a clean,
  completed run rather than an environment failure. Delivered the property
  — every box demonstrated on committed evidence — rather than the literal
  naming, and made the report cover rootless failures so those three are
  still tested.

## Map delta

- **created:** `docs/map/CON-configuration-stages.md`
- **changed:** `docs/map/INDEX.md` (one concept row, two routing rows),
  `docs/map/SUB-application.md` (the new module's entry-point block)
- **new checks:** 4 (two in the new document, one in `SUB-application.md`,
  plus the yaml-reachability AST assertion shared with the test suite) —
  each would go red if the behaviour regressed
- **not changed, deliberately:** `docs/map/SUB-periphery.md` — it owns
  `mcp_server.py`, not `cli/`, and no MCP tool was added
- **left stale:** `SUB-application.md` still shows commits since its
  `Verified-at:`. Deliberate: this tranche did not re-run that document's
  full `Verify:` line (five pytest files), and a false stamp is worse than
  an honest one.
- **map gates:** `--links` 0 dangling over 75 documents; `docs_verify` 3
  failed and `--audit` 1 finding, every one matched by name to a recorded
  baseline in `docs/AUDIT_BASELINES.md` (lines 67, 68, 90) and none in a
  document this tranche touched.

## Errata

`docs/ERRATA.md`: **errata: none** — no committed ordinary document was
found to be wrong.

`docs/ERRATA_EXECUTOR.md`: **X12 added** (the process ledger, whose scope
is `.claude/skills/`). It records that no infrastructure document required
a diagnosing window to derive its first account from the record, quotes
your words verbatim as the authority, carries the P-A1 qualification row
that contradicted the window, and prices the old reading style at NAIVE
1/8 vs SHIPPED 8/8.

## Parked (not done, not promised)

**P1 — the six engine-config fields the manifest does not carry.** The
structural cause underneath this whole tranche. The report now MARKS them;
carrying them is frozen surface 4 and needs your grant. Ready-to-send
prompt in `PARKED.md`, prices three roads and requires the grant be
requested in SPEC.md before any code.

**P2 — the installed-wheel operational smoke fails at
`continuation_resume`.** Measured pre-existing: it fails identically at
the tranche base, which carries none of this work. No gate runs this
smoke, so nothing else will catch it. Ready-to-send prompt in `PARKED.md`.

**P3 — the tranche instruction's own root inventory was written from
narrative, not from `git ls-tree`.** Recorded, deliberately without a
prompt: the remedy would be an `authoring-skills` rule, and that skill
requires two recorded instances before a rule is written. This is one.

**Recommended next: P2.** It is the only one of the three that is a live
defect in a shipped instrument, it is invisible to every gate, and it sits
on the path to the next release. P1 is bigger and needs a frozen-surface
grant from you before it can start.
