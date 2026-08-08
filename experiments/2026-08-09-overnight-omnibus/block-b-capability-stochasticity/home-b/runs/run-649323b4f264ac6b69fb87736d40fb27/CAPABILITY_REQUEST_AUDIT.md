# Capability Request Audit

Manifest: `e41756268190fd0f705c8bad4cf7c406cd3d84bddfdda05c661c9527ebed03fa`

Every entry below is reconstructed from typed Capability events and immutable records.

## lcg_die_fairness_301b61

Proposal: `sha256:6eaab344f9ef2d62856703d0f2d81dc984c208b76aea0307c321badfc827040b`  
Origin work: `sha256:55e43e8e832ec966a738a4d1af3d9cf3d401a79760436cc6ca802a3d31ccf7bc`  
Source call sequence: `20`  
Hypothesis: The exact LCG recurrence X_0=42, X_{n+1}=(1103515245*X_n+12345) mod 2^31, die_n=1+(X_n mod 6) for n=1..10000 produces six face counts that can be determined only by simulation. The simulation returns the first ten (X_n, die_n) pairs for calibration and the six flat counts (count_1..count_6) plus total as the discriminating evidence. The fairness verdict is NOT baked into the program; the harness applies the two-standard-deviation tolerance to the returned counts.  
Discriminating purpose: Produce the exact face-count tallies and the first ten (X_n, die_n) calibration pairs so the harness can hand-verify the recurrence and apply the fairness tolerance to the counts. The program returns evidence, not a verdict.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

