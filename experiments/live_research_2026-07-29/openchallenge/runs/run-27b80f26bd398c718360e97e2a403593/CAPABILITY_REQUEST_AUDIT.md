# Capability Request Audit

Manifest: `91bb8195d1c16beaa011e920ffcf1aa34db43bdec935bb28c7fc7b0b421dc889`

Every entry below is reconstructed from typed Capability events and immutable records.

## sim_2x2_diagonal_W_refutation

Proposal: `sha256:480ef6d2abfa46076131681d0f9a444fd553832d479c4a840901192c52402f83`  
Origin work: `sha256:680c6a0dba037695b4ec7a1c405d24579fbab221637e0e25a9f785c19f0bad95`  
Source call sequence: `159`  
Hypothesis: Restricting the W coefficient matrices to diagonal matrices makes it impossible to represent the 2x2 matrix multiplication tensor, regardless of the rank allowed.  
Discriminating purpose: Calibrate the tensor rank verifier by accepting Strassen's rank-7 2x2 algorithm and rejecting a corrupted copy, then discriminate the structural lemma by demonstrating mathematically within the script that diagonal W matrices yield zero for off-diagonal C entries, refuting the lemma.  
Lifecycle: proposed → validated → denied  
Terminal reason: `invalid_model_program`

## fetch_tensor_rank_bounds

Proposal: `sha256:5ccb64119294ad129205382718e8f025ae33c1e94cc12acecc8cc6c110c7d221`  
Origin work: `sha256:680c6a0dba037695b4ec7a1c405d24579fbab221637e0e25a9f785c19f0bad95`  
Source call sequence: `159`  
Purpose: Verify the bounds for 3x3 matrix multiplication tensor rank (R(3,3,3)) stated in the dossier against published knowledge, specifically checking if the best known upper bound is 23 (Laderman 1976) and the best lower bound is 19.  
Requested URLs: `https://en.wikipedia.org/wiki/Matrix_multiplication_algorithm`  
Lifecycle: proposed → validated → granted → compiled → dispatched → succeeded → result_packaged → consumed  
Terminal reason: `evidence_registered`

