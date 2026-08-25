# Section 15 - Transferable insights

*Every claim here is grounded in a specific incident in this record. Where an insight is
speculative or rests on one instance, that is stated.*

---

## 15.1 A green test suite is not evidence, and the gap is enormous

**The measurement.** 701 test methods, 2,985 subtests, 28,987 lines of test code against
13,206 lines of engine - a 2.2 : 1 ratio. Against 62 mutations that each silently reverse a
stated commitment: **16 caught, 46 survived. 3 of 26 commitments held.**

**Why the gap is structural, not a failure of diligence.** The ordinary test is written by
*reading the code and asserting what it does*. It therefore agrees with the code **by
construction**, and it goes on agreeing after the code stops being right. It is a
description, not a constraint. Nothing about care or coverage percentage changes this; the
test and the code have the same author and the same reading.

**The strongest evidence is the distribution, not the total.** `compile.py` lost **1 of 9**
mutations. Every other module guarded the ordinary way fell over: `registry.py` 6/6,
`validate.py` 6/7, `canonical.py` 4/4, `binding/plan.py` 4/4. `compile.py` is the file whose
guards were each written under the rule *a guard is not installed until shown to FAIL on a
planted violation.* Same author, same week, same repository, same care - **different
installation procedure, order-of-magnitude different result.**

**Caveat on the strength of this.** It is one repository, one author, one week, and the
mutations were proposed by models that had read the acceptance record. The direction of the
effect is unambiguous; the magnitude should not be generalised without replication.

---

## 15.2 A guard that reads its subject holds nothing

Three distinct instances in this record, all found by planting rather than reading:

1. **Iterating the constant under test.** A guard written to hold
   `_RULE_TARGET_BLOCKING_KINDS` looped over that very set. Removing a member ran one fewer
   subtest - 95 became 94 - and nothing failed.
2. **Checking a declared field list.** A guard inspected
   `DiscernmentReport.__dataclass_fields__`. A mutation added a `@property accepted`
   returning `self.status is Status.LIVE`. **A property is not a dataclass field.** 691 tests
   green while the forbidden inference became public API.
3. **Checking data beside behaviour.** A guard read `_CYCLE_SETTLING_EDGE_KINDS` and asserted
   `CONTRARY_TO` was absent. A mutation added an `elif` branch *next to* the frozenset, in
   the only place that consults it. The frozenset was untouched. 691 tests green.

**The rule, stated precisely:** *a guard must not derive the set of things it checks from the
artifact under test.* Reading the artifact to assert a **specific expected value** is fine;
generating the checks from it is not, because shrinking the artifact then shrinks the test.

**The corollary, from instances 2 and 3:** a guard that checks **declared data** does not see
**added behaviour**. The remedy is to check the *surface* or the *behaviour*, not one
declaration mechanism.

---

## 15.3 The static scan narrows; only the mutation decides

An AST scan for the shape in 13.1 - loops deriving their checks from an engine-owned
collection - found 7 candidates across 28,987 lines. Mutating the two most alarming
(`canonical.RECORD_COLLECTIONS`, the pack's `PREDICATES`) showed **both are in fact held**, by
neighbouring guards rather than by the flagged loops. `RECORD_COLLECTIONS` is rescued by a
sibling test that checks it against `dataclasses.fields(Package)`.

**Insight:** shape-based static analysis is a *risk indicator*, not a verdict. Reporting the
7 as findings would have been false. The correct pipeline is **scan to narrow, mutate to
decide**.

---

## 15.4 An instrument's own defects masquerade as findings

Four instances, each of which produced a wrong number before it was caught:

| the instrument | the artifact it produced | the real cause |
|---|---|---|
| Mutation probe | "59 caught, 3 survived" | Its applicability check tripped over its own edit, so every non-additive mutation read as caught |
| Consistency audit | A `CONTRADICT` on a real pair | A 200-character excerpt window cut four lines before the document's own qualification |
| Reviewer packet | Three EMPTY replies at `finish=length` | Not size - an **unbounded question** with no stopping rule |
| Consistency packet build | Two dead patterns surviving for cycles | It checked per-*document*, not per-*pattern* |

**Insight:** before quoting an instrument's number, control it in both directions - it must
report the *negative* case correctly too. The mutation probe was only trusted after a control
mutation that reverses nothing was confirmed to report `SURVIVED`. A probe that only ever
says `CAUGHT` measures nothing.

**The specific trap in the "59/3" case is worth isolating.** The error was not noise, it was
**masking**: mutations no guard catches were reported as caught. It was found by reading the
*attribution* - which test caught each mutation - rather than the verdict. **Always record
which guard fired, not just that one did.**

---

## 15.5 Independent review finds different things than review-by-reading

**What the models found that the author did not:**

- The `_RULE_TARGET_BLOCKING_KINDS` gap - found by asking *"what could revert without a test
  catching it?"* rather than *"is this correct?"* The question form did the work.
- A self-contradicting sentence in the acceptance record, caught by **two models
  independently**, one quoting the contradiction back verbatim.
- A code comment breaching the very condition it was documenting (DF-1 condition 1 requires
  every record of the binding to cite battery pair C; the comment cited nothing).
- An overstated claim: the registry mechanism "does not establish that the id was already a
  version carrier."

**What the models got wrong, and how it was visible:**

- A reviewer answered `CONFORMS` from a packet that did not contain the evidence, reasoning
  from a role name. A second reviewer on identical material returned `MISSING` and declined
  to guess. **The disagreement was more informative than either verdict.**
- A coverage critic reported a decision as uncovered when it was covered by a mutation
  outside the material it was shown - an author packet error, not a reasoning error.

**Insight:** the value is concentrated in (a) **adversarial question forms** - "what would
silently revert this?" beats "is this correct?"; (b) **two independent readers on identical
material**, where disagreement is the signal; and (c) **`MISSING` as a first-class verdict**,
so a reviewer can decline rather than guess.

---

## 15.6 Guard the process against the author, and expect it to fire

The review ledger's designated-reviewer rule refused the author's own work:

    accepted-reg was reviewed by kimi-k2.7-code without declaring which job it
    corroborates; that is a substituted reviewer, not corroboration

Routing different questions to different models *feels* like independence and is, from the
ledger's side, indistinguishable from shopping for a friendlier reader. **The remedy was to
satisfy the guard substantively rather than weaken it** - the designated reviewer was asked
both questions from identical material.

**Insight:** a process guard that never fires on its author is probably not a guard. Design
for the case where it fires on you, and treat weakening it as the failure.

---

## 15.7 Measurements report reachable subsets, and should say so

RT-1's blast radius was measured at **22 packages**; implementation produced **346 failing
tests**. The instrument enumerated packages built by *no-argument fixture builders* - it
could not see packages constructed inline in test bodies, nor second-order effects on tests
asserting on compiled output.

**Insight:** an enumeration instrument reports a **lower bound**. Stating the bound's shape -
*what the instrument can and cannot reach* - is part of reporting the number, not a caveat
appended to it.

---

## 15.8 "Cannot express" is not "considered and rejected"

Twice in one day, *the vocabulary cannot follow this path* was written down as though it were
*this option was considered and narrowed away*. The distinction became a two-part probe:
**does the referent exist in any reachable record**, and **can the vocabulary follow the
path**. "Referent present, capability absent" is a **missing capability**.

This carried the DF-1 decision. Two independent reviewers were asked directly whether the
characterisation was honest or "a rejected reading dressed up." Both said honest, and one
gave the discriminating reason: *a rejected reading would require showing the face-binding
produces a wrong semantic result; here it was never tested semantically because it could not
be compiled.*

**Insight:** the two produce identical prose and opposite epistemic states. A rejected option
has been *tested*; an inexpressible one has not. Only the first is evidence.

---

## 15.9 The twin is not the compiler

A hand-written model (`build_program`) reproduced the compiler's lowering for the example
batteries. Twice, a decision turned out to be exercised **only through the twin**: battery
pair C for DF-1, and the `wound` challenge kind for RT-6. In both cases the real compiler had
no route driving it, and the suite was green.

**Insight:** a hand-built model of a system is a *specification of intent*, useful for
minimal pairs and for detecting divergence. It is not evidence about the system. Every
decision needs at least one route through the real implementation.

---

## 15.10 The diagnosed root mechanism, in the project's own words

> one mechanism under most reports - **compression under narrative pressure**. When evidence
> becomes a document, the author compresses toward the cleaner story: fewer decisions,
> settled questions, orderings that look derived. The counterweight is not vigilance (it
> failed repeatedly) but instruments.

Two features of this deserve emphasis for external analysis:

1. **"The author" is the LLM agent doing the work.** The library says so and adds that *"the
   remedies assume the next agent will have them too."* These are documented **agent failure
   modes**, written by the agent that exhibited them.
2. **Vigilance was explicitly tried and explicitly failed.** Every remedy in eighteen field
   reports is a mechanism that fails loudly. Not one is an intention.

**The most striking instance is self-referential:** the guard written on 2026-08-25 to close
the vacuous-guard gap was itself vacuous, and its own author's comment claimed *"a silent
addition here fails there"* - a claim a mutation proved false the same day. Compression under
narrative pressure applied to a document *about* compression under narrative pressure.

---

## 15.11 Open questions this record does not settle

- **Does mutation coverage generalise as a metric?** One repository, one week. The direction
  is unambiguous; the 3-of-26 magnitude is not established as typical.
- **What is the right mutation-registry size?** 62 mutations over 26 commitments is
  arbitrary. Five accepted decisions still carry none (AU-1, AU-7, REG-2, REG-3, RT-1a), and
  a critic named 18 further uncovered commitments, 14 of which remain open in
  `zoo/mutations/BACKLOG.md`.
- **Can mutations be generated rather than authored?** All 62 were written by models reading
  the acceptance record. Whether a model without the record could propose equally meaningful
  reversals is untested.
- **Is the 46-survivor result actionable at reasonable cost?** Writing 46 guards, each proved
  on its mutation, is a large amount of work whose value is unmeasured. Nothing here shows
  that closing them prevents a real defect.
- **How much of the value came from the models versus from the question forms?** The most
  productive finding came from the prompt *"name anything that could silently revert without
  a test catching it."* Whether a weaker model with that prompt outperforms a stronger model
  without it is untested.

