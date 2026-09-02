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
