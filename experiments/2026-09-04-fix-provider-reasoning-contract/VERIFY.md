# Verification

## Criterion 1 — offline regression, mutation-proven

    $ python -m pytest tests/test_provider_reasoning_wire_contract.py -q
    ...                                                                      [100%]
    3 passed in 0.05s

Mutation proof, four deliberate edits to `llm/providers.py`, each reverted:

    M1 ollama emits a bare `reasoning` STRING (the refused shape) -> 3 failed
    M2 ollama's int budget collapses to the inverted effort        -> 1 failed
    M3 deepseek's disable rewritten to a bare `reasoning` string    -> 2 failed
    M4 the generic no-op starts carrying the value                  -> 2 failed
    reverted, git diff --stat src/deepreason/llm/providers.py empty -> 3 passed

## Criterion 2 — one guarded live call per provider profile in the catalog

Run twice, and the two runs disagreed. Both are committed; neither is
discarded.

**Run A** (`PROBE.json`, 2026-09-04): 42 of 42 harness-built bodies
accepted, across all six models and all seven values. The single refusal
is the hand-built control.

**Run B** (`PROBE_VERIFY.json`, later the same day):

    harness rows: 42  accepted: 35  contract-refused: 0  unavailable: 7
    models unreachable during this run (says nothing about the shape): ['deepseek-v4-pro']

    GOAL CRITERION 2 (no committed catalog profile refuses the harness's
    reasoning field; unreachable models are not counted against it): MET

    qwen3.5:397b  bare-reasoning-string  reasoning  http=400  CONTRACT_REFUSED
      json: cannot unmarshal string into Go struct field
      ChatCompletionRequest.reasoning of type openai.Reasoning
    qwen3.5:397b  reasoning-object       reasoning  http=200  ACCEPTED  reas=0
    qwen3.5:397b  think-false            think      http=200  ACCEPTED  reas=1111

### The instrument was corrected during verification — say so plainly

Run B's seven failures were all `deepseek-v4-pro`, all HTTP 503
`model 'deepseek-v4-pro:0813' is temporarily overloaded`. The probe's
first verdict counted any non-200 as a failure of the criterion, so it
reported NOT MET — a verdict about fleet capacity wearing a verdict
about the request shape. That is the same hazard the previous tranche
parked as its P3: a measure that reports something other than what it
names.

The discriminator, measured rather than assumed — six calls alternating
the knob off and on, three seconds apart:

    #0 value=None   http=503  FAIL      #1 value=low  http=503  FAIL
    #2 value=None   http=503  FAIL      #3 value=low  http=503  FAIL
    #4 value=None   http=503  FAIL      #5 value=low  http=503  FAIL

The no-knob control fails identically, so the outage is the fleet and not
the field. `probe_reasoning.py` now classifies each row ACCEPTED /
CONTRACT_REFUSED / UNAVAILABLE and fails the criterion only on a contract
refusal, or on an unavailability that IS attributable to the field — a
model that serves the no-knob request and fails every knob-set one.

Proven able to fail, four scripted providers through the real `main()`:

    A: everything served                                        rc=0  MET
    B: one model 503s on every value incl. no-knob (observed)    rc=0  MET
    C: 503 ONLY when the knob is set                             rc=1  NOT MET
    D: the provider refuses reasoning_effort with 400            rc=1  NOT MET

Across both runs every model in the committed catalog has been accepted
at every value of the neutral vocabulary at least once, and no run has
ever produced a contract refusal for a harness-built body.

## Criterion 3 — the provider's contract is recorded

    $ grep -q "ChatCompletionRequest.reasoning" docs/OLLAMA_CLOUD_OPERATIONS.md
    exit 0

Section 9, with the transcript path, the accepted and refused shapes, the
auth-before-body-parse finding, and the two model facts.

## Criterion 4 — nothing else moved

    $ python -m pytest tests/ -q -n 4
    5024 passed, 6 skipped in 1080.60s (0:18:00)

    $ python tools/docs_verify.py
    docs_verify: 6 failed

All six are documented baseline rows (`docs/AUDIT_BASELINES.md`: "on this
container's SHALLOW clone the total is 5 OR 6 failed"): three git-history
rows in `CON-run-identity.md`, two in `INV-frozen-surfaces.md`, and the
known malformed check at `SEAM-llm-x-rules.md:54`. No delta.
`SUB-llm.md` was re-derived on its own — **24 checks, 0 failed**,
including the new trap's check — which is why its `Verified-at:` was
advanced.

## The goal's third clause — a relaunch reaching its first seat result

Soak first, as CLAUDE.md requires before any live launch:
`python -u scripts/cycle_soak.py --case reach-rich` → `[soak] exit 0 (clean)`
(`SOAK.txt`).

`relaunch.sh` then rebuilt the committed launch config's provider profile
field for field — solo `qwen3.5:397b`, `--reasoning none`, 131072 window,
8192 completion cap — in a FRESH home, and launched detached.

    === setup     rc=0
    === qualify   rc=0     (full battery, ~3m45s, a fresh home so no cache hit)
    === reason    rc=4

Run `run-ecd1a8d2461eff1eddd9756b51336ce5`, typed outcome:

    state           = 'failed'
    stop_reason     = 'operational_failure'
    message         = 'token budget denied transactional work sha256:c01bc9d1…'
    provider attempts: 29, outcomes {'provider_result': 29}
    completion tokens: 31225   logged_tokens: 114226 of a 120000 budget
    artifacts: 41 admitted, 41 accepted
    REPLAY_VALIDATION valid: True, violations 0
    continue: ACCEPTED   amend: ACCEPTED

**The clause is met.** The relaunched run reached its first seat result
and then 28 more: 29 provider attempts, every one `provider_result`, 41
artifacts admitted and accepted, and a record that replays valid. The
stop report rules ENVIRONMENT out explicitly — "no HTTP 429, no
transport-fault streak, and no qualification case carrying an environment
failure code" — so nothing about the reasoning field entered this stop.
Qualification is itself corroboration: a full battery of live seat calls
carrying `reasoning: none`, passed 20/20 first-pass on every form.

## Verdict: PASS

All four criteria met, and the goal's third clause proven live.

## Residue (honest)

- **The relaunch stopped `operational_failure` on a budget denial with
  114 226 of 120 000 tokens spent.** CLAUDE.md's 2026-08-29 operator law
  says a budget denial on an exhausted budget must terminate
  `budget_exhausted` (clean), never `operational_failure`. This looks
  like that case and is PARKED as P3, not adjudicated here: whether the
  harness treats "the next reservation does not fit in the remaining
  5 774" as exhaustion is the follow-up's question, not this tranche's.
  Continuability, the law's other half, does hold — `continue` and
  `amend` are both ACCEPTED.
- **One live probe is one moment.** `deepseek-v4-pro` was served in run A
  and unreachable in run B, hours apart. The contract measured here is a
  measurement with a date, not a guarantee; the operations document says
  so and names the command that re-checks it.
- **Two providers in the adapter table were never probed.** `deepseek`
  and `openai` have no committed provider profile pointing at them, so
  their mappings are pinned by the regression and asserted from the
  committed table, not measured live.
- **The 400 was reproduced on one model only.** The refusal control ran
  against `qwen3.5:397b` in both runs. Whether every model behind
  `ollama.com/v1` refuses the bare string identically is untested; the
  error is emitted by the gateway's request decoder rather than by a
  model, which makes per-model variation unlikely but not measured.
- **The commit's diff exceeded its ceiling.** `DIFF_BUDGET_RESULT_V1`
  verdict EXCEEDED, 324 insertions against 160, zero under `src/`.
  Disclosed in FIX.md with its disposition rather than trimmed.

## Errata

`docs/ERRATA.md` **E76** — PARKED P2's premise, that the newest committed
launch config sends the refused field. Landed with the fix commit rather
than with VERIFY.md because the correction and the pin that enforces it
belong together; recorded here as this tranche's errata entry.
