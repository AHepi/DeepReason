# FIELD_REPORTS.md — defects 14–26

treadle evolves by field report: a defect observed in real use, its instance,
and the module or rule that now prevents it. Reports 1–13 belong to earlier
cycles (10–13 are visible as the hardening notes in `battery_digest.py`; the
earlier ones are not carried). Reports 14–26 come from one working cycle on
the Poietics repository, 2026-08, in which the author's work was audited by
independent models and adversarial subagents throughout. Where a report says
"the author", it means the LLM agent doing the work — these are agent failure
modes, and the remedies assume the next agent will have them too.

Summary of the cycle's error analysis: one mechanism under most reports —
**compression under narrative pressure**. When evidence becomes a document,
the author compresses toward the cleaner story: fewer decisions, settled
questions, orderings that look derived. The counterweight is not vigilance
(it failed repeatedly) but instruments: guards on derivation, execution over
reading, and reviews that are required to attack.

---

**FR-14 — hand-propagation drift.** A false claim ("no registry change is
needed") was corrected in one document and left standing in another; a second
claim went stale the same way; a heading contradicted its own body. No
single-document review can see any of this. → `consistency_packet.py`: the
claims that appear in more than one document are extracted into one packet
with `--write`/`--verify`; an edit to any quoted claim fails verify, forcing a
re-check that the documents still agree. Found two live instances on its
first run.

**FR-15 — reviewer packet overrun.** Four whole documents sent to a reviewer
returned an EMPTY reply at finish=length, twice; raising the output budget to
32k did not help, because the problem was prompt-side. An extract of the
claims (2.7k tokens) was answered immediately and found real defects.
→ `review_harness.py` enforces a packet ceiling and refuses oversized jobs
with the remedy named: shrink the packet, never raise the budget.

**FR-16 — provenance read as reproducibility.** A byte-identical packet at
temperature 0 and a fixed seed returned two different replies. The transcript
header's config line invited the wrong inference. → transcripts carry an
explicit `reproducibility: none` line; `LEDGER_FORMAT.md` states that the
ledger guarantees the bytes SENT can be rechecked, never that the reply can
be regenerated. An external call is never an acceptance command.

**FR-17 — superseded transcripts.** A job re-ran (packet changed); the new
transcript overwrote the old at the same path; the ledger kept both rows; the
verify test failed on the older row. Correct behaviour, undefined semantics.
→ `LEDGER_FORMAT.md`: the transcript agrees with the LATEST row for its path;
every superseded row keeps its digests so the loss is visible; the hash chain
covers superseded rows so a re-run cannot quietly drop one.

**FR-18 — vacuous guards.** Three separate guards passed while checking
nothing: a token matcher that also matched Python type annotations, a section
extractor truncated by a markdown table's own `---` separator, an assertion
whose target string legitimately appeared in the fixture. Each was found only
by planting a violation. → the standing rule, enforced by `selftest.py` and
SETUP step 5: a guard is not installed until it has been shown to FAIL on a
planted violation, and a regression test is not done until it has been seen
red without its fix.

**FR-19 — single-perspective determinism tests.** A canonical-bytes bug made
one package hash differently in different processes (a sort key dropped half
of a two-reference member; ties fell to hash-seed-dependent set order). The
determinism test compared two calls in one process; the only cross-process
harness pinned PYTHONHASHSEED=0 — structurally hiding seed dependence.
→ SETUP rule 5: canonicalisation and digest claims are tested across ≥2 hash
seeds in separate processes; pinning the seed in such a harness is forbidden.

**FR-20 — single-shape fixtures, and undiscriminated options.** A cycle
collapser was only ever tested on a positive cycle, so negation cycles
escaped it; separately, a three-option decision turned out to have NO fixture
separating the options (two behaviourally identical, one inexpressible) —
discovered late, by accident. → `example-battery` gains the COLLAPSE/SPLIT
refutation modes and a separability statement; `denotation-tests` gains an
option-level discrimination check: for every pair of live options, name the
observable that separates them, or declare the choice observationally
vacuous. That declaration changes what acceptance means and must be in front
of the decider.

**FR-21 — disposition smuggling.** The author closed a question that was the
owner's to decide (recommending against building a specified deliverable, as
a finding); then over-corrected into "no recommendation is attached" beside a
recommendation in prose. → `term-pinning` gains disposition typing: every
open item carries exactly one of DECIDE / PROPOSE / ESCALATE; a view inside a
PROPOSE is marked as a view and separated from the options; a decision not to
do specified work is a decision. `review-response` makes the check standing.

**FR-22 — dependency-map inversion.** A queue map filed the item its own
source calls "the largest thing here for the owner to decide" as a rider on a
smaller decision; fabricated a shared cause between two independent
questions; counted two table rows by different rules, flattering the step the
author preferred; and presented a preference ordering as derived.
→ `decision-mapping` skill: the rider test (an item rides on a root only if
EVERY answer determines it), the admission/shape/freeze-time tiers, per-option
verification of eliminations, one counting rule per table, and orderings
labelled as preferences with their criteria and their chooser named.

**FR-23 — "not expressible" misread as narrowing.** Twice in one day the
author found an inexpressibility and concluded the owner's choice was
narrowed. Both times the referent existed (once via a two-hop join the
selector vocabulary couldn't follow) and the finding was evidence of a
MISSING CAPABILITY — an argument for changing the model, not for accepting
the approximation. → `expressibility-probe` skill: the two-part test (does
the referent exist in any reachable record; can the vocabulary follow the
path), verified by construction through the real validator, and the mandated
framing of the conclusion.

**FR-24 — analogy transporting the unprotected property.** "Faces are
required to name a closure because faces are selective; rules are not
selective; therefore optional" — invalid, because the precedent's rule
protects universal targetability, not existence selectivity, and the text
("For every face f...") says so. → `precedent-transport` skill: name the
invariant the precedent's rule protects, show the target shares it, or the
analogy is decoration.

**FR-25 — reading versus running.** Every load-bearing claim about code that
was checked by executing it survived or was corrected decisively; claims made
from reading alone failed at roughly a coin-flip rate across the cycle
("two fields move statuses" — one; "no referent exists" — it did; "no
registry change needed" — false). → `discharge-typing` gains the run-first
rule: a claim about code without an execution route is PROSE and does not
enter a ledger; `influence_probe.py` exists so "what can affect what" is
measured, not argued.

**FR-26 — arithmetic from memory.** A document's headline total (24) did not
match its own sources (23), because it was written from recollection; the
same draft omitted one item entirely while including its alias.
→ `mapping-table` rule 4 extends to numbers: no total enters a document from
memory; every count is recomputed by the document's staleness guard.
