# DELIVERY — checkpoint hardening (lane A, ultracode batch 2)

Stands alone. A monitor reviewing this tranche needs nothing else open.

Revised 2026-08-30 after an independent skeptic pass re-ran every claim below.
Eight findings were confirmed; all eight are answered here, and two of them
removed something this document previously called delivered. What the skeptics
found is in "The skeptic pass" near the end, with the command for each.

## The one-paragraph answer

**The half of the operator's law about SILENT stops is shipped; the half about
TAMPERED records is not, and this tranche now says so in one voice instead of
two.** A failure terminal records, typed, that it cannot be continued —
including the terminal that used to write `run-result.json` and nothing else,
which is the operator's "corrupted stop" in its purest form. The integrity gate
the law asks for was built exactly as specified, proved on a one-byte forgery
of a committed root, and then REVERTED: the ring turned eight tests red where
the spec predicted one, and three of the eight are the product's own repair
roads, not fixtures. The spec's own pre-registered rule calls that a stop and a
re-plan, and forbids weakening any assertion to get past it. So it is parked,
with the implementation, the proof and the full collision list preserved — and
now with a stronger acceptance target than the one it was parked with, because
the skeptic pass measured the whole jailbreak completing (`amend` ACCEPTED,
then `continue` ACCEPTED) on a forged `amend_ready` root. The one reader change
this tranche did ship (S7) was WITHDRAWN in that pass: with the verbs ungated
it made `deepreason results --verify` print `ready: no` for a forged root both
verbs accept, which is a false statement about the exact population the law is
about.

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
| S3 | the tamper proof as a one-byte differential on one committed root | **PROVEN, as an instrument — and superseded** | `proof/forge_one_byte.py` / `.json` (six surfaces, intact vs forged) plus `proof/forge_amend_ready.py` / `.json`, which reaches the tamper-to-RESUME the first could not |
| S4 | witness regression over the 16-root gap | **NO — parked with S1/S2** | the population is preserved as measurement: `proof/census.json`, `proof/gate_probe.json` |
| S5 | the ordinary worker-failure terminal records its own uncontinuability | **YES** | `tests/test_checkpoint_hardening.py::test_a_failure_terminal_records_why_it_cannot_be_continued`, RED `KeyError: 'terminal_lifecycle_refusal'` -> GREEN. The predicted `continue_refusal` field was REMOVED in the skeptic pass: it was a constant, and it is wrong on one of the 16 committed roots of that shape |
| S6 | the no-harness failure terminal records `TERMINAL_NO_CHECKPOINT_WRITTEN` | **YES** | `...::test_a_terminal_that_wrote_no_checkpoint_records_that_fact`, same RED -> GREEN, with `run-stop.json` and `checkpoint.json` asserted ABSENT |
| S7 | the results reader answers from the verdict it is holding | **NO — WITHDRAWN in the skeptic pass** | it made `--verify` print `amend_ready: false` on a forged root where `amend` and `continue` both succeed (VALIDATION.md S7 quotes that reading; `proof/forge_amend_ready.json` holds the delivered tree's); `results.py` and `tests/test_results_command.py` are byte-identical to `origin/main` |
| S8 | the map moves in the same commit | **YES, describing what actually shipped** | `CON-run-identity.md` Traps (the measured blindness, the full jailbreak, and "the gate is NOT shipped"), with a check that now RE-DERIVES its numbers instead of re-reading them; `SUB-application.md` one row, one Traps entry, P6 rewritten not deleted; `SUB-amendment.md` reverted |
| S9 | census and probes as committed instruments | **YES** | NINE scripts under `proof/` and the output of each, `MEASUREMENTS.md` (M1-M11), `gate_collisions.md`; four of the nine were added in the skeptic pass |

## The cone, as measured

    $ git diff --name-only 84514a0280f45d29e5066bb3be3d273ba73798db -- src tests docs/map
    docs/map/CON-run-identity.md
    docs/map/SUB-application.md
    src/deepreason/application/text_runs.py
    tests/test_checkpoint_hardening.py

ONE source file, inside the granted cone. `runtime/continuation.py`,
`amendment/apply.py`, `application/results.py` and `tests/test_results_command.py`
were written and then reverted; all four are byte-identical to `origin/main`.
`workflow/lifecycle.py` was granted and deliberately never touched (F1). No
frozen surface is contacted — the seven-path tripwire, widened here to include
`src/deepreason/verification/`, matches nothing.

## The skeptic pass, 2026-08-30

An independent reader re-ran this lane's claims and confirmed eight defects.
Every one is answered; nothing was argued away.

| finding | what it showed | what was done |
|---|---|---|
| a forged `amend_ready` root buys BOTH verbs | the S3 differential used a root whose `continue` refuses for unrelated reasons, so it never demonstrated tamper-to-resume | reproduced as a committed instrument (`proof/forge_amend_ready.py`) and installed as F9's ACCEPTANCE TARGET; the map Traps entry now states it |
| S7 shipped while S2 was reverted, so `--verify` printed a FALSE readiness verdict | on a forged root, HEAD said `ready: no` where the verbs say yes; base said `yes`, which is true, with the `verify_root` verdict already on its own line | **S7 reverted.** `results.py` and its test are back at `origin/main`; SPEC.md S7 carries the withdrawal and the measurement |
| the byte-unchanged control could not see a run root being DELETED | its predicate keyed on a file the mutation removes; `blobs/` and `objects/` — 98% of the tracked bytes in a root — were invisible too | predicate rebuilt on git's INDEX (`git ls-files`) and NUL-delimited status, so deletes, renames and every path under a root are caught; six arms mutation-proven in `proof/control_predicate_arms.txt` |
| `CON-run-identity.md`'s new check could not fail for the reason its prose gives | the numeric half re-read the committed `forge.json` | the check now RE-DERIVES it: `forge_probe.py --witnesses` forges `valid: true` on all four blind roots and two detected ones, and exits 1 the moment the blindness moves. Mutation-proven both ways |
| shipped docstrings asserted a gate that does not exist | `results.py` and its test said "since 2026-08-30 the ACTING verbs re-derive it" | removed with the S7 revert; SPEC.md's S7 rationale corrected in the same edit |
| S7 changed `--verify` in BOTH directions, and only one was tested | on committed roots it also flipped `valid_typed_terminal` False->True, and `amend_ready` on two of them | moot — S7 is reverted — and MEASUREMENTS M4/M5 now names WHICH re-derived verdict it means, because the two predicates disagree on 4 of 6 roots |
| S5's record asserted a `continue_refusal` code it did not derive | 15 of the 16 committed roots of that shape raise it; one raises a different code | field REMOVED. The test still drives `prepare_continuation` and asserts the code actually raised |
| `SUB-application.md` miscounted the branches it certifies, and claimed committed roots changed | one `except` block with THREE exits, not two; and "16 committed roots stop being silent" is impossible | both rewritten; the third exit is measured and parked as F10 |

Also corrected: the diff-budget transcript, which was captured one commit early
and hand-trimmed, and CHECKLIST.md row 12, which recorded ring #2 as
`0 failed | DONE` where VALIDATION.md recorded `1 failed, 193 passed`.

## Stops bubbled (PARKED.md carries a ready-to-send prompt for each)

| # | stop | who decides |
|---|---|---|
| F1 | does "every terminal must leave checkpoints sufficient for relaunch" make FAILURE terminals resumable? 16 committed roots hold the full checkpoint file set and cannot be continued; widening `RESUMABLE_STOP_REASONS` overturns owner decision 4a of 2026-07-27 | operator |
| F2 | limb one's unshipped half: `WorkBudgetDenied` still terminates `operational_failure`, verified on two committed roots | a tranche with the scheduler cone |
| F3 | `Scheduler._record_stop` calls `build_stopped_lifecycle` with no handler for `UnfinishedWorkflowAuthorityError` — the P6 defect, unmirrored, one layer down | a tranche with the scheduler cone |
| F4 | "unresolved containment-breach evidence" names a record type that does not exist; creating it means editing frozen surface 3 | operator, then a granted tranche |
| F5 | `docs/map/INDEX.md` routes to none of SUB-application, SUB-amendment, SUB-periphery; two seams undocumented on both sides | the lane that owns map repair |
| F6 | `amend_ready` requires a resumable stop reason and `amend` does not — a pre-existing reader/actor disagreement. The S7 revert leaves it exactly as found, and the skeptic pass confirms the right predicate is `derive_terminal_authority`, not any replay verdict | monitor |
| F7 | one committed root neither `amend` nor `finalize` can touch | operator |
| F8 | the diff-budget ceiling read EXCEEDED with the gate armed and WITHIN after the revert; the reading it raised is recorded, the fork is not live | monitor, next time |
| **F9** | **the integrity gate: what does "fails replay validation" mean, is `amend` gated at all, and do INCOMPLETE roots fail? Now carries a measured acceptance target: `proof/forge_amend_ready.py` must read `jailbreak_open: False`** | **operator / monitor** |
| F10 | the THIRD exit of `_worker`'s `except` block records nothing, and `finalize` recovers that root — so what should it say in the meantime? | a tranche with the application cone |

## The numbers a monitor will want

    ring #4 (15 files, shared box)  207 passed, 0 failed, 641.67s
    docs_verify                     9 failed = this shallow container's recorded
                                    baseline (AUDIT_BASELINES.md), delta ZERO
    diff budget                     src 34, tests 238, docs/map 68, total 340,
                                    ceiling 400, WITHIN (re-run at HEAD)
    frozen surfaces                 none touched (seven paths plus verification/)
    census re-run                   exit 0, population 59, census.json byte-identical

No full gate was run by this lane; the orchestrator runs one at fan-in.

## Honest residue

- **The law's security clause is not satisfied, and the measurement of that is
  now worse than when this tranche first reported it.** A one-byte forgery of
  an `amend_ready` committed root buys `amend` AND `continue`, in sequence,
  today. `proof/forge_amend_ready.json` is the measurement, not a promise.
- **Nothing this tranche shipped detects a forged record.** With S7 withdrawn,
  the surface that can see the forgery is the one that could always see it:
  `deepreason results --verify` prints the re-derived `verify_root` verdict on
  its own line. It does not, and now does not pretend to, change what the verbs
  will do.
- **The gate's collisions were discovered by the ring, not by the spec.** Seven
  of eight were unpredicted. The spec priced Option B's LATENCY and never asked
  what else `verify_root`'s violation set contains. That is the reusable lesson:
  `verify_root` answers "does every invariant hold over this session", which is
  a broader question than "was this record tampered with".
- **Two different re-derivations were being called one thing.**
  `verify_root(...)['violations']` (every channel) and
  `verify_root_report(...).summary_payload()['valid']` (integrity + security)
  disagree on 4 of the 6 witness roots. MEASUREMENTS M4/M5 said "the re-derived
  verdict" without saying which; it now says.
- **S5's and S6's records are TRUE but NARROW.** They say a failure terminal
  cannot be continued. They do not make it continuable, and whether it should
  be is F1. The third exit of the same block says nothing at all: F10.
- **The no-harness terminal's test injects its failure.** It is declared in the
  test: `start_manifest_run` opens the same root READ-ONLY first, so a genuinely
  unreadable root kills the launch and never reaches the worker. The branch is
  entered exactly as a real open failure would enter it, but the failure itself
  is injected.
- **A one-byte flip of a TIMESTAMP is not caught by anything**, measured on the
  same root (`verify_root` violations `[]`). The gate that was built would have
  caught what `verify_root` catches, no more. Recorded so nobody reads the
  endpoint proof as "any tampering is detected".
- **The control test's delete arm is proven on a scratch repository, not on a
  committed root.** Deleting a committed root to watch the control fire would
  be the mutation the control exists to forbid, so the six arms run against
  real `git` output in a repository built for the purpose
  (`proof/control_predicate_arms.py`).
- **No live evidence.** This batch is offline by construction (SETUP.md: no
  `OLLAMA_API_KEY`, no `env` file). Every number here comes from committed roots
  or offline probes.
- **The box was shared.** Other lanes ran their suites throughout. Timings are
  upper bounds; correctness results are not affected.

## Analogy

A locksmith was asked to fit a lock that refuses a forged key. The lock was
made, and on the bench it refused the forgery and passed the real key. Fitted
to the door, it also refused the caretaker coming in to repair the very lock,
and refused two doors that had never had a frame. So it is off the door and on
the shelf with its test key beside it. The inspector who came afterwards found
two further things: the forged key opens not just the outer door but the inner
one too, which nobody had thought to try — and the little sign the locksmith
had hung up, reading "this door is not openable with a forged key", was simply
false, so it has been taken down rather than repainted.
