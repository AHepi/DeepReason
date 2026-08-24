# VALIDATION — treadle third lane + limits pilot

Verdict: **PASS**, with three requirements disposed as SUPERSEDED-BY-AMENDMENT
and one as NOT-EXERCISED. Every row's proof is a command output or a typed
record, never a narrative.

## Per-requirement, against SPEC.md's acceptance checks

| R | Check | Result |
|---|---|---|
| R1 | `diff -r --exclude=.venv --exclude=treadle.egg-info` unpacked zip vs `tools/treadle/` | **PASS** — empty except `VENDORED.md`; 33 files tracked |
| R2 | `tools/treadle/VENDORED.md` names 0.4.1, the zip sha256, and D1–D5 | **PASS** |
| R3 | `git check-ignore` on `tools/treadle/.venv` and `.treadle` | **PASS** — both exit 0; `git ls-files` lists nothing under either |
| R4 | treadle's own suite from its venv | **PASS** — `34 passed`. The doc's "5 passed" is 0.1.0's count; reported as the instruction required |
| R5 | gate, config and skills at their documented paths; no name collision | **PASS** — `comm -12` over `skills/` and `.claude/skills/` is empty |
| R6 | `treadle --repo . doctor` verbatim, exit 0, no MISS | **PASS** — pasted in RESULTS.md; every line OK including credentials and all model tags |
| R7 | CLAUDE.md "Third lane: treadle" with all three clauses | **PASS** — routes-to (two classes), never-routes-to (frozen surfaces, judgment work, record sealing), who-authors (operator or monitor only). Extended after T5 with the two measured limits |
| R8 | install commit carries CLAUDE.md and AUDIT_BASELINES.md | **PASS** — `99caedf1e` lists both |
| R9 | AUDIT_BASELINES.md treadle-doctor row | **PASS** — added at install, updated when the third stage landed, with the line-count caveat that the arithmetic moves |
| R10 | every pilot cone checked against the seven frozen paths | **PASS** — `cone_frozen_check.sh`: four cones, all clean |
| R11 | T1 delta table exists and names the 3 pre-existing failures | **PASS** — board `DONE`; table names 200/202/204 and `3 failed` |
| R12 | REV- task reaches a typed `verdict` event; verdict read from the log | **PASS** — four `verdict` events in `.swarm/log.jsonl`; `REVF-RungDTip` PASS, three FAIL, each read from the log, none from prose |
| R13 | pytest on the new file passes AND the mutation proof exits correctly | **PASS** — independently re-run by the monitor: `1 passed`; mutation proof green-then-RED-then-restored |
| R14 | prediction committed BEFORE the run; outcome classified | **PASS** — `git merge-base --is-ancestor` confirms the order. Outcome: prediction **FALSIFIED**, recorded as such |
| R15 | board + `calls.jsonl` captured between rungs | **PASS** — captured at every rung; 10 calls, 58 gate events, `log-verify` → `chain intact` |
| R16 | typed outcomes only | **PASS** — every verdict in RESULTS.md cites a board state, a log event, a ledger row or an exit code. Model prose is quoted only to classify which outcome occurred |
| R17 | per-rung ledger with cost and failure mode | **PASS**, with a stated gap: `calls.jsonl` records prompt tokens on generate calls only and completion tokens nowhere, so per-rung token cost is **not fully recoverable**. Said plainly rather than estimated |
| R18 | closing recommendation table | **PASS** — revised after T5 |
| R19 | every `REFUSED_*` obeyed | **PASS** — three encountered, three obeyed. `REFUSED_WIP_LIMIT` is the load-bearing one: the limit was not raised; the two open rungs were closed by verdict |
| R20 | treadle 0.5 installed | **PASS** — `selftest.py` 38 checks / 12 planted refused / 0 failed; SETUP.md steps 0–6 followed in order; `docs/TREADLE_ASSEMBLY.md` written before any copy |
| R21 | "keep going" | **PASS** — rung T5 run, disposition written, two real defects found |

## Requirements the amendment overtook

**R11–R18 were satisfied against 0.4.1 and cannot be re-run under 0.5.** 0.5
ships no `treadle run`, no board and no stage table; `MODULES.md` retires the
driver deliberately. The pilot's evidence is therefore evidence about **0.4.1**,
and is labelled that way throughout RESULTS.md. This is recorded, not worked
around: re-running the four rungs under 0.5 is not a thing that can be done.

**NOT EXERCISED, and named so no reader infers otherwise:** escalation and
`BLOCKED` never fired in any generate rung. Nothing in this tranche is evidence
about either.

## Instruments at the delivery boundary

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` (install boundary) | 3 failed → cause fixed → **3875 passed, 0 failed** |
| `python -m pytest tests/ -q -n 4` (final) | **3873 passed, 2 failed, 6 skipped** — both failures `tests/test_mcp_run.py`, both in the baseline's named known-flaky set ("3 tests in `tests/test_mcp_run.py` ... thread-join timing"). Verified rather than assumed: serial re-run `2 passed in 12.22s`. Nothing in this tranche touches MCP |
| `python tools/docs_verify.py` | **3 failed**, the three `CON-run-identity.md` shallow-clone checks — exactly the recorded baseline, no new failure |
| `python3 tools/treadle0.5/selftest.py` | 38 checks, 12 planted violations refused, **0 failed** |
| `python3 scripts/consistency_packet.py --verify` | exit 0 |
| `verify_ledger('zoo/reviews/calls.jsonl')` | 5 rows, clean |
| `treadle --repo . doctor` | exit 0, every line OK |
| `swarm_gate.py log-verify` | `chain intact` |
| credential scan | the key appears in **0** tracked files; no env file tracked |

## The one regression this tranche caused, and its disposal

Committing `.swarm/log.jsonl` turned three tests red. Fixed by correcting the
root-discovery predicate, not the assertions — proven by census: loose 115
roots, tight 114, dropped exactly `['.swarm']`. No assertion weakened, no
fixture rebaselined.

## What this validation does NOT establish

That treadle is a good fit for DeepReason. It establishes that the install is
byte-faithful, that every guard has been seen to fail on purpose, that the
pilot's outcomes are typed and reproducible from the record, and that the
repository's own gates are green with it in the tree. Whether the lane earns
its place is a question for the tranches that use it — and RESULTS.md's residue
lists the five things that would have to be measured first.
