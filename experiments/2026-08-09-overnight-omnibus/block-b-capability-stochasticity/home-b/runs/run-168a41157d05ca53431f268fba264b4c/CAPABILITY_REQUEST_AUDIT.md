# Capability Request Audit

Manifest: `3f3fcc9f172e4b2bbaeb29ab2ad2badd81f243f14427e197dd1c5c0b903f61ba`

Every entry below is reconstructed from typed Capability events and immutable records.

## lcg_die_fairness_n10000

Proposal: `sha256:0b04a6756ff4e91af0686141eaf0784138f3a0e0fe4f7608dd69b898253894c3`  
Origin work: `sha256:7550a346473e910bc84021edaeb31159a75d864884cb6412c6f6108a9dbd2cad`  
Source call sequence: `20`  
Hypothesis: The specified LCG (X_0=42, X_(n+1) = (1103515245 * X_n + 12345) mod 2^31, die_n = 1 + (X_n mod 6)) produces a distribution over six faces at N=10000 where every face count falls within two standard deviations of the uniform expectation (1666.67 ± 129.47).  
Discriminating purpose: Produce the exact six face counts (count_1 through count_6) and total for the specified LCG over 10000 draws, plus the first 10 (X_n, die_n) pairs for calibration, so the fairness claim can be evaluated against the 2-sigma tolerance.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

## lcg_die_fairness_001

Proposal: `sha256:ccc1e5f34fcf20eb72b45d8b0cf79463cfab4ef58281eb53cc6ccd2fff64e74d`  
Origin work: `sha256:ddff7bb68a2fcc3a16bec4846cfe694577d34719139e68268d0805eff7df9860`  
Source call sequence: `94`  
Hypothesis: The LCG X_(n+1) = (1103515245 * X_n + 12345) mod 2^31 with X_0 = 42, mapped to die faces via 1 + (X_n mod 6) for n=1..10000, produces face counts that may or may not fall within 2 standard deviations of the uniform expectation (1666.67 ± 52.38). The simulation returns exact counts and a calibration trace.  
Discriminating purpose: Determine the exact face counts from the specified LCG to adjudicate the fairness claim, with a calibration trace to verify implementation correctness.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

