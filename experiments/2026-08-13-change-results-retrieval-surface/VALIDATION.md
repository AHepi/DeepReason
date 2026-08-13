# VALIDATION — `deepreason results`

Verdict: **PASS**

Validated 2026-08-13 against branch `claude/results-retrieval-surface-v6jmiy`.
Every SPEC.md acceptance check was run and its real output pasted. Instruments
compared against `docs/AUDIT_BASELINES.md`.

---

## 1. Per-item acceptance checks

| Item | Check | Result |
|---|---|---|
| S1 (R1, R5) | `python -c "...results_summary(...); assert s['schema']=='deepreason-results.v1'; assert set(s)>={...}"` | `ok` |
| S2 (R4) | `grep -q "from deepreason.findings import findings_summary" src/deepreason/application/results.py` | exit 0 |
| S2 (R4) | `grep -c "state.status.get" src/deepreason/application/results.py` | `0` — no duplicated status walk |
| S3 (R6) | `test_results_summary_reports_run_identity_state_and_budget` | pass |
| S4 (R7) | `test_results_summary_reports_artifact_survivor_and_frontier_counts` | pass |
| S4a (R7,R12) | `test_a_failed_run_reports_no_survivor_set_rather_than_zero` | pass |
| S5 (R8) | `test_adjudication_counts_judge_calls_and_trial_verdicts`, `test_adjudication_absence_is_a_typed_zero_not_a_missing_key` | pass |
| S6 (R9) | `test_verification_reads_the_stored_verdict_and_does_not_replay`, `test_verify_flag_re_derives_the_same_five_family_shape`, `test_verification_is_a_typed_absence_when_no_verdict_was_published` | pass |
| S6a (R9,R12) | violations/families read from their real files; `valid == (violations == 0)` asserted | pass |
| S7 (R10) | `test_terminal_readiness_answers_the_amend_question`, `test_terminal_readiness_is_false_with_typed_absences_on_an_unterminalized_root` | pass |
| S8 (R11) | `python -m deepreason results <root> --json \| python -c "json.load(sys.stdin)"` | `json parses, exit 0` |
| S8 (R11) | `test_rendering_glosses_every_technical_label_and_shows_absences`, `test_rendering_never_prints_an_absence_as_a_number` | pass |
| S9 (R12) | `test_absent_facts_are_typed_absences_not_omitted_keys`, `test_every_absence_reason_is_reachable_from_the_declared_set` | pass |
| S10 (R13) | `python -m deepreason explain-error RESULTS_ROOT_NOT_FOUND` | rc=0, non-empty gloss (pasted in CHECKLIST step 8) |
| S10 (R13) | `test_catalog_keys_are_real_results_codes` — every `RESULTS_*` key is a real raise site | pass |
| S11 (R14,R16) | `deepreason --help \| grep -q "results" && grep -q "read a run's typed results"` | exit 0 |
| S11 (R16) | `test_top_level_help_names_the_results_verb` — **mutation-proved red** | pass |
| S12 (R15) | `grep -q "deepreason results" .claude/skills/dr-drive-harness/SKILL.md && grep -q "deepreason results" README.md` | exit 0 |
| S12 (R15) | FORM DR-1 untouched: `grep -c results docs/FORM_DR1_RUN_APPLICATION.md` | `0` — no regeneration needed |
| S13 (R17) | `test_results_summary_writes_nothing_into_a_committed_root` — **mutation-proved red** | pass |
| S14 (R18) | `blast_radius.py` → `frozen_surface_verdict: "CLEAR"`, contacts `[]` | pass |
| S15 (R19) | `git diff --stat origin/main -- scripts/wheel_smoke.py scripts/wheel_operational_smoke.py src/deepreason/mcp_server.py pyproject.toml` | **empty** |
| S16 (R20) | `git status --porcelain experiments/` minus this tranche | **empty** |
| S18 (R22) | `grep -q "results_summary" docs/map/SUB-application.md` | exit 0 |
| S19 (R23) | errata trigger re-run | does not fire — see §3 |
| S21 (R25) | `proof/results-grounded-extension.txt` / `.json` | exist; JSON parses |

`tests/test_results_command.py` collects **22 tests**; all pass.

## 2. Instruments, against `docs/AUDIT_BASELINES.md`

### Full gate — `python -m pytest tests/ -q -n 4`

    1 failed, 3562 passed, 7 skipped in 797.15s (0:13:17)

    FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
      assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]
    E assert 159 == 165

**== baseline exactly.** `AUDIT_BASELINES.md` records this one pre-existing
failure verbatim, including its `assert 159 == 165`, parked with a diagnosis
prompt in `experiments/2026-08-09-change-judge-evidence-review/PARKED.md` P1.
None of the five known `-n 4` thread-timing flakes appeared, so no serial
re-run was needed. Nothing this tranche touched is in or near that test.

### Map — `python tools/docs_verify.py` (FULL, not `--fast`)

    docs_verify [full]: 53 documents, 864 checks, 4 workers
      FAIL CON-run-identity.md:195 ...
      FAIL CON-run-identity.md:197 ... fatal: ambiguous argument '1637e808'
      FAIL CON-run-identity.md:199 ... fatal: ambiguous argument 'f304fec1'
    docs_verify: 3 failed

**== baseline exactly.** All three are the `CON-run-identity.md` git-history
checks that require an unshallowed clone; `AUDIT_BASELINES.md` records "on a
full clone the expected value is 0 failed". The full mode was run because
`--fast` reuses cached results and cannot catch a document a `src/` change just
broke — and that is not theoretical here: `--fast` DID catch
`SEAM-harness-x-workflow.md` drifting to 4 failures mid-tranche, which was
fixed in the same commit (see §4).

    python tools/docs_verify.py --audit  →  0 finding(s)

No vacuous check was added: every new `check:` in `SUB-application.md` can fail.

### Wheel smoke — `python scripts/wheel_smoke.py`

    exit=0
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas

Exit 0, which is BETTER than the baseline's "KNOWN STALE" allowance — the MCP
schema sha and tool-set pins still match because S15 left the MCP surface
alone. `wheel_operational_smoke.py` was not run: it drives a live provider and
this container has no `env` credential file (`ls experiments/*/env` → nothing).
Stated as a gap, not as a pass.

### Root sweep — not run; substituted, with SPEC.md's authorization

`tools/root_sweep.py` takes ~10 minutes over 42 roots. SPEC.md's
"Record-observable guardrails" section authorized the substitute in advance,
and CLAUDE.md states the governing rule: "a committed root is immutable, so its
verdict can only move if the READER moved." Every reader this tranche uses —
`verify_root`, `verify_root_report`, `Harness`, `findings_summary` — is CALLED,
never modified; the only new reader is additive and has no committed-root
consumer. `git status --porcelain experiments/` outside this tranche is empty,
so no root's bytes moved either. **Substitution used: yes. This is weaker than
the sweep and is recorded as such.**

## 3. R23's errata trigger — does not fire

    $ grep -rn "deepreason results\|--results\b" docs/ README.md .claude/skills/ \
        | grep -v "2026-08-13-change-results"
    docs/map/SUB-application.md   (x3)   <- introduced by this tranche
    README.md                     (x2)   <- introduced by this tranche
    .claude/skills/dr-drive-harness/SKILL.md  <- introduced by this tranche

Every hit is a mention this tranche introduced of a command that now exists.
**No pre-existing committed document instructed a session to retrieve results
via a flag or command that does not exist**, so R23's condition is unmet.
Recorded as a negative result rather than as silence.

An errata entry WAS earned for a different reason found on the way — E25, the
`SEAM-harness-x-workflow.md` prose/check count divergence (§4).

## 4. One drift the blast-radius census did not predict

`docs/map/SEAM-harness-x-workflow.md` carries a `check:` counting files under
`src/deepreason` that name both `harness` and `workflow`, pinned at 58. The new
reader legitimately names both (`deepreason.harness` for a read-only open,
`deepreason.workflow.lifecycle` for `RESUMABLE_STOP_REASONS`), moving the true
count to 59.

`blast_radius.py`'s `consumers.map_checks` returned `[]` for `results.py`
because that check keys off a shell grep COUNT, not a Python symbol name —
exactly the class SPEC.md's census said the manual grep is retained for, and
the manual grep missed it too. **`docs_verify` is what caught it**, which is
the argument for running the full mode before committing `src/` changes.

Fixed in the same commit as the code: the count was RE-DERIVED (not
incremented) and both the check and its prose set to 59. While fixing it, the
prose was found to say "Fifty-seven" against its own check's 58 — already stale
before this tranche touched it. Recorded as `docs/ERRATA.md` **E25** (next free
number; the ledger tail was E24).

## 5. Budget — the one place this tranche overran

| Measurement | Ceiling | Actual | Verdict |
|---|---|---|---|
| step 2 | 433 (my estimate) | 651 | EXCEEDED → operator asked, answered "Raise ceiling to 800, continue" (REQUEST.md Amendment 1 / R26) |
| step 7 | 800 (operator) | 1004 | EXCEEDED → recorded, not re-asked; Amendment 1 approved a trade, not a number |
| step 14 | 1150 (self) | **1242** | EXCEEDED → stopped re-guessing; 1242 is measured and final |

Final, over SPEC.md's declared areas:

    {"areas": {"src/deepreason": 565, "tests": 610, "docs/map": 42,
      ".claude/skills": 14, "README.md": 11}, "total_insertions": 1242}

Tests are 610 of the 1242 — nearly half, and the single largest estimate error.
No requirement was dropped, added, or narrowed to fit any of these numbers.

## 6. Verdict

**PASS.** Every SPEC.md acceptance check passes. Both instruments that ran
match their recorded baselines exactly; the wheel smoke exceeds its baseline.
Two rails (R17 read-only, R16 discoverability) are mutation-proved rather than
merely green. The residue, stated plainly: the root sweep was substituted
rather than run, and `wheel_operational_smoke.py` could not run without
provider credentials.
