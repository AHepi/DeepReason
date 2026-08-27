# Findings

## Question

Construct a configuration of 13 points in the unit square achieving the largest minimum triangle area you can; every candidate must state its coordinates and claimed score, and survives only if the checker confirms it. Score = the smallest area among all 286 triangles formed by triples of your 13 points; every point must lie in [0,1]x[0,1] and all 13 points must be distinct. State the construction in exactly this form, one point per line: a line "POINT x y" for each of the 13 points, with x and y written as decimals with at most 6 decimal places, then a final line "CLAIM v" giving your claimed minimum triangle area as a decimal. A claim the checker cannot confirm is refuted.

## Positions the record accepts

21 positions stand formally accepted. Where they answer the same question differently they are unresolved rivals: the record deliberately preserves the disagreement rather than merging it.

- {"cycle": 2, "evidence": {"conjecturer": {"n": 6, "repair_rate": 0.0, "truncation_rate": 0.0}}, "knobs": {"cap:conjecturer": 20480}} `[56f9c6cb7b0d]`
- nu: verdict of frontier-claim-honest@v1 on 305a72d19b3be8a93a5ec25c612c761e4e10d648127fce3b4dc252a82c308c5b is sound and relevant `[4c756ac4d14e]`
- critic: frontier-claim-honest@v1 failed on 305a72d19b3b `[3b99a2f8978c]`
- nu: verdict of frontier-above-floor@v1 on 305a72d19b3be8a93a5ec25c612c761e4e10d648127fce3b4dc252a82c308c5b is sound and relevant `[f86ce9d2255b]`
- critic: frontier-above-floor@v1 failed on 305a72d19b3b `[a38c3abfb411]`
- nu: verdict of frontier-claim-honest@v1 on b68e0539c9d09b9fd6d1ebdd4c8242032356fada3238ba3e3ff9223bfb26e7cd is sound and relevant `[9704c211ae22]`
- critic: frontier-claim-honest@v1 failed on b68e0539c9d0 `[b9322acd4f35]`
- nu: verdict of frontier-above-floor@v1 on b68e0539c9d09b9fd6d1ebdd4c8242032356fada3238ba3e3ff9223bfb26e7cd is sound and relevant `[41f20208d31e]`
- critic: frontier-above-floor@v1 failed on b68e0539c9d0 `[f3dd90a5d3d5]`
- nu: verdict of frontier-claim-honest@v1 on d3d6ef593f531d46e7d40a3e224135621842b5882785271967246bfc874241f1 is sound and relevant `[3570335cd855]`
- critic: frontier-claim-honest@v1 failed on d3d6ef593f53 `[3fb3d563deab]`
- nu: verdict of frontier-above-floor@v1 on d3d6ef593f531d46e7d40a3e224135621842b5882785271967246bfc874241f1 is sound and relevant `[1e8efc50b519]`
- critic: frontier-above-floor@v1 failed on d3d6ef593f53 `[bdaad3ec0790]`
- nu: verdict of frontier-claim-honest@v1 on 559b426a0d540fcee3900fca220a5ec54294490c4fbbe32161a5e5880e3b68ca is sound and relevant `[c118ddd9795a]`
- critic: frontier-claim-honest@v1 failed on 559b426a0d54 `[88e22c703009]`
- nu: verdict of frontier-above-floor@v1 on 559b426a0d540fcee3900fca220a5ec54294490c4fbbe32161a5e5880e3b68ca is sound and relevant `[7bbd88e7b1d6]`
- critic: frontier-above-floor@v1 failed on 559b426a0d54 `[e5709b6807a0]`
- {"adjustments": {"render_slices": {"attackers": 10, "departures": 8}}, "bands": {"ath": false, "debt": true, "egr": true, "rr": true, "sc": true, "var": true}, "enter_k": 2, "exit_k": 0, "mode": "diversify", "no_lever": {"critic_budgets": "the lever exists but belongs to the ALLOCATION controller under its own envelope law; two controllers writing one seat cap is a defect, not a feature", "lineage_quotas": "no lineage quota exists on this tree; a scheduler that capped work per lineage root would be one", "retrieval_balance": "retrieval balance lives on the evidence policy, not on a knob this c… `[081f6623da8a]`
- {"cycle": 4, "evidence": {"conjecturer": {"n": 6, "repair_rate": 0.0, "truncation_rate": 0.0}}, "knobs": {"cap:conjecturer": 12800}} `[c6e27bb93265]`
- {"cycle": 6, "evidence": {"conjecturer": {"n": 6, "repair_rate": 0.0, "truncation_rate": 0.0}}, "knobs": {"cap:conjecturer": 8000}} `[f7fda6a61308]`
- {"cycle": 8, "evidence": {"conjecturer": {"n": 6, "repair_rate": 0.0, "truncation_rate": 0.0}}, "knobs": {"cap:conjecturer": 5000}} `[08f91786ac9d]`

## Positions the record refuted

- POINT 0.01 0.01 POINT 0.95 0.01 POINT 0.01 0.99 POINT 0.99 0.99 POINT 0.50 0.50 POINT 0.40 0.15 POINT 0.85 0.50 POINT 0.55 0.80 POINT 0.15 0.50 POINT 0.30 0.25 POINT 0.75 0.30 POINT 0.25 0.75 POINT 0.75 0.75 CLAIM 0.005 `[305a72d19b3b]`
- POINT 0.05 0.05 POINT 0.95 0.05 POINT 0.05 0.95 POINT 0.95 0.95 POINT 0.50 0.50 POINT 0.45 0.20 POINT 0.80 0.50 POINT 0.55 0.80 POINT 0.20 0.50 POINT 0.35 0.25 POINT 0.70 0.30 POINT 0.30 0.70 POINT 0.65 0.75 CLAIM 0.005 `[b68e0539c9d0]`
- POINT 0.02 0.02 POINT 0.98 0.02 POINT 0.02 0.98 POINT 0.98 0.98 POINT 0.50 0.50 POINT 0.42 0.18 POINT 0.82 0.52 POINT 0.58 0.82 POINT 0.18 0.48 POINT 0.32 0.28 POINT 0.72 0.32 POINT 0.28 0.72 POINT 0.72 0.72 CLAIM 0.005 `[d3d6ef593f53]`
- POINT 0.01 0.01 POINT 0.99 0.01 POINT 0.01 0.99 POINT 0.99 0.99 POINT 0.50 0.50 POINT 0.40 0.10 POINT 0.90 0.50 POINT 0.60 0.90 POINT 0.10 0.50 POINT 0.20 0.20 POINT 0.80 0.20 POINT 0.20 0.80 POINT 0.80 0.80 CLAIM 0.005 `[559b426a0d54]`

---
Every statement above is derived from the append-only run record; nothing was generated by a model for this report. Accepted does not mean true — it means the position survived recorded criticism so far, and the run remains continuable.
