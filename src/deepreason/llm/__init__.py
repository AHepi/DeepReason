"""LLM adapter (spec §9).

The LLM is a bounded pure function: pack -> schema-validated JSON (§0).
Roles: conjecturer (Verbalized Sampling, §11.6), argumentative_critic,
defender, variator (mu, mu_struct), judge (trial protocol only), summarizer,
synthesizer, embedder (non-generator model; raws logged).

Cross-family rules: judge on >=2 endpoints from different families; foreign-
reviewer rule routes critics across schools (farthest recent embedding
centroid, tiebreak by school id).
"""
