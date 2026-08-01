# Capability contract for this run

Each capability has a typed proposal channel. Work that only DESCRIBES using a
capability in prose — without filing the typed proposal — is unverified by
construction, and the record's critics have convicted every such candidate in
prior runs. File proposals; do not narrate them.

## What is different about this run, stated plainly

You are being asked to invent a runtime intervention on language models, and
the obvious way to test one is to call a language model. You cannot do that
from the simulation channel, and the reason is not arbitrary.

`sandboxed_python_v1` executes model-authored Python inside an unshared network
namespace (`unshare --net`), and the backend REFUSES TO RUN if the host cannot
create that namespace. It fails closed. That namespace is the only reason
running model-authored code is safe here at all, and it is not being removed
for a convenience.

So the live calls were made for you, in advance, by a fixed harness-side driver
whose source you are shown (`probe.py`, summarised below). You reason over real
measurements of a real model; you do not get a socket.

This is a real constraint on what you can conclude, and you should say so in
your answer rather than write as though you had run the experiments yourself.

## The supplied measurements

They are ATTACHED as an evidence document (`JOLT_MEASUREMENTS.md`), not sealed
into the simulation input catalog: this CLI exposes no flag for the catalog, so
the numbers reach you as readable evidence rather than as `inputs` inside
`simulate`. If you want to compute over them in the simulation channel you must
carry the relevant figures into the program text yourself, and you should
transcribe only what your claim actually rests on.

    model         glm-5.2
    samples       12 independent calls per (jolt, task) cell
    tasks         6 prompts with a known dominant answer
    jolts         9 conditions, including baseline

Per cell you get:

    samples       how many calls returned usable text
    distinct      number of distinct normalised answers
    top_mass      share of samples on the single most common answer
                  (1.0 = total collapse; 1/samples = perfectly spread)
    mode          the most common answer
    histogram     the top answers with counts

The nine jolts are: `baseline`, `temperature_high` (T=1.3), `temperature_max`
(T=1.8), `top_p_wide` (T=1.0, top_p=0.99), `seed_varied` (explicit per-call
seed), `avoid_obvious` (instruction not to give the common answer),
`persona_random` (system prompt asserting uniform sampling), `school_stance`
(this harness's own schools mechanism transplanted — a rotating critical school
in the system prompt), and `anti_anchor_fewshot` (system prompt asserting the
popular answers are taken).

`school_stance` is measured deliberately: it is the mechanism you are being
asked to improve on, and it gets no benefit of the doubt.

## Sandboxed simulation (simulation_mode sandboxed_python_v1)

Contained Python: scratch working directory, scrubbed environment, hard
resource limits, NO network. Deterministic and self-contained; integer and
float arithmetic only. The whole source is exactly one
`def simulate(inputs, rng)` and nothing else, and the mapping it RETURNS is the
only output recorded. Printing records nothing. Every name in
`requested_observables` must be a key of that returned mapping.

Fit for this challenge, in rough order of how decisive it is:

- **Testing a claim about the measurements.** Any statement that a jolt works
  is a statement about `top_mass` and `distinct` across cells. Compute it and
  RETURN the per-cell numbers your claim rests on, not a summary verdict.
- **Separating diversity from degradation.** `temperature_max` will move the
  collapse. Whether it moves it usefully is a different question. Return a
  statistic that distinguishes the two on this data, and be explicit about
  what it assumes.
- **Refuting a jolt.** "Jolt X reduces collapse" is refutable per task. Return
  the tasks where it fails, not the mean across tasks — a mean hides exactly
  the partial results requirement 2 asks you to surface.
- **Sensitivity of your own mechanism.** If your mechanism has a parameter,
  compute what its choice does to the predicted effect, and return the curve
  rather than the single point you prefer.

A simulation that cannot separate rival predictions is weight, not evidence.
Return the discriminating quantity — the cell, the histogram, the divergence —
never a boolean summarising it.

## Scratch workshop

Requirement 4 asks for a mechanism that predicts something the data does not
already show. That does not arrive in one step. Use scratch to carry the
provisional versions, link them to the simulations that bear on them, and kill
the ones the numbers contradict. A recorded dead conjecture is worth more than
silence about it.

## Directed research (allowlist: en.wikipedia.org, ollama.com)

`ollama.com` is on the allowlist for this run so you can read the provider's
own documentation on the runtime knobs actually exposed — sampling parameters,
seeds, reasoning controls, and their semantics. A mechanism that depends on a
knob the API does not expose is not implementable, and checking is cheap.

Treat what you fetch as evidence about what is DOCUMENTED, not about what is
true. Documentation routinely describes intended behaviour rather than observed
behaviour, and the supplied measurements are the better authority where the two
disagree. Where they disagree, say so — that is a finding.
