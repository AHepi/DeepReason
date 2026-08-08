# Results — Rung S6, the live two-seat A/B

Honest-ledger segments only. "Accepted does not mean true." Model prose
is never evidence; `run-status.json`, `verify_root`, `recorded_seat_
bindings`, and the LLM-call records in `log.jsonl` are.

## Failure ledger (numbered as spent, not retrospectively)

**Failure #1 — qualification battery failure (combination fell to
shallow tier), diagnosed before any theory.** `qualify` completed
(rc=0, 477s) but the COMBINATION subject reached only
`qualification_state: "ready_shallow"` (`tier: "shallow"`), so `reason`
(full V6) refused typed on the very next step:

    QUALIFICATION_TIER_SHALLOW: this provider/model is qualified at
    tier "shallow" only; full V6 reasoning is refused. Use: deepreason
    reason --shallow "YOUR QUESTION"

Read the diagnostic blob (`home-s6/qualification-cache/f9295c2b....
unqualified-doctor.json`) before theorizing, per the driving manual's
own rule. `summary.qualified_pair_count: 14/15`; the one unqualified
pair (`pairs[11]`) is `role: "summarizer"`, `contract_id:
"scratch.cluster-guide.compact.v1"`, `model_id: "glm-5.2"`:
`eventual_valid_count: 19/20` (at the `eventual_valid_minimum_per_pair`
floor) but `scope_violations: 1` (case-004, `failure_code:
"REPAIR_SCOPE_VIOLATION"`). `cli/doctor.py:139` confirmed this is a
ZERO-TOLERANCE gate — `sum(item.scope_violations for item in cases) ==
0` is required regardless of the eventual-valid count, so 19/20 valid
plus one scope violation still fails the pair. `_is_scope_violation`
(`cli/doctor.py:431`) classifies `REPAIR_SCOPE_VIOLATION` as: the model,
during a JSON-repair retry, edited a field outside the allowed repair
scope — a content-shape/discipline issue on this one representative
case, not a config error or a run death.

**Remedy (knob, not code):** raised `--maximum-completion-tokens` from
8192 to 16384 and re-ran `setup` + `qualify` MANUALLY (outside the
ladder script) to confirm the fix before touching the ladder. This
changes the profile's own digest, forcing a FRESH, independently-
sampled battery (qualification caches by subject digest; re-running the
SAME profile would have replayed the identical cached failure) — the
standard adaptation for a stochastic single-case miss, not a certainty
of fixing the specific repair-scope behavior, but the cheapest knob
available that plausibly gives the model more room during a repair
attempt. Confirmed: the fresh battery reached `qualification_state:
"ready"`, `tier: "full"` for the combination (digest
`2c507ede9c...`), coder seat unaffected (`cache_reused: true`, still
`ready`/`full`).

**Failure #2 — self-inflicted ladder bug, logged honestly.**
Re-launched `s6_run.sh` to resume the ladder from `setup` onward,
expecting `setup` to be a harmless no-op re-affirming the already-fixed
profile. It was not: `s6_run.sh`'s own `setup` invocation still had
`--maximum-completion-tokens 8192` HARD-CODED, so re-running it
silently overwrote the manually-fixed `16384` profile back to the
failing one. `qualify` then cache-hit the STALE shallow-tier subject
digest (`f9295c2b...`, the same one Failure #1 diagnosed), and `reason`
refused typed with the identical `QUALIFICATION_TIER_SHALLOW` error.
This is a ladder bug, not a new model/qualification finding -- caused
by fixing the LIVE environment manually without updating the SCRIPT
that reproduces it, then blindly re-running the script. **Remedy:**
`s6_run.sh` corrected in place (the hardcoded value now reads `16384`,
with a one-line comment naming Failure #1 as the reason), verified by
re-reading the file before the next launch.

## 2026-08-08 — launch

Ladder launched detached at `2026-08-08T03:24:53Z`, head `19a294ba`.
`setup` succeeded on the first attempt: `deepreason status --json`
(smoke-tested pre-launch against a throwaway home, then live) confirms
the `coder` seat bound to `gemma4:31b` alongside the default `glm-5.2`
profile. Qualification battery started (~1140 calls expected, ~14 min).

## 2026-08-08 — the live run and its two typed audits

After Failures #1/#2 (above) were diagnosed and fixed, `s6_run.sh` ran
clean end to end: `setup_rc=0`, `qualify_rc=0` (cache hit, both subjects
already `ready`/`full`), `reason_rc=0` (744s, `run_id=
run-79900e7847544b09bfb266518e2d8484`), `audit1_rc=0`, `continue_rc=0`
(353s), `audit2_rc=0`. No further failures spent (budget: 2/10 used).

**What the FIRST audit (`s6-audit1.json`, taken right after `reason`
stopped) shows, from the typed record alone:**

- `state: "completed"`, `stop_reason: "budget_exhausted"` — a typed,
  resumable stop (criterion 2 of PLAN.md).
- `replay_valid: true`, `verify_violations: []` — **criterion (c)
  PASSED.**
- `seat_bindings_stamp_count: 1`, naming `group: "coder"`, `provider:
  "ollama"`, `model_id: "gemma4:31b"` — **criterion (b) PASSED**: the
  stamp matches exactly what `deepreason setup --seat coder=...` bound.
- `llm_calls_by_role`: `{"argumentative_critic": ["glm-5.2"],
  "conjecturer": ["glm-5.2"]}`, 34 total LLM calls, `attribution_clean:
  true`, `attribution_mismatches: []` — **criterion (a) PASSED for
  every attempt that occurred**: every dispatched call is attributable
  to its role, and every role's calls used exactly the model that
  role's binding (or the default, for unbound roles) predicts.
- `property_designer_calls: 0` — the coder seat's own role never fired
  live. This is the accepted, PRE-REGISTERED stochastic miss named in
  PLAN.md before launch (`property_designer`'s trigger path,
  `checker_wf_commitment`, requires an active property-oracle
  commitment that historically has never appeared in ANY committed
  root in this repository — a capability-channel-adjacent mechanism
  CLAUDE.md's own doctrine already documents as stochastic). Not a
  failure: it does not count against the ten-failure budget, and the
  plan's own words hold — "The offline regression is the proof; one
  live attempt is the demonstration (stochasticity rule)." The
  controlling proof for the `coder`/`gemma4:31b` channel specifically
  remains `tests/test_seat_bindings_record.py::
  test_a_two_profile_home_stamps_both_bound_groups_in_one_run` (Rung
  S5, offline, MockEndpoint-driven, both bound groups exercised
  deterministically).

**What the SECOND audit (`s6-audit2.json`, taken after `deepreason
--root <root> continue --budget cycles=2`) adds — the proof for
criterion (d):**

- The continuation itself: `continue_rc=0`, reaching a second typed
  stop (`state: "completed"`, `stop_reason: "budget_exhausted"` again,
  cycle 8 overall).
- `replay_valid: true`, `verify_violations: []` still — no violation
  introduced by the continuation.
- `attribution_clean: true` still (38 calls now, +4 over audit1, all
  still correctly attributed; `property_designer_calls` still 0).
- `seat_bindings_stamp_count: 2` — a SECOND stamp was appended. This is
  the EXACT, pre-registered shape Rung S5's own SPEC.md predicted (Q5/
  A5): `Scheduler._seat_bindings_recorded` is a per-instance guard,
  copied deliberately from the rung-4 module-fingerprint template, that
  resets on `deepreason continue`'s fresh `Scheduler` construction — so
  a continuation legitimately re-stamps. **Both stamps carry the
  IDENTICAL digest (`ae0034400f7381fd2f45256e7764f7656f6450cbc53606db
  1b98e7b642d74121`) and identical binding content
  (`coder`/`ollama`/`gemma4:31b`)** — the record's own reader
  (`recorded_seat_bindings`, returning EVERY stamp, never a
  single-unpack) reads both correctly, and `seat_bindings_for_run`
  projects the same, unchanged binding either way. **Criterion (d)
  PASSED: bindings preserved byte-identically across the continuation
  boundary** — the "preserves bindings" branch of "a continuation
  preserves bindings or refuses typed," not the refusal branch, and a
  live, positive confirmation that Rung S5's own reader-partition
  design (never `(x,) = recorded_seat_bindings(...)`) is exactly what
  a real continuation needed.

## Residue — what remains unproven

Per CLAUDE.md's own honest-ledger convention: "accepted does not mean
true." This live attempt did not exercise `property_designer` /
`coder` seat's own role live, so criterion (a)'s claim about THAT
specific channel rests entirely on the offline regression (Rung S5),
not on this run. A future live attempt aimed specifically at
triggering a property-oracle commitment (e.g. an attached-evidence run
naming an explicit checker spec, if the public surface ever exposes
one) would close this residue; it is not required for THIS rung's own
accept criteria, which name the offline regression as sufficient proof
for exactly this situation.

## Verdict

All four of the plan's own accept criteria (a)-(d) are met: (a) clean
for every attempt that occurred, with the property_designer gap named
and not hidden; (b) the stamp matches what setup bound; (c) verify_root
green both before and after continuation; (d) bindings preserved
byte-identically across the continuation boundary. Two failures spent,
both diagnosed from the typed record before any remedy, both logged as
they happened. Rung S6 is DELIVERED. No dead root to retire — the one
run root this tranche produced (`run-79900e7847544b09bfb266518e2d8484`)
is the evidence, kept as committed.
