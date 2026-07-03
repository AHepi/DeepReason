"""DeepReason — Conjecture-Criticism Harness (creativity-calculus spec v1.3).

Core invariant (spec §0): the harness is deterministic and carries all
epistemology. The LLM is a bounded pure function ``pack -> schema-validated
JSON`` (the conjecture operator gamma) and never holds graph state,
adjudicates, or controls flow. Nothing is deleted; the event log is the
source of truth. Measures never adjudicate.
"""

__version__ = "0.1.0"
