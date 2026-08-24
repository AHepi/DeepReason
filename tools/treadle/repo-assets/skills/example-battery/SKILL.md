---
name: example-battery
description: Build a battery of concrete instances BEFORE writing or evaluating any definition, pin, or semantic clause (Reed step 1). Use whenever a term needs a meaning, a pin is being drafted, or an existing pin is being retrofitted. Converts semantic mapping from unaided imagination into curation of juxtaposed structures.
---

# Example Battery (Reed 1)

<!-- PROMPT-CORE-BEGIN -->
Before any clause about a term's meaning is written, build its battery.

1. Construct, as small concrete structures in the fragment language:
   - >=3 POSITIVE instances the intended meaning must admit;
   - >=3 NEAR-MISS negatives, each a minimal pair with a positive -
     identical except in one respect, which the meaning must exclude;
   - >=1 BOUNDARY case whose classification is genuinely undecided,
     recorded as OPEN with the question stated.
2. Structures are explicit and tiny: name the sorts, list the elements,
   give every relevant relation extensionally. No instance is described
   only in prose.
3. Juxtapose everything in one file, positives beside their near-miss
   partners, with one line per pair naming the single difference.
   Near-misses are pairwise DISTINCT in the clause that admits them: no
   two N-instances may be the same single-bit flip of (structurally) the
   same positive -- a battery's discriminating power is the count of
   distinct negative shapes, not the count of N labels.
   Any structural assumption not present in the inventory candidate
   (e.g. licensing a chained/transitive reading of a relation) is never
   a silent positive: it becomes a boundary (B) instance carrying the
   question, or it is omitted.
4. If the term has a recorded risk corridor ("too weak admits X, too
   strong excludes Y"), X and Y are MANDATORY battery members: build the
   structure the too-weak reading wrongly admits and the structure the
   too-strong reading wrongly excludes. A corridor without its two walls
   built is not yet analyzed.
5. If you cannot construct three positives, the term is not understood
   well enough to pin: record what blocks each attempted instance and
   stop. That record is the deliverable.
6. Battery instances carry ids. Digests are produced ONLY by the repo's
   digest tool (scripts/battery_digest.py --write) over the canonical
   instance bytes; NEVER compute, estimate, or invent a digest yourself.
   Write the literal placeholder PENDING-DIGEST in every digest cell and
   let the acceptance command run the tool. A hand-written hash is a
   fabrication even if it happens to be correct.
7. The battery file is parsed by machines: its exact grammar (heading
   form, id pattern, registry table columns) is defined in
   zoo/batteries/FORMAT.md and is provided to you as a READ-ONLY
   REFERENCE section in your context. Conform to it byte-exactly. If
   that reference section is absent or marked MISSING, STOP and report
   BLOCKED requesting it -- never invent structure; semantically fine
   but mechanically unparseable output is a failure.
8. Instances are proto-members of the model zoo and feed the denotation
   tests. Never delete a battery instance a pin fails on; a failed
   instance is evidence, not clutter.
<!-- PROMPT-CORE-END -->
