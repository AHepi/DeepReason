# Validation for: one run path — "Get rid of the old one"

Base: `origin/main` `fc0d75473`. Branch:
`claude/single-run-path-unification-bhn2ob`.

## Acceptance checks

**S1.1 (R1) — manifest-direct entry, object or path**

    $ python -m pytest tests/test_single_run_path.py -q
    ..........                                          [100%]
    10 passed in 43.48s

`test_service_entry_accepts_a_precompiled_manifest_object_and_a_manifest_path`
is parametrized over both shapes; both reach a published terminal. **PASS**

**S1.2 (R2) — the door narrows no configuration the compiler admits**

`test_the_door_narrows_no_configuration_the_compiler_admits`, green in the
run above. The manifest it drives asserts its own richness before
launching: `len(manifest.roles["judge"]) == 2`,
`manifest.criticism_policy is not None`,
`control_plane_policy.school_execution.mode == "route_bound"`.

Structurally pinned as well, by a new map check that mutation-proved:

    $ python -c "import inspect;from deepreason.application.text_runs import
      TextRunApplicationService as S;f=S.start_manifest_run;
      code=inspect.getsource(f).replace(f.__doc__,'');
      assert not any(t in code for t in ('judge','school','criticism','roles'))"
    (exit 0)

    mutation (inject `manifest.criticism_policy` into the method) -> rc=1
    restored                                                      -> rc=0

**PASS**

**S1.3 (R3) — the grounded tranche's own config enters through the door**

`test_the_grounded_tranche_config_enters_through_the_new_door` imports
`experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`
from its git-tracked path, calls `build(root)` under a tmp
`DEEPREASON_HOME`, asserts

    summary["manifest_sha256"] == 8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d

— the live grounded run's own digest — and drives that exact root through
`start_manifest_run` to `state == "completed"`. **PASS**

**S2.1 (R4) — the verb's CLI surface is unchanged**

`test_run_verb_parser_surface_is_byte_identical` pins the full introspected
action table (option strings, dest, default, required, action class) for
the `run` subparser:

    (("-h","--help"),  "help",        "==SUPPRESS==", False, "_HelpAction")
    (("--budget",),    "budget",       None,  True,  "_StoreAction")
    (("--problem",),   "problem",      None,  False, "_StoreAction")
    (("--token-budget",), "token_budget", None, False, "_StoreAction")
    (("--run-manifest",), "run_manifest", None, False, "_StoreAction")
    (("--dry-run",),   "dry_run",      False, False, "_StoreTrueAction")

**PASS**

**S2.2 (R5) — the rc exit-code contract**

`test_run_exit_code_contract_is_run_result_exit_code`, parametrized:
`completed -> 0` and `failed -> 4`, each asserted equal to
`run_result_exit_code(published)`. `test_run_preflight_refusals_still_exit_one`
holds the pre-terminal refusal at `1` with no `run-result.json` written.

The `failed` case is what makes this a pin: as first written (completed
only) it passed against the OLD path too, because a completed run maps to
0 under both behaviors. Recorded at CHECKLIST step 10. **PASS**

**S2.3 (R6) — ladders and scripts unmodified**

    $ git diff --stat fc0d75473..HEAD -- 'experiments/*/*.sh' 'experiments/*/**/*.sh'
    (empty)

**PASS**

**S3.1 (R7) — the old road is deleted**

    $ grep -q "_execute_bound_run" src/deepreason/cli/main.py
    absent from cli/main.py: PASS

    $ grep -rn '_execute_bound_run' --include='*.py' src tests scripts
    tests/test_v6_global_dispatch_guard.py:1046:    Migrated 2026-08-13 from `test_execute_bound_run_v6_launch_policy_
    tests/test_v6_global_dispatch_guard.py:1047:    precedes_harness`, which drove `cli.main._execute_bound_run` — the

Two remaining references, both PROSE inside the migrated test's own
docstring recording where it came from. No call site, no definition.
SPEC.md's literal accept was `test -z "$(grep ...)"`; the deviation is
recorded here rather than met by deleting the provenance sentence, which
would destroy the migration's own audit trail. **PASS (with the deviation
stated)**

**S3.2 (R8) — dead census with reference proof**

`proof/dead-census.txt`, three scans and a per-symbol verdict. It did its
job: `attach_bound_evidence_once` fell to src 2 (own def + `__all__`) and
tests 0 — its only caller in the tree was the deleted function. It is the
lifecycle tranche's bare-path retrofit, which R7 names for removal.
Deleted; `test_manifest_launched_root_renders_its_bound_evidence` still
passes without it. Every other censused symbol keeps callers, listed
file:line. **PASS**

**S3.3 (R9) — every migrated test asserts the same behavior**

    tests/test_lifecycle_operation_parity.py: before=11 after=11
    tests/test_v6_global_dispatch_guard.py:   before=23 after=23
    tests/test_v6_only_cli_admission.py:      before=18 after=18

    $ python -m pytest <the three files> -q
    129 passed in 87.72s (0:01:27)

No test deleted. Two strengthened: the dispatch guard now runs against a
real bound root with a byte-identical snapshot and forbids `Harness` in
both bindings plus the service entry; the qualification-ordering test
patches the binding the service actually calls, mutation-proved (stubbing
the qualification gate makes the lock be reached and the test fail).
**PASS**

**S4.1 (R10) — run identity is deterministic through the one road**

`test_run_identity_is_deterministic_through_the_one_road`: compiling the
grounded configuration twice agrees on `manifest_sha256`
`8e22d0431fd2b98d…`, and every `progress.jsonl` line in the root the one
path writes records `run_id` equal to that digest. **PASS**

**S4.2 (R11) — the lifecycle delta is stated, not hidden**

Deferred to DELIVERY.md by design (its accept names DELIVERY.md).
Verified there. **PASS at delivery**

**S4.3 (R12) — old committed roots replay byte-unchanged**

`proof/replay.txt`. Structural half:

    $ git diff --stat origin/main -- src/deepreason/invariants.py \
        src/deepreason/verification/ src/deepreason/harness.py \
        src/deepreason/capabilities/state.py src/deepreason/run_manifest.py
    (empty)

Measured half, on the largest committed root in the tree:

    prior (committed): verify_root_after_amend.json -> []
    after:  elapsed 468.2s
            violations: []
            stats: events 12991, artifacts 304, problems 2894,
                   warrants 16, accepted 287, refuted 16,
                   logged_tokens 1244594
            manifest_sha256 8e22d0431fd2b98d…

UNCHANGED. **PASS**

**S4.4 (R13) — MCP start_run and qualification untouched**

    $ git diff --stat fc0d75473..HEAD -- src/deepreason/mcp_server.py \
        src/deepreason/qualification.py
    (empty)

**PASS**

**S5.1 (R14) — frozen surfaces**: see the dedicated section below. **PASS**

**S5.2 (R15) / S5.3 (R16) / S5.4 (R17) / S5.5 (R18)**: see Full gate, Map,
and the requirement sweep. **PASS**

## Full gate

    FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
      assert 159 == 165
    1 failed, 3562 passed, 7 skipped in 1003.05s (0:16:43)

The single failure is the recorded pre-existing one
(`docs/AUDIT_BASELINES.md`: "1 pre-existing failure … `assert 159 == 165`;
parked, diagnosis prompt in
`experiments/2026-08-09-change-judge-evidence-review/PARKED.md` P1"). It
is a census inconsistency in a report module this tranche never touched
(`git diff --stat fc0d75473..HEAD -- src/deepreason/` names only
`application/text_runs.py` and `cli/main.py`). Delta against baseline = 0.
None of the known `-n 4` flakes fired. Run on an idle box with no
`docs_verify` or sweep concurrent. **PASS**

## Record-behavior preservation

`experiments/2026-08-12-live-grounded-extension-expansion/run`:
**unchanged** — `verify_root` violations `[]` before and after, matching
the committed `verify_root_after_amend.json` byte for byte.

Two further roots are recorded in `proof/replay.txt` under
`verify_root_report`, which is a DIFFERENT instrument with no committed
prior for them; the file states that they are a baseline, not a
comparison, and cites each number with its instrument per CLAUDE.md.

The 42-root sweep is deliberately not re-run: no reader changed (frozen
diff empty above), and CLAUDE.md's own rule is that a committed root's
verdict can move only if the reader moved.

## Frozen-surface diff

    $ git diff --stat fc0d75473..HEAD -- \
        src/deepreason/capabilities/state.py src/deepreason/harness.py \
        src/deepreason/invariants.py src/deepreason/run_manifest.py \
        src/deepreason/qualification.py
    (empty)

Empty, as SPEC.md's forecast predicted from `tools/blast_radius.py`'s own
`frozen_surface_verdict: CLEAR`. **PASS**

## Map

    docs_verify:            53 documents, 868 checks, 3 failed : PASS (= baseline)
    docs_verify --audit:    0 finding(s)                       : PASS
    docs_verify --links:    0 dangling reference(s), 53 docs   : PASS
    docs_verify --coverage: 6 seams swept, 16 without a Sweep: header,
                            2 finding(s)                       : PASS (pre-existing)
    docs_verify --stale:    0 document(s) worth re-reading      : PASS

The 3 `docs_verify` failures are all `CON-run-identity.md` git-history
checks (lines 200/202/204) that require an unshallowed clone — the exact
`docs/AUDIT_BASELINES.md` baseline, which states "on a full clone the
expected value is 0 failed". Delta 0.

`--coverage`'s 2 findings name `SEAM-schools-x-scratch.md` and seams
without `Sweep:` headers. This tranche touched exactly two map documents —

    $ git diff --name-only fc0d75473..HEAD -- docs/map/
    docs/map/CON-run-identity.md
    docs/map/SUB-application.md

— neither of which is a `SEAM-` document, so both findings pre-date the
change. Dismissed as pre-existing, not fixed here (fixing another seam's
coverage mid-validation is exactly what this phase forbids).

**New checks added by this change** — three, all in the two touched
documents, all mutation-proved before being written down:

1. `SUB-application.md` entry-points check gains `start_manifest_run` to
   the method list AND a source-inspection assertion that the method names
   none of `judge` / `school` / `criticism` / `roles`. Mutation: injecting
   `manifest.criticism_policy` into the method body -> rc=1.
2. `SUB-application.md`'s bare-path Trap check became a NEGATION:
   `! grep -q "run_scheduler" src/deepreason/cli/main.py &&
   grep -q "start_manifest_run" …`. Mutation: reinstating an
   `ops.run_scheduler` import in `cli/main.py` -> rc=1.
3. `CON-run-identity.md`'s trap check became the same negation.

The negation is the point: the old checks asserted that `cli/main.py`
CALLS `terminalize_text_run`, which cannot survive deleting the caller.
The new ones assert that no second run path exists, which is the property
the tranche actually delivers and which would fail if one came back.

**Record observables added vs sweep probes**: none added. This change
writes no new field, record type or finding — the terminal records that
manifest-launched roots now receive are written by the UNCHANGED
`terminalize_text_run`. No `tools/root_sweep.py` probe is owed, and
SPEC.md says so in its Frozen-surface forecast rather than leaving the
silence to be interpreted.

**Wheel smoke**:

    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    rc=0

    $ git diff --stat fc0d75473..HEAD -- scripts/
    (empty)

No pin moved, as R17 predicted. The operational smoke is not owed: the
provider-facing operational surface did not move (no CLI verb added or
removed, no MCP tool or schema changed) — recorded as a decision, not an
omission.

**Note on `Verified-at:` stamps.** Both touched map documents kept their
existing stamps (`98a5bc8f`, `bdc476e8`) although all 44 of their checks
were re-run and pass. Advancing them is a file edit, which this phase may
not make; `--stale` reports 0 documents worth re-reading, so nothing is
flagged. Recorded so the next reader knows the stamps under-report rather
than mislead — a stale stamp is honest, a false one is not.

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 manifest-direct entry | S1.1 — `start_manifest_run`, parametrized over object and path |
| R2 full configuration space, no narrowing | S1.2 — judge ensemble + route_bound schools + criticism_policy reach a terminal; plus the source-inspection map check, mutation-proved |
| R3 grounded config is the acceptance fixture | S1.3 — `build_manifest.py` imported from its committed path, digest `8e22d0431fd2b98d…` asserted |
| R4 exact CLI surface, thin wrapper | S2.1 — full parser action table pinned |
| R5 rc contract + flags, regression-pinned | S2.2 — `completed -> 0`, `failed -> 4`, refusal `-> 1` |
| R6 ladders keep working unmodified | S2.3 — no `.sh` in the diff; `grounded_run.sh` byte-unchanged |
| R7 delete the old road + the retrofit | S3.1 (`_execute_bound_run` gone) and S3.2 (`attach_bound_evidence_once` gone) |
| R8 census every deleted symbol | S3.2 — `proof/dead-census.txt`, three scans + per-symbol verdict |
| R9 every old-road test MIGRATES | S3.3 — counts 11/23/18 unchanged, 129 passed, two strengthened |
| R10 deterministic run identity | S4.1 — same config → same digest → same `run_id` in `progress.jsonl` |
| R11 state the lifecycle delta | DELIVERY.md (its accept names that file) |
| R12 old roots replay unchanged | S4.3 — `verify_root` `[]` before and after on a 12 991-event root; frozen diff empty |
| R13 MCP + qualification untouched | S4.4 — empty diff |
| R14 frozen surfaces / stop condition | Frozen-surface diff empty; `blast_radius` verdict `CLEAR` at spec time and at every commit |
| R15 ring, full gate, docs_verify full | Full gate 1 failed (baseline) / 3562 passed; docs_verify full 3 failed (baseline) |
| R16 map moves in the same commits | Both documents landed in the deletion commit; `git show --stat` for that commit lists them |
| R17 wheel smoke pins do not move | `scripts/` diff empty, smoke rc=0 |
| R18 errata entry | E26 appended (tail was E25); CLAUDE.md's mechanism sentence updated in the same commit |
| R19 commit and push every boundary | Six pushed commits on the branch, each a phase or step boundary |
| R20 R-by-R delivery + census line | DELIVERY.md |

None deferred.

## Assumptions carried (operator may override)

- **A1** The door takes a precompiled manifest — object or path — not a
  run-config YAML. Compiling YAML needs policy arguments only the caller
  has (`build_manifest.py:147-166`).
- **A2** "Exact CLI surface" = verb, flags, defaults, synchronous
  blocking, exit contract. Two stdout lines lost their source and are
  gone: the scheduler `[note]` diagnostics (never persisted) and the raw
  `meter.snapshot()` JSON (the meter is built inside `run_scheduler` and
  the worker discards it). No test or ladder asserts either; census in
  SPEC.md.
- **A3** Terminal outcomes exit through `run_result_exit_code`;
  pre-terminal refusals keep exiting `1`.
- **A4** The acceptance fixture is `build_manifest.build(root)` under a
  tmp `DEEPREASON_HOME`.
- **A5** Only `_cmd_run`'s dispatch tail is replaced — and one behavior
  NARROWS as a consequence: a second `deepreason run` on a root that
  already has `progress.jsonl` or `run-result.json` now refuses
  `RUN_ALREADY_STARTED: choose a fresh root or continue_run`, because
  that is `_launch`'s rule for every configuration. `deepreason continue`
  is the successor operation, which this unification makes available to
  these roots for the first time.
- **A6** R12's "targeted" = `verify_root` on the grounded root plus
  `verify_root_report` on two others, not the 42-root sweep.
- **A7** `workload_spec_for_root` opens a read-only harness only when the
  root already carries a `log.jsonl`.
- **Amendment 1** (operator's mid-execution questions) is answered in
  REQUEST.md and proved by
  `test_the_door_carries_the_token_steering_authority`. Classified as
  questions, not new requirements; the operator may reclassify.

## Verdict: PASS
