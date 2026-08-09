# Capability Request Audit

Manifest: `f89be1d5c8d2caf8a634aea4a162d47ec6067f79691a43948fb6c1be4dd3bc82`

Every entry below is reconstructed from typed Capability events and immutable records.

## lcg_face_counts_seed9_v1

Proposal: `sha256:df8feaf3c9c990791480385510fd7f87b62af6db58c6e5fa5413609d18ca8036`  
Origin work: `sha256:83814e2677332c5648d981d67c4492d3d6bb8a38026a53c8e6a1c273ad93119c`  
Source call sequence: `20`  
Hypothesis: The exact face-count distribution of the LCG sequence X_0=42, X_(n+1) = (1103515245 * X_n + 12345) mod 2^31, die_n = 1 + (X_n mod 6), for n=1..10000, can be obtained by running the exact integer recurrence in Python and tallying. The calibration trace (first ten X_n, die_n pairs) should match hand computation.  
Discriminating purpose: Return the exact six face counts and a ten-step calibration trace for the specified LCG over 10000 draws so the fairness verdict can be adjudicated externally from raw data.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

## seed9_lcg_exact_counts_and_calibration

Proposal: `sha256:cc734735ecc4c2d233e8852d577312c7b041a17718385d8d6ee0e01ce90cf491`  
Origin work: `sha256:fd358eb25611fc715e12329c8b99c1c9e3f2fcb038057c034b7c787e1e3bde84`  
Source call sequence: `49`  
Hypothesis: Implementing the exact recurrence X_0=42, X_{n+1}=(1103515245*X_n+12345) mod 2^31, die_n=1+(X_n mod 6) for n=1..10000 yields six face counts. The calibration trace (first 10 pairs) can be checked by hand, and the full tally will be the only durable evidence for or against the fairness claim.  
Discriminating purpose: Produce the exact six face counts (count_1..count_6) and a ten-pair calibration trace (x1, die1, ..., x10, die10) so that the recurrence and face-mapping can be checked by hand, and the fairness verdict can be applied by the criticism cycle rather than baked in.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

## lcg_die_fairness_sim_v1

Proposal: `sha256:b102c495d853ab85c0109adbcd8ec5d9efe8b125b496e624e549b50703597859`  
Origin work: `sha256:b282b2ad5737ad92b72a36e03325ef91330a74e07aa94f562f8965f310acbc19`  
Source call sequence: `103`  
Hypothesis: The LCG with X_0=42, a=1103515245, c=12345, mod 2^31, mapped to die faces via 1 + (X_n mod 6), produces a catastrophically unfair distribution: only faces 1 and 4 appear, each approximately 5000 times, all other faces zero.  
Discriminating purpose: Determine the exact face-count distribution of the specified LCG over 10000 draws to decide whether it meets the fairness criterion. Return the six flat counts plus total, and a calibration trace of the first ten (X_n, die_n) pairs for hand-checking the recurrence and face-mapping.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

