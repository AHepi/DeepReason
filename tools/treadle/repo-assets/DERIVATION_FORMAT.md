# Derivation file machine grammar (zoo/derivations/FORMAT.md)

Checked by scripts/derivation_check.py RULES THEORY FILE. Strict JSON,
canonical serialization. One derivation per file.

{ "schema": "DERIVATION_V1",
  "theory": "<theory name>",
  "target": "<row id being derived>",
  "steps": [
    {"id": "s1", "rule": "PREMISE", "row": "<theory row id>", "grade": "D"},
    {"id": "s2", "rule": "<rule id>", "premises": ["s1", ...],
     "formula": <s-expression>, "grade": "<grade>"} ],
  "conclusion_step": "<id>" }

Rules of the grammar:
1. Step ids unique; a step may cite only EARLIER steps.
2. PREMISE steps name a theory row and carry NO formula: the checker takes
   the row's condition byte-authoritatively from the theory profile.
3. Every other step states its full formula in the s-expression condition
   language (same language as the theory profile) and exactly one rule.
4. Grades come from the rules profile's declared order; propagation is
   checked (default: a step's grade cannot exceed the minimum of its
   premises' grades).
5. The conclusion step's formula must equal the target row's condition
   byte-exactly. Close is not equal.
6. A derivation you cannot complete is reported as BLOCKED with
   CANNOT_DERIVE and what was attempted -- NEVER as a padded pseudo-proof,
   and NEVER as a claim that no derivation exists (non-derivability
   belongs to countermodel search, not to a model's failure).
