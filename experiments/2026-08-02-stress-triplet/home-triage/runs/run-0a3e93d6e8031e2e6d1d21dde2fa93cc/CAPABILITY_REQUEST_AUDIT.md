# Capability Request Audit

Manifest: `2e8904aa31694454dafa755ece0bb563c34928a339b27784ab5d56af0f1e43a1`

Every entry below is reconstructed from typed Capability events and immutable records.

## blast_radius_ordering_sim_001

Proposal: `sha256:98cbf11e309d9758243f47f9c6c8c57de1fc10b96a4836a96d3a2ba1ea7524ad`  
Origin work: `sha256:1befdefc2300885417b317d9d3f80f00df94f5fc29e918436a8de82c3831329b`  
Source call sequence: `264`  
Hypothesis: The proposed ordering (1. _reset, 2. lease-mismatch, 3. unimported functions, 4. context receipt, 5. torn-tail, 6. census delta) minimizes expected total blast radius when guards die in random order, compared to alternative orderings. Blast radius is modeled as the number of downstream components affected by each guard's death.  
Discriminating purpose: Determine whether the blast-radius ordering (record corruption > security bypass > routing rot > recovery failure > partial coverage > observability discrepancy) is robust to permutations of the six gaps, or whether alternative orderings produce fewer expected corruptions under random guard-death scenarios.  
Lifecycle: proposed → validated → denied  
Terminal reason: `runner_profile_mismatch`

