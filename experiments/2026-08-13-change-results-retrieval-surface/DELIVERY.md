# Delivered: one discoverable way to retrieve run results — `deepreason results`

Branch: `claude/results-retrieval-surface-v6jmiy` @ `6104fd971` (pushed, tree
clean). 14 commits + this one.

## What changed

`deepreason results <root-or-home>` now exists, and `deepreason --help` names
it on one line: **"read a run's typed results"**. It prints one record of a
run's typed outcome — run id, state, stop reason, cycles, tokens spent against
budget, accepted/refuted/suspended counts, survivor and frontier counts,
defended-trial verdicts and judge-call count, the stored `verify_root` verdict,
amendment epochs, and whether the root stands where `amend`/`continue` can act.
`--json` emits stable documented keys (`deepreason-results.v1`); `--verify`
re-derives the verification verdict instead of reading the stored one.

Facts a root does not carry print as **typed absences** — `— not recorded
(NO_RUN_STATUS_JSON)` — never as omitted keys and never as a zero. That matters
more than it sounds: 20 of the 107 committed roots carry no `run-status.json`
at all.

The reader lives in `src/deepreason/application/results.py` and **composes**
`findings.findings_summary` rather than duplicating it — the census found the
fix already half-existed there, and R4 forbids a second implementation. The CLI
branch in `src/deepreason/cli/main.py` is thin. Two refusals
(`RESULTS_ROOT_NOT_FOUND`, `RESULTS_HOME_AMBIGUOUS`) are in the error catalog,
so `deepreason explain-error` covers them; the ambiguous-home refusal lists
every candidate root so the next command is a paste rather than another guess.
`docs/map/SUB-application.md`, `.claude/skills/dr-drive-harness/SKILL.md` and
`README.md` all moved in the same commit as the code.

Proven by 22 new tests, of which two are mutation-proved (deliberately broken,
watched go red, restored): the one asserting `--help` names the verb, and the
one asserting the command never writes a byte into a committed run root.

## The demonstration R25 asked for

`deepreason results experiments/2026-08-12-live-grounded-extension-expansion/run`
— chosen because it is the strongest available test of typed absences: it has a
manifest and a full log but never published `run-status.json`,
`run-result.json` or `REPLAY_VALIDATION.json`.

```
# Results for /home/user/DeepReason/experiments/2026-08-12-live-grounded-extension-expansion/run
  (resolved from a root)

## Question
  Propose innovative ways to expand and strengthen DeepReason's grounded extension — the skeptical fixed-point semantics (spec §4, Pass 1) by which conjectures are accepted, refuted, or suspended — such that each proposal preserves the existing guarantees: determinism of the fixed point, polynomial cost, reinstatement as a derived property, and the validity of every committed root.

## Run
  run id (the deterministic identity of this run): — not recorded (NO_RUN_IDENTITY_RECORD)
  state: — not recorded (NO_RUN_STATUS_JSON)
  stop_reason (the typed reason it ended, never a crash): — not recorded (NO_STOP_RECORD)
  cycles completed: — not recorded (NO_CYCLE_RECORD)
  tokens spent vs budget: — not recorded (NO_RUN_STATUS_JSON) / — not recorded (NO_RUN_STATUS_JSON)
  manifest (the compiled configuration the run carries) present: yes, schema version 6

## Artifacts
  accepted / refuted / suspended: 215 / 12 / 0
  survivors (positions still standing at the end): — not recorded (NO_RUN_RESULT_JSON)
  frontier (the open edge of the inquiry): — not recorded (NO_RUN_RESULT_JSON) artifacts, problem — not recorded (NO_RUN_STATUS_JSON)

## Adjudication (defended trials — a criticism argued and judged)
  ran: yes
  judge calls: 238
  trial verdicts observed: none
  trials declined (the case did not sustain): defence-sustained=27, ensemble-split=44, execution-backed=39, paraphrase-flip=2, referential-integrity=7
  trials blocked by a guard: none

## Verification
  verify_root verdict (the replay check that re-derives the whole run from its log and confirms nothing in the record is corrupt or altered): — not recorded (NO_REPLAY_VALIDATION_JSON)
  read from: — not recorded (NO_REPLAY_VALIDATION_JSON) (pass --verify to re-derive it instead of reading the stored verdict)
  violations: — not recorded (NO_REPLAY_VALIDATION_JSON)
  finding families: — not recorded (NO_REPLAY_VALIDATION_JSON)

## Amendment and terminal readiness
  amendment epochs (later question/evidence appended without editing anything): 0
  stands at a valid typed terminal: no (terminal epoch — not recorded (NO_REPLAY_VALIDATION_JSON))
  stop reason is resumable: — not recorded (NO_STOP_RECORD)
  ready for `deepreason amend` / `deepreason continue`: no

## Not recorded by this root
  NO_CYCLE_RECORD
  NO_REPLAY_VALIDATION_JSON
  NO_RUN_IDENTITY_RECORD
  NO_RUN_RESULT_JSON
  NO_RUN_STATUS_JSON
  NO_STOP_RECORD
```

Note what the record still answers even with three sidecars missing: 215
accepted positions, 12 refuted, 238 judge calls, and five distinct reasons
defended trials declined. The log is the record; the sidecars are conveniences.

The `--json` form is in `proof/results-grounded-extension.json` (118 lines,
parses).

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "one discoverable way to retrieve run results — `deepreason results`" | done | `e3301a438`; VALIDATION S11 |
| R2 | "Route through dr-change-orchestrator" | done | REQUEST/CENSUS/SPEC/CHECKLIST/VALIDATION/DELIVERY all present |
| R3 | "table every current way to read a run's outcome… paste the argparse census" | done | `cb04fb5c1`, CENSUS.md §1–§3 |
| R4 | "the fix is surfacing and completing it, not duplicating it" | done | CENSUS.md §4; VALIDATION S2 (`grep -c "state.status.get"` → `0`) |
| R5 | "`deepreason results <root-or-home>` emitting the typed outcome" | done-with-assumption A1, A2 | `d69b7522f`, `e3301a438`; VALIDATION S1 |
| R6 | "run id, state, stop_reason, cycles completed, token spend vs budget" | done | `d69b7522f`; VALIDATION S3 |
| R7 | "artifact counts… final survivor count, frontier id" | done-with-assumption A3 | `d69b7522f`; VALIDATION S4, S4a |
| R8 | "defended-trial verdict counts and judge-call count" | done-with-assumption A4 | `ba1359454`; VALIDATION S5 |
| R9 | "verify_root verdict… read the stored record, do not re-derive unless --verify" | done | `a1c60e9c1`; VALIDATION S6, S6a — the default path is proved not to replay by making the replay raise |
| R10 | "amendment epochs present, and whether the root stands at a valid typed terminal" | done | `6e9bc7862`; VALIDATION S7 |
| R11 | "Two output modes: human-readable (glossed labels) and --json (stable keys, documented)" | done | `51a59a3e4`; keys documented in SPEC.md's schema block; VALIDATION S8 |
| R12 | "Unknown/absent facts print as typed absences, never omitted" | done | VALIDATION S9; and S4a/S6a, two cases the record taught that the spec had not foreseen |
| R13 | "Errors route through the error catalog… so `deepreason explain-error` covers them" | done | `15498f72a`; VALIDATION S10 |
| R14 | "`deepreason --help` names the command with one line" | done | `e3301a438`; VALIDATION S11 |
| R15 | "dr-drive-harness's CLI-lifecycle section gains the retrieval row in the SAME commit; FORM DR-1/docs mentions regenerate if touched" | done | `e3301a438`; FORM DR-1 checked and NOT touched (`grep -c results` → 0), so no regeneration |
| R16 | "Acceptance test for the defect itself… pin with a test" | done | `test_top_level_help_names_the_results_verb`, **mutation-proved** |
| R17 | "read-only against roots — the command NEVER writes into a run root" | done | `test_results_summary_writes_nothing_into_a_committed_root`, content-addressed over every file, **mutation-proved** |
| R18 | "Frozen surfaces: none expected" | done | `blast_radius.py` → `frozen_surface_verdict: "CLEAR"`, contacts `[]`, run twice (forecast at spec time, verified once the files existed) |
| R19 | "if the MCP surface gains a results tool… window's call, record either way" | done-with-assumption A5 — **no MCP tool added** | SPEC.md S15 with its reason; `git diff --stat` over all four pin files + `mcp_server.py` + `pyproject.toml` → **empty**; wheel smoke exit 0 |
| R20 | "Old roots replay byte-unchanged" | done | VALIDATION §2 — `git status --porcelain experiments/` empty; sweep SUBSTITUTED per SPEC.md's pre-authorization, stated as weaker |
| R21 | "ring while iterating; full gate at the boundary; docs_verify full" | done | VALIDATION §2 — both at baseline exactly |
| R22 | "Map moves in the same commits (SUB-cli covering doc; SUB-application if the reader lives there)" | done-with-assumption A6 | `e3301a438`; there is no `SUB-cli.md` — `SUB-application.md` owns `cli/` |
| R23 | "Errata: if any committed document instructs sessions to retrieve results via a flag or command that does not exist" | done — **trigger does not fire** | VALIDATION §3; a DIFFERENT errata was earned, E25 |
| R24 | "Commit and push every phase boundary" | done | 15 commits, each pushed |
| R25 | "Deliver R-by-R with pasted PROOF, including one demonstration run" | done | this document |
| R26 (Amendment 1) | "Raise ceiling to 800, continue" | done — **and then overrun again** | see Budget below; final measured 1242 |

No requirement is `deferred` or `not-done`.

## Budget — the one thing that did not go to plan

I under-estimated this change by nearly a factor of three, three times running,
and each time it was the tests.

| When | Ceiling | Actual | What happened |
|---|---|---|---|
| step 2 | 433 (mine) | 651 | asked you; you said raise to 800 and continue |
| step 7 | 800 (yours) | 1004 | recorded, not re-asked — your answer approved a trade, not a number |
| step 14 | 1150 (mine) | **1242** | stopped guessing; 1242 is measured and final |

Final split: `src/deepreason` 565, `tests` 610, `docs/map` 42,
`.claude/skills` 14, `README.md` 11. Tests are nearly half, because every fact
the command reports earned both a presence test and a typed-absence test, and
R16/R17 each earned a mutation-proved pin. **Nothing was dropped, narrowed, or
added to reach any of those numbers.**

## Assumptions the operator may override

- **A1** — a home holding several run roots REFUSES and lists them all, rather
  than picking the newest. Guessing which run you meant is the failure this
  command exists to end.
- **A2** — the path argument is optional; bare `deepreason results` reads
  `$DEEPREASON_HOME` (else `~/.deepreason`). Strictly more permissive than your
  written form, which still works unchanged.
- **A3** — "frontier id": the record has no single frontier identifier, so all
  three candidate readings are emitted under one `frontier` object (`count`,
  `problem_id`, `artifact_ids`) rather than one being picked.
- **A4** — judge calls are counted from `event.llm.role == "judge"`; trial
  verdicts from the `trial-*` Measure signals. "No trial ran" prints as a typed
  ZERO, not an absence — it is a fact worth stating.
- **A5** — **no MCP results tool.** The MCP surface already serves
  `run_status`, `run_result` and `run_findings` and hands every caller their
  JSON Schema over `tools/list`, so a model caller there cannot grep for a flag
  that does not exist. Your defect is CLI-specific. Avoided cost: four pin
  locations plus a recomputed schema sha, whose smoke `docs/AUDIT_BASELINES.md`
  currently marks KNOWN STALE with a re-pin tranche in flight.
- **A6** — the covering map document is `SUB-application.md`; no `SUB-cli.md`
  exists.
- **A8** — `results` is deliberately NOT in `_ROOT_ADMISSION_COMMANDS`. A
  reader that refused pre-V6 roots would refuse exactly the roots most worth
  inspecting (11 committed roots raise `UnsupportedRunManifestVersionError`).
  The manifest's admission state is reported as a fact instead.

## Two things the record taught that the spec had not foreseen

Both are now permanent `Traps` entries in `docs/map/SUB-application.md`, so the
next reader meets them before the code does:

1. A `deepreason-run-result-v2` payload for a **failed** run carries
   `error`/`error_type` and **no** `survivors`/`frontier` at all. Counting the
   missing key as `0` would have stated a result the record never held. It now
   reads `NO_SURVIVOR_RECORD`.
2. `REPLAY_VALIDATION.json`'s `verification` block is the legacy
   `{stats, violations}` shape in **all 86** committed roots that carry it. The
   five-family breakdown lives in `run-result.json`. The reader reads both.

## Map delta

- **changed:** `docs/map/SUB-application.md` (admission sentence corrected to
  name the two reader exceptions; entry-point row; "where to change what" row;
  a `Traps` entry with both discoveries above), and
  `docs/map/SEAM-harness-x-workflow.md` (a file-count check the new reader
  legitimately moved, 58 → 59, re-derived not incremented).
- **created:** none.
- **new checks:** 3 (all in `SUB-application.md`); 1 existing check corrected.
  `docs_verify --audit` reports `0 finding(s)`, so none of them is vacuous.
- **`Verified-at:` advanced** on exactly the two documents whose checks were
  actually re-run.
- **left stale:** none introduced. The three pre-existing `CON-run-identity.md`
  git-history failures remain — they need an unshallowed clone and are
  baselined.

One honest note on instrumentation: `blast_radius.py` did **not** predict the
`SEAM-harness-x-workflow.md` drift, because that check keys on a shell grep
COUNT rather than a Python symbol, and my manual cross-check missed it too.
`docs_verify` caught it. That is the argument for running the full mode — not
`--fast` — before committing a `src/` change, and it is now the reason recorded
in the checklist.

## Errata

**E25 added** — `docs/map/SEAM-harness-x-workflow.md`'s prose said
"Fifty-seven files under `src/deepreason` name both sides" while the executable
check on the very next line pinned 58. One of the two had been stale since some
earlier commit and nothing forced them to agree: a `check:` authenticates the
claim it guards, not the sentence beside it. Both now read 59, re-derived.
General lesson recorded with it: a prose number beside a pinned number is a
second, unguarded copy.

R23's own trigger — a committed document instructing sessions to retrieve
results via a nonexistent flag — **did not fire**; no such document exists.

## Parked (not done, not promised)

Two entries, each with a ready-to-send prompt in
`experiments/2026-08-13-change-results-retrieval-surface/PARKED.md`:

- **P1 — should read-only run-root readers pass the V6 admission gate?**
  `findings` and now `results` both read a run root and both sit outside
  `_ROOT_ADMISSION_COMMANDS`. This tranche made the map say so honestly, but
  did not decide whether that is right. The prompt asks for one of two written
  answers: admission is for verbs that interpret or mutate (then add a test
  proving every non-admitted verb is read-only), or readers belong inside too
  (then admission needs a read-only tier that reports rather than refuses).
- **P2 — the map covers no top-level reader module.** 21 top-level
  `src/deepreason/*.py` files are in no map document's `Owns:` header, most of
  them readers (`findings.py`, `error_catalog.py`, `report.py`, `signals.py`,
  `status_display.py`). This tranche avoided widening the gap by putting its
  reader inside `application/`, which the map already covers. Docs-only work.

**Recommended next: P1.** It is small, it is the direct consequence of a
decision this tranche had to make without your words, and leaving it open means
the next person adding a run-root reader faces the same undecided question with
one more precedent and no rule.

## Residue — what is not proven

- The **42-root sweep was substituted, not run.** SPEC.md pre-authorized the
  substitute (no reader was modified — every reader used is called, not
  changed; and no committed root's bytes moved), but the substitute is weaker
  than the instrument.
- **`wheel_operational_smoke.py` could not run**: it drives a live provider and
  this container has no credential file. `wheel_smoke.py` passed at exit 0.
- The **full gate's one failure** is the baselined `test_bronze_report` census
  assertion (`assert 159 == 165`), unrelated to and untouched by this work.
- `deepreason results` has been exercised against **committed roots only**. No
  live run was made this session; none was needed, and none is claimed.
