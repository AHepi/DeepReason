# Capability Request Audit

Manifest: `a975fb78817a69b46dc3855ab362440fc8043764524e7deceee07d2412a241a0`

Every entry below is reconstructed from typed Capability events and immutable records.

## sim_lcg_die_fairness_seed10

Proposal: `sha256:5f45da17da4dbae756b5bb09cf98c8c37312960cff81e22dfdc279bc7f3d0dc2`  
Origin work: `sha256:9864ad0a1e8e902199f57aedf7536fe61d45dc57fdc9fe6b0c656dd6f194f74b`  
Source call sequence: `20`  
Hypothesis: The LCG X_0=42; X_(n+1)=(1103515245*X_n+12345) mod 2^31; die_n=1+(X_n mod 6) produces a specific deterministic count vector over n=1..10000 that may or may not fall within two standard deviations of the uniform expectation (1666.67 +/- 2*sqrt(10000*5/36)). The simulation returns the exact counts plus a calibration trace.  
Discriminating purpose: Determine the exact face-count distribution of the specified LCG over 10000 draws and calibrate the implementation by emitting the first ten (X_n, die_n) pairs for hand-verification, so the fairness question can be adjudicated by applying the 2-sigma tolerance to the returned counts rather than by narrative assertion.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

