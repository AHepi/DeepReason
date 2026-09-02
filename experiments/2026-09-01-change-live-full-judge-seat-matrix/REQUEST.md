# Request: test all seat configurations on full judge trial

Captured: 2026-09-01 from the operator messages in this tranche.

## Verbatim

> Oh never merge with main. For now. Design some tests using the below API key.
> Don't worry about token use. This a cheap throw away account. Test all seat
> configurations on full judge trial. No observe only. Just do not use Kimi K3.
> It's too big.
>
> Just a word of warning. Don't use thinking high. And check Ollama
> documentation so you know what settings actually mean. GLM 5.3 thinking none
> means trace will populate its forms. Also, only 3 concurrent processes can run
> on this API key.
> Try to test everything.

> No try to test all configurations as well. I want to know what's possible and
> what isn't. Breaking the machine isn't a problem on GitHub since all damage is
> reversible.

> I forgot to tell you to use alphaXiv plugin whenever exploring options. There
> may already be solutions that have been tested.

The credential value supplied in a prior operator message is deliberately not
copied into this tracked artifact.

## Requirements

R1 (artifact): "Design some tests using the below API key."

R2 (behavior): "Test all seat configurations on full judge trial."

R3 (behavior): "No observe only."

R4 (behavior): "Just do not use Kimi K3. It's too big."

R5 (behavior): "Don't use thinking high."

R6 (process): "check Ollama documentation so you know what settings actually
mean."

R7 (behavior): "GLM 5.3 thinking none means trace will populate its forms."

R8 (behavior): "only 3 concurrent processes can run on this API key."

R9 (process): "Try to test everything."

R10 (behavior): "test all configurations as well."

R11 (artifact): "I want to know what's possible and what isn't."

R12 (process): "use alphaXiv plugin whenever exploring options."

## Standing constraints

C1: "Oh never merge with main. For now."

C2: "Don't worry about token use. This a cheap throw away account."

C3: "Breaking the machine isn't a problem on GitHub since all damage is
reversible."

C4: Credential material is never committed, logged, or copied into an artifact.

## Map preflight

Resolved owners: `DR-SUB-evaluation`, `DR-SUB-llm`, `DR-SUB-manifest`,
`DR-CON-authority`, `DR-CON-criticism-source`, `DR-CON-schools`, `DR-CON-seats`,
`DR-SEAM-evaluation-x-rules`, `DR-SEAM-llm-x-manifest`, and
`DR-INV-frozen-surfaces`.

## Open questions (for dr-spec-change)

Q1: "all configurations" is unbounded if it includes arbitrary judge-seat
counts, arbitrary numeric settings, and every future model; what finite current
surface preserves the operator's request without silently sampling it?

Q2: the credential named by R1 is not available through this process's
environment or credential store; what secure handoff is required before live
provider contact?

## Amendments

Captured from the operator's standing design-law messages that govern this
campaign:

> What are your thoughts about using these for improvements? Remember maximum
> modularity and configurability is essential. As well as usability by other
> humans.

> Hmm. A standing rule is that formalism shouldn't out rank valid prose. And
> since prose isn't always mechanically valid, I'm afraid that vocabulary will
> wipe almost everything from the board. Also, the harness is inherently anti
> inductivist and tries to avoid mechanically defining optimisation targets or
> statistical tightening of any sort. It's also meant to allow open exploration
> without the mechanical constraint that may hinder it. Heuristics imply
> something about the problem space being known, but in popperian epistemology,
> that's reductionist and inductivist and inherently hinders creativity. Which
> is what I was trying to create with DeepReason.

These standing laws add traceable constraints C5-C8:

C5: formalism must not outrank valid prose; mechanical probe or parser failure
is never evidence that prose is epistemically invalid.

C6: no ranking, optimization target, eliminator, heuristic reduction, or
statistical tightening is introduced by this campaign.

C7: exploration remains open; no observed prefix is used to prune the frozen
queue.

C8: campaign configuration and reports remain modular and human-readable.
