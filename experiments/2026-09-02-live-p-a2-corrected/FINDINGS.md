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
