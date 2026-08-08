# Capability Request Audit

Manifest: `182afd07b7808ff26c2f601bd11eff3d39d5cc963616f68d2ca5136a1c6992c7`

Every entry below is reconstructed from typed Capability events and immutable records.

## lcg_die_counts_10000_v1

Proposal: `sha256:89c2c15b736d2dec9b2a619b8f417389083e5fa125380ebed0b2492ad455bd03`  
Origin work: `sha256:c36a6ca6612cb2f7e58996f64b0f77d41d0fee32eee720ea226e877dffad4303`  
Source call sequence: `20`  
Hypothesis: The LCG produces a distribution where count_1 is inflated by the structural modular bias (2^31 mod 6 = 2) and falls outside the two-standard-deviation tolerance [1614, 1720], rendering it NOT FAIR.  
Discriminating purpose: Establish the exact face counts (count_1 through count_6) and total for the specified LCG over 10000 draws, and return a calibration trace of the first 10 (X_n, die_n) pairs so the recurrence can be verified by hand.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

## sim_lcg_fairness_v1

Proposal: `sha256:eeffbe32b7f4104da9f26bd5da39a16f0edd4da77352de62ab0a461f7145dad9`  
Origin work: `sha256:d038ca3c09efdc6e0323a580ed76185a8ee0a7f175b491aede7b11f78937bfec`  
Source call sequence: `83`  
Hypothesis: The LCG produces an unfair distribution where count_6 equals 1724, exceeding the upper 2-sigma tolerance of 1719.  
Discriminating purpose: Compute the exact face counts for the specified LCG over 10000 draws to determine if any count falls outside the 2-sigma fairness window, while providing a 10-step calibration trace to verify the recurrence and mapping.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

