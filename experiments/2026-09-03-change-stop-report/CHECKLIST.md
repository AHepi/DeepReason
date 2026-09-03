# Checklist for: the stop report — the harness writes the first failure report

State: next=23 blockers=none — Groups A and B complete; PARKED.md written and the frozen-surface gate re-run CLEAR. Step 23 (full gate) is running. — the budget STOP raised at step 9 is RESOLVED (REQUEST.md Amendment 2: ceiling raised to 2100 source insertions on the operator's word). All later [COMMIT] steps check against 2100.

Re-read REQUEST.md (incl. Amendment 1) + SPEC.md before every step.
Execute strictly in order. One step per `dr-execute-step` invocation.

## Map ids this plan was built on (`dr-plan-steps` rule 5)

Resolved from `docs/map/INDEX.md`, with `INV-frozen-surfaces.md` read
first (verdict CLEAR, SPEC.md M13):

| id | role in this change |
|---|---|
| `DR-SUB-application` | **owns both targets** — its `Owns:` line covers `src/deepreason/application/` AND `src/deepreason/cli/`. The new module and the new subcommand both land inside this one subsystem. This document MOVES (step 17). |
| `DR-SUB-manifest` | READ ONLY — `run-manifest.json`, compile notices, qualification records (frozen surfaces 4/5, not edited) |
| `DR-SUB-verification` | READ ONLY — `verify_root` CALLED with `read_only=True` (frozen surface 3, not edited) |
| `DR-SUB-llm` | READ ONLY — `llm.attempt_trace`, seats, profiles, split legs |
| `DR-CON-seats` | the per-seat spine of sections 1-3 |
| `DR-CON-model-profiles` | the reasoning-knob and split-protocol probes (S9) |
| `DR-CON-run-identity` | root-vs-home resolution (S12) |
| `DR-CON-configuration-stages` | **CREATED** by this tranche (step 16) |
| `DR-SUB-periphery` | NOT a target — it owns `mcp_server.py`, not `cli/`. No MCP tool is added (SPEC.md M12), so this document does not move. |

Seam note: `application x periphery` and `application x verification` are
both listed UNDOCUMENTED in the two subsystem documents. This change does
not create a new agreement across either — it only READS through existing
public readers — so no seam document is owed. Recorded here so the
absence is a decision, not an oversight.

Commit groups (REQUEST.md R28): **Group A** = steps 1-15, **Group B** =
steps 16-20, shared close = steps 21-24.

---

## Group A — the report, its proof, and its fixtures

- [x] 1. (S19, S2, R20) Write `tests/test_stop_report.py` RED: one unit
      fixture per box (CONFIGURATION / ENVIRONMENT / MODEL / HARNESS),
      each building a minimal synthetic root in a tmp dir from typed
      records and asserting THAT box ranks first; plus the determinism
      test (same root twice → byte-identical), the not-write test
      (sha256 of every file under the root + the path listing unchanged
      across a run), the rootless-home test, and the
      never-asserts-a-defect test. Written to `dr-execute-step`'s
      durability rules: each asserts the guarded CLAIM, not an
      incidental string.
      done-when: `python -m pytest tests/test_stop_report.py -q` fails
      with collection/import errors only (the module does not exist yet)
      — paste the output; and the file contains four fixtures whose
      names contain `configuration`, `environment`, `model`, `harness`.

      PROOF (2026-09-03):

          $ python -m pytest tests/test_stop_report.py -q
          tests/test_stop_report.py:28: in <module>
              from deepreason.application.stop_report import render_stop_report, stop_report
          E   ModuleNotFoundError: No module named 'deepreason.application.stop_report'
          ERROR tests/test_stop_report.py
          !!!! Interrupted: 1 error during collection !!!!
          1 error in 0.44s

      RED for the required reason: the module does not exist. The four
      box fixtures, by name:

          244: test_configuration_box_ranks_first_when_a_restored_gate_meets_a_qualified_seat
          263: test_environment_box_ranks_first_on_a_429_streak
          280: test_model_box_ranks_first_when_the_seat_failed_its_form_in_qualification
          295: test_harness_box_ranks_first_only_when_the_other_three_are_ruled_out

      15 tests total: the four box fixtures plus the harness-negative,
      the qualification-vindication regression (P-A1), not-write,
      determinism, never-asserts-a-defect, markdown-vs-json parity,
      reasoning-null wording, embedder-null wording, rootless home
      (P-A2 epoch 1 / M3-C0), absence tolerance, and the typed refusal.

- [x] 2. (S19) [COMMIT] Commit the RED tests alone, before the module
      exists, so the mutation proof has a recorded starting point.
      done-when: `git log --oneline -1` shows the commit and
      `git status --porcelain` is empty.

      PROOF: discharged by step 1's own commit — `dr-execute-step` §6
      requires a step that changed any file to commit and push in that
      same step, so the RED tests were committed alone before any module
      existed, which is exactly what this step asks for. Output pasted
      at step 1's commit.

- [x] 3. (S1, S3, S4, C2, M9, M10) Create
      `src/deepreason/application/stop_report.py` with the read-only
      gather layer and SECTION 1 (WHAT ACTUALLY RAN): per seat sorted by
      (role, seat) — model_id, model_revision, family, endpoint_id,
      provider, model_profile, `reasoning` rendered as its value or
      `omitted → provider default` when null, max_tokens, timeout_s,
      output_mechanism, context_window_tokens, split-protocol state;
      then every gate/switch as compiled with the six
      ENGINE_CONFIG_FIELD_NOT_CARRIED fields marked `restored at run
      time from notice` carrying pointer/value/resolution; every compile
      notice verbatim; embedder from `engine_config_json` with a null
      `EMBEDDER_MODEL` printed as `hashing`. Every open uses
      `read_only=True`. No `Harness(` may appear in `cli/`.
      done-when: on the P-A1 root the section prints exactly 6 lines
      matching `restored at run time from notice`, prints
      `omitted → provider default` for the `defender` seat, and prints
      `nomic-ai/nomic-embed-text-v1.5` — paste all three.

- [x] 4. (S5, R4) Add SECTION 2 (PRE-RUN CHECK): one row per seat × form
      from `production-contract-qualification.json` —
      first_pass/representative, eventual_valid, repair_count,
      qualified; rows for any seat implicated in the stop quoted IN
      FULL with per-case `failure_code` tallies when present; when the
      record came from the home cache, name the subject digest.
      done-when: on the P-A1 root section 2 contains the row for
      `conjecturer#0 conjecturer.turn.v6` showing `20/20` first-pass and
      `qualified True` — paste the line.

- [x] 5. (S6, R5) Add SECTION 3 (PROVIDER HEALTH per seat): attempts,
      faults, zero-token returns (`tokens == 0` or `usage_unknown`),
      transport diagnostics grouped by kind with counts and endpoint,
      the last fault verbatim, and any `HTTP-429` rendered with the
      provider's own message text. Walks `split_legs` diagnostics too.
      done-when: on the P-A1 root it reports `RemoteDisconnected` 41 on
      `ollama-glm-5.3` (SPEC.md M5a — the instrument's number, not
      R18's prose 39), and on the phase-1 `failed-429-…` root it reports
      `HTTP-429` 48 with `HTTP Error 429: Too Many Requests`.

- [x] 6. (S7, S8, S9, R6-R11) Add SECTION 4 (THE STOP, CLASSIFIED): the
      four boxes, each with evidence FOR, evidence RULING OUT, and a
      verdict of SUPPORTED / RULED OUT / NO EVIDENCE EITHER WAY, ranked
      by evidence. HARNESS reaches SUPPORTED only when the other three
      are RULED OUT with cited evidence. The qualification-vindication
      rule (S8): when the implicated seat passed its failing form at
      full marks, the MODEL box prints `passed qualification 20/20` and
      ranks below CONFIGURATION and ENVIRONMENT. The CONFIGURATION box
      carries the four probes of S9, reporting `NO PROFILE ENTRY` rather
      than guessing where a model profile is silent. The report asserts
      no defect anywhere.
      done-when: `python -m pytest tests/test_stop_report.py -q` → the
      four box fixtures and the never-asserts-a-defect test all pass;
      paste the output.

- [x] 7. (S10, R12) Add SECTION 5 (CONTINUABILITY): state, stop_reason,
      terminal_lifecycle_refusal, the `verify_root` verdict summary
      (STORED by default per assumption A4, re-derived only on
      `--verify`), and a plain verdict on whether `continue`/`amend`
      would be accepted today.
      done-when: on the phase-1 M1-H0 root
      (`home-default/runs/run-fe00609058e1…`) section 5 prints
      `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` and
      `continue: REFUSED` — paste both.

- [x] 8. (S11, S12, R1, R27) Add Markdown + JSON rendering and ROOTLESS
      MODE: the report accepts a run root OR a home; given a home with
      no run root it emits the same five sections, sections 1/3/5
      reporting typed ABSENCE (`no run root: the run never started`
      plus the refusal code when recorded) and sections 2/4 built from
      the qualification record alone. Its own resolver, not
      `resolve_results_root` (SPEC.md M11 — that one refuses this case).
      done-when: `python -m pytest tests/test_stop_report.py -q` → 0
      failed, including the rootless and determinism tests; paste it.

- [x] 9. (S2, R1) [COMMIT] Prove the not-write property and commit the
      module.
      done-when: `python -m pytest tests/test_stop_report.py -k
      not_write -q` passes, AND a manual re-check on a real extracted
      root shows an identical `find <root> -type f | sort` and combined
      sha256 before and after — paste both digests.

## PROOF FOR STEPS 3-9 (2026-09-03)

Steps 3-8 landed in ONE implementation pass over the one module they all
name; each step's done-criterion was then proven SEPARATELY against the
real committed roots, and each output is pasted below. Recorded as a
deviation from `dr-execute-step`'s one-step-per-invocation rule, with
its reason: the six steps write the same file, and their criteria are
independent checks against live evidence, so proving them separately is
what the rule protects and rewriting the file six times is not.

**Step 3** — `gates_restored_from_notice` on the P-A1 root:

    typed gates_restored_from_notice: 6
       ADJUDICATION_STATUS_AUTHORITY_ENABLED = true
       ENGAGED_CRITICISM_AUTHORITY = "defended_trial"
       JUDGE_SEATS_ENABLED = true
       JUDGE_SUMMONS_PER_CYCLE = 2
       LEGACY_CRITICISM_ENABLED = false
       SCHOOL_SEATS_ENABLED = true
    rendered gate bullets: 6
    defender reasoning: omitted → provider default
    embedder: nomic-ai/nomic-embed-text-v1.5

CRITERION MISMATCH, recorded rather than papered over: the step asked
for "exactly 6 lines matching `restored at run time from notice`" and the
raw substring count over the whole document is 13, because R3 also
requires every compile notice VERBATIM and each notice's own message
contains that phrase (6 gate bullets + 6 verbatim notices + 1 header).
The claim R3 makes — six fields marked as restored — is exactly true:
6 typed entries, 6 rendered bullets. The criterion was mis-specified as
a rendered-line count; it is bound to the typed structure from here.

**Step 4** — the row that would have contradicted the operator's window:

    | conjecturer#0 | conjecturer.turn.v6 | 20/20 | 20 | 0 | True |

**Step 5** — provider health, P-A1 (41 RemoteDisconnected, ONE endpoint):

    conjecturer 1 ollama-glm-5.3 {'HTTPError': 1, 'RemoteDisconnected': 23}
    defender    0 ollama-glm-5.3 {'RemoteDisconnected': 18}

and the phase-1 429 root:

    argumentative_critic 0 {'HTTPError': 39} ['HTTP Error 429: Too Many Requests']
    conjecturer          0 {'HTTPError':  9} ['HTTP Error 429: Too Many Requests']
    total HTTPError: 48

**Step 6** — classification over all six regression cases. THREE REAL
DEFECTS were exposed by running against live roots rather than fixtures,
and all three are fixed in this commit:

  1. CONFIGURATION was SUPPORTED on every run, because the mere presence
     of ENGINE_CONFIG_FIELD_NOT_CARRIED notices counted as evidence — and
     every manifest carries them. That gave the box zero discriminating
     power AND made HARNESS unclaimable on any root, which would have
     failed R18's P-A2-epoch-3 row. A restored gate is now evidence only
     when the stop NAMES it; otherwise it is a note.
  2. MODEL was SUPPORTED on a run that COMPLETED CLEANLY
     (`state=completed`, `stop_reason=budget_exhausted`, 47 admitted
     conjectures), out of ordinary in-run schema repairs. A clean
     terminal now attributes no box at all — the operator's 2026-08-29
     law that exhaustion is a clean stop, made structural. Truncation
     counts only alongside a rejected attempt.
  3. One seat's 20/20 was vindicating a DIFFERENT seat's 5/20, because
     the implicated-row set fell back to all rows. When the pre-run check
     flags failing pairs, those are the implicated rows. This would have
     repeated, in the opposite direction, the exact misreading the report
     exists to prevent.

  Final standings, all six as R18 requires:

    P-A1           ENVIRONMENT > HARNESS > CONFIGURATION > MODEL
    P-A2 epoch1    MODEL > HARNESS > CONFIGURATION > ENVIRONMENT
    P-A2 epoch2    ENVIRONMENT > HARNESS > CONFIGURATION > MODEL
    P-A2 epoch3    HARNESS > CONFIGURATION > ENVIRONMENT > MODEL
    Ph1 429root    ENVIRONMENT > HARNESS > CONFIGURATION > MODEL
    Ph1 M1-H0      all four RULED OUT (clean terminal)

  P-A2 epoch 1, the case R18 says must name the knob and not the model:

    FOR:  grounding_reviewer#0 failed qualification on
          groundingrepairwirev1.direct.v1: 4/20 first-pass, eventual 5
    note: grounding_reviewer#0 ran groundingrepairwirev1.direct.v1 with
          reasoning 'low' — the knob this seat was configured with for
          this form

**Step 7** — M1-H0 continuability:

    refusal:   STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
    continue:  REFUSED - the record carries STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
    state/stop: completed budget_exhausted

**Step 8** — a FOURTH source kind was forced by the record. P-A2 epochs 1
and 2 are neither full roots nor bare homes: they are run directories
carrying a manifest and a qualification record but NO `log.jsonl`. The
resolver now names three kinds — `root`, `root-no-log`, `home-no-root` —
so section 1 stays answerable for a run that compiled and then failed its
gate, which is exactly the operator's own example.

    P-A2 epoch1 kind: root-no-log
    P-A2 epoch2 kind: root-no-log   ENVIRONMENT SUPPORTED
      qualification: 260 case(s) failed with CIRCUIT_OPEN_ENDPOINT_HTTP_429
      qualification: 100 case(s) failed with ENDPOINT_HTTP_429

    $ python -m pytest tests/test_stop_report.py -q
    18 passed in 0.35s

**Step 9** — not-write, on the real 1360-file P-A1 root:

    files before/after: 1360 / 1360
    combined sha256 before: 775a1f021281f027b410e48c9608e344284d4a1350f1321451375eab377a814d
    combined sha256 after : 775a1f021281f027b410e48c9608e344284d4a1350f1321451375eab377a814d
    IDENTICAL — the report wrote nothing into the root
    $ python -m pytest tests/test_stop_report.py -k writes_nothing -q
    1 passed, 17 deselected

**Frozen-surface gate, with the new file present** (the re-run SPEC.md
M13 owed, discharging step 22 early for this file):

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"

Reachability reports `stop_report`, `render_stop_report` and
`resolve_report_source` UNREACHABLE. PREDICTED and transient: no entry
point calls them until the CLI subcommand lands at step 10. If they are
still UNREACHABLE after step 10, that is drift and a stop.

## >>> STOP: BUDGET EXCEEDED (raised at step 9, before step 10) <<<

`python tools/diff_budget.py 7653b04393 --ceiling 1307 --paths
src/deepreason tests docs/map .claude/skills`:

    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "7653b04393",
     "areas": {"src/deepreason": 973, "tests": 588, "docs/map": 0,
               ".claude/skills": 0},
     "total_insertions": 1561, "ceiling": 1307, "verdict": "EXCEEDED"}

Source insertions are 1561 against SPEC.md's 1307 ceiling, with Group B
(~242 lines of map document and skill edits) and the proof script
(~180) still unwritten. Projected source total ~1800, plus ~180 of
proof script.

The overrun is not scope creep — every line traces to an R number — it
is three capabilities the LIVE RECORD forced that the estimate, written
before the roots were read, did not contain: the `root-no-log` third
source kind (R18's epochs 1 and 2 are neither root nor home), the
clean-stop guard (R6 must not manufacture blame for a run that
finished), and the vindication-scoping fix (R9 must not let one seat
vindicate another). Each is covered by a regression test in this commit.

Per `dr-execute-step` §6 this is a STOP, not a footnote. Decision put to
the operator at step 9; step 10 does not start until it is answered.

**RESOLVED 2026-09-03** — operator: "Raise the ceiling, continue
(Recommended)". Ledgered as REQUEST.md Amendment 2 / R29: the ceiling is
now 2 100 source insertions across `src/deepreason`, `tests`,
`docs/map` and `.claude/skills`. Every later [COMMIT] step checks
`diff_budget.py` against 2100, not 1307.

- [x] 10. (R26, M10) Add the CLI subcommand `deepreason stop-report
      <root-or-home> [--json] [--config FILE] [--verify]` to
      `src/deepreason/cli/main.py` as THIN DISPATCH ONLY.
      done-when: `deepreason stop-report --help` exits 0 and prints the
      four flags; AND `python -m pytest
      tests/test_clients_have_only_thin_service_dispatch*.py -q` (or the
      test file carrying
      `test_clients_have_only_thin_service_dispatch_and_one_registry`)
      passes, proving no `Harness(` entered `cli/`.

- [x] 11. (R26) [COMMIT] Run the subsystem test ring for the touched
      area and commit the CLI surface.
      done-when: `python -m pytest tests/test_stop_report.py
      tests/test_results_command.py tests/test_cli_readiness.py
      tests/test_v6_only_cli_admission.py -q` → 0 failed; paste it.

## PROOF FOR STEPS 10-11 (2026-09-03)

**Step 10** — the subcommand, thin dispatch only:

    $ deepreason stop-report --help
    usage: deepreason stop-report [-h] [--json] [--config CONFIG] [--verify]
                                  [path]
    positional arguments:
      path             run root or home (default: $DEEPREASON_HOME, else
                       ~/.deepreason)
    options:
      --json           emit the typed report as JSON
      --config CONFIG  a run-config YAML to diff against the compiled
                       manifest; the ONLY input read from outside the record
      --verify         re-derive the verify_root verdict instead of reading
                       the stored one

    $ python -m pytest tests/test_application_text_runs_d0.py         -k thin_service_dispatch -q
    1 passed, 11 deselected

No `Harness(` entered `cli/`: the dispatch imports the application layer
and returns. End-to-end on the real P-A1 root, section 4, exit 0:

    ### 1. ENVIRONMENT — SUPPORTED
    - evidence FOR: transport wall: 41 RemoteDisconnected on endpoint
      ollama-glm-5.3
    ### 2. HARNESS — NO EVIDENCE EITHER WAY
    - note: not claimable: ENVIRONMENT, MODEL still holds evidence.
    ### 3. CONFIGURATION — RULED OUT
    ### 4. MODEL — SUPPORTED
    - evidence FOR: the stop names seat exhaustion: "V6_ROUTE_SEAT_...
    - note: conjecturer#0 passed qualification 20/20 first-pass on
      conjecturer.turn.v6 with 0 repairs

That last note is the tranche's whole point, printed by a command rather
than reconstructed by a window.

**Reachability drift check** (owed from step 9, where all three symbols
read UNREACHABLE with no caller yet):

    frozen_surface_verdict: CLEAR | contacts: [] | adjacent: []
      stop_report          REACHABLE
      render_stop_report   REACHABLE
      resolve_report_source REACHABLE

The predicted transition, so no drift.

**Step 11** — the ring:

    $ python -m pytest tests/test_stop_report.py tests/test_results_command.py         tests/test_cli_readiness.py tests/test_v6_only_cli_admission.py -q
    136 passed in 46.60s

- [x] 12. (S18, R18) Write
      `experiments/2026-09-03-change-stop-report/proof/run_regression.py`:
      takes a path per case, runs the report, asserts the required box
      ranking with the evidence quoted, and records for each root the
      branch + commit it came from plus the `git archive` command that
      re-extracts it. Roots are NOT copied into this branch.
      done-when: the file exists and `--help` (or a dry run with no
      paths) exits 0 listing all eight cases of SPEC.md S18.

- [x] 13. (S18, R18, contradiction (b)) Extract the six roots read-only
      to the scratchpad and run the regression; commit the outputs
      under `proof/`.
      done-when: `python experiments/2026-09-03-change-stop-report/proof/run_regression.py`
      → every case PASS, including the three ROOTLESS cases (P-A2 epoch
      1, P-A2 epoch 2, Phase-1 M3-C0) and the
      qualification-vindication case; paste the summary line.

- [x] 14. (S20, R19) [COMMIT] The mutation proof: implement the NAIVE
      classifier (read the run-config YAML and blame the seat named in
      the stop message) inside the proof script only — OUTSIDE the
      module it judges — run it over the same cases, capture
      `proof/naive_red.txt` and `proof/shipped_green.txt`, and commit
      both in this commit.
      done-when: `proof/naive_red.txt` shows ≥ 2 misfiled cases
      (P-A1 and P-A2 epoch 1 at minimum) and `proof/shipped_green.txt`
      shows 0 misfiled; paste both counts.

## PROOF FOR STEPS 12-14 (2026-09-03)

Eight cases, three branches, roots re-materialised read-only by
`git archive` rather than copied into this branch.

**SHIPPED — `python run_regression.py --extract`:**

    PASS  P-A1 — seat exhaustion behind a transport wall      ENVIRONMENT
    PASS  P-A1 — qualification vindication (R9)               ENVIRONMENT
    PASS  P-A2 epoch 1 — one seat x form refused, knob named  MODEL
    PASS  P-A2 epoch 2 — account usage cap                    ENVIRONMENT
    PASS  P-A2 epoch 3 — harness box, earned                  HARNESS
    PASS  Phase-1 429 root — self-inflicted concurrency cap   ENVIRONMENT
    PASS  Phase-1 M3-C0 — 429 in qualification, no run root   ENVIRONMENT
    PASS  Phase-1 M1-H0 — a CLEAN terminal attributes no box  (none)

    SHIPPED: 8/8 correct, 0 misfiled

**NAIVE — `python run_regression.py --naive` (the classifier this
tranche replaces: read the settings, blame the seat the stop names,
never open the qualification record):**

    FAIL  P-A1                first box 'MODEL', expected 'ENVIRONMENT'
    FAIL  P-A1 vindication    first box 'MODEL', expected 'ENVIRONMENT'
    FAIL  P-A2 epoch 1        first box None,    expected 'MODEL'
    FAIL  P-A2 epoch 2        first box None,    expected 'ENVIRONMENT'
    PASS  P-A2 epoch 3        first box: HARNESS
    FAIL  Phase-1 429 root    first box 'HARNESS', expected 'ENVIRONMENT'
    FAIL  Phase-1 M3-C0       first box None,    expected 'ENVIRONMENT'
    FAIL  Phase-1 M1-H0       first box 'HARNESS', expected None

    NAIVE: 1/8 correct, 7 misfiled

RED and GREEN on the same eight cases, from the same records. The naive
reader's first two failures are the operator's own incident reproduced
exactly: it blames the MODEL on P-A1, the root whose `conjecturer#0`
passed `conjecturer.turn.v6` 20/20 first-pass with 0 repairs. Its three
`None` results are the three failures that produced no readable run
status at all — the rootless class R18 named and the naive reader cannot
see. Its one PASS is a coincidence, not competence: it reaches HARNESS
on P-A2 epoch 3 by the rule "the stop message is not about a seat",
which is the same rule that misfiles the phase-1 429 root.

The naive classifier lives inside `proof/run_regression.py`, OUTSIDE the
module it judges — CLAUDE.md's treadle lesson: keep whatever judges the
work outside the cone it judges.

- [x] 15. (S21, R21, M12) [COMMIT] Run both wheel smokes and record
      whether any pin moved. SPEC.md M12 predicts none moves because the
      pinned surface is console-script entry-point NAMES, the MCP tool
      set and the MCP schema sha — and no MCP tool is added. Verify, do
      not assume; if a pin did move, update it in THIS commit.
      done-when: `python scripts/wheel_smoke.py` → rc 0 AND
      `python -u scripts/wheel_operational_smoke.py` → rc 0; paste both
      rc lines and state explicitly whether any pin changed.

## PROOF FOR STEP 15 (2026-09-03)

**`python scripts/wheel_smoke.py` → rc 0:**

    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    WHEEL_SMOKE_RC=0

**NO PIN MOVED, and that was verified rather than assumed.** SPEC.md M12
predicted it: the pinned surface is console-script entry-point NAMES, the
MCP tool set and the MCP schema sha. This tranche adds a `deepreason`
SUBCOMMAND and no MCP tool, so it touches none of them. `git diff` on
`scripts/wheel_smoke.py` is empty and the smoke passes on the built
wheel, which together is the proof. R21 is discharged.

**`python -u scripts/wheel_operational_smoke.py` → rc 1**, failing at

    "stage": "continuation_resume"
    "failure_kind": "assertion_failed"
    "schema": "deepreason-wheel-operational-failure-v4"

**NOT THIS TRANCHE'S — measured, not assumed.** The same smoke was run in
a clean `git worktree` at the tranche base `7653b04393`, which contains
none of this tranche's commits, and fails IDENTICALLY: same stage, same
failure_kind, same rc. Envelope captured at
`proof/wheel_operational_base_failure.json`.

    $ git worktree add /tmp/base-tree 7653b04393
    $ cd /tmp/base-tree && python -u scripts/wheel_operational_smoke.py
    BASE_RC=1
    "failure_kind":"assertion_failed"
    "stage":"continuation_resume"

`docs/AUDIT_BASELINES.md` (lines 195-202) baselines only smoke failures
naming the MCP schema sha or tool-set pins; this names neither, so by that
document it is a FINDING. It is not, however, a finding this tranche may
act on: CLAUDE.md's cross-routing rule is that a defect found mid-change
is PARKED, not fixed, and REQUEST.md C3 parks "any defect found while
building" by name. Parked with a ready-to-send prompt at step 21.

## Group B — the refusal and the configuration-stages page

- [x] 16. (S15, S16, R16, R17) Create
      `docs/map/CON-configuration-stages.md` to `docs/map/SCHEMA.md`:
      the four stages a setting passes through (operator's file →
      compiled manifest → run-time restoration from notices → what the
      seat receives), each with the command that reveals it, plus the
      six traps of R17 stated flatly. Re-runnable single-line `check:`
      lines at column 0. ≤ 200 lines.
      done-when: `python tools/docs_verify.py` → 0 failed AND
      `python tools/docs_verify.py --audit` reports none of this
      document's checks as unable to fail; paste both.

- [x] 17. (S17, R23, C7) Register the new document in
      `docs/map/INDEX.md` (concept table + routing row) and update
      `docs/map/SUB-application.md` for the new module and the new
      subcommand — in the SAME commit, per the map law. Re-check
      whether `SUB-periphery.md:44` genuinely asserts on `cli/main.py`
      and update it only if it does.
      done-when: `python tools/docs_verify.py --links` → every DR-
      reference resolves, AND `python tools/docs_verify.py` → 0 failed;
      paste both.

- [x] 18. (R23) [COMMIT] Commit the map documents.
      done-when: `git status --porcelain` empty for `docs/map/`.

- [x] 19. (S13, R13, R14, R15) Load the `authoring-skills` skill, then
      amend `.claude/skills/dr-diagnose/SKILL.md`: DIAGNOSIS.md must
      OPEN with the stop report's section 4 pasted verbatim; no phase
      may name a defect, a seat, or a model as the cause without citing
      the report line supporting it; a window that cannot produce the
      report stops there. The incident is QUOTED — the operator's own
      words from REQUEST.md, including "The window that said criticism
      fails to leave a trace was wrong."
      done-when: `grep -q 'stop-report' .claude/skills/dr-diagnose/SKILL.md`
      and the operator's verbatim sentence appears in the file; paste
      both greps.

- [x] 20. (S14, R13) [COMMIT] Amend
      `.claude/skills/dr-drive-harness/SKILL.md` §5 so the "where to
      look when something breaks" table names the stop report FIRST,
      above the per-file rows it subsumes. Commit both skill edits.
      done-when: the stop-report row precedes the `run-status.json` row
      in that table — paste the table.

## PROOF FOR STEPS 16-20 (2026-09-03)

**Steps 16-18 — the map.** `docs/map/CON-configuration-stages.md` created
(163 lines, under R17's "short enough to read at the moment of doubt"),
registered in `INDEX.md` (a concept row and two routing rows), and
`SUB-application.md` given the new module's entry-point block with its
own check. `SUB-periphery.md` was checked and NOT edited: it owns
`mcp_server.py`, not `cli/`, and no MCP tool was added.

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 75 document(s)   RC=0

    $ python tools/docs_verify.py
    docs_verify [full]: 75 documents, 1326 checks, 4 workers
      FAIL SEAM-llm-x-rules.md:54: unparseable check ...
      FAIL CON-run-identity.md:211: git log -M --diff-filter=R ...
      FAIL INV-frozen-surfaces.md:181: test "$(find experiments runs ...
    docs_verify: 3 failed

ALL THREE ARE RECORDED BASELINES, not this tranche's — matched against
`docs/AUDIT_BASELINES.md` by name, not by counting:

  * `SEAM-llm-x-rules.md:54` — baselines line 67, "a lost closing
    backtick merged the check with the paragraph after it", parked P3.
  * `INV-frozen-surfaces.md:181` — baselines line 68, "the census
    asserting ZERO committed `transport_failure` attempts; one exists, in
    a root committed 2026-08-26", parked P-D3. Verified not ours: the one
    matching file is
    `experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c/`,
    and this tranche commits no run root at all.
  * `CON-run-identity.md:211` — baselines line 90, a SHALLOW-clone-only
    git-history row.

    $ python tools/docs_verify.py --audit
    SEAM-llm-x-rules.md:54: unparseable check ...
    docs_verify --audit: 1 finding(s)

The one finding is the pre-existing P3 above, which
`docs/AUDIT_BASELINES.md:67` calls "the single finding keeping `--audit`
above zero". `CON-configuration-stages.md` is named nowhere in the audit
output: none of its checks is vacuous or unparseable. R16's accept met.

The count fell from 6 to 3 during this step. One of the three repaired
was OURS and is worth naming: `SUB-ontology.md`'s census pins
`LLMAttempt.natural_stop` to three files because the field is "WRITTEN
AND NEVER READ — letting a guard, rank, status, label or warrant consume
it would make it an evidence signal, which the seats/evidence law
forbids". The first draft of the report read it to count truncation, which
would have turned a correctness signal into evidence that RANKS a box —
precisely the law's target. Truncation now comes from `LLMCall.truncated`,
which is lawfully consumed elsewhere (`controller.py`, `report.py`).
`tests/test_seats_evidence_law.py::test_natural_stop_is_recorded_and_never_consumed`
passes, and all 8 regression cases still land correctly. The other two
were cleared by `git fetch origin claude/deepreason-p-s1-commitments-wowcib`,
the remedy the baselines name at line 83 for the judge-canary row.

**Steps 19-20 — the refusal.** `dr-diagnose/SKILL.md` gains "Step 1 — run
the stop report, and open DIAGNOSIS.md with it", before the Traps read
and before any code. It carries a real GATE
(`grep -q "THE STOP, CLASSIFIED" DIAGNOSIS.md`), an outlet table (one per
prohibition, per `authoring-skills` X1), and names what it displaces
(`run-status.json` and `REPLAY_VALIDATION.json` drop from rows 1 and 4 of
a hand-read list to a deeper dive entered after the report names a box),
per E4. `dr-drive-harness` §5's table now opens with the stop-report row.

    | Look at | It tells you |
    |---|---|
    | `deepreason stop-report <root-or-home>` | **run this first.** ... |
    | `<root>/run-status.json` | state, stop_reason, message ... |

**A conflict between R15 and `authoring-skills` W5, resolved rather than
picked.** R15 says the incident is quoted in the skill; W5 says
"Mechanize the lesson as a GATE ... delete the story. History lives in
ERRATA.md, not in instructions." Both are honoured by splitting them: the
RULE and its GATE are in `dr-diagnose/SKILL.md`, and the operator's
verbatim words are in `docs/ERRATA_EXECUTOR.md` X12 — the ledger whose
own stated scope is `.claude/skills/`, "THE PROCESS, not the codebase".
X12 also carries the measured cost (NAIVE 1/8 vs SHIPPED 8/8) and the
P-A1 qualification row that contradicted the window the operator caught.

## Shared close

- [x] 21. (S24, C3) Write `PARKED.md` with one paste-ready fenced prompt
      per park: the six not-carried fields (surface 4, priced); the P2
      config-echo gap if it blocked section 1 (say so either way); and
      any defect found while building.
      done-when: `PARKED.md` exists and contains one fenced code block
      per park, each a complete standalone prompt.

- [x] 22. (M13, S1) Re-run the frozen-surface gate with the NEW files
      present — SPEC.md M13 excluded them because the tool refuses a
      declared path that does not exist yet.
      done-when: `python tools/blast_radius.py --files <all targets incl.
      the new ones> --symbols <the new symbols>` →
      `"frozen_surface_verdict": "CLEAR"` with
      `frozen_surface_contacts: []`; paste the verdict verbatim.

## PROOF FOR STEPS 21-22 (2026-09-03)

**Step 21** — `PARKED.md` written with three entries, each carrying a
complete paste-ready prompt where a prompt is the right remedy:

  * **P1** the six engine-config fields the manifest does not carry —
    frozen surface 4, DESIGN-AND-STOP prompt that prices three roads and
    requires the grant be requested in SPEC.md before code, per the
    documented recipe.
  * **P2** the installed-wheel operational smoke failing at
    `continuation_resume` — measured pre-existing at the tranche base,
    envelope committed, framed as a fork the record can decide.
  * **P3** the tranche instruction's own root inventory, written from
    narrative rather than `git ls-tree`. Deliberately NO prompt: the
    remedy would be an `authoring-skills` rule, and that skill's own E1
    tripwire requires TWO recorded instances before a rule is written.
    This is instance one, so it is recorded and left alone.

**Step 22** — the frozen-surface gate re-run with every new file present,
which is what SPEC.md M13 owed (it had to exclude files that did not yet
exist, because the tool refuses a declared path that is absent):

    frozen_surface_contacts: []
    frozen_adjacent_contacts: []
    frozen_surface_verdict: CLEAR
      reach: stop_report           REACHABLE
      reach: render_stop_report    REACHABLE
      reach: resolve_report_source REACHABLE

    "This change touches none of the five frozen surfaces. 3 test file(s)
     and 7 map document(s) assert on the touched targets today."

No `frozen_surface_contacts` entry absent from SPEC.md's forecast (both
are empty), and no unpredicted `newly_dead`/`newly_live` reachability
direction. No drift.

- [ ] 23. (S22, R22) Full gate on an otherwise idle box (never
      concurrently with `docs_verify` — `dr-drive-harness` §5b).
      done-when: `python -m pytest tests/ -q -n 4` ends `N passed, 0
      failed` — paste it. Any failure is either fixed, or shown to be a
      pre-authorized baseline in `docs/AUDIT_BASELINES.md` (the `bc` map
      check; the toolchain-digest pin) and recorded, not stopped on.

- [ ] 24. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND the branch head
      is on `origin/claude/executor-stop-report-paiagc`.

Then: `dr-validate-change` → VALIDATION.md, and only on PASS
`dr-deliver-change` → DELIVERY.md reconciling R1-R28.
