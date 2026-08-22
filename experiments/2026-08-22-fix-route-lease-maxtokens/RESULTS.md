# Results — route lease vs controller-tuned max_tokens

Narrative for this tranche only. The reach-rich live experiment's own
narrative stays in `experiments/2026-08-22-live-reach-rich-run/RESULTS.md`;
this tranche did not run the harness and adds nothing there.

---

## 2026-08-22 — the producer was named in the record, and both halves moved

**What the record showed.** The epoch-2 reach-rich run
(`40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`) died at
cycle 2 of 24 with `state=failed`, `stop_reason=operational_failure`, and the
typed error `ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens
expected=32768 actual=20480`. PARKED.md P9-reach recorded that `20480` was no
literal in `src/` and appeared in no token-reservation record, named the
transport clamp at `adapter.py:1193` as an unverified candidate, and made
establishing the producer the first obligation of this tranche.

**The producer is the allocation controller, and the record says so directly.**
`log.jsonl` seq 442 is a `Refl` event whose artifact
(`492b41029fbd2b6f16eef2f520818a65c84e5f504ff59ab70d419fb334bf4003`) reads,
verbatim: `{"cycle": 2, "evidence": {"argumentative_critic": {"n": 6,
"repair_rate": 0.0, "truncation_rate": 0.0}, "conjecturer": {"n": 6,
"repair_rate": 0.0, "truncation_rate": 0.0}}, "knobs":
{"cap:argumentative_critic": 20480, "cap:conjecturer": 20480}}`, provenance
`role: "controller"`. The value re-derives from committed code exactly:
`cap_envelope('cap:conjecturer', 32768)` yields `{'min': 800, 'max': 32768,
'step': 1.6, 'dwell': 2}` and `round(32768 / 1.6) = 20480`. Seq 577 is the
resulting refusal; seq 578 is the stop. No provider call separates them.

**The named candidate was wrong, and now explained rather than merely
excluded.** `adapter.py:1193` reads `getattr(endpoint, "max_tokens", ...)`
into the attempt trace and runs *after* the `lease.verify(endpoint)` that
raised. On this run it never executed — which is precisely why `20480` appears
in no `workflow-token-reservation-v2` record. P9-reach's negative result is
confirmed and its cause identified.

**Epoch 1 emitted the byte-identical policy.** Same content hash, at its own
seq 352, followed by an unrelated death (P7-reach repair exhaustion) 76 events
later with no further provider call. The tune is deterministic across both
epochs; which of two deaths lands first is not. That rules out treating epoch
2 as a stochastic one-off.

**The disagreement, and which half moved.** `llm/firewall.py` carried both
rules within six lines: a comment saying `max_tokens` is a process-health
control the deterministic controller may tune, and a conditional adding
`max_tokens` to the frozen equality set whenever the route declares
`context_window_tokens`. The record chose the direction rather than taste:
`invariants.py` — frozen surface 3 — already admits an attempt whose
`max_tokens` differs from the route's when a prior logged controller policy
authorized it, so the replay validator and the firewall were in direct
contradiction; `INV-signal-contract.md` makes allocation's efficiency function
a frozen operator law; and the gate test pinning the strict branch is named
`test_runtime_endpoint_cannot_widen_frozen_capacity`, so the branch was
stricter than its own stated purpose. A ceiling serves that purpose exactly.

**Both halves moved, because one is not enough.** The reproduction demonstrated
an unrecorded sibling: `cap_envelope` anchors a knob's ceiling at
`max(static_max, configured_cap)`, so a qualified seat leased BELOW the static
ceiling (3000 against `cap:conjecturer`'s 5000) could be widened to 4800 by a
truncation signal — above its lease, and refused the same way. No committed
root shows it; it is closed at the tuner by `Controller._lease_ceiling`,
applied in both `_propose` and `_apply_cap`.

**What the record now shows.** Nine mutation-proven regression tests
(`tests/test_route_lease_maxtokens_tuning.py`); five deliberate sabotages each
killing exactly one test; `repro.py` inverted on all three cases; full gate
3829 passed / 0 failed against a 3820 baseline; `docs_verify` 976 checks with
only the three pre-existing shallow-clone failures, `--audit` 0 findings. Both
epoch roots re-derive to 0 `verify_root` violations, matching their stored
verdicts — no verdict moved, as predicted, because `cap_envelope` was left
byte-identical precisely so that replay validation's authorized set could not
narrow.

**The map gained the seam that did not exist.** `llm × scheduler` was already
listed in both owning documents' `Seams-undocumented:` headers, so
`SEAM-llm-x-scheduler.md` closes an identified gap rather than inventing one.
It crosses zero imports in the direction that matters — `controller.py`
imports nothing from `deepreason.llm` and reaches the leases duck-typed off
the adapter — which is why no coupling metric could have surfaced this pair,
and why `INDEX.md`'s matrix now lists it among the seams with no import count.

**Residue.** Proven offline, not live: no third epoch has run, and P7-reach
remains open, so a relaunch can still die at cycle 2 of a different cause.
Case B has no live witness and now cannot acquire one. The `dropped-call`
mis-tagging of a firewall refusal is parked as P1-lease, unmeasured on the
question that decides it. Accepted does not mean true; what is shown here is
that this configuration can no longer die this particular way, not that the
next run will finish.
