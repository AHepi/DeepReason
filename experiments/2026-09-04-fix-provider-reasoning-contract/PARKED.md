# Parked — noticed by this tranche, deliberately not fixed here

One tranche, one goal. Both entries below are MODEL facts measured
incidentally by this tranche's probe. `DR-CON-model-profiles` makes a
model's settings a document a human writes, never a source edit, so
neither belongs in this tranche's `llm/` scope and neither is touched.

---

## P1 — `gpt-oss:120b` still thinks at the value that silences every other model

**What.** In the 2026-09-04 probe, `reasoning_effort: "none"` returned
zero reasoning characters on `qwen3.5:397b`, `glm-5.2`, `kimi-k2.6`,
`deepseek-v4-pro` and `glm-5.3`, and 311 on `gpt-oss:120b`. That model
carries a committed reference document at
`docs/model-profiles/gpt-oss:120b/agent.md`. Whether the document says
this, and what its emission leg should send instead, is unread by this
tranche — the goal put model-profile documents out of scope.

**Ready to send:**

```
Route: dr-change-orchestrator (a change: a model's document, not code).
Goal: bring `docs/model-profiles/gpt-oss:120b/agent.md` into agreement with what
the model measurably does. Measured 2026-09-04: `reasoning_effort: "none"`
returns 311 characters of reasoning on this model where the other five models in
the same probe return zero, so "none" does not switch thinking off here and any
seat budgeting on the assumption that it does is budgeting wrong.
Evidence: experiments/2026-09-04-fix-provider-reasoning-contract/PROBE.json
(rows with model `gpt-oss:120b`); docs/OLLAMA_CLOUD_OPERATIONS.md section 9,
"Two model facts the same probe measured"; PARKED.md P1 is this entry.
End state: the document's `reasoning` block states what each value does on this
model with the probe as its evidence line, and names the command that re-checks
it — or the document records that it was checked and needed no change.
```

---

## P2 — `glm-5.3` at `none` put its trace in the answer channel, live, again

**What.** One probe row returned, as `message.content`, "The user is
asking me to reply with exactly this JSON and nothing else: {"ok":true}
/ This is a simple, harmless request." — the reasoning, in the content
field, ahead of the answer. This is the exact mechanism
`docs/map/SUB-llm.md` already records ("`none` does not stop the
thinking there, it stops the SEPARATION") and that killed three runs
before the model-profile tranche. Nothing is broken: the model's
committed document already says to use `low`, and `low` returned clean
content in the same probe. It is parked because a live re-confirmation
of a recorded trap is worth an evidence line in the document that
carries the claim, and this tranche may not write one.

**Ready to send:**

```
Route: dr-change-orchestrator (a change: a model's document).
Goal: add the 2026-09-04 live re-confirmation as an evidence line on
`docs/model-profiles/glm-5.3/agent.md`, where the claim "none moves the trace
into the content" currently rests on the 2026-09-01 measurement alone. One row
of a 45-call probe reproduced it verbatim three days later, on the current
fleet, at a 2000-token cap.
Evidence: experiments/2026-09-04-fix-provider-reasoning-contract/PROBE.json
(model `glm-5.3`, reasoning_value `none`, its `content` field); the standing
claim is in docs/map/SUB-llm.md Traps, "Unset reasoning is not off".
End state: the document carries the second measurement with its date and
transcript path; no code changes.
```

---

## P3 — a budget denial at 114 226 of 120 000 tokens terminated `operational_failure`, not `budget_exhausted`

**What.** This tranche's own verification relaunch,
`experiments/2026-09-04-fix-provider-reasoning-contract/relaunch-home/runs/run-ecd1a8d2461eff1eddd9756b51336ce5`,
stopped `state: failed`, `stop_reason: operational_failure`, message
`token budget denied transactional work sha256:c01bc9d1...`, having spent
114 226 of the 120 000 tokens it was given. CLAUDE.md's operator law of
2026-08-29 says a budget denial on an exhausted budget terminates
`budget_exhausted` and clean, never `operational_failure` — the operator's
own words were "clean stop. with an assurance that continuing is
possible." The assurance half holds: `continue` and `amend` are both
ACCEPTED and the record replays valid with zero violations. It is the
CLASSIFICATION that looks wrong, and only that.

Not adjudicated here, deliberately: whether the harness should treat "the
next reservation does not fit in the remaining 5 774 tokens" as exhaustion
is a design question this tranche has no mandate over, and the run was a
verification instrument rather than the subject.

**Ready to send:**

```
Route: deepreason-orchestrator (defect).
Goal: decide whether a token-budget denial raised when the remaining budget
cannot cover the next reservation is an exhausted budget, and make the terminal
match the answer. Today it terminates `state: failed`, `stop_reason:
operational_failure`; the operator's 2026-08-29 law says a budget denial on an
exhausted budget is a clean `budget_exhausted`. The run had spent 114226 of
120000 tokens, so this is the exhaustion case if anything is.
Evidence: experiments/2026-09-04-fix-provider-reasoning-contract/relaunch-home/
runs/run-ecd1a8d2461eff1eddd9756b51336ce5 (run-status.json, its 29
workflow-provider-attempt-v1 objects all `provider_result`, REPLAY_VALIDATION
valid with 0 violations); `deepreason stop-report` on it rules ENVIRONMENT out,
so nothing about the provider is involved; PARKED.md P3 is this entry. The law
is CLAUDE.md, "Exhaustion is a clean stop".
Note the law's other half already holds and must not regress: `continue` and
`amend` are both ACCEPTED on this root, so whatever changes must keep
continuability intact.
End state: a budget denial on an exhausted budget reaches `budget_exhausted`,
with a regression driving a run to that boundary, and the distinction between
this case and a genuine operational failure stated where the next reader will
find it — or the record says why `operational_failure` is right here and the
law does not reach this case.
```

---

## Not parked, because it is this tranche's own finding, now corrected

The premise of `experiments/2026-09-04-experiment-blind-critic/PARKED.md`
P2 — that the committed launch config sends the refused field — is wrong,
and is corrected in `docs/ERRATA.md` E76 rather than parked. That
tranche's own file is left unedited, per the errata ledger's rule.
