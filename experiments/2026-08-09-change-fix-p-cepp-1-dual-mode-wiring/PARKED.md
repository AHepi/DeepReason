# Parked — P-CEPP-1 dual-mode wiring tranche

Nothing here is fixed in-tree this tranche. Each entry is a ready-to-send
prompt for a future tranche.

**P-CEPP-1-BATTERY-1 — should `cli/doctor.py` (frozen surface 5, the
qualification pair inventory) be widened so `conjecturer.turn.v7`
becomes reachable through the NORMAL `deepreason doctor`/qualification
battery, not just a hand-built bypass?**

Confirmed, not assumed (`REQUEST.md` Amendment 1): surface 5 is
byte-untouched by this tranche —
`ProductionContractPairV1.contract_id`'s `Literal`
(`src/deepreason/cli/doctor.py:62`) still does not admit
`"conjecturer.turn.v7"`. This tranche's own live run
(`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/
live_run_v7/`) proved v7 dispatches correctly end-to-end against a
real provider, but only by BYPASSING the qualification battery
(`scripts/live_run_v7.py::_bind_classification_bypassing_doctor`,
mirroring the same technique the S2/S4 regression tests use) — a
v7-configured manifest still cannot pass through `deepreason doctor`
or the ordinary `deepreason setup`/`deepreason run` CLI lifecycle,
because `production_contract_pairs(manifest)` raises a
`pydantic.ValidationError` the first time it tries to project a
`conjecturer.turn.v7` grant into a `ProductionContractPairV1`
(`src/deepreason/cli/doctor.py:332`).

This was explicitly out of scope for Option C (the operator's own
choice among three priced options, `SPEC.md`) and remains untouched by
design, not oversight — widening it would trigger a qualification
cache miss (~14 min, ~1160 calls, `CLAUDE.md`'s own documented cost of
any manifest/pair-inventory change) and touches a THIRD frozen surface
this tranche never got explicit words for.

---

**P-CEPP-1-MAP-1 — advance the `Verified-at:` stamps on
`SEAM-harness-x-verification.md` and `SUB-workflow.md`, and give
`SEAM-harness-x-verification.md` a sentence about the v6/v7
conjecturer-turn-contract dispatch fact.**

Found by `dr-validate-change`'s `python tools/docs_verify.py --stale`
run (`VALIDATION.md`), which is advisory and does not itself block a
PASS verdict — not fixed in that phase per its own rule against
editing map documents while validating them. Two small, purely
mechanical items:
- `SEAM-harness-x-verification.md` owns `invariants.py` (in addition
  to `SUB-verification.md`, which this tranche's own CHECKLIST step 11
  DID update) — this tranche's S4 commit (`d5f47101a`) touched that
  file without this seam document's prose or `Verified-at:` stamp
  being touched at all. Needs one sentence (the same v6/v7-both-
  authorized fact `SUB-verification.md`'s new row already states) plus
  a re-run of this document's own `check:` commands to justify
  advancing the stamp.
- `SUB-workflow.md`'s prose WAS updated in this tranche (CHECKLIST step
  8), but its `Verified-at:` stamp was never advanced even though
  `docs_verify.py`'s full run (CHECKLIST step 14, run twice) has since
  re-verified its checks clean — purely a bookkeeping gap, no content
  change needed, just re-run its checks standalone and bump the stamp.

**Ready-to-send prompt**: "Close `P-CEPP-1-MAP-1`
(`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/PARKED.md`):
(1) add one sentence to `docs/map/SEAM-harness-x-verification.md`
stating that `invariants.py`'s two conjecturer-turn-contract membership
checks (widened by the P-CEPP-1 tranche, commit `d5f47101a`) now
authorize both `conjecturer.turn.v6` and `conjecturer.turn.v7`, then
re-run that document's own `check:` commands standalone and advance its
`Verified-at:` stamp if they pass; (2) re-run
`docs/map/SUB-workflow.md`'s own `check:` commands standalone (no
content change needed, already updated by P-CEPP-1 commit `aaefae58e`)
and advance its `Verified-at:` stamp if they pass. Both are mechanical;
neither should need new investigation."

---

**P-CEPP-1-BRONZE-1 — `test_bronze_report.py::test_census_totals_internally_consistent`
fails deterministically (`159 == 165`), found by this tranche's own
full-gate run but proven unrelated to it.**

Discovered running `pytest tests/ -q -n 4` (`CHECKLIST.md` step 15).
Proven, not assumed, to predate and be independent of this tranche:
`git diff 781ad6811 HEAD -- tests/test_bronze_report.py
scripts/bronze_census.py experiments/bronze_flat_2026-07-13/` is
EMPTY (byte-identical to base); the census script's only `deepreason`
import (`harness.py`) is untouched by this tranche's five changed
files; the failure reproduces deterministically standalone, not
flaky; the experiment root is fully git-tracked with no missing or
modified files. This is a defect (not this tranche's to fix, per
CLAUDE.md's own "a defect found mid-change is PARKED, not fixed") in
`scripts/bronze_census.py`'s reconciliation of `gate_blocked` count
against `gate_measures` count for the `bronze_flat_2026-07-13`
experiment roots — a pre-existing counting/data inconsistency,
diagnosis not attempted here.

**Ready-to-send prompt**: "Diagnose and fix
`tests/test_bronze_report.py::test_census_totals_internally_consistent`,
which fails deterministically with `assert counts['gate_blocked'] ==
census['streams'][stream]['gate_measures']` → `159 == 165` (as of
commit `1931f788a`, the P-CEPP-1 tranche's own gate run — confirmed
pre-existing and unrelated to that tranche's diff). Start from the
record: `scripts/bronze_census.py`'s `build_census` function, the
`gate_blocked` tally (counts rows with `disposition == 'gate-blocked'`)
vs. the `gate_measures` tally (`len(gate_events)`) for whichever
stream disagrees — read the code before theorizing, per
`deepreason-orchestrator`'s diagnose-from-the-record discipline."

**Ready-to-send prompt**: "Widen `ProductionContractPairV1.contract_id`
(`src/deepreason/cli/doctor.py:62`, frozen surface 5) to admit
`\"conjecturer.turn.v7\"` alongside `\"conjecturer.turn.v6\"`, so a
v7-configured manifest can pass through the normal
`deepreason doctor`/qualification battery and the ordinary
`deepreason setup`/`deepreason run` CLI lifecycle without the
hand-built classification bypass
`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/
scripts/live_run_v7.py` uses. Requires explicit operator words for
touching frozen surface 5 specifically (this tranche's own Amendment 1
established that a prior option-selection's preview text is not a
substitute for that). Budget for the qualification cache miss (~14
min, ~1160 calls) this will cost. The four files this earlier tranche
(`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/`)
already wired (`run_manifest.py`, `rules/conj.py`,
`workflow/profiles.py`, `invariants.py`) do not need to be touched
again — they already treat v6 and v7 identically; only surface 5's own
pair-inventory Literal is the remaining gap."
