# Checklist for: the stop report — the harness writes the first failure report

State: next=3 blockers=none

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

- [ ] 3. (S1, S3, S4, C2, M9, M10) Create
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

- [ ] 4. (S5, R4) Add SECTION 2 (PRE-RUN CHECK): one row per seat × form
      from `production-contract-qualification.json` —
      first_pass/representative, eventual_valid, repair_count,
      qualified; rows for any seat implicated in the stop quoted IN
      FULL with per-case `failure_code` tallies when present; when the
      record came from the home cache, name the subject digest.
      done-when: on the P-A1 root section 2 contains the row for
      `conjecturer#0 conjecturer.turn.v6` showing `20/20` first-pass and
      `qualified True` — paste the line.

- [ ] 5. (S6, R5) Add SECTION 3 (PROVIDER HEALTH per seat): attempts,
      faults, zero-token returns (`tokens == 0` or `usage_unknown`),
      transport diagnostics grouped by kind with counts and endpoint,
      the last fault verbatim, and any `HTTP-429` rendered with the
      provider's own message text. Walks `split_legs` diagnostics too.
      done-when: on the P-A1 root it reports `RemoteDisconnected` 41 on
      `ollama-glm-5.3` (SPEC.md M5a — the instrument's number, not
      R18's prose 39), and on the phase-1 `failed-429-…` root it reports
      `HTTP-429` 48 with `HTTP Error 429: Too Many Requests`.

- [ ] 6. (S7, S8, S9, R6-R11) Add SECTION 4 (THE STOP, CLASSIFIED): the
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

- [ ] 7. (S10, R12) Add SECTION 5 (CONTINUABILITY): state, stop_reason,
      terminal_lifecycle_refusal, the `verify_root` verdict summary
      (STORED by default per assumption A4, re-derived only on
      `--verify`), and a plain verdict on whether `continue`/`amend`
      would be accepted today.
      done-when: on the phase-1 M1-H0 root
      (`home-default/runs/run-fe00609058e1…`) section 5 prints
      `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` and
      `continue: REFUSED` — paste both.

- [ ] 8. (S11, S12, R1, R27) Add Markdown + JSON rendering and ROOTLESS
      MODE: the report accepts a run root OR a home; given a home with
      no run root it emits the same five sections, sections 1/3/5
      reporting typed ABSENCE (`no run root: the run never started`
      plus the refusal code when recorded) and sections 2/4 built from
      the qualification record alone. Its own resolver, not
      `resolve_results_root` (SPEC.md M11 — that one refuses this case).
      done-when: `python -m pytest tests/test_stop_report.py -q` → 0
      failed, including the rootless and determinism tests; paste it.

- [ ] 9. (S2, R1) [COMMIT] Prove the not-write property and commit the
      module.
      done-when: `python -m pytest tests/test_stop_report.py -k
      not_write -q` passes, AND a manual re-check on a real extracted
      root shows an identical `find <root> -type f | sort` and combined
      sha256 before and after — paste both digests.

- [ ] 10. (R26, M10) Add the CLI subcommand `deepreason stop-report
      <root-or-home> [--json] [--config FILE] [--verify]` to
      `src/deepreason/cli/main.py` as THIN DISPATCH ONLY.
      done-when: `deepreason stop-report --help` exits 0 and prints the
      four flags; AND `python -m pytest
      tests/test_clients_have_only_thin_service_dispatch*.py -q` (or the
      test file carrying
      `test_clients_have_only_thin_service_dispatch_and_one_registry`)
      passes, proving no `Harness(` entered `cli/`.

- [ ] 11. (R26) [COMMIT] Run the subsystem test ring for the touched
      area and commit the CLI surface.
      done-when: `python -m pytest tests/test_stop_report.py
      tests/test_results_command.py tests/test_cli_readiness.py
      tests/test_v6_only_cli_admission.py -q` → 0 failed; paste it.

- [ ] 12. (S18, R18) Write
      `experiments/2026-09-03-change-stop-report/proof/run_regression.py`:
      takes a path per case, runs the report, asserts the required box
      ranking with the evidence quoted, and records for each root the
      branch + commit it came from plus the `git archive` command that
      re-extracts it. Roots are NOT copied into this branch.
      done-when: the file exists and `--help` (or a dry run with no
      paths) exits 0 listing all eight cases of SPEC.md S18.

- [ ] 13. (S18, R18, contradiction (b)) Extract the six roots read-only
      to the scratchpad and run the regression; commit the outputs
      under `proof/`.
      done-when: `python experiments/2026-09-03-change-stop-report/proof/run_regression.py`
      → every case PASS, including the three ROOTLESS cases (P-A2 epoch
      1, P-A2 epoch 2, Phase-1 M3-C0) and the
      qualification-vindication case; paste the summary line.

- [ ] 14. (S20, R19) [COMMIT] The mutation proof: implement the NAIVE
      classifier (read the run-config YAML and blame the seat named in
      the stop message) inside the proof script only — OUTSIDE the
      module it judges — run it over the same cases, capture
      `proof/naive_red.txt` and `proof/shipped_green.txt`, and commit
      both in this commit.
      done-when: `proof/naive_red.txt` shows ≥ 2 misfiled cases
      (P-A1 and P-A2 epoch 1 at minimum) and `proof/shipped_green.txt`
      shows 0 misfiled; paste both counts.

- [ ] 15. (S21, R21, M12) [COMMIT] Run both wheel smokes and record
      whether any pin moved. SPEC.md M12 predicts none moves because the
      pinned surface is console-script entry-point NAMES, the MCP tool
      set and the MCP schema sha — and no MCP tool is added. Verify, do
      not assume; if a pin did move, update it in THIS commit.
      done-when: `python scripts/wheel_smoke.py` → rc 0 AND
      `python -u scripts/wheel_operational_smoke.py` → rc 0; paste both
      rc lines and state explicitly whether any pin changed.

## Group B — the refusal and the configuration-stages page

- [ ] 16. (S15, S16, R16, R17) Create
      `docs/map/CON-configuration-stages.md` to `docs/map/SCHEMA.md`:
      the four stages a setting passes through (operator's file →
      compiled manifest → run-time restoration from notices → what the
      seat receives), each with the command that reveals it, plus the
      six traps of R17 stated flatly. Re-runnable single-line `check:`
      lines at column 0. ≤ 200 lines.
      done-when: `python tools/docs_verify.py` → 0 failed AND
      `python tools/docs_verify.py --audit` reports none of this
      document's checks as unable to fail; paste both.

- [ ] 17. (S17, R23, C7) Register the new document in
      `docs/map/INDEX.md` (concept table + routing row) and update
      `docs/map/SUB-application.md` for the new module and the new
      subcommand — in the SAME commit, per the map law. Re-check
      whether `SUB-periphery.md:44` genuinely asserts on `cli/main.py`
      and update it only if it does.
      done-when: `python tools/docs_verify.py --links` → every DR-
      reference resolves, AND `python tools/docs_verify.py` → 0 failed;
      paste both.

- [ ] 18. (R23) [COMMIT] Commit the map documents.
      done-when: `git status --porcelain` empty for `docs/map/`.

- [ ] 19. (S13, R13, R14, R15) Load the `authoring-skills` skill, then
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

- [ ] 20. (S14, R13) [COMMIT] Amend
      `.claude/skills/dr-drive-harness/SKILL.md` §5 so the "where to
      look when something breaks" table names the stop report FIRST,
      above the per-file rows it subsumes. Commit both skill edits.
      done-when: the stop-report row precedes the `run-status.json` row
      in that table — paste the table.

## Shared close

- [ ] 21. (S24, C3) Write `PARKED.md` with one paste-ready fenced prompt
      per park: the six not-carried fields (surface 4, priced); the P2
      config-echo gap if it blocked section 1 (say so either way); and
      any defect found while building.
      done-when: `PARKED.md` exists and contains one fenced code block
      per park, each a complete standalone prompt.

- [ ] 22. (M13, S1) Re-run the frozen-surface gate with the NEW files
      present — SPEC.md M13 excluded them because the tool refuses a
      declared path that does not exist yet.
      done-when: `python tools/blast_radius.py --files <all targets incl.
      the new ones> --symbols <the new symbols>` →
      `"frozen_surface_verdict": "CLEAR"` with
      `frozen_surface_contacts: []`; paste the verdict verbatim.

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
