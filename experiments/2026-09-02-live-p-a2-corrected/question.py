"""The P-A1 seed question, frozen as bytes.

The operator supplied this verbatim in the tranche instruction. It is kept in
its own module, imported and never restated, for the reason every predecessor
tranche keeps its question in one: a copy is a second thing to keep true, and
a question that drifts by a byte mints a different run id and silently makes
the launch a different experiment from the one that was pre-registered.

`preflight_pa1.py` asserts QUESTION_SHA256 against the value PREREG.md §2
froze, so drift is caught before any provider call.
"""

QUESTION = (
    "Consider asynchronous majority dynamics on a random 3-regular graph on n "
    "vertices: at each step one uniformly random vertex adopts the majority "
    "opinion of its three neighbors. Starting from a uniformly random "
    "two-coloring, as n grows, does the probability of reaching unanimous "
    "consensus tend to 1, to 0, or to a constant strictly between? "
    "Characterize the finite obstruction structures (locally stable mixed "
    "configurations) that prevent consensus, and give either a proof sketch "
    "or a falsifiable quantitative law for how their prevalence scales with n."
)
