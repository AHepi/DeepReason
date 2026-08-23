# Delivered: the two-call seat protocol

Branch: `claude/two-call-seat-protocol-mmaaf5` @ `4df372339` (pushed, tree
clean). 17 commits from the tranche base `e1ea05e82`.

## What changed

A seat call — one request to the model on behalf of one role — is now two
provider legs against the same route, the same lease and the same
authorization. Leg `reason` deliberates in free prose at `B_r` with the route's
own reasoning setting, carries no schema and no `response_format`, and is
allowed to come back empty or cut off. Leg `extract` is then handed whatever
trace exists — truncated, recovered from the provider's reasoning side channel,
or entirely absent — and does nothing but serialize it into the wire contract at
`B_a`, with thinking switched off so its whole budget reaches the answer.

`B_a` is taken OUT of the ceiling rather than added to it: the emission leg
takes at most half, and at least 256 or the ceiling is not divided at all. So
`B_r + B_a == ceiling` by construction, and neither leg nor their sum can escape
the bound `EndpointLease.verify` binds and the controller is clamped to (E43).

Nothing refuses. A seat that cannot be split runs exactly as it did before and
records a typed notice naming which reason: a repair authorization, a route
enforced at the sampler, a ceiling too small to divide, a provider with no
reasoning knob, an emission request over the frozen envelope, or no token
headroom.

New code: `src/deepreason/llm/split.py` (the pure planner and the two request
renderers), `LLMAdapter._split_plan` / `_dispatch_split` in
`src/deepreason/llm/adapter.py`, per-request `max_tokens` / `reasoning` /
`json_mode` overrides and reasoning-trace capture in
`src/deepreason/llm/endpoints.py`, two `Config` fields, four defaulted
`LLMAttempt` fields, and two `data.pop` lines in `run_manifest.py` under the
operator's grant. Proven by 22 new regressions plus a full gate at **3857
passed, 0 failed**.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "a seat call becomes reason-at-B_r then a separate non-thinking extraction pass at B_a ... feeding the possibly-truncated trace" | done | `3811f9975`, `e2bd28c57`; VALIDATION S1/S2/S3 |
| R2 | "a per-profile Config choice with the default ON for reasoning-model profiles (glm-5.2), OFF where a profile is non-thinking" | done-with-assumption **A1** | `3811f9975`; VALIDATION S5, `test_the_shipped_glm_seat_actually_arms` |
| R3 | "All configurations compile (typed notice, never refusal, where a provider cannot honor the mode)" | done | `3811f9975`; VALIDATION S7 |
| R4 | "a truncated reasoning trace yields an answer instead of an empty seat failure" | done | `3811f9975`; VALIDATION S7 |
| R5 | "read both sections IN FULL and ledger them" | done | `689cd12bc` REQUEST.md AUTHORITY block; SPEC.md cites Q7 and the coercion note at the items they govern |
| R6 | "whether the reasoning call terminated on its own becomes a typed per-attempt field" | done | `1ec56586b`; VALIDATION S6 |
| R7 | "Recorded, not acted on — no gate or label may consume it" | done-with-assumption **A4** | `286409e25`; VALIDATION S8, three mutations shown red |
| R8 | "the extraction call's schema is the minimal envelope" | done | `3811f9975`; VALIDATION S7 |
| R9 | "both calls' token budgets sit inside the route lease ceiling" | done-with-assumption **A5** | `3811f9975`; VALIDATION S1 |
| R10 | "add the regression that the split never exceeds it" | done | `3811f9975`; six-ceiling sweep plus a wire-level assertion |
| R11 | "the old path yields the empty-completion typed failure, the new path yields the extracted answer; mutation-proven" | done | `2daeb1ff9` (RED first), `3811f9975` |
| R12 | "Wheel smokes only if the public surface moves (it should not)" | done | `23bb8bf66`; VALIDATION S4 — packaging surface untouched, smoke not owed |
| R13 | "state which profiles moved and the requalification price per home" | done | `07312ba52`; VALIDATION S10 — **none moved, price zero** |
| R14 | "ring while iterating; full gate at the boundary; docs_verify full. Map moves in the same commits" | done | `23bb8bf66`, `ecfb7b2e9`; VALIDATION Full gate + Map |
| R15 | "Commit and push every phase boundary" | done | 17 commits, each pushed with retry |
| R16 | "Deliver R-by-R with pasted PROOF" | done | this document |
| R17 | (Amendment 1) row the eight measured frozen-surface false positives; no writes to the five surfaces | done, **superseded in one place by R19** | `b2fbf415e`; VALIDATION Frozen-surface diff |
| R18 | (Amendment 1) "the extraction leg rides the bundle ... refused, with a typed notice, on any repair bundle" | done | `b2fbf415e`, `3811f9975`; two regressions |
| R19 | (Amendment 2) "Insertions only, 11 and 0, into the function that exists for exactly this" | done | `ee73c815c`; frozen-surface diff shows 11 insertions, 0 deletions, that function only |

Nineteen requirements, nineteen dispositions, none deferred and none not-done.

## Assumptions the operator may override

- **A1** — "reasoning-model profile" means the seat's ROUTE, not `ModelProfile`,
  because the presentation profile says nothing about whether a model thinks.
  Since validated on a real compiled setup profile rather than left assumed.
- **A2** — a per-call reasoning override is admissible because it never mutates
  the endpoint, so the frozen lease still verifies. Extended during execution to
  a `json_mode` override on the deliberation leg, on the same reasoning.
- **A3** — the split applies to attempt 0 only; repair turns are
  extraction-shaped by construction.
- **A4** — R7's negative is proved twice: a reference census and a behavioural
  mutation test.
- **A5** — `B_a = min(512, ceiling // 2)` with a 256 floor. The flat
  `min(512, ceiling)` rule the spec started from handed a 513-token ceiling's
  reasoning leg one token; the parametrised regression caught it.

## Map delta

changed: `docs/map/SUB-llm.md`, `docs/map/SUB-ontology.md`,
`docs/map/CON-seats.md`, `docs/map/INV-frozen-surfaces.md`. created: none.
new checks: **3**, each mutation-proven red before being written down —
the four `LLMAttempt` fields plus the `natural_stop` no-consumer census
(`SUB-ontology`), the one-seat-one-lease-one-authorization rule with its
ceiling arithmetic (`CON-seats`), and the no-`SPLIT_BUDGET_`-key-in-the-manifest
guard (`INV-frozen-surfaces`).

`Verified-at:` advanced on eight documents (the four above plus
`SEAM-llm-x-workflow`, `CON-schools`, `SUB-manifest`,
`SEAM-manifest-x-schools`, whose owned files this tranche moved without
editing) — and only because the full `docs_verify` run re-ran all 982 checks
green.

left stale: five, each naming a commit from another tranche and none this
tranche's to clear — `CON-run-identity.md`, `SEAM-evaluation-x-rules.md`,
`SEAM-llm-x-scheduler.md`, `SUB-evaluation.md`, `SUB-scheduler.md`.

## Errata

**E44** added (`ee73c815c`, rewritten from the draft in `72b9ecd0d`):
`INV-frozen-surfaces.md`'s "a `Config` value costs nothing to add and is
invisible to replay" omitted the step that makes the first half true — the key
must also be dropped in `run_manifest.py::_versioned_source_config_data`, where
eight prior knobs already sit. Without that step the qualification subject
digest moves and 22 frozen manifest goldens move with it. The entry also
records that this tranche's own first two answers to the question were wrong in
two different directions, and that the admissible answer is a before/after
digest plus a payload diff plus the full gate — never a signature, a grep, or a
digest comparison alone.

## Parked (not done, not promised)

**P1 — the extraction leg cannot ride a REPAIR authorization bundle.** A repair
turn that burns its cap on hidden reasoning still dies the old way, by the R18
guard's design.

    Route: dr-change-orchestrator.
    Goal (one): extend the two-call seat protocol to v6 repair attempts, so a
    repair turn that burns its completion cap on hidden reasoning yields a
    patch instead of a typed failure.
    Evidence pointers: experiments/2026-08-22-change-two-call-seat-protocol/
    SPEC.md QO2 and A3; src/deepreason/llm/adapter.py's transactional repair
    guard ("transactional repair requires a new authorization bundle");
    src/deepreason/workflow/repair_transaction.py.
    End state: a repair attempt splits under the same ceiling law as attempt 0,
    with the same typed notices; offline regression mutation-proven; full gate
    0 failed.

**P2 — the provider's reasoning payload is discarded on every NON-split call.**
This tranche captures it, but only the split path consumes it; an ordinary
failing call still stores no trace in its diagnostic blob.

    Route: deepreason-orchestrator (defect-shaped: evidence is being dropped
    from the typed record).
    Goal (one): a completion that dies with null or truncated content records
    the provider's reasoning payload in its diagnostic blob, so the blob-first
    diagnosis rule has something to read.
    Evidence pointers: src/deepreason/llm/endpoints.py's null-content
    EndpointError; experiments/2026-08-22-change-two-call-seat-protocol/SPEC.md
    M10; CLAUDE.md's "READ THE DIAGNOSTIC BLOB before theorising" invariant.
    End state: the diagnostic blob for a null/truncated completion carries the
    reasoning payload when the provider returned one; regression pinned; full
    gate 0 failed.

**recommended next: P2.** It is the smaller of the two, it is defect-shaped
rather than design-shaped, and it repairs a gap in the one discipline CLAUDE.md
names as having been violated twice already — the diagnostic blob is supposed
to be the first thing a reader opens after a cycle-0 death, and on the exact
failure this tranche exists for, that blob is currently empty.
