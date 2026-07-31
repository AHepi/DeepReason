# The schools mechanism, as this harness actually implements it

Extracted from source, not paraphrased from memory. Cited so you can reason
about what it does and does not achieve.

## What a school is

`src/deepreason/capture/schools.py`:

> A school is a persistent conditioning regime for gamma-calls, registered as
> an attackable school-policy artifact (Refl). Constitution = lineage
> inheritance: school k's packs draw exemplars from accepted artifacts with
> provenance.school == k — curation-free by construction. Reseed is
> succession, not deletion: a new policy artifact + a Reseed event; the roster
> is a deterministic function of the log. Schools never touch att/dep,
> adjudication, or statuses.

The design slogan is **islands in conjecture, panmixia in criticism**:
conjecture is partitioned so lineages diverge; criticism is deliberately
cross-cutting so nothing is judged only by its own kin.

## The stance library

One-time global curation, eight stances, assigned round-robin as
`school-k -> _STANCES[k % 8]`:

    mechanist     demand a causal mechanism
    skeptic       counterexample first
    unifier       seek the covering principle
    empiric       anchor in cases
    formalist     derivation first
    historicist   precedent and succession
    adversary     strongest attack on the incumbent
    minimalist    parsimony pressure

A public text run seeds exactly four (`school-0..school-3`, `PUBLIC_SCHOOL_COUNT`
in `v6_policy.py`), so in practice the live stances are mechanist, skeptic,
unifier, empiric.

## What the mechanism enforces

- **Lineage inheritance.** A school's prompt packs are built from artifacts
  that school itself produced. Divergence is structural: two schools see
  different exemplars, so they condition on different history.
- **Foreign criticism.** `workflow/criticism.py` plans criticism so a target
  is attacked by schools OTHER than its owner. `ForeignCriticAssignmentV1`
  binds `owner_school_id` and `critic_school_id` and the validators refuse an
  owner from appearing in its own completed-critic set. `verify_root` audits
  this: a target with zero foreign schools is a recorded violation
  (`minimum_foreign_school_coverage=1`).
- **Reseed as succession.** A lagging school's stance rotates, and
  `crossover_from` records the most-distant school so the reseeded school's
  next calls draw THAT lineage's exemplars. The comment states the reason
  directly: *"rotating the stance alone just yields the same echo in a new
  voice (a skeptic mutating its own math)"*.

## What it does NOT do, and why that matters here

All of the above is **conditioning**: different exemplars, different stance
text, different critic assignment. Every call still goes to the same model on
the same route. The mechanism diversifies WHAT IS IN THE CONTEXT; it has no
lever on the decoder.

Three consequences worth taking seriously:

1. If a model's attractor is strong enough, identical decoding over slightly
   different contexts can still collapse to the same output. Conditioning
   diversity is not sampling diversity.
2. The `crossover_from` comment is an admission that the naive version of this
   idea failed — stance rotation alone reproduced the same content in new
   vocabulary. That failure mode is exactly the one a runtime jolt has to
   avoid, and it is evidence that *surface* variation is cheap and ineffective.
3. Foreign criticism is an ADJUDICATION diversity mechanism, not a generation
   one. It catches an attractor after the fact by having someone else attack
   it. It does not stop the attractor forming.

So the schools mechanism is the best existing answer in this codebase and it
is a conditioning-layer answer. The question this run asks is whether a
better one exists at the decoding or protocol layer, and it is genuinely open.
