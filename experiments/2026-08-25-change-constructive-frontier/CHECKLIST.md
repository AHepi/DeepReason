# CHECKLIST — the constructive frontier, and P-C1

State: **step 1 of 13 — not started**

One step per `dr-execute-step` invocation. A step is checked ONLY with its
real done-criterion output pasted beneath it, copied from the terminal. No
step is checked in advance of running it. Every step cites SPEC.md items and
REQUEST.md requirements.

---

- [ ] **1. PROGRAM v2** — amend
      `experiments/2026-08-25-poietics-program/PROGRAM.md`: v2 header,
      P-R2/P-R3 CANCELLED with the operator's verbatim words as the
      cancelling authority, the series renamed to CONSTRUCTIVE FRONTIER,
      the problem class registered, P-C1 registered.
      *(S12; R5, R6, R7, R8)*
      **Done-criterion:** greps show the v2 header, both CANCELLED
      markers, the operator's quoted words, the problem class, and P-C1.

- [ ] **2. The checker** — `checker.py`: exact-rational scorer, the four
      validity rules, the claim check, `--score` and `--self-test`.
      *(S3; R12, R13, R14)*
      **Done-criterion:** `python checker.py --score` on a known-good
      construction prints `"valid": true` with an exact rational score.

- [ ] **3. The checker's mutation proof** — the S4 table, RED then GREEN.
      *(S4; R16)*
      **Done-criterion:** each of M2 and M3 shown FAILING against a
      deliberately weakened checker (RED), then caught by the real one
      (GREEN); `python checker.py --self-test` exits 0.

- [ ] **4. The in-run demarcation battery** — the three `predicate:`
      commitments, written to be evaluated by `programs.evaluate`.
      *(S5; R15)*
      **Done-criterion:** all three pass `programs._validate_predicate`.

- [ ] **5. The criteria preflight** — `preflight_criteria.py`: validity,
      the mutation table through the harness's own evaluator, the
      float-vs-exact bound, and the discrimination controls.
      *(S6; the `DR-SEAM-evaluation-x-ontology` malformed-predicate trap)*
      **Done-criterion:** `python preflight_criteria.py` exits 0.

- [ ] **6. ARM H's configuration and builder** — `run-config.yaml`,
      `build_manifest_pc1.py`, `pc1_run.sh`, `snapshot_loop.sh`.
      *(S7; R20, R28)*
      **Done-criterion:** `DRY_RUN=1 ./pc1_run.sh` exits 0 without a
      provider call.

- [ ] **7. The soak case** — one `SoakCase` entry in
      `scripts/cycle_soak.py`, in this same commit.
      *(S11; R26)*
      **Done-criterion:** `python -u scripts/cycle_soak.py --case pc1`
      exits 0, verbatim output pasted.

- [ ] **8. PREREG frozen and pushed** — `PREREG.md` carrying the question,
      both arms, the matched-budget rule, the registered prediction, the
      milestones and the repeat authorisation. Pushed BEFORE any provider
      call.
      *(S8, S9, S10; R17, R18, R19, R21, R22, R23, R24, R25)*
      **Done-criterion:** `PREREG.md` committed and pushed; the push
      precedes the first entry in `driver.log`.

- [ ] **9. ARM H launch** — detached, snapshot loop armed. Requires the
      operator's key (R27).
      *(S7; R20, R28)*
      **Done-criterion:** the run reaches a typed terminal; `verify_root`
      clean; `deepreason results` captured.

- [ ] **10. ARM S run** — `arm_s.py` to the measured matched budget.
      *(S8, S9; R21)*
      **Done-criterion:** `arm_s/results.jsonl` exists, cumulative tokens
      within the S9 band of ARM H's actual spend.

- [ ] **11. The census** — `milestone_census.py` decides M1/M2/M3 from the
      typed record and the checker outputs alone.
      *(S10; R4, R24, R31)*
      **Done-criterion:** `milestones.json` written; survivor figures
      conjecture-only.

- [ ] **12. RESULTS.md** — the honest ledger: both best scores, the
      margin, the refutation count, the residue.
      *(S13 C9; R2, R30)*
      **Done-criterion:** every number in it traces to a typed artifact or
      a checker output.

- [ ] **13. VALIDATION.md + DELIVERY.md** — every S13 acceptance check
      proven; R-by-R reconciliation; `git diff --stat` showing one file
      changed outside this directory.
      *(S13; R32)*
      **Done-criterion:** VALIDATION verdict PASS, DELIVERY table complete.

---

## Step outputs

*(Each step's verbatim terminal output is appended here as the step is
executed. Nothing is written here in advance.)*
