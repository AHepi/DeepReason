---
name: mapping-table
description: Maintain an explicit two-sided table for every syntax-to-semantics correspondence (Reed step 2) so the binding between terms and interpretations lives in an artifact, not in working memory. Use during pinning, fragment construction, doc-code reconciliation, or whenever label/identity conflation threatens.
---

# Mapping Table (Reed 2)

<!-- PROMPT-CORE-BEGIN -->
Every correspondence between a term and an interpretation is one row of
the mapping table; if it is not a row, it does not exist.

1. Row shape: term (with anchor equation/row) | fragment interpretation
   (named predicate or structure) | witness instance (battery id) |
   polarity notes (where negated, which rows) | status
   (CANDIDATE / PINNED / OPEN / RETIRED).
2. One row, one correspondence. A term interpreted two ways is two rows
   with distinct ids, never one row edited in place.
3. Label equality is never identity: a row asserting sameness across
   contexts must name the map that carries it and cite the witness
   instance where the map acts. No witness, no sameness row.
4. Before reasoning about any term, read its rows aloud into the work;
   never rely on remembered bindings. After any reasoning that changed a
   binding, update the row in the same work session.
5. Doc-code reconciliation is table-driven: each row cites both the
   document anchor and the code symbol; a row with only one side is by
   definition unreconciled and is listed in the table's OPEN section.
6. The table is append-and-supersede: retired rows stay, marked RETIRED
   with the superseding row id - the history of a binding is part of its
   meaning.
<!-- PROMPT-CORE-END -->
