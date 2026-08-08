# Capability Request Audit

Manifest: `b54979da17fca86a7d75b52bb604f421aa4941c4aa64eff8eadd5bdd15d88d9e`

Every entry below is reconstructed from typed Capability events and immutable records.

## lcg_die_fairness_10000

Proposal: `sha256:101950108968cc1671245d3808e53aa211fc072f1f281085eea2146ee9e11166`  
Origin work: `sha256:1930575119aa7543965357d0d62768c4fd573cfeaba57900ba159cde0768fa86`  
Source call sequence: `20`  
Hypothesis: The exact LCG recurrence X_0=42; X_(n+1)=(1103515245*X_n+12345) mod 2^31; die_n=1+(X_n mod 6) for n=1..10000 produces a specific face-count distribution. The simulation returns the exact six face counts, total, and a 10-pair calibration trace so the recurrence and face-mapping can be verified by hand. The verdict on fairness (all counts within 2*sigma of 10000/6) is left to the adjudicator.  
Discriminating purpose: Produce the exact six face counts (count_1..count_6) and total for the specified LCG over 10000 draws, plus a calibration trace of the first 10 (X_n, die_n) pairs, so the fairness question can be settled by the actual numbers rather than by structural-bias heuristics.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

