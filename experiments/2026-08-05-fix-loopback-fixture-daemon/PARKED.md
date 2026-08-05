# Parked — noticed during the S1 tranche, not done

## T1 — the qualify stage pins an OPTIMISTIC call count that reality does not satisfy (blocks GOAL's end state)

With the shadowing hang fixed, the smoke reaches and completes
qualification and then fails an exact-count assertion:

    stage=qualify  failure_kind=assertion_failed  timeout=False

    observed: total_calls = 300, qualification_calls = 80, provider errors = 0
    pinned  : total_calls = 280, qualification_calls = 80

`qualification_calls` matches the pin exactly. Only `total_calls` differs,
and the fixture's own per-contract breakdown says why:

    BoundBridgeCompositionWireV2   40   <-- 2 calls per case
    ClaimLedgerWireV2              40   <-- 2 calls per case
    (11 other pairs)               20   <-- 1 call per case
    AtomicConjectureCandidateWireV1 10 + AtomicReasoningConjectureCandidateWireV1 10
                                        (one pair split across two titles)
    sum = 300 across 14 titles

The smoke's own comment states the model it pinned: "4 bridge pairs x 20
cases x 2 provider calls (the bridge grants one schema repair) ... and
one clean pass makes exactly 14 x 20 = 280 loopback calls." So a second
call for a bridge contract is WITHIN the design's granted budget and
within the frozen maximum of 840; what is violated is only the optimistic
assumption that every contract passes first time. Two bridge contracts
now take their granted repair on every case.

**This is the operator's original suspect window, arriving one layer
below where it was first looked for.** It is not a request shape the
fixture predates — the fixture serves fine and records zero provider
errors — but the contract surface HAS moved since the pin was written,
and the pin encodes the old shape.

**Why it is parked rather than fixed here:**

1. **One tranche, one goal.** This tranche's named defect — the daemon
   not starting — is fixed and committed. This is a distinct defect with
   a distinct cause.
2. **It requires loosening an assertion, which is repo law's sharpest
   edge.** "Never weaken an assertion to get green." Changing 280 to 300
   would make the smoke pass while asserting the same brittle thing one
   notch further along; it would break again the next time a contract
   family changes. The right fix almost certainly states the PROPERTY —
   qualification completed, zero provider errors, total within the frozen
   maximum, each family within its own granted per-case budget — which is
   the identical lesson to the P1 tranche's expired-census readers, in a
   third location. That is a design decision, not a numeral edit.
3. **One thing is genuinely unverified**: whether those two bridge
   contracts SHOULD need their repair on every case, or whether
   first-pass validity there is itself a regression. Zero provider errors
   and an unchanged `qualification_calls` argue the fixture is healthy,
   but the doctor report that would settle it is deleted with the temp
   directory on failure (see T2). Re-pinning before answering that would
   bless a possible regression.

Suggested disposition: its own tranche, starting by capturing the
qualification doctor report for the two bridge pairs.

## T2 — the operational smoke conceals its own failures, three ways

Each of these cost real time this tranche and together they are why the
S1 defect took three tranches to name:

1. `_run` discards the child's `stdout`/`stderr` on
   `subprocess.TimeoutExpired` (line ~1475: raises
   `OperationalSmokeFailure(...) from None`, never reading
   `TimeoutExpired.stdout`/`.stderr`). The hang's cause lived in exactly
   that discarded stream.
2. `except AssertionError:` (line ~3610) builds the typed record with no
   message and no traceback, so a failed assertion names its stage and
   nothing else. Finding which of the qualify stage's two assertions
   fired required reading the source and instrumenting from outside.
3. `--keep` preserves the temp directory only on SUCCESS
   (`if succeeded and args.keep`), i.e. never when there is something to
   inspect. The counts in T1 had to be captured by an external poller
   copying the state file mid-run.

None is the cause of any failure, so none was fixed here. All three are
cheap and would have turned a three-tranche diagnosis into a one-command
one.

Suggested disposition: one small change tranche over all three.

## T3 — dead code left in place, deliberately

`_provider_server` and `ProviderState` in
`scripts/wheel_operational_smoke.py` are unreferenced in all 14 commits
of the file's history (AST-verified) and are NOT the fixture in use —
the sitecustomize is. They were left untouched because deleting ~70
lines in the same commit that fixed a hang would obscure which change
made the smoke progress. Removing them is a clean follow-up.

## T4 — `_unused_loopback_port` binds then releases

It binds port 0, reads the assigned number, closes the socket, and
returns the bare integer, so another process may claim the port before
the child binds it. Not implicated in this defect (the port was free and
simply never bound), but it is a real race.

## T5 — carried, still parked

From earlier tranches and untouched: P1a (ERRATA E5 misidentifies the
no-manifest roots), P1b (delivery measures before its own evidence
commits), P1e (a `src/` mutation inside a git worktree is never loaded
under an editable install), S2 (duplicate MCP pins across both smokes),
S3 (`docs/map/` covers no part of `scripts/`), and P7 (the round-robin
arm's `attempt-validity` violation).
