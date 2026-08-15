# CHECKLIST — Rung 2

State: **step 1 complete (the channel). Step 2 in progress (the wiring).**

## Step 1 — the channel (delivered, commit 56124b14)

| # | Step | Done-criterion | State |
|---|---|---|---|
| 1 | S1/S2 — `presupposition_wf` + the mention-law check | a `dependence`-ref'd attribution fails | ✅ |
| 2 | S4 — `premise_orphaned`, derived, both grades | two locks tested independently | ✅ |
| 3 | S5 — three resolutions as artifacts, reversible | attacking a retirement restores the problem | ✅ |
| 4 | S6a — the producer RULE | fires after N refutations, stands down once attributed | ✅ |
| 5 | A5 — the operator's siren case end to end | passes, with no conjecture on the problem | ✅ |
| 6 | S7 — map document | `docs_verify --ring` green | ✅ |
| 7 | Full gate | 3622 passed, 0 failed | ✅ |

## Step 2 — the wiring (SPEC.md "Step 2", R M12–M20)

| # | Step | Done-criterion | State |
|---|---|---|---|
| 8 | **S3a** — `measures/demarcation.py::crit(artifact, commitments)`; `PREMISE_RENT` commitment (`eval="demarcation:crit"`) in `premises.py` | A13: `crit()` False for structural-only and for rent-only interfaces; `_substantive(PREMISE_RENT)` is False | ✅ |
| 9 | **S3b** — `premises.py::premise_rent_sweep(harness)` registering the DEMONSTRATIVE fail warrant | A14: a rentless premise reaches `Status.REFUTED` with no hand-written attack in the test | ✅ |
| 10 | **S6b-i** — the filing channel: optional `premise` field on the four critic contracts | the four models carry it; `contract_id` values unchanged; `tests/test_wire_contracts.py` green | ✅ |
| 11 | **S6b-ii** — the pack invitation + registration in `rules/crit.py` | invited + `premise` present ⇒ premise X and attribution ρ registered; uninvited ⇒ nothing (A18) | ✅ |
| 12 | **S6b-iii** — the scheduler's three consults (retired filter, orphan rank term, invitation Measure) | A16 in both selection modes; pinned rank checks in `DR-SEAM-scheduler-x-rules` + `DR-CON-scheduler-ranking` moved in the same commit | ✅ |
| 13 | **S6b-iv** — the three signal declarations + per-cycle emission | A17: emitted by the real loop, every one non-`unspecified`; `tests/test_signals.py` + `tests/test_signal_contract.py` green | ✅ |
| 14 | **A15** — the producer fires in an offline run of the ACTUAL `Scheduler` loop | the loop test passes end to end: invitation Measure → premise + attribution → rent refutation → mark | ✅ |
| 15 | **[COMMIT]** map + gate | map moves in the same commit; `python tools/docs_verify.py` full; full gate 0 failed; `tools/diff_budget.py` measured (EXCEEDED, disclosed in SPEC.md) | ✅ |
| 16 | **S3c (M21)** — the SECOND check for prose: `mod`, completing `active()` | A20–A22 pass; full gate 3640 passed / 0 failed; `docs_verify` full at the 3-failure baseline | ✅ |
| 17 | **A19** — ONE guarded live run | typed outcome recorded either way: `verify_root`, run state, and whether any attribution reached the record | ⛔ **BLOCKED — no credential.** `experiments/*/env` is absent and `OLLAMA_API_KEY` is unset in this container. The ladder cannot reach a provider, so the run cannot be attempted, let alone judged. Not a MISS (a miss requires a run); an un-attempted check. Needs the operator's key. |
