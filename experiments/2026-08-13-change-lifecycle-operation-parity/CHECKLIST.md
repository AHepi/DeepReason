# Checklist for: lifecycle-operation parity — "The flags and operations available to the newer reason runs should be available to all configurations"

State: next=34 blockers=OLLAMA_API_KEY absent (blocks step 29-30 only)
Map ids (scoped before planning, per dr-plan-steps §5): `DR-SUB-application`
(owns `application/`, `cli/`, `runtime/` — both changed paths sit inside
this ONE document), `DR-SUB-amendment` (owns `amendment/`),
`DR-CON-run-identity` (owns `text_runs.py`, `continuation.py`,
`amendment/*`), `DR-SEAM-periphery-x-verification` (the only existing seam
document naming `attach_bound_evidence`), `DR-INV-frozen-surfaces` (read;
one disclosed CONTACT, pre-granted by C3, unused by this design).
No seam document exists for application × amendment or application ×
verification — recorded as PARKED P2, not created here (SPEC "Out of
scope": map completeness is its own tranche).

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

---

## Part A — the shared terminalization (S1, S4)

- [ ] 1. (S10) Write the regression pair and the supporting cases FIRST,
      in a new `tests/test_lifecycle_operation_parity.py`: a
      manifest-launched fixture root reaches a typed terminal and accepts
      `amend`; an interrupted one still refuses with
      `AMEND_NOT_AT_TERMINAL`. They are expected to FAIL now.
      done-when: `python -m pytest tests/test_lifecycle_operation_parity.py -q`
      -> collects ≥2 tests and reports failures naming the missing
      lifecycle records (paste the failure lines)

- [ ] 2. (S10) [COMMIT] Commit the failing regression pair.
      done-when: `git log --oneline -1` names the tests commit and
      `git status --porcelain` is empty

- [ ] 3. (S1) Extract `terminalize_text_run` in
      `src/deepreason/application/text_runs.py` and make
      `TextRunApplicationService._worker` call it. Update
      `docs/map/SUB-application.md` in the SAME edit (the terminalization
      block no longer belongs to `_worker`; `_record_exhaustion_lifecycle_stop`'s
      caller changes) with a `check:` command that fails if the behaviour
      regresses, and a `Traps` entry naming the grounded-extension run.
      done-when: `python -m pytest tests/test_r0_terminal_verification.py
      tests/test_v6_terminal_commitment_authority.py
      tests/test_application_text_runs_d0.py tests/test_stop_policy.py
      tests/test_continuation.py -q` -> 0 failed

- [ ] 4. (S4) Add `ensure_lifecycle_documents(root, *, spec)` to
      `text_runs.py`: writes `run-request.json` and `text-workload.json`
      when absent, refuses `RUN_REQUEST_CONFLICT` rather than replacing
      different bytes.
      done-when: a scratch test calling it twice on one root leaves
      byte-identical documents, and `_read_request(root)` returns a dict
      whose `problem.id` matches `run-input.json` (paste)

- [ ] 5. (S1, S4) [COMMIT] Commit Part A with its map move.
      done-when: `git show --stat HEAD` names BOTH
      `src/deepreason/application/text_runs.py` and
      `docs/map/SUB-application.md`

---

## Part B — the bare `run` path becomes lifecycle-complete (S2, S5, S9)

- [ ] 6. (S2, S5) Wire `_execute_bound_run` in
      `src/deepreason/cli/main.py`: lifecycle documents, `ProgressSink`
      emissions, `attach_bound_evidence` before scheduler dispatch when
      the manifest binds a dossier and no import-role record exists yet,
      and `terminalize_text_run` after the scheduler returns — all gated
      on `manifest.schema_version == 6`.
      done-when: `python -m pytest tests/test_lifecycle_operation_parity.py
      -q -k manifest_launched` -> passes (paste)

- [ ] 7. (S2) Ring check for the CLI run path's existing consumers.
      done-when: `python -m pytest tests/test_v6_global_dispatch_guard.py
      tests/test_v6_only_cli_admission.py tests/test_evidence_dossier.py
      tests/test_evidence_dossier_replay.py -q` -> 0 failed

- [ ] 8. (S9) Ledger the standing operator design law in `CLAUDE.md`
      §Operator design laws — "Operations are available to every
      configuration", operator's words verbatim, sibling of the
      2026-08-12 all-configurations law.
      done-when: `grep -c "available to all configurations" CLAUDE.md`
      -> ≥1

- [ ] 9. (S2, S5, S9) [COMMIT] Commit Part B. The law lands in the SAME
      commit as its enforcing code (R9).
      done-when: `git show --stat HEAD` names BOTH `CLAUDE.md` and
      `src/deepreason/cli/main.py`

---

## Part C — the `finalize` operation (S3)

- [ ] 10. (S3) Add `finalize_stopped_root(root, *, reason)` to
      `text_runs.py` and the `finalize` subcommand + `_cmd_finalize` to
      `cli/main.py`, with typed refusals `FINALIZE_ALREADY_TERMINAL`,
      `FINALIZE_RUN_ACTIVE`, `FINALIZE_MANIFEST_UNSUPPORTED`. Update
      `docs/map/SUB-application.md` and `docs/map/CON-run-identity.md`
      in the SAME edit.
      done-when: `python -m pytest tests/test_lifecycle_operation_parity.py
      -q` -> 0 failed

- [ ] 11. (S3) Prove the append-only property on a byte-copy of the REAL
      grounded root in the session scratchpad: finalize it, then compare
      every pre-existing file.
      done-when: every file that existed before finalize is byte-identical
      except `log.jsonl`, which is a strict PREFIX-preserving append
      (paste the `cmp -n <old_size>` result and the new-file list)

- [ ] 12. (S3) Re-run the wheel smokes — `finalize` changes the public
      console surface, so the pins move in this commit or the instrument
      rots (CLAUDE.md).
      done-when: `python scripts/wheel_smoke.py` and
      `python -u scripts/wheel_operational_smoke.py` both exit 0 (paste
      the tail of each)

- [ ] 13. (S3) [COMMIT] Commit Part C with its map moves and smoke pins.
      done-when: `git show --stat HEAD` names `cli/main.py`,
      `application/text_runs.py`, and at least one `docs/map/` file

---

## Part D — the amendment duplicate-refusal narrowing (S6)

- [ ] 14. (S6) Narrow `_admit_supplement` in
      `src/deepreason/amendment/apply.py`: refuse
      `AMEND_SOURCE_ALREADY_ADMITTED` only for a source that HAS an
      `attached-source-record.v1` artifact on the log; admit a bound but
      never-introduced source. Update `docs/map/SUB-amendment.md` in the
      SAME edit with a `check:` command and a `Traps` entry.
      done-when: `python -m pytest tests/test_amendment_epochs.py
      tests/test_amendment_chain_integrity.py
      tests/test_lifecycle_operation_parity.py -q` -> 0 failed

- [ ] 15. (S6) [COMMIT] Commit Part D with its map move.
      done-when: `git show --stat HEAD` names BOTH
      `src/deepreason/amendment/apply.py` and
      `docs/map/SUB-amendment.md`

---

## Part E — errata, map gate, full gate (S12, S13, S11)

- [ ] 16. (S13) Census `docs/` for any committed claim that
      amend/continue work for all run types, then write `docs/ERRATA.md`
      E25 — a correction if the census finds a claim, otherwise a record
      of the census result and the newly-true state.
      done-when: `grep -c '^\*\*E25 —' docs/ERRATA.md` -> 1

- [ ] 17. (S12) Map gate, FULL mode (not `--fast`: a cached run cannot
      catch a document this `src/` change just broke).
      done-when: `python tools/docs_verify.py` -> 0 failed, and
      `python tools/docs_verify.py --audit` -> no refused check, and
      `python tools/docs_verify.py --links` -> every DR- reference
      resolves (paste all three)

- [ ] 18. (S11) FULL GATE, on an otherwise idle box (never concurrent
      with `docs_verify` — dr-drive-harness §5b).
      done-when: `python -m pytest tests/ -q -n 4` -> output ends
      "N passed, 0 failed" (paste it)

- [ ] 19. (S8) Root sweep — no committed root's verdict may move.
      done-when: `python tools/root_sweep.py` -> zero verdict drift
      against `docs/AUDIT_BASELINES.md` (paste the delta line)

- [ ] 20. (S12, S13, S11, S8) [COMMIT] Commit Part E and push with
      2s/4s/8s/16s retry.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD origin/claude/lifecycle-operation-parity-zwzjar`
      prints the same sha twice

---

## Part F — the live proof on the REAL root (S14, S8, R7, R8, R15)

- [ ] 21. (S14) Recreate the gitignored credential file
      `experiments/2026-08-12-live-grounded-extension-expansion/env`
      (`OLLAMA_API_KEY=...`) from the operator's handover if the
      container dropped it. Never commit it.
      done-when: `git check-ignore -v <path>` names the ignore rule AND
      the key is non-empty

- [ ] 22. (S14) Write `live_parity.sh` in this tranche directory:
      finalize → amend → continue, detached-launchable, with the
      OLLAMA_CLOUD_OPERATIONS.md 429 rule (bounded retries with backoff,
      treat repeated 429 as quota exhaustion rather than retrying
      indefinitely) and `DEEPREASON_QUALIFY_CONCURRENCY=2`.
      done-when: `bash -n live_parity.sh` exits 0 and the file is
      `chmod +x`

- [ ] 23. (S14) [COMMIT] Commit the live driver BEFORE launching it, so
      a container rollback cannot lose it.
      done-when: `git show --stat HEAD` names `live_parity.sh`

- [ ] 24. (S14) Finalize the REAL grounded root through the new typed
      path.
      done-when: `derive_terminal_authority(root, manifest=...).status`
      -> `current_valid_committed` (paste), and
      `git status --short experiments/2026-08-12-live-grounded-extension-expansion/`
      shows only additions plus the appended `log.jsonl`

- [ ] 25. (S14) [COMMIT] Commit the finalized root immediately — a
      committed root's new terminal is evidence and must not live only
      on this container's disk.
      done-when: `git show --stat HEAD` names the root's `log.jsonl` and
      the new terminal files

- [ ] 26. (S14, R7) `deepreason amend` on the REAL root, admitting the
      six dossier documents as attached evidence.
      done-when: the amendment-result-v1 summary reports
      `sources_admitted: 6` (paste it)

- [ ] 27. (S14, R8) Measure the amendment epoch's typed outcome:
      attached source record count, provenance role, and the NEW-violation
      delta against the recorded 6.
      done-when: `verify_root(root)["violations"]` pasted, with the
      per-check delta stated against the pre-finalize 6 (report, never
      chase — C5)

- [ ] 28. (S14) [COMMIT] Commit the amended root and the measurement.
      done-when: `git status --porcelain` is empty

- [ ] 29. (S14, R7) Launch `deepreason continue --budget cycles=8
      --token-budget 500000` DETACHED (`setsid nohup ... & disown`) with
      the snapshot loop armed and a monitor on `progress.jsonl` and the
      driver log's `rc=` lines.
      done-when: the driver log records the launch and `progress.jsonl`
      advances past the resume event (paste the first cycle line)

- [ ] 30. (S14, R8) When the continuation stops, judge TYPED outcomes
      only: run state, stop_reason, `verify_root`, the count of
      continued-cycle criticism citing an imported source, and judge
      verdict counts.
      done-when: `LIVE.md` in this tranche directory carries each number
      with the command that produced it

- [ ] 31. (S14, R8) Add the dated segment to
      `experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md`
      — survivors refuted with the documents visible, new proposals,
      judge verdict counts, and the residue (what remains unproven).
      done-when: RESULTS.md contains a `## 2026-08-13 —` segment with a
      `### Residue` subsection

- [ ] 32. (S8, R14) Post-live sweep and the targeted byte-identity proof
      R14 names.
      done-when: `python tools/root_sweep.py` -> zero verdict drift, AND
      `verify_root_report` on one known-good OTHER committed root pasted
      unchanged

- [ ] 33. (all) [COMMIT] Commit Part F and push with retry.
      done-when: `git status --porcelain` is empty AND branch head is on
      origin

---

## Coverage check (every S-number has ≥1 step)

S1→3,5 · S2→6,7,9 · S3→10,11,12,13 · S4→4,5 · S5→6,9 · S6→14,15 ·
S7→(proved by 26 and 29) · S8→19,32 · S9→8,9 · S10→1,2 · S11→18,20 ·
S12→3,10,14,17 · S13→16 · S14→21-31


---

## Re-plan (appended after a validation failure; checked steps keep their outputs)

Step 24's first attempt was killed mid-flight by a container snapshot,
between the typed STOPPED receipt and the terminal commitment. That
interruption was evidence, not noise: it proved `finalize` was not
re-runnable, and re-running it would have recorded a SECOND stop on one
epoch. Two defects in this tranche's own new code, both found by it:

- [x] 34. (S3) `terminalize_text_run` reuses a durable typed stop that was
      recorded but never committed (`_recoverable_typed_stop`), instead of
      recording another.
      done-when: `test_finalize_resumes_after_an_interrupted_terminalization`
      asserts the stop digest/seq are the recovered ones and the count of
      `run-stop` MEASURE events is unchanged -> PASSED

- [x] 35. (S3) `finalize_stopped_root` derives the frontier through the new
      module-level `scheduler.run_report` instead of constructing a
      Scheduler. Constructing one SEEDS SCHOOLS, which appends four events;
      past a recovered stop's horizon those are unauthorized and the root's
      own terminal check fails `TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED`.
      done-when: `python -m pytest tests/test_lifecycle_operation_parity.py -q`
      -> `11 passed`

- [ ] 36. (S3, S14) Re-run `finalize` on the REAL grounded root, which now
      stands at the interrupted state (typed stop at seq 9947, no
      commitment).
      done-when: `derive_terminal_authority(...).status ==
      "current_valid_committed"` and the `run-stop` MEASURE count is
      unchanged

- [ ] 37. (S12) `docs/map/SUB-application.md` and
      `docs/map/SUB-scheduler.md` record `run_report` and the
      recovered-stop rule, in the same commit as the code.
      done-when: `python tools/docs_verify.py` -> 0 failed
