# SPEC — treadle 0.4.1 as the workflow's third lane, plus the four-rung limits pilot

Traces to REQUEST.md R1–R19, C1–C7. Written after reading the shipped
`AGENT_INSTALL.md`, `README.md`, `pyproject.toml`, `src/treadle/{cli,engine,
client}.py` and `repo-assets/swarm_gate.py` in full.

## Map preflight (recorded once, per CLAUDE.md)

Resolved ids: **DR-INV-frozen-surfaces** is the only map document this tranche
is governed by, and it is consumed READ-ONLY (R10). No `DR-SUB-`, `DR-CON-` or
`DR-SEAM-` is in scope: the install writes only to `tools/treadle/`,
`treadle.toml`, `skills/`, `scripts/swarm_gate.py`, `.swarm/`, `CLAUDE.md`,
`docs/AUDIT_BASELINES.md` and this experiment directory, none of which any map
document `Owns:`. Consequence: **no map document's `Verified-at:` may be
advanced by this tranche**, and none is. C4's "map moves in the same commits"
is satisfied vacuously and the vacuity is asserted here so a later audit can
check it rather than infer it.

Frozen surfaces, enumerated from `DR-INV-frozen-surfaces` for the R10 cone
test: (1) `src/deepreason/capabilities/state.py`; (2) `src/deepreason/
harness.py`; (3) replay-validation formats — `src/deepreason/invariants.py`,
`src/deepreason/verification/`; (4) `src/deepreason/run_manifest.py` schemas
AND validators; (5) anything altering qualification subject digests —
`src/deepreason/qualification.py`; frozen-adjacent: `route_fingerprint` in
`src/deepreason/llm/firewall.py`.

## Deviations (D1, D2 ledgered by the operator; D3–D5 recorded here)

**D1 (operator-directed).** Vendor, do not `~/tools`. Source committed at
`tools/treadle/` verbatim from the zip: `src/`, `repo-assets/`, `tests/`,
`pyproject.toml`, and the shipped `AGENT_INSTALL.md` / `README.md` /
`DEDUCTION.md` / `FIXES.md`. `tools/treadle/.venv/` and `.treadle/` gitignored
(R3). Rationale is C-environment, not preference: this container rolls back and
wipes gitignored paths, so a `~/tools` install would not survive the session.

**D2 (operator-directed).** `scripts/swarm_gate.py` from `repo-assets/`;
`treadle.toml` at repo root; `skills/` tree as shipped. Collision check for
`.claude/skills` is a required output, not an assumption.

**D3 (recorded).** `AGENT_INSTALL.md` §2 also stages `.swarm` (the board and
its hash-chained log) into the commit. `.swarm/` is therefore in the blast
radius even though C3 does not name it; C3 is the tranche instruction's
summary of where writes land, and the gate's own board is inseparable from
installing the gate. **Committed**, per the shipped instruction, so the board
survives a rollback.

**D4 (recorded).** `treadle.toml` is installed ADAPTED, not verbatim. R6
requires every `doctor` line to read OK, and `cli.py::dispatch` prints a
`WARN ... MISSING (dangling read reference)` line for every `context_files`
entry that does not exist. The shipped file points three of them at another
programme's tree (`zoo/batteries/FORMAT.md`, `zoo/derivations/FORMAT.md`,
`rules/rules.json`), none of which exists here. Those entries are removed.
D2's "as shipped" is preserved where it was stated — the `skills/` tree — and
`treadle.toml` is only required by D2 to be "at repo root". The shipped file is
committed unmodified at `tools/treadle/repo-assets/treadle.toml`, so the
adaptation is diffable against its origin.

**D5 (recorded).** The pilot adds one generate-kind stage, `pilot`, routed from
prefix `PIL-`, whose system prompt is a new `skills/pilot-task/SKILL.md`. The
five shipped generate stages carry PROMPT-CORE text written for a formal-methods
programme (term pinning, example batteries, discharge typing); routing a
DeepReason instrument task through one of them would measure the mismatch, not
the driver. T2 uses the SHIPPED `review` stage unmodified — the independent-
review claim (R12) is only tested honestly if the reviewer's system prompt is
the one treadle ships.

## Acceptance checks, per requirement

| R | Acceptance check (command or artifact) |
|---|---|
| R1 | `git ls-files tools/treadle` lists `src/treadle/{__init__,__main__,cli,client,engine}.py`, `tests/test_treadle.py`, `pyproject.toml`, and the `repo-assets/` tree; each byte-identical to the zip (`diff -r` against the unpacked copy, empty). |
| R2 | `tools/treadle/VENDORED.md` exists, names version 0.4.1, the zip's sha256, and D1–D5. |
| R3 | `git check-ignore -q tools/treadle/.venv && git check-ignore -q .treadle` both exit 0; `git ls-files` lists nothing under either. |
| R4 | `tools/treadle/.venv/bin/python -m pytest -q` from `tools/treadle/` exits 0; the actual count is reported (the doc's "5 passed" is 0.1.0's). |
| R5 | `scripts/swarm_gate.py`, `treadle.toml`, `skills/` all present; `ls skills .claude/skills` pasted, showing disjoint names. |
| R6 | `tools/treadle/.venv/bin/treadle --repo . doctor` output pasted verbatim; exit 0; no MISS line. |
| R7 | `CLAUDE.md` contains a "Third lane: treadle" paragraph with all three clauses (routes-to, never-routes-to, who-authors). |
| R8 | `git show --stat` for the install commit lists `CLAUDE.md` and `docs/AUDIT_BASELINES.md` alongside the install paths. |
| R9 | `docs/AUDIT_BASELINES.md` has a treadle-doctor instrument row, expected all OK. |
| R10 | For each of T1–T4, every cone glob is checked against the seven frozen paths enumerated above; the check and its output are recorded in RESULTS.md. |
| R11 | `experiments/2026-08-23-treadle-pilot/` holds the delta table; it names all 3 `CON-run-identity.md` failures. Board shows T1 DONE or BLOCKED — either is a recorded outcome. |
| R12 | Board shows the `REV-` task reaching a `verdict` event in `.swarm/log.jsonl`; the verdict value is read from the log, not from the model's prose. |
| R13 | `python -m pytest <new file>` exits 0 AND the mutation-proof script exits non-zero on the mutated tree. |
| R14 | The T4 prediction is written to `PREDICTION.md` and committed BEFORE T4 runs (`git log` order is the proof); the outcome is one of refine / escalate / BLOCKED / wrong-PASS. |
| R15 | Per rung: `swarm_gate.py board` and `wc -l .treadle/calls.jsonl` captured before and after, pasted into RESULTS.md. |
| R16 | RESULTS.md cites only board states, `.swarm/log.jsonl` events, `.treadle/calls.jsonl` records and acceptance exit codes as evidence. |
| R17 | RESULTS.md has one segment per rung with driver action, call count, token/budget evidence from `calls.jsonl`, and the failure mode where one occurred. |
| R18 | RESULTS.md ends with a routes-tomorrow / never-routes table over DeepReason task classes. |
| R19 | No `REFUSED_*` is worked around; each one encountered is pasted and obeyed. |

## The three failure modes (Q4, answered from the record, not the operator)

`README.md` and `engine.py::run_generate` agree: **refine** (re-prompt with the
acceptance output appended), then **escalate** once to `escalate_model`, then
**requeue as BLOCKED** with an evidence file under `.treadle/evidence/`. R14 and
R17 are scored against exactly these three.

## Pilot design

Every task is authored by this window (the monitor) per R7's law, with cone,
base, deterministic `accept`, and `out_of_scope`.

- **T1 `PIL-DocsVerifyDelta`** — generate. Cone
  `experiments/2026-08-23-treadle-pilot/T1/*`. Accept: a command that greps the
  produced table for all three `CON-run-identity.md` line numbers (200, 202,
  204) and for the string `3 failed`.
- **T2 `REV-RungD`** — review, shipped stage. The task is walked
  DRAFT→READY→CLAIMED→COMMITTED against Rung D's REAL commits (base = the
  commit before the tranche, sha = its last commit), so the reviewer receives
  `git diff base..sha` of delivered work. `_remote_required` means the shas
  must be on a remote branch; they are on `main`.
- **T3 `PIL-RegressionFixture`** — generate. Cone
  `experiments/2026-08-23-treadle-pilot/T3/*`. Accept: pytest on the new file
  passes AND a mutation-proof script exits 0 (the script itself asserts the
  test goes RED under mutation).
- **T4 `PIL-SpecDriftJudgment`** — generate. Cone
  `experiments/2026-08-23-treadle-pilot/T4/*`. Accept: a command that can only
  be satisfied by the correct reading-comprehension answer, and that cannot be
  satisfied by running any instrument. Pre-registered prediction required first.

## Stop conditions carried from the orchestrator

A step failing twice the same way; a cone found to touch a frozen surface; a
`REFUSED_*` that cannot be obeyed without changing the task; the API key
failing to authenticate. Each is a STOP with priced options, not a workaround.

## Budget

Install + governance ≈ 120 inserted lines outside `tools/treadle/` (which is
vendored, not authored). Pilot artifacts are experiment-directory only.
