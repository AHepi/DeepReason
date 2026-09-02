<!-- tranche: 2026-09-02-defect-provider-transport-faults -->

# Goal: a provider transport fault must be visible, retried on a typed policy, and survivable past the ~300 s wall

Class: defect

Observed (from the typed record only; no code reading in this phase):

- **P-A1, run `4565139800f5ca02`** (branch `claude/live-reasoning-p-a1-bv65kl`,
  `experiments/2026-09-01-live-all-modules-p-a1/run/`, READ-ONLY). Ten of
  glm-5.3's 25 calls returned zero tokens after ~1215 s each: `tokens: 0`,
  `usage_unknown: true`, `raw_ref: ""`, `transport_attempts: 4`,
  `transport_diagnostics: ["RemoteDisconnected: Remote end closed connection
  without response"] x4` (seqs 62, 100, 106, 204, 211, 255, 266, 274, 419,
  480). 39 `RemoteDisconnected` + 1 `HTTPError` across the run, all on the
  glm-5.3 endpoint, none on any other model. Those ten calls are 3.27 h of a
  4.94 h run (66%). The longest attempt that ever returned tokens was 271 s;
  nothing over ~280 s ever came back. The harness's own `timeout_s` was 1800
  and never fired, so the wall is outside the harness.
  Evidence pointer: `experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md`
  (on `main`), rows F6 and F7 and the Re-derivation block.
- **P-S1, run `9e48a36b1dec91ee`** (branch
  `claude/deepreason-p-s1-commitments-wowcib`,
  `experiments/2026-08-31-p-s1-commitments/`, READ-ONLY). 15 of 24 cycles ran
  against a dead provider; 54 transport failures typed in
  `workflow-provider-attempt-v1` objects; ZERO summary document mentions them.
- **The monitor blindness.** P-A1's own `monitor.sh` was written to catch this
  and raised 0 alerts on 40 faults, because it tested keys (`error` /
  `failure` / `status`) the attempt trace does not carry. The typed signature
  is `transport_diagnostics` / `tokens == 0` / `usage_unknown`.

Restated as ONE checkable statement: **a provider transport fault is recorded
in the per-attempt trace and nowhere an operator or a monitor looks — not in
`progress.jsonl`, not in `deepreason results`, not in any summary — and the
retry ladder answers it by resending the identical request into the same wall
four times.**

## Success criterion (machine-decidable)

Against a deterministic offline stub provider that closes the connection after
N seconds having written no body, and a second stub that emits bytes past N
seconds:

    python -m pytest tests/test_provider_transport_faults.py -q
    # expected: all pass, and each test is mutation-proven RED on the
    # pre-fix tree (RED transcripts committed under proof/).

The suite must pin, one test per clause:

1. the fault is recorded typed (attempt outcome + diagnostics), unchanged in
   shape from today;
2. `progress.jsonl` carries a per-seat provider-fault counter row field
   (attempts, faults, zero-byte returns, last fault kind);
3. `deepreason results` prints a typed "provider health" block, and prints a
   typed absence when there is nothing to report;
4. the second attempt is **not byte-identical** to the first — the typed
   policy either shrinks the cap or stands the leg down, per the policy
   specified in FIX.md;
5. a streaming stub that emits bytes past N seconds completes, where the same
   call non-streaming does not;
6. N consecutive zero-byte attempts on one seat emit a typed notice
   (disclose, never die).

Plus the whole-tree gate:

    python -m pytest tests/ -q -n 4
    # expected: 0 failed (pre-authorized baselines recorded, not stopped on:
    # the bc-dependent map check, and
    # test_the_shipped_qualification_subject_digest_does_not_move)
    python tools/docs_verify.py
    # expected: no NEW failure attributable to this tranche

## Phase 0 gate (precedes design; falsifiable, pre-registered)

`PREREG.md` freezes P1/P2/P3 before the first live call. If **P2 is FALSE**
(streaming does not survive past the wall), clause 5 above is struck and the
tranche STOPS and reports with the measurement, per the executor instruction.

## Map ids (resolved before design)

| touched | id | document |
|---|---|---|
| transport retry, endpoint completion call | `DR-SUB-llm` | `docs/map/SUB-llm.md` (Owns `src/deepreason/llm/`) |
| attempt outcome -> `workflow-provider-attempt-v1` | `DR-SEAM-llm-x-workflow` | `docs/map/SEAM-llm-x-workflow.md` |
| what `verify_root` reads of an attempt | `DR-SEAM-llm-x-verification` | `docs/map/SEAM-llm-x-verification.md` |
| seat -> provider request | `DR-CON-seats` | `docs/map/CON-seats.md` |
| `progress.jsonl` writer, `deepreason results` renderer | `DR-SUB-application` | `docs/map/SUB-application.md` (Owns `src/deepreason/application/`, `src/deepreason/cli/`, `src/deepreason/runtime/`) |
| what may not be touched | `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` |
| versioned-artifact + FREE-parameter pattern for the retry policy | `DR-INV-signal-contract` | `docs/map/INV-signal-contract.md` |

Read order enforced: `INDEX.md` -> `INV-frozen-surfaces.md` -> the seams ->
the subsystems.

## In scope (max 3 subsystems)

1. `src/deepreason/llm/endpoints.py` — the transport/retry path and the
   completion call.
2. The `progress.jsonl` writer and the `deepreason results` renderer under
   `src/deepreason/application/` + `src/deepreason/cli/` (excluding the two
   files another window owns, below).
3. A new versioned retry-policy artifact with FREE parameters in
   `src/deepreason/config.py`.

## NOT in scope

- **Files owned by other live windows — STOP and ask if the fix needs them:**
  `src/deepreason/llm/providers.py`, `src/deepreason/llm/split.py`
  (model-profile registry window); `src/deepreason/application/text_runs.py`,
  `src/deepreason/runtime/continuation.py` (failed-terminal continuation
  window).
- **Frozen surfaces:** `capabilities/state.py`, `harness.py`, `invariants.py`,
  `verification/`, `run_manifest.py`, `qualification.py`; and the
  frozen-ADJACENT `route_fingerprint` in `llm/firewall.py`. Nothing entering
  `route_sha256` or the manifest may move.
- **The transport-failure census check** at `docs/map/INV-frozen-surfaces.md:181`
  is a recorded baseline. It is not to be "fixed" by changing what it counts.
- The nearest tempting neighbour: **retiring a dead seat and continuing on the
  others** (seat degradation). Parked, not built.
- glm-5.3's reasoning-knob values and the split protocol's extraction leg.
- Failed-terminal continuability.
- Any live reasoning run beyond the ~20 pre-registered probe calls.
- No committed run root is touched. Old roots owe nothing (law 2026-08-14).

## Budget

**Stated honestly, as an exception the operator's instruction already
authorises.** `dr-set-goal`'s default is <=150 changed lines and one commit.
This goal carries three obligations the executor instruction binds together as
one goal — visibility, a typed retry policy, and surviving the wall — and
those will not fit in 150 lines. Planned: one commit per obligation plus the
probe, ~400 changed lines total including tests. If any single obligation
alone threatens to exceed ~150 lines of production code, that obligation is
split and the remainder parked.

Stop conditions inherited from orchestrator: yes. Additionally, per the
executor instruction, STOP AND ASK on: P2 false; any frozen or frozen-adjacent
contact; any manifest or route-bytes change; the dead-provider-streak stop
question; anything needing a file another window owns.
