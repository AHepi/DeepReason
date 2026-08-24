---
name: expressibility-probe
description: The two-part test behind any "X is not expressible" claim (FR-23). Use BEFORE writing that sentence. The source cycle drew the wrong conclusion from a true inexpressibility twice in one day.
---

# Expressibility Probe (new in 0.5, from FR-23)

<!-- PROMPT-CORE-BEGIN -->
"X is not expressible" is two claims and a conclusion, and each part is
checked separately - by construction and execution, never by reading
the model (FR-25).

1. THE DATA QUESTION: does the referent exist in ANY record reachable
   from the anchor - including via joins the vocabulary cannot follow?
   Walk the record graph, not one record's fields. (The source cycle
   declared "no atom referent exists" while a two-hop path
   discharge -> challenge -> atom sat in the model.)
2. THE CAPABILITY QUESTION: can the vocabulary follow the path?
   Construct the actual attempt and run it through the real validator;
   record the refusal code. A dataclass accepting a shape that
   validation refuses is exactly why reading is not enough.
3. THE MANDATED FRAMING: the two answers force the conclusion -
   - referent absent everywhere: the choice is genuinely narrowed; say
     to what;
   - referent present, capability absent: this is evidence of a
     MISSING CAPABILITY, an argument for amending the model, NOT for
     accepting the approximation. The decider chooses between an
     approximation and an amendment, and must be told that is the
     choice.
   Writing "narrowed" where the second case holds is the FR-23 defect.
4. Distinct inexpressibilities are distinct: name each one's fact and
   the test that measures it (see decision-mapping rule 4).
5. Each probe outcome enters the record with an executed route
   (discharge-typing rule 3): the construction script and its actual
   refusal or acceptance output.
<!-- PROMPT-CORE-END -->
