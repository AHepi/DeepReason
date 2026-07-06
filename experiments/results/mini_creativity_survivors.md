# What MiniReason says about LLM creativity


## pi-novelty-decay

> A strong LLM asked to generate many candidate explanations for one problem produces a diverse first batch, but its novelty decays over a sustained run: later candidates cluster, paraphrase earlier ones, and re-propose ideas already set aside. Why does the novelty of an LLM conjecture generator collapse under sustained self-conditioning on its own recent output, even at high sampling temperature?

**27 surviving conjectures.**


### 1. The LLM's novelty decays because its output distribution narrows due to auto-correlation in repeated self-conditioning.

- **Mechanism:** Each generation conditions on recent outputs, creating a positive feedback loop that concentrates probability mass on high-likelihood sequences, reducing exploration even at high temperature.
- **Forbidden (what would refute it):** External diverse prompts are interspersed every few steps, breaking the autocorrelation.
- `887d60182455`


### 2. Attention sink causes the model to focus excessively on a few recent tokens, ignoring broader context and leading to repetitive outputs.

- **Mechanism:** During sustained generation, the self-attention mechanism increasingly attends to high-frequency tokens (like 'the' or 'and'), creating an 'attention sink' that limits diversity.
- **Forbidden (what would refute it):** Attention is explicitly masked to prevent sink (e.g., via attention dropout or sink avoidance techniques).
- `6cc55758d789`


### 3. The model falls back on common templated patterns from its training data when faced with uncertainty, leading to repetitive conjectures.

- **Mechanism:** Training data contains many examples of causal explanations that follow a template (e.g., 'This is because...'), and the model's sampling defaults to these templates under high entropy.
- **Forbidden (what would refute it):** The training data is filtered to remove templated causal explanations.
- `139b1ff03fef`


### 4. Information bottleneck through repeated sampling discards fine-grained distinctions, causing convergence to a few high-probability regions.

- **Mechanism:** Each generation step passes through a bottleneck (e.g., logit normalization, top-k sampling) that erases low-probability nuances; cumulative effect reduces the effective number of distinct ideas.
- **Forbidden (what would refute it):** Generation uses pure greedy decoding (temperature=0) and novelty still decays.
- `f7723f6bb0fb`


### 5. The model exhausts a finite set of latent concepts relevant to the task; after each is expressed, remaining concepts become less likely.

- **Mechanism:** The model's embedding space for the task has limited distinct regions. Once a concept is sampled, its probability decreases due to repetition penalty, but the model cannot invent truly new concepts beyond its latent manifold.
- **Forbidden (what would refute it):** New concepts are introduced into the context from an external source (e.g., knowledge base).
- `5d4fb96053e0`


### 6. Self-reinforcing feedback loop: a small initial fluctuation is amplified by conditioning, causing the model to lock into a narrow trajectory.

- **Mechanism:** Early random variations in generated text shift the context distribution; subsequent generations condition on that shifted distribution, further magnifying the variation, leading to a cascade toward a single mode.
- **Forbidden (what would refute it):** The context window is reset to a fixed initial prompt after each generation (no self-conditioning).
- `d658cfa1f5e2`


### 7. The novelty collapse occurs because the model's sampling temperature does not effectively control diversity under self-conditioning; the conditional distribution becomes peaked even at high temperature due to the softmax function's sensitivity to logit differences.

- **Mechanism:** As the model generates, the logits for certain tokens become much larger than others due to conditioning on recent text, causing the softmax to produce near-deterministic choices despite high temperature.
- **Forbidden (what would refute it):** If an LLM with temperature=1.0 and no conditioning still shows decay over sustained runs
- `6733c96cd9ae`


### 8. The novelty collapse is an artifact of the beam search or top-k/top-p sampling parameters being held constant; dynamic adjustment could maintain diversity.

- **Mechanism:** Fixed sampling parameters do not adapt to the changing entropy of the conditional distribution; early on, high entropy allows diversity, but as entropy drops, the same parameters become over-restrictive.
- **Forbidden (what would refute it):** If an adaptive temperature schedule (e.g., increasing temperature over time) prevents decay
- `2cfaf49cfd06`


### 9. The LLM's novelty decay is a consequence of the 'mode collapse' in generative models, where the model overfits to its own synthetic outputs, similar to GAN training instability.

- **Mechanism:** Each generation produces a sample from the model's distribution; when that sample is used as input for the next generation, it biases the distribution towards that sample, creating a positive feedback loop that collapses to a single mode.
- **Forbidden (what would refute it):** If the model can recover diversity after being reset with a random seed
- `443e54abc080`


### 10. The collapse arises from the model's implicit Bayesian inference over latent topics; as more candidates are generated, the posterior over topics sharpens, reducing diversity.

- **Mechanism:** The LLM implicitly maintains a distribution over high-level topics or hypotheses. Each generated candidate provides evidence that updates the posterior, concentrating probability on a few topics and making alternative topics less likely to be sampled.
- **Forbidden (what would refute it):** If the entropy of the model's output distribution remains high after many generations (e.g., measured by perplexity or token diversity), then Bayesian sharpening is not occurring.
- `92cb700e096c`


### 11. The collapse stems from the model's decoder-only architecture and the causal masking, which forces each new token to depend on all previous tokens in a strictly sequential manner, causing error accumulation and convergence to a single mode.

- **Mechanism:** In a causal decoder, each token generation is conditioned on the entire preceding context. Small biases or noise at early steps propagate and amplify; eventually, the conditional distribution becomes dominated by the most frequent patterns, leading to a loss of diversity. This is akin to the 'mode collapse' in RNNs.
- **Forbidden (what would refute it):** If an encoder-decoder model with bidirectional attention on input does not show similar collapse, the architecture is the cause.
- `b0dd862a38d9`


### 12. The model's self-attention causes token-level embeddings to converge as context repeats, reducing semantic diversity.

- **Mechanism:** Each generation conditions on previous outputs; self-attention layers mix token representations, and repeated exposure to similar tokens drives their embeddings toward a common centroid, collapsing the effective latent space.
- **Forbidden (what would refute it):** Measuring token embedding cosine similarity across generations shows no monotonic increase.
- `326ba73c7971`


### 13. The model's prior over sequences is sharply peaked due to training data biases; self-conditioning merely exposes this prior, causing rapid convergence.

- **Mechanism:** Training on natural language with heavy repetition (e.g., common phrases) creates a prior that assigns high probability to a small set of patterns. Each generation draws from this prior, and conditioning on previous draws reinforces the same modes.
- **Forbidden (what would refute it):** Finetuning on a diverse corpus with perplexity constraints eliminates the collapse.
- `c9dbed97d8f3`


### 14. The collapse is due to the model's internal representation of 'current set of hypotheses' shrinking as it implicitly summarizes its own output, losing track of rejected ideas.

- **Mechanism:** The LLM maintains an implicit working memory of generated concepts; each new token update compresses this memory, and non-recent concepts are forgotten, narrowing the search.
- **Forbidden (what would refute it):** Explicitly storing and re-injecting all past candidates prevents collapse.
- `97581131b4ff`


### 15. The softmax function's exponentiation amplifies small logit differences, turning a mild preference into a dominant mode under repeated sampling.

- **Mechanism:** Even at high temperature, softmax(x/T) for large logit differences causes the largest logit to dominate. Repeated sampling magnifies any initial imbalance, creating a positive feedback loop.
- **Forbidden (what would refute it):** Using a different output transformation (e.g., sigmoid) eliminates the collapse.
- `a17526b452a6`


### 16. The model's token-level representation loses resolution after many steps because the embedding space is finite; new outputs become indistinguishable from earlier ones.

- **Mechanism:** Each output token is mapped to an embedding; after many steps, the accumulated embeddings occupy a limited region, so future choices are effectively forced to repeat.
- **Forbidden (what would refute it):** Projecting embeddings into a higher-dimensional space after each step prevents collapse.
- `547f45c61eb5`


### 17. The collapse arises from the model's implicit reinforcement of its own outputs, where each generated candidate is treated as a positive example, narrowing the search distribution.

- **Mechanism:** The LLM, when prompted to generate explanations, interprets its own earlier outputs as evidence of good hypotheses. This creates a positive feedback loop: the model assigns higher probability to variations of already generated ideas, reducing exploration.
- **Forbidden (what would refute it):** If an explicit diversity reward or penalty for repetition is added to the generation process, the collapse should be reduced or prevented.
- `0b2284f36dc5`


### 18. The model's self-conditioning on its own output acts as a positive feedback loop on hidden activations, causing the model to converge to a fixed point attractor in its embedding space.

- **Mechanism:** Each generation modifies the model's hidden states (key-value cache) by attending to its own output. In a deterministic transformer, repeated conditioning on similar inputs drives the hidden states toward a stable fixed point. High temperature adds noise, but the attractor basin remains; eventually, noise is insufficient to escape, and outputs become identical or near-identical.
- **Forbidden (what would refute it):** If the model is forced to reset its KV cache after each generation, collapse still occurs, showing it is not due to cache attractors.
- `8ba0d0c983a1`


### 19. The collapse is due to the model's limited context window: as the prompt (list of earlier candidates) grows, the model attends only to recent outputs, losing sight of the overall diversity goal.

- **Mechanism:** The LLM's self-conditioning uses its own previous output as context. But the context window is limited (e.g., 4096 tokens). After a few hundred candidates, the early diverse ones are no longer visible, so the model's generation is conditioned only on a recent cluster of similar outputs, leading to mode collapse.
- **Forbidden (what would refute it):** If the model is provided with a running summary that includes all earlier diverse outputs as part of the prompt, but collapse still occurs, then context limitation is not the primary cause.
- `2a6b135c6a8f`


### 20. The collapse is an artifact of the tokenization: high-frequency tokens dominate and force semantic convergence.

- **Mechanism:** Tokenization breaks vocabulary into subwords; high-frequency tokens appear in many contexts. When generating, the model repeatedly uses these tokens because they have high probability. Even at high temperature, the number of distinct rare tokens is limited, and the model's output quickly consists almost entirely of common tokens, which converge to similar meanings.
- **Forbidden (what would refute it):** If the model is switched to a character-level tokenizer (or byte-level) and collapse still occurs, then tokenization is not the cause.
- `df6be4903919`


### 21. The model's sampling algorithm (e.g., top-p or top-k) interacts with high temperature to create a 'stochastic trap': the set of possible next tokens is effectively reduced, leading to repetition.

- **Mechanism:** High temperature flattens the distribution, but when combined with top-p (nucleus) sampling, the number of tokens considered is still limited. At each step, only a small subset of tokens have non-negligible probability after top-p filtering. Over many steps, the model repeatedly samples from this small set, causing outputs to converge.
- **Forbidden (what would refute it):** If the model uses pure temperature sampling (no top-p or top-k) and collapse still occurs, then the stochastic trap is not the cause.
- `f882ce0fc40a`


### 22. The collapse is not inevitable: if the prompt is periodically refreshed with diverse seed ideas, novelty is maintained.

- **Mechanism:** Injecting random external prompts resets the model's context, breaking the self-conditioning loop and forcing exploration of new regions.
- **Forbidden (what would refute it):** An experiment shows that even with periodic resets, novelty still decays over a sustained run.
- `213cb818767a`


### 23. The model is fine-tuned to maximize likelihood of the next token, not to maximize novelty, so it naturally repeats.

- **Mechanism:** Under the maximum likelihood objective, the model assigns higher probability to continuations that are typical in the training distribution, penalizing surprising tokens.
- **Forbidden (what would refute it):** A model fine-tuned with a reward for diversity still shows collapse.
- `f41d030f598a`


### 24. Layer normalization in deep transformers causes the representation to lose variance over repeated generative steps, leading to identical outputs.

- **Mechanism:** Layer norm scales activations; after many steps, the mean and variance of activations converge, reducing distinctiveness.
- **Forbidden (what would refute it):** A shallow transformer does not show such collapse.
- `1dc0b8c70a03`


### 25. During inference, the model's CUDA kernel caching or beam search implementation favors high-frequency token sequences, reducing novelty.

- **Mechanism:** The inference engine's caching mechanism speeds up repeated sequences, making them more likely to be generated due to faster execution or lower latency.
- **Forbidden (what would refute it):** Novelty collapse persists even with random optimization flags and no caching.
- `844881280993`


### 26. Strong prior from training data pulls generations towards typical sequences, even with high temperature.

- **Mechanism:** The LLM is trained on a corpus with long-tailed distribution. Under self-conditioning, the model assigns high probability to common sequences, and even with high temperature, cumulative probability of a diverse chain is low, so the model defaults to repeating common patterns.
- **Forbidden (what would refute it):** If the model is trained on a corpus with uniform n-gram distribution and still collapses, the prior hypothesis is false.
- `48efbed95ec3`


### 27. Hidden state trajectory converges to an attractor under self-conditioning, reducing diversity.

- **Mechanism:** The model is a deterministic function of its input and previous state. When conditioning on its own output, the sequence of hidden states becomes a dynamical system with a stable attractor, leading to repeated generation of similar outputs.
- **Forbidden (what would refute it):** If the model's hidden state is perturbed with random noise at each step and diversity persists, the attractor claim is weakened.
- `6616454a54dd`

