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

## 2026-08-08 — correction: "stochastic miss" was wrong; the path is structurally dead

**This corrects, not edits, the "Residue" and "Verdict" segments
above** — those stand as written, with this segment naming exactly
what was wrong in them. The characterization of `property_designer`
never firing as a "pre-registered stochastic miss" (PLAN.md,
`s6-audit1.json`/`s6-audit2.json` analysis above) is REFUTED by the
tree. Probability of the `coder` seat actually dispatching a live call
was **0, not low** — this is a structural dead path, not a
capability-channel-style stochastic one, and PLAN.md's own citation of
CLAUDE.md's stochasticity doctrine to excuse it was a misapplication of
that doctrine to a mechanism the doctrine does not cover.

**The evidence chain, read fresh from the tree, not from memory:**

1. `GROUP_ROLES["coder"] = frozenset({"property_designer"})`
   (`seat_bindings.py`) — the `coder` group's ONLY role.
2. `property_designer` is dispatched from exactly one call site,
   `rules/experiment.py::propose_properties`, which early-returns `[]`
   unless `oracle.py::checker_wf_commitment(base)` returns non-`None`.
3. `checker_wf_commitment(base)` (`oracle.py:776`) itself early-returns
   `None` unless `base.eval == f"program:{PROPERTY_PROGRAM}"` — i.e.
   unless an ACTIVE property-oracle commitment already exists in the
   run's own graph.
4. The only function anywhere in `src/deepreason/` that constructs a
   NEW `Commitment` with `eval == "program:property_oracle"` is
   `oracle.py::property_oracle_commitment` (line 335).
5. `property_oracle_commitment`'s only caller in the entire tree is
   `oracle.py::admit_counterexample` (line 431,
   `grep -n "property_oracle_commitment(" src/deepreason/**/*.py`
   returns exactly this one call site outside the function's own
   definition).
6. `admit_counterexample` (`oracle.py:386`) itself REQUIRES `base.eval
   == f"program:{PROPERTY_PROGRAM}"` as its own precondition (line
   397: `if base.eval != f"program:{PROPERTY_PROGRAM}": return None,
   "target commitment is not a property oracle..."`) — it mints a
   counterexample-derived oracle INHERITING an existing base oracle's
   own spec, it does not mint the first one.
7. Every other reference to `PROPERTY_PROGRAM` in the tree
   (`run_manifest.py:3830`, `rules/crit.py:779,813,942`,
   `scheduler/scheduler.py:2201,2246,2288`) READS `commitment.eval ==
   f"program:{PROPERTY_PROGRAM}"` to gate some OTHER behavior; none of
   them constructs one.

**The circularity, stated plainly:** minting a property-oracle
commitment requires an existing property-oracle commitment as input.
No public path (the CLI, the seed-problem admission path, or any rule
this tranche's live run actually exercised) constructs the FIRST one.
`property_designer` therefore has no way to ever fire on ANY run
launched through the public surface — not "rarely," not
"stochastically across identical runs" (CLAUDE.md's own doctrine, which
governs capability/simulation-channel proposals that genuinely DO
authored by a live model call with a live probability of firing) —
**structurally never**, independent of the question asked, the cycle
budget given, or which models are bound to which seats. This explains,
retroactively, the OTHER finding already on record and unchanged since
it was first measured: no `log.jsonl` under `experiments/` or `runs/`
in this repository's entire history has ever carried a
`"role": "property_designer"` LLM-call record (checked at PLAN.md's own
writing, before this rung's live run, and still true after it).

**Why this was missed the first time:** PLAN.md reasoned by ANALOGY to
CLAUDE.md's documented capability-channel stochasticity doctrine
without tracing `property_oracle_commitment`'s own caller graph to its
end — the same kind of "reading a model and not its validator" pattern
`docs/map/INV-frozen-surfaces.md` names as this program's own recorded
trap for surface 4, applied here to a different mechanism. The fix
executor read three call sites deep and stopped one hop short of the
actual root cause.

**Consequence for THIS tranche's own accept criteria:** unchanged in
substance. Criterion (a) ("which seat produced every attempt") never
depended on `property_designer` firing — it was always "for whatever
attempts occurred, attribution is correct," and that stood then and
stands now. What changes is only the CHARACTERIZATION of why the
`coder` seat produced none: not an unlucky roll, a seat that cannot be
exercised through any public path today. Rung S6's own accept criteria
are satisfied more convincingly by re-running the demonstration on a
seat proven to do real work (below) than by continuing to lean on a
channel now known to be structurally dead.

## 2026-08-08 — Failure #3 (config error): re-run refused typed, `PREPARATION_QUALIFICATION_BUNDLE_MISMATCH`; my own PARKED.md assumption was wrong

**What happened:** `s6_run_v2.sh` set up the second combination
(`--seat "conjecture=$LIVE/coder-profile.yaml"`, same base
glm-5.2 profile, same `home-s6` DEEPREASON_HOME), qualified cleanly
(`qualify_rc=0`, both the base `ollama/glm-5.2` combination and the
`conjecture` seat reaching `qualification_state: "ready"`, `tier:
"full"`, in 207s — this combination's battery hit a warm cache for the
`conjecture` seat's own subject, since `gemma4:31b` had already
qualified for the `coder` seat in the first run), then `reason` refused
typed 3 seconds later with no `run_id` emitted:

```
PREPARATION_QUALIFICATION_BUNDLE_MISMATCH: managed run qualification differs from the completed cache
```

**Diagnosis, from the code (`src/deepreason/preparation.py`), not
theorised:** `_load_existing` (line 741) raises this exact code+message
at line 776-780 when a run root already exists at the computed
`managed_run_id` and its stored `qualification_bundle_digest` does not
match the freshly-recomputed `expected_bundle_digest`. `ls
home-s6/runs/` showed only ONE root: `run-79900e7847544b09bfb266518e2d8484`
— the FIRST (coder-seat) run, already committed as evidence. Its own
`run-preparation.json` records `managed_run_id =
run-79900e7847544b09bfb266518e2d8484` and `request_digest =
79900e7847544b09bfb266518e2d8484f827dddde9a488cc892f73bbffe3afe3` — the
run id IS (a prefix of) the request digest. `_request_digest`
(`preparation.py:249-265`) hashes exactly `{schema, question, budget,
provider_profile_digest, policy_preset_id, policy_preset_digest}` (plus
`dossier_digest` when present) — **seat bindings are not an input to
it at all.** Seat-binding overrides are folded in later, only inside
`_config_for_profile` (line 268) when actually building the run's
provider config, and the seat-bindings snapshot is written to the run
root as a sibling file (`SEAT_BINDINGS_SNAPSHOT_NAME`), never hashed
into the identity. Since v2's question text and base profile were
byte-identical to the first run's, its request digest collided with
the already-committed root, and `_load_existing` correctly refused: the
existing root's qualification bundle was frozen at the coder-seat
combination's digest, not the fresh conjecture-seat one.

**This refutes my own PARKED.md "In-flight note"** (written before
this attempt), which assumed "a fresh run identity since the seat
group changes the compiled manifest's roles table and therefore the
request digest." That assumption was never checked against
`_request_digest`'s actual field list before being written down — the
same class of mistake as the `property_designer` correction above
(reasoning from what seemed plausible instead of reading the one
function that decides it). Recorded as its own PARKED item (P2) below,
since it is a second, independent, load-bearing finding about the
harness's live behavior, not a restatement of P1.

**Work-around used (no code changed):** the tranche's own rule is
work around operationally if a no-code road exists, otherwise park.
One exists here: `_request_digest` includes `question` verbatim, so
giving the second demonstration a question that differs from the
first by more than whitespace mints an unrelated `managed_run_id`,
with no interaction with the already-committed `coder`-seat root at
all — no rename, no retirement, nothing touched. `s6_run_v2.sh`'s
`QUESTION` was edited (still committed as this rung's own artifact, not
`src/`/`tests/`/`tools/`/`docs/map/`) to add one distinguishing
sentence identifying it as the second-seat variant of the same
underlying question, keeping the demonstration's content comparable
while forcing a fresh identity. Re-launched immediately after; see the
next segment for its outcome.

Failure budget: 3/10 spent (2 carried in from the coder-seat run, this
is the third).

## 2026-08-08 — the retried v2 run: clean attribution, but two more findings (Failure #4, and a snapshot-loop process deviation)

The relaunch (`s6_run_v2.sh`, distinguished question, minted
`run-8c77c6588485304d1f73416318c62949`) got much further:

- `setup_rc=0`, `qualify_rc=0` (1 second — both the base combination and
  the `conjecture` seat hit warm caches from the earlier attempts).
- `reason_rc=0` after 611s, 6 cycles, `stop_reason=budget_exhausted`,
  140461/150000 tokens spent.
- `audit1` (`s6_audit_v2.py`) showed **criteria (a) and (b) fully met**:
  `attribution_clean: true`, `conjecturer_calls_on_gemma: true`,
  `argumentative_critic_calls_on_glm: true`, one seat-bindings stamp
  recorded with `group: "conjecture"`, `model_id: "gemma4:31b"`, matching
  what `setup --seat conjecture=...` bound. But `replay_valid: false`,
  with 9 `foreign-criticism` violations.

**Diagnosing the foreign-criticism violations, from the code
(`src/deepreason/invariants.py`), not theorised:** the terminal check at
line 4003-4009 requires every ACCEPTED artifact authored by a
`conjecturer`/`synthesizer` to have accumulated foreign-school criticism
(criticism from a DIFFERENT "school" — an independent line of critique,
a concept this program keeps distinct from "seat"; see below) meeting
`criticism_policy.minimum_foreign_school_coverage` (1, here). All 9
flagged targets had 0. This is NOT a seat-binding interaction: both
runs' compiled `criticism_policy` (`run-manifest.json`) are byte-for-byte
identical (4 schools, all `argumentative_critic` bound to the same
default `provider-profile-a3e...` endpoint in both runs — seat overrides
never touch that role in either the `coder` or `conjecture` group). It
reads instead as ordinary resource pressure: run2's `conjecturer` role
(now on `gemma4:31b`) produced more raw candidate conjectures per cycle
than run1's did (16 calls vs. run1's 11, comparably-sized budgets),
outrunning the scheduler's ability to also dispatch enough
`argumentative_critic` batches (25 calls vs. run1's 27) before the
150000-token ceiling hit — leaving 9 newly-accepted artifacts still
waiting for their mandatory second opinion when the run stopped.

**Failure #4 — a genuine harness defect, found live, NOT caused by
`--seat`:** the ladder's own `resumable` check (using `stop_reason`)
said this was safe to resume, so it ran `deepreason --root <run>
continue --budget cycles=2` to close the gap. That continuation crashed
4 events in: `state: "failed"`, `stop_reason: "operational_failure"`,
`error: "unknown critic task"`, `error_type:
"NonConjectureRecoveryAuthorityError"`. Traced to
`src/deepreason/workflow/nonconjecture_recovery.py:644`:

```python
def _criticism_contract(harness, manifest, item, preparation, payload):
    _authority(payload.get("schema") == "criticism.semantic-task.v1", "unknown critic task")
```

The captured `run-result.json` shows why: before the first `reason`
call stopped, one `argumentative_critic` batch (`batch-critic.v2`) had
already hit `schema_exhausted` (repeated malformed JSON from the model)
and the harness's own recovery machinery had begun decomposing it into
individual `critic.atomic-target.v1` children and switching that route
to a "compact" recovery profile (`mode:
"route_seat_compact_recovery"`) — a pre-existing, seat-independent
self-healing path for exactly this kind of model flakiness (glm-5.2
producing malformed batch JSON under load; CLAUDE.md's own documented
failure mode for reasoning models). Two of those atomic children had
already completed. `continue`'s attempt to RESUME that in-flight
decomposition is what hit `_criticism_contract` with a payload whose
`schema` field was not `"criticism.semantic-task.v1"` — almost
certainly the *atomic* child's own payload shape being routed through
the handler written for the *batch* contract. This is a resume-path
bug in the compact-recovery/decomposition machinery, not a `--seat`
interaction: nothing in the failing code path branches on seat
bindings, and the crash happened on the `argumentative_critic` role,
which is bound to the same default endpoint in every configuration this
tranche has run. Parked in full as P3 below (not fixed: `src/` stays
byte-untouched this tranche).

The run root (`run-8c77c6588485304d1f73416318c62949`) is now dead —
`state: "failed"` is terminal, and it never got a second seat-bindings
stamp (`seat_bindings_stamp_count` stayed 1), so it cannot demonstrate
criterion (d) either. Retired per this program's own convention:
`git mv run-8c77c6588485304d1f73416318c62949
failed-epoch1-run-8c77c6588485304d1f73416318c62949`, committed as its
own commit (`35df6616`) before anything else, contents otherwise
untouched.

**A process deviation worth naming plainly, not hiding:** the driver
script itself does not gate `audit2`/further steps on `continue_rc`, so
it ran `s6_audit_v2.py` again against the now-failed root regardless
(harmless — it just captured the failure state as `s6-audit2-v2.json`,
consistent with `s6-audit1-v2.json` plus the crash). More seriously,
`snapshot_loop.sh`'s 5-minute `git add -A "$LIVE_REL"` swept up this run
root TWICE while `continue` was still actively appending to it
(commits `4d527599` at 04:45:14Z, mid-`continue`, and `ae12fd3f` at
04:50:17Z, capturing its final failed state) — a direct violation of
this program's own "never commit mid-append" rule, caused by my own
snapshot tooling being less careful than the ladder's explicit
end-of-step commits. No harm resulted (the root was dead anyway and is
now retired, its mid-append commit superseded by the final one before
retirement), but the tooling gap is real and is now fixed:
`snapshot_loop.sh` was edited to exclude `home-s6/runs/` from its
sweep, so only the ladder's own deliberate, post-judgment commits will
ever include a run root going forward.

**Adaptation for the next attempt:** raising `--token-budget` will not
by itself prevent `schema_exhausted` (that trigger is about the model's
per-call output reliability, not the run's total budget), but a more
generous budget DOES reduce the chance of stopping mid-decomposition —
which is the specific state that exposed the `continue`-resume bug.
`s6_run_v2.sh`'s `--cycles 6 --token-budget 150000` is raised to
`--cycles 10 --token-budget 220000` for the retry, aiming for a run
that either fully resolves any schema-exhausted recovery within its own
single `reason` invocation (never needing a mid-decomposition
`continue`) or, if it still needs `continue`, does so from a clean stop
point the way run1's did.

Failure budget: 4/10 spent.
