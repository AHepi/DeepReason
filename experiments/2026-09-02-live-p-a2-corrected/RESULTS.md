# P-A2 — P-A1 re-run on the corrected configuration

Dated, honest-ledger segments. Each records what the RECORD shows and the
RESIDUE — what remains unproven. Model prose is never evidence here, on
either side of a claim. "Accepted does not mean true," and a negative or
inconclusive result is recorded as one.

The baseline throughout is P-A1 (run `4565139800f5ca02…`, branch
`claude/live-reasoning-p-a1-bv65kl`, read-only here) plus `MONITOR_REVIEW.md`
on main. The design is frozen in PREREG.md and was frozen before the first
live provider call.

---

## 2026-09-02 · Segment 1 — the configuration is P-A1's with four fields moved, and the diff proves it

**What the record shows.** The parsed-config difference between P-A1's
`run-config.yaml` and P-A2's is **13 leaves**, and every one belongs to a
correction the tranche instruction names:

| leaves | change |
|---|---|
| 6 | `reasoning` absent → `"low"` on every glm-5.3 seat |
| 6 | `max_tokens` 49152 → 32768 on every glm-5.3 seat |
| 1 | `SPLIT_BUDGET_SEAT_PROTOCOL` absent → `"off"` |

deepseek's five seats (49152, `reasoning` unset) and both judge seats (32768,
`reasoning` unset) are untouched, which is the control half of the
comparison. The seed question is byte-identical: digest
`933313a5d9ca6dd86f3052aec6e1f05f395ad00586e08096bd40d1be733d7560`,
asserted by the builder before any provider call, and the three scoring
criteria are P-A1's.

The compiled route matrix confirms the corrections reached the wire rather
than only the file: six glm-5.3 seats (conjecturer seat 1, defender,
summarizer, synthesizer, vision_critic, grounding_reviewer) at
`reasoning=low, max_tokens=32768`; deepseek and both judges unmoved.

**Two silent traps, caught by probe rather than by reading.** Both are
recorded in FINDINGS.md (F2) because either alone would have made C3 a claim
rather than a fact, and they compose into a change that leaves no trace
anywhere a reader would look:

1. **YAML 1.1 resolves a bare `off` to the boolean `False`**, and the field
   is `Literal["auto","on","off"]`. Unquoted, the value reaching Config is
   `False`.
2. **`SPLIT_BUDGET_SEAT_PROTOCOL` is popped from the manifest's
   engine-config echo** (`run_manifest.py:2469`) and arrives only through a
   carriage notice, which the compile emits verbatim: *"…is not carried by
   this manifest's engine config and is restored at run time from this
   notice"*. `preflight_pa2.py` therefore asserts the value on the REBUILT
   runtime Config, never on the YAML.

**Residue.** The diff being exactly the corrections is a property of the
CONFIGURATION, not of the run. It says the comparison is clean; it says
nothing yet about whether the corrections work.

---

## 2026-09-02 · Segment 2 — the monitor P-A1 lacked, proved in three directions before launch

**What the record shows.** P-A1's monitor classified a dead provider attempt
as `t.get("error") or t.get("failure") or t.get("status") == "error"`. The
attempt trace carries none of those three keys, so it printed
`provider calls FAILED: none` through 40 transport faults — 66% of that
run's wall clock (`MONITOR_REVIEW.md` MR-B).

`monitor_pa2.py` reads the typed vocabulary the harness actually writes, from
two independent surfaces that must agree: the stored objects
(`workflow-provider-attempt-v1` → `provider_result` | `transport_failure`;
`criticism-attempt-v1` → `completed` | `schema_failure` |
`transport_failure` | `budget_denied`;
`workflow-semantic-admission-v1` → … | `schema_exhausted`) and the log's
`attempt_trace` rows (`tokens`, `usage_unknown`, `transport_diagnostics`).
Stored objects wrap the record under a `data` key — a reader that skips that
sees every `outcome` as `None` and reports a clean run, which is the same
class of mistake in a new place.

It was proved in three directions, all committed:

1. **Planted fixture** (`monitor_fixture_proof.txt`): six synthetic roots,
   one per alert, **plus a clean control that must stay silent**. All six
   pass. The control is the half that is easy to skip and is not optional —
   a monitor that shouts at everything looks, in one screenshot, exactly as
   healthy as one that never shouts.
2. **Real regression** (`monitor_pa1_regression.txt`): pointed at P-A1's own
   committed record it re-derives **40 diagnostics (39 `RemoteDisconnected`
   + 1 `HTTPError`, all glm-5.3, none on any other model)**, **10 zero-token
   attempts of 71**, **10 typed provider `transport_failure`** split 6
   conjecturer seat 1 / 4 defender seat 0 — agreeing with MR-A, which derived
   its counts independently — and finds **two facts MR-A did not tally: 4
   `criticism-attempt-v1` transport failures and 2 `schema_exhausted`
   admissions**.
3. **A healthy live root**: run against the offline soak's root mid-drive it
   reported 194 provider attempts, all `provider_result`, and **no alert**.

**Residue.** The monitor proves it can SEE the P-A1 signature. It does not
make the signature less likely, and P2 is registered as the prediction most
likely to be refuted for exactly that reason.

---

## 2026-09-02 · Segment 3 — the launch gate was red, and the cause was the instrument

**What the record shows.** The first P-A2 soak failed qualification: **10 of
23 pairs, 200 of 460 cases** (`soak_output.txt`, manifest
`27dae00f0d188437`). Read before theorising, the per-pair failure codes name
the cause: two pairs failed `ENDPOINT_HTTP_500`
(`config-referee.v1` on deepseek, `groundingrepairwirev1.direct.v1` on
glm-5.3) and **eleven failed `CIRCUIT_OPEN_ENDPOINT_HTTP_500`** — cascade,
not independent faults. The offline stub has no fixture for
`ConfigRefereeWireV1` or `GroundingRepairWireV1`; an unsatisfied fixture is a
500, and a 500 opens the qualification circuit breaker for the whole
endpoint, so two gaps cost thirteen pairs.

**What it does NOT mean.** Nothing about P-A2's configuration, and nothing
the live run can hit: the failing responder is the offline STUB. Both
contracts are granted by configuration and both qualify against a real model.

**It is a recurrence, and that is the finding.** P-A1 met this, filed its own
F1, fixed it in `scripts/wheel_operational_smoke.py` — and **that fix never
merged to main**. So it returns for every later tranche that turns the config
referee or the bridge's repair path on. FINDINGS.md F1 preserves the
non-obvious half so it is not re-derived a third time: `remove_span` is the
correct grounding-repair fixture because it is the one action carrying no
substantive field (satisfying the schema's cross-field `allOf`/`if`/`then`
implications) AND the only action present in every entry of
`_ALLOWED_BY_STATUS` — the caller narrows the contract while the advertised
schema still `$ref`s the full enum, so a fixture chosen from the schema alone
can be structurally valid and out of scope. `correct_wording` is exactly that
trap.

**Routed around, not fixed.** `soak_pa2.py` rebinds
`wheel_operational_smoke.response_for_schema` to a wrapper carrying P-A1's
two fixtures verbatim, delegating everything else. No source file is edited.
The patch STRENGTHENS the gate: two contracts that could not be exercised at
all must now return schema-valid, in-scope responses or their pairs still
fail. With it, the same shape **qualified in 14.5 s**.

**Residue.** A green soak proves these contracts can be DISPATCHED and their
responses parsed against a deterministic stub. It proves nothing about
whether a real model produces useful referee verdicts or grounding repairs —
only the live run speaks to that, and no soak can stand in for it. The soak
also reproduces ONE of the four 2026-08-22 operational deaths and asserts the
other three, so green is not full coverage.

---

## 2026-09-02 · Segment 4 — the gate refused one seat, and the cause is the reasoning knob alone

**What the record shows.** The live run never reached a reasoning cycle. The
ladder stopped at qualification after 96 minutes with **22 of 23 pairs
qualified, 445 of 460 cases** — the gate doing precisely its job, refusing a
seat that cannot fill its contract *before* the run spends a token budget on
it. Compared pair-by-pair against P-A1's own `qualify.json` (23/23, 460/460),
**exactly one pair moved**: `grounding_reviewer /
groundingrepairwirev1.direct.v1 / glm-5.3`, from 20/20 to **5/20** against a
threshold of 19, with 15 `VALUE_ERROR` and 31 repair attempts spent.

Every other pair is 20/20 in BOTH runs, including six other glm-5.3 contracts
and four glm-5.3 scratch contracts. The corrections did not broadly degrade
this model; they cost exactly one contract.

**Which correction — measured across 60 live calls, not argued.** P-A2 moved
three things about that seat at once, so the isolation probe exercised only
that pair through the doctor's own per-case entry point:

| cell | reasoning | cap | split | valid |
|---|---|---|---|---|
| A | `low` | 32768 | off | **2/10** |
| C | `low` | 32768 | auto | **3/10** |
| E | `low` | 49152 | off | **4/10** |
| B | unset (`max`) | 49152 | auto | **10/10** |
| D | unset (`max`) | 49152 | off | **10/10** |
| F | unset (`max`) | 32768 | off | **10/10** |

**Perfect separation on the reasoning knob.** Every `low` cell fails at 2–4 of
10; every default-effort cell passes 10 of 10, while the cap and the split
protocol vary freely within each group and change nothing. Cell B reproduces
P-A1 exactly, which is what makes the comparison admissible: the cause is this
tranche's change, not provider drift.

**Two hypotheses refuted, both of them the monitor's own, and both stated to
the operator before the measurement came back.** First, that turning the
split-budget protocol off was the culprit — refuted by cell D (split off,
10/10) against cell C (split on, 3/10). Second, that this was F1's
forbidden-action trap reaching a live model — refuted by the record's own
`scope_violations: 0`, since `BRIDGE_REPAIR_ACTION_FORBIDDEN` is classified as
a scope violation and would have been counted as one.

**What it means, and what it does not.** It does NOT mean `low` was the wrong
correction: `low` is measured-correct for the generation seats, where six
glm-5.3 contracts qualify 20/20 and where P-A1's transport wall actually was.
It means the reasoning knob is **not uniform across contracts on one model**.
The committed profile's headline — *"set this seat's `reasoning` to `low`"* —
is right for generation and wrong for at least one structured-repair contract,
whose schema makes three fields required or forbidden depending on the chosen
action. Every failing case spends both repair attempts and still ends invalid,
which is a structural miss rather than a truncation.

**Residue.** This is 60 calls on ONE contract and ONE model; it does not say
which other contracts have the same sensitivity, and it does not identify the
exact field the model gets wrong — no raw response is persisted by the doctor,
by design, and this tranche did not add one. The five pre-registered
predictions P1–P5 are **unscored**: none of them can be evaluated, because no
reasoning cycle ran. That is recorded as an unscored outcome, not as a
negative one.

---

## 2026-09-02 · Segment 5 — the amendment shipped, and epoch 2 died on an account usage cap

**What the record shows.** The operator ruled for the per-seat remedy, and it
was implemented, gated and rehearsed before relaunch: `grounding_reviewer`
alone runs at glm-5.3's default effort while the five generation seats keep
`low`; the cap stays 32768 on all six because the isolation says the cap is
irrelevant here. The preflight gates the exception **in both directions** — a
generation seat that lost `low` fails it, and the reviewer seat carrying `low`
fails it too — and epoch 2 cleared **62 checks, 0 failures**. The amended
shape soaked GREEN beforehand: 24 of 24 cycles, `completed` /
`budget_exhausted`, `verify_root` 0 violations.

Epoch 2 launched 22:03:13Z and its qualification refused 26 minutes later,
against epoch 1's 96. **5 of 23 pairs, 100 of 460 cases**, and one failure
code throughout: `ENDPOINT_HTTP_429`, with the circuit breaker opening on both
endpoints at 20 block failures each and skipping 120 cases per opening. One
confirming call after the run returned the provider's own text: *"you
(aaron_thyne) have reached your session usage limit"*, with no `retry-after`
header. **An account usage cap, not a transport fault and not a contract
failure.**

**P6 is UNTESTED, not refuted — and the distinction is the whole point of
pre-registering it.** P6 predicted 23 of 23 with the grounding-repair pair
back above threshold. That pair did fail, but with `ENDPOINT_HTTP_429`,
exactly like twelve other pairs and like contracts that had already qualified
20/20 twice. A battery that cannot reach the provider says nothing about a
schema. Recording this as a refutation would have been the easiest and most
wrong reading available.

**F4 survives it, on the strength of its own control.** The isolation
completed before the cap and carried cell B — P-A1's settings — at 10/10 in
the same session in which cells A, C and E scored 2, 3 and 4 of 10. A usage
cap would have failed all four alike; a control that passes while its siblings
fail cannot be explained by one.

**Owning the part that was mine.** Three things ran against the account today:
epoch 1's full battery (~1 100+ completions), the F4 isolation probe
(~100–180), and epoch 2 until the breaker opened (~100+). The batteries
dominate, but the probe was mine and it was not free. It was still the right
call — it converted a bare failure into a measured attribution, and the
operator's standing law prefers generated evidence to agent reasoning — but it
is recorded as a contributor rather than quietly omitted.

**Residue.** P1–P5 remain **unscored**: no reasoning cycle has run in either
epoch. P6 is unscored too. What this tranche has proven is real but entirely
pre-cycle: the configuration is correct and gated, the monitor sees what
P-A1's could not, both soaks are green, and two defects are measured (F4's
per-contract reasoning sensitivity, F1's recurring stub gap). What it has NOT
produced is the live before/after against P-A1 that it was built for. Nothing
in the tranche needs rebuilding to get it — only the cap to clear.

---

## 2026-09-03 · Segment 6 — P6 HOLDS: the per-seat remedy is confirmed, and reasoning finally starts

**What the record shows.** With the account cap cleared (confirmed by a single
probe call returning HTTP 200 before anything was spent), epoch 3 launched
01:49:41Z, cleared **62 preflight checks with 0 failures**, and its
qualification returned **`QUALIFY OK rc=0`** at 02:33:05Z — 42 minutes.

    qualified            true
    qualified_pair_count 23 of 23
    eventual_valid_count 460 of 460
    first_pass_valid     456
    repair_count         4
    scope_violations     0

**The pair that blocked epoch 1:**

| | eventual_valid | first_pass | repairs |
|---|---|---|---|
| epoch 1 (`low`) | **5 / 20** | 4 | 31 |
| epoch 3 (default effort) | **20 / 20** | **20** | **0** |

**P6 HOLDS.** Twenty of twenty, every one valid on the FIRST pass with zero
repair turns spent — not a marginal clearance of the 19-threshold but the
contract satisfied outright.

**Why this is the load-bearing confirmation of F4.** The isolation probe
(60 calls, six cells) had already separated the reasoning knob from the cap
and the split protocol, but it exercised one pair in isolation through the
doctor's per-case entry point. This is the full battery, on the real launch
shape, at production scale: had the attribution been wrong — had the cap, the
split protocol, or something unmeasured been the cause — this is precisely
where it would have surfaced, because everything except that one seat's
reasoning knob is byte-identical to the epoch that failed.

It also retires a live hypothesis honestly: epoch 2's refusal genuinely was
the usage cap and nothing else. Had the amended shape carried a second latent
defect, 23/23 would not have happened on the first attempt after the cap
lifted.

**Reasoning has started** — `state=running phase=workload cycle=0`. For the
first time in this tranche a reasoning cycle is running, so P1–P5 are live
questions rather than unscored ones. They remain unscored until the typed
terminal; nothing below is claimed in advance.

**Residue.** P6 says the seat can FILL its contract in a battery of
representative probes. It does not say the grounding bridge will produce a
useful repair on this run's actual artifacts — that needs the run to reach a
terminal with a composed output, which is what the ladder's bridge step at
terminal exists to test.
