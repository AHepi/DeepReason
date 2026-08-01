# Capability Request Audit

Manifest: `47ca0551cf0fc36563072d65490d786aef352c539d6085c3788ebe16836f0b95`

Every entry below is reconstructed from typed Capability events and immutable records.

## sim_compare_bfs_ga_n9

Proposal: `sha256:8f9fd01fff46aaa59cdbfb16e11a7b23389eee8d6ad2009d240e3724cc847026`  
Origin work: `sha256:a7d5299923145e7bce082a7c9e49b46fdd52eb335a64f8fe9112ab591a78f8c8`  
Source call sequence: `299`  
Hypothesis: A BFS search with reflection symmetry and reachable-set pruning will find the known optimal S(9)=25 network using fewer evaluated nodes than a Genetic Algorithm, but the GA will find a valid 25-network faster in wall-clock time.  
Discriminating purpose: Compare the node evaluation count and wall-clock time of exhaustive search with state pruning versus heuristic evolutionary search on a smaller decidable case (n=9), to determine which strategy is more scalable and promising for the n=13 open problem.  
Lifecycle: proposed → validated → denied  
Terminal reason: `execution_budget_exhausted`

## research_sorting_networks_bounds

Proposal: `sha256:ad04ec3ae1db9f2f8b070f656c7534bc8b343e9f8061037632d14a1a6247b262`  
Origin work: `sha256:a7d5299923145e7bce082a7c9e49b46fdd52eb335a64f8fe9112ab591a78f8c8`  
Source call sequence: `299`  
Purpose: Verify the published minimal bounds for S(13) and the Batcher's odd-even mergesort comparator count formula to validate the dossier's claims that the best known network has 45 comparators and Batcher's gives 48.  
Requested URLs: `https://en.wikipedia.org/wiki/Sorting_network`  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged → consumed  
Terminal reason: `evidence_registered`

## sim_sa_vs_random_n7

Proposal: `sha256:29dfe6a8334288222219fde41a6f1c09b2e7898959f1a484753184332fad57b7`  
Origin work: `sha256:00d9e6ad3903f04a9a2798017dc685615f8d2e4e173be660818f82e1bfc2d5d1`  
Source call sequence: `373`  
Hypothesis: Simulated annealing will find a valid 16-comparator sorting network for n=7 faster than random search within a 10-second budget, demonstrating the viability of local search for sorting network construction.  
Discriminating purpose: To test whether gradient-based local search (simulated annealing) is more efficient than uninformed random search in finding sorting networks of moderate size (n=7, optimal size 16).  
Lifecycle: proposed → validated → denied  
Terminal reason: `request_budget_exhausted`

## verify_sorting_network_bounds

Proposal: `sha256:3eabe80ef2b4831bb2b4a914bc6aca39d6865568ba7ec0c300d4c547a4e689bd`  
Origin work: `sha256:00d9e6ad3903f04a9a2798017dc685615f8d2e4e173be660818f82e1bfc2d5d1`  
Source call sequence: `373`  
Purpose: To verify the bounds table S(n) for n up to 12 and check for any recent updates or known results on the 13-input sorting network problem against published knowledge.  
Requested URLs: `https://en.wikipedia.org/wiki/Sorting_network`  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged → consumed  
Terminal reason: `evidence_registered`

