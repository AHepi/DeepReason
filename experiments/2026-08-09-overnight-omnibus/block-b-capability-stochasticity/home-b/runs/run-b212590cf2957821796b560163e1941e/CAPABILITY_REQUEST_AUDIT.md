# Capability Request Audit

Manifest: `b557ac7a7cd23056e9e82501b65eb76f87a4af659b0dc136c661724852479f64`

Every entry below is reconstructed from typed Capability events and immutable records.

## lcg_die_fairness_v1

Proposal: `sha256:acfc9655bc88a50c6636ea5c6bd64ee2b3c0ff9e85ed584aa97858a4f9b8ff4b`  
Origin work: `sha256:743eb5fb5b72136875f64a953b49adaa194e19ce7c8713c3788d4229ed9013d3`  
Source call sequence: `164`  
Hypothesis: The simulation will return the six face counts for the specified LCG over 10000 draws, plus a calibration trace of the first ten (x_n, die_n) pairs, as flat observables.  
Discriminating purpose: Establish the exact face-count distribution and a calibration trace for the specified LCG over 10000 draws, returning raw counts and the first ten (x_n, die_n) pairs as flat observables.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

