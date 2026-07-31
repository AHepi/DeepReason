# Thinking off: the run did not happen, and why is the result

Intended: rerun the coin-canonicity question with (a) the reviewer seat
enabled, (b) the simulation contract shown to critics, (c) glm-5.2's
thinking switched off — and compare against
`run-c5f901f38208e862f4ce2fe60a26e551`.

Outcome: **no reasoning run exists.** `reason_rc=1`, no run id. The
harness refused, correctly, because glm-5.2 with thinking off failed
production qualification.

## What happened, in typed order

    setup_rc=0            profile written with reasoning: none
                          profile_digest e800ce9c...  (SPEC F6 predicted this)
    qualify_rc=0          qualify_seconds=352   tier: shallow
                          qualification_state: ready_shallow
    reason_rc=1           reason_seconds=1      run_id=  state=

`reason` refuses on a shallow tier: the shallow tier's next action is
`reason --shallow`, the reduced engine, which carries no capability
channels and so could not have exercised (a) or (b) anyway.

## The failing pair, twice

    DOCTOR_REPORT_PAIR_UNQUALIFIED at /pairs/14/qualified

    battery 1   pair[14] scratch.link.compact.v1  (synthesizer)
                first_pass 11/20  eventual 11/20  repairs 18   -> UNQUALIFIED
    battery 2   pair[14] scratch.link.compact.v1  (synthesizer)
                first_pass  9/20  eventual  9/20  repairs 22   -> UNQUALIFIED
                pair[15] scratch.link.minimal.v1 (synthesizer) -> ALSO UNQUALIFIED

Two independent full batteries, ~350 s each, second worse than the
first. Not flake.

Its siblings in the same battery, same model, same call:

    scratch.cluster-guide.compact.v1   20/20   qualified
    scratch.cluster-guide.minimal.v1   20/20   qualified
    conjecturer.turn.v6                        qualified
    batch-critic.v2                            qualified
    groundingverdictwirev1.direct.v1           qualified   <- the new seat

## The contrast, and the honest confound

The thinking-ON battery this repository already holds
(`live_coin_canonicity_2026-07-31/home/qualification-cache/f9dc3af3...json`,
the one the coin run reused) records **15 pairs, 0 unqualified — full
tier**. Same model, same contracts, thinking left on.

So on the evidence here: thinking ON qualifies; thinking OFF fails the
synthesizer's scratch-link contract, reproducibly.

Confounds, stated rather than buried:

  - The two batteries are not the same subject. Mine adds the reviewer
    pair (15 -> 16 pairs with attached evidence). But the reviewer pair
    QUALIFIED both times, and the failing contract is `scratch.link.*`,
    which this tranche does not touch. The seat change is not implicated.
  - They ran on different days against a hosted model. A provider-side
    model change cannot be excluded from this evidence.
  - Two batteries is two samples.

## What this says about the instruction

R5 — "GLM 5.2 should have had thinking off" — is now implemented and
binding, and it has a measured price: on this provider and this model,
thinking off costs the scratch-link contract and therefore the whole
full engine. That is not an argument against the rule. It is the rule
doing its job: it surfaced, at qualification time and before any
reasoning tokens were spent, a capability loss that would otherwise have
appeared as mysterious mid-run repair churn.

The D2b lesson repeats here in a new place: the harness's job is to make
a silent degradation typed and early.

## Open, for the operator

The thinking-off run is achievable, but only by giving something up.
The cheapest candidate is the scratch channel: `scratch.link.*` is the
only failing contract, and it belongs to the advisory scratch workshop,
not to conjecture, criticism, adjudication, or simulation. Disabling
scratch removes those pairs from the inventory, and the remaining
surface qualified cleanly with thinking off in both batteries.

That is a further change to the engaged preset and is not authorised
here, so it is not done.
