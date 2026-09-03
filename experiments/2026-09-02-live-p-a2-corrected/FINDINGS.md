# P-A2 findings

Findings, not fixes. This is a RUN tranche: no source is edited, and anything
that would need a code edit is recorded here and parked for a change tranche.
Each finding names the typed evidence it rests on and says plainly what it
does NOT mean, so a later reader does not over-read it.

---

## F1 — the offline soak stub still cannot serve two contracts that any maximum-configuration run grants (RECURRENCE)

**Status:** open on `main`. Routed around inside this tranche, not fixed.

**What the record shows.** The first P-A2 soak
(`soak_output.txt`, manifest `27dae00f0d188437`) failed qualification with
**10 of 23 pairs qualified, 200 of 460 cases valid**. Two pairs failed for a
genuine reason and eleven failed as cascade:

| pair | failure code | cases |
|---|---|---|
| `argumentative_critic` / `config-referee.v1` / deepseek | `ENDPOINT_HTTP_500` | 20 |
| `grounding_reviewer` / `groundingrepairwirev1.direct.v1` / glm-5.3 | `ENDPOINT_HTTP_500` | 20 |
| 11 further pairs across both endpoints | `CIRCUIT_OPEN_ENDPOINT_HTTP_500` | 20 each |

The stub has no fixture for `ConfigRefereeWireV1` or `GroundingRepairWireV1`,
and its generic schema synthesiser cannot produce either. An unsatisfied
fixture is an HTTP 500; a 500 trips the qualification circuit breaker for the
WHOLE endpoint, which is why two gaps cost thirteen pairs.

**What it does NOT mean.** It is not a defect in P-A2's configuration, and it
is not something the live run can hit: the failing responder is the offline
STUB, which exists only so a rehearsal need not call a real provider. Both
contracts are granted by configuration and both qualify against a real model.
Nothing about the harness is implicated.

**Why it recurred.** P-A1 met this first, filed it as its own F1, and fixed it
by adding the two fixtures to `scripts/wheel_operational_smoke.py`. **That fix
lives only on `claude/live-reasoning-p-a1-bv65kl` and never merged to main.**
So it recurs for every later tranche that turns the config referee or the
grounded bridge's repair path on — which is to say, for every
maximum-configuration run. The cost is not small: a fresh window meets a red
soak that looks exactly like a configuration defect and must re-derive P-A1's
answer, including its non-obvious half (below).

**The non-obvious half, preserved so it is not re-derived a third time.**
The correct `GroundingRepairWireV1` fixture is `{"action": "remove_span"}`,
and the choice is not arbitrary on either axis. STRUCTURALLY it is the one
action accepting no substantive field, so it satisfies the schema's
`allOf`/`if`/`then` branches — which make `replacement_text`, `resolution`
and `resolution_reason` required or forbidden depending on `action` — by
carrying nothing; a walker that fills properties independently cannot satisfy
a cross-field implication. IN SCOPE it is the only action present in EVERY
entry of `bridge.repair._ALLOWED_BY_STATUS`. The caller narrows the contract
to one finding status's permitted actions while the advertised JSON Schema
still `$ref`s the full `CorrectionMode` enum, so **a fixture chosen from the
schema alone can be structurally valid and still out of scope**.
`correct_wording` is exactly that trap: it validates, then
`_admit_production_probe_output` raises `BRIDGE_REPAIR_ACTION_FORBIDDEN`.

**How this tranche routed around it.** `soak_pa2.py` rebinds
`wheel_operational_smoke.response_for_schema` to a wrapper that supplies
P-A1's two fixtures verbatim and delegates everything else to the original.
No source file is edited. The patch makes the gate STRONGER, not weaker: two
contracts that previously could not be exercised at all must now return
schema-valid, in-scope responses or their pairs still fail. There is no check
here to relax.

**Recommended fix (a change tranche, not this one).** Port P-A1's two
fixtures to `scripts/wheel_operational_smoke.py` on main. The diff is
`git diff main origin/claude/live-reasoning-p-a1-bv65kl --
scripts/wheel_operational_smoke.py` and is +40 lines, additive, touching no
frozen surface. A regression test would assert that
`response_for_schema` returns a value for every contract title the engaged
preset can grant, so the next module switched on fails at the test rather
than at a red soak.

---

## F4 — glm-5.3 at `reasoning: low` cannot satisfy the grounding-repair contract (MEASURED, and it blocked the launch)

**Status:** open. This is the finding that stopped P-A2's live run, and it
is a real measured trade-off of the correction rather than an accident.

**What the record shows.** P-A2's qualification refused after 96 minutes:
**22 of 23 pairs qualified, 445 of 460 cases.** Compared pair-by-pair
against P-A1's own `qualify.json` (23/23, 460/460), **exactly one pair
moved**:

    grounding_reviewer / groundingrepairwirev1.direct.v1 / glm-5.3
        P-A1  20/20 eventual_valid
        P-A2   5/20  (19 required), first_pass 4, repairs 31, VALUE_ERROR x15

Every other pair is 20/20 in BOTH runs, including six other glm-5.3
contracts (`conjecturer.turn.v6`, `conjecturer.atomic-candidate.v1`,
`defender.direct.v1`, `groundingverdictwirev1.direct.v1`,
`bridge.ledger.v3`, `bridge.ledger-batch.v1`) and four glm-5.3 scratch
contracts. The corrections did not broadly degrade this model.

**Which correction, isolated by experiment.** P-A2 moved three things about
that seat at once, so `isolate_grounding_repair.py` exercised ONLY that pair
through the doctor's own per-case entry point, across six configurations,
ten cases each — 60 live calls:

| cell | reasoning | cap | split | valid |
|---|---|---|---|---|
| A | `low` | 32768 | off | **2/10** |
| C | `low` | 32768 | auto | **3/10** |
| E | `low` | 49152 | off | **4/10** |
| B | unset (`max`) | 49152 | auto | **10/10** |
| D | unset (`max`) | 49152 | off | **10/10** |
| F | unset (`max`) | 32768 | off | **10/10** |

**Perfect separation on the reasoning knob alone.** Every `low` cell fails at
2–4 of 10; every default-effort cell passes 10 of 10. The completion cap and
the split-budget protocol both vary freely WITHIN each group and change
nothing. Cell B reproduces P-A1 exactly, so the comparison is valid and the
cause is this tranche's change rather than provider drift.

**Two hypotheses this refutes, both of which were the monitor's own.**

1. *The split-budget protocol was quietly making glm-5.3's hardest
   structured output clean, and turning it off (C3) broke it.* **False.**
   Cell D runs with the split OFF and scores 10/10; cell C runs with it ON
   and scores 3/10. The protocol is irrelevant to this contract.
2. *This is F1's forbidden-action trap reaching a real model.* **False.**
   `BRIDGE_REPAIR_ACTION_FORBIDDEN` is classified as a scope violation by
   `doctor.py::_is_scope_violation`, and both runs report
   `scope_violations: 0`. The failures are bare `ValueError` — the
   class-name fallback in `_failure_code` for an error carrying no `.code`
   — so they are wire-object validation, not the narrowed-scope refusal.

**What it means for the model profile.** `docs/model-profiles/glm-5.3/agent.md`
says, as its headline: *"If you read one line here: set this seat's
`reasoning` to `low`, not `none`, and not unset."* That guidance is measured
and correct for GENERATION seats — six other glm-5.3 contracts qualify 20/20
at `low`, and `low` is what keeps those calls inside the ~300 s transport
wall. It is **wrong for at least one structured-repair contract**, whose
schema makes `replacement_text`, `resolution` and `resolution_reason`
required or forbidden depending on the chosen `action`. Satisfying a
cross-field implication appears to need the thinking that `low` removes.
Every failing case spends both repair attempts and still ends invalid, which
is the signature of a structural miss rather than a truncation.

The profile is a document a human writes and nothing in it can veto a
configured value, so this is a note for its author rather than a defect in
the mechanism: the reasoning knob is **not uniform across contracts on one
model**, and a per-model headline cannot express that.

**Recommended remedy (operator's call, not taken here).** Give the
`grounding_reviewer` seat its own route spec at the model's default effort
while the five generation glm-5.3 seats keep `low`. That is pure
configuration, it is exactly cell F (10/10), and it preserves the correction
where it was aimed — the seats that actually hit the transport wall. The cost
is that the correction is no longer uniform across glm-5.3 seats, and that
deviation must be written into the pre-registration rather than made quietly.

---

## F5 — epoch 2 died on an ACCOUNT USAGE LIMIT, not on any contract (STOP)

**Status:** blocking, and not routable by configuration. The operator must
decide.

**What the record shows.** Epoch 2 launched 22:03:13Z with 62 preflight
checks and 0 failures, and its qualification refused 26 minutes later —
against epoch 1's 96. It qualified **5 of 23 pairs, 100 of 460 cases**, and
the failure code is the same everywhere:

    ENDPOINT_HTTP_429   on ollama-deepseek-v4-pro-0813 and ollama-glm-5.3
    circuit breaker OPENED on both endpoints at 20 block failures each,
    skipping 120 cases per opening

The provider's own message, read directly from a single confirming call
after the run ended:

    HTTP 429 -- "you (aaron_thyne) have reached your session usage limit,
    upgrade for higher limits ... or add extra usage"

No `retry-after` header is returned. This is an ACCOUNT USAGE CAP, not a
transient per-second throttle and not a transport fault.

**What this does NOT mean, and the distinction matters.**

- **P6 is UNTESTED, not refuted.** The prediction was that the amended shape
  qualifies 23 of 23 with the grounding-repair pair back above threshold.
  That pair did fail — with `ENDPOINT_HTTP_429`, exactly like the twelve
  other pairs and like contracts that had qualified 20/20 twice already. A
  battery that cannot reach the provider tests nothing about a schema.
- **F4 still stands.** Its isolation completed BEFORE the cap was reached and
  carried its own control: cell B (P-A1's settings) scored 10/10 in the same
  session as cells A/C/E scoring 2–4/10. A control that passes while its
  siblings fail cannot be explained by a usage cap that would have failed all
  four alike.
- **Nothing about the amended configuration is implicated.** It cleared 62
  preflight checks and soaked green over 24 cycles before launch.

**Honest accounting of what consumed the budget, including my own part.**
Three things ran against this account today, in order:

| what | scale |
|---|---|
| epoch 1 qualification (full battery, 4 models × 23 pairs × 20 cases) | ~1 100+ completions |
| the F4 isolation probe (6 cells × 10 cases, with repair attempts) | ~100–180 completions |
| epoch 2 qualification, until the breaker opened | ~100+ completions |

The two full batteries dominate, but **the isolation probe was mine and it
was not free.** It was the right call — it converted a bare failure into the
measured attribution F4 rests on, and the operator's standing law prefers
generated evidence to agent reasoning — but it is recorded here as a
contributor rather than left out.

**What it costs to retry.** Nothing in the tranche needs rebuilding: the
amended configuration is committed, soaked green, and preflight-clean at
62/62. A relaunch needs only the cap to clear, and then repeats the ~96
minute qualification (the route change already minted a new subject digest,
so nothing is cached) plus up to ~5 hours of reasoning.

**Why this window did not retry.** Relaunching into an active cap would fail
identically and spend the tranche's remaining credibility on a foreseeable
repeat. The instruction's STOP list names exactly this case: a refusal that
cannot be routed around by configuration, and any temptation to relaunch
after a typed failure.

---

## F6 — the snapshot loop can race the operator's own commits after its driver dies (OPERATIONAL, mine)

**Status:** minor, mine, and worth one paragraph so the next window does not
lose a commit message to it.

`snapshot_loop_pa2.sh` checks whether its driver is still alive only AFTER
completing a commit-and-push cycle, and it sleeps 300 s between cycles. So
there is a window of up to five minutes after the ladder exits in which the
loop is still committing. In that window it (a) took `.git/index.lock` while
this window was mid-commit, producing a spurious "another git process seems to
be running", and (b) swept this window's FINDINGS/RESULTS edits into a commit
titled `P-A2 live-run snapshot`, so the reasoning for F5 landed in the
artifact but not in the commit message that carries it.

Neither costs evidence — the content is committed and the artifacts are the
authority, not the message — and the pushed commit was NOT rewritten to fix
cosmetics. The fix, for whoever writes the next loop: test the driver's
liveness at the TOP of the loop body, before the commit, not at the bottom.

---

## F7 — the conjecture-context RETRY path omits the v6 guard the primary path has (NEW DEFECT, killed the run at cycle 0)

**Status:** open, new, and reproducible by configuration. This is the defect
that ended epoch 3, and it is not any of the ones this tranche set out to
measure.

**What the record shows.** Epoch 3 qualified 23/23, ran real work, and then
died at **cycle 0**:

    state                       failed
    stop_reason                 operational_failure
    message                     "v6 conjecture context must be planned after
                                 durable work preparation"
    cycle                       0        token_spend 212 152 / 3 000 000
    terminal_lifecycle_refusal  TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL
    verify_root                 0 violations

**It is NOT the F4 seat death that P5 named as its honest risk.** No
`workflow-route-seat-insufficient-capability-v1` object exists in the root.
The last provider call before the stop (seq 295, deepseek conjecturer) was
`valid=True` at 30 389 tokens — **the model succeeded; the harness refused its
own next step.**

**The cause, located in the code after the record ruled out a model fault.**
`rules/conj.py:827` raises that exact ValueError when a v6 run is handed a
non-`None` `conjecture_context_plan`. There is exactly one caller
(`scheduler/scheduler.py:2434`), and the primary path is correct — at 2387-2392
it plans the context and then, on v6, **nulls it**:

```python
context_plan = self._plan_conjecture_context(problem, school_id)
if self.run_manifest is not None and self.run_manifest.schema_version == 6:
    # Controller-v3 persists preparation before its pure planners;
    # Conj owns that ordered transaction.
    context_plan = None
```

The RETRY path, twelve lines below at 2448-2451, does not:

```python
except ConjectureContextStale:
    if context_attempt:
        raise
    context_plan = self._plan_conjecture_context(problem, school_id)   # <- no v6 null-out
```

The loop then re-enters `conj(..., conjecture_context_plan=context_plan)` with
a live plan on a v6 manifest, `conj.py:827` raises, and the ValueError is
caught by none of the handlers below it (`WorkBudgetDenied`,
`SchemaRepairError`/`EndpointError`, `RouteFirewallError`, …), so it
propagates and terminalizes the run.

**Why P-A1 never hit it, and P-A2 did — the reachability condition.**
`ConjectureContextStale` is raised from exactly three sites, all in
`scratch/conjecture.py` (lines 324, 432, 661) — the SCRATCHPAD's
conjecture-context machinery. So the retry path is reachable only when the
scratchpad is live enough to build a context that can go stale.

| | scratchpad | outcome |
|---|---|---|
| P-A1 | configured ON but **did-not-fire** (no event carried a scratch payload) | never stale, retry path never taken, defect never reached |
| P-A2 | configured ON and **FIRED** — 4 `Scratch` events carrying payloads | context went stale, retry path taken, guard missing, run dead |

**This is therefore a defect that hides behind a module not firing.** Any
configuration that switches the scratchpad on AND actually uses it will meet
it on a v6 run. That makes it a direct hazard to the operator's own modularity
law: a customization point reachable purely by configuration takes the run
down.

**Proposed fix, for a change tranche and not this one.** Null the plan on v6
in the retry path exactly as the primary path does — a one-line change at
`scheduler.py:2451`, or better, hoist the v6 decision into
`_plan_conjecture_context` so a third caller cannot reintroduce the same
omission. The regression test writes itself: a v6 manifest with the scratchpad
enabled, forced through one `ConjectureContextStale`, must reach cycle 1.

**A second, independent defect visible in the same terminal.** The stop
carries `terminal_lifecycle_refusal:
TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` — the run is intact
(`verify_root` 0 violations) and NOT continuable, which is the same violation
of the 2026-08-29 continuability law that P-A1 recorded. Two independent runs
now show a clean record that no operation can resume.

---

## F2 — `SPLIT_BUDGET_SEAT_PROTOCOL` cannot be read off the configuration file (OBSERVATION, working as designed)

**Status:** not a defect. Recorded because it cost this tranche a probe and
would cost the next one the same.

**What the record shows.** The field is popped from the manifest's
engine-config echo (`run_manifest.py:2469`) and reaches the run only through
a carriage notice, emitted verbatim by the compile:

    NOTICE ENGINE_CONFIG_FIELD_NOT_CARRIED: SPLIT_BUDGET_SEAT_PROTOCOL='off'
    is not carried by this manifest's engine config and is restored at run
    time from this notice

**Why it matters here.** C3 is one of this run's four corrections, and its
YAML line is not evidence that it happened. A reader checking the config file
— or the manifest's config echo — would see nothing and could reasonably
conclude the split protocol was still armed. `preflight_pa2.py` therefore
asserts the value on the **rebuilt runtime Config**, which is the only
surface that answers the question.

**A second, smaller trap in the same field.** YAML 1.1 resolves a bare `off`
to the boolean `False`, and the field is `Literal["auto","on","off"]`. The
value must be quoted. Both the unquoted-boolean and the not-carried
behaviours are silent, and they compose: an unquoted value that also is not
echoed leaves no trace anywhere a reader would look.

---

## F3 — P-A1's `pa1` soak case is unreachable from `main` (OBSERVATION)

**Status:** open, low cost, recorded for completeness.

`scripts/cycle_soak.py --list-cases` on main offers eight cases and none is
`pa1`: that row lives on P-A1's branch alongside the stub fixtures of F1. A
tranche wanting to re-soak P-A1's exact shape on main cannot, which is the
same merge gap as F1 seen from a different side. This tranche registers its
own case from `soak_pa2.py` rather than editing source, which is a road any
later tranche can take.

---

## Findings the LIVE RUN may add

This file is written before the run's own findings exist. PREREG §4 names the
outcomes that would become findings — a `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`
second instance (P5), transport diagnostics surviving the `low` correction
(P2), or `hv` still unreachable with the grant present (P3) — and the run's
segments in RESULTS.md record which of them happened.
