# DELIVERY — checkpoint hardening (lane A, ultracode batch 2)

Stands alone. A monitor reviewing this tranche needs nothing else open.

## The one-paragraph answer

**The half of the operator's law about SILENT stops is shipped; the half about
TAMPERED records is not, and this tranche says so rather than claiming it.** A
failure terminal now records, typed, that it cannot be continued — including
the terminal that used to write `run-result.json` and nothing else, which is
the operator's "corrupted stop" in its purest form. `deepreason results
--verify` now answers from the verdict it actually re-derived, which makes it
the ONE surface out of six that can see a forged record. The integrity gate the
law asks for was built exactly as specified, proved on a one-byte forgery of a
committed root, and then REVERTED: the ring turned eight tests red where the
spec predicted one, and three of the eight are the product's own repair roads,
not fixtures. The spec's own pre-registered rule calls that a stop and a
re-plan, and forbids weakening any assertion to get past it. So it is parked,
with the implementation, the proof, and the full collision list preserved.

## What was asked

CLAUDE.md, operator, 2026-08-29, verbatim:

> clean stop. with an assurance that continuing is possible. Too often an
> operational failure overlooks securing enough checkpoints to allow relaunches
> or forgets to ensure continuing is possible that trigger corrupted stops. On
> that note, checkpoints need to be hardned. I don't want a jailbroken run to
> be continuable.

This lane owned limbs TWO ("every stop secures continuation") and THREE
("continuation is integrity-gated"). Requirement numbers are in REQUEST.md;
spec items in SPEC.md.

## Requirement by requirement

| item | what it asked | shipped? | evidence |
|---|---|---|---|
| S1 | `continue` re-derives the record through `verify_root` and refuses typed | **NO — parked (F9)** | built and proven (`proof/RED-`/`GREEN-checkpoint-hardening.txt`, `git show 5fccb1e91`), reverted after ring #1; `proof/gate_collisions.md` |
| S2 | `amend` does the same, as a 23rd `AmendmentError` code | **NO — parked (F9)** | same; `docs/map/SUB-amendment.md` restored byte-for-byte to origin/main so its 22-code check stays honest |
| S3 | the tamper proof as a one-byte differential on one committed root | **PROVEN, as an instrument** | `proof/forge_one_byte.py` / `.json` — six surfaces, intact vs forged, re-runnable |
| S4 | witness regression over the 16-root gap | **NO — parked with S1/S2** | the population is preserved as measurement: `proof/census.json`, `proof/gate_probe.json` |
| S5 | the ordinary worker-failure terminal records its own uncontinuability | **YES** | `tests/test_checkpoint_hardening.py::test_a_failure_terminal_records_why_it_cannot_be_continued`, RED `KeyError: 'terminal_lifecycle_refusal'` -> GREEN |
| S6 | the no-harness failure terminal records `TERMINAL_NO_CHECKPOINT_WRITTEN` | **YES** | `...::test_a_terminal_that_wrote_no_checkpoint_records_that_fact`, same RED -> GREEN, with `run-stop.json` and `checkpoint.json` asserted ABSENT |
| S7 | the results reader answers from the verdict it is holding | **YES** | `tests/test_results_command.py::test_terminal_readiness_answers_the_rederived_verdict_under_verify`, RED `assert True is False` -> GREEN |
| S8 | the map moves in the same commit | **YES, describing what actually shipped** | `CON-run-identity.md` Traps (the measured blindness + "the gate is NOT shipped", with a check that goes red if it lands and the entry is not rewritten); `SUB-application.md` two rows, one new Traps entry, P6 rewritten not deleted; `SUB-amendment.md` reverted |
| S9 | census and probes as committed instruments | **YES** | five scripts, five JSON outputs, `MEASUREMENTS.md`, `gate_collisions.md` |

## The cone, as measured

    $ git diff --name-only 84514a0280f45d29e5066bb3be3d273ba73798db -- src tests docs/map
    docs/map/CON-run-identity.md
    docs/map/SUB-application.md
    src/deepreason/application/results.py
    src/deepreason/application/text_runs.py
    tests/test_checkpoint_hardening.py
    tests/test_results_command.py

Two source files, both inside the granted cone. `runtime/continuation.py` and
`amendment/apply.py` were written and then reverted; they are unchanged from
`origin/main`. `workflow/lifecycle.py` was granted and deliberately never
touched (F1). No frozen surface is contacted — the seven-path tripwire,
widened here to include `src/deepreason/verification/`, matches nothing.

## Stops bubbled (PARKED.md carries a ready-to-send prompt for each)

| # | stop | who decides |
|---|---|---|
| F1 | does "every terminal must leave checkpoints sufficient for relaunch" make FAILURE terminals resumable? 16 committed roots hold the full checkpoint file set and cannot be continued; widening `RESUMABLE_STOP_REASONS` overturns owner decision 4a of 2026-07-27 | operator |
| F2 | limb one's unshipped half: `WorkBudgetDenied` still terminates `operational_failure`, verified on two committed roots | a tranche with the scheduler cone |
| F3 | `Scheduler._record_stop` calls `build_stopped_lifecycle` with no handler for `UnfinishedWorkflowAuthorityError` — the P6 defect, unmirrored, one layer down | a tranche with the scheduler cone |
| F4 | "unresolved containment-breach evidence" names a record type that does not exist; creating it means editing frozen surface 3 | operator, then a granted tranche |
| F5 | `docs/map/INDEX.md` routes to none of SUB-application, SUB-amendment, SUB-periphery; two seams undocumented on both sides | the lane that owns map repair |
| F6 | `amend_ready` requires a resumable stop reason and `amend` does not — a pre-existing reader/actor disagreement this tranche did not widen | monitor |
| F7 | one committed root neither `amend` nor `finalize` can touch | operator |
| F8 | the diff-budget ceiling read EXCEEDED with the gate armed and WITHIN after the revert; the reading it raised is recorded, the fork is not live | monitor, next time |
| **F9** | **the integrity gate: what does "fails replay validation" mean, is `amend` gated at all, and do INCOMPLETE roots fail?** | **operator / monitor** |

## Honest residue

- **The law's security clause is not satisfied.** A tampered record still buys
  an amendable run, and `continue`'s refusal on such a root is for unrelated
  reasons. `proof/forge_one_byte.json` is the measurement, not a promise.
- **The gate's collisions were discovered by the ring, not by the spec.** Seven
  of eight were unpredicted. The spec priced Option B's LATENCY and never asked
  what else `verify_root`'s violation set contains. That is the reusable lesson:
  `verify_root` answers "does every invariant hold over this session", which is
  a broader question than "was this record tampered with".
- **S5's and S6's records are TRUE but NARROW.** They say a failure terminal
  cannot be continued. They do not make it continuable, and whether it should
  be is F1.
- **The no-harness terminal's test injects its failure.** It is declared in the
  test: `start_manifest_run` opens the same root READ-ONLY first, so a genuinely
  unreadable root kills the launch and never reaches the worker. The branch is
  entered exactly as a real open failure would enter it, but the failure itself
  is injected.
- **A one-byte flip of a TIMESTAMP is not caught by anything**, measured this
  session on the same root (`verify_root` violations `[]`). The gate that was
  built would have caught what `verify_root` catches, no more. Recorded so
  nobody reads the endpoint proof as "any tampering is detected".
- **No live evidence.** This batch is offline by construction (SETUP.md: no
  `OLLAMA_API_KEY`, no `env` file). Every number here comes from committed roots
  or offline probes.
- **The box was shared.** Four other lanes ran their suites throughout. Timings
  are upper bounds; correctness results are not affected.

## Analogy

A locksmith was asked to fit a lock that refuses a forged key. The lock was
made, and on the bench it refused the forgery and passed the real key. Fitted
to the door, it also refused the caretaker coming in to repair the very lock,
and refused two doors that had never had a frame. So it is off the door and on
the shelf with its test key beside it, the door now carries a sign saying
plainly which rooms cannot be re-entered, and the caretaker's ledger — for the
first time — shows the forged key as forged.
