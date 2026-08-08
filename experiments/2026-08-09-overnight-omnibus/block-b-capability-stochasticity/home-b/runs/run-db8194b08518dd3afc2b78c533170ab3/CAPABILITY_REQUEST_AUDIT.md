# Capability Request Audit

Manifest: `278c8a616ef68467e0b807af59901428b92bb7714c380b68474e4eed74229b16`

Every entry below is reconstructed from typed Capability events and immutable records.

## lcg_die_fairness_seed7

Proposal: `sha256:cce21e11219257d704092c6a5fcba3a81af641dbf52078ca5099f7eacc51c101`  
Origin work: `sha256:d7e27dc49a9de9c42a4ae1f1a75c90da487265501a1adde1ae193004f16f2160`  
Source call sequence: `20`  
Hypothesis: The ANSI C LCG with X_0=42, X_(n+1) = (1103515245*X_n + 12345) mod 2^31, and die_n = 1 + (X_n mod 6) produces a fair distribution over 10000 draws, with all face counts within 2 standard deviations of 10000/6.  
Discriminating purpose: Determine whether the exact face counts from the specified LCG sequence fall within the 2-sigma tolerance band of the uniform expectation, and provide the calibration trace to verify the implementation against the specification.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

## lcg_die_fairness_run_001

Proposal: `sha256:27f36bee2338d80fc9cff35dc54ebf38d15a6896117d1cc90acd2a7aacefe1b6`  
Origin work: `sha256:ab5ea64f2c43edbf34710e1bd871540323af70ff24e47f84c81f9ceffe24451a`  
Source call sequence: `77`  
Hypothesis: The exact LCG recurrence specified produces a sequence of die faces whose tally over 10000 draws can be mechanically checked for fairness. The simulation acts as a pure data-extraction mechanism: it calculates the first ten trace values and the full 10000-draw face counts, leaving the 2-sigma tolerance application to the adjudicating harness.  
Discriminating purpose: To extract the exact (X_n, die_n) calibration trace and the exact final face counts (count_1 through count_6) for the specified LCG, providing the raw numerical evidence required to check fairness without asserting a verdict.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

## lcg_die_fairness_seed7

Proposal: `sha256:e59fd953f5ecadfe33e3ad250dd07336a6068ab175daf33c9f82cc81a30896a3`  
Origin work: `sha256:2c323e6fc8015cf28fa01eceef6f97e4fac916c374812398c8aeb66e0f28267a`  
Source call sequence: `103`  
Hypothesis: The generator produces a FAIR distribution: all six face counts at n=10000 fall within two standard deviations of the uniform expectation 10000/6.  
Discriminating purpose: Produce the exact six face counts for the specified LCG at n=10000 so the harness can adjudicate the two-sigma fairness tolerance, and return a calibration trace so the implementation can be checked by hand against the specification.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

