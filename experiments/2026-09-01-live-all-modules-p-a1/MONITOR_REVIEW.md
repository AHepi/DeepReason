# Monitor review of the P-A1 delivery (independent read of the record)

Date: 2026-09-01. Reviewed: branch `claude/live-reasoning-p-a1-bv65kl` at
`00c2d5836`, run `4565139800f5ca02…`. Everything below was re-derived from
`run/log.jsonl`, `run/objects/`, `run/blobs/` and the source on `main`; no
claim rests on the window's prose. Commands are given so each line can be
re-run against the branch.

## Verdicts on the window's findings

| window claim | verdict | what the record says |
|---|---|---|
| Judges fired live; zero `scrutiny`; explicit policy closed P-S1's gap | AGREE | 0 lines mention `scrutiny`; 4 `judgeruling.direct.v1` calls (qwen ×2, gpt-oss ×2) |
| "Six trials ran; all six DECLINED; the unanimous ensemble under-convicted" | DISAGREE (over-read) | 4 of the 6 `trial-declined` events are `execution-backed` = formal supremacy preflight (`informal/trial.py:962-974`): the target was formally backed, so NO seat was called. Only 2 trials reached judges. In both, the judges DISAGREED in opposite directions: trial 1 qwen `pass` / gpt-oss `fail`; trial 2 qwen `fail` / gpt-oss `pass` (typed `verdict` fields in the raw blobs of seqs 396/401/559/564). Each judge convicted once. The unanimity rule blocked both. "Judges under-convict" is not what n=2 shows; "judges disagree and unanimity zeroes them" is. |
| Six trials total | DISAGREE (undercount) | Trials by target: 4 preflight-declined; 4 reached the defender. Of those 4, the defender call returned ZERO tokens on 4 attempts (seqs 100, 204, 255, 266); two targets (f3f96ed…, 3d82a99…) never got a typed trial outcome at all — the attempt ends in `criticism.attempt.v1` + coverage debt with no `trial-declined`. Target 4c65c1e… failed twice on transport and succeeded on the third cycle. |
| F5: "glm-5.3 takes ~20 min per conjecture; the call SUCCEEDED, no transport fault; generation speed, not breakage" | DISAGREE (wrong mechanism) | Every ~1215 s glm call has `tokens: 0`, `usage_unknown: true`, `raw_ref: ""`, `transport_attempts: 4`, `transport_diagnostics: ["RemoteDisconnected: Remote end closed connection without response"] ×4` — four ~300 s connection drops with retries, nothing generated. 10 of glm-5.3's 25 calls (6 conjecturer, 4 defender) are this shape. Across the run: 39 `RemoteDisconnected` + 1 `HTTPError`, all on glm-5.3; zero on any other model. When glm did answer (from seq 386 on), the reason leg took 245–280 s and mostly hit truncation. |
| F4 defect 1: one seat's exhaustion kills the run | AGREE | `workflow-route-seat-insufficient-capability-v1`: seat 1 glm-5.3, `smallest_authorized_contract_schema_exhausted`; deepseek seat 0 healthy. Amendment: the exhausted seat is the seat whose provider had been dropping connections all run; the contract ladder ran out AFTER a 10-call transport-failure streak and cap-truncated outputs, so the transport layer belongs in the root cause. |
| F4 defect 2: failed terminal not continuable, violating the 2026-08-29 law | AGREE | `run-status.json`: `terminal_lifecycle_refusal: TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`; `verify_root` 0 violations. Intact and unusable. |
| F2: `hv` structurally unreachable on any v6 run | AGREE (verified in code) | `scheduler/scheduler.py:696-752` `_defer_untransactional_v6_phase` returns True for every v6 manifest; reads no grant, route or Config field. `reach` unaffected. |
| D1: frontier 1 seed / 13 harness-minted | AGREE | `frontier.txt`: 1 seed, 3 conn, 8 research, 2 disc |
| Bridge configured and called, refused downstream of the failure | AGREE | `BRIDGE_REASONING_NOT_COMPLETED`, `BRIDGE BUILD rc=1` after `REASON rc=5` |

## Two findings the window did not make

**MR-A (was F6 in this review; the P-A1 branch later minted its own F6) — the run's wall clock was a transport failure, not a slow model.**
Run span 10:11→15:07 (4.94 h). glm-5.3 accounted for 3.99 h of it; 3.27 h
(66% of the run) was the ten zero-token calls. This is the P-S1 "dead
provider, no summary said so" signature recurring, on one endpoint only.
The ~300 s per attempt is a hypothesis worth one cheap experiment: a proxy or
gateway idle limit on long glm-5.3 thinking at the 49 152 cap (the successful
glm reason legs all landed at 245–280 s; one at 839 s contradicts a hard cut).

**MR-B (was F7 in this review) — the window's own monitor was blind to the signature it was built for.**
`monitor.sh` classifies a failed attempt by `t.get("error") or
t.get("failure") or t.get("status") == "error"`; the attempt trace carries
none of those keys. The typed signature is `transport_diagnostics` /
`tokens == 0` / `usage_unknown`. 40 transport faults, 0 alerts, and
FINDINGS.md / RESULTS.md / MODULE_COVERAGE.md contain no occurrence of
`RemoteDisconnected` or `transport`.

## Re-derivation

```
git worktree add /tmp/pa1 origin/claude/live-reasoning-p-a1-bv65kl
cd /tmp/pa1/experiments/2026-09-01-live-all-modules-p-a1/run
grep -c scrutiny log.jsonl                                  # 0
grep -o '"trial-declined"[^]]*' log.jsonl | sort | uniq -c   # 2 ensemble-split, 4 execution-backed
python3 - <<'PY'
import json,collections
c=collections.Counter(); z=collections.Counter()
for l in open('log.jsonl'):
    e=json.loads(l); llm=e.get('llm')
    if not llm: continue
    for a in llm['attempt_trace']:
        for d in a.get('transport_diagnostics',[]): c[(llm['model'],d.split(':')[0])]+=1
        if not a.get('tokens'): z[(llm['model'],llm['role'])]+=1
print(c); print(z)
PY
# judge verdicts: raw_ref of seqs 396/401/559/564 -> blobs/<xx>/<ref>, field "verdict"
sed -n '696,752p' ../../../../src/deepreason/scheduler/scheduler.py     # F2
sed -n '962,974p' ../../../../src/deepreason/informal/trial.py          # execution-backed = formal supremacy
```

## Addendum, 2026-09-01 — the operator's hypothesis, checked: the glm-5.3 reasoning knob

The operator suspected the glm-5.3 endpoint was coded with the wrong thinking
value (`none` where `low` belongs). The record and Ollama's own model page
confirm it, in a sharper form than a seat-config typo:

- Ollama's glm-5.3 page: "`reasoning_effort` accepts `low`, `high`, and
  `max`, and defaults to `max`." `none` is not in the set. P-S1 measured what
  `none` does on this model: it does not stop thinking, it stops the
  SEPARATION, so the trace lands in `message.content` (SEAT_REASONING_FINDINGS.md,
  0/8 clean at `none`, 8/8 clean at `low`).
- The split-budget protocol hard-codes `REASONING_OFF = "none"`
  (`llm/providers.py:70`) onto every extraction leg
  (`llm/split.py:163`, `extract_reasoning=REASONING_OFF if knob else None`),
  and the Ollama adapter passes it straight through as `reasoning_effort:
  "none"`. This is a constant, not a configuration: no run-config value can
  change what the extraction leg sends. Under the modularity law that is a
  finding in its own right.
- P-A1 armed that protocol on glm-5.3 (`reasoning` omitted → `auto` split).
  Every glm-5.3 extraction-leg raw blob begins with thinking prose ("Let me
  understand the task…", seqs 386, 583, 629 …), the 512-token leg is cut
  before any JSON (`natural_stop: false` on 5 of 6), the serialize step
  fails, compact recovery ratchets the cap down, and the seat exhausts. That
  is P-S1's M-1 mechanism, verbatim, re-run.
- The REASON leg ran with the knob omitted, i.e. at glm-5.3's default
  `max` effort against a 48 640-token budget. That is what pushed those calls
  past the ~300 s transport wall (MR-A). `low` would have shortened them by
  orders of magnitude (P-S1: median 7 vs 64 tokens on a fixed prompt).
- deepseek is unaffected by the `none` leak (its extraction legs are clean
  JSON) but its conjecturer extraction legs were still cut at 512 tokens in
  10 of 13 cases, because the conjecturer schema does not fit in 512:
  `SPLIT_BUDGET_EXTRACTION_TOKENS` (config.py:744, default 512) was left at
  a value P-C2b measured for a much smaller planner output.

**The monitor's part.** The P-A1 instruction said "thinking stays ON …
do not attempt to turn thinking off", read off P-S1's `none` finding. The
right instruction was the one P-S1's own final run-config already encoded:
glm-5.3 at `reasoning: "low"`, split protocol OFF. The window followed the
instruction it was given.

**Fixes, in order.** (1) Config, immediately, no code: glm-5.3 seats at
`reasoning: "low"`; `SPLIT_BUDGET_SEAT_PROTOCOL: off` (a run-level knob — with
`auto` on, an explicit `low` still arms the split and the leg still sends
`none`); if the split is ever re-armed, raise `SPLIT_BUDGET_EXTRACTION_TOKENS`
to fit the conjecturer schema. (2) Harness, small, non-frozen: the extraction
leg's off-token must be realized per provider/model through the
`providers.py` seam (glm-5.3's most-off documented value is `low`) or become
a configuration value; never a hard-coded `none`. (3) The ~300 s transport
wall and blind identical retries (F6) stay real and get their own probe, at
lower priority once `low` keeps glm inside the wall.
