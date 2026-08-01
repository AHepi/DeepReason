# Capability contract for this run

This run grants three operator-opted capabilities. Each has a typed
proposal channel, and work that only DESCRIBES using a capability in
prose — without filing the typed proposal — is unverified by
construction. Prior recorded runs on other problems left the simulation
channel empty while describing simulations at length, and the record's
critics convicted every such candidate. File proposals; do not narrate
them.

## Sandboxed simulation (simulation_mode sandboxed_python_v1)

Contained Python: scratch working directory, scrubbed environment, hard
resource limits, no network. Programs must be deterministic and
self-contained — the program text carries everything it needs, including
any coin systems and any candidate procedure under test. Integer
arithmetic only.

The program's shape is fixed and the schema states it: the whole source
is exactly one `def simulate(inputs, rng)` and nothing else, and the
mapping it RETURNS is the only output that is recorded. Printing records
nothing. Every name in `requested_observables` must be a key of that
returned mapping, or the run fails with `declared observable missing`.

Fit for this challenge — in rough order of how decisive it is:

- **Refuting a claimed search bound.** Any claimed bound W(C) is a
  refutable universal claim. Enumerate small coin systems, decide each
  by brute force, and return the ones whose smallest counterexample
  exceeds the claimed W(C). Returning even one such system settles the
  question against the bound. Returning none over a large enumerated
  space is evidence for the bound and is not a proof of it — report
  which of the two you have.
- **Differential testing of a candidate procedure** against the brute
  force oracle across an enumerated family of systems, returning the
  disagreements rather than a pass/fail summary. A disagreement is a
  concrete counterexample to the procedure.
- **Oracle calibration**, before any oracle verdict is offered as
  evidence: show it reports a counterexample for at least one system and
  none for at least one other, and return both.
- **Measuring where smallest counterexamples actually sit** across the
  enumerated space, as a distribution over the coin values, which can
  suggest the true bound rather than confirm a guessed one.

A simulation that cannot separate rival predictions is weight, not
evidence. Return the discriminating quantity itself — the offending
system, the disagreeing amount — not a boolean summarising it.

## Directed research (frozen allowlist: en.wikipedia.org)

Research proposals must name specific https URLs on the frozen
allowlist. The request budget is small. Spend it on pages that can
settle a live disagreement — above all a published bound or a published
complexity result, if one exists — rather than on background reading.
Anything fetched is evidence about what is PUBLISHED; a fetched claim
still has to survive the simulation channel before it is relied on.

## Evidence citation

Claims attributed to the dossier or to fetched research must cite the
admitted block ids. Citations are byte-checked against the admitted
text: a quote that does not appear in the block it cites refuses as
typed evidence.

The dossier states definitions and rules of evidence only. It asserts no
bound and reports no result, so there is nothing in it that can be cited
as a fact about the answer. Any bound in a candidate answer is therefore
either derived in that candidate, fetched from research, or unsupported
— and criticism should establish which.
