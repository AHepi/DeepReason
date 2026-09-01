# Diagnosis: an omitted compiler argument separates defended-trial intent from the manifest fields that authorize it

Primary cause: `compile_run_manifest` treats an omitted `criticism_policy` as authoritative `None` even when the carried runtime `Config` requests engaged `defended_trial` criticism. It then stores no criticism policy and compiles defender/judge behavioral grants only when the stored policy is present and has `authority == "defended_trial"`. P-S1's builder supplied the requesting `Config` but omitted the policy argument, so the manifest silently froze observation-only criticism with empty trial grants.

Evidence:
  - `claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/failed-epoch1-run-712b0f5c8f463166/run-manifest.json` -> `criticism_policy` is null; `config_from_run_manifest` restores `ENGAGED_CRITICISM_AUTHORITY='defended_trial'`, both master gates true, and `LEGACY_CRITICISM_ENABLED=false`; defender and both judge plan entries have zero contracts. Its typed `log.jsonl` records 140 `Measure(["scrutiny", ...])` observations.
  - `claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/completed-epoch2-run-9e48a36b1dec91ee/run-manifest.json` -> the same null-policy/non-null-runtime split and the same empty trial grants. Its typed `log.jsonl` records 147 scrutiny observations (seq 96 through 3839).
  - `claude/deepreason-p-s1-commitments-wowcib:experiments/2026-08-31-p-s1-commitments/build_manifest_ps1.py:264-290` -> the call supplies `config`, v6 control policy, routes, and inquiry policy but no `criticism_policy=` argument.
  - `src/deepreason/run_manifest.py:3652,3721-3724,4005-4008,2059-2077` -> omission resolves to `None`, no manifest policy field is stored, and defender/judge contracts are added only for a stored `defended_trial` policy. `src/deepreason/rules/crit.py:88-113,2209-2224` then files resolved `observe_only` cases as scrutiny.

Implicated code: `experiments/2026-08-31-p-s1-commitments/build_manifest_ps1.py:264-290` (read-only witness); `src/deepreason/run_manifest.py:3629-3653,3712-3725,3978-4008,2059-2077`; `src/deepreason/rules/crit.py:88-113,2209-2224` (read-only downstream witness)

Falsifiable prediction: `python experiments/2026-09-01-defect-judge-canary-compile-gap/reproduce_compile_gap.py` on the anchored base will exit 0 only after printing a v6 manifest with carried runtime authority `defended_trial`, stored criticism policy `null`, effective criticism authority `observe_only`, and empty defender/judge trial-contract lists.

Ruled out: the P10 configuration-carriage fix is not the remaining defect. Reconstructing `Config` from both committed manifests restores every relevant requested value; the loss occurs specifically between that carried intent and the separately supplied manifest `criticism_policy`, before downstream trial dispatch.
