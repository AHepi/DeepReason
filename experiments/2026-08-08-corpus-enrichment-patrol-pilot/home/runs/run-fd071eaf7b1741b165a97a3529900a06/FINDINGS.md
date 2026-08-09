# Findings

## Question

What is 15% of 80?

## Positions the record accepts

89 positions stand formally accepted. Where they answer the same question differently they are unresolved rivals: the record deliberately preserves the disagreement rather than merging it.

- 15% of 80 equals 12. `[ee320832cb5d]`
- 15% of 80 equals 12, derived via decomposition into 10% and 5%. `[2b8805ad3d63]`
- 15% of 80 equals 12, by transposing the operands and computing 80% of 15. `[71a594c3289e]`
- 15% of 80 equals 12, via a unit-rate scaling mechanism. `[b02617095ed9]`
- 15% of 80 equals 12, derived via fraction reduction and multiplication. `[dc83b9f3381b]`
- 15% of 80 equals 12, assuming the percentage is a markup on a cost base that is unknown. `[e6ef9843d0c6]`
- SRC_002 injects an unsupported financial-context premise ('assuming the percentage is a markup on a cost base that is unknown') that the problem never states. The actual problem is a bare arithmetic question: 'What is 15% of 80?' It contains no cost base, no markup, and no reverse-percentage framing. Although the mechanism eventually collapses to the correct direct multiplication 0.15 * 80 = 12, the surrounding reasoning envelope obscures the covering principle: percent-of is simply multiplication by the decimal equivalent. The extraneous hypothetical branches violate the substance of the task… `[70a0815d2bff]`
- 15% of 80 equals 12. `[7a0083969b9c]`
- 15% of 80 equals 12, by transposing the operands and computing 80% of 15. `[fec24b57f4ec]`
- 15% of 80 equals 12, derived via decomposition into 10% and 5%. `[86cf5b9502fe]`
- 15% of 80 equals 12, via a unit-rate scaling mechanism. `[610102a961b9]`
- 15% of 80 equals 12, via proportional reduction to a simpler base. `[2ca5575df308]`
- 15% of 80 equals 12, by converting the percentage to a fraction and simplifying. `[9c7f0f7481d7]`
- 15% of 80 equals 12, derived from the covering principle that multiplication is commutative, making 15% of 80 strictly equal to 80% of 15. `[7e20e854a484]`
- 15% of 80 equals 12, derived via structural decomposition into 10% and 5% components. `[2bc193878a87]`
- 15% of 80 equals 12, derived by scaling the unit fraction 1% to the target 15%. `[78f068f2f3ff]`
- 15% of 80 equals 12, derived via the complementary principle: computing what is left after removing 85%. `[a1a1385a5cb1]`
- 15% of 80 equals 1200, derived by computing the raw product of the percentage points and the base without division by 100. `[93c2e46e48f0]`
- 15% of 80 equals 120, derived by an off-by-one order of magnitude error in decimal shifting. `[5bace5661033]`
- The target asserts a claim that is mathematically false: it states '15% of 80 equals 120' and provides a causal mechanism that operates on a malformed input (1.5 instead of 0.15). Under the demand for a causal mechanism, a mechanism built on an explicitly incorrect decimal conversion does not constitute a valid causal pathway to the solution; it is a documented error, not a reasoned derivation. The claim fails the problem standard of computing 15% of 80, which is 12, not 120. `[1eee503ca079]`
- The claim states that 15% of 80 equals 1200, which is factually incorrect for the stated problem. A percentage represents a proportion per hundred, so 15% means 15/100. The correct computation is (15/100) * 80 = 0.15 * 80 = 12. By omitting the division by 100, the target yields a result 100x too large. A simple counterexample confirms the error: if the problem asked for 100% of 80, the target's raw-product method would give 100 * 80 = 8000 instead of the correct 80, demonstrating that the percentage must be normalized. `[fdfe37bdce3e]`
- 15% of 80 equals 12. `[98a2f4abea74]`
- 15% of 80 equals 12, derived via decomposition into 10% and 5%. `[9b005b2ad4cb]`
- 15% of 80 equals 12, by transposing the operands and computing 80% of 15. `[420a618510b3]`
- 15% of 80 equals 12, via a unit-rate scaling mechanism. `[0bb04ede1aba]`
- 15% of 80 equals 11, assuming a continuous compounding or a truncated step-function distribution. `[f4ce70aa8df1]`
- 15% of 80 equals 0.001875, derived by misapplying the percentage as a recursive division operator. `[f2a5960614c6]`
- The target's proposed causal mechanism substitutes a non-standard recursive division operator for the correct operation. The term 'of' in '15% of 80' maps to multiplication (0.15 * 80), not division. By applying the operator as 15 / (100 * 80), the mechanism inverts the base relationship and yields 0.001875, which is not 15% of 80. The counterconditions themselves concede this flaw by noting the result fails if 'of' is correctly defined as multiplication. `[82d061d5f189]`
- The target claims 15% of 80 equals 11 under truncation, but the stated truncation arithmetic is internally inconsistent: if 5% of 80 is truncated from 4.0 (not 3.5) the sum is 8+4=12; and if the intent is 15% computed in one step, 0.15*80=12 exactly with no truncation possible. The counterexample fails because the problem is pure real-number arithmetic, and no step decomposition producing 3.5 from 5% of 80 is arithmetically valid. `[2e350e6deebd]`
- SRC_011 contradicts SRC_010: SRC_011 claims 15% of 80 equals 11 via continuous compounding or a truncated step-function, which directly negates SRC_010's claim that the result is 12 via linear unit-rate scaling. The contradiction turns on whether the scaling mechanism is linear or non-linear. This is refuted if a linear percentage scaling mechanism is the only admissible interpretation of '15% of 80' under the standard parts-per-hundred definition, making SRC_011's non-linear model inapplicable. `[5bf375f39933]`
- SRC_012 contradicts SRC_006: SRC_012 claims 15% of 80 equals 0.001875 by recursively dividing the base by the percentage factor, whereas SRC_006 derives 12 by scaling the unit fraction 1% by 15. The contradiction arises from a recursive operator misapplication vs. a standard linear scaling mechanism. This is refuted if percentage 'of' is strictly defined as multiplication by the rate (0.15 × 80), which eliminates the recursive division interpretation and invalidates SRC_012's result. `[73f98d5859a6]`
- SRC_009 shares mechanism with SRC_003: SRC_009 computes 80% of 15 by transposing the operands, and SRC_003 explicitly notes that 80 is 0.8 of 100 so 15 × 0.8 = 12. Both artifacts exploit the commutativity of multiplication (a × b% = b × a%) as the underlying mechanism, even though they apply it to different intermediate steps. This is refuted if the multiplication a × p/100 is not commutative in a% of b, or if the commutative rearrangement fails to produce equivalent results under the standard percentage definition. `[a460dc435684]`
- SRC_008 reduces to SRC_005: SRC_008 decomposes 15% into 10% + 5% (8 + 4 = 12), which is a specific instance of the proportional scaling family. SRC_005 scales the base by a factor of 8, computes 15% of 10 = 1.5, and scales back. Both are reduction-to-simpler-base strategies, but SRC_008's additive split is a special case of proportional decomposition. This is refuted if the 10% + 5% decomposition requires an independent distributive mechanism not subsumed by the proportional scaling principle, making SRC_008 non-reducible to SRC_005's approach. `[a4764bc47d7a]`
- SRC_007 abstracts SRC_004, SRC_006, and SRC_010: SRC_007 claims '15% of 80 equals 12' as a bare result, while SRC_004, SRC_006, and SRC_010 each provide a specific unit-rate scaling mechanism. SRC_007 is the abstract claim that the unit-rate scaling derivations instantiate. This is refuted if SRC_007's statement carries a mechanism or constraint that is not captured by the unit-rate scaling derivations, meaning it is not a pure abstraction of them. `[78ceec4ae873]`
- SRC_011 is compatible with SRC_003 in a restricted domain: SRC_011's non-linear compounding model yields 11 instead of 12, while SRC_003's linear unit-rate model yields 12. They are compatible only if the domain admits both linear and non-linear percentage interpretations, with the linear model serving as the limiting case. This is refuted if the standard definition of '15% of' unambiguously mandates linear scaling (as SRC_003's counterconditions require), making the non-linear model inadmissible rather than a coexisting alternative. `[c793dcc79dd6]`
- The 'refuted if' condition names only a linear mechanism and admissibility of interpretation, but never specifies a causal pathway connecting the endpoints; the relation is characterized as a direct 'negation' of results without identifying the mechanism that produces the contradiction (e.g., conflicting operator precedence or distinct algebraic routes). A negated output equality is a summary of endpoints, not a substantive causal relation. `[224b9389255c]`
- The target asserts a contradiction between 'recursive operator misapplication' and 'standard linear scaling,' but the 'refuted if' clause only reiterates that 'of' is defined as multiplication, offering no mechanism that causally explains how the recursive division route arises from or is excluded by the multiplication route. It states results differ and names a definitional override, which is a summary-level comparison rather than a causal dependence. `[7a4a50b0e751]`
- The target claims SRC_008 reduces to SRC_005 via 'specific instance of proportional scaling family,' but the causal mechanism is absent: it never demonstrates that the additive 10%+5% split is generated by the same proportional-base-and-scale-back mechanism SRC_005 uses. The 'refuted if' points to an independent distributive mechanism but the main relation relies on categorical family membership, not a derivation pathway. Without showing how SRC_005's scale-by-8/scale-back causally produces the additive decomposition, the relation is a label, not a mechanism. `[033459cd9c58]`
- SRC_001 names 'shared mechanism' but the substantive link it identifies — commutativity of multiplication — is an elementary algebraic property of every multiplication, not a mechanism specific to the neighbourhood of 0bb04ede1aba. Asserting that two artifacts both rely on commutativity does not connect 0bb04ede1aba to its neighbourhood in any substantive sense; it is a vacuous, universally-true observation that would 'relate' any pair of multiplication-based artifacts. The covering principle here is trivial: it provides no dependence, reduction, shared mechanism, or integration that actually … `[b1bd45e3fd12]`
- 15% of 80 equals 12, derived via decimal multiplication: 0.15 × 80 = 12. `[08d5e4611db2]`
- 15% of 80 equals 12, derived by decomposing the percentage into 10% and 5%. `[cc1eeb6934a0]`
- 15% of 80 equals 12, derived by transposing the operands and computing 80% of 15. `[91c3622dbc55]`
- 15% of 80 equals 12, derived via fraction reduction: 15/100 × 80 = 3/20 × 80 = 240/20 = 12. `[13b3c7a5b32c]`
- 15% of 80 equals 12, derived via a unit-rate scaling mechanism where 1% of 80 equals 0.8. `[971b83a35b7c]`
- 15% of 80 equals 12, derived by taking three-fifths of 20% of 80. `[e13162e78d2d]`
- 15% of 80 equals 12. `[b8d5b7a4b385]`
- 15% of 80 equals 12, derived via decomposition into 10% and 5%. `[b3bf009d8157]`
- 15% of 80 equals 12, by transposing the operands and computing 80% of 15. `[ed7b23c338ae]`
- 15% of 80 equals 12, via converting the percentage to a fraction and simplifying. `[b8c9bf88ed9f]`
- 15% of 80 equals 12, derived by computing 15% of 100 and scaling down by a factor of 5. `[fa6da335160b]`
- 15% of 80 equals 1200, treating the operation as raw multiplication without division by 100. `[a9c770c7bca5]`
- The target answers '15% of 80 equals 1200,' which is arithmetically incorrect. The problem asks for 15% of 80; the correct value is 12, obtained by (15/100)*80. By treating '%' as a raw multiplier and omitting division by 100, the claim produces a value 100x too large and fails the problem as stated. `[d66ad4111636]`
- 15% of 80 equals 12, derived by exploiting the commutativity of multiplication: 0.15 × 80 = 80 × 0.15 = 80 × 15% = 12. `[41331e43a298]`
- 15% of 80 equals 12, derived via structural decomposition into 10% and 5% components. `[cc2793576e5a]`
- 15% of 80 equals 12, derived by computing the complementary remainder after removing 85%. `[1f5d4d826066]`
- 15% of 80 equals 1200, derived by computing the raw product of the percentage points and the base without division by 100. `[7f81acc627bb]`
- 15% of 80 equals 120, derived by an off-by-one order of magnitude error in decimal shifting. `[7b5ce18cbd47]`
- If the percentage is compounded over multiple iterations rather than applied as a single linear factor, the result diverges from 12. `[76ed774d096c]`
- 15% of 80 equals 12, derived from the covering principle that multiplication is commutative, making 15% of 80 strictly equal to 80% of 15. `[9f3db756a3e6]`
- 15% of 80 equals 12, derived via structural decomposition into 10% and 5% components. `[6c2681995f19]`
- 15% of 80 equals 12, derived by scaling the unit fraction 1% to the target 15%. `[5062c2745f1e]`
- 15% of 80 equals 12, derived via the complementary principle: computing what is left after removing 85%. `[168983086579]`
- 15% of 80 equals 1200, derived by computing the raw product of the percentage points and the base without division by 100. `[493b6f2cf155]`
- 15% of 80 equals 120, derived by an off-by-one order of magnitude error in decimal shifting. `[154b31122c63]`
- SRC_001 asserts a claim of '15% of 80 equals 120' with a mechanism that is explicitly an off-by-one decimal-shift error (1.5 × 80). The problem asks for the correct value of 15% of 80; presenting a knowingly wrong answer as the claim is a substantive failure, not a valid counterfactual, since the final claim does not satisfy the problem statement. `[8f6e79d26c45]`
- The target's claim asserts '15% of 80 equals 1200', which is mathematically false. The counterconditions merely note the failure mode without correcting it, and the mechanism describes the erroneous raw-integer multiplication (15×80=1200) as its derivation. A counterexample to the claimed result is straightforward. `[e04ee056f163]`
- The target answers 1200, which is mathematically wrong for the stated problem. The claim itself concedes the mechanism omits the required normalization step (division by 100), and the listed countercondition identifies the standard definition as requiring this step. Since the countercondition falsifies the target's own approach, the target fails the problem as stated. `[5a4e491b32f3]`
- The target answers 120, which exceeds the base 80 and therefore cannot be 15% of 80. The target's own countercondition identifies that 120 exceeds the base, which is impossible for a percentage < 100%, directly falsifying its own claim. `[d9ab8a11ff2f]`
- 15% of 80 equals 12, by decomposing the percentage into 10% + 5% and scaling the base linearly. `[3990a58419bd]`
- 15% of 80 equals 12, derived by computing 15% of 100 (which is 15) and then scaling that result down by the factor 80/100, yielding 15 × 0.8 = 12. `[7dbaa721195e]`
- 15% of 80 equals 12 because the problem implicitly requires a single linear application of a percentage as a scalar multiplication (0.15 × 80), and any non-linear interpretation is admissible only if a time or iteration dimension is specified. `[58da546bcfce]`
- 15% of 80 equals 12, derived via a base-ten shift and unit-scaling mechanism: 15% is defined as 15 per 100, establishing a scalar ratio of 15/100 = 0.15, which scales the base 80 by linear multiplication. `[b03dbc25189c]`
- 15% of 80 equals 12, derived by translating the percentage into a decimal fraction (0.15) and applying linear scalar multiplication: 0.15 × 80 = 12. `[a76c6a4bd499]`
- 15% of 80 equals 12, derived by interpreting 15% as the dimensional scalar 0.15 and operating on the extensive quantity 80, anchoring the computation in a foundational case of linear scaling that abstracts over specific operand identities. `[18fce0b1fd83]`
- SRC_004 reduces to SRC_003 because computing 15% of 100 (yielding 15) and then scaling by 80/100 is arithmetically equivalent to finding the unit rate 1% of 80 (0.8) and multiplying by 15; both are factored forms of the associative product 15 × (80/100). This is refuted if SRC_004's normalization to a canonical base of 100 is a domain requirement (e.g., tax brackets) rather than an arithmetic shortcut, making the intermediate value 15 a semantically necessary quantity. `[c5a0daad1371]`
- SRC_002 depends on SRC_005 because the direct decimal multiplication 0.15 × 80 inherits its validity from the base-ten definition of percentage as 15/100 = 0.15. SRC_002 is a single-step compression of SRC_005's explicit base-ten decomposition (10/100 + 5/100 of 80). This is refuted if the multiplication 0.15 × 80 relies on a floating-point approximation rather than the exact rational fraction 15/100, violating SRC_005's dimensionless scalar definition. `[0bf16aa0e386]`
- SRC_004 contradicts SRC_003 in causal mechanism if the canonical base of 100 is a semantic prerequisite: SRC_004 anchors the operation to 100 and scales down, while SRC_003 anchors directly to 80. This is refuted if both methods are proven to be strictly commutative and associative re-factorizations of the same linear equation with no domain-specific anchoring constraints. `[5bb463d45409]`
- SRC_005 abstracts SRC_001, SRC_002, SRC_003, and SRC_004 by providing the general principle that percentage is a dimensionless scalar applied via linear multiplication. The specific decomposition routes (unit-rate, direct decimal, canonical normalization) are concrete instantiations of this abstraction. This is refuted if any specific route (e.g., SRC_004's intermediate value of 15) carries domain information that is lost in the abstract scalar multiplication, making the abstraction invalid for that domain. `[85bf82beba01]`
- SRC_002 reduces to SRC_004 because direct decimal multiplication (0.15 × 80) implicitly embeds the canonical normalization to 100 (where 15% of 100 = 15) and the scaling factor (80/100 = 0.8). This is refuted if 0.15 is treated as a primitive irrational coefficient independent of the base-ten percentage definition, severing the dependency on the normalization step. `[02a510052907]`
- nu: verdict of relation-form@578e42df713e on b90593c47c717bd7ef8becf56de755fd3e112add3d03a2560c9c42d6b139f447 is sound and relevant `[2c098a54ce58]`
- critic: relation-form@578e42df713e failed on b90593c47c71 `[3d2b3b4e0858]`
- The proposed reduction conflates arithmetic coincidence with a genuine reduction. SRC_002 (direct decimal multiplication) does not 'reduce to' SRC_004 merely because the normalization to 100 is algebraically implicit in the decimal 0.15. A reduction relation requires SRC_002 to depend on SRC_004's intermediate computational step (the canonical normalization to 100). However, 0.15 × 80 is evaluated directly as a dimensionless scalar multiplication without ever passing through SRC_004's base-100 framework; the factor 0.15 is a pre-derived constant, not an in-route reduction of SRC_004's procedur… `[cc6703e38288]`
- 15% of 80 equals 12, derived via decimal multiplication (0.15 × 80 = 12). `[41678294d00d]`
- 15% of 80 equals 12, by decomposition into 10% and 5%. `[aded7f6767e9]`
- 15% of 80 equals 12, by transposing the operands and computing 80% of 15. `[ddef9a6f2070]`
- 15% of 80 equals 12, derived via fraction reduction and multiplication. `[1cec55f673a5]`
- 15% of 80 equals 12, via a unit-rate scaling mechanism. `[d451f5a31319]`
- 15% of 80 equals 12, assuming the percentage is a markup on a cost base that is unknown. `[e6889437b965]`
- SRC_002 injects an unstated 'markup' business context and an 'unknown cost base' that the problem never requests. The stated problem asks for 15% of 80; by adding the assumption that 80 is a final selling price inclusive of a 15% markup, SRC_002 makes the answer depend on a reverse-engineered base (~69.57) rather than the direct calculation, contradicting the plain proportional reading required by the problem. `[130ca31bec8f]`

## Positions the record refuted

- SRC_001 and SRC_003 share mechanism: they both isolate a unit rate (1% = 0.15, then 1% of 80 = 0.8) and scale it linearly by 15 to reach 12. This is refuted if the unit rate '0.15' in SRC_001 is interpreted as a fixed coefficient rather than a derived quantity per 100, breaking the conceptual symmetry with SRC_003's explicit derivation of 0.8. `[b90593c47c71]`

---
Every statement above is derived from the append-only run record; nothing was generated by a model for this report. Accepted does not mean true — it means the position survived recorded criticism so far, and the run remains continuable.
