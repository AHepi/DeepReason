# Full-harness frontier: how a ~10B model runs the harness unaided

**Engine: deepseek-v4-pro, thinking OFF, on the FULL DeepReason harness** (scheduler, born-connected conjecture, argumentative critics, trial protocol with a pro-thinking-off + flash judge ensemble, reinstatement, capture detection). 701,384 tokens, 0 invariant violations, byte-replay clean. 221 conjectures → **30 accepted / 191 refuted** (86% refutation). Forbidden cases were rubric-adjudicated by the trial protocol, not Python-eval'd — so the predicate self-refutation that sank the mini round did not recur (conjecturer valid-JSON 0.98).

Accepted proposals are surviving conjectures — each states what would refute it and withstood live criticism; they are hypotheses, not validated fixes.


## R1 — nested-JSON stack failure (generation)  (4)

### `752c638b0410`  Split the single-pass generation into a nested two-step protocol: gamma1 drafts a flat skeleton with claim and forgiving placeholders; gamma2 expands placeholders into structured parts, with a schema-aware validator ensuring correctness at each step.

- **Mechanism:** In the harness loop, the conjecture call is replaced by a controlled sequence: (1) prompt gamma to output a flat JSON with only top-level fields and placeholder tokens for nested objects/arrays; (2) a deterministic expander replaces placeholders with further calls to gamma (constrained by a limited-depth prompt) or with static defaults. A JSON schema validator rejects any output that doesn't confo
- school: `school-1`  ·  problem: `pi-10b-impl`

### `f4160a135a55`  A two-stage generate-and-fill pipeline eliminates nesting complexity: the 10B model first generates a flat template with placeholders, then a second pass fills values.

- **Mechanism:** The harness conducts two consecutive LLM calls (the same 10B model). In Stage 1 (skeleton generation), the prompt instructs the model to output a simplified JSON skeleton with only keys and placeholder tokens (e.g., '<<CLAIM>>', '<<MECHANISM>>'), ensuring the structure is flat and braces are balanced because the model only emits keys and static punctuation. The harness validates and parses this sk
- school: `school-0`  ·  problem: `succ:27f513b2c7b8`

### `aac1bdd9ff36`  Enforce structural correctness during decoding via a deterministic pushdown automaton that constrains the LLM token sampling to only those tokens that maintain bracket balance and valid JSON nesting

- **Mechanism:** At each decoding step, the harness maintains a stack representing the JSON nesting context. The LLM's logits are masked: any token that would break bracket pairing (e.g., an unescaped quote, missing brace, or improper comma) is assigned -inf log-probability. The automaton transitions through a small set of states (object, array, key, value) using top-of-stack and next-token. This ensures the outpu
- school: `school-1`  ·  problem: `succ:21c33d69d52d`

### `2935a79911e8`  Integrate a bracket-balancing constrained decoder that terminates generation only when braces/brackets are balanced, preventing nesting errors.

- **Mechanism:** During generation, the model output is constrained by a pushdown automaton that tracks nesting depth. The harness uses a logit mask that sets probabilities of tokens causing imbalance to zero, ensuring a well-formed JSON skeleton is produced in a single pass.
- school: `school-1`  ·  problem: `succ:53956f4d4275`


## R2 — self-falsification burden (forbidden cases)  (3)

### `6c88ddab3c82`  Adversarial self-play training for forbidden case generation: fine-tune the 10B model on a synthetic dataset of conjecture-criticism exchanges where it must generate, then refute, its own claims, using a two-turn prompt. At inference, the model simulates both sides in one call by conditioning on a separator token.

- **Mechanism:** A two-turn fine-tuning: The model is trained on (prompt, conjecture) and then (conjecture, criticism) pairs, learning to anticipate its own mistakes. During inference, the harness appends a special token that triggers the model to generate the forbidden cases as part of its output, effectively making it a self-critic. This is a model-side change, not a harness change, so deterministic replay is pr
- school: `school-0`  ·  problem: `succ:7d2ff3395e80`

### `b6314a083f92`  Model the acceptance problem as a cooperative bargaining game among three stakeholders: the 'Quality
- school: `school-1`  ·  problem: `succ:20b4155eb5fe`

### `28c4ee09cb42`  Use multi-turn self-play within a single inference call, where the model sequentially generates a claim and then attacks it, refining it until a self-consistent candidate emerges.

- **Mechanism:** The harness orchestrates a loop: prompt the model to generate an initial candidate, then immediately prompt it (in the same context window) to critique that candidate by generating a forbidden case. The final output is the last refined claim and its defense. This iterative critique is performed without external models.
- school: `school-1`  ·  problem: `succ:53956f4d4275`


## R3 — predicate language (anchoring)  (1)

### `850b23f4716f`  Anchor inner predicate strings by requiring them to be valid Python lambda expressions that operate on a content string, enforced by a harness-side Python syntax checker (ast.parse) before accepting the skeleton.

- **Mechanism:** In the output contract, replace the free-text 'eval' field in forbidden cases with 'eval_lambda', a string that must be a valid Python lambda expression with exactly one argument (e.g., 'lambda x: len(x) > 10'). After gamma outputs the skeleton, the harness runs ast.parse on the string; if it raises SyntaxError, the skeleton is rejected and gamma is re-prompted with the error. This provides immedi
- school: `school-0`  ·  problem: `succ:7d2ff3395e80`


## Adjacent — acceptance-threshold designs (spawned successor problems)  (22)

### `a7d86125896b`  Replace the fixed hv threshold with a dynamic one that adjusts based on the distribution of heuristi
- school: `school-1`  ·  problem: `succ:ce2e3f5e8657`

### `448f372d9a5c`  Use an external verifier that re-reads the generated output and checks for internal logical consiste
- school: `school-1`  ·  problem: `succ:7021f05bf47b`

### `3a635a9caba2`  Treat the generation process as a dynamical system where heuristic value acts as a bifurcation param
- school: `school-1`  ·  problem: `succ:cbe59cb141e3`

### `f434721c239a`  Frame the selection of a heuristic value threshold as a game between the harness (minimizing worst-c
- school: `school-1`  ·  problem: `succ:cbe59cb141e3`

### `a9f2979cfc00`  Instead of a fixed hv threshold, compute a bootstrap confidence interval for the proportion of candi
- school: `school-1`  ·  problem: `succ:cbe59cb141e3`

### `526f7d1665b1`  Design an evolutionary algorithm where the heuristic value landscape is augmented with diversity and
- school: `school-1`  ·  problem: `succ:20b4155eb5fe`

### `57d42e719441`  Adopt an axiomatic framework where the acceptance of a candidate is governed by three non-negotiable
- school: `school-1`  ·  problem: `succ:20b4155eb5fe`

### `5701fbd101a5`  Model the harness's acceptance decision as a causal graph: candidate quality Q (latent) causes both 
- school: `school-1`  ·  problem: `succ:bd532f293850`

### `4ce606c076f9`  We replace the fixed hv threshold with a sense-disambiguated coherence score: each generated candida
- school: `school-1`  ·  problem: `succ:bd532f293850`

### `b6521f635257`  We recast candidate generation as WaveFunctionCollapse on a grid of narrative slots. The tileset com
- school: `school-1`  ·  problem: `succ:bd532f293850`

### `1ec6d131ac3a`  Construct a Bayesian Truth Serum (BTS) market where participants trade prediction tokens on the prob
- school: `school-1`  ·  problem: `succ:498f91dbb584`

### `590619f9e282`  Implement a Decentralized Arbitrariness Auction (DAA) where each candidate is minted as an NFT and s
- school: `school-1`  ·  problem: `succ:498f91dbb584`

### `ec933a3b7b7f`  Establish a Tiered Review Committee (TRC) within the harness: an algorithmic body with three escalat
- school: `school-1`  ·  problem: `succ:498f91dbb584`

### `600862726dc1`  Construct a causal graph over candidate features, generation parameters, and heuristic value, then l
- school: `school-1`  ·  problem: `succ:46c193508a49`

### `605d11f93876`  Model the generation process as a hierarchical Bayesian model where each candidate's latent quality 
- school: `school-1`  ·  problem: `succ:46c193508a49`

### `691a0801e5a2`  Apply L1-regularized logistic regression to select features from candidate-level metrics (e.g., cohe
- school: `school-1`  ·  problem: `succ:46c193508a49`

### `ca18181f615b`  Model the problem as a causal DAG where the heuristic value is a noisy mediator between the true qua
- school: `school-1`  ·  problem: `succ:a4cb0378047d`

### `3557c45ffd57`  Define a Lie group of symmetries (e.g., permutations of equivalent problem elements) and require tha
- school: `school-1`  ·  problem: `succ:a4cb0378047d`

### `8b3898b217b4`  Impose a hard cap on the total number of measurements (e.g., token generation steps, API calls, or c
- school: `school-1`  ·  problem: `succ:a4cb0378047d`

### `600ad9dc2ffb`  Introduce a stochastic acceptance rule where candidates are accepted with probability proportional t
- school: `school-1`  ·  problem: `succ:d1f286b65755`

### `9e28d156f0bb`  Replace the point estimate of candidate quality with a full Bayesian posterior over hv, using a nonp
- school: `school-1`  ·  problem: `succ:d1f286b65755`

### `7129da3f71dc`  Frame candidate selection as a multi-armed bandit where each possible hv threshold is an arm. Use an
- school: `school-1`  ·  problem: `succ:d1f286b65755`

