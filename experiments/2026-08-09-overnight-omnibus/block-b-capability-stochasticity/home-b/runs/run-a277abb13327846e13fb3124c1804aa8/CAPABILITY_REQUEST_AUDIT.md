# Capability Request Audit

Manifest: `20fe929ca22f02f5cdabddb40697fd74052441346e555fef53890cba6a07d90f`

Every entry below is reconstructed from typed Capability events and immutable records.

## sim-lcg-die-fairness-seed6

Proposal: `sha256:598b26055045cfb18a74b8c15af5ab6691c0a9b822ed5ec6b0e94afa164ac28d`  
Origin work: `sha256:081a7785fb8f195c9b501972bc7896502cdedfc061083331908031ad68458479`  
Source call sequence: `20`  
Hypothesis: The LCG produces a fair distribution over six faces after 10000 draws, where fair means every face count falls within two standard deviations of the uniform expectation. The simulation will return the exact counts and a calibration trace of the first ten pairs.  
Discriminating purpose: To establish the exact face-count distribution for the specified LCG at n=10000 and provide a calibration trace, allowing the criticism cycle to apply the fairness tolerance to the empirical counts.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

## sim_lcg_die_fairness_seed6

Proposal: `sha256:aac65a345c84a6c4f24d95768495069e5d9e1f70a53c04dfb8dd04bd3d575f99`  
Origin work: `sha256:ceb2a574815dabf3af374e7e4f99df208dab624dec2cb48ff2dde09ba138943c`  
Source call sequence: `86`  
Hypothesis: The LCG X_(n+1) = (1103515245 * X_n + 12345) mod 2^31, die_n = 1 + (X_n mod 6), seeded at X_0 = 42, is UNFAIR over 10000 draws: at least one face count falls outside two standard deviations of the uniform expectation 1666.7 ± 52.7. The LCG's state space (mod 2^31, coprime to 6) creates a systematic bias.  
Discriminating purpose: Establish the exact six face counts for the specified LCG over 10000 draws, plus a calibration trace of the first ten (X_n, die_n) pairs, to determine whether the generator is fair or unfair by the problem's numerical criterion.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

