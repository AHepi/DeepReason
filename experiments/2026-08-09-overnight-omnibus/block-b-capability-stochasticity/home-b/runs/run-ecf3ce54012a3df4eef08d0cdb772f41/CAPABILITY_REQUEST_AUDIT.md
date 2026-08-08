# Capability Request Audit

Manifest: `9ce3d3442c08bb817542ad3a30e275d4f5aa014a39ecf36a408e7bad0d37eeea`

Every entry below is reconstructed from typed Capability events and immutable records.

## sim_lcg_die_fairness_836f39

Proposal: `sha256:7c092d0db6f243e0b1d54d914a2a797cec11b66b0d99535e7c7befe85490805f`  
Origin work: `sha256:0956a32988917fffd4e79686eeabda8ec3d7a1eac8645ada35cd2c509f34f1b8`  
Source call sequence: `20`  
Hypothesis: The specified LCG produces face counts that fall within two standard deviations of the uniform expectation (10000/6) over 10000 draws, i.e., the generator is 'fair' by the problem's definition.  
Discriminating purpose: Establish the exact six face counts and the calibration trace for the specified LCG to adjudicate the fairness claim, returning the discriminating quantities (counts and trace) rather than a boolean verdict.  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged  
Terminal reason: `bounded_result_context_packaged`

## lcg_die_fairness_sim_001

Proposal: `sha256:95746bafae2d621a03528e393017d8b27e395b145dbb3285d0c396e4939699a0`  
Origin work: `sha256:13f511c4a2e71e2998407e4248a2d9981adc8c2d73e3559932cc3ed7cd1ee862`  
Source call sequence: `72`  
Hypothesis: The LCG X_(n+1)=(1103515245*X_n+12345) mod 2^31 with X_0=42, mapped to die faces via 1+(X_n mod 6), produces face counts over n=1..10000 that either fall within or outside the 2-sigma fairness window (1613.9 to 1719.4). The simulation will return the exact counts and a calibration trace of the first 10 pairs for verification.  
Discriminating purpose: Obtain the exact face counts for the specified LCG over 10000 draws and a calibration trace of the first 10 (X_n, die_n) pairs to verify the implementation before trusting the tally as evidence.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

## lcg_dice_fairness_seed8

Proposal: `sha256:a0e218f827592f3506da955417e18756342b4956153ef44e4505f36380f6255e`  
Origin work: `sha256:4c04bd8bf4b3300d478506e0f67a49eee62ce1211395ce3f3f57503f5854c04d`  
Source call sequence: `137`  
Hypothesis: The LCG modulo bias favors faces 1 and 2 (residues 0 and 1) because 2^31 is not divisible by 6. This bias accumulates over 10000 draws and pushes at least one count outside the 2-sigma window [1592.0, 1741.4].  
Discriminating purpose: Compute the exact six face counts for the LCG X_(n+1) = (1103515245 * X_n + 12345) mod 2^31, die_n = 1 + (X_n mod 6) over n=1..10000 with X_0=42, plus a calibration trace of the first ten (X_n, die_n) pairs. The counts will be checked against the fairness criterion: every count must fall within [1592.0, 1741.4] (2 standard deviations of the uniform expectation 1666.67).  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

## lcg_exact_tally_and_trace_001

Proposal: `sha256:0e93b693f345e45d6faeb7f94dceb2852538009b6da0ac1186d12dac3d81180e`  
Origin work: `sha256:e0e636243689f4049fd398e0139bf89541728a19058a6410ab51c775b2ed47ce`  
Source call sequence: `213`  
Hypothesis: The LCG X_{n+1} = (1103515245 * X_n + 12345) mod 2^31 with X_0 = 42, mapped via die_n = 1 + (X_n mod 6), produces a distribution over 10000 draws where all face counts fall within two standard deviations of the uniform expectation (1666.67 ± 74.54).  
Discriminating purpose: Establish the exact face counts for the specified LCG over 10000 draws, provide a calibration trace of the first ten pairs, and measure the distribution against the 2-sigma fairness criterion.  
Lifecycle: proposed  
Terminal reason: `transaction_semantic_proposal`

