# Section 00 - Executive summary

**Poietics** is a Python implementation of the *PFF Core v0.1* specification: a typed
admission boundary plus a deterministic well-founded evaluator. This record covers nine days,
2026-08-17 to 2026-08-25, 50 commits, in which an LLM agent built the implementation, put
every semantic freeze to independent model review, obtained owner acceptance for sixteen
normative decisions, implemented them, and then measured how much of that was actually held
by anything.

## The headline

| | |
|---|---|
| Engine | 29 modules, 13,206 lines |
| Tests | 33 files, **701 test methods, 2,985 subtests**, 28,987 lines |
| Test-to-code ratio | **2.2 : 1** |
| Independent model calls | 53, all hash-chained and auditable |
| Accepted decisions | 16 (14 numbered + 2 unnumbered), all implemented |
| Independent review of the implementation | **15/15 conformance rows CONFORM** |
| Mutations that silently reverse a stated commitment | **62 registered: 16 caught, 46 survived** |
| **Commitments actually held** | **3 of 26** |

A suite of 701 passing tests, a 2.2 : 1 test-to-code ratio, and three independent models
confirming the implementation does what was accepted - **holding three of twenty-six
commitments.**

## What that means, precisely

`SURVIVED` does **not** mean the code is wrong. Every one of the 46 surviving edits was
applied to code that is, as far as anything here can determine, correct. The reviewers were
right about the code.

A survivor means: **nothing would tell you if it stopped being correct.**

## The mechanism, and the strongest evidence for it

The ordinary test is written by *reading the code and asserting what it does*. It agrees with
the code **by construction**, and goes on agreeing after the code stops being right. It
describes; it does not constrain.

The evidence is the distribution, not the total. `compile.py` lost **1 of 9** mutations.
Every other module fell over - `registry.py` 6/6, `validate.py` 6/7, `canonical.py` 4/4,
`binding/plan.py` 4/4. `compile.py` is the file whose guards were each written under the rule
*a guard is not installed until shown to FAIL on a planted violation.* Same author, same
week, same care. **Different installation procedure; order-of-magnitude different result.**

## How the finding was reached, and the two false starts

1. A constant naming two challenge kinds lost a member. **677 tests stayed green.** It
   surfaced only because a reviewer, asked *"what could revert without a test catching it?"*,
   happened to name that constant. Luck, not method.
2. **The first guard written to close that gap was itself vacuous** - it iterated the constant
   it was holding, so removing a member ran one fewer subtest. 95 became 94; nothing failed.
3. The plant was made a **standing registry** indexed by *decision*, not by file, so the
   report answers "which commitments are held?"
4. **The first full run reported "59 caught, 3 survived" and was wrong.** The probe's own
   applicability check tripped over the probe's own edit, so every non-additive mutation read
   as caught. It was found by reading *which test* caught each mutation rather than the
   verdict.
5. The probe left a planted defect in the working tree **twice** - once to a command timeout,
   once to a `SIGKILL` no handler catches - before being moved into a throwaway copy.

## Controls, because a number this bad needs them

- Full suite on an **unmutated** sandbox copy: 701 passed, identical to the working tree.
- **Zero disagreements** across 26 verdicts shared between three runs (two in-tree, one
  sandboxed).
- Survivors read by hand for equivalent mutants. `isinstance(True, int)` is `True` in Python,
  so one survivor silently admits a bool as an integer detail; another grows a vocabulary the
  specification says "may grow only through a registry version change"; a third stops a
  discharge lifting a block. All genuine.

## What independent review contributed

53 calls across three approved models, every prompt digest recorded in an append-only
hash-chained ledger (independently re-verified during this compilation). Reviews found: the
constant gap above; a **self-contradicting sentence** in the acceptance record, caught by two
models independently; a code comment breaching the very condition it documented; and an
overstated claim about what a registry mechanism establishes.

They were also wrong in instructive ways - one answered `CONFORMS` from a packet lacking the
evidence while a second on identical material returned `MISSING` and declined to guess. **The
disagreement was worth more than either verdict.**

The ledger's designated-reviewer guard **refused the author's own work** mid-cycle, catching
review routing that was indistinguishable from shopping for a friendlier reader. It was
satisfied substantively rather than weakened.

## The diagnosed root cause, in the project's own words

> one mechanism under most reports - **compression under narrative pressure**. When evidence
> becomes a document, the author compresses toward the cleaner story: fewer decisions,
> settled questions, orderings that look derived. The counterweight is not vigilance (it
> failed repeatedly) but instruments.

"The author" is the LLM agent. Eighteen field reports document its failure modes, and every
remedy is a mechanism that fails loudly - not one is an intention to be more careful. The
sharpest instance is self-referential: the guard written to close the vacuous-guard gap was
itself vacuous, and its own comment claimed *"a silent addition here fails there"* - which a
mutation disproved the same day.

## What this record does not establish

One repository, one author, one week. The **direction** of the coverage finding is
unambiguous; the 3-of-26 **magnitude** is not established as typical. It is also unmeasured
whether closing the 46 survivors would prevent any real defect, and untested whether a model
without the acceptance record could propose equally meaningful reversals. Section 15.11
states the open questions in full.

