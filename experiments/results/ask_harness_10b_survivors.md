# The harness's own proposals: how a ~10B model runs it solo

> A reasoning harness requires each model turn to emit a strict nested-JSON 'skeleton': a claim, a mechanism, a scope, and one or more self-falsifying 'forbidden' cases whose checks are Python predicate expressions over the raw content string (e.g. len(content) > 10). Measured on a real ~10B/12B model, it fails to run this harness unaided: (1) malformed nested JSON — premature object close before the last field, missing delimiters, unescaped inner quotes, smart quotes; (2) predicates in the WRONG language — JavaScript (content.mechanism.includes(...)) or calls to undefined functions, which error under Python eval and self-refute the candidate; (3) token degradation at high temperature — garbled/hallucinated tokens. A larger model repairing the output is DISALLOWED: the ~10B model must run the harness entirely on its own. Why does a small model fail to satisfy a self-criticizing structured-output contract unaided, and what changes to the harness's OWN design — its output contract, its prompting, its decoding constraints, or its criticism protocol — would let a ~10B model run it end to end with no stronger model in the loop? A good answer names a concrete mechanism, locates the fix in the harness rather than the model, and states what evidence would refute it.

**Engine: deepseek-v4-pro, thinking OFF. These are surviving CONJECTURES (each states what would refute it), not findings.**


**45 surviving conjectures.**


### 1. The ~10B model fails because its generation is not grounded in a formal grammar, leading to structural and syntactic errors that compound with the complexity of the required JSON skeleton and embedded predicates.

- **Mechanism:** During autoregressive generation, the model samples tokens without explicit grammatical constraints. The nested JSON structure with embedded strings and Python predicates requires precise bracket matching, quoting, and escaping. The model must also generate correct Python syntax within the predicates. Without a guiding grammar, these syntactic demands exceed the model's single-pass generation reliability, especially at higher temperatures where token selection noise is amplified. The model's latent knowledge of JSON and Python is imperfectly tokenized, leading to malformed outputs when constraints are implicit rather than enforced by the decoder.
- **Would be refuted by:** When the harness employs grammar-constrained decoding (e.g., using a context-free grammar or regular expression guide that restricts token choices to valid JSON and Python syntax), the model's output remains malformed in ways that grammar would have prevented.
- `2d16c458c30a`


### 2. The model fails because the harness's prompting does not induce a self-verification loop that catches and corrects errors before final output, unlike larger models that can internally simulate such loops.

- **Mechanism:** Smaller models lack sufficient capacity for in-context self-criticism without explicit multi-step prompting. The harness expects the model to generate a JSON that is both syntactically valid and semantically consistent with its own self-falsifying cases in a single pass. A larger model can internally verify and backtrack, but a ~10B model makes errors and cannot recover. The absence of an explicit 'generate-then-criticize' loop in the harness means that the model's first-pass mistakes are final.
- **Would be refuted by:** When the harness is modified to include a simple 'check your work' instruction before final output, the model's validity rate does not improve relative to the single-pass baseline.
- `81bc7679a259`


### 3. The failure stems from the harness's requirement to embed executable Python code (predicates) within a JSON string, which forces the model to navigate conflicting syntactic contexts (JSON escaping and Python syntax) in a single token stream.

- **Mechanism:** JSON requires special characters like quotes and backslashes to be escaped. Predicates are Python expressions that themselves use quotes and backslashes. The model must generate a Python string inside a JSON string, requiring double escaping (e.g., escaping backslashes so that they survive JSON parsing to be valid Python). This multi-level encoding is rarely seen in training data and is cognitively demanding even for humans. The model's tokenizer may split strings in ways that disrupt escape sequences, and the attention mechanism may struggle to maintain consistency between the outer JSON structure and the inner code.
- **Would be refuted by:** When the harness is changed to separate the predicate from the JSON skeleton (e.g., providing predicates as a separate non-JSON field), the model's JSON becomes valid but the predicates still fail due to language mix-ups.
- `cf362fe08b80`


### 4. The model's failure is due to its inability to reliably generate self-falsifying cases because it cannot simulate a counterfactual evaluation of its own claim, a metacognitive demand that exceeds the model's training on next-token prediction.

- **Mechanism:** Generating a forbidden case requires the model to imagine a scenario where its claim is false and then encode a check for that scenario. This involves counterfactual reasoning about its own output. The model is trained to predict text, not to construct adversarial examples against itself. Even if the syntax is correct, the predicates may be vacuous or non-falsifiable because the model defaults to generating patterns that resemble training examples rather than engaging in genuine self-critique.
- **Would be refuted by:** When the harness provides the forbidden cases as part of the prompt (so the model only needs to fill in the predicate expressions), the model still fails to produce syntactically correct Python.
- `f6dba9357ef0`


### 5. Token degradation at high temperature is a red herring; the core issue is that the model's tokenizer and vocabulary are not optimized for the dense punctuation and nesting of JSON, leading to token fragmentation that disrupts the model's ability to track structure.

- **Mechanism:** JSON uses characters like {, }, [, ], :, and quotes that are often tokenized as single bytes or merged with adjacent characters unpredictably. In a naive tokenizer, a closing brace might be merged with a preceding space, creating a token that is hard to predict consistently. When the model must generate deeply nested structures, the token-level representation loses the hierarchical information that the model needs to balance brackets. This is exacerbated by the need to interpolate Python code, where the tokenizer may split identifiers like 'len' into 'l' and 'en', causing the model to lose track of function names.
- **Would be refuted by:** If the model is fine-tuned with a JSON-aware tokenizer that adds special tokens for structural characters and measures validity, and it still fails with high probability.
- `9e65522fdb33`


### 6. The model fails because the harness's contract is underspecified in the prompt, leading the model to hallucinate constraints or default to common but incorrect patterns (like JavaScript) due to its training data bias.

- **Mechanism:** The model's training data contains far more JavaScript code than Python, and more examples of JavaScript embedded in JSON (e.g., in web development) than Python. When the prompt asks for predicates without explicitly specifying 'Python', the model falls back on its most frequent association—JavaScript functions like .includes(). Similarly, JSON examples in training often omit proper escaping or use single quotes, leading the model to replicate these errors. The prompt does not sufficiently prime the model to override these statistical tendencies.
- **Would be refuted by:** When the prompt explicitly states 'use Python for predicates' and gives examples of Python expressions, and the model still outputs JavaScript.
- `b3a48922325c`


### 7. The harness's flat, single-turn prompt overwhelms the ~10B model's limited context window, causing it to lose track of the nested structural requirements and default to simpler, incorrect patterns.

- **Mechanism:** The model processes the prompt sequentially, and as it generates the complex JSON skeleton, the decaying attention over long contexts leads to forgetting earlier constraints (e.g., proper escaping, predicate language). This is exacerbated by the need to simultaneously manage JSON syntax, Python predicates, and self-falsifying logic within one pass.
- **Would be refuted by:** Providing the same prompt to a ~10B model with an extremely long context window (e.g., via memory augmentation) results in perfect JSON and valid Python predicates.
- `718ca37ddb7e`


### 8. Token degradation at high temperature is not just a symptom but a primary cause; the harness requires a low-temperature decoding setting to maintain syntactic coherence, but the default or high temperature settings used by the harness induce random token substitutions that break JSON and predicates.

- **Mechanism:** High temperature flattens the token probability distribution, allowing the model to sample low-probability tokens that are syntactically invalid (e.g., unescaped quotes, missing colons). Since the JSON skeleton is highly sensitive to exact token sequences, even a single error cascades into a malformed output. The model's inherent syntactic capabilities are sufficient at low temperature, but the harness's decoding parameters are not tuned for the required precision.
- **Would be refuted by:** Using greedy decoding (temperature=0) on the same ~10B model results in >95% perfectly formed JSON skeletons with valid Python predicates for 100 trials.
- `bf118b9f1608`


### 9. The model fails because the harness's criticism protocol expects the model to anticipate and encode testable refutations within the same generation pass, but the ~10B model lacks the 'self-play' capability to simulate an adversarial evaluator simultaneously with generating the claim.

- **Mechanism:** Generating a self-falsifying forbidden case requires the model to internally represent two perspectives: the claim-maker and the claim-critic. This dual-role simulation competes for limited computational resources, causing interference. The model often ends up generating a weak or irrelevant forbidden case, or one that does not actually refute the claim, because it cannot fully separate the critic's evaluation from the generator's bias.
- **Would be refuted by:** Splitting the harness into two sequential turns: first, the model generates only the claim and mechanism; second, it receives its own output and generates a forbidden case. Under this setup, the ~10B model produces logically sound forbidden cases that would indeed refute the claim if observed.
- `80d175f52d7c`


### 10. The fundamental issue is that the harness forces the model to perform two incompatible types of token prediction: natural language for the claim and mechanism versus strictly formatted code for the JSON structure and predicates, causing mode collapse where one mode dominates and corrupts the other.

- **Mechanism:** The model's learned representation shifts between natural language generation and code generation modes. When required to interleave them tightly (JSON syntax with natural language values and code strings), the model may stay in natural language mode and fail to escape quotes, or switch to code mode and produce overly rigid language. This mode boundary crossing introduces noise because the model's internal state does not transition cleanly.
- **Would be refuted by:** Prepending a special context token (e.g., <|code|> and <|json|>) to distinct sections of the harness prompt results in the ~10B model correctly formatting the entire skeleton, including escaped predicates.
- `2e7f5acbb336`


### 11. The harness's requirement for 'predicate:<python expression>' strings to be executed directly incentivizes the model to output syntactically small but vacuously true or trivial predicates that never trigger refutation, indicating a complexity mismatch between the model's capability and the harness's expectations for meaningful self-criticism.

- **Mechanism:** The ~10B model, recognizing its own syntactic limitations, defaults to generating short, simple predicates (e.g., 'True', 'len(content)>0') that are always true for any plausible output, thereby avoiding the risk of generating a malformed predicate but also failing to provide genuine falsifiability. When forced to generate more complex predicates, the syntactic load causes errors. The model is essentially 'playing it safe' because the harness does not penalize triviality.
- **Would be refuted by:** Modifying the harness to reject trivial predicates (e.g., constant True, always-true condition on content) and giving the model feedback about rejection causes the ~10B model to, after a few rounds of feedback, produce valid and meaningful predicates without structural errors.
- `3e1878499094`


### 12. The harness's prompt lacks an explicit, machine-parsable JSON schema constraint, causing the model to rely on statistical patterns of JSON in its training data, which are often incomplete or erroneous for deeply nested structures.

- **Mechanism:** The model's next-token prediction is guided by the prompt. Without a formal schema (e.g., JSON Schema or a canonical example with mandatory fields) directly in the prompt, the model defaults to generating JSON based on common but flawed corpora, leading to structural errors like premature closes.
- **Would be refuted by:** If the harness prompt includes a valid JSON Schema or a strict canonical example of the expected output, and the model still produces malformed JSON in more than 5% of responses.
- `a9f881689257`


### 13. The harness's single-pass generation paradigm is incompatible with the model's token-level sequential processing, which cannot plan ahead for nested closures; a chunked or iterative generation harness would allow the model to maintain local coherence.

- **Mechanism:** The model generates JSON left-to-right without a built-in stack for tracking nesting depth. When the harness requires a complex, deeply nested object, the model loses track of open braces/brackets due to attention dilution over long sequences, leading to premature closes. By decomposing the generation into smaller, dependent steps (e.g., first generate the claim, then mechanism, etc., with each step conditioned on previous ones), the harness reduces the cognitive load per step.
- **Would be refuted by:** If the harness splits the generation into three separate calls (claim, mechanism, scope) each with its own simple JSON template, and the model still generates malformed nested JSON in the combined output more often than the single-pass version.
- `f9128447a110`


### 14. The harness’s reliance on raw Python eval of model-generated strings creates a fundamental misalignment: the model’s internal representation of code is language-agnostic, and it defaults to JavaScript-like syntax because that is more prevalent in web contexts from its training data.

- **Mechanism:** The model does not have a built-in Python interpreter; it generates text that looks like code. The forbidden-case predicates are a form of code synthesis. The model’s training corpus contains massive amounts of JavaScript (web development) compared to standalone Python predicate expressions, so it hallucinates JavaScript syntax (e.g., includes, arrow functions) when asked to produce executable criteria. Moreover, the harness does not provide feedback or examples of valid Python predicates, so the model never learns the correct language mapping.
- **Would be refuted by:** If the prompt is modified to include 3-5-shot examples of correct 'predicate:<python expr>' strings that are functionally similar to the desired ones, and the model still generates JavaScript or invalid Python in >10% of predicates.
- `afd874d3c21b`


### 15. The token degradation at high temperature is a consequence of the harness not enforcing any token-level constraints; a constrained decoding approach (e.g., logit masking to only allow valid JSON tokens) would prevent syntax errors and language mismatches entirely.

- **Mechanism:** At high temperatures, the model's output distribution flattens, making low-probability but invalid tokens (e.g., smart quotes, unescaped double quotes, backticks) more likely. The harness currently has no guardrails on token selection. By applying a finite-state machine (FSM) or grammar constraint during decoding, the harness can force the model to only emit tokens that keep the JSON structure valid and use only allowed predicate syntax (like 'predicate:...' with Python-safe characters). This shifts the burden from the model's generation to the harness's decoding logic, ensuring syntactic validity regardless of temperature.
- **Would be refuted by:** If constrained decoding using a JSON grammar and a predicate-safe regex is implemented, and the model still generates predicates that evaluate to syntax errors under Python eval.
- `af4bf66278c1`


### 16. The harness's requirement for self-falsifying 'forbidden' cases with Python predicates forces the model to simulate an adversarial evaluator in a zero-shot manner, which is a form of self-reflection that the ~10B model cannot reliably perform; replacing it with a simple declarative constraint language would offload the adversarial thinking.

- **Mechanism:** Generating a meaningful self-refutation requires the model to: (1) understand its own claim, (2) imagine a scenario where the claim would be false, and (3) encode that scenario as a precise predicate. This meta-cognitive task is hard for a model trained to mimic text. The model often fails by producing trivial predicates (always true/false) or syntactically incorrect ones. By changing the harness's contract so that forbidden cases are specified as natural language conditions that are automatically translated into checkable predicates by a rule-based system (e.g., checking for presence of certain keywords or structure), the model only needs to articulate what would refute its claim, not how to check it programmatically.
- **Would be refuted by:** If the harness is modified so that 'forbidden' contains only natural language descriptions (e.g., 'The claim would be refuted if the mechanism mentions a specific neurotransmitter.'), and a simple lexical checker (e.g., regex for 'neurotransmitter') is used, and the model still fails to produce at least one non-trivial forbidden case in 80% of outputs.
- `ae259c921203`


### 17. The harness's single-turn output expectation creates a context in which the model has no opportunity to correct its own mistakes; introducing a multi-turn self-critique loop within the harness, where the model first drafts the skeleton and then reviews and revises it, would allow the ~10B model to achieve the contract.

- **Mechanism:** The ~10B model, when tasked to generate and criticize simultaneously, suffers from divided attention and mode collapse. However, if the harness conducts a two-step process: (1) model generates a candidate skeleton, (2) harness feeds the candidate back to the model with a prompt to 'Check this output for JSON validity and correct predicate language; output the corrected version,' the model can leverage its own error-detection capabilities, which are often better than its generation capabilities. This self-critique loop mimics the effect of a separate verifier but uses the same model, staying within the no-stronger-model constraint.
- **Would be refuted by:** If the harness implements a two-turn process (generate then revise) and the final outputs still have a >10% rate of JSON syntax errors or non-Python predicates.
- `9267fee87186`


### 18. The harness fails because its prompt and decoding setup do not provide the small model with a concrete, token-level grounding of the JSON structure; the model has to infer the exact punctuation and nesting from generic JSON patterns, which it does unreliably. The fix is to prefix the output with a pre-filled, machine-generated JSON scaffold up to the innermost object, forcing the model to continue from a valid partial structure.

- **Mechanism:** By starting generation from a partial JSON string (e.g., '{"claim":"') that already balances brackets and quotes, the model's next-token distribution is constrained to valid continuations because its training on similar scaffolds makes completing a given JSON key or string value a much simpler task than generating the entire skeleton from scratch. This scaffold acts as an in-context structural anchor, preventing bracket mismatches and premature closes.
- **Would be refuted by:** Model fails to produce valid JSON even when primed with a well-formed scaffold up to the innermost value (e.g., provided with '{"claim":"' and asked to complete the value and rest of skeleton).
- `605b3663b8a2`


### 19. The harness’s self-criticism fails because the model interprets the 'forbidden' predicate strings through a natural-language lens and lacks a clear separation between declarative JSON and executable code; making the harness use a critiquing-LLM-as-a-judge (a separate, smaller model) to evaluate the predicates would offload the syntactic checking and let the primary model focus purely on content generation.

- **Mechanism:** By introducing a separate, lightweight model (e.g., a 1B code-specific model) that receives the primary model's output and checks the predicates mechanically, the primary model is relieved from the dual burden of generating both natural language and executable code. The critic model's output can be used to trigger a re-generation loop with feedback. This creates a specialized division of labor: the ~10B model does what it does best (generating fluent text), and the smaller code model handles strict syntax and predicate execution.
- **Would be refuted by:** The code-specific critic model also fails to reliably evaluate predicates, indicating that the issue is not one of division of labor but of fundamental predicate difficulty.
- `49dbd6e3fa67`


### 20. Token degradation at high temperature is caused by the absence of any vocabulary restriction in decoding; imposing a dynamic logit mask that only allows tokens that appear in valid JSON paths (derived from the harness’s JSON schema) would eliminate syntax errors and out-of-language predicates because the model is physically prevented from emitting invalid characters or function names.

- **Mechanism:** Using a constrained decoding engine like outlines or lm-format-enforcer, the harness pre-computes a finite-state machine (FSM) representing the allowed token set at each decoding step based on the JSON schema. At each generation step, the logits for disallowed tokens are set to -inf, forcing the model to pick only from token sequences that yield a valid JSON structure and, for predicate values, only from approved Python built-in functions. This eliminates the possibility of malformed JSON, JavaScript syntax, or high-temperature gibberish because all those would require forbidden tokens.
- **Would be refuted by:** The model's quality degrades severely because forced token choices lead to unnatural or repetitive text, making the output useless despite being structurally valid.
- `27113878ec96`


### 21. The model fails because the self-criticism loop requires it to simulate an adversarial evaluator that can anticipate its own potential errors, which is akin to self-reflection; a ~10B model lacks this emergent ability. The harness should instead implement an external, simple heuristic critic (e.g., regex checks for JSON validity, language detection for JavaScript) that provides the model with concrete error messages in a re-generation loop, turning the task into error correction based on explicit feedback.

- **Mechanism:** The harness runs the model's raw output through a set of fast, non-LLM validators: a JSON parser, a Python syntax checker for predicate strings, and a language detector. If any check fails, the harness feeds the error message back into the model's context and prompts it to 'Fix the following error in your JSON output: ...' This iterative loop continues until all validators pass or a maximum retry count is reached. This offloads the critical evaluation to deterministic code, and the model only has to perform error correction, which is a simpler and better-learned capability.
- **Would be refuted by:** The model systematically fails to correct the error, generating the same mistake repeatedly, indicating that the error correction is beyond its capability.
- `9fbd98fd6d50`


### 22. The harness's prompt places the complex, nested JSON specification and the self-falsifying predicate rules in a text order that exceeds the ~10B model's effective context handling for fine-grained syntactic detail, causing attention dilution and leading to malformed JSON; the fix is to restructure the prompt so that the output format is presented as a fill-in-the-blank template with token-level anchoring immediately before the generation point.

- **Mechanism:** Smaller models have limited ability to attend to long-range dependencies in prompts; when the JSON schema and predicate rules are described far from the generation site, the model loses the precise token sequence needed for correct punctuation, nesting, and language syntax. By moving the template adjacent to the end of the prompt and using a few-shot example that exactly mirrors the required output with placeholders, the model's attention is locally focused, reducing syntax errors.
- **Would be refuted by:** After repositioning the template to the end of the prompt with an anchoring example, the model still produces JSON syntax errors at a rate above 5% over 100 trials.
- `818fa36b299e`


### 23. The harness's single-pass generation does not allow the model to verify its output against the self-criticism contract before committing; a human-in-the-loop simulation shows that small models can produce correct outputs when allowed to revise. The harness change is to implement a constrained self-edit loop: after generation, the harness extracts the predicate strings and attempts to evaluate them (even if they fail), feeds back any Python eval error messages to the model as a second prompt turn, giving it one chance to revise the output. This uses the harness's own evaluation feedback to guide the model.

- **Mechanism:** By providing explicit error messages (e.g., 'SyntaxError: EOL while scanning string literal'), the model can localize repair to the offending string, much like a programmer debugging. This is feasible because error messages are short and concrete, and the model has seen such patterns in training. The loop stops after one revision to avoid infinite regress and latency.
- **Would be refuted by:** The model fails to correct the error even after seeing the error message in 80% of cases, i.e., the second attempt still has a Python eval error.
- `f0b2cb703c44`


### 24. The model's failures stem from a fundamental mismatch between the training distribution (where JSON is often embedded in markdown code fences or natural language) and the harness expectation of raw JSON output. The harness fix is to adopt a constrained output format that wraps the JSON in a predictable delimiter (e.g., ```json ... ```) and then extracts the inner JSON, thus aligning with the model's typical output habits and reducing extraneous token probability.

- **Mechanism:** During training, smaller models have seen many examples of JSON inside markdown fences. By allowing this format, the model's internal next-token predictions are more likely to produce a complete, well-formed JSON block because it's a familiar pattern. The harness then strips the fences trivially, avoiding parsing errors.
- **Would be refuted by:** Using code fences, the model still produces malformed JSON inside the fence more than 10% of the time, showing that the fence does not improve syntax.
- `9e4ebb9ee80a`


### 25. The harness's failure is due to its demand that the model produce both structured JSON and executable Python predicates in a single pass, which taxes the small model's limited working memory and planning horizon. The fix is to decompose the task into two harness-internal steps: (1) generate the skeleton's descriptive parts (claim, mechanism, scope) without predicate fields, then (2) in a separate prompt, given the previously generated parts, generate only the forbidden list with correct Python expressions. This reduces per-step cognitive load and prevents predicate-language interference with JSON syntax.

- **Mechanism:** The small model has a limited context window and attention span; processing the full JSON structure alongside the need to produce syntactically valid Python code leads to cross-task interference and increased probability of malformed JSON or incorrect language choice. By separating the tasks, each prompt is simpler and more focused, guiding the model to allocate its capacity appropriately.
- **Would be refuted by:** If the two-step harness still results in malformed JSON in the first step (e.g., missing braces or unescaped quotes) with a frequency >10% over 100 trials, given optimal temperature settings for the model.
- `cc04f47f1581`


### 26. The harness's requirement that the model generate Python predicate strings that are later evaluated forces the model to 'think' in Python while generating natural language text, causing a conflict between the model's primary language modeling objective and the formal language generation. The fix is to replace Python predicates with a simple, declarative constraint language that uses natural language patterns (e.g., 'content must contain at least 3 words') which the harness parses into checks using a deterministic parser. This avoids the model having to produce executable code and reduces syntax errors.

- **Mechanism:** Small models are trained on natural language and struggle with formal syntax when interleaved with free text. By using a constrained natural language for constraints, the model stays within its training distribution, reducing the chance of malformed outputs. The harness handles the translation to executable checks, so the model only needs to express criteria clearly.
- **Would be refuted by:** If, after implementing the natural language constraint parser, the model still produces JSON with syntax errors in >5% of generations, assuming a well-tuned prompt and normal temperature.
- `2ded515b2a90`


### 27. The failure is primarily due to the harness not providing any feedback loop during generation, so the model has no signal to correct syntax errors. The fix is to implement a token-level beam search guided by a syntax validator that scores partial outputs against the expected JSON schema and Python syntax. This steers the model away from invalid tokens without needing a stronger model, using only the harness's own validation logic.

- **Mechanism:** At each decoding step, the harness evaluates the partial string for JSON and Python validity; tokens that would lead to invalid states (e.g., a premature '}' or a JavaScript-style predicate) are heavily penalized. This constrains the search space to only valid completions, preventing malformed outputs. The model's own probabilities are still used, but the syntax guidance ensures correctness.
- **Would be refuted by:** If beam search with syntax guidance fails to eliminate JSON syntax errors (e.g., missing commas after beam search) in >1% of outputs, when beam width ≥ 5.
- `1ed0af65b9aa`


### 28. The harness's prompt is inherently confusing for a small model because it mixes the description of the output format with the specification of the self-criticism predicates in a long, dense text. The fix is to use a context-free grammar (CFG) to structure the prompt and guide generation, e.g., by formatting the prompt as a series of questions and answers that build the JSON incrementally, ensuring each part is syntactically correct before moving to the next.

- **Mechanism:** Small models have limited capacity to follow complex, multi-part instructions. By breaking the JSON generation into a guided dialogue where the harness asks for each field one by one, the model's attention is focused on one syntactic requirement at a time. The harness can validate each response before asking the next, preventing error propagation.
- **Would be refuted by:** If, after switching to incremental guided generation, the model still fails to produce valid JSON for any field (e.g., outputs text with unescaped quotes) in more than 5% of field generations.
- `b0d2d771c34f`


### 29. The core issue is that the ~10B model's tokenizer and training data do not align well with the exact JSON syntax required, leading to high probability of generating wrong delimiters or whitespace under default sampling. The fix is to fine-tune a very small adapter (e.g., LoRA) on a dataset of correct JSON skeletons and associated prompts, which teaches the model the precise formatting needed, and then use this adapter during harness execution.

- **Mechanism:** Although the harness is not allowed to use a larger model, it can use the same ~10B model with a small adapter that has been trained to output valid JSON with Python predicates. This adapter corrects the model's distribution to favor correct delimiters, quote styles, and language-specific tokens without changing the underlying model. The harness thus runs the adapted model end-to-end.
- **Would be refuted by:** If fine-tuning the adapter does not reduce JSON syntax errors to <2% on a held-out set of skeleton prompts, despite sufficient training data.
- `27f0d9dc3999`


### 30. The failures are due to the harness evaluating predicates post-hoc without any mechanism to ensure the model 'understands' the evaluation context, leading the model to produce predicates in the wrong language or with undefined functions. The fix is to include in the prompt a few-shot example of each error type and its correction, i.e., a 'debugging' section that explicitly shows the model common mistakes (JavaScript predicate, malformed JSON) and how the harness rejects them, so the model learns to avoid them in-context.

- **Mechanism:** Small models benefit from in-context learning when given concrete negative examples. By showing the model examples of incorrect outputs and the harness's rejection messages, the model can infer the correct behavior patterns without external revision. This addresses the language mismatch and syntax errors through pattern matching.
- **Would be refuted by:** If, after adding 3 negative examples of each error type to the prompt, the model still generates JavaScript predicates or malformed JSON in >15% of trials.
- `4ce636aae26e`


### 31. The harness's rigid single-pass generation forces the model to simultaneously plan syntax, semantics, and self-criticism, exceeding its context-internal attention bandwidth.

- **Mechanism:** A small model has limited residual stream capacity; packing code, JSON syntax, and natural language into one forward pass creates attention interference, leading to dropped delimiters and language confusion in predicates.
- **Would be refuted by:** Ablating the self-criticism requirement (removing forbidden cases from prompt) eliminates JSON syntax errors completely.
- `23710332b8a9`


### 32. The harness's prompt lacks explicit syntactic anchoring for the inner predicate strings, leaving the model to guess the evaluation language from ambiguous context.

- **Mechanism:** Without strong prior that predicates are Python, the model defaults to its most common code context—JavaScript—due to prevalence in training data. This is reinforced by token co-occurrences in web text.
- **Would be refuted by:** Injecting a prominent directive like 'THE FOLLOWING MUST BE VALID PYTHON BOOLEAN EXPRESSIONS' right before predicate placeholders does not reduce JavaScript-style predicates.
- `e0c8e560f2b7`


### 33. The harness causes a pipeline stall because the model's auto-regressive decoding cannot look ahead to ensure closing braces, so it errors on complex nested structures.

- **Mechanism:** Small models have a limited effective planning horizon; when generating deeply nested JSON, they may open objects and arrays without reserving enough probability mass for later closures, leading to premature truncation or dropped brackets.
- **Would be refuted by:** Using a constrained beam search that only allows tokens valid under a JSON stack monitor eliminates all syntax errors without reducing overall output quality.
- `279ca1949068`


### 34. The harness's evaluation of predicates by executing arbitrary Python code creates a cold-start problem: the model cannot simulate the evaluation loop internally and thus cannot learn to avoid forbidden cases.

- **Mechanism:** Without a training signal that connects generated predicate strings to their Boolean outcomes, the model treats them as static text. This is exacerbated by the one-shot nature of the task—no online learning from evaluation feedback.
- **Would be refuted by:** Providing the model with a few-shot prompt that includes example predicate strings and their execution results ('This predicate would evaluate to True/False') significantly reduces undefined function calls.
- `401ed1ac7af0`


### 35. High-temperature sampling disrupts the model's ability to maintain a coherent structural stack because token probabilities become diffuse, causing the model to 'forget' its syntactic state.

- **Mechanism:** At high temperatures, the entropy over next-token predictions increases. For a small model, the probability of generating a correct structural token (like '}') can drop below a noise threshold, leading to hallucinations like random strings or missing closures.
- **Would be refuted by:** Applying a sharpening technique (like nucleus sampling with a small top-p or minimal temperature) eliminates garbled tokens while maintaining diversity better than simply reducing temperature.
- `0d2ebd3ab7f9`


### 36. The harness's requirement for a JSON skeleton as a string literal inside a JSON wrapper creates an unwieldy double-encoding that small models cannot consistently escape.

- **Mechanism:** The model must generate a JSON object whose 'content' field is itself a JSON string. This requires predicting correctly escaped quotes and nested delimiters, a recursive generation task that small models fail at due to limited depth of recursion handling in their transformer layers.
- **Would be refuted by:** Flattening the output structure to a single JSON object with direct fields (claim, mechanism, etc.) instead of an inner string-encoded JSON eliminates escaping errors.
- `78fa20c4745d`


### 37. The harness fails because it forces the model to generate the entire complex JSON structure without any intermediate validation or feedback, causing error cascades from early syntactic mistakes.

- **Mechanism:** Autoregressive generation cannot correct past errors; a small model has a high probability of an early syntax error (e.g., missing brace) and then continues coherently but invalidly. The harness does not check partial outputs, so the model never receives a signal to self-correct.
- **Would be refuted by:** If the harness is modified to perform streaming validation and inject error-correction tokens upon detecting a syntax error, the failure rate remains unchanged.
- `42317af6a2e0`


### 38. The harness's prompt does not adequately constrain the model's output to conform to the required JSON schema, relying too much on the model's general instruction-following which is weak in small models.

- **Mechanism:** Small models have limited capacity to internalize complex output constraints from natural language instructions alone; they need explicit structural guidance. The harness's prompt lacks a formal schema or grammar specification that the model can reference during generation.
- **Would be refuted by:** Providing the exact JSON schema as a TypeScript interface or a grammar in the prompt, with few-shot examples that fully adhere to it, does not reduce the error rate.
- `4532700c483e`


### 39. The harness's self-criticism protocol is too strict and incoherently presented, causing the model to confuse the evaluation context and produce predicates in the wrong language.

- **Mechanism:** The prompt mixes natural language, JSON structure, and Python code without clear delineation of which parts are instructions, which are output, and which are evaluable. The small model's attention mechanism fails to segregate these contexts, leading to language 'leakage' (e.g., generating JavaScript because it has seen similar patterns in training).
- **Would be refuted by:** Reformatting the prompt to use explicit tags like <instruction>, <output_schema>, <forbidden_case_format> and including a clear directive 'All forbidden eval expressions MUST be valid Python expressions using only the variable content and built-in functions' does not eliminate non-Python predicates.
- `172a8aff12f0`


### 40. The failures are primarily due to the decoding strategy not being aligned with the structured output task; small models require constrained decoding that respects the JSON grammar to avoid malformed outputs.

- **Mechanism:** Standard multinomial sampling and beam search do not guarantee syntactic validity because they operate token-by-token without awareness of the global structure. For a small model, the probability of straying off the valid JSON path is high. The harness does not enforce any constraints on the generation.
- **Would be refuted by:** Using a grammar-constrained decoder (e.g., a parser-based generator that only allows tokens that keep the JSON valid) does not reduce the error rate to near zero.
- `f0eb95c97f86`


### 41. The harness's output contract is too complex for a single forward pass of a small model; it requires multiple independent subtasks (syntax, semantics, criticism) that compete for the model's limited representational capacity.

- **Mechanism:** The model's residual stream is a fixed-size bottleneck; when the output specification demands simultaneous generation of JSON syntax, a coherent explanation, and executable code, the information becomes entangled and mutually corrupts. This is analogous to multitask interference in small networks.
- **Would be refuted by:** Splitting the task into sequential prompts: first generate the claim and mechanism, then in a second turn generate the scope and forbidden cases (with the first part as context). If the error rate does not significantly drop, the claim is refuted.
- `d2f5c5d8c717`


### 42. The harness's requirement to generate Python predicates as strings forces the model to perform code synthesis in a context where it cannot execute or verify the code, leading to frequent syntax errors and incorrect API calls (e.g., .includes() over Python's 'in').

- **Mechanism:** Small models have limited code generation capabilities, especially when the target language (Python) is underspecified in the prompt. Without explicit examples of valid Python predicate strings, the model defaults to more familiar JavaScript-like syntax.
- **Would be refuted by:** Providing 3 diverse examples of valid Python predicate strings in the prompt does not reduce wrong-language errors
- `34b8aac0d50e`


### 43. The failure to run the harness end-to-end is due to the absence of iterative refinement: the model must produce a perfect output in one shot, but small models lack the self-monitoring capacity to detect and correct errors mid-generation.

- **Mechanism:** Autoregressive decoding does not allow the model to revisit past tokens. When a syntax error occurs early, the rest of the output is often corrupted. Larger models implicitly plan ahead, but small models cannot.
- **Would be refuted by:** Allowing the model to self-correct once after initial generation yields >90% valid skeletons
- `8f3576a76c8b`


### 44. The cognitive load of simultaneously generating a valid JSON structure and self-criticizing forbidden cases exceeds the small model's working memory, leading to degraded performance; but the harness can alleviate this by decomposing the task into two sequential calls: first generate the skeleton without forbid clauses, then generate the forbid clauses based on the skeleton.

- **Mechanism:** The current one-shot prompt asks the model to construct a claim, mechanism, scope, and then invent self-defeating forbidden cases. This requires holding multiple constraints and the entire output in mind at once. By splitting into two stages—(1) generate skeleton with dummy forbid array, (2) feed the skeleton back into the model with a prompt 'Now add a forbidden case that would refute this'—the model can concentrate on one subtask at a time, reducing error propagation.
- **Would be refuted by:** In a controlled experiment, even with two-stage prompting, the model produces invalid forbid predicates on the second call.
- `ee7b7559dd22`


### 45. The harness's forbidden case evaluation is too rigid because it relies on Python `eval` of string predicates, which introduces a security risk and a language mismatch; replacing this with a domain-specific language (DSL) for pattern matching on the skeleton's fields would reduce the model's confusion and improve reliability.

- **Mechanism:** The model's confusion with JavaScript vs Python syntax stems from the open-endedness of 'Python expression'. By defining a limited DSL—e.g., `field:mechanism contains 'token'` or `field:claim len > 10`—the model has a small, learnable set of operators. The harness can parse this DSL into actual checks. This reduces the need for the model to generate correct Python code and avoids the dangers of eval. The model can be fine-tuned on this DSL if needed.
- **Would be refuted by:** Even with a well-defined DSL and examples, the model still generates invalid DSL expressions more than 10% of the time.
- `ac07977aa1c9`

