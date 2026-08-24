---
name: mapping-table
description: Every syntax-to-semantics correspondence is one row of an explicit table (Reed 2); bindings live in artifacts, not working memory - and neither do NUMBERS (FR-26). Use during pinning, doc-code reconciliation, or whenever conflation threatens.
---

# Mapping Table (Reed 2)

<!-- PROMPT-CORE-BEGIN -->
Every correspondence between a term and an interpretation is one row of
the mapping table; if it is not a row, it does not exist.

1. Row shape: term (anchor) | fragment interpretation | witness
   instance (battery id) | polarity notes | status (CANDIDATE / PINNED
   / OPEN / RETIRED).
2. One row, one correspondence. A term interpreted two ways is two rows
   with distinct ids, never one row edited in place.
3. Label equality is never identity: a sameness row names the map that
   carries it and cites the witness where the map acts. No witness, no
   sameness row.
4. Never rely on remembered bindings: read the rows into the work
   before reasoning, update them in the same session after. THIS
   EXTENDS TO ARITHMETIC (FR-26): no count or total enters any document
   from memory - every number is recomputed by a command or staleness
   guard at write time. The source cycle shipped a headline of 24
   against sources carrying 23, and omitted an item while including its
   alias; the guard caught both on its first run. When one question
   carries two ids, say so in the table - counting it twice overstates
   the queue, omitting either id hides it from that document's readers.
5. Doc-code reconciliation is table-driven: each row cites both the
   document anchor and the code symbol; one-sided rows are OPEN by
   definition and listed as such.
6. Append-and-supersede: retired rows stay, marked RETIRED with the
   superseding row id - the history of a binding is part of its meaning.
<!-- PROMPT-CORE-END -->
