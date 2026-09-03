# VERIFY — the fix against GOAL.md's success criterion

Four criteria were written in GOAL.md before any code moved. Each is
answered here with the command that answers it, not with a summary.

## 1. The regression file is byte-identical to the originating commit

    $ git show 06b0d9fd9:tests/test_scheduler_v6_context_plan_retry.py | sha256sum
    03c84608a418455df5ea341d5ead01fde65c7c0c8ddfedd6fe00069d37c68858  -
    $ sha256sum tests/test_scheduler_v6_context_plan_retry.py
    03c84608a418455df5ea341d5ead01fde65c7c0c8ddfedd6fe00069d37c68858  tests/...

**PASS.**

## 2. Mutation proof, ON MAIN

5 passed → (pre-fix retry line restored) 2 failed / 3 passed → (fix
restored) 5 passed, with the test file's sha256 identical at every
step. Full transcript in `mutation.log`; table and the failing
assertion in REPRO.md §Results.

**PASS**, and it matches the result the originating commit recorded on
its own tree, which is what makes the transplant a transplant rather
than a new claim.

## 3. Full gate

    $ python -m pytest tests/ -q -n 4
    4694 passed, 6 skipped in 1624.94s (0:27:04)

**PASS — 0 failed.** No assertion was weakened and no fixture was
touched to get there; the only test file this tranche adds is the
regression one, taken verbatim.

Two things worth recording against `docs/AUDIT_BASELINES.md`:

- The baseline names a KNOWN-FLAKY set under `-n 4` — 3 tests in
  `tests/test_mcp_run.py` and 2 in `tests/test_mcp_scratch_bridge.py`,
  thread-join timing, green on a serial re-run. **None of them fired**,
  so no serial re-run was needed and none is being leaned on. Recorded
  because a green gate that happens not to have tripped the known
  flakes is worth distinguishing from one that tripped them and was
  re-run.
- The 6 skips are collection-level skips, not failures, and the
  baseline pins `0 failed` rather than a passed count — CLAUDE.md is
  explicit that the passed total moves every tranche and must not be
  pinned here.

Wall clock was **27:04**, roughly double the ~14 min CLAUDE.md
documents. That is this container being slow, not the suite growing:
the ring runs earlier in the tranche showed the same stretch
(53 scheduler tests in 29 s). Noted so a later reader does not read the
duration as a regression.

## 4. docs_verify

    $ python tools/docs_verify.py
    docs_verify [full]: 74 documents, 1320 checks, 4 workers
    docs_verify: 6 failed

**PASS — no delta from `docs/AUDIT_BASELINES.md`.** Six failures, and
every one of them is a recorded row. Neither of this tranche's two
re-expressed checks appears, and neither does `SUB-scheduler.md`'s new
`Traps` check; all three passed. (The 1320/74 totals are not pinned
values — AUDIT_BASELINES is explicit that the total moves with every
tranche that adds a check, and the failure LIST is what a delta is
measured against.)

Row by row, against the baseline's own classes:

| where | baseline class | disposition |
|---|---|---|
| `SEAM-llm-x-rules.md:54` | **known, pre-authorized** — check malformed, a lost closing backtick merges the check with the paragraph after it. Parked P3 (`experiments/2026-08-29-fix-docs-verify-multiline-checks/PARKED.md`) | `baseline` |
| `INV-frozen-surfaces.md:181` | **known, pre-authorized** — claim rotted: the census asserting zero committed `transport_failure` attempts; one exists, in a root committed 2026-08-26. Its repair is a design fork, parked P-D3 (`experiments/2026-08-30-fix-rotted-map-checks/PARKED.md`) | `baseline` |
| `CON-run-identity.md:211` | environment — shallow clone, git-history row | `baseline` |
| `CON-run-identity.md:213` | environment — shallow clone (`unknown revision 1637e808`) | `baseline` |
| `CON-run-identity.md:215` | environment — shallow clone (`unknown revision f304fec1`) | `baseline` |
| `CON-run-identity.md:298` | container-conditional — `TIMEOUT after 300s` | `baseline`, DISPOSED by re-run, below |

The two the tranche instruction pre-authorized as known-not-mine are
the first two: `SEAM-llm-x-rules.md:54` and
`INV-frozen-surfaces.md:181`. Both are parked elsewhere with named
owners, and neither is touched here.

The judge-canary row that the baseline lists separately — the
`INV-frozen-surfaces.md` check running
`price_compile_gap.py`, which does
`git show origin/claude/deepreason-p-s1-commitments-wowcib:…` — did NOT
fire, because that ref was fetched during setup. That is the baseline's
documented remedy, applied rather than discovered.

### Disposing of the conditional row, per the baseline's own procedure

AUDIT_BASELINES states the disposal in one line: re-run the check
alone; a PASS means the ceiling and the row is `baseline`, a FAIL means
the claim moved and it IS a finding. Re-run, verbatim:

    $ python -c "...CONTINUE_RECORD_NOT_VERIFIED / record_verification_refusal
                 / AMEND_RECORD_NOT_VERIFIED assertions..." \
        && python -m pytest tests/test_jailbreak_gate.py -q
    9 passed in 346.78s (0:05:46)
    rc=0

**PASS.** The 2026-08-29 integrity-gate claim is intact; the check
timed out on cost, not on truth. Corroborated independently: the full
gate ran `tests/test_jailbreak_gate.py` inside its 4694 passed / 0
failed, and nothing this tranche touched is anywhere near
`runtime/continuation.py` or `amendment/apply.py`.

One thing the re-run shows that the baseline does not yet record, and
that is worth a future runner's attention rather than mine: **346.78 s
STANDALONE, with no contention, already exceeds the 300 s per-check
ceiling** at `tools/docs_verify.py:185`. On this container the row is
not merely conditional, it is unconditional — it will time out on every
run here. That is the same class as the `SUB-application.md` row the
2026-08-31 tranche retired by narrowing a whole-file pytest run to the
four node ids that exercise the claim. It is NOT this tranche's goal,
so it is PARKED (`PARKED.md` P1) rather than fixed.

## What is NOT proven here, stated plainly

- **No live run was made.** The proof is offline and structural. The
  live evidence this fix answers to is the two roots in DIAGNOSIS.md,
  both of which predate the fix; nothing in this tranche demonstrates
  a v6 run surviving a stale context on a provider. The next v6 ladder
  that fires the scratchpad is the live test, and it is not owed by
  this tranche.
- **The reachability condition is unchanged.** `ConjectureContextStale`
  is still raised from the same three sites in `scratch/conjecture.py`,
  and the retry is still reachable only when the scratchpad is live.
  This fix makes that retry survivable; it does not make the stale
  context less likely, and no claim is made that it should.
- **The originating branch carries more than this.** Only the two
  files came across. Whatever else `claude/model-profile-registry-opkgal`
  holds is untouched by this tranche and is not asserted to be sound
  or unsound here.
